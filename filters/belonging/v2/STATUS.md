# belonging v2 — DRAFT (2026-10-01), PARKED 2026-10-02

⛔ **PARKED (owner-approved plan, 2026-10-02):** the next belonging model reshapes the TRAINING DATA, the human_thriving
v9 recipe: adjudicated v1 labels, production positives and hard negatives, v1's prompt for dimension scores. This
prompt is not the lever. Its leakage, and the record that added rules move failures without removing them, both point
that way. Plan: `docs/TODO.md` ▶ START HERE item 0; evidence `docs/evidence/2026-10-02-belonging-reader-snapshot/`.

Prompt and config only. No model, no scorer code, no calibration, and nothing deployed. Production runs
belonging **v1**.

- **What it is:** the v1 prompt plus STEP 1b, the cohesion test. It is built to the #130 ruling: belonging
  means cohesion that is holding or growing.
- **Where it stands:** evaluated on the v2 test set and on a 150-row held-out production sample.
- **Results:** `docs/evidence/2026-10-01-belonging-v2-test-set/README.md` § *Result: the v2 prompt*.
- ⛔ **Not ready to label with.** About half of the held-out passers are still junk.
- ⛔ The `v1_heldout_top` test rows must stay out of any v2 training draw.
- ⛔ **The prompt's contrast examples paraphrase test-set rows** (review 2026-10-02). Rewrite them from rows
  outside every evaluation set before the next evaluation.
- ⚠️ **Cliff risk (FILTER_PLAYBOOK §1b):** the 2.5 cap on community_fabric plus the code gatekeeper (< 3.0 caps
  the score at 3.42) make a step. Before any deploy, check student scores on capped rows near 3.0.
