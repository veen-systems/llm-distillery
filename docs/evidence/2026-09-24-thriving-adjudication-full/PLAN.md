# Thriving adjudication — FULL RUN plan (written before the run)

**2026-09-24.** The pilot passed all four bar items (`../2026-09-24-thriving-adjudication-pilot/README.md`,
owner 10/10). The definition, categories, blinding and instructions are **identical** to the pilot.

- **Population:** every `human_thriving v8` label ≥ 3.5 not in the pilot. That is 828 of the
  878 rows, shuffled with seed 20260925, in batches of 60 (`input_A*.jsonl`).
- **Pass A:** every row, one blind subagent per batch.
- **Pass B (drift check):** a seeded 20% sample (166 rows, `input_B*.jsonl`), judged blind
  again. **Stop rule: if A-vs-B binary agreement on the sample falls below 0.90, the run is NOT
  used and the result is reported, not repaired.**
- **Ties** (A and B split on in/out): the row is set **not in scope**. This follows ADR-023:
  when unsure, protect specificity.
- **Output:** `datasets/scored/human_thriving_v8/labels_adjudicated_v1.jsonl`, a new file. The
  original labels are untouched. Each row carries the original verdict and label, the
  adjudicated verdict, the quote, the reason, and the pass(es) that decided it. Rows below 3.5
  are copied unchanged, marked `not_adjudicated`.
- **Not decided here:** how a corrected out-of-scope row's six dimensions are set for training.
  The pilot pre-registration said "the oracle's 0–2 out-of-scope convention". The exact rule is
  written before any retrain.

**Owner, 2026-09-24, before the run:** *"A little bit strict is actually a good thing. th thriving
lens is a firhose right now"*. This supports the tie rule above. It does not change the definition:
the adjudicators apply the rubric and rulings as written, not a stricter private standard.
