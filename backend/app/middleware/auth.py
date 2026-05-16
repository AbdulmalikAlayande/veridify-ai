import hashlib

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import queries
from app.db.database import get_db
from app.db.models import Client
from app.exceptions import InvalidApiKeyError


async def get_current_client(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Client:
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    client = await queries.get_client_by_api_key_hash(db, key_hash)
    if client is None:
        raise InvalidApiKeyError()
    await queries.update_api_key_last_used(db, key_hash)
    await db.commit()
    return client
