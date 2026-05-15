# VERIDIFI — BUILD ORDER
## Exact Step-by-Step Instructions for Claude Code / Codex
### Read VERIDIFI_PROJECT_SPECIFICATIONS.md first
### Read VERIDIFI_GUIDELINES.md second
### Execute this file third — in order, no skipping

---

> YOU ARE BUILDING THE VERIDIFI BACKEND FROM SCRATCH.
> The GitHub repo `veridify` exists. The `/backend` folder exists but is empty.
> You are filling it. Every step below is a discrete unit of work.
> Complete each step fully before moving to the next.
> After each step, confirm the code runs before proceeding.

---

## BEFORE YOU START — READ THIS

**What Veridifi is:** A FastAPI REST API that accepts an image and returns whether
it is AUTHENTIC, MANIPULATED, or AI-SYNTHETIC. Each call costs ₦175, deducted from
a pre-funded Squad Virtual Account balance.

**The team context:**
- You are building what Abdulmalik (backend lead) owns
- Peter (frontend) is consuming this API from a React app — he needs the mock running ASAP
- David (QA) will write tests once the foundation is in place
- The ML model is built separately in Google Colab — you build the stub that accepts it

**The one non-negotiable:** Squad API integration must be FUNCTIONAL, not cosmetic.
It is 20% of the judging score and a disqualification gate.

**Current state of environment variables:**
Squad sandbox keys are NOT yet obtained. The `MOCK_INFERENCE=true` env var means
Squad Virtual Account creation will be called but payment processing won't be live
until keys arrive. Build Squad integration code fully — it just won't be testable
end-to-end until keys are in hand.

---

## STEP 0 — INITIALISE THE PROJECT STRUCTURE

Create every folder and every `__init__.py`. This is the full tree.

```bash
cd /path/to/veridify/backend

# Create all directories
mkdir -p app/routes
mkdir -p app/services
mkdir -p app/db
mkdir -p app/middleware
mkdir -p app/schemas
mkdir -p alembic/versions
mkdir -p models
mkdir -p tests

# Create all __init__.py files
touch app/__init__.py
touch app/routes/__init__.py
touch app/services/__init__.py
touch app/db/__init__.py
touch app/middleware/__init__.py
touch app/schemas/__init__.py
touch tests/__init__.py

# Create placeholder for model weights (not committed)
touch models/.gitkeep
```

Create `.gitignore`:
```
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
models/*.keras
models/*.h5
/tmp/
*.egg-info/
dist/
build/
.DS_Store
```

**STEP 0 IS DONE WHEN:** `find . -name "*.py" | head -20` shows all __init__.py
files in place and the directory tree matches the spec.

---

## STEP 1 — requirements.txt AND .env.example

Create `requirements.txt`:
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
aiofiles==23.2.1
```

Create `.env.example` (all keys present, all values empty — shows what is needed):
```bash
# Application
APP_ENV=development
APP_NAME=Veridifi
SECRET_KEY=

# Database — use postgresql+asyncpg:// scheme, NOT postgresql://
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/veridify

# Squad Payment API — get from https://sandbox-dashboard.squadco.com
SQUAD_SECRET_KEY=
SQUAD_BASE_URL=https://sandbox-api-d.squadco.com
SQUAD_WEBHOOK_SECRET=
SQUAD_CURRENCY=NGN

# ML Model
MODEL_PATH=./models/dual_branch_v1.keras
MOCK_INFERENCE=true

# Billing
VERIFICATION_COST_NAIRA=175

# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# File handling
MAX_IMAGE_SIZE_MB=10
TEMP_FILE_DIR=/tmp/veridifi
IMAGE_RETENTION_SECONDS=60

# Cache
CACHE_TTL_HOURS=24

