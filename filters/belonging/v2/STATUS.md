# belonging v2 — DRAFT (2026-10-01)

Prompt and config only. No model, no scorer code, no calibration, and nothing deployed. Production runs
belonging **v1**.

- **What it is:** the v1 prompt plus STEP 1b, the cohesion test. It is built to the #130 ruling: belonging
  means cohesion that is holding or growing.
- **Where it stands:** evaluated on the v2 test set and on a 150-row held-out production sample.
- **Results:** `docs/evidence/2026-10-01-belonging-v2-test-set/README.md` § *Result: the v2 prompt*.
- ⛔ **Not ready to label with.** About half of the held-out passers are still junk.
- ⛔ The `v1_heldout_top` test rows must stay out of any v2 training draw.
