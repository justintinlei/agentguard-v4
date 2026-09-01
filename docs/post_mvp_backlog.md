# AgentGuard v4 — Post-MVP Backlog and Job-Search Integration

Two parts: what a real next version would build (and why each item is
deliberately outside the MVP), and how the finished prototype turns into
résumé, LinkedIn, portfolio, and interview material.

The MVP scope boundary is a decision, not an omission. Everything below the line
is named, not hidden — being able to say "here is what I would do next, and the
trade-off I made to leave it out" is the point.

---

# Part 1 — Post-MVP backlog

Each item: **what**, **why it is out of MVP scope**, **rough approach**. Several
turn forward an *accepted residual risk* from `docs/v4_threat_model.md`.

## Identity & authorization

- **Approval RBAC and separation of duties.** *What:* approvals tied to a
  person's role, with rules like "the proposer cannot be the approver" and
  "HIGH-risk changes need two approvers". *Why deferred:* the MVP records a
  single free-text reviewer name — enough to demonstrate exact-hash binding, not
  enough for real governance. *Approach:* an identity provider (OIDC), a role
  claim on each `ApprovalRecord`, and a policy check in the
  `APPROVED → VERIFIED` gate.
- **Workload identity for agents.** *What:* discover an agent's *cryptographic*
  identity (a SPIFFE ID, a cloud workload identity), not a free-text `owner`
  string. *Why deferred:* the synthetic registry has no real identity system
  behind it. *Approach:* an identity connector per platform, feeding a verified
  identity into the scanner alongside the existing fields.
- **Authenticated remote MCP.** *What:* the discovery server reachable over an
  authenticated network transport, not only a local STDIO subprocess. *Why
  deferred:* v3 deliberately kept the server local so "read-only" was provable
  from source; a remote server adds auth, transport security, and the
  currently-accepted uncapped-parse risk. *Approach:* the MCP HTTP/SSE
  transport, mutual TLS or a signed token, and a size cap on
  `mcp_client._structured()`.

## Discovery

- **Continuous discovery.** *What:* scheduled or event-driven inventory refresh
  instead of an on-demand scan. *Why deferred:* the MVP proves the trust
  boundary once; a scheduler is orthogonal plumbing. *Approach:* a cron/worker
  that runs the discovery path and writes a dated provenance record.
