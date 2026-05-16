"""Squad webhook test stubs. David fills these in.

Use ``hmac.new(SECRET.encode(), body, hashlib.sha512).hexdigest().upper()`` to forge
a valid signature; SECRET = SQUAD_WEBHOOK_SECRET or SQUAD_SECRET_KEY.
"""

import pytest


@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_200(client):
    pass


@pytest.mark.asyncio
async def test_webhook_invalid_signature_does_not_credit_balance(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_webhook_invalid_signature_is_logged(client):
    pass


@pytest.mark.asyncio
async def test_webhook_valid_signature_credits_balance(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_webhook_valid_signature_creates_credit_transaction(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_webhook_duplicate_transaction_ref_is_idempotent(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_webhook_unknown_customer_returns_200_no_credit(client):
    pass


@pytest.mark.asyncio
async def test_webhook_malformed_json_returns_200(client):
    pass


@pytest.mark.asyncio
async def test_webhook_missing_amount_returns_200_no_credit(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_webhook_completes_matching_payment_intent(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_webhook_logs_all_events(client, registered_client):
    pass
