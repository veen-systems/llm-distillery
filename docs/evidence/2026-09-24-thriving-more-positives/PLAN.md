# More Thriving positives — plan (written before adjudication)

**2026-09-24, evening.** The owner asked "should we get more data in the meantime?" and
"also more distributed among all possible output dimensions?". The assistant proposed this plan.
The owner then left the session open **without approving the ~$3 oracle step**. So this runs
**only the $0 part** and stops before any oracle call.

## Why (measured on `datasets/training/human_thriving_v8_adj1/`)
Labels ≥ 4.5: train 161, val 20, test 23. The high end is nearly empty: 33 rows ≥ 6, 1 ≥ 7. By
dimension, rows ≥ 8: justice 12, cohesion 3, distribution **0**, durability 3.

## Pool (read-only on sadalsuud, 2026-09-18 → 09-24, ~39 cycles per lens)
Stage-2 passers at each lens's EXECUTED op-point: uplifting 4.5, human_thriving 4.5, belonging 4.0.
Solutions uses **5.0** (its `medium_high` tier), not its 2.25 op-point, to raise the yield of
strong candidates. Excluded: `news.google.com` in the url (standing rule; never oracle a GN row),
content < 300 chars, ids already in the v8 corpus, and duplicate `content_hash`.
**11,946 unique candidates.**

## Sample (`sample.jsonl`, seed 20260924) — ⚠️ DESIGN-WEIGHTED, on purpose
| stratum | pool | drawn |
|---|---|---|
| v8_hit (any v8 pass) | 1,389 | 200 |
| belonging_no_v8 | 2,910 | 200 |
| uplifting_only | 7,610 | 200 |
| solutions (≥ 5.0) | 37 | 37 (all) |

This is **active learning toward positives** (ADR-005), not a production-representative sample.
In-scope yields are reported **per stratum**. No pooled "production rate" may be derived from it.

## Steps
1. Blind Claude scope adjudication. Same rubric, rulings, instructions and verdict set as the
   full run. Pass A covers every row; pass B covers a seeded 20% as the drift check (stop below
   0.90); an A/B split goes out.
2. **STOP.** Oracle dimension scoring of the in-scope rows (k=3, DeepSeek V4.1), the V4-vs-V4.1
   control on ~50 existing in-scope rows, and the 80/10/10 split need the owner's approval
   (~$3).

## Predicted (before running)
In-scope yield: v8_hit **50–70%**, belonging_no_v8 **25–45%**, uplifting_only **15–35%**,
solutions **30–60%**. These are guesses anchored on the full run's 35.4% moved-out rate for
labels ≥ 4.5.

## Oracle step — APPROVED by the owner 2026-09-24 (topped up; "dolne" = done), rules fixed before any call

The measured cost is ~$0.20, not the ~$3 first quoted. That figure was priced at the uncached rate;
k=3 on one article costs ≈ $0.00077 once the prompt is cached (EXP-010 repriced at V4.1).

- **Prompt: `prompt-v8-4.md`** (the current oracle prompt), k=3, DeepSeek `deepseek-chat` (V4.1).
- **Control (the model swap):** 50 existing rows, seeded, that are adjudicated `in_scope` and whose
  label was produced by **v8-4 under V4** (`prompt_hash c4705408c477`, the 456-row relabel). Only
  the model differs. Rule: let `d` = median of (V4.1 − V4) on the weighted average over the 50.
  **If |d| ≤ 0.30, the new rows are mixed into train/val/test (80/10/10). If |d| > 0.30, the new
  rows go to TEST ONLY**, because mixing two oracle versions into one training set is a
  hand-built population.
- **Oracle disagrees with Claude:** if the oracle's k=3 majority verdict on a Claude-`in_scope`
  row is not `in_scope`, its dimensions are forced to 0–2 and are unusable as a positive. The row
  is **excluded** and counted, not relabelled.