# CORS
ALLOWED_ORIGINS=http://localhost:5173,https://veridify.onrender.com
```

Create `.env` by copying `.env.example`. Fill in `DATABASE_URL` with your local
PostgreSQL connection string. Leave Squad keys empty for now.

Install dependencies:
```bash
pip install -r requirements.txt
```

**STEP 1 IS DONE WHEN:** `pip install -r requirements.txt` completes with no errors.

---

## STEP 2 — app/config.py

Implement the Settings class exactly as shown in VERIDIFI_GUIDELINES.md section 2.

The settings object is the single source of truth for all configuration. Every
service, every query function, and every route that needs a config value gets it
from here. No `os.environ.get()` calls outside of this file.

After writing config.py, verify it loads:
```python
# Quick smoke test — run this in python shell
from app.config import get_settings
s = get_settings()
print(s.mock_inference)  # Should print True
print(s.verification_cost_naira)  # Should print 175
```

**STEP 2 IS DONE WHEN:** `get_settings()` returns a valid Settings object with
no errors and `mock_inference` is `True`.

---

## STEP 3 — app/exceptions.py

Implement all custom exceptions:
- `VeridifiError` (base)
- `InsufficientBalanceError`
- `InvalidApiKeyError`
- `ImageTooLargeError`
- `UnsupportedImageTypeError`
- `InferenceFailedError`
- `SquadAPIError`

See VERIDIFI_GUIDELINES.md section 16 for the pattern. Add `InferenceFailedError`
and `SquadAPIError` following the same pattern.

**STEP 3 IS DONE WHEN:** All exception classes are importable from `app.exceptions`.

---

## STEP 4 — app/db/database.py

Implement the async database engine and session factory. Exact pattern in
VERIDIFI_GUIDELINES.md section 3.

Key requirements:
- Use `postgresql+asyncpg://` scheme in DATABASE_URL
- `pool_size=10`, `max_overflow=20`
- `get_db()` is an async generator used as FastAPI dependency
- Session rolls back on exception, always closes in finally

**STEP 4 IS DONE WHEN:** `from app.db.database import get_db, engine, Base`
imports without error.

---

## STEP 5 — app/db/models.py

Implement all 6 SQLAlchemy ORM models. These must match the schema in
VERIDIFI_PROJECT_SPECIFICATIONS.md section 5 exactly.

Models to implement:
1. `Client` — maps to `clients` table
2. `ApiKey` — maps to `api_keys` table
3. `Verification` — maps to `verifications` table
4. `Transaction` — maps to `transactions` table
5. `PaymentIntent` — maps to `payment_intents` table
6. `WebhookLog` — maps to `webhook_logs` table

For `WebhookLog`, the `raw_payload` column uses `JSONB` (PostgreSQL-specific).
Import it from `sqlalchemy.dialects.postgresql`.

For the `Verification.transaction_id` column: this is a foreign key to
`transactions.id` but the relationship is circular (transaction also references
verification). Handle this with `use_alter=True` in the ForeignKey constraint,
or set up the constraint post-creation. The simplest approach for the hackathon:
declare `transaction_id` as a plain UUID column without a FK constraint in the ORM
(just a UUID column), and handle the relationship in application code. This avoids
the circular dependency.

Add relationships:
- `Client.api_keys` → list of ApiKey
- `Client.verifications` → list of Verification
- `Client.transactions` → list of Transaction
- `ApiKey.client` → Client
- `Verification.client` → Client
- `Transaction.client` → Client

**STEP 5 IS DONE WHEN:** `from app.db.models import Client, ApiKey, Verification,
Transaction, PaymentIntent, WebhookLog` imports without error.

---

## STEP 6 — ALEMBIC SETUP AND FIRST MIGRATION

Initialise Alembic:
```bash
alembic init alembic
```

Edit `alembic/env.py`:
- Import `Base` from `app.db.database`
- Import all models from `app.db.models` (so Alembic sees them)
- Set `target_metadata = Base.metadata`
- Configure the database URL from the settings object, not from alembic.ini

Edit `alembic.ini`:
- Set `script_location = alembic`
- The database URL should be loaded dynamically from settings in env.py — do not
  hardcode it in alembic.ini

Create and run the first migration:
```bash
# Generate the migration
alembic revision --autogenerate -m "initial schema"

# Apply it
alembic upgrade head
```

