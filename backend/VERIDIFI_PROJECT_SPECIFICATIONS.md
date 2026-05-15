# VERIDIFI — PROJECT SPECIFICATIONS
## Backend Module — Complete Reference Document
### For: Claude Code / Codex / Any AI Coding Agent
### Written by: Claude (Anthropic) — synthesised from full project chat history
### Context: Squad Hackathon 3.0 — Challenge 01: Proof of Life, Media & Information

---

> **TO THE AGENT READING THIS:**
> You are building the backend of Veridifi — an AI-powered image authenticity
> verification API. Every decision in this document was made deliberately across
> multiple design sessions with the team lead (Abdulmalik). Do not override these
> decisions. Do not simplify the schema. Do not change the tech stack. Read this
> document fully before writing a single line of code. Then read VERIDIFI_GUIDELINES.md.
> Then read VERIDIFI_BUILD_ORDER.md. Build in the exact order described.

---

## 1. WHAT VERIDIFI IS

Veridifi is a REST API that accepts an image and returns an authenticity verdict
within 3 seconds. It answers one question: is this image real, manipulated, or
AI-generated?

The product exists because AI image generation tools (Midjourney, DALL-E, FLUX,
Stable Diffusion) are now accessible to everyday fraudsters in Nigeria. Insurance
adjusters, marketplace operators, and fact-checkers have no affordable tool to
detect these forgeries. Nigerian insurance fraud costs an estimated ₦100B+ annually
(NAICOM data). Veridifi's API plugs directly into existing workflows via a single
POST /verify call.

**Revenue model:** Pay-per-verification. Each API call costs ₦175, deducted from a
pre-funded Squad Virtual Account. Squad (a GTBank subsidiary) is the payment
infrastructure. This is not cosmetic — Squad integration is a judging criterion
worth 20% of the total score and is a disqualification gate.

---

## 2. THE TEAM AND OWNERSHIP

| Person | Role | Backend relevance |
|---|---|---|
| Abdulmalik | ML Engineer + Backend Lead | Owns entire /backend folder |
| Peter | Frontend Engineer (React) | Consumes the API — never touches backend |
| David | QA Engineer | Writes tests against the API |
| Mathematician | Research + Documentation | No backend involvement |

The agent is building what Abdulmalik owns. Peter builds against the mock from day
one. Do not wait for Peter. Do not coordinate with Peter. Just build the contract
Peter calls.

---

## 3. LOCKED TECHNICAL DECISIONS

These are not suggestions. They were debated and decided. Do not change them.

| Decision | Chosen | Reason |
|---|---|---|
| Language | Python | ML model is TensorFlow/Keras — one language, one deployment |
| Framework | FastAPI | Async support, Pydantic validation, automatic OpenAPI docs |
| Database | PostgreSQL | Relational, strong UUID support, production-grade |
| ORM | SQLAlchemy (async) | Type-safe queries, Alembic migration support |
| Migrations | Alembic | Version-controlled schema changes |
| Deployment | Render | Simple, supports Python, single container |
| Payment | Squad API (sandbox) | Hackathon requirement — 20% judging weight |
| ML Model | EfficientNetB0 dual-branch | Transfer learning + frequency domain, 3-class output |
| Image storage | Temp only — 60 second TTL | Privacy by design — never persist images |
| Auth | API key in X-API-Key header | Simple, stateless, inspectable by judges |
| Free tier | NONE — removed for simplicity | Keeps billing logic clean for hackathon |
| Cache | 24 hours per image hash per client | Same image submitted twice → return cached result, still bill ₦175 |

---

## 4. REPOSITORY STRUCTURE

The GitHub repo is named `veridify`. The `/backend` folder exists but is empty.
The agent builds everything inside `/backend`.

