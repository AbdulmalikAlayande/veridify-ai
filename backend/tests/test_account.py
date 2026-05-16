"""Account-route test stubs. David fills these in."""

import pytest


@pytest.mark.asyncio
async def test_create_account_returns_201(client):
    pass


@pytest.mark.asyncio
async def test_create_account_returns_api_key(client):
    pass


@pytest.mark.asyncio
async def test_create_account_returns_squad_va_when_keys_configured(client):
    pass


@pytest.mark.asyncio
async def test_create_account_duplicate_email_returns_409(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_create_account_invalid_email_returns_422(client):
    pass


@pytest.mark.asyncio
async def test_get_balance_without_api_key_returns_422(client):
    pass


@pytest.mark.asyncio
async def test_get_balance_with_invalid_key_returns_401(client):
    pass


@pytest.mark.asyncio
async def test_get_balance_with_valid_key_returns_zero(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_get_balance_lists_recent_transactions(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_fund_account_returns_payment_link(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_fund_account_amount_below_100_returns_422(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_fund_account_amount_above_1m_returns_422(client, registered_client):
    pass
