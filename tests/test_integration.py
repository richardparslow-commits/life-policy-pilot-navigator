"""End-to-end integration tests: real backend + real Navigator.

Boots the actual FastAPI backend from the life-policy-pilot-backend repo as
a uvicorn subprocess, then drives it with the real api_client and the real
Streamlit UI (AppTest). No HTTP mocking anywhere on the backend side.

Requires a backend checkout:
- CI: the ``integration`` job checks out the private backend repo with a
  read-only PAT (secret ``BACKEND_REPO_TOKEN``) into ``./backend`` and sets
  ``BACKEND_PATH=backend``.
- Local: ``BACKEND_PATH`` may point at any backend checkout, and
  ``BACKEND_PYTHON`` at an interpreter that has its requirements installed
  (defaults to the current interpreter).

The suite skips when no backend checkout is available (e.g. plain unit runs).
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

BACKEND_PATH = os.getenv(
    "BACKEND_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "life-policy-pilot-backend"),
)
BACKEND_PYTHON = os.getenv("BACKEND_PYTHON", sys.executable)
BACKEND_APP_PY = Path(BACKEND_PATH) / "app.py"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not BACKEND_APP_PY.exists(), reason="backend checkout not present (set BACKEND_PATH)"),
]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def backend_url() -> str:
    """Boot the real backend on a free port and yield its base URL."""
    port = _free_port()
    env = dict(os.environ)
    # Pin the RSS feed to a fast-failing URL so startup and per-request
    # refreshes never touch the network (keeps the test deterministic).
    env["BLOG_RSS_URL"] = "http://127.0.0.1:1/feed"
    env["ARTICLES_REFRESH_SECONDS"] = "999999"
    proc = subprocess.Popen(
        [
            BACKEND_PYTHON,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=BACKEND_PATH,
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"backend exited early with code {proc.returncode}")
        try:
            if requests.get(f"{url}/health", timeout=2).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.25)
    else:
        proc.terminate()
        pytest.fail("backend did not become ready within 45s")
    try:
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_health_endpoint(backend_url: str) -> None:
    resp = requests.get(f"{backend_url}/health", timeout=5)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["kb_items"] >= 40  # the real knowledge base is loaded


def test_api_client_chats_with_live_backend(backend_url: str) -> None:
    from api_client import chat

    data = chat("what is term life insurance", "e2e-session", backend_url)

    # Full contract the Navigator UI renders:
    assert isinstance(data["answer"], str) and len(data["answer"]) > 20
    assert "term" in data["answer"].lower()
    assert data["needs_clarification"] is False
    assert data["booking_url"].startswith("http")
    assert data["disclaimer"]
    # Well-covered question must return a real matched FAQ...
    assert data["matched_faq"], "expected at least one matched FAQ"
    first = data["matched_faq"][0]
    assert first["id"] and first["question"] and first["category"]
    assert isinstance(first["score"], float)
    # The matched FAQ must include its answer so the UI can render it.
    assert first["answer"], "matched FAQ is missing its answer text"
    # ...and articles are shaped correctly (may be empty: feed is pinned off)
    assert isinstance(data["recommended_articles"], list)
    for article in data["recommended_articles"]:
        assert article["title"] and article["url"].startswith("http")


def test_tool_endpoint_live_backend(backend_url: str) -> None:
    resp = requests.post(
        f"{backend_url}/tools/life_insurance_faq",
        json={"query": "how do i cancel my policy"},
        timeout=10,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["matched_faq"]
    assert body["matched_faq"][0]["id"] == "policies_006"  # the cancellation FAQ
    assert body["booking_url"].startswith("http")


def test_streamlit_ui_chats_with_live_backend(backend_url: str, monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("BACKEND_URL", backend_url)
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "streamlit_app.py"), default_timeout=20)
    at.run()
    at.chat_input[0].set_value("what is term life insurance")
    at.run()

    assert len(at.exception) == 0
    last = at.session_state["messages"][-1]
    assert last["role"] == "assistant"
    assert not last["content"].startswith("⚠️"), "UI should reach the live backend"
    assert "term life" in last["content"].lower()
    # Related FAQs expander appears (real backend returned a match)
    assert any("Related FAQs" in e.label for e in at.expander)