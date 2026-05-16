from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ApiKey,
    Client,
    PaymentIntent,
    Transaction,
    Verification,
    WebhookLog,
)
from app.exceptions import InsufficientBalanceError


# ---------------------------------------------------------------------------
# Client queries
# ---------------------------------------------------------------------------

async def create_client(db: AsyncSession, name: str, email: str) -> Client:
    client = Client(name=name, email=email, balance_naira=0)
    db.add(client)
    await db.flush()
    await db.refresh(client)
    return client


async def get_client_by_id(db: AsyncSession, client_id: UUID) -> Client | None:
    result = await db.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


async def get_client_by_email(db: AsyncSession, email: str) -> Client | None:
    result = await db.execute(select(Client).where(Client.email == email))
    return result.scalar_one_or_none()


async def update_client_squad_info(
    db: AsyncSession,
    client_id: UUID,
    virtual_account_ref: str,
    customer_id: str,
    account_number: str,
    bank_name: str,
) -> None:
    await db.execute(
        update(Client)
        .where(Client.id == client_id)
        .values(
            squad_virtual_account_ref=virtual_account_ref,
            squad_customer_id=customer_id,
            squad_account_number=account_number,
            squad_bank_name=bank_name,
        )
    )


async def update_client_balance(db: AsyncSession, client_id: UUID, new_balance: int) -> None:
    await db.execute(
        update(Client).where(Client.id == client_id).values(balance_naira=new_balance)
    )


async def deduct_balance(db: AsyncSession, client_id: UUID, amount: int) -> tuple[int, int]:
    """Atomically deduct `amount` from client's balance. Uses SELECT FOR UPDATE.

    Returns (balance_before, balance_after). Raises InsufficientBalanceError if
    balance < amount. Caller is responsible for committing the session.
    """
    result = await db.execute(
        select(Client).where(Client.id == client_id).with_for_update()
    )
    client = result.scalar_one()
    if client.balance_naira < amount:
        raise InsufficientBalanceError(client.balance_naira)
    balance_before = client.balance_naira
    balance_after = balance_before - amount
    client.balance_naira = balance_after
    await db.flush()
    return balance_before, balance_after


# ---------------------------------------------------------------------------
# API key queries
# ---------------------------------------------------------------------------