- **Real registry connectors.** *What:* pull agent inventory from actual
  systems (an MDM, a cloud IAM, an agent framework's registry). *Why deferred:*
  synthetic data keeps every demo safe and reproducible. *Approach:* one adapter
  per source that emits the same validated `Agent` shape the scanner already
  consumes — nothing downstream changes.
- **Bounded streaming for large inventories.** *What:* handle inventories too
  large to read into memory at once. *Why deferred:* the three demo files are
  tiny and a fixed allowlist. *Approach:* stream + cap the parse; carries the v3
  "unbounded response-block parse" residual risk.

## Policy & explanation

- **A versioned policy engine.** *What:* policy as testable, versioned rules
  with their own change history, not only retrieved prose. *Why deferred:* the
  MVP shows retrieval + grounding is enough to make an AI explanation auditable;
  a rules engine is a separate product surface. *Approach:* keep
  `policy_library.py` as the evidence store, add a rule evaluator whose output
  the grounding validator can also check.
- **Broader explanation evaluation.** *What:* the v2 eval matrix over many more
  synthetic cases and adversarial policy text. *Why deferred:* three golden
  cases prove the mechanism; breadth is incremental. *Approach:* expand
  `evals/v2_cases.json` and add mutation cases.

## Approval & audit

- **Wire the durable audit trail into the UI (`v4_service`).** *What:* the
  Streamlit page's event timeline comes from the SQLite `workflow_events` table,
  not an in-memory list. *Why deferred:* the durable path
  (`audit_db.py`, `workflow.record_terminal_state`) is fully built and tested;
  only the orchestrator that wires it into `app_v4.py` is missing, and a test
  currently forbids the import to keep the boundary clean. *Approach:* build the
  `v4_service.create_and_verify(...)` orchestrator the starter sketches, have
  the app call it, and relax that one test.
- **Tamper-evident audit events.** *What:* signed or hash-chained rows so a
  later edit is detectable, not only append-only by convention. *Why deferred:*
  convention + no UPDATE/DELETE code path is honest for a local demo. *Approach:*
  a per-row HMAC or a Merkle chain over `id`-ordered rows, verified on read.

## Delivery & rollback

- **A reviewed post-merge revert flow.** *What:* when a merged change must be
  undone, generate a `git revert` pull request for human review. *Why deferred:*
  the MVP correctly *refuses* automatic post-merge rollback
  (`rollback_plan(merged=True)`); building the reviewed path is the natural
  follow-on. *Approach:* a new plan type that produces a revert branch + a draft
  PR, never an automatic merge.
- **More remediation templates.** *What:* additional bounded fixes behind the
  same allowlist discipline (e.g. "scope a tool to read-only", "add a rate
  limit"). *Why deferred:* three templates cover the current AG rules and prove
  the pattern. *Approach:* one deterministic function per template, added to
  `ALLOWED_TEMPLATES`, each with immutability tests.

## Operability

- **Multi-tenancy, deployment hardening, production observability, scale
  tests, compliance mapping.** *What:* everything needed to run this for more
  than one team, safely, at load, with an audit an external assessor accepts.
  *Why deferred:* out of scope for a reference MVP by definition. *Approach:*
  standard platform work — tenant isolation, secrets management, metrics/traces,
  load testing, and a control-to-framework mapping (e.g. to an AI risk
  framework).

## Validation

- **Design-partner pilots.** *What:* run AgentGuard against a real customer's
  consented inventory and remediation targets. *Why deferred:* needs partners,
  legal review, and real (not synthetic) data. *Approach:* a scoped pilot with a
  dedicated non-production environment and a written data agreement.

## What stays fixed no matter what

None of the above changes the invariant: **deterministic rules decide *what* to
propose, software verifies correctness, a human approves *intent*, and the AI
layer may explain a finding and propose a remediation — never approve, apply,
verify, or score.** `scanner.py` stays the sole authority for the risk number. The
posture stays **allowlist, not denylist** — templates, repositories, branches,
file paths, and workflow transitions are all closed sets. A backlog item that
would weaken any of these is rejected, not scheduled.

---

# Part 2 — Job-search integration

How the finished prototype supports résumé, LinkedIn, portfolio, and targeted
interviews. Fill in your own name, links, and contact details — the templates
below use placeholders on purpose.

## Résumé bullets (pick 3–5; keep them honest and quantified)

- Built **AgentGuard**, a governed AI-agent remediation MVP: deterministic risk
  scoring (5 rules), a policy-grounded LLM explanation layer with citation
  validation, read-only MCP 2.x discovery (exactly 5 tools), SHA-256-bound human
  approval, isolated verification, draft-only GitHub delivery, and an
  append-only SQLite audit trail — **872 automated tests** behind a
  **one-command release gate**.
- Designed an **explicit remediation state machine** with fail-closed terminal
  states and a **failure-injection evaluation** (`run_v4_evals.py`) that injects
  10 abuse cases — state-skipping, stale approval, post-merge rollback,
  repository injection — and passes only when each is refused.
- Enforced an **allowlist-not-denylist** action boundary: 3 deterministic
  remediation templates (no free-form AI patches), a repo/branch/path allowlist
  with shell-injection-safe token-list commands, and **no merge command anywhere
  in the codebase**.
- Made every control **demonstrable**: a three-layer evidence package
  (protocol / product / verification), a rehearsed five-minute demo, and a
  threat model that maps each of 9 abuse categories to the control and the test
  that blocks it.
- Packaged the app as a **non-root Docker container** with a CI pipeline running
  the full unit + evaluation + secret-scan suite on every push.

## LinkedIn "About" / project blurb (2–3 sentences)

> AgentGuard is a reference MVP for governing AI agents in an enterprise: it
> discovers agent inventory over a read-only protocol boundary, scores risk with
> deterministic rules, and lets a human approve a narrow, verified fix that ships
> only as a draft pull request — with a full audit trail and rollback. The
> design principle throughout is that a probabilistic model can explain and
> propose, but never decides risk or changes production. It's a synthetic,
> local demo built to make each security control visible and defensible.

## Portfolio entry

**One-liner:** *A governed AI-agent remediation MVP — deterministic risk,
grounded explanation, human-approved and verified change, draft-only delivery,
full audit and rollback.*

**Link these, and say what each shows:**

| Link | What it shows |
|---|---|
| The repository | The whole system, `RELEASE GATE PASS for AgentGuard v4` reproducible in one command |
| `README.md` | The invariant, the end-to-end flow, the six trust boundaries, the test report |
| `docs/v4_threat_model.md` | 9 abuse categories, each with its control and the test that proves it |
| `docs/final_mvp_interview_brief.md` | 11 grounded Q&A — how each control actually works |
| `evidence/README.md` | The three-layer capture checklist and the five-minute demo script |
| The five-minute demo recording | The trust chain, live, with no credential on screen |

## Targeted-interview map

| Role / topic | Open this artifact | Raise this backlog item |
|---|---|---|
| AI-safety / guardrails engineering | the template allowlist + `evals/run_v4_evals.py` | approval RBAC + separation of duties |
| Platform / infrastructure | the MCP boundary + `Dockerfile` / `compose.yaml` | authenticated remote MCP |
| Security engineering | `docs/v4_threat_model.md` + `scripts/check_no_secrets.py` | tamper-evident (signed) audit events |
| AI product | the visible chain of trust in `README.md` + the demo | design-partner pilots on real inventory |
| Backend / data | `audit_db.py` (append-only, `id`-ordered) + `proposal_hash.py` | wire the durable audit trail into the UI (`v4_service`) |

## What NOT to claim

- This is a **synthetic, local demo**, not a production deployment.
- It is **not** complete enterprise agent discovery or full coverage.
- There is **no autonomous remediation** — every applied change is gated by a
  human approval bound to the exact reviewed content.
- The AI layer **never** approves, applies, verifies, or scores.
- No production auth/authz, multi-tenancy, high availability, or compliance
  certification — those are the backlog above, stated openly.
