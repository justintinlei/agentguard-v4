"""Tests that the finalized v3 entry-point docs stay finalized (Day 10, Lab 3).

Source-string checks (same approach as tests/test_ci_workflow.py). The
point is to stop the "planned / not yet built" language from silently
creeping back into README.md and docs/v3_architecture.md, and to catch a
dangling doc link before a reader does.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
ARCHITECTURE = (ROOT / "docs" / "v3_architecture.md").read_text(encoding="utf-8")
THREAT_MODEL = (ROOT / "docs" / "v3_threat_model.md").read_text(encoding="utf-8")
START_HERE = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
EVIDENCE = (ROOT / "evidence" / "README.md").read_text(encoding="utf-8")
INTERVIEW = (ROOT / "docs" / "v3_interview_brief.md").read_text(encoding="utf-8")
HANDOFF = (ROOT / "docs" / "v3_to_v4_handoff.md").read_text(encoding="utf-8")

FIVE_TOOLS = (
    "health_check",
    "list_agent_inventory",
    "get_agent_by_name",
    "list_tool_catalog",
    "list_agent_ownership",
)
STALE_PHRASES = ("not yet reached", "No MCP code exists", "not yet built", "(Planned)")


def test_the_four_entry_point_docs_exist_and_are_non_empty():
    for text in (README, ARCHITECTURE, THREAT_MODEL, START_HERE):
        assert len(text.strip()) > 200


def test_readme_describes_v3_as_built():
    for phrase in STALE_PHRASES:
        assert phrase not in README
    assert "app_v3.py" in README
    assert "scripts/run_release_gate.py" in README
    assert "RELEASE GATE PASS for AgentGuard v3" in README
    for tool in FIVE_TOOLS:
        assert tool in README


def test_architecture_doc_is_finalized_with_a_reproduce_section():
    assert "(Planned)" not in ARCHITECTURE
    assert "only designed" not in ARCHITECTURE
    assert "## Reproduce this integration" in ARCHITECTURE
    # The invariant must survive every edit.
    assert "only v1's deterministic" in ARCHITECTURE
    assert "sets the risk score" in ARCHITECTURE


def test_threat_model_lists_all_seven_categories_and_the_residual_risks():
    category_headings = re.findall(r"^## \d+\. ", THREAT_MODEL, re.MULTILINE)
    assert len(category_headings) == 7
    assert "## Accepted residual risks (carried to v4)" in THREAT_MODEL
    assert "read_json_with_provenance" in THREAT_MODEL
    assert "_structured" in THREAT_MODEL


def test_start_here_points_at_the_release_gate_and_the_invariant():
    assert "RELEASE GATE PASS for AgentGuard v3" in START_HERE
    assert "exactly five tools" in START_HERE


def test_every_repo_relative_link_in_the_readme_resolves():
    for target in re.findall(r"\]\(([^)]+)\)", README):
        if target.startswith("http") or target.startswith("#"):
            continue
        assert (ROOT / target).exists(), target


# --- Day 10, Lab 4: the final evidence-capture section ---------------------

def test_evidence_readme_is_finalized():
    assert not EVIDENCE.lstrip().startswith("# AgentGuard v1 — Required Evidence")
    assert "Day 10: Final evidence capture" in EVIDENCE
    for layer in ("protocol", "product", "verification"):
        assert layer in EVIDENCE.lower()
    assert "npx @modelcontextprotocol/inspector" in EVIDENCE
    assert "app_v3.py" in EVIDENCE
    assert "RELEASE GATE PASS for AgentGuard v3" in EVIDENCE


def test_every_command_target_in_the_evidence_readme_exists():
    # Directory-prefixed scripts and docs only (a bare "app.py" is covered by
    # other tests; transient files like agents.json.bak are deliberately absent).
    for path in re.findall(r"(?:scripts|evals|docs|tests)/[\w./-]+\.(?:py|md)", EVIDENCE):
        assert (ROOT / path).exists(), path


# --- Day 10, Lab 5: the five-minute demo script ---------------------------

def test_evidence_readme_has_the_demo_script():
    lower = EVIDENCE.lower()
    assert "the five-minute demo" in lower
    # the four beats the learning goal names
    for beat in ("discovery", "provenance", "scanner", "control"):
        assert beat in lower
    # scope honesty and a live fallback
    assert "what not to claim" in lower
    assert "run_mcp_live_smoke.py" in EVIDENCE


# --- Day 10, Lab 6: the MCP / agent-security interview brief --------------

def test_interview_brief_covers_the_three_areas():
    assert len(INTERVIEW.strip()) > 800
    assert INTERVIEW.count("**Q:") >= 6                       # Q&A format
    for phrase in STALE_PHRASES:
        assert phrase not in INTERVIEW
    lower = INTERVIEW.lower()
    # MCP architecture
    assert "mcpserver" in lower and "mcp[cli]>=2.0,<3" in INTERVIEW
    for tool in FIVE_TOOLS:
        assert tool in INTERVIEW or "exactly five" in lower
    # authorization boundaries — both mechanisms named
    assert "_verify_tool_allowlist" in INTERVIEW
    assert "discovery_adapter.py" in INTERVIEW
    # prompt injection
    assert "prompt injection" in lower


def test_readme_links_the_interview_brief():
    assert "docs/v3_interview_brief.md" in README


# --- Day 10, Lab 8: the v3 -> v4 governed-action handoff -----------------

def test_v3_to_v4_handoff_explains_the_governed_action_decision():
    assert len(HANDOFF.strip()) > 800
    lower = HANDOFF.lower()
    # the core decision: no write tool on the discovery server
    assert "does not" in lower and "write tool" in lower
    # the governed workflow verbs
    for verb in ("propose", "approv", "apply", "rollback"):
        assert verb in lower
    # what v4 must preserve: scanner stays sole authority; a proposal only predicts
    assert "sole" in lower and "authority" in lower
    assert "predict" in lower
    assert "five read-only" in lower
    assert "RELEASE GATE PASS for AgentGuard v3" in HANDOFF
    for phrase in STALE_PHRASES:
        assert phrase not in HANDOFF


def test_readme_links_the_v4_handoff():
    assert "docs/v3_to_v4_handoff.md" in README