After running, verify in psql or pgAdmin:
```sql
\dt  -- should show clients, api_keys, verifications, transactions, payment_intents, webhook_logs
```

**STEP 6 IS DONE WHEN:** `alembic upgrade head` runs without errors and all 6
tables exist in the database with all correct columns and indexes.

---

## STEP 7 — app/db/queries.py

Implement all reusable query functions. Services call these — nothing else touches
the database directly.

Implement these functions (full signatures):

```python
# Client queries
async def create_client(db, name: str, email: str) -> Client
async def get_client_by_id(db, client_id: UUID) -> Client | None
async def get_client_by_email(db, email: str) -> Client | None
async def update_client_squad_info(db, client_id: UUID, virtual_account_ref: str,
    customer_id: str, account_number: str, bank_name: str) -> None
async def update_client_balance(db, client_id: UUID, new_balance: int) -> None
async def deduct_balance(db, client_id: UUID, amount: int) -> tuple[int, int]
    # Returns (balance_before, balance_after). Uses SELECT FOR UPDATE.

# API key queries
async def create_api_key(db, client_id: UUID, key_hash: str, key_prefix: str,
    label: str = "default") -> ApiKey
async def get_client_by_api_key_hash(db, key_hash: str) -> Client | None
async def update_api_key_last_used(db, key_hash: str) -> None

# Verification queries
async def get_cached_verification(db, image_hash: str, client_id: UUID) -> Verification | None
    # Only returns if cache_expires_at > NOW() and cached=FALSE
async def create_verification(db, client_id: UUID, image_hash: str, trust_score: int,
    verdict: str, confidence: str, spatial_score: int, frequency_score: int,
    processing_ms: int, billed_amount: int, cached: bool,
    image_size_bytes: int = None, image_mime_type: str = None) -> Verification
async def update_verification_transaction_id(db, verification_id: UUID,
    transaction_id: UUID) -> None
async def get_verifications_by_client(db, client_id: UUID, limit: int = 20) -> list[Verification]

# Transaction queries
async def create_transaction(db, client_id: UUID, verification_id: UUID | None,
    amount_naira: int, type: str, balance_before: int, balance_after: int,
    description: str, squad_ref: str = None, squad_event: str = None,
    idempotency_key: str = None) -> Transaction
async def get_transactions_by_client(db, client_id: UUID, limit: int = 20) -> list[Transaction]
async def transaction_exists_by_idempotency_key(db, key: str) -> bool

# Payment intent queries
async def create_payment_intent(db, client_id: UUID, amount_naira: int,
    payment_link: str, squad_ref: str = None) -> PaymentIntent
async def complete_payment_intent(db, squad_ref: str) -> None

# Webhook log queries
async def log_webhook(db, raw_payload: bytes, signature: str,
    signature_valid: bool) -> WebhookLog
async def update_webhook_log(db, webhook_id: UUID, matched: bool,
    matched_client_id: UUID = None, processed: bool = False,
    processing_error: str = None, idempotency_key: str = None) -> None
async def get_client_by_squad_customer_id(db, squad_customer_id: str) -> Client | None
```

**STEP 7 IS DONE WHEN:** All query functions are implemented, importable, and each
one has a corresponding unit test stub in `tests/test_queries.py` (even empty
test functions are fine — David fills them in).

---

## STEP 8 — app/services/inference.py

Implement the inference service with both mock and real stubs.

The mock MUST be deterministic — same image_hash returns same score every time.
See VERIDIFI_GUIDELINES.md section 9 for the exact implementation.

The real inference stub raises `NotImplementedError` with a clear message.
This is replaced by Abdulmalik when the model is trained. The interface contract
that Abdulmalik must match:

```python
# Abdulmalik's model must produce output compatible with this return shape:
{
    "trust_score": int,          # 0-100
    "verdict": str,              # "AUTHENTIC" | "MANIPULATED" | "SYNTHETIC"
    "confidence": str,           # "HIGH" | "MEDIUM" | "LOW"
    "spatial_score": int,        # 0-100 — EfficientNetB0 branch
    "frequency_score": int,      # 0-100 — DCT/FFT branch
    "processing_ms": int,        # milliseconds
}
```