```
veridify/
    /backend                         ← AGENT BUILDS EVERYTHING HERE
        /app
            __init__.py
            main.py                  ← FastAPI app instantiation, router registration, CORS, startup events
            config.py                ← All env vars via pydantic BaseSettings

            /routes
                __init__.py
                verify.py            ← POST /verify
                account.py           ← POST /account/create, GET /account/balance, POST /account/fund
                webhook.py           ← POST /webhook/squad

            /services
                __init__.py
                inference.py         ← image → trust score. Mock first, real model swap later
                squad.py             ← All Squad API calls (virtual account, payment link)
                account.py           ← balance check, deduction, freemium logic removed

            /db
                __init__.py
                database.py          ← async engine, session factory, get_db dependency
                models.py            ← SQLAlchemy ORM models for all 6 tables
                queries.py           ← reusable async query functions

            /middleware
                __init__.py
                auth.py              ← X-API-Key extraction and validation
                rate_limit.py        ← per-client 60 req/min limiter

            /schemas
                __init__.py
                verify.py            ← Pydantic request/response shapes for /verify
                account.py           ← Pydantic shapes for account endpoints
                webhook.py           ← Pydantic shape for Squad webhook payload

        /alembic
            env.py
            /versions               ← migration files created by alembic revision

        /models                     ← ML model weights live here (not committed to git)
            .gitkeep

        /tests                      ← David's test suite (agent scaffolds this)
            __init__.py
            conftest.py
            test_verify.py
            test_account.py
            test_webhook.py

        alembic.ini
        requirements.txt
        Dockerfile
        .env.example
        .env                        ← NOT committed to git
        .gitignore
```

---

## 5. THE DATABASE SCHEMA — COMPLETE AND FINAL

Six tables. Every column has a reason. Do not add, remove, or rename columns.

### Table 1: clients
```sql
CREATE TABLE clients (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                        VARCHAR(255) NOT NULL,
    email                       VARCHAR(255) UNIQUE NOT NULL,
    squad_virtual_account_ref   VARCHAR(255),
    squad_customer_id           VARCHAR(255) UNIQUE,
    squad_account_number        VARCHAR(20),
    squad_bank_name             VARCHAR(100),
    balance_naira               INTEGER NOT NULL DEFAULT 0,
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_squad_customer_id ON clients(squad_customer_id);
```

### Table 2: api_keys
```sql
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    key_hash        VARCHAR(255) UNIQUE NOT NULL,
    key_prefix      VARCHAR(12) NOT NULL,
    label           VARCHAR(100),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_client_id ON api_keys(client_id);
```

Why separate from clients? Key rotation, multiple environments (dev/prod), revocation
without destroying the account. The raw API key is NEVER stored — only its SHA-256
hash. The actual key is returned once on creation and never again.

### Table 3: verifications
```sql
CREATE TABLE verifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    transaction_id      UUID,
    image_hash          VARCHAR(64) NOT NULL,
    image_size_bytes    INTEGER,
    image_mime_type     VARCHAR(50),
    trust_score         INTEGER NOT NULL,
    verdict             VARCHAR(20) NOT NULL,
    confidence          VARCHAR(10) NOT NULL,
    spatial_score       INTEGER,
    frequency_score     INTEGER,
    processing_ms       INTEGER,
    billed_amount       INTEGER NOT NULL DEFAULT 0,
    cached              BOOLEAN NOT NULL DEFAULT FALSE,
    cache_expires_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_verifications_client_id ON verifications(client_id);
CREATE INDEX idx_verifications_image_hash ON verifications(image_hash);
CREATE INDEX idx_verifications_created_at ON verifications(created_at DESC);
CREATE INDEX idx_verifications_cache ON verifications(image_hash, cache_expires_at)
    WHERE cached = FALSE;
```

### Table 4: transactions
```sql
CREATE TABLE transactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    verification_id     UUID REFERENCES verifications(id),
    amount_naira        INTEGER NOT NULL,
    type                VARCHAR(10) NOT NULL,        -- CREDIT or DEBIT
    balance_before      INTEGER NOT NULL,
    balance_after       INTEGER NOT NULL,
    squad_ref           VARCHAR(255),
    squad_event         VARCHAR(50),
    idempotency_key     VARCHAR(255) UNIQUE,
    description         TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_transactions_client_id ON transactions(client_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX idx_transactions_idempotency ON transactions(idempotency_key);
CREATE INDEX idx_transactions_squad_ref ON transactions(squad_ref);
```

