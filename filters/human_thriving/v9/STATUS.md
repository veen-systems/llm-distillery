# human_thriving v9 — status

**2026-09-25: PACKAGED, NOT DEPLOYED.** Nothing reads this package in production.

| step | state |
|---|---|
| gate (ADR-021) | ✅ WIN vs v8 (`ground_truth_gate.json`) |
| live-week audit | ✅ WIN vs v8 |
| cut-off | ✅ 4.5, owner ruling 2026-09-25 |
| calibration / normalization | ✅ own `calibration.json`; own `normalization.json` (fitted at packaging) |
| `verify_filter_package.py` (static) | ✅ 7/7 |
| real-scorer smoke test | ⏳ on b650: `venv-prodparity/bin/python scripts/gate/v8_smoke_test.py v9` |
| Hub upload (`jeergrvgreg/human-thriving-filter-v9`) | ⏳ not done |
| NexusMind deploy (parallel, reader-invisible slot) | ⏳ approved in principle (step 2a); ⏸️ open: does v9 REPLACE v8 there? |
| reader-facing cutover from `uplifting v7` (#151) | ⛔ NOT decided (owner: "not yet") |

Weights: gitignored. Local copy at `filters/human_thriving/v9/model/` (deploy guard E); source run
`b650-gpu:~/llm-distillery/runs/human_thriving_v8_adj3/`. Adapter sha256 prefix `4f4feac2ed6e`.