Also implement image preprocessing utilities:
```python
async def validate_image(image_bytes: bytes, max_size_mb: int) -> tuple[str, str]
    # Returns (mime_type, extension). Raises ImageTooLargeError, UnsupportedImageTypeError.
    # Validates from bytes, NOT from filename — filenames lie.

def compute_image_hash(image_bytes: bytes) -> str
    # Returns SHA-256 hex string

async def save_temp_image(image_bytes: bytes, ext: str) -> Path
    # Writes to /tmp/veridifi/{uuid}.{ext}

def delete_temp_image(path: Path) -> None
    # try/except — never raises
```

Supported MIME types: `image/jpeg`, `image/png`, `image/webp`

**STEP 8 IS DONE WHEN:** Mock inference returns consistent results for the same
hash, `compute_image_hash` returns a 64-char hex string, and `validate_image`
correctly rejects a text file passed as an image.

---

## STEP 9 — app/services/squad.py

Implement all Squad API calls. See VERIDIFI_GUIDELINES.md section 12 for patterns.

Functions to implement:

```python
async def create_virtual_account(client_email: str, client_name: str) -> dict
    # POST {SQUAD_BASE_URL}/virtual-account
    # Returns Squad response body
    # Raises SquadAPIError on failure

async def generate_payment_link(amount_naira: int, client_email: str = None) -> dict
    # POST {SQUAD_BASE_URL}/payment_link/otp
    # amount_naira → convert to kobo (multiply by 100) before sending
    # Returns Squad response body including checkout_url
    # Raises SquadAPIError on failure
```

IMPORTANT: When `SQUAD_SECRET_KEY` is empty (not yet obtained), these functions
must fail gracefully with a `SquadAPIError` that includes a helpful message:
"Squad API key not configured — set SQUAD_SECRET_KEY in .env"

Do NOT let missing Squad credentials cause an unhandled 500.

**STEP 9 IS DONE WHEN:** Both functions are implemented, Squad calls are wrapped
in try/except, and missing credentials return a clean SquadAPIError.

---

## STEP 10 — app/services/account.py

Implement account business logic. This service orchestrates between Squad and the DB.

```python
async def create_account(db: AsyncSession, name: str, email: str) -> dict
    """
    1. Check email uniqueness — raise HTTP 409 if already exists
    2. Generate API key pair (raw, hash)
    3. Create client row in DB
    4. Create api_key row in DB
    5. Call squad.create_virtual_account()
       → If Squad call succeeds: update client with Squad refs
       → If Squad call fails: log the error, continue (client exists, Squad pending)
    6. Return: {client_id, api_key (raw), squad_virtual_account, balance_naira}
    """

async def get_balance(db: AsyncSession, client: Client) -> dict
    """
    1. Fetch recent transactions (last 20) for this client
    2. Count total verifications
    3. Return: {balance_naira, total_verifications, recent_transactions}
    """

async def fund_account(db: AsyncSession, client: Client, amount_naira: int) -> dict
    """
    1. Validate amount_naira > 0 and <= 1_000_000 (1 million Naira max per top-up)
    2. Call squad.generate_payment_link(amount_naira)
    3. Create payment_intent row in DB
    4. Return: {payment_link, amount_naira, expires_in_hours: 24}
    """
```

**STEP 10 IS DONE WHEN:** All three service functions are implemented and
Squad failures in `create_account` do not prevent the client from being created.

---

## STEP 11 — app/services/verification.py

This is the most critical service. It implements the exact request flow from
VERIDIFI_PROJECT_SPECIFICATIONS.md section 6 (/verify endpoint).