The `balance_before` and `balance_after` columns are critical. Every Naira movement
is snapshotted. If a judge asks "how did this client go from ₦10,000 to ₦7,350?"
you trace the exact debit chain. This is your audit trail.

### Table 5: payment_intents
```sql
CREATE TABLE payment_intents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    amount_naira    INTEGER NOT NULL,
    payment_link    TEXT NOT NULL,
    squad_ref       VARCHAR(255),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    expires_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_payment_intents_client_id ON payment_intents(client_id);
CREATE INDEX idx_payment_intents_squad_ref ON payment_intents(squad_ref);
CREATE INDEX idx_payment_intents_status ON payment_intents(status);
```

Tracks payment links generated before Squad confirms payment. Links the "fund account"
request to the eventual `payment.success` webhook. Status: pending → completed | expired.

### Table 6: webhook_logs
```sql
CREATE TABLE webhook_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type          VARCHAR(100),
    squad_ref           VARCHAR(255),
    raw_payload         JSONB NOT NULL,
    signature_valid     BOOLEAN NOT NULL,
    matched_client_id   UUID REFERENCES clients(id),
    matched             BOOLEAN NOT NULL DEFAULT FALSE,
    processed           BOOLEAN NOT NULL DEFAULT FALSE,
    processing_error    TEXT,
    idempotency_key     VARCHAR(255),
    received_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_webhook_logs_squad_ref ON webhook_logs(squad_ref);
CREATE INDEX idx_webhook_logs_event_type ON webhook_logs(event_type);
CREATE INDEX idx_webhook_logs_received_at ON webhook_logs(received_at DESC);
CREATE INDEX idx_webhook_logs_matched ON webhook_logs(matched) WHERE matched = FALSE;
```

Every Squad webhook is logged here — whether or not it matches a client. This is
your debugging lifeline on demo day. A webhook that silently fails is invisible.
A webhook that fails but is logged is debuggable in 30 seconds.

---

## 6. THE API CONTRACT — EVERY ENDPOINT IN FULL

### POST /account/create
No authentication required. Called at onboarding.

**Request body:**
```json
{ "name": "Sterling Assurance", "email": "dev@sterling.ng" }
```

**What happens internally:**
1. Validate email uniqueness in DB
2. Generate API key: `vrf_sk_live_` + 32 random hex chars
3. Hash the key with SHA-256, store hash in api_keys table
4. Call Squad API to create virtual account for this client
5. Store Squad refs in clients table
6. Return the raw key ONCE — never again

**Response 201:**
```json
{
  "client_id": "uuid",
  "api_key": "vrf_sk_live_a3f9...c2d1",
  "message": "Store this API key — it will not be shown again",
  "squad_virtual_account": {
    "account_number": "0123456789",
    "bank_name": "GTBank",
    "account_name": "VERIDIFY/STERLING ASSURANCE"
  },
  "balance_naira": 0
}
```

---

### POST /account/fund
Requires: `X-API-Key` header

**Request body:**
```json
{ "amount_naira": 10000 }
```

**What happens internally:**
1. Validate API key → get client
2. Call Squad API to generate payment link for amount_naira
3. Insert row into payment_intents table (status: pending)
4. Return payment link to client

**Response 200:**
```json
{
  "payment_link": "https://pay.squadco.com/xxxx",
  "amount_naira": 10000,
  "expires_in_hours": 24,
  "message": "Complete this payment to credit your balance"
}
```

---

### GET /account/balance
Requires: `X-API-Key` header

