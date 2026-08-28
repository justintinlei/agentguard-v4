"""AgentGuard v1 - Local Policy Scanner

A synthetic training demo. Streamlit app that shows a small inventory of
fake AI agents, then scans each one against five deterministic rules
(AG-001 through AG-005) to show what a "before" and "after" guardrail
fix looks like.
"""

from pathlib import Path

import streamlit as st

from scanner import load_agents, evaluate_agent

BASE_DIR = Path(__file__).resolve().parent
BEFORE_PATH = BASE_DIR / "sample_environment_before.json"
AFTER_PATH = BASE_DIR / "sample_environment_after.json"

NOT_FULLY_SECURE_NOTE = (
    "Note: \"NO RISK FOUND\" only means none of AgentGuard's five rules were "
    "triggered. It does not mean the agent is fully secure — it just passed "
    "the checks this tool knows how to run."
)


def inventory_rows(agents):
    return [
        {
            "Agent name": a.agent_name,
            "Owner": a.owner if a.owner else "(blank)",
            "Identity": a.identity,
            "Tools": ", ".join(a.tools),
            "Sensitive data access": a.sensitive_data_access,
            "Human approval required": a.human_approval_required,
        }
        for a in agents
    ]


def results_rows(results):
    return [
        {
            "Agent name": r.agent.agent_name,
            "Risk level": r.risk_level,
            "Score": r.score,
            "Findings": len(r.findings),
        }
        for r in results
    ]


def risk_counts(results):
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "NO RISK FOUND": 0}
    for r in results:
        counts[r.risk_level] += 1
    return counts


def render_findings(result):
    with st.expander(f"{result.agent.agent_name} — {result.risk_level} ({result.score} pts)"):
        if not result.findings:
            st.write("No policy findings for this agent.")
            return
        for f in result.findings:
            st.markdown(f"**{f.rule_id} — {f.title}** · {f.severity} · {f.points} pts")
            st.write(f.explanation)
            st.write(f"**Recommendation:** {f.recommendation}")
            st.divider()


def render_environment_tab(heading, path, state_key):
    agents = load_agents(path)

    st.subheader(f"{heading} — agent inventory")
    st.table(inventory_rows(agents))

    if st.button("Scan this environment", key=f"scan_button_{state_key}"):
        st.session_state[state_key] = [evaluate_agent(a) for a in agents]

    results = st.session_state.get(state_key)
    if not results:
        return None

    st.subheader(f"{heading} — scan results")
    counts = risk_counts(results)
    cols = st.columns(5)
    cols[0].metric("Agents scanned", len(results))
    cols[1].metric("HIGH", counts["HIGH"])
    cols[2].metric("MEDIUM", counts["MEDIUM"])
    cols[3].metric("LOW", counts["LOW"])
    cols[4].metric("NO RISK FOUND", counts["NO RISK FOUND"])

    st.table(results_rows(results))

    st.write("**Details for each agent:**")
    for r in results:
        render_findings(r)

    st.caption(NOT_FULLY_SECURE_NOTE)
    return results


def render_comparison_tab():
    st.subheader("Before vs. after guardrails")

    before_results = {
        r.agent.agent_name: r for r in (evaluate_agent(a) for a in load_agents(BEFORE_PATH))
    }
    after_results = {
        r.agent.agent_name: r for r in (evaluate_agent(a) for a in load_agents(AFTER_PATH))
    }

    rows = []
    for name, before in before_results.items():
        after = after_results.get(name)
        rows.append(
            {
                "Agent name": name,
                "Before risk": before.risk_level,
                "Before score": before.score,
                "After risk": after.risk_level if after else "N/A",
                "After score": after.score if after else "N/A",
            }
        )
    st.table(rows)
    st.caption(NOT_FULLY_SECURE_NOTE)


def main():
    st.set_page_config(page_title="AgentGuard v1 - Local Policy Scanner")
    st.title("AgentGuard v1 - Local Policy Scanner")
    st.warning(
        "This is a synthetic training demo. All agents, owners, and tools "
        "shown here are made up for learning purposes — nothing here is a "
        "real system.",
        icon="⚠️",
    )

    tab_problem, tab_before, tab_after, tab_compare = st.tabs(
        ["Problem", "Before guardrails", "After guardrails", "Before vs. after"]
    )

    with tab_problem:
        st.subheader("What problem is this solving?")
        st.write(
            "AgentGuard v1 is a beginner-friendly, local-only tool that "
            "inventories sample AI agents and applies deterministic security "
            "rules to their identity, tools, data access, ownership, and "
            "human-approval settings. This is a local demo only."
        )
        st.write(
            "It applies five fixed rules (AG-001 through AG-005) that look "
            "for things like admin-level tool access, destructive actions "
            "without human approval, sensitive data access without human "
            "approval, outbound communication without approval, and agents "
            "with no assigned owner."
        )
        st.write(
            "The rules are deterministic: the same input always produces "
            "the same result. There is no AI model or external service "
            "involved in the scoring."
        )
        st.caption(NOT_FULLY_SECURE_NOTE)

    with tab_before:
        render_environment_tab("Before guardrails", BEFORE_PATH, "before_results")

    with tab_after:
        render_environment_tab("After guardrails", AFTER_PATH, "after_results")

    with tab_compare:
        render_comparison_tab()


if __name__ == "__main__":
    main()
