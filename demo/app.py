"""FigureOut — Interactive Streamlit Demo

A startup advisor chatbot that routes questions to specialist roles:
  - market_research  → market sizing, competitors, trends
  - technical_advice → tech stack, architecture, engineering
  - fundraising      → funding, pitch, investor relations
  - off_topic        → graceful fallback

Run:
    streamlit run demo/app.py
"""

import asyncio
import json

import streamlit as st

from figureout import FigureOut, LLM, RoleDefinition

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="FigureOut Demo",
    page_icon="🧩",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------

ROLES = {
    "market_research": RoleDefinition(
        prompt=(
            "You are a startup market research analyst. "
            "Provide concise, data-driven insights on market size, competitors, and trends. "
            "Be specific and actionable."
        ),
        schema=json.dumps({
            "summary": "string — 1-2 sentence overview",
            "key_points": ["string — insight 1", "string — insight 2"],
            "recommendation": "string — next step for the founder",
        }),
        guideline="questions about market size, competitors, industry trends, target customers, or market opportunities",
    ),
    "technical_advice": RoleDefinition(
        prompt=(
            "You are a senior software architect advising early-stage startups. "
            "Give practical, opinionated advice on tech stack, architecture, and engineering decisions. "
            "Favour simplicity and speed-to-market."
        ),
        schema=json.dumps({
            "summary": "string — 1-2 sentence overview",
            "key_points": ["string — advice 1", "string — advice 2"],
            "recommendation": "string — concrete next step",
        }),
        guideline="questions about technology stack, software architecture, engineering decisions, APIs, databases, or infrastructure",
    ),
    "fundraising": RoleDefinition(
        prompt=(
            "You are a startup fundraising advisor with experience in seed and Series A rounds. "
            "Give honest, direct advice on funding strategy, pitch decks, and investor relations."
        ),
        schema=json.dumps({
            "summary": "string — 1-2 sentence overview",
            "key_points": ["string — advice 1", "string — advice 2"],
            "recommendation": "string — concrete next step",
        }),
        guideline="questions about fundraising, investors, pitch decks, valuations, term sheets, or funding rounds",
    ),
    "off_topic": RoleDefinition(
        prompt="Politely explain that you are a startup advisor and can only help with market research, technical decisions, or fundraising topics.",
        schema=json.dumps({"message": "string"}),
        guideline="anything unrelated to startups, technology, markets, or fundraising",
    ),
}

ROLE_LABELS = {
    "market_research": "📊 Market Research",
    "technical_advice": "⚙️ Technical Advice",
    "fundraising": "💰 Fundraising",
    "off_topic": "🚫 Off Topic",
}

PROVIDER_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "meta": "META_API_KEY",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "claude": "claude-haiku-4-5-20251001",
    "groq": "llama-3.3-70b-versatile",
    "mistral": "mistral-small-latest",
    "meta": "Llama-4-Scout-17B-16E-Instruct",
}

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🧩 FigureOut")
    st.caption("Lightweight multi-LLM orchestrator")
    st.divider()

    provider = st.selectbox(
        "LLM Provider",
        options=list(PROVIDER_ENV_KEYS.keys()),
        format_func=lambda p: p.capitalize(),
    )

    model = st.text_input("Model version", value=DEFAULT_MODELS[provider])

    api_key = st.text_input(
        f"API Key ({PROVIDER_ENV_KEYS[provider]})",
        type="password",
        placeholder="Paste your API key here",
    )

    show_debug = st.toggle("Show debug info", value=False)

    st.divider()
    st.markdown("**Example questions**")
    examples = [
        "Who are the main competitors in the AI coding assistant market?",
        "Should I use PostgreSQL or MongoDB for a SaaS app?",
        "How do I prepare for a seed round pitch?",
        "What's the best pizza topping?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["prefill"] = ex

# ---------------------------------------------------------------------------
# FigureOut instance — cached so it's created once per config change
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_engine(provider: str, model: str, api_key: str, verbose: bool) -> FigureOut:
    return FigureOut(
        llm=provider,
        llm_version=model,
        roles=ROLES,
        api_key=api_key or None,
        verbose=verbose,
        cache_enabled=True,
    )

# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

st.title("🚀 Startup Advisor")
st.caption(
    "Powered by **FigureOut** — ask anything about markets, tech, or fundraising. "
    "Watch how FigureOut routes your question to the right specialist."
)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("role_tag"):
            st.caption(f"Routed to: {msg['role_tag']}")

# Input — support sidebar example button prefill
prefill = st.session_state.pop("prefill", "")
query = st.chat_input("Ask your startup question…", key="chat_input") or prefill

if query:
    # Show user message
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    if not api_key:
        st.warning(f"Enter your {PROVIDER_ENV_KEYS[provider]} in the sidebar to continue.", icon="🔑")
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                engine = get_engine(provider, model, api_key, verbose=True)
                raw = asyncio.run(engine.run(query))

                # Extract response and debug info
                response = raw.get("response", raw)
                debug = raw.get("debug", {})
                roles_selected = debug.get("roles_selected", [])
                role_tag = ROLE_LABELS.get(roles_selected[0], "") if roles_selected else ""

                # Render response
                if "message" in response:
                    # off_topic fallback
                    st.info(response["message"])
                else:
                    st.markdown(f"**{response.get('summary', '')}**")

                    key_points = response.get("key_points", [])
                    if key_points:
                        for point in key_points:
                            st.markdown(f"- {point}")

                    rec = response.get("recommendation", "")
                    if rec:
                        st.success(f"**Next step:** {rec}")

                if role_tag:
                    st.caption(f"Routed to: {role_tag}")

                # Debug panel
                if show_debug and debug:
                    with st.expander("Debug info"):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Input tokens", debug.get("input_tokens", 0))
                        col2.metric("Output tokens", debug.get("output_tokens", 0))
                        col3.metric("Roles matched", len(debug.get("roles_matched", [])))
                        st.json(debug)

                # Save to history
                content_lines = []
                if "message" in response:
                    content_lines.append(response["message"])
                else:
                    if response.get("summary"):
                        content_lines.append(f"**{response['summary']}**")
                    for point in response.get("key_points", []):
                        content_lines.append(f"- {point}")
                    if response.get("recommendation"):
                        content_lines.append(f"\n**Next step:** {response['recommendation']}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "\n".join(content_lines),
                    "role_tag": role_tag,
                })

            except Exception as exc:
                st.error(f"Error: {exc}")
