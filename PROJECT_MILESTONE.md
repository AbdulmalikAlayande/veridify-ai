# Veridify — Full Project Execution Plan
---

## Team & Roles — Final

| Person | Role | Track |
|---|---|---|
| Abdulmalik | ML Engineer + Backend (FastAPI) | Model + API |
| Peter | Frontend Engineer (React) | Dashboard + Demo UI |
| David | QA Engineer (Testing + Validation) | Tests + Breaking things |
| Mathematician | Research + Documentation | Stats + Pitch deck |

**One repo. One FastAPI Python backend. One React frontend. Two folders.**

```
veridify/
    /backend          ← Abdulmalik owns this entirely
    /frontend         ← Peter owns this entirely
    /research         ← Mathematician owns this
    /tests            ← David owns this
    README.md
    .env.example
```

---

## The Dependency Chain
Nothing moves in the wrong order. This is the sequence everything depends on:

```
1. Datasets downloaded and structured       (Abdulmalik)
2. Mock inference endpoint running          (Abdulmalik — Day 1)
3. Squad sandbox keys obtained              (Abdulmalik)
4. Backend API running against mock         (Abdulmalik)
5. Frontend running against mock backend    (Peter)
6. Real model trained and swapped in        (Abdulmalik)
7. Full integration tested end to end       (David)
8. Demo rehearsed and stable                (Everyone)
```

Peter should never wait for a real model. He shoud build against a mock from day one. David never starts testing until Milestone 3 is done. Mathematician runs in parallel the entire time.

---

## Milestone 0 — Foundation

**Abdulmalik:**
- [ ] Create GitHub repo named `veridify`, invite everyone
- [ ] Create Squad sandbox account at https://sandbox-dashboard.squadco.com
- [ ] Obtain Squad sandbox secret key, save to `.env.example`
- [ ] Set up Colab environment, confirm TensorFlow imports without errors
- [ ] Create the repo folder structure above and push to GitHub

**Peter:**
- [ ] Clone the repo
- [ ] Initialise React app inside `/frontend` using Vite
- [ ] Confirm it runs locally on port 5173
- [ ] Read the five frontend screens listed in Milestone 5

**David:**
- [ ] Clone the repo
- [ ] Install Postman/Insomnia
- [ ] Read the full judging criteria document — all six criteria and weights
- [ ] Write down ten questions a judge might ask during Q&A and share with team

**Mathematician:**
- [ ] Read the challenge document one more time
- [ ] Create `/research/judging_matrix.md` — a table mapping each judging criterion to what evidence we need to show for it
- [ ] Begin sourcing Nigerian insurance fraud statistics for slide 1 and slide 7
- [ ] Find the NAICOM annual report data on fraud losses

**Milestone 0 is done when:** 
- Everyone has cloned the repo
- Squad sandbox keys exist in `.env.example`, 
- Colab runs without errors.

---

## Milestone 1 — Data Pipeline Ready
### Abdulmalik

**Task 1.1 — Download datasets in this exact order:**

CIFAKE first — smallest, fastest, gets the pipeline working:
```python
!pip install kaggle
# Upload kaggle.json to Colab first
!kaggle datasets download -d birdy654/cifake-real-and-ai-generated-synthetic-images
!unzip cifake-real-and-ai-generated-synthetic-images.zip -d /content/data/synthetic
```

CASIA second — manipulation detection data:
```python
!kaggle datasets download -d sophatvathana/casia-dataset
!unzip casia-dataset.zip -d /content/data/manipulated
```

GenImage third — Midjourney and SD subsets only, not all 1.3M images:
```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="GenImage/GenImage",
    repo_type="dataset",
    allow_patterns=["midjourney/*", "stable_diffusion_v_1_5/*"],
    local_dir="/content/data/genimage"
)
```

ArtiFact last — OOD test set only, never touched during training:
```python
from datasets import load_dataset
ds = load_dataset("awsaf49/artifact")
# Save to /content/data/ood_test — do not mix with training data
```

**Task 1.2 — Build unified folder structure:**
```
/content/data/
    train/
        authentic/      ← real images from CIFAKE + CASIA real splits
        manipulated/    ← tampered images from CASIA v1/v2
        synthetic/      ← AI-generated from CIFAKE + GenImage
    val/
        authentic/
        manipulated/
        synthetic/
    test/
        authentic/
        manipulated/
        synthetic/
    ood_test/           ← ArtiFact only. Never seen during training.
        authentic/
        manipulated/
        synthetic/
```

