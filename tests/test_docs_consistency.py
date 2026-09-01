"""Doc-consistency guards (Day 10, Lab 5 — finalized for v4).

Source-string checks (same approach as tests/test_ci_workflow.py). Two jobs:

  1. Keep the v4 entry-point docs (README, START_HERE, v4 architecture, v4
     threat model) describing v4 "as built" — no "planned / not yet" language
     creeping back, no dangling links, no state-machine drift.
  2. Keep the frozen v3 docs (v3 architecture / threat model / handoff)
     exactly as finalized — v3 is done and must not regress.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

README = (ROOT / "README.md").read_text(encoding="utf-8")
START_HERE = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")

V4_ARCH = (ROOT / "docs" / "v4_architecture.md").read_text(encoding="utf-8")
V4_STATE = (ROOT / "docs" / "v4_state_machine.md").read_text(encoding="utf-8")
V4_THREAT = (ROOT / "docs" / "v4_threat_model.md").read_text(encoding="utf-8")

V3_ARCH = (ROOT / "docs" / "v3_architecture.md").read_text(encoding="utf-8")
V3_THREAT = (ROOT / "docs" / "v3_threat_model.md").read_text(encoding="utf-8")
HANDOFF = (ROOT / "docs" / "v3_to_v4_handoff.md").read_text(encoding="utf-8")

EVIDENCE = (ROOT / "evidence" / "README.md").read_text(encoding="utf-8")
INTERVIEW = (ROOT / "docs" / "final_mvp_interview_brief.md").read_text(encoding="utf-8")
BACKLOG = (ROOT / "docs" / "post_mvp_backlog.md").read_text(encoding="utf-8")

FIVE_TOOLS = (
    "health_check",
    "list_agent_inventory",
    "get_agent_by_name",
    "list_tool_catalog",
    "list_agent_ownership",
)
STALE_PHRASES = ("not yet reached", "not yet built", "(Planned)", "planned behaviour")

# The v4 invariant, in the words every doc must keep.
INVARIANT_MARKERS = ("sole authority", "predicts", "never", "scanner.py")


# --- the v4 entry-point docs are finalized ------------------------------------

def test_the_entry_point_docs_exist_and_are_non_trivial():
    for text in (README, START_HERE, V4_ARCH, V4_THREAT):
        assert len(text.strip()) > 400


def test_version_file_names_v4():
    assert VERSION.strip() == "AgentGuard v4 - Governed Remediation MVP"


def test_readme_describes_v4_as_built():
    assert README.lstrip().startswith("# AgentGuard v4")
    for phrase in STALE_PHRASES:
        assert phrase not in README
    for marker in ("app_v4.py", "scripts/run_release_gate.py",
                   "RELEASE GATE PASS for AgentGuard v4", "draft", "dry-run"):
        assert marker in README
    # the invariant is stated
    assert "sole authority" in README
    # the inherited v3 boundary is still named exactly
    for tool in FIVE_TOOLS:
        assert tool in README


def test_readme_has_the_release_gate_test_report():
    lower = README.lower()
    assert "test report" in lower
    # the real, reproducible numbers
    assert "866 passed" in README
    assert "V2 EVALUATION PASS: 3 of 3" in README
    assert "V3 SECURITY EVAL SUITE PASS" in README
    assert "10 of 10 checks held" in README


def test_start_here_points_at_the_v4_gate_and_the_invariant():
    assert "RELEASE GATE PASS for AgentGuard v4" in START_HERE
    for tool in FIVE_TOOLS:
        assert tool in START_HERE
    assert "three" in START_HERE.lower() and "template" in START_HERE.lower()
    assert "no merge command" in START_HERE.lower()


def test_every_repo_relative_link_in_the_entry_docs_resolves():
    for text in (README, START_HERE):
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith("http") or target.startswith("#"):
                continue
            assert (ROOT / target).exists(), target


# --- the v4 architecture doc is reconciled with workflow.py ------------------

def test_v4_architecture_is_marked_as_built_not_design():
    assert "Status: as built" in V4_ARCH
    assert "Status: design" not in V4_ARCH
    assert "planned behaviour" not in V4_ARCH
    assert "## How this is verified" in V4_ARCH
    # the invariant paragraph survives every edit
    assert "sole authority for the risk number" in V4_ARCH
    assert "it never *sets* one" in V4_ARCH


def test_v4_architecture_state_machine_matches_the_implemented_transitions():
    # These two arrows were in the Day-1 sketch but never implemented
    # (workflow.ALLOWED_TRANSITIONS has APPROVED -> {VERIFIED, FAILED} and
    # DRAFT_PR_CREATED -> {ROLLED_BACK}). The reconciled doc must not draw them.
    assert "APPROVED ───────────────► REJECTED" not in V4_ARCH
    assert "DRAFT_PR_CREATED ───────► FAILED" not in V4_ARCH
    assert "returns to `PROPOSED` / `REJECTED`" not in V4_ARCH
    # and it must state the real rule
    assert "Only `PROPOSED` can be rejected" in V4_ARCH
    assert "pure guard" in V4_ARCH


def test_v4_state_machine_doc_still_agrees_with_itself():
    # unchanged this lab, but it is the canonical map the arch doc defers to
    assert "`DRAFT_PR_CREATED` | `ROLLED_BACK`" in V4_STATE
    assert "APPROVED` | `VERIFIED`, `FAILED`" in V4_STATE


# --- the v4 threat model is complete ----------------------------------------

def test_v4_threat_model_has_numbered_categories_and_residual_risks():
    categories = re.findall(r"^## \d+\. ", V4_THREAT, re.MULTILINE)
    assert len(categories) == 9
    assert "## Accepted residual risks" in V4_THREAT
    # every category ties to the end-to-end failure-injection eval
    assert "run_v4_evals.py" in V4_THREAT
    assert "fails closed" in V4_THREAT.lower()
    for phrase in STALE_PHRASES:
        assert phrase not in V4_THREAT


def test_v4_threat_model_names_the_real_controls():
    for control in ("require_allowlisted", "validate_approval", "require_verified",
                    "SAFE_BRANCH", "transition()", "rollback_plan",
                    "record_terminal_state", "check_no_secrets.py"):
        assert control in V4_THREAT


# --- the frozen v3 docs stay finalized -------------------------------------

def test_v3_architecture_doc_stays_finalized():
    assert "(Planned)" not in V3_ARCH
    assert "only designed" not in V3_ARCH
    assert "## Reproduce this integration" in V3_ARCH
    assert "only v1's deterministic" in V3_ARCH
    assert "sets the risk score" in V3_ARCH


def test_v3_threat_model_stays_finalized():
    category_headings = re.findall(r"^## \d+\. ", V3_THREAT, re.MULTILINE)
    assert len(category_headings) == 7
    assert "## Accepted residual risks (carried to v4)" in V3_THREAT
    assert "read_json_with_provenance" in V3_THREAT
    assert "_structured" in V3_THREAT


def test_v3_to_v4_handoff_still_explains_the_governed_action_decision():
    lower = HANDOFF.lower()
    assert "does not" in lower and "write tool" in lower
    for verb in ("propose", "approv", "apply", "rollback"):
        assert verb in lower
    assert "sole" in lower and "authority" in lower
    assert "predict" in lower
    assert "five read-only" in lower
    assert "RELEASE GATE PASS for AgentGuard v3" in HANDOFF
    for phrase in STALE_PHRASES:
        assert phrase not in HANDOFF


def test_readme_links_the_frozen_v3_reference_docs():
    for link in ("docs/v3_architecture.md", "docs/v3_threat_model.md",
                 "docs/v3_to_v4_handoff.md"):
        assert link in README


# --- Day 10 Lab 6: the v4 final evidence package + five-minute demo ---------

def test_evidence_readme_has_the_v4_final_capture_and_demo():
    assert "# AgentGuard v4 — Day 10: Final evidence capture" in EVIDENCE
    assert "# AgentGuard v4 — Day 10: The five-minute demo" in EVIDENCE
    lower = EVIDENCE.lower()
    # the three layers "it works" splits into
    for layer in ("protocol", "product", "verification"):
        assert layer in lower
    # the v4 product + the one-command proof
    assert "app_v4.py" in EVIDENCE
    assert "RELEASE GATE PASS for AgentGuard v4" in EVIDENCE
    assert "10 of 10 checks held" in EVIDENCE
    # the credential-safety content — the learning goal of this lab
    assert "credential-safety checklist" in lower
    assert ".env" in EVIDENCE
    assert "gh auth status" in EVIDENCE
    assert "screenshot" in lower and "video frame" in lower
    assert "token" in lower
    for phrase in STALE_PHRASES:
        assert phrase not in EVIDENCE


def test_every_directory_prefixed_command_target_in_the_evidence_readme_exists():
    # Directory-prefixed scripts/docs/tests only (a bare "app_v4.py" is covered
    # by other tests; transient demo files like agents.json.bak are not real).
    for path in re.findall(r"(?:scripts|evals|docs|tests)/[\w./-]+\.(?:py|md)", EVIDENCE):
        assert (ROOT / path).exists(), path


# --- Day 10 Lab 7: the final interview brief ------------------------------

def test_final_interview_brief_covers_the_learning_goal_topics():
    assert len(INTERVIEW.strip()) > 2000
    assert INTERVIEW.count("**Q:") >= 9          # Q&A format
    lower = INTERVIEW.lower()
    # every topic the lab's learning goal names
    for topic in ("identity", "policy", "mcp", "rag", "guardrail",
                  "approval", "verification", "audit", "rollback"):
        assert topic in lower, topic
    # the answers cite the real code, not a generic description
    for symbol in ("scanner.py", "remediation_templates", "validate_approval",
                   "require_verified", "record_terminal_state", "rollback_plan"):
        assert symbol in INTERVIEW, symbol
    # the invariant is restated
    assert "sole authority" in INTERVIEW
    for phrase in STALE_PHRASES:
        assert phrase not in INTERVIEW


def test_readme_links_the_final_interview_brief():
    assert "docs/final_mvp_interview_brief.md" in README


# --- Day 10 Lab 8: the post-MVP backlog + job-search integration ----------

def test_post_mvp_backlog_has_next_work_and_job_search_content():
    assert len(BACKLOG.strip()) > 1500
    lower = BACKLOG.lower()
    assert "backlog" in lower
    # concrete deferred items, each turning forward a real MVP limit
    for item in ("rbac", "remote", "v4_service", "tamper"):
        assert item in lower, item
    # the job-search half — the learning goal
    for asset in ("linkedin", "portfolio", "interview", "job-search"):
        assert asset in lower, asset
    # the backlog is not read as "these safety limits are temporary"
    assert "sole authority" in BACKLOG
    assert "allowlist, not denylist" in lower
    for phrase in STALE_PHRASES:
        assert phrase not in BACKLOG


def test_readme_links_the_post_mvp_backlog():
    assert "docs/post_mvp_backlog.md" in README
