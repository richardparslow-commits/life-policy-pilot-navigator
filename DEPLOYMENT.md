# Deployment runbook

This app is two pieces that must both be live and wired together:

1. **Backend** — `richardparslow-commits/life-policy-pilot-backend` (FastAPI FAQ service)
2. **Frontend** — this repo (`life-policy-pilot-navigator`, Streamlit chat UI)

The frontend reads the backend's URL from the `BACKEND_URL` secret, and the
backend only answers browser calls from origins in its `ALLOWED_ORIGINS`
allowlist. Both must be configured.

---

## 1. Deploy the backend (Render)

The backend repo is deployment-ready: `Procfile` start command, `.python-version`
(bare `3.12.9`, which Render's native runtime reads), and a fixed `Dockerfile`
as an alternative. Recommended path — **Native (Python) runtime** (fast wheel
builds):

1. Go to https://dashboard.render.com → **New → Web Service**.
2. Connect the `richardparslow-commits/life-policy-pilot-backend` repo.
3. Choose the **Native** (Python) environment. Render pre-fills the start
   command from the `Procfile`; it must be:
   ```
   uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
   (The `Dockerfile` route also works if you prefer Docker; both were fixed
   and verified.)
4. Optionally set `PYTHON_VERSION=3.12.9` (belt-and-suspenders; the repo's
   `.python-version` already pins it).
5. Add the environment variables (everything else has a sane default):
   | Variable | Value |
   |---|---|
   | `ALLOWED_ORIGINS` | `https://lifepolicypilot.blog,https://www.lifepolicypilot.blog,https://<your-app-name>.streamlit.app` |
   | `ADMIN_TOKEN` | (optional) a long random string if you want to use `/admin/refresh-articles` |
6. Deploy. Note the service URL, e.g. `https://life-policy-pilot-backend.onrender.com`.
7. Verify: `curl https://<your-service>.onrender.com/health` → `{"ok": true, "kb_items": 48, ...}`.

> **Free tier note:** Render free web services sleep after ~15 minutes idle and
> take 30–60s to cold-start. The frontend retries once with a 30s timeout, so
> the first question after idle may feel slow but should succeed.

## 2. Deploy the frontend (Streamlit Community Cloud)

1. This repo must be on GitHub (`richardparslow-commits/life-policy-pilot-navigator`).
   It is private; Streamlit Cloud supports private repos (free tier includes one).
2. Go to https://share.streamlit.io (or the Streamlit dashboard) → **Create app**.
3. Pick the repo, branch `main`, main file `streamlit_app.py` → **Deploy**.
4. Note the app URL, e.g. `https://life-policy-pilot-navigator.streamlit.app`.

## 3. Wire them together

1. **Backend → allow the frontend:** if the Streamlit app URL differs from the
   default allowlist, edit `ALLOWED_ORIGINS` on Render to include
   `https://<your-app-name>.streamlit.app` and redeploy (or just save — Render
   redeploys on env change).
2. **Frontend → point at the backend:** in Streamlit Cloud, open the app →
   **Settings → Secrets** and add:
   ```toml
   BACKEND_URL = "https://<your-service>.onrender.com"
   ```
   The app restarts automatically with the new secret.
3. Verify end-to-end: open the app, ask "what is term life insurance", and
   confirm you get the FAQ answer plus recommended articles.

## Notes

- The deployed app URL is public even though the repo is private — anyone with
  the link can use the chat (that is the point of the Navigator).
- If you want to reuse the existing `life-policy-pilot-navigator.streamlit.app`
  URL, delete the old app first — Streamlit app names are unique per account.
- `secrets.toml` is git-ignored; the app also boots without it (it falls back
  to `http://localhost:8000`), so a missing secret never crashes the deploy.