# AgentGuard v2 Cost Controls

Concrete, already-implemented practices that keep this project's Claude
API spend small, bounded, and predictable — not intentions, but settings
and behaviors you can point to in the code.

- **Mock mode is the default.** `AGENTGUARD_MODE` defaults to `mock` —
  every lab except the deliberate Day 6 live-call labs runs for free, with
  no network request at all.
- **One synthetic agent analyzed at a time.** The UI's dropdown selects a
  single agent per run; there is no bulk or batch mode that could multiply
  calls unexpectedly.
- **A capped, low-cost model configuration.** Live calls use
  `AGENTGUARD_MODEL=claude-sonnet-5` at `effort: "low"`, with output capped
  at `AGENTGUARD_MAX_OUTPUT_TOKENS=1200` and a `AGENTGUARD_MAX_CALLS_PER_RUN=3`
  ceiling — all set in `.env.example` / read by `claude_analyst.py`.
- **A fixed request timeout.** `REQUEST_TIMEOUT_SECONDS = 30.0` in
  `claude_analyst.py` means a hung request fails fast instead of running
  indefinitely.
- **The API key lives only in `.env`.** Never in source code, never
  committed — loaded as an environment variable at runtime
  (`ANTHROPIC_API_KEY`).
- **A hard dollar ceiling in the Anthropic Console.** A $5 monthly spend
  limit was set before any key was created (Day 2 · Lab 3) — the backstop
  if every other control above somehow failed.
- **Live testing stops once acceptance cases pass.** There's no standing
  reason to keep making live calls after a lab's verification is done.
- **Cost estimates shown in the UI are estimates, not billing.**
  `AGENTGUARD_ESTIMATED_INPUT_COST_PER_MTOK` / `_OUTPUT_COST_PER_MTOK` in
  `.env.example` are rough per-million-token figures used only to display
  a sanity-check number — they should be checked against Anthropic's
  current official pricing before being treated as accurate.
- **CI is cost-free by construction, not by convention.** No
  `ANTHROPIC_API_KEY` secret is configured in GitHub Actions
  (`.github/workflows/tests.yml`), so an automated run has no way to reach
  a live, billed call even if someone tried — verified by running the same
  `pytest -q` / `python evals/run_v2_evals.py` commands locally with both
  `ANTHROPIC_API_KEY` and `AGENTGUARD_MODE` explicitly unset and getting an
  unchanged, full pass (Day 9 · Lab 3, re-confirmed Lab 4).
