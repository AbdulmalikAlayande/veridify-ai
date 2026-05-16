"""Shared fixtures for the Veridifi test suite.

David: this file gives you a live ASGI client and a pre-registered Squad-less
account. Use them in your test bodies — you do not need to start a server.

Run the suite with:
    .venv/Scripts/python.exe -m pytest tests/ -v
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Swap the production pooled engine for a NullPool one BEFORE the app imports.
# Pooled asyncpg connections are bound to whatever event loop created them; pytest
# spins up its own loop and reusing the pooled conns triggers
# `InterfaceError: cannot perform operation: another operation is in progress`.
from app.config import get_settings  # noqa: E402
from app.db import database as _database  # noqa: E402

_settings = get_settings()
_database.engine = create_async_engine(
    _settings.database_url,
    echo=False,
    poolclass=NullPool,
)
_database.AsyncSessionLocal = async_sessionmaker(
    _database.engine, expire_on_commit=False, autoflush=False
)

from app.db.database import AsyncSessionLocal  # noqa: E402
from app.db.models import (  # noqa: E402
    ApiKey,
    Client,
    PaymentIntent,
    Transaction,
    Verification,
    WebhookLog,
)
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP client that calls the FastAPI app in-process (no real network)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_client(client: AsyncClient):
    """Creates a fresh client + API key, yields the response body, cleans up after."""
    email = f"pytest-{uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/account/create",
        json={"name": "Pytest Client", "email": email},
    )
    body = response.json()
    body["_email"] = email
    yield body

    client_id = UUID(body["client_id"])
    async with AsyncSessionLocal() as db:
        await db.execute(delete(WebhookLog).where(WebhookLog.matched_client_id == client_id))
        await db.execute(delete(Transaction).where(Transaction.client_id == client_id))
        await db.execute(delete(Verification).where(Verification.client_id == client_id))
        await db.execute(delete(PaymentIntent).where(PaymentIntent.client_id == client_id))
        await db.execute(delete(ApiKey).where(ApiKey.client_id == client_id))
        await db.execute(delete(Client).where(Client.id == client_id))
        await db.commit()


@pytest.fixture
def png_image_bytes() -> bytes:
    """Tiny valid PNG. Use with ``files={'image': ('t.png', png_image_bytes, 'image/png')}``."""
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (32, 32), "purple").save(buf, format="PNG")
    return buf.getvalue()
