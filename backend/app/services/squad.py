"""Squad payment gateway integration.

Endpoints used:
  - POST /virtual-account/business  → create per-client dedicated VA (B2B)
  - POST /transaction/initiate      → one-shot top-up payment link

Both calls expect `Authorization: Bearer <secret_key>` and JSON bodies.
Amounts are sent in kobo (naira × 100).

Webhook signing is HMAC-SHA512(secret, raw_body) → hex UPPERCASE in the
`x-squad-encrypted-body` header. See verify_squad_signature().
"""

from __future__ import annotations

import hmac
import hashlib
import uuid
from typing import Any

import httpx

from app.config import get_settings
from app.exceptions import SquadAPIError

settings = get_settings()

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def _require_key() -> str:
    key = settings.squad_secret_key.strip()
    if not key:
        raise SquadAPIError(
            "Squad API key not configured — set SQUAD_SECRET_KEY in .env"
        )
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{settings.squad_base_url.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            resp = await http.post(url, headers=_headers(), json=body)
    except httpx.HTTPError as exc:
        raise SquadAPIError(f"Squad request failed: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError:
        payload = {"raw": resp.text}

    if resp.status_code >= 400 or not payload.get("success", True):
        raise SquadAPIError(
            f"Squad {path} returned {resp.status_code}",
            upstream_status=resp.status_code,
            upstream_body=payload,
        )
    return payload


async def create_virtual_account(client_id: str, client_email: str, client_name: str) -> dict:
    """Create a B2B dedicated virtual account for this client.

    `client_id` is sent as `customer_identifier` so we can match webhook events
    back to the client without a separate lookup.
    """
    body = {
        "customer_identifier": str(client_id),
        "business_name": client_name,
        "mobile_num": settings.squad_test_mobile,
        "bvn": settings.squad_test_bvn,
        "beneficiary_account": settings.squad_beneficiary_account,
    }
    return await _post("/virtual-account/business", body)


async def generate_payment_link(amount_naira: int, client_email: str) -> dict:
    """Generate a one-shot checkout URL for a top-up of `amount_naira`.

    Returns the parsed Squad response (which contains `data.checkout_url` and
    the `transaction_ref` we generated locally so the webhook can correlate).
    """
    transaction_ref = f"vrf_{uuid.uuid4().hex}"
    body = {
        "amount": amount_naira * 100,  # kobo
        "email": client_email,
        "currency": settings.squad_currency,
        "initiate_type": "inline",
        "transaction_ref": transaction_ref,
    }
    response = await _post("/transaction/initiate", body)
    # Surface our generated ref so the caller can persist it on payment_intent.
    response["_transaction_ref"] = transaction_ref
    return response


def verify_squad_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Constant-time HMAC-SHA512 compare. Squad sends hex UPPERCASE."""
    if not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest().upper()
    return hmac.compare_digest(expected, signature.strip().upper())
