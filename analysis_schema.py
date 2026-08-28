"""The data contract for AgentGuard v2's AI explanation layer.

Every field, length limit, and count limit here is a check Pydantic runs
automatically the moment this data is constructed - "runtime validation"
- so this file is an enforceable contract, not just documentation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    """One citation: which policy chunk, and the exact quote from it.

    `quote` is length-capped so a citation can't just be an entire
    document dumped in - it has to be a specific, checkable passage.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    quote: str = Field(min_length=1, max_length=300)


class GroundedAnalysis(BaseModel):
    """The full structured explanation the model layer must produce.

    `deterministic_risk_level`/`deterministic_risk_score` exist so the
    grounding validator (a later lab) can confirm the model reported
    v1's real score back unchanged - this schema does not give the model
    any authority to set them, only to repeat them.
    """

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    deterministic_risk_level: str
    deterministic_risk_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=1200)
    why_it_matters: str = Field(min_length=1, max_length=1200)
    recommended_next_step: str = Field(min_length=1, max_length=1200)
    citations: list[Citation] = Field(min_length=1, max_length=5)
