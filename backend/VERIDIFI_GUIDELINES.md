# VERIDIFI — PROJECT GUIDELINES
## Coding Standards, Patterns, and Principles for the Backend Agent
### Read this after VERIDIFI_PROJECT_SPECIFICATIONS.md
### Read this before VERIDIFI_BUILD_ORDER.md

---

> These guidelines govern HOW you write the code. The specs tell you WHAT to build.
> The build order tells you in WHAT SEQUENCE. All three documents work together.
> Violating these guidelines produces code that cannot be maintained, cannot be
> debugged on demo day, and cannot be handed off to another agent mid-build.

---

## 1. LANGUAGE AND RUNTIME

- Python 3.11+
- FastAPI 0.111+
- SQLAlchemy 2.0+ (use the 2.0 async style — not the legacy 1.x style)
- Pydantic v2 (FastAPI 0.111 uses Pydantic v2 — do not use v1 syntax)
- asyncpg for PostgreSQL driver
- Alembic for migrations

Do not use synchronous database calls anywhere. Every database operation is async.
Do not use `Session` — use `AsyncSession` everywhere.

---

## 2. PROJECT CONFIGURATION — config.py

Use `pydantic-settings` with `BaseSettings`. All configuration comes from environment
variables. No hardcoded values anywhere in the codebase.

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Veridifi"
    secret_key: str

    database_url: str
    squad_secret_key: str
    squad_base_url: str = "https://sandbox-api-d.squadco.com"
    squad_webhook_secret: str

    model_path: str = "./models/dual_branch_v1.keras"
    mock_inference: bool = True

    verification_cost_naira: int = 175
    rate_limit_per_minute: int = 60
    max_image_size_mb: int = 10
    temp_file_dir: str = "/tmp/veridifi"
    image_retention_seconds: int = 60
    cache_ttl_hours: int = 24

    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

Use `Depends(get_settings)` in routes when needed, but prefer injecting settings
at the service layer so routes stay clean.

---

## 3. DATABASE PATTERNS

### Connection setup (database.py)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.database_url, echo=False, pool_size=10)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Query pattern
All queries go in `db/queries.py`. Routes never write SQL. Services call queries.
Never put query logic in routes or directly in service functions — centralise it.

```python
# db/queries.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Client, ApiKey

async def get_client_by_api_key_hash(db: AsyncSession, key_hash: str) -> Client | None:
    result = await db.execute(
        select(Client)
        .join(ApiKey, Client.id == ApiKey.client_id)
        .where(ApiKey.key_hash == key_hash)
        .where(ApiKey.is_active == True)
        .where(Client.is_active == True)
    )
    return result.scalar_one_or_none()
```

### Transaction pattern for balance deduction
Balance deduction MUST be atomic. Use SELECT FOR UPDATE to prevent race conditions
if two requests come in simultaneously for the same client.

```python
async def deduct_balance(db: AsyncSession, client_id: UUID, amount: int) -> tuple[int, int]:
    """
    Returns (balance_before, balance_after).
    Raises InsufficientBalanceError if balance < amount.
    """
    result = await db.execute(
        select(Client).where(Client.id == client_id).with_for_update()
    )
    client = result.scalar_one()

    if client.balance_naira < amount:
        raise InsufficientBalanceError(client.balance_naira)

    balance_before = client.balance_naira
    balance_after = balance_before - amount
    client.balance_naira = balance_after
    await db.flush()  # flush but don't commit — caller commits

    return balance_before, balance_after
```

---

## 4. MODELS — SQLAlchemy ORM

Use the SQLAlchemy 2.0 declarative style with type annotations. Every model in
`db/models.py`. Use UUID primary keys everywhere. Use TIMESTAMPTZ (timezone-aware).

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    squad_virtual_account_ref: Mapped[str | None] = mapped_column(String(255))
    squad_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    squad_account_number: Mapped[str | None] = mapped_column(String(20))
    squad_bank_name: Mapped[str | None] = mapped_column(String(100))
    balance_naira: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 5. PYDANTIC SCHEMAS

All request/response shapes in `/schemas`. Never expose ORM models directly
in responses — always convert through Pydantic schemas.

Use `model_config = ConfigDict(from_attributes=True)` on all response schemas
so `.model_validate(orm_object)` works cleanly.

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class VerifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_id: UUID
    trust_score: int
    verdict: str
    confidence: str
    processing_ms: int
    cached: bool
    billed_naira: int
    balance_remaining: int
    breakdown: dict
```

---

## 6. ROUTE STRUCTURE — THIN ROUTES

Routes are thin. They validate input, call a service function, return a response.
No business logic in routes. No database calls in routes. No Squad calls in routes.

```python
# routes/verify.py
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.middleware.auth import get_current_client
from app.services import verification as verification_service
from app.schemas.verify import VerifyResponse

