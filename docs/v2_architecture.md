# AgentGuard v2 Architecture — Input → Process → Output Flow

This is the one picture every later lab fits into. v2 is a **pipeline**: a
sequence of stages where each stage's output becomes the next stage's
input. Only one stage is ever allowed to set the risk score — everything
after it may only explain.

## The five things flowing through the pipeline

1. **Agent data** — the synthetic JSON record for one AI agent (tools,
   owner, approval settings). Same shape v1 already reads.
2. **Scanner findings** — v1's deterministic output: a score, a risk
   level, and the specific rules (AG-001–AG-005) that triggered. Produced
   by `scanner.py`, unchanged from v1.
3. **Policy evidence** — short passages retrieved from the `policies/`
   folder, chosen because they're relevant to whichever findings fired.
4. **Model output** — a structured, cited explanation written by a free
   "mock analyst" or the real Claude API, using only the retrieved
   evidence — never anything the model "remembers" on its own.
5. **Validation** — a check that runs after the model responds, confirming
   every citation is real and the score was never touched.

## Flow diagram

```
                     Synthetic Agent JSON
                             │
                             ▼
                 v1 Deterministic Scanner
                 (scanner.py, rules AG-001..005)
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
     Score + Risk Level              Findings (list of
     (the one and only               triggered rules)
      source of risk truth)                  │
              │                              ▼
              │                    Retrieval Query
              │                    (built from findings)
              │                              │
              │                              ▼
              │                    Policy Retriever
              │                    (RAG over policies/)
              │                              │
              │                              ▼
              │                    Retrieved Policy Chunks
              │                    (the only evidence allowed)
              │                              │
              │                              ▼
              │                    Mock Analyst / Claude API
              │                    (explanation + citations)
              │                              │
              │                              ▼
              │                    Grounding Validator
              │                    (checks citations are real AND
              │                     score/severity were not changed)
              │                              │
              │                    ┌─────────┴─────────┐
              │                    ▼                    ▼
              │              passes validation     fails validation
              │                    │                    │
              │                    ▼                    ▼
              │         Validated Explanation      Rejected — not shown
              │                    │
              └──────────┬─────────┘
                         ▼
                  Streamlit UI
        (deterministic score shown in its own
         section, separate from the AI text)
                         │
                         ▼
                  Audit Log Entry
        (latency, tokens, model, mode, cost)
```

## Security boundary: who can touch the score

| Stage | Can change the risk score? |
|---|---|
| v1 deterministic scanner | **Yes** — this is the only place a score is ever computed. |
| Retrieval query / policy retriever | No — read-only lookup against a fixed local file set. |
| Mock analyst / Claude API | No — may only describe findings and cite evidence; any attempt to output a different score or severity is discarded by the validator, not trusted. |
| Grounding validator | No — it only accepts or rejects the model's output; it never invents or edits a score itself. |
| Streamlit UI | No — it displays whatever the scanner and validator already decided, in two clearly separated sections. |

That single row — "only the v1 scanner sets the score" — is the whole
point of v2's design, and every later lab (retrieval, prompt building,
grounding, the UI) is built to protect it.

## Abuse cases considered

This architecture was designed against a specific list of things that
could go wrong at each stage — an injected instruction in retrieved
evidence, an invented citation, a model-altered score, runaway API cost,
a leaked key, malformed model output, sensitive data in logs, and more.
See [`docs/v2_threat_model.md`](v2_threat_model.md) for the full risk to
control mapping, and [`docs/v2_cost_controls.md`](v2_cost_controls.md)
for the specific settings that keep any live Claude API usage small and
bounded.
