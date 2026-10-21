# EXP-055: cross-family panel for human_thriving (#177 step 6), IN PROGRESS

The pre-registration is `PREREGISTRATION.md`. The analysis is `analyse.py`, committed before any panel score was
read (`1185a13`). A bug fix after that commit made the pass/block ratings explicit strings, because the
agreement library refuses bools; it changes no measure.

## State, 2026-10-21

**Interim, local members only: `result-interim-locals.txt`.**
- L1 (qwen3.8:27b) is INELIGIBLE under the pre-registered 95% parse bar. Only 85 of 100 items have both
  runs. On some items it thinks until it fills the 16K context: 15 empty replies and 5 cut-off JSONs. No
  prompt was truncated; the longest is 13.3K tokens.
- L2 and L3 agree with each other at alpha 0.695 (nominal). Both pass far more than the oracle does: 62 and
  55 of 100, against the oracle's 30.
- Against their majority, the oracle's specificity is 1.000 and its recall 0.528. Ties are left out: 14
  items.

⚠️ **This is not a verdict.** The majority is two local models with a shared lenient bias, and the cloud
member is missing. "The oracle blocks what the panel passes" also fits a deliberately conservative oracle
(memory: conservative oracle prompts produce better students). The final reading waits for P1.

**P1 (Gemini 2.5 Flash):** 20 of 100 items done.
- The billing key's prepay is depleted (HTTP 402).
- The other key is free tier, limited to 20 requests per day. The owner chose (2026-10-21) to finish on it
  over 4 days: a transient user timer, `ld-exp055-p1.timer`, runs 10-22 to 10-25 at 09:30.
- ⚠️ This is a deviation from D2/D3's "paid key". Free-tier terms may let the vendor use submitted content
  (from memory, unverified).
- To undo: `systemctl --user stop ld-exp055-p1.timer`.

Data: lab `experiments/2026-10-21-cross-family-panel/{L1,L2,L3}` (hash-verified pulls). P1 is still in the
session scratchpad until it finishes.
