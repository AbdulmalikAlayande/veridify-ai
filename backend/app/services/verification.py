"""Verification orchestrator — the /verify endpoint's business logic."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import queries
from app.db.models import Client
from app.exceptions import (
    InferenceFailedError,
    InsufficientBalanceError,
    SquadAPIError,
    UnsupportedImageTypeError,
    VeridifiError,
)
from app.services import inference as inference_service
from app.services import squad as squad_service

logger = logging.getLogger(__name__)
settings = get_settings()


async def _payment_link_for_topup(client: Client, amount_naira: int) -> str | None:
    try:
        resp = await squad_service.generate_payment_link(
            amount_naira=amount_naira, client_email=client.email,
        )
    except SquadAPIError as exc:
        logger.warning("Could not attach payment link to 402 response: %s", exc.message)
        return None
    data = resp.get("data") or {}
    return data.get("checkout_url") or None


async def process_verification(
    db: AsyncSession, client: Client, image: UploadFile
) -> dict:
    cost = settings.verification_cost_naira

    if client.balance_naira < cost:
        payment_link = await _payment_link_for_topup(client, max(cost, 1000))
        raise InsufficientBalanceError(client.balance_naira, payment_link=payment_link)

    image_bytes = await image.read()
    if not image_bytes:
        raise UnsupportedImageTypeError("empty")

    mime_type, ext = await inference_service.validate_image(image_bytes, settings.max_image_size_mb)
    image_hash = inference_service.compute_image_hash(image_bytes)

    cached_row = await queries.get_cached_verification(db, image_hash, client.id)

    if cached_row is not None:
        # Cache hit: reuse the prior result without billing or writing a new row.
        # Spec contract — "the same image submitted twice does not charge twice."
        return {
            "verification_id": cached_row.id,
            "trust_score": cached_row.trust_score,
            "verdict": cached_row.verdict,
            "confidence": cached_row.confidence,
            "processing_ms": cached_row.processing_ms or 0,
            "cached": True,
            "billed_naira": 0,
            "balance_remaining": client.balance_naira,
            "breakdown": {
                "spatial_score": cached_row.spatial_score or 0,
                "frequency_score": cached_row.frequency_score or 0,
            },
        }

    temp_path: Path | None = None
    try:
        temp_path = await inference_service.save_temp_image(image_bytes, ext)
        try:
            scores = await inference_service.run_inference(image_bytes, image_hash)
        except NotImplementedError as exc:
            raise InferenceFailedError(str(exc)) from exc
        except VeridifiError:
            raise
        except Exception as exc:
            logger.exception("Inference crashed for client=%s", client.id)
            raise InferenceFailedError("Inference engine error") from exc
    finally:
        if temp_path is not None:
            inference_service.delete_temp_image(temp_path)

    verification = await queries.create_verification(
        db,
        client_id=client.id,
        image_hash=image_hash,
        trust_score=scores["trust_score"],
        verdict=scores["verdict"],
        confidence=scores["confidence"],
        spatial_score=scores["spatial_score"],
        frequency_score=scores["frequency_score"],
        processing_ms=scores["processing_ms"],
        billed_amount=cost,
        cached=False,
        image_size_bytes=len(image_bytes),
        image_mime_type=mime_type,
    )

    balance_before, balance_after = await queries.deduct_balance(db, client.id, cost)

    txn = await queries.create_transaction(
        db,
        client_id=client.id,
        verification_id=verification.id,
        amount_naira=cost,
        type="DEBIT",
        balance_before=balance_before,
        balance_after=balance_after,
        description="Image verification",
    )

    await queries.update_verification_transaction_id(db, verification.id, txn.id)

    await db.commit()

    return {
        "verification_id": verification.id,
        "trust_score": scores["trust_score"],
        "verdict": scores["verdict"],
        "confidence": scores["confidence"],
        "processing_ms": scores["processing_ms"],
        "cached": False,
        "billed_naira": cost,
        "balance_remaining": balance_after,
        "breakdown": {
            "spatial_score": scores["spatial_score"],
            "frequency_score": scores["frequency_score"],
        },
    }
