# Thriving adjudication — FULL RUN result

**2026-09-24.** Plan in `PLAN.md`, written before the run. Merge and all checks: `merge.py`, which
rebuilds `datasets/scored/human_thriving_v8/labels_adjudicated_v1.jsonl` (gitignored; the tracked
`out_*.jsonl` here plus the pilot's are its complete source). The original labels are untouched.

| check | result |
|---|---|
| every `out_*` file vs its input | ids, order, verdict set, and quote-in-article all verified by `merge.py` |
| drift check, A vs B on the 166-row seeded sample | **0.946** (stop below 0.90) — passes |
| rows adjudicated | **878** = every label ≥ 3.5 (50 pilot + 828 full) |
| tie rule (A/B split → out) | applied to 11 rows |

## Outcome — every change is in → out, none is out → in

| oracle label band | kept `in_scope` | moved out | share moved |
|---|---|---|---|
| **≥ 4.5** (what the student learns to publish) | 204 | **112** | **35.4%** of 316 |
| [3.5, 4.5) | 121 | **441** | **78.5%** of 562 |

The out verdicts split as: `out_of_scope` 452, `no_person_benefits` 47, `response_to_harm` 36,
`harm_is_subject` 18. All 878 rows carried the oracle verdict `in_scope`.

⚠️ **This is Claude's judgment under a written rubric**, validated on the pilot (owner 10/10,
n=10). It is not independent human truth. Self-consistency (0.946–0.960) is not independence.

## Not done yet
- **The training rule for moved-out rows**, i.e. how their six dimensions are set. PLAN.md left
  this open. It must be written before any retrain.
- Retrain (b650), the ADR-021 gate, and a live audit.
