"""Human approval for a remediation proposal - the audit-evidence record.

An `ApprovalRecord` is a *recorded human decision* that stands on its own
as evidence. It answers every question an auditor asks, in one immutable
object:

  who        -> reviewer
  what       -> decision (APPROVE / REJECT) + proposal_sha256 + source_sha256
  why        -> reason
  when       -> decided_at   (UTC, ISO-8601)
  which run  -> workflow_id

It is bound to two hashes: the exact proposal that was reviewed, and the
exact source environment it was built against. `validate_approval()`
refuses to let a proposal proceed unless an `APPROVE` decision exists
whose bound hashes still match - so an approval can never be reused for a
proposal that changed, or against an environment that moved.

Day 4 Lab 5 (this slice) added the audit fields `workflow_id` and
`decided_at`. Lab 6 adds the approve/reject choice in the product; Labs
7-8 the stale-approval rejection tests.

Day 8 Lab 6 adds `approval_is_current()` - the non-raising companion to
`validate_approval()`: it *reports* whether a re-review is needed
(returns a bool) where `validate_approval()` *enforces* it (raises).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

VALID_DECISIONS = {"APPROVE", "REJECT"}


@dataclass(frozen=True)
class ApprovalRecord:
    """One human decision about one proposal - the unit of audit evidence.

    Frozen: once made, a decision cannot be edited. Every field is part of
    the trail:

      workflow_id      which end-to-end remediation run this belongs to
      proposal_sha256  the exact proposal that was approved (Day 4 Lab 4)
      source_sha256    the exact environment it was built against (Lab 3)
      reviewer         the human who decided
      decision         APPROVE or REJECT
      reason           the human's stated justification
      decided_at       when decide() ran, in UTC (ISO-8601 text)
    """

    workflow_id: str
    proposal_sha256: str
    source_sha256: str
    reviewer: str
    decision: str
    reason: str
    decided_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def decide(
    workflow_id: str,
    proposal_sha256: str,
    source_sha256: str,
    reviewer: str,
    decision: str,
    reason: str,
) -> ApprovalRecord:
    """Record a human's APPROVE / REJECT decision on a proposal.

    Raises ValueError if the decision is not APPROVE/REJECT, or if the
    reviewer or the reason is blank - a decision must always say who made
    it and why. `workflow_id` is a system-generated identifier, not user
    free text, so it is stored as given. `decided_at` is stamped here in
    UTC so the record carries its own timestamp.
    """
    reviewer = reviewer.strip()
    reason = reason.strip()
    if decision not in VALID_DECISIONS:
        raise ValueError("decision must be APPROVE or REJECT")
    if not reviewer or not reason:
        raise ValueError("reviewer and reason are required")
    return ApprovalRecord(
        workflow_id=workflow_id,
        proposal_sha256=proposal_sha256,
        source_sha256=source_sha256,
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        decided_at=datetime.now(timezone.utc).isoformat(),
    )


def validate_approval(
    record: ApprovalRecord,
    proposal_sha256: str,
    source_sha256: str,
) -> None:
    """Raise unless `record` approves *exactly* this proposal and source.

    Three ways to fail:
      - the decision was not APPROVE;
      - the proposal changed since it was approved;
      - the source environment changed since it was approved.

    `workflow_id` and `decided_at` are audit metadata - recorded for the
    trail, but intentionally not part of this match.
    """
    if record.decision != "APPROVE":
        raise ValueError("The proposal was not approved.")
    if record.proposal_sha256 != proposal_sha256:
        raise ValueError("Approval is stale because the proposal changed.")
    if record.source_sha256 != source_sha256:
        raise ValueError("Approval is stale because the source changed.")


def approval_is_current(
    record: ApprovalRecord,
    proposal_sha256: str,
    source_sha256: str,
) -> bool:
    """Non-raising form of `validate_approval()`.

    Return `True` iff `record` is an APPROVE decision still bound to
    exactly this proposal and this source; `False` if the decision was
    not APPROVE, or the proposal or source hash has drifted since
    sign-off.

    Use this to *show* whether a re-review is needed (a status field, a
    UI banner); use `validate_approval()` to *enforce* it right before a
    change is applied. The two always agree, because "current" is defined
    here in terms of that one function.
    """
    try:
        validate_approval(record, proposal_sha256, source_sha256)
        return True
    except ValueError:
        return False