**Task 1.3 — Class balance check:**
```python
import os
for split in ['train', 'val', 'test']:
    for cls in ['authentic', 'manipulated', 'synthetic']:
        path = f"/content/data/{split}/{cls}"
        count = len(os.listdir(path))
        print(f"{split}/{cls}: {count} images")
```
If any class has more than 2x the images of another, undersample the majority class. Equal representation matters.

**Milestone 1 is done when:** 
- Abdulmalik prints a clean class distribution table with no severe imbalance and one batch loads from each class without errors.

---

## Milestone 2 — Mock Backend + Squad Integration
### Abdulmalik

Peter develops against this from day one. The mock means Peter never waits.

**Task 2.1 — Backend folder structure:**
```
/backend
    /app
        main.py              ← FastAPI app entry point
        /routes
            verify.py        ← POST /verify
            account.py       ← POST /account/create, GET /account/balance
            webhook.py       ← POST /webhook/squad
        /services
            inference.py     ← calls ML model (mock first, real later)
            squad.py         ← all Squad API calls
            account.py       ← balance logic, freemium gating
        /db
            database.py      ← PostgreSQL connection
            models.py        ← SQLAlchemy table definitions
            queries.py       ← reusable query functions
        /middleware
            auth.py          ← API key validation
        config.py            ← environment variables
    requirements.txt
    Dockerfile
    .env
```

**Task 2.2 — Mock inference service:**
```python
# services/inference.py — mock version
# Abdulmalik replaces this with real model in Milestone 3
import random, time

async def run_inference(image_bytes: bytes) -> dict:
    time.sleep(0.5)  # simulate processing time
    score = random.randint(0, 100)
    if score >= 70:
        verdict = "AUTHENTIC"
    elif score >= 35:
        verdict = "MANIPULATED"
    else:
        verdict = "SYNTHETIC"
    return {
        "trust_score": score,
        "verdict": verdict,
        "confidence": "HIGH" if abs(score - 50) > 30 else "MEDIUM",
        "processing_ms": 487
    }
```

**Task 2.3 — Three Squad API calls to implement:**

1. Create virtual account — at client onboarding
2. Generate payment link — when client tops up balance
3. Webhook receiver — when Squad confirms payment

Squad sandbox documentation: https://squadinc.gitbook.io/squad-api-documentation

**Task 2.4 — PostgreSQL schema — three tables:**
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    squad_virtual_account_ref VARCHAR(255),
    balance_naira INTEGER DEFAULT 0,
    free_quota_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    image_hash VARCHAR(64) NOT NULL,
    trust_score INTEGER NOT NULL,
    verdict VARCHAR(50) NOT NULL,
    confidence VARCHAR(50) NOT NULL,
    processing_ms INTEGER,
    billed_amount INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    amount_naira INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    description TEXT,
    squad_ref VARCHAR(255),
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Milestone 2 is done when:** `POST /verify` returns a mock JSON verdict, a Squad payment link generates in the sandbox, and Peter can call the API from his React app and see a response.

---

## Milestone 3 — Model Trained and Serving
### Abdulmalk

**Task 3.1 — Build dual-branch model:**
EfficientNetB0 spatial branch + frequency domain branch. Three-class output. We have already discussed this architecture in full.

**Task 3.2 — Training phases:**
- Phase 1: Backbone frozen, train head only — 5 epochs, Adam 1e-3
- Phase 2: Unfreeze last 30 layers, fine-tune — 10 epochs, Adam 1e-5
- Log per-class accuracy and AUC after every epoch — not just overall accuracy

**Task 3.3 — Evaluation before declaring done:**
Record these six numbers and hand them to the mathematician:
- Authentic class accuracy
- Manipulated class accuracy
- Synthetic class accuracy
- Overall AUC
- In-distribution accuracy (test split)
- OOD accuracy (ArtiFact — never seen during training)

**Task 3.4 — Swap mock for real model:**
One line change in `services/inference.py`. The mock function is replaced with the real model call. Everything else in the system stays identical. Peter notices nothing changed — his frontend still works.

**Milestone 3 is done when:** Real model returns a verdict in under 3 seconds for any test image, per-class accuracy numbers are documented and handed to the mathematician, and the full backend flow works with real inference.

---

## Milestone 4 — Frontend Dashboard
### Peter

Peter builds this entirely against the mock API. Real model swap is invisible to him.

**Five screens. No more.**

**Screen 1 — Onboarding:**
Client enters name and email. System creates their account and Squad virtual account. Payment link displayed immediately. Clean, minimal form.

**Screen 2 — Dashboard home:**
Balance in Naira displayed prominently. Number of verifications used this month. Quick verify button. Transaction history summary.