```python
async def process_verification(db: AsyncSession, client: Client, image: UploadFile) -> dict
    """
    EXACT SEQUENCE — do not reorder:
    1.  Check client.balance_naira >= VERIFICATION_COST_NAIRA
        → Raise InsufficientBalanceError if insufficient
        → Include a freshly-generated Squad payment link in the error detail
    2.  Read image bytes from UploadFile
    3.  Validate image (mime type, size)
    4.  Compute SHA-256 hash of raw bytes
    5.  Check cache: query get_cached_verification(db, image_hash, client.id)
        → CACHE HIT: use stored scores (trust_score, verdict, etc.)
                     set is_cached = True, skip steps 6-9
        → CACHE MISS: set is_cached = False, proceed to step 6
    6.  Save image to temp file
    7.  Run inference via inference.run_inference(image_bytes, image_hash)
    8.  Delete temp file IMMEDIATELY (in finally block — always runs)
    9.  Determine cache_expires_at = NOW() + 24 hours
    10. Create verification row in DB
    11. Atomically deduct ₦175 from client balance
        (balance_before, balance_after) = await queries.deduct_balance(db, client.id, cost)
    12. Create DEBIT transaction row in DB
        Include: client_id, verification_id, amount_naira=175, type='DEBIT',
        balance_before, balance_after, description='Image verification'
    13. Update verification.transaction_id with the new transaction's ID
    14. Commit the database session
    15. Return response dict matching VerifyResponse schema
    """
```

Edge cases to handle:
- UploadFile with no content → raise UnsupportedImageTypeError
- Inference raises any exception → still delete temp file, raise InferenceFailedError
- Balance deduction fails (race condition) → transaction rolls back, return 402

**STEP 11 IS DONE WHEN:** A POST to /verify with a valid image and sufficient
balance returns a 200 with the correct JSON shape. A POST with zero balance
returns a 402 with a payment_link in the detail.

---

## STEP 12 — app/middleware/auth.py AND app/middleware/rate_limit.py

### auth.py
Implement `get_current_client` as a FastAPI dependency.
See VERIDIFI_GUIDELINES.md section 7 for exact implementation.

The dependency:
1. Reads `X-API-Key` header
2. Hashes it with SHA-256
3. Queries `api_keys` table (joined to `clients`)
4. Returns the `Client` ORM object
5. Raises `InvalidApiKeyError` (which the exception handler converts to 401)

### rate_limit.py
Simple in-memory rate limiter per API key. 60 requests per minute.

For the hackathon, use a simple dict-based counter with a timestamp:
```python
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException

_counters: dict[str, list[datetime]] = defaultdict(list)

async def rate_limit(request: Request, client=Depends(get_current_client)):
    key = str(client.id)
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=1)
    # Clean old entries
    _counters[key] = [t for t in _counters[key] if t > window_start]
    if len(_counters[key]) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail={"error": "RATE_LIMIT_EXCEEDED", "message": "60 requests per minute limit exceeded"}
        )
    _counters[key].append(now)
```

Note: In-memory rate limiter resets on server restart. Acceptable for hackathon.
Production would use Redis. Do not over-engineer this.

**STEP 12 IS DONE WHEN:** A request without X-API-Key returns 422 (missing header),
a request with an invalid key returns 401, and a valid key returns the client object.

---

## STEP 13 — app/schemas/ (ALL PYDANTIC SCHEMAS)

Implement all request and response schemas. These are what Peter's React app
receives. They must be exact.

### schemas/account.py
```python
class CreateAccountRequest(BaseModel):
    name: str
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
```

### schemas/verify.py
```python
class BreakdownScores(BaseModel):
    spatial_score: int
    frequency_score: int

class VerifyResponse(BaseModel):
    verification_id: UUID
    trust_score: int
    verdict: str
    confidence: str
    processing_ms: int
    cached: bool
    billed_naira: int
    balance_remaining: int
    breakdown: BreakdownScores
```

### schemas/webhook.py
```python
class SquadWebhookBody(BaseModel):
    transaction_ref: str | None = None
    amount: int | None = None
    transaction_status: str | None = None
    customer_id: str | None = None

class SquadWebhookPayload(BaseModel):
    Event: str
    Body: SquadWebhookBody

class WebhookResponse(BaseModel):
    status: str
```

