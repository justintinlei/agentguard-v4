"""AgentGuard v2 - Grounded AI Analyst. Streamlit page: page
configuration, title, disclaimer, selecting one controlled synthetic
agent, mock/live mode controls that make a live call structurally
impossible without a real API key, the deterministic decision shown
visually separate from Claude's generated explanation, citations with
their real source name and passage so a user can verify them, usage/cost
evidence, and safe (traceback-free) error messages on failure.
"""

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from policy_library import load_policy_chunks
from scanner import Agent, evaluate_agent
from v2_service import POLICIES_DIR, analyze_agent

load_dotenv()

st.set_page_config(page_title="AgentGuard v2 - Grounded AI Analyst", page_icon="🛡️", layout="wide")

st.title("🛡️ AgentGuard v2 - Grounded AI Analyst")
st.write(
    "Shows v1's unchanged deterministic risk score alongside a Claude-generated "
    "explanation, validated and cited before anything is displayed."
)
st.warning(
    "This page uses only synthetic, made-up agent data - no real systems or personal information.",
    icon="⚠️",
)

BASE_DIR = Path(__file__).resolve().parent
ENVIRONMENT_PATH = BASE_DIR / "sample_environment_before.json"

agents = json.loads(ENVIRONMENT_PATH.read_text())
agent_names = [agent["agent_name"] for agent in agents]
selected_name = st.selectbox("Select a synthetic agent", agent_names)
selected_agent = next(agent for agent in agents if agent["agent_name"] == selected_name)

st.subheader("Input agent")
st.json(selected_agent)

has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
mode = st.radio("Analysis mode", ["mock", "live"], horizontal=True)

if mode == "live" and not has_api_key:
    st.error(
        "Live mode needs ANTHROPIC_API_KEY set in your .env file. "
        "Add it there, or switch back to mock mode - mock mode is always free and needs no key."
    )

if st.button("Analyze selected agent", disabled=(mode == "live" and not has_api_key)):
    agent = Agent(**selected_agent)
    try:
        scan_result = evaluate_agent(agent)
        analysis, usage = analyze_agent(agent, mode=mode)
        st.session_state["v2_result"] = (scan_result, analysis, usage)
        st.success("Analysis complete.")
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")

if "v2_result" in st.session_state:
    scan_result, analysis, usage = st.session_state["v2_result"]

    st.subheader("Deterministic decision - source of truth")
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk level", scan_result.risk_level)
    col2.metric("Risk score", scan_result.score)
    col3.metric("Findings", len(scan_result.findings))

    if scan_result.findings:
        for finding in scan_result.findings:
            with st.expander(f"{finding.rule_id} - {finding.title} ({finding.severity}, {finding.points} pts)"):
                st.write(finding.explanation)
                st.write(finding.recommendation)
    else:
        st.caption("No findings - this agent triggered none of the five deterministic rules.")

    with st.container(border=True):
        st.subheader("Claude's explanation (generated text - cannot change the score above)")
        st.write(analysis.summary)
        st.info(analysis.why_it_matters)
        st.success(analysis.recommended_next_step)

        st.subheader("Citations - verify these yourself")
        chunks_by_id = {chunk.chunk_id: chunk for chunk in load_policy_chunks(POLICIES_DIR)}
        for citation in analysis.citations:
            source_chunk = chunks_by_id.get(citation.chunk_id)
            title = source_chunk.title if source_chunk else citation.chunk_id
            # Show a path relative to the project, never the full local
            # filesystem path (which would leak the machine's username).
            source_path = str(Path(source_chunk.source_path).relative_to(BASE_DIR)) if source_chunk else "unknown source"
            with st.expander(f"{citation.chunk_id} - {title}"):
                st.write(f'"{citation.quote}"')
                st.caption(source_path)

    st.subheader("Usage & cost evidence")
    cost_cols = st.columns(5)
    cost_cols[0].metric("Mode", usage.mode)
    cost_cols[1].metric("Model", usage.model)
    cost_cols[2].metric("Tokens (in/out)", f"{usage.input_tokens}/{usage.output_tokens}")
    cost_cols[3].metric("Latency", f"{usage.latency_ms} ms")
    cost_cols[4].metric("Est. cost", f"${usage.estimated_cost_usd:.4f}")
