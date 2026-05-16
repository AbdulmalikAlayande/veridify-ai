"""Stubs — David fills these in. Each stub names exactly what to test."""

import pytest


@pytest.mark.asyncio
async def test_create_client_persists_row():
    pass


@pytest.mark.asyncio
async def test_get_client_by_email_returns_match():
    pass


@pytest.mark.asyncio
async def test_get_client_by_email_returns_none_when_missing():
    pass


@pytest.mark.asyncio
async def test_update_client_squad_info_sets_all_four_fields():
    pass


@pytest.mark.asyncio
async def test_deduct_balance_returns_before_and_after():
    pass


@pytest.mark.asyncio
async def test_deduct_balance_raises_when_insufficient():
    pass


@pytest.mark.asyncio
async def test_deduct_balance_is_atomic_under_concurrent_writes():
    pass


@pytest.mark.asyncio
async def test_create_api_key_links_to_client():
    pass


@pytest.mark.asyncio
async def test_get_client_by_api_key_hash_ignores_inactive_keys():
    pass


@pytest.mark.asyncio
async def test_get_client_by_api_key_hash_ignores_inactive_clients():
    pass


@pytest.mark.asyncio
async def test_update_api_key_last_used_sets_timestamp():
    pass


@pytest.mark.asyncio
async def test_get_cached_verification_returns_fresh_match():
    pass


@pytest.mark.asyncio
async def test_get_cached_verification_returns_none_when_expired():
    pass


@pytest.mark.asyncio
async def test_get_cached_verification_ignores_other_clients():
    pass


@pytest.mark.asyncio
async def test_create_verification_sets_cache_expires_at_24h():
    pass


@pytest.mark.asyncio
async def test_update_verification_transaction_id_links_transaction():
    pass


@pytest.mark.asyncio
async def test_create_transaction_persists_row():
    pass


@pytest.mark.asyncio
async def test_get_transactions_by_client_orders_desc():
    pass


@pytest.mark.asyncio
async def test_transaction_exists_by_idempotency_key_detects_duplicate():
    pass


@pytest.mark.asyncio
async def test_create_payment_intent_default_status_pending():
    pass


@pytest.mark.asyncio
async def test_complete_payment_intent_sets_completed_at():
    pass


@pytest.mark.asyncio
async def test_log_webhook_extracts_event_and_ref():
    pass


@pytest.mark.asyncio
async def test_log_webhook_records_invalid_signature():
    pass


@pytest.mark.asyncio
async def test_update_webhook_log_only_sets_provided_fields():
    pass


@pytest.mark.asyncio
async def test_get_client_by_squad_customer_id_returns_match():
    pass
