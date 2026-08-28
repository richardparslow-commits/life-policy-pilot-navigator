"""HTTP client for the Life Policy Pilot FAQ backend.

Kept separate from the Streamlit UI so it can be unit-tested without a
browser or a running backend.
"""
from __future__ import annotations

from typing import Any, Dict

import requests


class BackendError(Exception):
    """Raised when the backend can't be reached or returns an error."""


def chat(message: str, session_id: str, base_url: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Send a chat message to the backend and return its response dict.

    Raises BackendError on network failure, timeout, or a non-200 response.
    """
    url = base_url.rstrip("/") + "/chat"
    try:
        resp = requests.post(
            url,
            json={"message": message, "sessionId": session_id},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise BackendError(f"Could not reach the backend at {url}: {exc}") from exc

    if resp.status_code != 200:
        raise BackendError(f"Backend returned HTTP {resp.status_code}")

    try:
        return resp.json()
    except ValueError as exc:
        raise BackendError("Backend returned an invalid response") from exc