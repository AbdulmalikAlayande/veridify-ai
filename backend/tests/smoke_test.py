"""End-to-end smoke test mirroring the 9-step manual flow in VERIDIFI_BUILD_ORDER.md (STEP 18).

Run with:  .venv/Scripts/python.exe -m tests.smoke_test

The script boots the real ASGI app in-process (no separate uvicorn needed), seeds a
client, exercises every public endpoint, and cleans up after itself. Squad calls
that need real keys/beneficiary will fail gracefully — those assertions are softened.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from io import BytesIO
from uuid import UUID, uuid4

from PIL import Image
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.config import get_settings
from app.db import queries
from app.db.database import AsyncSessionLocal
from app.db.models import ApiKey, Client, PaymentIntent, Transaction, Verification, WebhookLog
from app.main import app

settings = get_settings()
SECRET = (settings.squad_webhook_secret or settings.squad_secret_key or "").strip()


def png_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (32, 32), "purple").save(buf, format="PNG")
    return buf.getvalue()


def sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha512).hexdigest().upper()


async def cleanup(client_id: UUID, extra_refs: list[str] | None = None) -> None:
    async with AsyncSessionLocal() as db:
        if extra_refs:
            await db.execute(delete(WebhookLog).where(WebhookLog.squad_ref.in_(extra_refs)))
        await db.execute(delete(WebhookLog).where(WebhookLog.matched_client_id == client_id))
        await db.execute(delete(Transaction).where(Transaction.client_id == client_id))
        await db.execute(delete(Verification).where(Verification.client_id == client_id))
        await db.execute(delete(PaymentIntent).where(PaymentIntent.client_id == client_id))
        await db.execute(delete(ApiKey).where(ApiKey.client_id == client_id))
        await db.execute(delete(Client).where(Client.id == client_id))
        await db.commit()


async def run() -> None:
    email = f"smoke-{uuid4().hex[:8]}@example.com"
    image = png_bytes()
    refs_used: list[str] = []

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        # Step 0 — health
        r = await http.get("/health")
        assert r.status_code == 200 and r.json() == {"status": "ok", "mode": "mock"}
        print("PASS  /health -> 200 mode=mock")

        # Step 1 — create account
        r = await http.post("/account/create", json={"name": "Test Insurer", "email": email})
        assert r.status_code == 201, r.text
        body = r.json()
        client_id = UUID(body["client_id"])
        api_key = body["api_key"]
        assert api_key.startswith("vrf_sk_live_")
        assert body["balance_naira"] == 0
        print(f"PASS  POST /account/create -> 201; client_id={client_id}; squad_va={body['squad_virtual_account'] is not None}")

        try:
            # Step 2 — balance (zero)
            r = await http.get("/account/balance", headers={"X-API-Key": api_key})
            assert r.status_code == 200
            assert r.json()["balance_naira"] == 0
            print("PASS  GET  /account/balance -> 200 balance=0")

            # Step 3 — verify with zero balance => 402
            r = await http.post(
                "/verify",
                files={"image": ("t.png", image, "image/png")},
                headers={"X-API-Key": api_key},
            )
            assert r.status_code == 402
            err = r.json()
            assert err["error"] == "INSUFFICIENT_BALANCE"
            print(f"PASS  POST /verify  (no balance) -> 402; payment_link_present={bool(err['detail'].get('payment_link'))}")

            # Step 4 — top up via DB (simulating a paid webhook)
            async with AsyncSessionLocal() as db:
                await queries.update_client_balance(db, client_id, 10_000)
                await db.commit()
            print("PASS  manual top-up -> balance=10000")

            # Step 5 — verify (cache miss)
            r = await http.post(
                "/verify",
                files={"image": ("t.png", image, "image/png")},
                headers={"X-API-Key": api_key},
            )
            assert r.status_code == 200
            first = r.json()
            assert first["cached"] is False
            assert first["billed_naira"] == 175
            assert first["balance_remaining"] == 9_825
            print(f"PASS  POST /verify  -> 200 cached=false trust={first['trust_score']} verdict={first['verdict']} remaining=9825")

            # Step 6 — verify same image (cache hit, still billed)
            r = await http.post(
                "/verify",
                files={"image": ("t.png", image, "image/png")},
                headers={"X-API-Key": api_key},
            )
            assert r.status_code == 200
            second = r.json()
            assert second["cached"] is True
            assert second["trust_score"] == first["trust_score"]
            assert second["balance_remaining"] == 9_650
            print("PASS  POST /verify  -> 200 cached=true remaining=9650")

            # Step 7 — GET verification by id
            r = await http.get(f"/verify/{first['verification_id']}", headers={"X-API-Key": api_key})
            assert r.status_code == 200
            assert r.json()["verification_id"] == first["verification_id"]
            print("PASS  GET  /verify/{id} -> 200")

            # Step 8 — balance shows the two DEBITs
            r = await http.get("/account/balance", headers={"X-API-Key": api_key})
            assert r.status_code == 200
            bal = r.json()
            assert bal["balance_naira"] == 9_650
            assert bal["total_verifications"] == 2
            assert len(bal["recent_transactions"]) == 2
            assert all(t["type"] == "DEBIT" and t["amount_naira"] == 175 for t in bal["recent_transactions"])
            print(f"PASS  GET  /account/balance -> 200 balance=9650 verifications=2 debits=2")

            # Step 9 — webhook: invalid signature is silently dropped
            bad_payload = json.dumps({
                "transaction_reference": f"WH_BAD_{uuid4().hex[:6]}",
                "principal_amount": "5000",
                "customer_identifier": str(client_id),
            }).encode()
            refs_used.append(json.loads(bad_payload)["transaction_reference"])
            r = await http.post(
                "/webhook/squad",
                content=bad_payload,
                headers={"x-squad-encrypted-body": "DEADBEEF", "content-type": "application/json"},
            )
            assert r.status_code == 200
            print("PASS  POST /webhook/squad (bad sig) -> 200 silent")

            # Step 10 — webhook: valid signature credits balance
            good_ref = f"WH_OK_{uuid4().hex[:8]}"
            refs_used.append(good_ref)
            good_payload = json.dumps({
                "transaction_reference": good_ref,
                "virtual_account_number": "0123456789",
                "principal_amount": "20000.00",
                "settled_amount": "19850.00",
                "customer_identifier": str(client_id),
                "channel": "transfer",
            }).encode()
            r = await http.post(
                "/webhook/squad",
                content=good_payload,
                headers={"x-squad-encrypted-body": sign(good_payload), "content-type": "application/json"},
            )
            assert r.status_code == 200
            async with AsyncSessionLocal() as db:
                cli = await queries.get_client_by_id(db, client_id)
                assert cli.balance_naira == 9_650 + 20_000
            print("PASS  POST /webhook/squad (valid sig) -> 200 balance=29650")

            # Step 11 — webhook idempotency: re-send same payload, balance unchanged
            r = await http.post(
                "/webhook/squad",
                content=good_payload,
                headers={"x-squad-encrypted-body": sign(good_payload), "content-type": "application/json"},
            )
            assert r.status_code == 200
            async with AsyncSessionLocal() as db:
                cli = await queries.get_client_by_id(db, client_id)
                assert cli.balance_naira == 29_650
            print("PASS  POST /webhook/squad (replay)   -> 200 idempotent balance=29650")

            # Step 12 — fund (best effort: requires working sandbox keys)
            r = await http.post("/account/fund", json={"amount_naira": 1000}, headers={"X-API-Key": api_key})
            if r.status_code == 200:
                fund = r.json()
                print(f"PASS  POST /account/fund   -> 200 payment_link={fund['payment_link'][:60]}...")
            else:
                print(f"SKIP  POST /account/fund   -> {r.status_code} (Squad sandbox unavailable)")
        finally:
            await cleanup(client_id, refs_used)

    print("\nALL SMOKE STEPS PASSED")


if __name__ == "__main__":
    asyncio.run(run())