**Response 200:**
```json
{
  "balance_naira": 8350,
  "total_verifications": 127,
  "recent_transactions": [
    {
      "type": "DEBIT",
      "amount_naira": 175,
      "description": "Image verification",
      "balance_after": 8350,
      "created_at": "2026-05-15T10:00:00Z"
    }
  ]
}
```

---

### POST /verify
Requires: `X-API-Key` header
Content-Type: `multipart/form-data`
Body field: `image` (JPEG, PNG, WEBP — max 10MB)

**What happens internally — exact sequence:**
```
1.  Auth middleware: extract X-API-Key, hash it, look up in api_keys table
    → 401 if not found or revoked
2.  Rate limit middleware: check per-client request count (60/min)
    → 429 if exceeded
3.  Balance check: client.balance_naira >= VERIFICATION_COST_NAIRA (175)?
    → 402 with payment link if insufficient
4.  Read image bytes from multipart upload
5.  Validate: is this actually an image? check MIME type from bytes, not filename
6.  Compute SHA-256 hash of raw image bytes
7.  Cache check: SELECT from verifications WHERE image_hash=$1
    AND client_id=$2 AND cached=FALSE AND cache_expires_at > NOW()
    LIMIT 1
    → CACHE HIT: use stored scores, skip inference, set cached=TRUE on new row
    → CACHE MISS: proceed to inference
8.  Write image bytes to /tmp/{uuid}.{ext}
9.  Run inference (mock or real — controlled by MOCK_INFERENCE env var)
10. Delete /tmp/{uuid}.{ext} IMMEDIATELY — do not wait for response
11. Insert row into verifications table (cached=FALSE, cache_expires_at=NOW()+24h)
12. Deduct ₦175 from client.balance_naira (atomic update with balance snapshot)
13. Insert DEBIT row into transactions table
14. Update verifications.transaction_id with the new transaction UUID
15. Update api_keys.last_used_at
16. Return response
```

**Response 200:**
```json
{
  "verification_id": "uuid",
  "trust_score": 82,
  "verdict": "AUTHENTIC",
  "confidence": "HIGH",
  "processing_ms": 1243,
  "cached": false,
  "billed_naira": 175,
  "balance_remaining": 8175,
  "breakdown": {
    "spatial_score": 84,
    "frequency_score": 79
  }
}
```

**Response 402 (insufficient balance):**
```json
{
  "error": "INSUFFICIENT_BALANCE",
  "balance_naira": 0,
  "verification_cost_naira": 175,
  "payment_link": "https://pay.squadco.com/xxxx",
  "message": "Fund your account to continue verifications"
}
```

**Verdict logic:**
- trust_score 70–100 → AUTHENTIC, confidence HIGH if score > 85 else MEDIUM
- trust_score 35–69 → MANIPULATED, confidence HIGH if score < 40 else MEDIUM
- trust_score 0–34 → SYNTHETIC, confidence HIGH if score < 20 else MEDIUM

---

### POST /webhook/squad
No authentication header. Squad signs its webhooks differently.

**Security: HMAC-SHA512 verification**
Squad sends an `x-squad-encrypted-body` header. The value is HMAC-SHA512 of the
raw request body using `SQUAD_SECRET_KEY`. Verify this before doing ANYTHING else.

**What happens internally:**
```
1.  Read raw request body as bytes (before JSON parsing)
2.  Compute HMAC-SHA512(raw_body, SQUAD_SECRET_KEY)
3.  Compare with x-squad-encrypted-body header (constant-time comparison)
4.  Log to webhook_logs table regardless of signature validity
    → signature_valid=FALSE: log and return 200 silently (never reveal why rejected)
5.  Parse JSON payload
6.  Extract idempotency_key (use squad transaction_ref)
7.  Check transactions table for existing row with this idempotency_key
    → Already exists: return 200 immediately (duplicate delivery — Squad retries)
8.  Match customer: look up clients by squad_customer_id
    → No match: log matched=FALSE, return 200 (Squad must not receive errors)
9.  On payment.success:
    a. Convert amount from kobo to naira (divide by 100)
    b. Credit client.balance_naira
    c. Insert CREDIT row into transactions table with idempotency_key
    d. Update payment_intents status to 'completed' if squad_ref matches
    e. Update webhook_logs: matched=TRUE, processed=TRUE
10. Always return 200 {"status": "received"}
    NEVER return 4xx or 5xx to Squad — it will retry indefinitely
```

