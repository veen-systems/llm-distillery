# The ≥ 7 pool — RESULT (2026-09-26)

**177 new Thriving positives**, adjudicated in scope and oracle-labelled. Their labels can be
mixed into training (alias control d = +0.017). The top of the scale is still empty: **0 rows at
weighted ≥ 8** (max 7.35). Plan: `PLAN.md` (`682c214`), committed before any judge or oracle call.

## Step 1 — blind adjudication ($0), `analyse.py` → `result_step1.txt`
| check | result |
|---|---|
| outputs vs inputs (ids, order, keys, verdict set, quote-in-article) | **0 problems** over 14 files |
| drift, pass A vs pass B, binary, 131 rows | **0.924** (stop below 0.90) — passes |
| A/B splits (tie rule → not in scope) | 10 |
| **in scope** (`in_scope_ids.json`) | **183 of 656** |

In-scope yield per filter set — ⚠️ design-weighted; do NOT pool into a production rate:

| scored ≥ 7 by | in scope | predicted |
|---|---|---|
| uplifting only | **86 / 192 = 44.8%** | 15–35% ✗ above |
| belonging only | **89 / 450 = 19.8%** | 10–30% ✅ |
| belonging + uplifting | 8 / 14 = 57.1% | 20–50% (n too small) |

*Reading (assistant's, not measured):* at ≥ 7, uplifting v7 is right about Thriving far more
often than at its op-point (11.5% for uplifting-only passers in the more-positives run). Its top
end is closer to on-lens than its bulk.

## Step 2 — oracle, `analyse_oracle.py` → `oracle_result.txt`
Prompt `prompt-v8-4.md` (`c4705408c477`), k=3, DeepSeek `deepseek-chat`, every id scored exactly
once per run (3 of 6 runs needed resumes for JSON parse failures; all filled).
- **Alias control** (n=50 of the 2026-09-24 V4.1 labels, seed 20260928, same prompt): median Δ
  **+0.017**, IQR [−0.079, +0.133]. |d| ≤ 0.30 → **MIX**. The alias did not move since 09-24.
- **Kept 177**, excluded 6 (oracle majority not in scope).
- Weighted ≥ 4.5: **154**, ≥ 6: **58**, ≥ 7: **8**, ≥ 8: **0** (max 7.35). The more-positives
  round gave 120 / 21 / 2 / 0 from 186 rows.
- Per dimension ≥ 6 / ≥ 8: Wellbeing 110/23, Connection 99/4, Justice 29/5, Evidence 99/16,
  Reach 63/4, Durability 123/21.

## The scale question (PLAN.md's test)
Articles that production scored ≥ 7 AND Claude calls in scope get **no** oracle weighted average
≥ 8. By the pre-registered reading, that points at the oracle's **scale**, not missing data.
⚠️ Part of it is arithmetic: a weighted mean of six dimensions, averaged over k=3, compresses
extremes. Single dimensions do reach ≥ 8 (Wellbeing 23 rows, Durability 21). Only Connection and
Reach stay nearly empty at the top.

## Cost
**$0.36 off-peak** (Saturday; estimated from counted tokens in the six logs), against the
**$0.10–0.20 estimate** the owner approved. The estimate was low; the 2026-09-24 round's $0.24
for a similar size was the better anchor.

## Not done (owner calls)
- Hard negatives: the 473 not-in-scope rows as capped negatives (adj3 precedent). Not run.
- A retrain on adj3 + these 177 rows (v10 candidate): a separate, gated step (ADR-021).
