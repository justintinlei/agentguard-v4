"""The one file in this project that talks to the real Claude API.

Every other module (grounding.py, mock_analyst.py, retrieval.py, ...)
stays completely unaware of the anthropic package or ANTHROPIC_API_KEY.
The key is read from the environment only, at call time, inside
analyze_with_claude - never hardcoded, never a default, never logged.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass

from analysis_schema import GroundedAnalysis
from prompt_builder import SYSTEM_INSTRUCTION, build_user_prompt
from retrieval import RetrievalHit
from scanner import ScanResult

# Request-level controls: bound one call's worst-case latency and cost,
# regardless of what the model or the network happens to do.
REQUEST_TIMEOUT_SECONDS = 30.0  # give up waiting for a response after this long
MAX_RETRIES = 1  # how many times the SDK retries a failed request before giving up


@dataclass(frozen=True)
class UsageRecord:
    """Observability record for one live call - what happened, not what
    was said: mode, model, token counts, latency, and an estimated cost.
    """

    mode: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    estimated_cost_usd: float

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Rough USD estimate from the per-million-token rates in .env.

    Not billing-accurate - just a sanity-check number, using rates the
    project itself configured rather than hardcoded pricing.
    """
    input_rate = float(os.getenv("AGENTGUARD_ESTIMATED_INPUT_COST_PER_MTOK", "3.00"))
    output_rate = float(os.getenv("AGENTGUARD_ESTIMATED_OUTPUT_COST_PER_MTOK", "15.00"))
    return round(
        (input_tokens / 1_000_000) * input_rate
        + (output_tokens / 1_000_000) * output_rate,
        6,
    )


# JSON Schema constraint keywords Claude's structured output rejects -
# discovered by trial: "minimum"/"maximum" on integer fields, and
# "minItems"/"maxItems" on array fields both caused real 400 errors.
# "minLength"/"maxLength" (on the nested Citation model's string fields,
# under $defs) are stripped preemptively for the same reason, before
# spending another live call finding out the same way.
_UNSUPPORTED_SCHEMA_KEYWORDS = (
    "minimum",
    "maximum",
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
)


def _api_compatible_schema(model_json_schema: dict):
    """Recursively strip unsupported keywords from every level of a
    Pydantic-generated schema, including nested model definitions
    ($defs), so the whole tree - not just the top level - is API-safe.

    This only relaxes the *hint* sent to the API - our own Pydantic
    validation (GroundedAnalysis.model_validate, below) still enforces
    every real constraint when the response comes back, regardless of
    what the API's schema mechanism does or doesn't support.
    """
    if isinstance(model_json_schema, dict):
        return {
            key: _api_compatible_schema(value)
            for key, value in model_json_schema.items()
            if key not in _UNSUPPORTED_SCHEMA_KEYWORDS
        }
    if isinstance(model_json_schema, list):
        return [_api_compatible_schema(item) for item in model_json_schema]
    return model_json_schema


def _extract_text(message) -> str:
    """Pull the text out of a Claude response, ignoring any non-text blocks."""
    parts = [block.text for block in message.content if getattr(block, "type", "") == "text"]
    if not parts:
        raise ValueError("Claude returned no text block.")
    return "\n".join(parts)


def analyze_with_claude(
    scan_result: ScanResult, evidence: list[RetrievalHit]
) -> tuple[GroundedAnalysis, UsageRecord]:
    """Send one request to the real Claude API and return a validated
    GroundedAnalysis plus a UsageRecord describing the call itself.

    Fails immediately, before importing the SDK or making any network
    call, if ANTHROPIC_API_KEY isn't set - a missing key is a clear,
    predictable error, not something left to fail unpredictably later.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing. Use mock mode or set the key in .env."
        )

    from anthropic import Anthropic, APITimeoutError  # imported here, not at module load time

    model = os.getenv("AGENTGUARD_MODEL", "claude-sonnet-5")
    max_tokens = int(os.getenv("AGENTGUARD_MAX_OUTPUT_TOKENS", "1200"))
    client = Anthropic(
        api_key=api_key,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    )

    # Constrain the response to GroundedAnalysis's real shape - this
    # guarantees the JSON is well-formed and matches our fields, not
    # that its content is true (grounding.py still checks that).
    schema = _api_compatible_schema(GroundedAnalysis.model_json_schema())

    start = time.perf_counter()
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": build_user_prompt(scan_result, evidence)}],
            # "low" effort fits this project's bounded, well-specified
            # summarization task - see Day 6, Lab 1's model/pricing review.
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": schema},
            },
        )
    except APITimeoutError as exc:
        raise RuntimeError(
            f"Claude API request timed out after {REQUEST_TIMEOUT_SECONDS}s. "
            "Try again or use mock mode."
        ) from exc
    latency_ms = int((time.perf_counter() - start) * 1000)

    # A documented, real API outcome distinct from a network or parsing
    # failure: the model itself declined to answer. Fail closed here
    # rather than letting a refusal fall through and fail confusingly at
    # the JSON-parsing step below.
    if getattr(message, "stop_reason", None) == "refusal":
        raise RuntimeError("Claude declined to generate a response for this request.")

    raw_text = _extract_text(message)
    try:
        analysis = GroundedAnalysis.model_validate(json.loads(raw_text))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Claude's response was not valid JSON: {exc}") from exc

    input_tokens = int(getattr(message.usage, "input_tokens", 0))
    output_tokens = int(getattr(message.usage, "output_tokens", 0))
    usage = UsageRecord(
        mode="live",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        estimated_cost_usd=estimate_cost(input_tokens, output_tokens),
    )
    return analysis, usage
