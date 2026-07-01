import os

import requests
import streamlit as st

st.set_page_config(
    page_title="Vijay Diagnostics — Chat Assistant",
    page_icon="🩺",
    layout="centered",
)

# --- Config ---
# Locally: defaults to your local backend.
# On Streamlit Community Cloud: set API_BASE_URL in the app's Secrets
# (Settings -> Secrets) to your EC2 backend's public address, e.g.
# "http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com:8000"
def _get_api_base_url() -> str:
    try:
        if "API_BASE_URL" in st.secrets:
            return st.secrets["API_BASE_URL"]
    except Exception:
        pass  # no secrets.toml present (normal for local dev) - fall through
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


API_BASE_URL = _get_api_base_url()

# Temporary debug - remove after confirming deployment works
st.sidebar.caption(f"🔗 API: {API_BASE_URL}")

# --- Theme: clinical teal/blue, clean and trustworthy ---
PRIMARY = "#0E7C7B"      # deep teal
PRIMARY_DARK = "#0A5C5B"
ACCENT = "#E8F6F6"       # pale teal background
TEXT_DARK = "#1A2B2B"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #F7FAFA;
    }}
    .vd-header {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }}
    .vd-header h1 {{
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }}
    .vd-header p {{
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        opacity: 0.9;
    }}
    .vd-badge {{
        display: inline-block;
        background: rgba(255,255,255,0.15);
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }}
    .vd-suggestion-btn {{
        background: {ACCENT};
        border: 1px solid {PRIMARY};
        color: {PRIMARY_DARK};
    }}
    [data-testid="stChatMessage"] {{
        border-radius: 12px;
    }}
    .vd-sources {{
        font-size: 0.8rem;
        color: #5A6B6B;
        margin-top: 0.4rem;
        padding: 0.5rem 0.8rem;
        background: {ACCENT};
        border-radius: 8px;
        border-left: 3px solid {PRIMARY};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
st.markdown(
    """
    <div class="vd-header">
        <h1>🩺 Vijay Diagnostics</h1>
        <p>Your AI assistant for tests, pricing, packages, and bookings</p>
        <span class="vd-badge">● Online — typically replies instantly</span>
    </div>
    """,
    unsafe_allow_html=True,
)

def wake_backend():
    """Silently ping the backend on app load to warm it up before the user sends a message."""
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=60)
    except Exception:
        pass  # Silent - don't show an error before the user does anything


# Warm up the backend silently on every page load
wake_backend()

# --- Session state ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": ..., "content": ..., "sources": [...]}


def call_chat_api(message: str):
    """Calls the backend /chat endpoint. Returns (answer, sources) or (error_message, None)."""
    payload = {"message": message}
    if st.session_state.session_id:
        payload["session_id"] = st.session_state.session_id

    try:
        resp = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=60)
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ I can't reach the server right now. Please make sure the backend "
            "API is running, then refresh this page.",
            None,
        )
    except requests.exceptions.Timeout:
        return "⚠️ The request took too long. Please try again.", None

    if resp.status_code != 200:
        detail = resp.json().get("detail", "Unknown error") if resp.headers.get(
            "content-type", ""
        ).startswith("application/json") else resp.text
        return f"⚠️ Something went wrong: {detail}", None

    data = resp.json()
    st.session_state.session_id = data["session_id"]
    return data["answer"], data.get("sources", [])


# --- Sidebar: info + reset ---
with st.sidebar:
    st.markdown("### About this assistant")
    st.write(
        "I can help with:\n"
        "- Test pricing & catalog\n"
        "- Fasting / prep instructions\n"
        "- Health checkup packages\n"
        "- Home sample collection\n"
        "- Report delivery timelines\n"
        "- Branch locations & timings"
    )
    st.divider()
    if st.button("🔄 Start New Conversation", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Session ID: `{st.session_state.session_id or 'not started'}`")

# --- Suggested questions (shown only at the start of a conversation) ---
if not st.session_state.messages:
    st.write("**Try asking:**")
    suggestions = [
        "What's the cost of a Lipid Profile test?",
        "Do I need to fast for a Thyroid test?",
        "What's in the Comprehensive Health Checkup package?",
        "How does home sample collection work?",
    ]
    cols = st.columns(2)
    for i, q in enumerate(suggestions):
        if cols[i % 2].button(q, key=f"sugg_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q, "sources": None})
            answer, sources = call_chat_api(q)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
            st.rerun()

# --- Render chat history ---
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🩺"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        if msg.get("sources"):
            sections = ", ".join(sorted({s["section"] for s in msg["sources"] if s.get("section")}))
            if sections:
                st.markdown(f'<div class="vd-sources">📄 Based on: {sections}</div>', unsafe_allow_html=True)

# --- Chat input ---
user_input = st.chat_input("Ask about tests, pricing, packages, or bookings...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "sources": None})
    with st.chat_message("user", avatar="🧑"):
        st.write(user_input)

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner("Checking..."):
            answer, sources = call_chat_api(user_input)
        st.write(answer)
        if sources:
            sections = ", ".join(sorted({s["section"] for s in sources if s.get("section")}))
            if sections:
                st.markdown(f'<div class="vd-sources">📄 Based on: {sections}</div>', unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
