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