router = APIRouter()

@router.post("/verify", response_model=VerifyResponse)
async def verify_image(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    client = Depends(get_current_client),
):
    return await verification_service.process_verification(db, client, image)
```

---

## 7. MIDDLEWARE — AUTH

Auth middleware reads `X-API-Key`, hashes it with SHA-256, looks it up in the
`api_keys` table. Implemented as a FastAPI dependency, not a Starlette middleware
class — this gives clean per-route control.

```python
# middleware/auth.py
import hashlib
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db import queries

async def get_current_client(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    client = await queries.get_client_by_api_key_hash(db, key_hash)
    if not client:
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_API_KEY", "message": "Invalid or revoked API key"}
        )
    await queries.update_api_key_last_used(db, key_hash)
    return client
```

---

## 8. WEBHOOK SECURITY — CRITICAL, DO NOT SKIP

The Squad webhook endpoint MUST implement HMAC-SHA512 verification.
Without it, anyone can POST fake payment confirmations and credit arbitrary balances.

```python
import hmac
import hashlib

def verify_squad_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        raw_body,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

Use `hmac.compare_digest` — NOT `==`. Constant-time comparison prevents timing attacks.

The route MUST receive the raw body BEFORE FastAPI parses it as JSON.

```python
@router.post("/webhook/squad")
async def squad_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")
    is_valid = verify_squad_signature(raw_body, signature, settings.squad_webhook_secret)
    # Log REGARDLESS of validity — this is your debugging tool on demo day
    await queries.log_webhook(db, raw_body, signature, is_valid)
    if not is_valid:
        return {"status": "received"}  # Silent rejection — NEVER return 4xx to Squad
    payload = json.loads(raw_body)
    # Continue processing...
```

---

## 9. INFERENCE SERVICE — MOCK AND REAL

The mock MUST return DETERMINISTIC results based on the image hash.
Same image → same score every time. Non-determinism breaks Peter's frontend
and breaks David's tests.

```python
# services/inference.py
import hashlib
import time
from app.config import get_settings

settings = get_settings()

async def run_inference(image_bytes: bytes, image_hash: str) -> dict:
    if settings.mock_inference:
        return _mock_inference(image_hash)
    return await _real_inference(image_bytes)

def _mock_inference(image_hash: str) -> dict:
    # Deterministic score derived from hash
    seed = int(image_hash[:8], 16) % 100
    trust_score = seed
    start = time.time()
    time.sleep(0.3)
    processing_ms = int((time.time() - start) * 1000)

    if trust_score >= 70:
        verdict = "AUTHENTIC"
        confidence = "HIGH" if trust_score > 85 else "MEDIUM"
    elif trust_score >= 35:
        verdict = "MANIPULATED"
        confidence = "HIGH" if trust_score < 40 else "MEDIUM"
    else:
        verdict = "SYNTHETIC"
        confidence = "HIGH" if trust_score < 20 else "MEDIUM"

    return {
        "trust_score": trust_score,
        "verdict": verdict,
        "confidence": confidence,
        "spatial_score": min(trust_score + 3, 100),
        "frequency_score": max(trust_score - 3, 0),
        "processing_ms": processing_ms,
    }

async def _real_inference(image_bytes: bytes) -> dict:
    # This stub is replaced when Abdulmalik's model is ready
    # Model is loaded at startup in main.py — never load it here
    raise NotImplementedError("Set MOCK_INFERENCE=false and provide MODEL_PATH")
```

---

## 10. IMAGE HANDLING — PRIVACY CONTRACT

Images never persist beyond inference. This is a promise made to judges.

```python
import os
import uuid
from pathlib import Path

async def save_temp_image(image_bytes: bytes, ext: str) -> Path:
    temp_dir = Path(settings.temp_file_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"{uuid.uuid4()}.{ext}"
    path.write_bytes(image_bytes)
    return path

def delete_temp_image(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass  # Never let cleanup failure propagate
```

Always use try/finally:
```python
temp_path = await save_temp_image(image_bytes, ext)
try:
    result = await run_inference(image_bytes, image_hash)
finally:
    delete_temp_image(temp_path)  # Always runs — even on inference failure
```

---

## 11. API KEY GENERATION

```python
import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """
    Returns (raw_key, key_hash).
    raw_key: returned to client ONCE — never stored in database.
    key_hash: stored in api_keys table — used for all lookups.
    """
    raw = "vrf_sk_live_" + secrets.token_hex(32)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, key_hash
```

---

## 12. SQUAD SERVICE — HTTP CLIENT

Use `httpx` for async HTTP. Never use `requests` (synchronous).

