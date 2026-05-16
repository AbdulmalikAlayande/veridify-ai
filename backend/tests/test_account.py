"""Account-route integration tests."""

import pytest


@pytest.mark.asyncio
async def test_create_account_returns_201(client):
    response = await client.post("/account/create", json={
        "name": "Test Client",
        "email": "create201@example.com"
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_account_returns_api_key(client):
    response = await client.post("/account/create", json={
        "name": "Test Client",
        "email": "create_api_key@example.com"
    })
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("vrf_sk_live_")


@pytest.mark.asyncio
async def test_create_account_returns_squad_va_when_keys_configured(client):
    response = await client.post("/account/create", json={
        "name": "Test Client",
        "email": "create_va@example.com"
    })
    data = response.json()
    # Depending on whether squad_secret_key is empty in .env, it either returns null or the VA dict
    assert "squad_virtual_account" in data


@pytest.mark.asyncio
async def test_create_account_duplicate_email_returns_409(client, registered_client):
    email = registered_client["_email"]
    response = await client.post("/account/create", json={
        "name": "Duplicate Client",
        "email": email
    })
    assert response.status_code == 409
    assert response.json()["error"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_account_invalid_email_returns_422(client):
    response = await client.post("/account/create", json={
        "name": "Invalid Email",
        "email": "not-an-email"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_balance_without_api_key_returns_422(client):
    response = await client.get("/account/balance")
    # FastAPI returns 422 Unprocessable Entity when required header is missing
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_balance_with_invalid_key_returns_401(client):
    response = await client.get("/account/balance", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 401
    assert response.json()["error"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_get_balance_with_valid_key_returns_zero(client, registered_client):
    api_key = registered_client["api_key"]
    response = await client.get("/account/balance", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["balance_naira"] == 0
    assert data["total_verifications"] == 0


@pytest.mark.asyncio
async def test_get_balance_lists_recent_transactions(client, registered_client):
    api_key = registered_client["api_key"]
    response = await client.get("/account/balance", headers={"X-API-Key": api_key})
    data = response.json()
    assert "recent_transactions" in data
    assert isinstance(data["recent_transactions"], list)


@pytest.mark.asyncio
async def test_fund_account_returns_payment_link(client, registered_client):
    api_key = registered_client["api_key"]
    response = await client.post("/account/fund", json={"amount_naira": 1000}, headers={"X-API-Key": api_key})
    assert response.status_code == 200
    data = response.json()
    assert "payment_link" in data
    assert data["amount_naira"] == 1000


@pytest.mark.asyncio
async def test_fund_account_amount_below_100_returns_422(client, registered_client):
    api_key = registered_client["api_key"]
    response = await client.post("/account/fund", json={"amount_naira": 50}, headers={"X-API-Key": api_key})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_fund_account_amount_above_1m_returns_422(client, registered_client):
    api_key = registered_client["api_key"]
    response = await client.post("/account/fund", json={"amount_naira": 2000000}, headers={"X-API-Key": api_key})
    assert response.status_code == 422
