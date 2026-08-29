"""UI tests for the Streamlit app using Streamlit's AppTest harness.

These run the real app headlessly with the HTTP transport mocked, so no
backend or network is needed. They cover boot (including the no-secrets
case), chat rendering (answer, related FAQs, articles, booking link), and
the single-retry path in send_message().
"""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import requests
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")

SAMPLE_RESPONSE = {
    "answer": "Term life insurance provides coverage for a fixed period.",
    "disclaimer": "General information only.",
    "booking_url": "https://calendar.app.google/test",
    "matched_faq": [
        {"question": "What is term life insurance?", "category": "policies", "score": 0.9}
    ],
    "recommended_articles": [
        {"title": "Term Life Basics", "url": "https://lifepolicypilot.blog/term-life/"}
    ],
}


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self) -> dict:
        return self._payload


def start_app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=20)


def send_chat(at: AppTest, text: str) -> AppTest:
    at.run()  # boot the app so widgets exist
    at.chat_input[0].set_value(text)
    at.run()
    return at


def booking_link_labels(at: AppTest) -> list:
    """Labels of all rendered link buttons (AppTest exposes them via get())."""
    return [b.proto.label for b in at.get("link_button")]


def test_app_boots_without_secrets_file() -> None:
    """Regression: st.secrets access must not crash when no secrets file exists."""
    at = start_app()
    at.run()
    assert len(at.exception) == 0
    assert at.session_state["session_id"]
    assert at.session_state["messages"] == []


def test_chat_renders_answer_and_meta() -> None:
    at = start_app()
    with mock.patch("api_client.requests.post", return_value=FakeResponse(200, SAMPLE_RESPONSE)):
        send_chat(at, "what is term life insurance")

    assert len(at.exception) == 0
    messages = at.session_state["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[-1]["content"] == SAMPLE_RESPONSE["answer"]

    rendered = [m.value for m in at.markdown]
    assert SAMPLE_RESPONSE["answer"] in rendered
    # Every answer ends with a CTA button to the contact page.
    assert any("Book a consultation" in label for label in booking_link_labels(at))
    assert any("Have questions" in m.value for m in at.markdown)
    assert any("Educational use only" in c.value for c in at.caption)
    assert any("Related FAQs" in e.label for e in at.expander)
    assert any("Recommended articles" in e.label for e in at.expander)


def test_chat_retries_once_then_succeeds() -> None:
    """First call fails (e.g. free-tier cold start); the single retry succeeds."""
    at = start_app()
    side_effect = [requests.ConnectionError("cold start"), FakeResponse(200, SAMPLE_RESPONSE)]
    with mock.patch("api_client.requests.post", side_effect=side_effect) as post:
        send_chat(at, "what is term life insurance")

    assert post.call_count == 2  # exactly one retry, no more
    assert len(at.exception) == 0
    assert at.session_state["messages"][-1]["content"] == SAMPLE_RESPONSE["answer"]


def test_chat_retry_fails_shows_error_card() -> None:
    """Both attempts fail -> graceful error card, not a crash."""
    at = start_app()
    with mock.patch("api_client.requests.post", side_effect=requests.ConnectionError("down")) as post:
        send_chat(at, "what is term life insurance")

    assert post.call_count == 2
    assert len(at.exception) == 0
    last = at.session_state["messages"][-1]
    assert last["role"] == "assistant"
    assert last["content"].startswith("⚠️")
    assert any("Schedule a consultation" in label for label in booking_link_labels(at))


def test_chat_backend_http_error_is_rendered_not_crashed() -> None:
    at = start_app()
    with mock.patch("api_client.requests.post", return_value=FakeResponse(500, {})):
        send_chat(at, "hi")

    assert len(at.exception) == 0
    assert at.session_state["messages"][-1]["content"].startswith("⚠️")