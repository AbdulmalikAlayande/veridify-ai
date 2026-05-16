"""Squad webhook receiver.

Squad sends a FLAT JSON payload to this URL when a virtual account is credited:
  {
    "transaction_reference": "...",
    "virtual_account_number": "...",
    "principal_amount": "17500.00",   # decimal string, naira
    "customer_identifier": "<our client.id>",
    "channel": "transfer",
    ...
  }

Squad authenticates the call with HMAC-SHA512(secret, raw_body) → hex UPPERCASE
in the `x-squad-encrypted-body` header. We always return 200 to stop Squad's retry
loop, but we silently ignore unsigned / malformed / unmatched payloads.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import queries
from app.db.database import get_db
from app.schemas.webhook import WebhookResponse
from app.services.squad import verify_squad_signature

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def _amount_naira(raw) -> int | None:
    if raw is None:
        return None
    try:
        # Squad delivers naira as a decimal string (e.g. "17500.00").
        # Truncate fractional kobo — we bill in whole naira.
        return int(Decimal(str(raw)))
    except (InvalidOperation, ValueError):
        return None


def _hmac_secret() -> str:
    # Squad uses the secret key itself as the HMAC secret. SQUAD_WEBHOOK_SECRET
    # is supported as an override if a user separates them on the dashboard.
    return (settings.squad_webhook_secret or settings.squad_secret_key or "").strip()


@router.post("/squad", response_model=WebhookResponse)
async def squad_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")
    is_valid = verify_squad_signature(raw_body, signature, _hmac_secret())

    webhook_log = await queries.log_webhook(db, raw_body, signature, is_valid)
    await db.commit()

    if not is_valid:
        logger.warning("Webhook rejected: invalid HMAC (log_id=%s)", webhook_log.id)
        return {"status": "received"}

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        await queries.update_webhook_log(
            db, webhook_log.id, matched=False, processed=False,
            processing_error="invalid_json",
        )
        await db.commit()
        return {"status": "received"}

    squad_ref = payload.get("transaction_reference") or payload.get("transaction_ref") or ""
    customer_identifier = payload.get("customer_identifier") or ""
    amount_naira = _amount_naira(payload.get("principal_amount") or payload.get("settled_amount"))

    if not squad_ref or not amount_naira or amount_naira <= 0:
        await queries.update_webhook_log(
            db, webhook_log.id, matched=False, processed=False,
            processing_error="missing_required_fields",
        )
        await db.commit()
        return {"status": "received"}

    idempotency_key = f"webhook_{squad_ref}"

    if await queries.transaction_exists_by_idempotency_key(db, idempotency_key):
        await queries.update_webhook_log(
            db, webhook_log.id, matched=True, processed=True,
            idempotency_key=idempotency_key,
            processing_error="duplicate_ignored",
        )
        await db.commit()
        return {"status": "received"}

    client = None
    if customer_identifier:
        client = await queries.get_client_by_squad_customer_id(db, customer_identifier)
        if client is None:
            # We set customer_identifier = str(client.id) at VA creation. Match on that.
            try:
                from uuid import UUID
                client = await queries.get_client_by_id(db, UUID(customer_identifier))
            except (ValueError, TypeError):
                client = None

    if client is None:
        await queries.update_webhook_log(
            db, webhook_log.id, matched=False, processed=False,
            processing_error="no_matching_client",
        )
        await db.commit()
        return {"status": "received"}

    balance_before = client.balance_naira
    balance_after = balance_before + amount_naira
    await queries.update_client_balance(db, client.id, balance_after)

    await queries.create_transaction(
        db,
        client_id=client.id,
        verification_id=None,
        amount_naira=amount_naira,
        type="CREDIT",
        balance_before=balance_before,
        balance_after=balance_after,
        description=f"Squad top-up - ref: {squad_ref}",
        squad_ref=squad_ref,
        squad_event="virtual_account.credit",
        idempotency_key=idempotency_key,
    )

    await queries.complete_payment_intent(db, squad_ref)

    await queries.update_webhook_log(
        db, webhook_log.id,
        matched=True, matched_client_id=client.id,
        processed=True, idempotency_key=idempotency_key,
    )
    await db.commit()

    return {"status": "received"}
