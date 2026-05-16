"""Squad webhook payload schemas.

Squad sends a FLAT JSON payload for virtual-account credits (no Event/Body wrapper):
  {
    "transaction_reference": "20240515ABC123",
    "virtual_account_number": "0123456789",
    "principal_amount": "17500.00",
    "settled_amount": "17400.00",
    "fee_charged": "100.00",
    "transaction_date": "2024-05-15T10:30:00Z",
    "customer_identifier": "<our client.id>",
    "channel": "transfer"
  }

We only consume fields we need. Pydantic ignores extras by default unless told otherwise.
"""

from pydantic import BaseModel


class SquadWebhookPayload(BaseModel):
    transaction_reference: str | None = None
    virtual_account_number: str | None = None
    principal_amount: str | float | None = None
    settled_amount: str | float | None = None
    fee_charged: str | float | None = None
    transaction_date: str | None = None
    customer_identifier: str | None = None
    channel: str | None = None


class WebhookResponse(BaseModel):
    status: str
