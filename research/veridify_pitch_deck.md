# Veridify Pitch Deck

Built from the current repository state and the slide order shown in the challenge guide image.

## Slide 1 - Problem
- AI-generated and manipulated images are getting cheap, fast, and convincing.
- Veridify's backend spec frames the core pain clearly: Nigerian insurance fraud is costly, image review is still manual, and existing tools are either expensive or disconnected from local workflows.
- Teams need a faster trust decision before approving claims, listings, or public-facing content.

## Slide 2 - Target User
- Primary user: insurance claims reviewers and fraud teams.
- Secondary users: marketplace trust teams, fact-checkers, and compliance or operations teams that receive user-submitted images.
- Buyer: organizations that want an API-first verification layer instead of another standalone dashboard.

## Slide 3 - Solution Overview
- Veridify is an AI-powered media verification product with a FastAPI backend and a Next.js frontend demo.
- The product flow already exists in code: create account, fund wallet, upload image, get verdict, review transaction history.
- Each verification returns a trust score, verdict, confidence, processing time, and signal breakdown.

## Slide 4 - Squad API Integration
- Squad is wired into the product, not added as a cosmetic payment badge.
- Onboarding creates a dedicated virtual account, funding creates a checkout flow, and a webhook confirms wallet top-ups.
- Every verification deducts NGN 175 from the user's balance, so the money trail stays visible throughout the demo.

## Slide 5 - AI / Data Intelligence
- The backend is already designed for three outcomes: AUTHENTIC, MANIPULATED, and SYNTHETIC.
- Today's shipped build uses deterministic mock inference for stable demos and frontend integration.
- The model contract is already prepared for a dual-branch architecture: EfficientNetB0 spatial analysis plus frequency-domain features, returned as trust score plus spatial and frequency breakdown scores.

## Slide 6 - User Flow
- The frontend implements the full five-screen demo journey: onboarding, dashboard, verify, result, and transactions.
- The verify screen supports drag-and-drop upload and live processing feedback.
- The result and transaction screens tie the AI verdict directly to wallet deductions and audit history.

## Slide 7 - Impact Potential
- Veridify helps teams decide faster when a wrong image decision costs money, trust, or time.
- The strongest early wedge is insurance fraud review, with the same engine reusable for marketplaces and fact-checking.
- Revenue assumption for pitch math: 10,000 verifications per month at NGN 175 each equals NGN 1.75M monthly gross verification revenue.

## Slide 8 - Scalability & Business Model
- Business model: pay-per-verification through a pre-funded Squad wallet.
- The architecture is already API-first: stateless API keys, async backend, cached repeat checks, and frontend/backend separation.
- This can scale from the demo dashboard into partner APIs, internal trust tools, or future channels without changing the core verification engine.

## Slide 9 - Research & Validation
- The repo shows strong implementation validation: webhook logging, rate limiting, balance tracking, transaction history, and QA coverage for key flows.
- The product docs also anchor the problem in Nigerian fraud and manipulated-media risk.
- The honest next step is external validation: real model metrics, pilot users, and production threshold tuning.

## Slide 10 - Team
- Abdulmalik: ML engineering and backend.
- Peter: frontend experience and live demo flow.
- David: QA, testing, and failure discovery.
- Mathematician: research, documentation, and pitch support.

## Repo Evidence
- Backend product definition: `backend/VERIDIFI_PROJECT_SPECIFICATIONS.md`
- Build and demo milestones: `PROJECT_MILESTONE.md`
- Frontend flow: `frontend/components/screens/onboarding-screen.tsx`
- Frontend wallet and funding story: `frontend/components/screens/dashboard-screen.tsx`
- Frontend verification story: `frontend/components/screens/verify-screen.tsx`
- Frontend result story: `frontend/components/screens/result-screen.tsx`
- Frontend audit story: `frontend/components/screens/transactions-screen.tsx`
- Frontend/backend contract layer: `frontend/lib/live-api.ts`
- API assembly and routes: `backend/app/main.py`, `backend/app/routes/account.py`, `backend/app/routes/verify.py`, `backend/app/routes/webhook.py`
