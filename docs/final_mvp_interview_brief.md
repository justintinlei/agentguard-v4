# AgentGuard v4 — Final MVP Interview Brief

Eleven questions likely to come up when explaining this project, each with a
concise (2–5 sentence) answer written from what is actually built and verified in
this repo — not a generic description. Pairs with `docs/v2_interview_brief.md`
(deterministic authority, RAG, grounding in detail) and `docs/v3_interview_brief.md`
(MCP roles, provenance, the read-only guarantee). The five-minute demo script is
in `evidence/README.md`.

---

**Q: In one sentence, what is AgentGuard v4, and what did each version add?**

AgentGuard v4 is a governed-remediation MVP: it discovers synthetic AI-agent
inventory, scores it with deterministic rules, explains findings with a
policy-grounded AI layer, and delivers a bounded, human-approved, verified change
only as a draft pull request. v1 is the local-file scanner (five rules,
`AG-001`–`AG-005`); v2 added a grounded Claude explanation layer that never
changes the score; v3 replaced the local-file source with a read-only MCP
client/server boundary; v4 adds the action layer — proposal, hash, approval,
verification, dry-run/draft-PR delivery, audit, and rollback. `scanner.py` is
byte-for-byte unchanged from v1 through v4.

**Q: What does "identity" mean in this system, and why is it a security concern?**

Every agent record carries an `identity` string and an `owner`. "Who is
accountable for this agent" is a governance question: rule `AG-005` flags any
agent with an empty owner as LOW risk, and one of the three remediation templates
(`ASSIGN_OWNER`) exists specifically to fix that. Ownership is also discovered as
its own MCP tool (`list_agent_ownership`), separate from the inventory, so a
reviewer can cross-check that the agents running in an environment match the
ownership records an enterprise keeps. An unowned agent with a destructive tool
is exactly the combination the scanner escalates.

**Q: Where does "policy" live, and how is it used?**

`policies/` holds real, human-written policy text; `policy_library.py` loads it
into small chunks, each with a stable identifier and a content hash, so any
citation can be traced back to an exact passage. Policy is never summarised into
the model's weights — it is retrieved fresh per finding and handed to the model
as the evidence it must cite. That is what makes the AI explanation auditable:
the claim "this violates policy X" is checkable against the retrieved chunk, not
taken on the model's word.

**Q: Explain the MCP boundary — the roles, the transport, and why it is read-only.**

The **host** is AgentGuard (`app_v4.py`); the **client** (`mcp_client.py`) speaks
the protocol and manages the connection; the **server** (`mcp_server.py`) is a
separate process exposing exactly five **tools** — `health_check`,
`list_agent_inventory`, `get_agent_by_name`, `list_tool_catalog`,
`list_agent_ownership` — over a STDIO **transport** (the client launches the
server as a local subprocess; there is no network). It is read-only three
independent ways: every tool only reads and hashes; a static check asserts no
write operation exists in the discovery source; and `validate_starter_kit.py`
re-parses the server and client on every release-gate run to confirm the tool set
is exactly those five and that no tool name contains a write verb. v4 adds **no**
sixth, write-capable tool — remediation is a separate governed component so the
discovery server stays provably read-only forever.

**Q: How does RAG and grounding work here, and what does the grounding validator
actually reject?**

`retrieval.retrieve(query, chunks)` selects the most relevant policy chunks for a
finding; those chunks — and only those — are put in the prompt. After the model
responds, `grounding.validate_grounding()` checks the structured output before it
reaches the screen: the risk score in the explanation must equal the scanner's
score exactly, and every policy citation must quote text that is actually present
in a retrieved chunk. An explanation that inflates or lowers the score, or cites
a policy passage that was not retrieved, is rejected — the model can explain and
cite, it cannot decide.

**Q: What are the guardrails on the *action* layer, and why allowlists rather
than denylists?**

Three things are allowlisted: the **remediation** is one of exactly three
deterministic templates in `remediation_templates.py` (`REQUIRE_HUMAN_APPROVAL`,
`ASSIGN_OWNER`, `REMOVE_BROAD_ADMIN_TOOL`) — never a free-form AI-generated
patch; the **GitHub target** is one repository, one `agentguard/` branch prefix,
and one file path (`github_plan.py`), checked by both a shape regex and exact
membership; and the **workflow** may only move along arrows in
`workflow.ALLOWED_TRANSITIONS`. An allowlist fails safe: anything not explicitly
permitted is refused, so a new attack vector or an unforeseen input is blocked by
default rather than needing a rule written against it.

**Q: How is a human approval bound to *exactly* what was reviewed?**

