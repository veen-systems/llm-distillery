# More Thriving positives — the $0 adjudication part is DONE; the oracle step awaits the owner

**2026-09-24, evening.** Plan: `PLAN.md`, written before adjudication. Every `out_*` file was
checked against its input: ids, order, verdict set, and quote-in-article.

| check | result |
|---|---|
| rows adjudicated (pass A) | 637 |
| drift check, A vs B on a seeded 127-row sample | **0.921** (stop below 0.90) — passes |
| A/B splits sent out (tie rule) | 10 |
| **in-scope articles** (`in_scope_ids.json`) | **198** |

## In-scope yield per stratum — ⚠️ design-weighted; do NOT pool into a production rate

| stratum (7 days of passers, 2026-09-18 → 09-24) | in scope | predicted |
|---|---|---|
| v8_hit | **119 / 200 = 59.5%** | 50–70% ✅ |
| solutions (≥ 5.0) | **18 / 37 = 48.6%** | 30–60% ✅ |
| belonging_no_v8 | **38 / 200 = 19.0%** | 25–45% ✗ below |
| uplifting_only | **23 / 200 = 11.5%** | 15–35% ✗ below |

⭐ **The uplifting_only row is a finding in its own right.** Of the articles that only
`uplifting v7`, the filter serving the Thriving tab today, surfaced in this window,
**88.5% are not Thriving** under the owner-validated rubric. The uplifting_only pool held 7,610
unique articles in 7 days. This is direct evidence for the owner's *"the thriving lens is a
firehose"* and bears on the cutover decision (#151). Caveat: it is Claude's judgment, validated
10/10 by the owner on the pilot.

## Next — needs the owner's explicit yes (~$3)
Oracle dimension scoring of the 198 in-scope articles (k=3, DeepSeek V4.1), plus the V4-vs-V4.1
control on ~50 existing in-scope rows, then an 80/10/10 split. Before any training, report
dimension coverage for Connection, Reach and Durability.

## Oracle step — DONE (owner approved after top-up), spend $0.24 (counted tokens, V4.1 off-peak)

Result (`oracle_result.txt`, from `analyse_oracle.py`, rules fixed in PLAN.md before any call):

- **Model-swap control (n=50, prompt fixed at v8-4, V4 → V4.1):** median Δ **−0.267**, mean
  −0.331, IQR [−0.652, +0.144]. |d| ≤ 0.30, so the pre-registered rule says **MIX**. ⚠️ It is
  close to the line: V4.1 scores the same articles about a quarter-point lower, so the new rows'
  labels are slightly deflated relative to the old V4 rows. Any retrain result must be read with
  that in mind.
- **New rows:** 186 kept, 12 excluded (oracle majority not in_scope). Weighted ≥ 4.5: **120**,
  ≥ 6: 21, ≥ 7: 2.
- **Per dimension on the new rows, ≥ 6 / ≥ 8:** Wellbeing 99/9, Connection 42/**0**, Justice
  21/4, Evidence 89/7, Reach 39/**1**, Durability 85/7. **The very top of Connection and Reach is
  still empty.** This round filled the middle-high band (≥ 6), not the top.
- **`datasets/training/human_thriving_v8_adj2/`** (gitignored) = adj1 plus the 186 new rows,
  seeded 80/10/10 (149/18/19). Labels ≥ 4.5: train 161 → **257**, val 20 → **34**, test 23 → **33**.