**STEP 13 IS DONE WHEN:** All schemas import without errors.

---

## STEP 14 — app/routes/account.py

Implement the three account routes. Routes are thin — all logic is in services.

```python
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
```

**STEP 14 IS DONE WHEN:** All three routes are registered and respond correctly
to test requests via curl or httpx.

---

## STEP 15 — app/routes/verify.py

```python
router = APIRouter()

@router.post("/verify", response_model=VerifyResponse)
async def verify_image(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    # Rate limit check inline here or via another Depends
    return await verification_service.process_verification(db, client, image)
```

Also implement a `GET /verify/{verification_id}` route:
```python
@router.get("/verify/{verification_id}")
async def get_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    # Return the stored verification result for this client
    # 404 if not found or belongs to different client
```

**STEP 15 IS DONE WHEN:** POST /verify with a real PNG file returns the full
JSON response. GET /verify/{id} returns the stored result.

---

## STEP 16 — app/routes/webhook.py

This is the Squad webhook listener. Read VERIDIFI_GUIDELINES.md section 8 and
VERIDIFI_PROJECT_SPECIFICATIONS.md section 6 (/webhook/squad) before writing this.

```python
router = APIRouter()

@router.post("/squad")
async def squad_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # 1. Read raw bytes BEFORE any parsing
    raw_body = await request.body()

    # 2. Extract Squad signature header
    signature = request.headers.get("x-squad-encrypted-body", "")

    # 3. Verify HMAC-SHA512
    is_valid = verify_squad_signature(raw_body, signature, settings.squad_webhook_secret)

    # 4. Log to webhook_logs — ALWAYS, valid or not
    webhook_log = await queries.log_webhook(db, raw_body, signature, is_valid)
    await db.commit()

    # 5. Silent rejection if invalid
    if not is_valid:
        return {"status": "received"}

    # 6. Parse payload
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return {"status": "received"}

    event_type = payload.get("Event", "")
    body = payload.get("Body", {})
    squad_ref = body.get("transaction_ref", "")
    idempotency_key = f"webhook_{squad_ref}"

    # 7. Idempotency check
    already_processed = await queries.transaction_exists_by_idempotency_key(db, idempotency_key)
    if already_processed:
        return {"status": "received"}

    # 8. Handle payment.success
    if event_type == "payment.success":
        customer_id = body.get("customer_id", "")
        amount_kobo = body.get("amount", 0)
        amount_naira = amount_kobo // 100

        # Find client
        client = await queries.get_client_by_squad_customer_id(db, customer_id)

        if not client:
            await queries.update_webhook_log(db, webhook_log.id, matched=False)
            await db.commit()
            return {"status": "received"}

        # Credit balance
        balance_before = client.balance_naira
        balance_after = balance_before + amount_naira
        await queries.update_client_balance(db, client.id, balance_after)

        # Record transaction
        await queries.create_transaction(
            db,
            client_id=client.id,
            verification_id=None,
            amount_naira=amount_naira,
            type="CREDIT",
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"Squad top-up — ref: {squad_ref}",
            squad_ref=squad_ref,
            squad_event=event_type,
            idempotency_key=idempotency_key,
        )

        # Mark payment intent as completed
        await queries.complete_payment_intent(db, squad_ref)

        # Update webhook log
        await queries.update_webhook_log(
            db, webhook_log.id,
            matched=True,
            matched_client_id=client.id,
            processed=True,
            idempotency_key=idempotency_key,
        )

        await db.commit()

    # 9. Always return 200 — Squad retries on any non-200
    return {"status": "received"}
```

**STEP 16 IS DONE WHEN:** A POST to /webhook/squad with a correctly signed payload
credits the client's balance and logs the event. An unsigned payload is logged but
ignored. A duplicate payload is detected and ignored.

---

## STEP 17 — app/main.py

Assemble everything. See VERIDIFI_GUIDELINES.md section 13 for the exact implementation.

