"""Unit tests for the API client (no network, no Streamlit needed)."""
from __future__ import annotations

import pytest
import requests

from api_client import BackendError, chat


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_chat_posts_correct_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(200, {"answer": "hi", "matched_faq": []})

    monkeypatch.setattr(requests, "post", fake_post)
    result = chat("what is term life", "abc123", "http://localhost:8000/")

    assert captured["url"] == "http://localhost:8000/chat"
    assert captured["json"] == {"message": "what is term life", "sessionId": "abc123"}
    assert captured["timeout"] == 30.0
    assert result == {"answer": "hi", "matched_faq": []}


def test_chat_strips_trailing_slash(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        requests,
        "post",
        lambda url, json, timeout: captured.update(url=url) or FakeResponse(200, {}),
    )
    chat("hi", "s", "https://api.example.com/")
    assert captured["url"] == "https://api.example.com/chat"


def test_chat_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(500, {}))
    with pytest.raises(BackendError, match="500"):
        chat("hi", "s", "http://localhost:8000")


def test_chat_raises_on_network_error(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "post", boom)
    with pytest.raises(BackendError, match="Could not reach"):
        chat("hi", "s", "http://localhost:8000")


def test_chat_raises_on_invalid_json(monkeypatch):
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: FakeResponse(200, ValueError("bad json"))
    )
    with pytest.raises(BackendError, match="invalid response"):
        chat("hi", "s", "http://localhost:8000")