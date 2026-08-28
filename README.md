# Life Policy Pilot Navigator (Streamlit frontend)

[![CI](https://github.com/richardparslow-commits/life-policy-pilot-navigator/actions/workflows/ci.yml/badge.svg)](https://github.com/richardparslow-commits/life-policy-pilot-navigator/actions/workflows/ci.yml)

Chat frontend for the Life Policy Pilot FAQ backend
(`richardparslow-commits/life-policy-pilot-backend`). It sends questions
to the backend `/chat` endpoint and renders the answer, related FAQs,
recommended blog articles, and the consultation booking link.

## Run locally

    pip install -r requirements.txt
    streamlit run streamlit_app.py

Point the app at your backend by creating `.streamlit/secrets.toml`
(see `.streamlit/secrets.toml.example`) or setting `BACKEND_URL`:

    BACKEND_URL="http://localhost:8000" streamlit run streamlit_app.py

## Deploy

Full two-sided runbook (backend on Render + frontend on Streamlit Community
Cloud + wiring): see **DEPLOYMENT.md**.

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