Register all three routers:
- `verify.router` — no prefix (POST /verify lives at root)
- `account.router` — prefix `/account`
- `webhook.router` — prefix `/webhook`

Add the `GET /health` endpoint.
Add the lifespan context manager (model loading on startup).
Add the CORS middleware.
Add the `VeridifiError` exception handler.

**STEP 17 IS DONE WHEN:** `uvicorn app.main:app --reload` starts without errors
and `http://localhost:8000/health` returns `{"status": "ok", "mode": "mock"}`.

---

## STEP 18 — INTEGRATION SMOKE TEST

Run this sequence manually to verify the full flow works end-to-end in mock mode.

```bash
# 1. Start the server
uvicorn app.main:app --reload

# 2. Create an account
curl -X POST http://localhost:8000/account/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Insurer", "email": "test@insurer.ng"}'
# → Should return 201 with api_key and squad_virtual_account

# Save the api_key from step 2
API_KEY="vrf_sk_live_xxxx"

# 3. Check balance (should be 0)
curl http://localhost:8000/account/balance \
  -H "X-API-Key: $API_KEY"

# 4. Verify an image (should fail with 402 — zero balance)
curl -X POST http://localhost:8000/verify \
  -H "X-API-Key: $API_KEY" \
  -F "image=@/path/to/test.jpg"
# → Should return 402 INSUFFICIENT_BALANCE with payment_link

# 5. Manually credit the client balance in DB for testing
# psql -c "UPDATE clients SET balance_naira = 10000 WHERE email = 'test@insurer.ng'"

# 6. Verify again (should succeed now)
curl -X POST http://localhost:8000/verify \
  -H "X-API-Key: $API_KEY" \
  -F "image=@/path/to/test.jpg"
# → Should return 200 with trust_score, verdict, billed_naira=175, balance_remaining=9825

# 7. Verify same image again (should be cached, still charges ₦175)
curl -X POST http://localhost:8000/verify \
  -H "X-API-Key: $API_KEY" \
  -F "image=@/path/to/test.jpg"
# → Should return 200 with cached=true

# 8. Check balance (should now show deductions)
curl http://localhost:8000/account/balance \
  -H "X-API-Key: $API_KEY"
# → Should show balance_naira=9650, recent_transactions with two DEBIT entries

# 9. Simulate a Squad webhook
curl -X POST http://localhost:8000/webhook/squad \
  -H "Content-Type: application/json" \
  -H "x-squad-encrypted-body: $(echo -n '{"Event":"payment.success","Body":{"transaction_ref":"SQ_TEST_001","amount":1000000,"customer_id":"test_customer"}}' | openssl dgst -sha512 -hmac "$SQUAD_WEBHOOK_SECRET" | cut -d' ' -f2)" \
  -d '{"Event":"payment.success","Body":{"transaction_ref":"SQ_TEST_001","amount":1000000,"customer_id":"test_customer"}}'
# → Should return {"status": "received"} and credit ₦10,000 to the matching client
```

**STEP 18 IS DONE WHEN:** All 9 curl commands above return expected responses.
Document any differences from expected in a comment in the test file.

---

## STEP 19 — SCAFFOLD TESTS FOR DAVID

Create test stubs that David (QA engineer) can fill in. These are not full test
implementations — they are well-named empty test functions that communicate clearly
what needs to be tested.

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.db.database import engine, Base

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def registered_client(client):
    response = await client.post("/account/create", json={
        "name": "Test Client",
        "email": "test@example.com"
    })
    return response.json()
```

```python
# tests/test_account.py
async def test_create_account_returns_201(client): pass
async def test_create_account_returns_api_key(client): pass
async def test_create_account_duplicate_email_returns_409(client): pass
async def test_get_balance_without_api_key_returns_401(client): pass
async def test_get_balance_with_valid_key_returns_zero(client, registered_client): pass
async def test_fund_account_returns_payment_link(client, registered_client): pass

