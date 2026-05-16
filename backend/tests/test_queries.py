"""Tests for database queries.

These are true integration tests that run against the PostgreSQL database.
"""

import uuid
import pytest
from datetime import datetime, timezone

from app.db.database import AsyncSessionLocal
from app.db import queries
from app.exceptions import InsufficientBalanceError
from sqlalchemy import select
from app.db.models import Client, ApiKey, Verification, Transaction, PaymentIntent, WebhookLog


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_create_client_persists_row(db_session):
    client = await queries.create_client(db_session, name="Query Test", email=f"query{uuid.uuid4().hex[:8]}@test.com")
    assert client.id is not None
    assert client.balance_naira == 0


@pytest.mark.asyncio
async def test_get_client_by_email_returns_match(db_session):
    email = f"match{uuid.uuid4().hex[:8]}@test.com"
    created = await queries.create_client(db_session, name="Match Test", email=email)
    fetched = await queries.get_client_by_email(db_session, email)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_client_by_email_returns_none_when_missing(db_session):
    fetched = await queries.get_client_by_email(db_session, "missing@test.com")
    assert fetched is None


@pytest.mark.asyncio
async def test_update_client_squad_info_sets_all_four_fields(db_session):
    client = await queries.create_client(db_session, name="Squad Info", email=f"squad{uuid.uuid4().hex[:8]}@test.com")
    await queries.update_client_squad_info(
        db_session, client.id, "v_ref_123", "c_id_123", "0123456789", "GTBank"
    )
    await db_session.commit()
    
    fetched = await queries.get_client_by_id(db_session, client.id)
    assert fetched.squad_virtual_account_ref == "v_ref_123"
    assert fetched.squad_customer_id == "c_id_123"
    assert fetched.squad_account_number == "0123456789"
    assert fetched.squad_bank_name == "GTBank"


@pytest.mark.asyncio
async def test_deduct_balance_returns_before_and_after(db_session):
    client = await queries.create_client(db_session, name="Deduct", email=f"deduct{uuid.uuid4().hex[:8]}@test.com")
    await queries.update_client_balance(db_session, client.id, 1000)
    await db_session.commit()
    
    before, after = await queries.deduct_balance(db_session, client.id, 175)
    await db_session.commit()
    
    assert before == 1000
    assert after == 825
    
    fetched = await queries.get_client_by_id(db_session, client.id)
    assert fetched.balance_naira == 825


@pytest.mark.asyncio
async def test_deduct_balance_raises_when_insufficient(db_session):
    client = await queries.create_client(db_session, name="Deduct Fail", email=f"fail{uuid.uuid4().hex[:8]}@test.com")
    await queries.update_client_balance(db_session, client.id, 100)
    await db_session.commit()
    
    with pytest.raises(InsufficientBalanceError):
        await queries.deduct_balance(db_session, client.id, 175)


@pytest.mark.asyncio
async def test_create_api_key_links_to_client(db_session):
    client = await queries.create_client(db_session, name="Key Client", email=f"key{uuid.uuid4().hex[:8]}@test.com")
    key_hash = f"hash_{uuid.uuid4().hex}"
    api_key = await queries.create_api_key(db_session, client.id, key_hash, "vrf_sk_live_")
    assert api_key.client_id == client.id
    assert api_key.key_hash == key_hash


@pytest.mark.asyncio
async def test_get_client_by_api_key_hash_ignores_inactive_keys(db_session):
    client = await queries.create_client(db_session, name="Key Inactive", email=f"kinactive{uuid.uuid4().hex[:8]}@test.com")
    key_hash = f"hash_{uuid.uuid4().hex}"
    api_key = await queries.create_api_key(db_session, client.id, key_hash, "vrf_sk_live_")
    
    api_key.is_active = False
    await db_session.flush()
    
    fetched = await queries.get_client_by_api_key_hash(db_session, key_hash)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_client_by_api_key_hash_ignores_inactive_clients(db_session):
    client = await queries.create_client(db_session, name="Client Inactive", email=f"cinactive{uuid.uuid4().hex[:8]}@test.com")
    key_hash = f"hash_{uuid.uuid4().hex}"
    await queries.create_api_key(db_session, client.id, key_hash, "vrf_sk_live_")
    
    client.is_active = False
    await db_session.flush()
    
    fetched = await queries.get_client_by_api_key_hash(db_session, key_hash)
    assert fetched is None