**Squad webhook payload shape:**
```json
{
  "Event": "payment.success",
  "Body": {
    "transaction_ref": "SQ_xxxx",
    "amount": 1000000,
    "transaction_status": "success",
    "customer_id": "squad_customer_id",
    "meta": {}
  }
}
```

---

## 7. THE ML MODEL — WHAT THE INFERENCE SERVICE MUST INTEGRATE

The ML model is built by Abdulmalik in Google Colab separately. The backend's
`inference.py` must be designed to receive its output. Here is the full context.

### Architecture: Dual-Branch
**Branch A (Spatial):** EfficientNetB0 pretrained on ImageNet, fine-tuned on our
dataset. Input: 300×300×3 RGB image. Output: spatial feature vector.

**Branch B (Frequency Domain):** Manual feature extraction from the Y (luminance)
channel. Three sub-branches:
- DCT branch: 8 features (energy ratios, high/low frequency distribution)
- FFT branch: 11 features (ring statistics at 5 radii + spectral flatness)
- Noise residual branch: 4 features (noise power, Laplacian variance)
Total: 23 features padded to 64-dim vector.

**Fusion:** Concatenate spatial + frequency features → Dense(256) → Dropout(0.3)
→ Dense(128) → Dense(3, softmax) → 3-class output.

**Classes:** AUTHENTIC | MANIPULATED | SYNTHETIC

**Input preprocessing:**
```python
import cv2
import numpy as np

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    # Decode bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Resize to model input size
    img = cv2.resize(img, (300, 300))
    # Normalize to [0, 1]
    img = img.astype(np.float32) / 255.0
    return img
```

### Mock inference (used until model is trained):
When `MOCK_INFERENCE=true` in .env, `inference.py` returns deterministic fake scores
based on the image hash so repeated calls return consistent results during testing.

### Real inference swap:
When `MOCK_INFERENCE=false`, `inference.py` loads the model from `MODEL_PATH` at
startup (not per-request — loading once at startup is critical for the 3-second SLA).
The swap is one env var change. Zero other code changes.

---

## 8. ENVIRONMENT VARIABLES

Every variable the application needs. The agent creates `.env.example` with these
keys and empty values. `.env` is in `.gitignore`.

```bash
# Application
APP_ENV=development                          # development | production
APP_NAME=Veridifi
SECRET_KEY=                                  # 64 random hex chars — used for internal signing

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/veridify

# Squad Payment API
SQUAD_SECRET_KEY=                            # From sandbox-dashboard.squadco.com
SQUAD_BASE_URL=https://sandbox-api-d.squadco.com
SQUAD_WEBHOOK_SECRET=                        # Separate secret for webhook HMAC verification
SQUAD_CURRENCY=NGN
SQUAD_INITIATE_TRANSFER_URL=                 # Squad transfer endpoint (for payouts - roadmap)

# ML Model
MODEL_PATH=./models/dual_branch_v1.keras    # Path to trained .keras file
MOCK_INFERENCE=true                          # CRITICAL: set false when real model is ready

# Billing
VERIFICATION_COST_NAIRA=175                 # Cost per verification call

# Rate limiting
RATE_LIMIT_PER_MINUTE=60                    # Per API key

# File handling
MAX_IMAGE_SIZE_MB=10
TEMP_FILE_DIR=/tmp/veridify
IMAGE_RETENTION_SECONDS=60                  # Max time an image lives on disk

# Cache
CACHE_TTL_HOURS=24                          # Same image submitted twice → use cache for 24h

# CORS (for Peter's frontend)
ALLOWED_ORIGINS=http://localhost:5173,https://veridify.onrender.com
```

