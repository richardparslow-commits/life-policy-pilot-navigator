"""Life Policy Pilot Navigator - Streamlit chat frontend.

Calls the Life Policy Pilot FAQ backend (/chat) and renders the answer,
matched FAQs, recommended blog articles, and the booking link.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List

import streamlit as st

from api_client import BackendError, chat

PRIMARY_RED = "#CC0700"
SILVER_GRAY = "#E2E8F0"

# Where to send users who want to reach out for an appointment.
CONTACT_PAGE_URL = "https://lifepolicypilot.blog/contact-2/"

EDUCATIONAL_NOTICE = (
    "Educational use only. This tool is provided for educational and informational "
    "purposes only. It is not financial, legal, or tax advice, and it is not a "
    "recommendation to buy or sell any insurance product. Policy terms, availability, "
    "and rates vary by insurer and state and change over time. Please speak with a "
    "licensed professional about your own situation."
)

st.set_page_config(
    page_title="Life Policy Pilot | Navigator",
    page_icon="🇺🇸",
    layout="centered",
    initial_sidebar_state="expanded",
)

def _backend_url() -> str:
    """Backend URL: Streamlit secrets > env var > local dev default."""
    try:
        return st.secrets["BACKEND_URL"]
    except Exception:
        return os.getenv("BACKEND_URL") or "http://localhost:8000"


BACKEND_URL = _backend_url()

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, {SILVER_GRAY} 0%, #FFFFFF 100%);
    }}
    .block-container {{
        background-color: white;
        padding: 32px !important;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.05);
        margin-top: 20px;
    }}
    h1, h2, h3 {{ color: {PRIMARY_RED} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------- Session state -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role", "content", "meta"?}
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex


def render_article_links(articles: List[Dict[str, Any]]) -> None:
    if not articles:
        return
    with st.expander(f"📰 Recommended articles ({len(articles)})"):
        for a in articles:
            title = a.get("title", "Article")
            url = a.get("url", "")
            if url:
                st.markdown(f"- [{title}]({url})")
            else:
                st.markdown(f"- {title}")


def render_faq_matches(matched: List[Dict[str, Any]]) -> None:
    if not matched:
        return
    with st.expander(f"❓ Related FAQs ({len(matched)})"):
        for m in matched:
            st.markdown(f"**{m.get('question', '')}**")
            if m.get("category"):
                # Scores can exceed 1.0 because of retrieval boosts, so cap the
                # displayed confidence at 100%.
                match = min(m.get("score", 0), 1.0)
                st.caption(f"Category: {m['category']}  ·  Match: {match:.0%}")
            answer = m.get("answer")
            if answer:
                st.markdown(answer)
            st.markdown("---")


def render_educational_cta() -> None:
    """End-of-answer footer: encourage reaching out, with an appointment button
    to the contact page and a legal educational-print disclaimer."""
    st.markdown("---")
    st.markdown(
        "**Have questions, or ready to talk through your life insurance "
        "options?** I'd be glad to help — reach out to set up an appointment."
    )
    st.link_button("📅 Book a consultation", CONTACT_PAGE_URL)
    st.caption(EDUCATIONAL_NOTICE)


def render_assistant_message(msg: Dict[str, Any]) -> None:
    with st.chat_message("assistant"):
        st.markdown(msg["content"])
        meta = msg.get("meta", {})
        disclaimer = meta.get("disclaimer")
        if disclaimer:
            st.caption(disclaimer)
        render_faq_matches(meta.get("matched_faq", []))
        render_article_links(meta.get("recommended_articles", []))
        render_educational_cta()


def send_message(text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)

    try:
        # One retry: free-tier hosts (e.g. Render) cold-start in 30-60s after
        # idle, which can exceed the first request's timeout.
        try:
            data = chat(text, st.session_state.session_id, BACKEND_URL)
        except BackendError:
            data = chat(text, st.session_state.session_id, BACKEND_URL)
    except BackendError as exc:
        st.session_state.messages.append(
            {"role": "assistant", "content": f"⚠️ I couldn't reach the FAQ service right now. {exc}", "meta": {}}
        )
        with st.chat_message("assistant"):
            st.markdown(f"⚠️ I couldn't reach the FAQ service right now. {exc}")
            st.link_button("📅 Schedule a consultation", "https://lifepolicypilot.blog/contact-2/")
        return

    assistant = {
        "role": "assistant",
        "content": data.get("answer", ""),
        "meta": {
            "booking_url": data.get("booking_url"),
            "disclaimer": data.get("disclaimer"),
            "matched_faq": data.get("matched_faq", []),
            "recommended_articles": data.get("recommended_articles", []),
        },
    }
    st.session_state.messages.append(assistant)
    render_assistant_message(assistant)


# ----------------------- Sidebar -----------------------
with st.sidebar:
    st.title("🇺🇸 Life Policy Pilot")
    st.markdown(
        "An interactive guide to life insurance — policies, coverage, "
        "claims, and more. Answers come from our curated FAQ knowledge base."
    )
    st.link_button("📅 Schedule a consultation", "https://lifepolicypilot.blog/contact-2/")
    st.caption(f"Backend: {BACKEND_URL}")
    st.divider()
    st.caption(
        "🔒 Privacy: please don't share SSNs, bank details, or other "
        "sensitive personal information in chat."
    )

# ----------------------- Header -----------------------
st.title("🇺🇸 Life Policy Pilot Navigator")
st.caption("Interactive navigation & guidance for life insurance concepts.")

# ----------------------- Chat -----------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        render_assistant_message(msg)

if prompt := st.chat_input("Ask about life insurance..."):
    send_message(prompt)

# ----------------------- Footer -----------------------
st.markdown("---")
st.caption("⭐ Proudly built for the Lone Star State — Texas")
