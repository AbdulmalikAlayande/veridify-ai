"""Verification-route test stubs. David fills these in."""

import pytest


@pytest.mark.asyncio
async def test_verify_without_api_key_returns_422(client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_with_invalid_key_returns_401(client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_with_zero_balance_returns_402(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_402_includes_payment_link_when_squad_configured(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_with_balance_returns_200(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_response_has_required_fields(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_deducts_175_from_balance(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_same_image_twice_returns_cached_true(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_cached_call_still_charges_175(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_oversized_image_returns_413(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_verify_non_image_file_returns_415(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_get_verification_by_id_returns_200_for_owner(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_get_verification_by_id_returns_404_for_other_client(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_get_verification_unknown_id_returns_404(client, registered_client):
    pass


@pytest.mark.asyncio
async def test_verify_rate_limit_60_per_minute(client, registered_client, png_image_bytes):
    pass


@pytest.mark.asyncio
async def test_verify_deletes_temp_image_immediately(client, registered_client, png_image_bytes):
    """Privacy contract: no PNG/JPEG/WEBP should remain in /tmp/veridifi after the call."""
    pass
