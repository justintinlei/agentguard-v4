# AGP-005 - Grounded AI Explanations

When an AI model explains a security finding, it must say clearly which
deterministic finding it's explaining and back up its explanation with
citations to these approved policy documents. A claim with no valid
citation must be rejected instead of shown to a user.

## Required controls

- The model's output must never change the deterministic score or
  severity it's explaining — only describe it.
- Every citation must point to a real, existing policy passage — no
  citation, no display.
- Structured model output must be validated before anyone sees it, not
  trusted on arrival.
