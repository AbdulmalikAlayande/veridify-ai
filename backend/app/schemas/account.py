from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateAccountRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class SquadVirtualAccount(BaseModel):
    account_number: str
    bank_name: str
    account_name: str


class CreateAccountResponse(BaseModel):
    client_id: UUID
    api_key: str
    message: str
    squad_virtual_account: SquadVirtualAccount | None
    balance_naira: int


class FundAccountRequest(BaseModel):
    amount_naira: int = Field(..., ge=100, le=1_000_000)


class FundAccountResponse(BaseModel):
    payment_link: str
    amount_naira: int
    expires_in_hours: int
    message: str


class TransactionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str
    amount_naira: int
    description: str | None
    balance_after: int
    created_at: datetime


class BalanceResponse(BaseModel):
    balance_naira: int
    total_verifications: int
    recent_transactions: list[TransactionItem]