**Screen 3 — Verify page:**
Drag and drop image upload. Large drop zone. Submit button. Loading spinner with processing time counter while inference runs.

**Screen 4 — Result page:**
This is the most important screen. The judge stares at this during the demo.
- Trust score: large circular gauge, 0–100
- Verdict: colour-coded badge — green AUTHENTIC, amber MANIPULATED, red SYNTHETIC
- Confidence level displayed below verdict
- Plain English explanation of what the verdict means
- Squad deduction shown: "₦175 deducted from your balance"
- Remaining balance shown
- Button to verify another image

**Screen 5 — Transaction history:**
Table of past verifications. Columns: timestamp, verdict, trust score, amount billed. Filterable by verdict type.

**Milestone 4 is done when:** Peter uploads a real image in the browser, sees Abdulmalik's real model verdict on screen, and the Squad transaction shows in the history table.

---

## Milestone 5 — Full Integration + David's Testing
### David leads, Abdulmalik + Peter support

**David owns the following test suite:**

**Functional tests — does it work:**
- Upload a known AI-generated image → expect verdict SYNTHETIC
- Upload a known real photo → expect verdict AUTHENTIC
- Upload a known manipulated image → expect verdict MANIPULATED
- Upload with zero balance → expect 402 error with payment link in response
- Upload with invalid API key → expect 401 error
- Upload a corrupted file → expect graceful error, not a crash
- Fund account via Squad payment link → expect balance to increase
- Trigger webhook manually → expect balance to update in database

**Performance tests — does it hold:**
- Send 10 concurrent verify requests → all must return in under 5 seconds
- Check that the same image submitted twice does not charge twice incorrectly

**Squad integration tests — the disqualification gate:**
- Confirm Squad virtual account is created for every new client
- Confirm balance deducts correctly after every paid verification
- Confirm webhook updates balance when payment lands
- Confirm low balance returns the payment link in the API response

**David reports all failures as GitHub issues with:** what he did, what he expected, what actually happened. He does not fix. He finds and documents.

**Milestone 5 is done when:** David cannot break the system with normal usage, all Squad transactions fire correctly, and the full demo flow runs three times without intervention.

---

## Milestone 6 — Pitch, Documentation, Rehearsal
### Mathematician leads, everyone reviews

**Mathematician delivers:**

- [ ] 10-slide pitch deck in the exact order from the guidelines document
- [ ] Slide 5 content: model accuracy table with per-class numbers and OOD results
- [ ] Bias analysis: where the model performs poorly and why — written honestly
- [ ] One-pager A4 PDF: problem, solution, Squad APIs used, four pillars addressed
- [ ] Nigerian insurance fraud statistics for slides 1 and 7
- [ ] Year 1 impact numbers with clear assumptions stated

**Pitch deck slide order — from the guidelines:**
1. Problem
2. Target user
3. Solution overview
4. Squad API integration
5. AI and data intelligence
6. User flow
7. Impact potential
8. Scalability and business model
9. Research and validation
10. The team

**Demo rehearsal — three rounds:**

Round 1 — broken run. Do it without preparation. Find every gap.
Round 2 — fixed run. Address every gap from round 1. Time it. Must be under 5 minutes.
Round 3 — pressure run. David asks judge questions mid-demo. Everyone must stay composed.

**Every team member must be able to answer without hesitation:**
- Why Squad APIs specifically — not just "payments"
- What happens when a client's balance runs out
- How does the model detect manipulation versus synthetic generation
- What is your OOD accuracy and what does that mean
- How does this scale beyond the demo

**Milestone 6 is done when:** Full demo runs clean in under 5 minutes, one-pager is printed, deck is 10 slides exactly, and every team member has spoken during rehearsal.

---

## Milestone 7 — Submission Ready
### Abdulmalik coordinates

- [ ] GitHub README complete: what the project does, how to run it, environment variables needed
- [ ] Demo URL live on Render and stable — test it from a different network
- [ ] Squad sandbox showing real transaction history — screenshots saved as backup
- [ ] `.env.example` committed with all keys listed but no values
- [ ] All four team members' names on the pitch deck and one-pager
- [ ] One-pager PDF printed physical copies for judges
- [ ] Backup plan: if live demo fails, recorded walkthrough video ready to play

---

## The One Thing That Will Sink Us

We need to say it together and mean it:

**The Squad transaction must fire visibly during the demo. Not described. Visible. The judge watches the balance decrease in real time.**

Every single rehearsal must include this moment. It must be muscle memory by presentation day.