# tests/test_verify.py
async def test_verify_without_api_key_returns_422(client): pass
async def test_verify_with_invalid_key_returns_401(client): pass
async def test_verify_with_zero_balance_returns_402(client, registered_client): pass
async def test_verify_with_balance_returns_200(client, registered_client): pass
async def test_verify_response_has_correct_fields(client, registered_client): pass
async def test_verify_deducts_175_from_balance(client, registered_client): pass
async def test_verify_same_image_twice_returns_cached_true(client, registered_client): pass
async def test_verify_oversized_image_returns_413(client, registered_client): pass
async def test_verify_non_image_file_returns_415(client, registered_client): pass

# tests/test_webhook.py
async def test_webhook_invalid_signature_returns_200(client): pass
async def test_webhook_invalid_signature_does_not_credit_balance(client): pass
async def test_webhook_valid_payment_success_credits_balance(client, registered_client): pass
async def test_webhook_duplicate_squad_ref_is_idempotent(client, registered_client): pass
async def test_webhook_unknown_customer_returns_200(client): pass
async def test_webhook_logs_all_events(client): pass
```

**STEP 19 IS DONE WHEN:** `pytest tests/ -v` runs without import errors and
shows all test functions (even though they pass vacuously — empty test bodies pass).

---

## STEP 20 — Dockerfile AND RENDER DEPLOYMENT PREP

Create the Dockerfile (exact content in VERIDIFI_GUIDELINES.md section 15).

Create `render.yaml` for Render deployment:
```yaml
services:
  - type: web
    name: veridifi-api
    env: python
    buildCommand: pip install -r requirements.txt && alembic upgrade head
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: APP_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: veridifi-db
          property: connectionString
      - key: SQUAD_SECRET_KEY
        sync: false
      - key: SQUAD_WEBHOOK_SECRET
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: MOCK_INFERENCE
        value: "true"
      - key: ALLOWED_ORIGINS
        value: https://veridify-frontend.onrender.com

databases:
  - name: veridifi-db
    databaseName: veridify
    user: veridify
```

**STEP 20 IS DONE WHEN:** `docker build -t veridifi-backend .` completes and
`docker run -p 8000:8000 --env-file .env veridifi-backend` starts the server.

---

## FINAL CHECKLIST BEFORE HANDING OFF

Before declaring the backend complete, verify every item:

- [ ] `uvicorn app.main:app` starts without errors
- [ ] `GET /health` returns `{"status": "ok", "mode": "mock"}`
- [ ] `POST /account/create` creates a client, API key, and calls Squad (or fails gracefully)
- [ ] `GET /account/balance` with valid key returns balance and transactions
- [ ] `POST /account/fund` generates a Squad payment link
- [ ] `POST /verify` with zero balance returns 402 with payment_link
- [ ] `POST /verify` with balance returns 200 with correct JSON shape
- [ ] `POST /verify` same image twice returns `cached: true` on second call
- [ ] `POST /verify` deducts ₦175 and records balance_before/balance_after
- [ ] `POST /webhook/squad` with invalid HMAC returns 200 silently
- [ ] `POST /webhook/squad` with valid HMAC credits client balance
- [ ] Duplicate webhook with same squad_ref is idempotent
- [ ] All webhook events are logged in webhook_logs table
- [ ] Images are deleted from /tmp immediately after inference
- [ ] `pytest tests/ -v` runs without import errors
- [ ] `docker build` completes successfully
- [ ] `alembic upgrade head` applies all migrations cleanly
- [ ] OpenAPI docs at `http://localhost:8000/docs` shows all endpoints correctly

---

## HOW TO HAND OFF TO THE NEXT AGENT

If you must stop mid-build, leave a `PROGRESS.md` file in `/backend` with:

```markdown
# Veridifi Backend — Build Progress

## Last completed step: STEP [N]
## Date: [date]
## What works: [list]
## What is incomplete: [list]
## Known issues: [list]
## Next action: [exactly what to do first]
```

The next agent reads the three spec files, then reads PROGRESS.md, then continues
from the step listed as incomplete. They run `pytest tests/ -v` first to confirm
what is currently working before making any changes.
