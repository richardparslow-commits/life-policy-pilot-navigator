# Life Policy Pilot Navigator (Streamlit frontend)

[![CI](https://github.com/richardparslow-commits/life-policy-pilot-navigator/actions/workflows/ci.yml/badge.svg)](https://github.com/richardparslow-commits/life-policy-pilot-navigator/actions/workflows/ci.yml)

Chat frontend for the Life Policy Pilot FAQ backend
(`richardparslow-commits/life-policy-pilot-backend`). It sends questions
to the backend `/chat` endpoint and renders the answer, related FAQs,
recommended blog articles, and the consultation booking link.

## About

**Life Policy Pilot Navigator** is a conversational life-insurance guide:
ask a question and it answers from a curated knowledge base, showing which
FAQs it drew from and recommending related LifePolicyPilot.blog articles.
It covers policy types (term, whole life, universal, IUL, return-of-premium),
cost and coverage, claims and beneficiaries, health-related qualifying
(diabetes, cancer survivors, veterans/VGLI, pre-existing conditions), cash
value, riders, and Texas-specific rules — and describes what each of the
**17 carriers** on the SFG Carrier Quotes panel sells and what each product
is for (term, whole life, IUL, annuities, final expense, mortgage
protection, and more).

Every answer carries a "general information, not financial/legal/tax
advice" disclaimer and a consultation booking link, and a privacy guardrail
keeps the chat from collecting SSNs, bank/card numbers, or ID details.

The frontend talks to the FastAPI backend in this project's companion repo
(`richardparslow-commits/life-policy-pilot-backend`); see **Deploy** below
for the two live pieces and how they are wired together.

## Run locally

    pip install -r requirements.txt
    streamlit run streamlit_app.py

Point the app at your backend by creating `.streamlit/secrets.toml`
(see `.streamlit/secrets.toml.example`) or setting `BACKEND_URL`:

    BACKEND_URL="http://localhost:8000" streamlit run streamlit_app.py

## Deploy

Full two-sided runbook (backend on Render + frontend on Streamlit Community
Cloud + wiring): see **DEPLOYMENT.md**.

**Live deployment (current):**
- Frontend: https://life-policy-pilot-navigator1984.streamlit.app
- Backend: https://life-policy-pilot-backend-1.onrender.com
  (`BACKEND_URL` secret ⇒ `ALLOWED_ORIGINS` allowlist — both wired)

## Test

    pip install -r requirements-dev.txt
    python -m pytest tests/ -q

### End-to-end tests (real backend + Navigator)

`tests/test_integration.py` boots the actual backend (uvicorn subprocess)
and drives it with the real API client and Streamlit UI — no mocking on the
backend side. CI runs it in a separate `integration` job that needs read
access to the private backend repo:

1. Create a fine-grained PAT (GitHub → Settings → Developer settings →
   Fine-grained personal access tokens): repository access **only**
   `richardparslow-commits/life-policy-pilot-backend`, with
   **Contents: Read-only** (Metadata read-only comes automatically).
2. Add it as a repository secret named `BACKEND_REPO_TOKEN` in **this** repo
   (Settings → Secrets and variables → Actions).
3. The `integration` job activates on the next push; it is skipped until the
   secret exists, so CI never breaks while it is missing.

Run locally (requires a backend checkout):

    BACKEND_PATH=../life-policy-pilot-backend \
    BACKEND_PYTHON=../life-policy-pilot-backend/.venv/bin/python \
    python -m pytest tests/test_integration.py -q