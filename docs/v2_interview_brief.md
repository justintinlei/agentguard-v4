# AgentGuard v2 Interview Brief

Seven questions likely to come up when explaining this project, each with
a concise (2-4 sentence) answer. Written from what's actually built and
verified in this repo, not a generic description.

---

**Q: Why does v1's deterministic score keep final authority over the AI
layer?**

An AI explanation can read confidently and still be wrong. v1's five
rule-based checks (`AG-001`–`AG-005`) always give the same score for the
same input — no randomness, no model judgment. v2 adds a Claude-generated
explanation on top, but `grounding.validate_grounding()` rejects any
output where the model's stated score or risk level doesn't exactly match
v1's real scan result, before anything reaches a user. The model can
explain a finding and cite policy text; it can never decide one.

**Q: What is RAG, and how does retrieval work in this project
specifically?**

RAG (Retrieval-Augmented Generation) means searching an approved document
set for the passages most relevant to the current situation, and giving a
model only those passages as evidence — instead of relying on whatever
the model "remembers" from training. Concretely: a scanner finding
becomes a search query, that query is scored against every chunk in the
5-file `policies/` corpus using cosine similarity over word-overlap
(`retrieval.py`, no vector database or embeddings), and the top-K
best-matching chunks are the only evidence the model ever sees.

**Q: What is structured output, and why does it matter here?**

Structured output means the model returns data matching a predefined
shape (specific fields and types) instead of a free-form paragraph — a
`GroundedAnalysis` Pydantic model with fields like
`deterministic_risk_score` and a list of `Citation` objects. This matters
because a plain-text response gives no reliable way to programmatically
check "did the model change the score" or "does every citation have a
real chunk ID" — the schema is what makes an automated grounding check
possible to write at all.

**Q: What is grounding, and — precisely — what does it check and not
check?**

Grounding means every claim in a model's output traces back to something
real and checkable. `validate_grounding()` checks exactly two things:
score/level match the real scan (score authority), and every citation's
quote is a real substring of a chunk that was actually supplied (citation
authenticity). It does **not** check whether that evidence's content is
itself safe — a Day 9 security review and a follow-up prompt-injection
exercise both confirmed this precisely: the real defense against
injected instructions is upstream, in keeping the policy corpus small and
hand-reviewed, not in the grounding check itself.

**Q: What's the difference between a regression test and an evaluation?**

A regression test (`tests/`) checks that code behaves the same as before
— did `scanner.py`'s score stay identical, did `validate_grounding()`
still reject a known-bad citation. An evaluation (`evals/run_v2_evals.py`)
checks something pytest can't score on its own: is the *generated*
output actually good — does it hit the expected risk level, does it cite
something real, across a set of representative cases with known-correct
expected outcomes. Regression tests prove correctness; evaluations prove
quality.

**Q: How is cost controlled between mock and live mode?**

Mock mode is the default everywhere, including CI — no API key is ever
configured in GitHub Actions, so a live call is structurally unreachable
there, not just discouraged. When live mode is used: requests are capped
at 1200 output tokens, run at low reasoning effort, have a 30-second
timeout, and a hard $5 monthly spend limit is set in the Anthropic
Console as a backstop — turning "how bad can a mistake get" from
unbounded into a small, known number.

**Q: Tell me about a real bug you found and fixed in this project.**

A Day 9 security review found that `validate_grounding()`'s citation
check had a real logic gap: it normalized a quote by collapsing
whitespace before checking it was a substring of the source text, but a
whitespace-only quote collapses to an empty string — and an empty string
is a substring of *everything* in Python. So a citation with a real
`chunk_id` but a blank quote passed the check unconditionally. Fixed with
one guard clause rejecting an empty normalized quote, plus a regression
test (`test_whitespace_only_quote_is_rejected`) proving it's caught now —
committed alone, in its own isolated commit, separate from everything
else.