async def create_api_key(
    db: AsyncSession,
    client_id: UUID,
    key_hash: str,
    key_prefix: str,
    label: str = "default",
) -> ApiKey:
    api_key = ApiKey(
        client_id=client_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        label=label,
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    return api_key


async def get_client_by_api_key_hash(db: AsyncSession, key_hash: str) -> Client | None:
    result = await db.execute(
        select(Client)
        .join(ApiKey, Client.id == ApiKey.client_id)
        .where(ApiKey.key_hash == key_hash)
        .where(ApiKey.is_active == True)  # noqa: E712
        .where(Client.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def update_api_key_last_used(db: AsyncSession, key_hash: str) -> None:
    await db.execute(
        update(ApiKey).where(ApiKey.key_hash == key_hash).values(last_used_at=datetime.now(timezone.utc))
    )


# ---------------------------------------------------------------------------
# Verification queries
# ---------------------------------------------------------------------------

async def get_cached_verification(
    db: AsyncSession, image_hash: str, client_id: UUID
) -> Verification | None:
    """Returns the most recent non-cached verification for this image+client whose
    cache window has not expired. Returns None if no fresh result exists."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Verification)
        .where(Verification.image_hash == image_hash)
        .where(Verification.client_id == client_id)
        .where(Verification.cached == False)  # noqa: E712
        .where(Verification.cache_expires_at > now)
        .order_by(Verification.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_verification(
    db: AsyncSession,
    client_id: UUID,
    image_hash: str,
    trust_score: int,
    verdict: str,
    confidence: str,
    spatial_score: int,
    frequency_score: int,
    processing_ms: int,
    billed_amount: int,
    cached: bool,
    image_size_bytes: int | None = None,
    image_mime_type: str | None = None,
) -> Verification:
    verification = Verification(
        client_id=client_id,
        image_hash=image_hash,
        image_size_bytes=image_size_bytes,
        image_mime_type=image_mime_type,
        trust_score=trust_score,
        verdict=verdict,
        confidence=confidence,
        spatial_score=spatial_score,
        frequency_score=frequency_score,
        processing_ms=processing_ms,
        billed_amount=billed_amount,
        cached=cached,
        cache_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)
    await db.flush()
    await db.refresh(verification)
    return verification


async def update_verification_transaction_id(
    db: AsyncSession, verification_id: UUID, transaction_id: UUID
) -> None:
    await db.execute(
        update(Verification)
        .where(Verification.id == verification_id)
        .values(transaction_id=transaction_id)
    )


async def get_verifications_by_client(
    db: AsyncSession, client_id: UUID, limit: int = 20
) -> list[Verification]:
    result = await db.execute(
        select(Verification)
        .where(Verification.client_id == client_id)
        .order_by(Verification.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Transaction queries
# ---------------------------------------------------------------------------

async def create_transaction(
    db: AsyncSession,
    client_id: UUID,
    verification_id: UUID | None,
    amount_naira: int,
    type: str,
    balance_before: int,
    balance_after: int,
    description: str,
    squad_ref: str | None = None,
    squad_event: str | None = None,
    idempotency_key: str | None = None,
) -> Transaction:
    transaction = Transaction(
        client_id=client_id,
        verification_id=verification_id,
        amount_naira=amount_naira,
        type=type,
        balance_before=balance_before,
        balance_after=balance_after,
        description=description,
        squad_ref=squad_ref,
        squad_event=squad_event,
        idempotency_key=idempotency_key,
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def get_transactions_by_client(
    db: AsyncSession, client_id: UUID, limit: int = 20
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.client_id == client_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def transaction_exists_by_idempotency_key(db: AsyncSession, key: str) -> bool:
    result = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.idempotency_key == key)
    )
    return (result.scalar() or 0) > 0


async def count_verifications_by_client(db: AsyncSession, client_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Verification).where(Verification.client_id == client_id)
    )
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Payment intent queries
# ---------------------------------------------------------------------------

async def create_payment_intent(
    db: AsyncSession,
    client_id: UUID,
    amount_naira: int,
    payment_link: str,
    squad_ref: str | None = None,
) -> PaymentIntent:
    intent = PaymentIntent(
        client_id=client_id,
        amount_naira=amount_naira,
        payment_link=payment_link,
        squad_ref=squad_ref,
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(intent)
    await db.flush()
    await db.refresh(intent)
    return intent


async def complete_payment_intent(db: AsyncSession, squad_ref: str) -> None:
    await db.execute(
        update(PaymentIntent)
        .where(PaymentIntent.squad_ref == squad_ref)
        .values(status="completed", completed_at=datetime.now(timezone.utc))
    )


# ---------------------------------------------------------------------------
# Webhook log queries
# ---------------------------------------------------------------------------

async def log_webhook(
    db: AsyncSession, raw_payload: bytes, signature: str, signature_valid: bool
) -> WebhookLog:
    import json

    try:
        parsed = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        parsed = {"_raw": raw_payload.decode("utf-8", errors="replace")}

    event_type = None
    squad_ref = None
    if isinstance(parsed, dict):
        # Flat Squad virtual-account webhook (real shape)
        squad_ref = parsed.get("transaction_reference") or parsed.get("transaction_ref")
        event_type = parsed.get("event") or parsed.get("Event")
        # Legacy {Event, Body} envelope (fallback)
        if not squad_ref and isinstance(parsed.get("Body"), dict):
            squad_ref = parsed["Body"].get("transaction_ref")

    log = WebhookLog(
        event_type=event_type,
        squad_ref=squad_ref,
        raw_payload=parsed,
        signature_valid=signature_valid,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def update_webhook_log(
    db: AsyncSession,
    webhook_id: UUID,
    matched: bool,
    matched_client_id: UUID | None = None,
    processed: bool = False,
    processing_error: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    values: dict = {"matched": matched, "processed": processed}
    if matched_client_id is not None:
        values["matched_client_id"] = matched_client_id
    if processing_error is not None:
        values["processing_error"] = processing_error
    if idempotency_key is not None:
        values["idempotency_key"] = idempotency_key
    await db.execute(update(WebhookLog).where(WebhookLog.id == webhook_id).values(**values))


async def get_client_by_squad_customer_id(
    db: AsyncSession, squad_customer_id: str
) -> Client | None:
    result = await db.execute(
        select(Client).where(Client.squad_customer_id == squad_customer_id)
    )
    return result.scalar_one_or_none()
