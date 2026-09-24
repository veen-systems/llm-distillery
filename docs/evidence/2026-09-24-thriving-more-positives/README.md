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