`proposal_hash.canonical_json()` serialises a value with sorted keys and fixed
separators, and `sha256_value()` hashes that — so the same logical content always
produces the same 64-hex fingerprint. `approval.decide()` records an
`ApprovalRecord` bound to **two** hashes: the SHA-256 of the proposal and the
SHA-256 of the source environment it was built from. `approval.validate_approval()`
raises unless the decision is `APPROVE` **and** both hashes still match, in a
fixed order ("not approved" / "proposal changed" / "source changed"). So an
approval cannot be replayed against a modified proposal or a modified inventory —
if either drifts, the `APPROVED → VERIFIED` check fails and the workflow goes to
`FAILED`.

**Q: What is the difference between approval and verification here?**

Approval is a human recording *intent* — "yes, make this change" — and it touches
no real configuration. Verification is *software* confirming *correctness*:
`verifier.verify()` applies the approved proposal to an **isolated throwaway
copy** of the environment, re-scans it, and runs ten checks — the predicted score
is reached, exactly one agent changed, only allowlisted keys changed, the data
still serialises, and the HIGH-risk count did **not** increase.
`verifier.require_verified()` raises on any failed check, which blocks every
GitHub step. A person can be confident and wrong; the verifier is the
deterministic second opinion before anything is delivered.

**Q: What does the audit trail guarantee, and how?**

Every workflow step is one row in a SQLite `workflow_events` table
(`audit_db.py`), append-only by convention — the module has no `UPDATE` or
`DELETE` code path — and ordered by an autoincrement `id`, not by timestamp
(two events can share a millisecond). `workflow.transition()` is a pure guard
that writes nothing; the orchestrator records each step separately, and
`workflow.record_terminal_state()` is the one helper that records a *non-success*
ending — `workflow_rejected`, `workflow_failed`, or `workflow_rolled_back` — with
a required non-empty reason. So a rejected, failed, or rolled-back run leaves as
deliberate a record as a successful one; the log is never silent.

**Q: How does rollback work, and why does it refuse after a merge?**

Before a merge, `rollback.rollback_plan(repository, pr_number, branch,
merged=False)` returns two reversible commands: `gh pr close` (a closed PR can be
reopened) and `git push origin --delete <agentguard/ branch>` (a deleted branch
can be re-pushed from a local copy). It never force-pushes or rewrites history.
`merged=True` raises `ValueError("Automatic rollback is refused after merge. Use
a reviewed revert workflow.")` and returns no command — a merged change is in
shared history, and undoing it means a new, human-reviewed `git revert` pull
request, which AgentGuard deliberately does not automate. The `merged` flag is
required and keyword-only, so there is no fail-open default.

**Q: What is the one invariant, and what are the honest limitations?**

The invariant: deterministic rules decide *what* to propose, software verifies
correctness, a human approves *intent*, and the AI layer may explain a finding
and propose a remediation — never approve, apply, verify, or score. `scanner.py`
stays the sole authority for the risk number from v1 through v4; a proposal
*predicts* a score, it never sets one. The limitations, stated not hidden: this
is a local demo on synthetic data; the Streamlit page's event timeline is
in-memory rather than the durable SQLite audit log (the `v4_service` orchestrator
that wires them is deferred); approval is a single free-text reviewer name with
no identity check or RBAC; and there is no autonomous remediation, no
multi-tenancy, and no production auth/HA/compliance — those are post-MVP work.

---

## What this project proves about the builder

- **LLM / API integration** — structured output, RAG, grounding validation,
  citations, evaluation suites, token/cost observability, and a free deterministic
  mock fallback.
- **MCP 2.x design** — server/client roles, tool schemas, least privilege, an
  exact-match tool allowlist, provenance hashing, and adversarial testing of the
  protocol boundary.
- **Agentic workflow design** — bounded actions, an explicit state machine with
  fail-closed terminals, human-in-the-loop approval bound to content hashes,
  deterministic guardrails, isolated verification, rollback, and an append-only
  audit log.
- **Engineering practice** — Python, Streamlit, pytest (874 tests), a
  one-command release gate, failure-injection evaluation, GitHub CLI integration
  behind an allowlist, Docker packaging as non-root, CI, threat modeling, and
  product storytelling.

## Interview answer (one paragraph)

"I built AgentGuard to work out how an enterprise can let AI help govern its
agents without putting a probabilistic model in charge of security decisions or
production changes. Deterministic rules set the risk score; Claude only produces
policy-grounded explanations, and a validator rejects any explanation that
changes the score or cites something it wasn't given; discovery is a read-only
MCP boundary with exactly five tools; remediation is three allowlisted templates,
never a free-form patch; a human approval is cryptographically bound to the exact
proposal and source; software verifies the change on an isolated copy before it
is delivered as a draft-only pull request; and every step — including every
failure and rollback — is an append-only audit event. It taught me how to combine
agentic AI with identity, policy, retrieval, guardrails, approvals, verification,
audit, and safe rollback, and how to make each of those controls visible and
demonstrable rather than asserted."
