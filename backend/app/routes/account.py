from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Client
from app.middleware.auth import get_current_client
from app.schemas.account import (
    BalanceResponse,
    CreateAccountRequest,
    CreateAccountResponse,
    FundAccountRequest,
    FundAccountResponse,
)
from app.services import account as account_service

router = APIRouter()


@router.post("/create", response_model=CreateAccountResponse, status_code=201)
async def create_account(
    body: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
):
    return await account_service.create_account(db, body.name, body.email)


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    return await account_service.get_balance(db, client)


@router.post("/fund", response_model=FundAccountResponse)
async def fund_account(
    body: FundAccountRequest,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    return await account_service.fund_account(db, client, body.amount_naira)
