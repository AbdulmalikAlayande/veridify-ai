"""Account business logic — orchestrates Squad + database for client lifecycle."""

from __future__ import annotations

import hashlib
import logging
import secrets

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import queries
from app.db.models import Client
from app.exceptions import SquadAPIError
from app.services import squad as squad_service

logger = logging.getLogger(__name__)
settings = get_settings()


def _generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, key_hash). Raw is shown to the user once; only the hash persists."""
    raw = "vrf_sk_live_" + secrets.token_hex(32)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, key_hash


def _extract_squad_va(squad_response: dict) -> dict | None:
    """Pull the virtual-account details out of Squad's response envelope.

    Squad returns: {"success": true, "data": {"virtual_account_number": "...", "bank_code": "058", ...}}
    """
    data = squad_response.get("data") or {}
    va_number = data.get("virtual_account_number")
    if not va_number:
        return None
    bank_code = data.get("bank_code", "")
    bank_name = "GTBank" if bank_code == "058" else (data.get("bank_name") or "")
    return {
        "virtual_account_number": va_number,
        "customer_identifier": data.get("customer_identifier") or "",
        "bank_name": bank_name,
    }


async def create_account(db: AsyncSession, name: str, email: str) -> dict:
    existing = await queries.get_client_by_email(db, email)
    if existing is not None:
        raise HTTPException(status_code=409, detail={
            "error": "EMAIL_ALREADY_REGISTERED",
            "message": "An account with this email already exists",
        })

    client = await queries.create_client(db, name=name, email=email)
    raw_key, key_hash = _generate_api_key()
    key_prefix = raw_key[:12]
    await queries.create_api_key(db, client.id, key_hash, key_prefix, label="default")

    squad_va: dict | None = None
    try:
        squad_response = await squad_service.create_virtual_account(
            client_id=str(client.id), client_email=email, client_name=name,
        )
        squad_va = _extract_squad_va(squad_response)
        if squad_va:
            await queries.update_client_squad_info(
                db,
                client_id=client.id,
                virtual_account_ref=squad_va["virtual_account_number"],
                customer_id=squad_va["customer_identifier"] or str(client.id),
                account_number=squad_va["virtual_account_number"],
                bank_name=squad_va["bank_name"],
            )
    except SquadAPIError as exc:
        logger.warning("Squad VA creation failed for client %s: %s", client.id, exc.message)

    await db.commit()

    return {
        "client_id": client.id,
        "api_key": raw_key,
        "message": "Account created. Store the api_key securely — it will not be shown again.",
        "squad_virtual_account": (
            {
                "account_number": squad_va["virtual_account_number"],
                "bank_name": squad_va["bank_name"] or "GTBank",
                "account_name": name,
            }
            if squad_va
            else None
        ),
        "balance_naira": 0,
    }


async def get_balance(db: AsyncSession, client: Client) -> dict:
    recent = await queries.get_transactions_by_client(db, client.id, limit=20)
    total = await queries.count_verifications_by_client(db, client.id)
    return {
        "balance_naira": client.balance_naira,
        "total_verifications": total,
        "recent_transactions": [
            {
                "type": t.type,
                "amount_naira": t.amount_naira,
                "description": t.description,
                "balance_after": t.balance_after,
                "created_at": t.created_at,
            }
            for t in recent
        ],
    }


async def fund_account(db: AsyncSession, client: Client, amount_naira: int) -> dict:
    if amount_naira <= 0 or amount_naira > 1_000_000:
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_AMOUNT",
            "message": "amount_naira must be between 1 and 1,000,000",
        })

    squad_response = await squad_service.generate_payment_link(
        amount_naira=amount_naira, client_email=client.email,
    )
    data = squad_response.get("data") or {}
    checkout_url = data.get("checkout_url") or ""
    squad_ref = squad_response.get("_transaction_ref")

    await queries.create_payment_intent(
        db,
        client_id=client.id,
        amount_naira=amount_naira,
        payment_link=checkout_url,
        squad_ref=squad_ref,
    )
    await db.commit()

    return {
        "payment_link": checkout_url,
        "amount_naira": amount_naira,
        "expires_in_hours": 24,
        "message": "Open the payment link in a browser to fund your account.",
    }