@pytest.mark.asyncio
async def test_update_api_key_last_used_sets_timestamp(db_session):
    client = await queries.create_client(db_session, name="Key TS", email=f"kts{uuid.uuid4().hex[:8]}@test.com")
    key_hash = f"hash_{uuid.uuid4().hex}"
    api_key = await queries.create_api_key(db_session, client.id, key_hash, "vrf_sk_live_")
    
    assert api_key.last_used_at is None
    await queries.update_api_key_last_used(db_session, key_hash)
    await db_session.commit()
    
    result = await db_session.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    fetched = result.scalar_one()
    assert fetched.last_used_at is not None


@pytest.mark.asyncio
async def test_get_cached_verification_returns_fresh_match(db_session):
    client = await queries.create_client(db_session, name="Cache Match", email=f"cmatch{uuid.uuid4().hex[:8]}@test.com")
    image_hash = f"img_{uuid.uuid4().hex}"
    
    created = await queries.create_verification(
        db_session, client.id, image_hash, 90, "AUTHENTIC", "HIGH", 92, 88, 300, 175, False
    )
    
    fetched = await queries.get_cached_verification(db_session, image_hash, client.id)
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_cached_verification_returns_none_when_expired(db_session):
    client = await queries.create_client(db_session, name="Cache Expire", email=f"cexpire{uuid.uuid4().hex[:8]}@test.com")
    image_hash = f"img_{uuid.uuid4().hex}"
    
    ver = await queries.create_verification(
        db_session, client.id, image_hash, 90, "AUTHENTIC", "HIGH", 92, 88, 300, 175, False
    )
    # Manually expire
    from datetime import timedelta
    ver.cache_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.flush()
    
    fetched = await queries.get_cached_verification(db_session, image_hash, client.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_cached_verification_ignores_other_clients(db_session):
    client1 = await queries.create_client(db_session, name="C1", email=f"c1{uuid.uuid4().hex[:8]}@test.com")
    client2 = await queries.create_client(db_session, name="C2", email=f"c2{uuid.uuid4().hex[:8]}@test.com")
    image_hash = f"img_{uuid.uuid4().hex}"
    
    await queries.create_verification(
        db_session, client1.id, image_hash, 90, "AUTHENTIC", "HIGH", 92, 88, 300, 175, False
    )
    
    fetched = await queries.get_cached_verification(db_session, image_hash, client2.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_create_verification_sets_cache_expires_at_24h(db_session):
    client = await queries.create_client(db_session, name="Cache 24", email=f"c24{uuid.uuid4().hex[:8]}@test.com")
    ver = await queries.create_verification(
        db_session, client.id, "hash123", 90, "AUTHENTIC", "HIGH", 92, 88, 300, 175, False
    )
    
    diff = ver.cache_expires_at - datetime.now(timezone.utc)
    # Should be roughly 24 hours (86400 seconds)
    assert 86000 < diff.total_seconds() < 87000


@pytest.mark.asyncio
async def test_update_verification_transaction_id_links_transaction(db_session):
    client = await queries.create_client(db_session, name="Ver Trans", email=f"vt{uuid.uuid4().hex[:8]}@test.com")
    ver = await queries.create_verification(
        db_session, client.id, "hash123", 90, "AUTHENTIC", "HIGH", 92, 88, 300, 175, False
    )
    tx = await queries.create_transaction(
        db_session, client.id, ver.id, 175, "DEBIT", 1000, 825, "Test"
    )
    
    await queries.update_verification_transaction_id(db_session, ver.id, tx.id)
    await db_session.commit()
    
    result = await db_session.execute(select(Verification).where(Verification.id == ver.id))
    fetched_ver = result.scalar_one()
    assert fetched_ver.transaction_id == tx.id


@pytest.mark.asyncio
async def test_create_transaction_persists_row(db_session):
    client = await queries.create_client(db_session, name="Txn Persist", email=f"txnp{uuid.uuid4().hex[:8]}@test.com")
    tx = await queries.create_transaction(
        db_session, client.id, None, 1000, "CREDIT", 0, 1000, "Topup"
    )
    assert tx.id is not None
    assert tx.amount_naira == 1000


@pytest.mark.asyncio
async def test_get_transactions_by_client_orders_desc(db_session):
    client = await queries.create_client(db_session, name="Txn Desc", email=f"txnd{uuid.uuid4().hex[:8]}@test.com")
    await queries.create_transaction(db_session, client.id, None, 100, "CREDIT", 0, 100, "1")
    await queries.create_transaction(db_session, client.id, None, 200, "CREDIT", 100, 300, "2")
    
    txs = await queries.get_transactions_by_client(db_session, client.id)
    assert len(txs) == 2
    assert txs[0].amount_naira == 200 # Most recent first
    assert txs[1].amount_naira == 100


@pytest.mark.asyncio
async def test_transaction_exists_by_idempotency_key_detects_duplicate(db_session):
    client = await queries.create_client(db_session, name="Txn Idemp", email=f"txni{uuid.uuid4().hex[:8]}@test.com")
    key = f"idem_{uuid.uuid4().hex}"
    
    exists = await queries.transaction_exists_by_idempotency_key(db_session, key)
    assert not exists
    
    await queries.create_transaction(db_session, client.id, None, 100, "CREDIT", 0, 100, "T", idempotency_key=key)
    
    exists = await queries.transaction_exists_by_idempotency_key(db_session, key)
    assert exists


@pytest.mark.asyncio
async def test_create_payment_intent_default_status_pending(db_session):
    client = await queries.create_client(db_session, name="PI Pending", email=f"pip{uuid.uuid4().hex[:8]}@test.com")
    pi = await queries.create_payment_intent(db_session, client.id, 1000, "http://link")
    assert pi.status == "pending"


@pytest.mark.asyncio
async def test_complete_payment_intent_sets_completed_at(db_session):
    client = await queries.create_client(db_session, name="PI Comp", email=f"pic{uuid.uuid4().hex[:8]}@test.com")
    ref = f"SQ_{uuid.uuid4().hex}"
    pi = await queries.create_payment_intent(db_session, client.id, 1000, "http://link", squad_ref=ref)
    
    await queries.complete_payment_intent(db_session, ref)
    await db_session.commit()
    
    result = await db_session.execute(select(PaymentIntent).where(PaymentIntent.id == pi.id))
    fetched = result.scalar_one()
    assert fetched.status == "completed"
    assert fetched.completed_at is not None


@pytest.mark.asyncio
async def test_log_webhook_extracts_event_and_ref(db_session):
    payload = b'{"event":"payment.success","transaction_ref":"SQ_123"}'
    log = await queries.log_webhook(db_session, payload, "sig", True)
    assert log.event_type == "payment.success"
    assert log.squad_ref == "SQ_123"


@pytest.mark.asyncio
async def test_log_webhook_records_invalid_signature(db_session):
    payload = b'{"event":"payment.success","transaction_ref":"SQ_123"}'
    log = await queries.log_webhook(db_session, payload, "bad_sig", False)
    assert log.signature_valid is False


@pytest.mark.asyncio
async def test_update_webhook_log_only_sets_provided_fields(db_session):
    log = await queries.log_webhook(db_session, b'{}', "sig", True)
    
    await queries.update_webhook_log(db_session, log.id, matched=True, processed=True)
    await db_session.commit()
    
    result = await db_session.execute(select(WebhookLog).where(WebhookLog.id == log.id))
    fetched = result.scalar_one()
    assert fetched.matched is True
    assert fetched.processed is True
    assert fetched.matched_client_id is None


@pytest.mark.asyncio
async def test_get_client_by_squad_customer_id_returns_match(db_session):
    client = await queries.create_client(db_session, name="Squad Match", email=f"sqm{uuid.uuid4().hex[:8]}@test.com")
    await queries.update_client_squad_info(db_session, client.id, "vref", "CUST_123", "012", "GTB")
    
    fetched = await queries.get_client_by_squad_customer_id(db_session, "CUST_123")
    assert fetched is not None
    assert fetched.id == client.id