```python
# services/squad.py
import httpx
from app.config import get_settings

settings = get_settings()

async def create_virtual_account(client_email: str, client_name: str) -> dict:
    async with httpx.AsyncClient() as http:
        response = await http.post(
            f"{settings.squad_base_url}/virtual-account",
            headers={
                "Authorization": f"Bearer {settings.squad_secret_key}",
                "Content-Type": "application/json",
            },
            json={
                "customer_identifier": client_email,
                "display_name": f"VERIDIFI/{client_name.upper()}",
                "bvn": "",
                "mobile_num": "",
                "beneficiary_account": "",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

async def generate_payment_link(amount_naira: int) -> dict:
    amount_kobo = amount_naira * 100
    async with httpx.AsyncClient() as http:
        response = await http.post(
            f"{settings.squad_base_url}/payment_link/otp",
            headers={
                "Authorization": f"Bearer {settings.squad_secret_key}",
                "Content-Type": "application/json",
            },
            json={
                "amount": amount_kobo,
                "currency_id": "NGN",
                "name": "Veridifi Balance Top-up",
                "description": "Fund your Veridifi verification account",
                "redirect_link": "https://veridifi.onrender.com/payment/success",
                "return_msg": "Payment successful — balance updating shortly",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
```

Wrap all Squad calls in try/except. Squad being down should not crash the API.

---

## 13. MAIN.PY STRUCTURE

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import verify, account, webhook
from app.exceptions import VeridifiError
from fastapi.responses import JSONResponse

settings = get_settings()
model = None  # Loaded during startup if MOCK_INFERENCE=false

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    if not settings.mock_inference:
        import tensorflow as tf
        model = tf.keras.models.load_model(settings.model_path)
        print(f"[STARTUP] Model loaded: {settings.model_path}")
    else:
        print("[STARTUP] Mock inference mode — no model loaded")
    yield
    print("[SHUTDOWN] Veridifi API shutting down")

app = FastAPI(
    title="Veridifi API",
    description="AI-powered image authenticity verification",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(VeridifiError)
async def veridifi_error_handler(request, exc: VeridifiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message, "detail": exc.detail}
    )

app.include_router(verify.router, tags=["Verification"])
app.include_router(account.router, prefix="/account", tags=["Account"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "mode": "mock" if settings.mock_inference else "live",
        "version": "1.0.0"
    }
```

---

## 14. REQUIREMENTS.TXT

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
pydantic-settings==2.2.1
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
httpx==0.27.0
python-multipart==0.0.9
python-dotenv==1.0.1
opencv-python-headless==4.9.0.80
numpy==1.26.4
pillow==10.3.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

---

## 15. DOCKERFILE

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /tmp/veridifi

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 16. ERROR HANDLING

```python
# app/exceptions.py
class VeridifiError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int, detail: dict = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}

class InsufficientBalanceError(VeridifiError):
    def __init__(self, current_balance: int, payment_link: str = None):
        super().__init__(
            "INSUFFICIENT_BALANCE",
            "Insufficient balance for verification",
            402,
            {"balance_naira": current_balance, "verification_cost_naira": 175, "payment_link": payment_link}
        )

class InvalidApiKeyError(VeridifiError):
    def __init__(self):
        super().__init__("INVALID_API_KEY", "Invalid or revoked API key", 401)

class ImageTooLargeError(VeridifiError):
    def __init__(self, size_mb: float):
        super().__init__("IMAGE_TOO_LARGE", f"Image size {size_mb:.1f}MB exceeds 10MB limit", 413)

class UnsupportedImageTypeError(VeridifiError):
    def __init__(self, mime_type: str):
        super().__init__("UNSUPPORTED_IMAGE_TYPE", f"Image type {mime_type} is not supported", 415)
```

---

## 17. HANDOFF PROTOCOL — FOR THE NEXT AGENT

If you are picking up this build mid-way through because the previous agent ran
out of tokens, do the following in order:

1. Read `VERIDIFI_PROJECT_SPECIFICATIONS.md` fully — understand what is being built
2. Read this file fully — understand how to write the code
3. Read `VERIDIFI_BUILD_ORDER.md` fully — understand the sequence
4. Audit what exists:
   ```bash
   find /path/to/backend -name "*.py" -not -path "*/alembic/*" | sort
   ```
5. Check which step in BUILD_ORDER is the last completed one
6. Run the existing tests to confirm they pass:
   ```bash
   cd backend && pytest tests/ -v
   ```
7. Continue from the next incomplete step
8. Never change existing function signatures without checking all callers
9. Never change the database schema — it is final and locked
10. Never change environment variable names — config.py is the source of truth
11. After completing each step, run the tests before moving to the next