---

## 9. SQUAD API INTEGRATION — HOW TO CALL SQUAD

Base URL (sandbox): `https://sandbox-api-d.squadco.com`
Base URL (production): `https://api-d.squadco.com`

All Squad API calls use HTTP Basic Auth: username = your secret key, password = empty.
Or Bearer token depending on endpoint — check Squad docs:
https://squadinc.gitbook.io/squad-api-documentation

### Three Squad calls to implement:

**1. Create Virtual Account (called at /account/create):**
```
POST {SQUAD_BASE_URL}/virtual-account
Auth: Bearer {SQUAD_SECRET_KEY}
Body: {
  "customer_identifier": "client_email",
  "display_name": "VERIDIFY/{CLIENT_NAME}",
  "bvn": "",              // optional for sandbox
  "mobile_num": "",
  "beneficiary_account": ""
}
```

**2. Generate Payment Link (called at /account/fund):**
```
POST {SQUAD_BASE_URL}/payment_link/otp
Auth: Bearer {SQUAD_SECRET_KEY}
Body: {
  "amount": amount_in_kobo,  // multiply naira by 100
  "currency_id": "NGN",
  "name": "Veridifi Balance Top-up",
  "description": "Fund your Veridifi verification account",
  "redirect_link": "{YOUR_APP_URL}/payment/success",
  "return_msg": "Payment successful"
}
```

**3. Webhook verification (no outbound call — inbound from Squad):**
Squad sends POST to /webhook/squad. Verify HMAC-SHA512 as described in section 6.

---

## 10. WHAT HAPPENS ON DEMO DAY — THE JUDGE FLOW

The judge will:
1. Hit the web dashboard (Peter's React app)
2. Create an account → see Squad virtual account number generated in real time
3. Fund the account via Squad payment link → see balance credit arrive via webhook
4. Upload a suspicious insurance claim image → see trust score, verdict, billed amount
5. Check the transaction history → see every deduction with balance snapshots
6. Ask: "show me this in Postman" → David shows raw JSON request/response
7. Ask: "show me the Squad dashboard" → Squad sandbox shows the transaction

Every one of these steps must work. The backend owns steps 2, 3, 4, 5, and the
raw API view of 6. Nothing can fail silently.

---

## 11. PERFORMANCE REQUIREMENTS

- POST /verify must respond in under 3 seconds end-to-end (mock: under 500ms)
- POST /webhook/squad must respond in under 1 second (Squad retries after timeout)
- Database queries must use indexed columns only for all hot paths
- Model loads at startup, not per-request — never reload on every call
- Image files deleted immediately after inference — never after response sent

---

## 12. ERROR HANDLING PHILOSOPHY

Every error response follows this shape:
```json
{
  "error": "SNAKE_CASE_ERROR_CODE",
  "message": "Human readable message",
  "detail": {}    // optional extra context
}
```

Error codes used:
- `INVALID_API_KEY` → 401
- `RATE_LIMIT_EXCEEDED` → 429
- `INSUFFICIENT_BALANCE` → 402 (includes payment_link in detail)
- `IMAGE_TOO_LARGE` → 413
- `UNSUPPORTED_IMAGE_TYPE` → 415
- `INFERENCE_FAILED` → 500 (never expose stack trace)
- `DATABASE_ERROR` → 500 (never expose detail)
- `INVALID_WEBHOOK_SIGNATURE` → 200 (yes, 200 — never tell Squad it failed)

---

## 13. WHAT THIS BACKEND IS NOT RESPONSIBLE FOR

- Training the ML model (Abdulmalik does this in Colab)
- The React frontend (Peter owns /frontend)
- The pitch deck (Mathematician owns /research)
- WhatsApp bot (roadmap only — not built for hackathon)
- Production secrets rotation (hackathon scope)
- User authentication beyond API keys (no OAuth, no JWT, no sessions)
