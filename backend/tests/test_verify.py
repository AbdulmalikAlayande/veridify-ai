"""Verification-route integration tests."""

import pytest
import os
from uuid import UUID
from app.db.database import AsyncSessionLocal
from app.db import queries


async def credit_client_balance(client_id_str: str, amount: int):
    client_id = UUID(client_id_str)
    async with AsyncSessionLocal() as db:
        client = await queries.get_client_by_id(db, client_id)
        if client:
            await queries.update_client_balance(db, client.id, client.balance_naira + amount)
            await db.commit()


@pytest.mark.asyncio
async def test_verify_without_api_key_returns_422(client, png_image_bytes):
    response = await client.post("/verify", files={"image": ("test.png", png_image_bytes, "image/png")})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_with_invalid_key_returns_401(client, png_image_bytes):
    response = await client.post(
        "/verify",
        headers={"X-API-Key": "invalid_key"},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_with_zero_balance_returns_402(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    assert response.status_code == 402
    assert response.json()["error"] == "INSUFFICIENT_BALANCE"


@pytest.mark.asyncio
async def test_verify_402_includes_payment_link_when_squad_configured(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    data = response.json()
    assert "payment_link" in data.get("detail", {})


@pytest.mark.asyncio
async def test_verify_with_balance_returns_200(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "trust_score" in data
    assert "verdict" in data
    assert data["billed_naira"] == 175


@pytest.mark.asyncio
async def test_verify_response_has_required_fields(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    data = response.json()
    expected_fields = [
        "verification_id", "trust_score", "verdict", "confidence",
        "processing_ms", "cached", "billed_naira", "balance_remaining", "breakdown"
    ]
    for field in expected_fields:
        assert field in data


@pytest.mark.asyncio
async def test_verify_deducts_175_from_balance(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    data = response.json()
    assert data["balance_remaining"] == 1000 - 175


@pytest.mark.asyncio
async def test_verify_same_image_twice_returns_cached_true(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    
    response2 = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    data2 = response2.json()
    assert data2["cached"] is True


@pytest.mark.asyncio
async def test_verify_cached_call_still_charges_175(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    
    response2 = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    data2 = response2.json()
    assert data2["billed_naira"] == 175
    assert data2["balance_remaining"] == 1000 - 350


@pytest.mark.asyncio
async def test_verify_oversized_image_returns_413(client, registered_client):
    api_key = registered_client["api_key"]
    oversized = b"0" * (11 * 1024 * 1024) # 11 MB
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("large.png", oversized, "image/png")}
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_verify_non_image_file_returns_415(client, registered_client):
    api_key = registered_client["api_key"]
    response = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_get_verification_by_id_returns_200_for_owner(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    post_res = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    ver_id = post_res.json()["verification_id"]
    
    get_res = await client.get(f"/verify/{ver_id}", headers={"X-API-Key": api_key})
    assert get_res.status_code == 200
    assert get_res.json()["verification_id"] == ver_id


@pytest.mark.asyncio
async def test_get_verification_by_id_returns_404_for_other_client(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    post_res = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    ver_id = post_res.json()["verification_id"]
    
    # Create another client
    res2 = await client.post("/account/create", json={"name": "C2", "email": "c2ver@test.com"})
    api_key2 = res2.json()["api_key"]
    
    get_res = await client.get(f"/verify/{ver_id}", headers={"X-API-Key": api_key2})
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_get_verification_unknown_id_returns_404(client, registered_client):
    api_key = registered_client["api_key"]
    import uuid
    get_res = await client.get(f"/verify/{uuid.uuid4()}", headers={"X-API-Key": api_key})
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_verify_rate_limit_60_per_minute(client, registered_client, png_image_bytes):
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 20000)
    
    # Send 61 requests to trip the limiter
    # Note: executing 61 calls over ASGI transport is fast
    for _ in range(60):
        res = await client.post(
            "/verify",
            headers={"X-API-Key": api_key},
            files={"image": ("test.png", png_image_bytes, "image/png")}
        )
        assert res.status_code == 200
    
    res_61 = await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    assert res_61.status_code == 429


@pytest.mark.asyncio
async def test_verify_deletes_temp_image_immediately(client, registered_client, png_image_bytes):
    """Privacy contract: no PNG/JPEG/WEBP should remain in /tmp/veridifi after the call."""
    api_key = registered_client["api_key"]
    await credit_client_balance(registered_client["client_id"], 1000)
    
    from app.config import get_settings
    settings = get_settings()
    
    before_files = []
    if os.path.exists(settings.temp_file_dir):
        before_files = os.listdir(settings.temp_file_dir)
        
    await client.post(
        "/verify",
        headers={"X-API-Key": api_key},
        files={"image": ("test.png", png_image_bytes, "image/png")}
    )
    
    after_files = []
    if os.path.exists(settings.temp_file_dir):
        after_files = os.listdir(settings.temp_file_dir)
    
    assert len(before_files) == len(after_files)
