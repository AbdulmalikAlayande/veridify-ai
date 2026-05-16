"""Squad webhook integration tests."""

import pytest
import hmac
import hashlib
import json
import uuid
from app.config import get_settings

settings = get_settings()


def generate_signature(payload: str) -> str:
    secret = settings.squad_webhook_secret or settings.squad_secret_key
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha512
    ).hexdigest().upper()


@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_200(client):
    payload = json.dumps({"Event": "payment.success", "Body": {"transaction_ref": "123"}})
    response = await client.post(
        "/webhook/squad",
        content=payload,
        headers={"x-squad-encrypted-body": "invalid_sig"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "received"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_does_not_credit_balance(client, registered_client):
    customer_id = "test_cust_" + uuid.uuid4().hex
    
    # Update client with squad_customer_id manually
    from app.db.database import AsyncSessionLocal
    from app.db import queries
    async with AsyncSessionLocal() as db:
        await queries.update_client_squad_info(db, uuid.UUID(registered_client["client_id"]), "vref", customer_id, "acc", "bank")
        await db.commit()
        
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": "123", "customer_id": customer_id, "amount": 10000} # 100 Naira
    })
    
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": "invalid_sig"})
    
    res = await client.get("/account/balance", headers={"X-API-Key": registered_client["api_key"]})
    assert res.json()["balance_naira"] == 0


@pytest.mark.asyncio
async def test_webhook_invalid_signature_is_logged(client):
    payload = json.dumps({"Event": "payment.success", "Body": {"transaction_ref": "log_test"}})
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": "invalid_sig"})
    
    # Check DB logs
    from app.db.database import AsyncSessionLocal
    from app.db.models import WebhookLog
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WebhookLog).where(WebhookLog.squad_ref == "log_test"))
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.signature_valid is False


@pytest.mark.asyncio
async def test_webhook_valid_signature_credits_balance(client, registered_client):
    customer_id = "test_cust_" + uuid.uuid4().hex
    from app.db.database import AsyncSessionLocal
    from app.db import queries
    async with AsyncSessionLocal() as db:
        await queries.update_client_squad_info(db, uuid.UUID(registered_client["client_id"]), "vref", customer_id, "acc", "bank")
        await db.commit()
        
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": "SQ_" + uuid.uuid4().hex, "customer_id": customer_id, "amount": 50000} # 500 Naira
    })
    sig = generate_signature(payload)
    
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    
    res = await client.get("/account/balance", headers={"X-API-Key": registered_client["api_key"]})
    assert res.json()["balance_naira"] == 500


@pytest.mark.asyncio
async def test_webhook_valid_signature_creates_credit_transaction(client, registered_client):
    customer_id = "test_cust_" + uuid.uuid4().hex
    from app.db.database import AsyncSessionLocal
    from app.db import queries
    async with AsyncSessionLocal() as db:
        await queries.update_client_squad_info(db, uuid.UUID(registered_client["client_id"]), "vref", customer_id, "acc", "bank")
        await db.commit()
        
    ref = "SQ_" + uuid.uuid4().hex
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": ref, "customer_id": customer_id, "amount": 50000}
    })
    sig = generate_signature(payload)
    
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    
    res = await client.get("/account/balance", headers={"X-API-Key": registered_client["api_key"]})
    txs = res.json()["recent_transactions"]
    assert len(txs) == 1
    assert txs[0]["type"] == "CREDIT"
    assert txs[0]["amount_naira"] == 500


@pytest.mark.asyncio
async def test_webhook_duplicate_transaction_ref_is_idempotent(client, registered_client):
    customer_id = "test_cust_" + uuid.uuid4().hex
    from app.db.database import AsyncSessionLocal
    from app.db import queries
    async with AsyncSessionLocal() as db:
        await queries.update_client_squad_info(db, uuid.UUID(registered_client["client_id"]), "vref", customer_id, "acc", "bank")
        await db.commit()
        
    ref = "SQ_" + uuid.uuid4().hex
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": ref, "customer_id": customer_id, "amount": 50000}
    })
    sig = generate_signature(payload)
    
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    
    res = await client.get("/account/balance", headers={"X-API-Key": registered_client["api_key"]})
    assert res.json()["balance_naira"] == 500 # Should still be 500, not 1000


@pytest.mark.asyncio
async def test_webhook_unknown_customer_returns_200_no_credit(client):
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": "SQ_" + uuid.uuid4().hex, "customer_id": "unknown", "amount": 50000}
    })
    sig = generate_signature(payload)
    
    res = await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_webhook_malformed_json_returns_200(client):
    payload = "{"
    sig = generate_signature(payload)
    res = await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_webhook_missing_amount_returns_200_no_credit(client, registered_client):
    customer_id = "test_cust_" + uuid.uuid4().hex
    from app.db.database import AsyncSessionLocal
    from app.db import queries
    async with AsyncSessionLocal() as db:
        await queries.update_client_squad_info(db, uuid.UUID(registered_client["client_id"]), "vref", customer_id, "acc", "bank")
        await db.commit()
        
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": "SQ_" + uuid.uuid4().hex, "customer_id": customer_id}
    })
    sig = generate_signature(payload)
    
    res = await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    assert res.status_code == 200
    
    bal = await client.get("/account/balance", headers={"X-API-Key": registered_client["api_key"]})
    assert bal.json()["balance_naira"] == 0


@pytest.mark.asyncio
async def test_webhook_completes_matching_payment_intent(client, registered_client):
    customer_id = "test_cust_" + uuid.uuid4().hex
    from app.db.database import AsyncSessionLocal
    from app.db import queries
    async with AsyncSessionLocal() as db:
        await queries.update_client_squad_info(db, uuid.UUID(registered_client["client_id"]), "vref", customer_id, "acc", "bank")
        ref = "SQ_" + uuid.uuid4().hex
        await queries.create_payment_intent(db, uuid.UUID(registered_client["client_id"]), 500, "link", ref)
        await db.commit()
        
    payload = json.dumps({
        "Event": "payment.success",
        "Body": {"transaction_ref": ref, "customer_id": customer_id, "amount": 50000}
    })
    sig = generate_signature(payload)
    
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    
    # Verify DB
    from app.db.models import PaymentIntent
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PaymentIntent).where(PaymentIntent.squad_ref == ref))
        pi = result.scalar_one()
        assert pi.status == "completed"


@pytest.mark.asyncio
async def test_webhook_logs_all_events(client, registered_client):
    payload = json.dumps({
        "Event": "payment.failure",
        "Body": {"transaction_ref": "SQ_FAIL_" + uuid.uuid4().hex}
    })
    sig = generate_signature(payload)
    
    await client.post("/webhook/squad", content=payload, headers={"x-squad-encrypted-body": sig})
    
    from app.db.database import AsyncSessionLocal
    from app.db.models import WebhookLog
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WebhookLog).where(WebhookLog.event_type == "payment.failure"))
        log = result.scalars().first()
        assert log is not None
        assert log.signature_valid is True
