# DeepSeek oracle token counts — the only counted shapes we have

Copied here 2026-08-24 because `datasets/` is gitignored (`.gitignore:76`, and
llm-distillery#97 is why it stays that way), so `scripts/analysis/oracle_cost.py`
would have failed on a clean clone. **These two logs contain counters only — no
article text, no titles, no URLs** — so they are safe in a public repo.

Both are `scripts/score_deepseek_production.py` run logs from 2026-07-07, under the
**pre-2026-08-16** DeepSeek rate card.

| file | n | input/article | output/article | cache hit | logged cost |
|---|---|---|---|---|---|
| `nr_v4_batch.log` | 3,641 | 5,986 | 195.9 | **0.34%** | $3.24 |
| `nr_v4_positives.log` | 289 | 6,502 | 293.7 | **4.9%** | $0.27 |

⚠️ **The file names say v4; the runs are v3.** `nr_v4_batch.log` reads
`nr_v3_batch_input.jsonl` → `nature_recovery_v3_deepseek.jsonl`. The v3 prompt is not
on disk (`filters/nature_recovery/` has v1, v2, v4), so the nearest cache-ceiling proxy
is the v1/v2 template's 3.2%.

⚠️ **`nr_v4_positives.log` decays 14% → 7% → 5% across its progress lines to a 4.9%
total.** A mid-run cache reading is not a run cache rate — that decay is the most likely
origin of the "14% cache hit" this project carried as a constant for months.

Why they are load-bearing: llm-distillery#103's oracle choice was argued on two figures
**back-solved from invoice totals** under an assumed input shape. A residual inherits the
full error of everything subtracted from it. These are counts.
