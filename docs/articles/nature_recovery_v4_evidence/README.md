# nature_recovery v4 — evidence data (backing the report + paper drafts)

Raw quantified results behind `docs/reports/nature_recovery_v4_report.pdf`, kept here so the
paper drafts in `docs/articles/` can cite concrete numbers. Regenerate the PDF with
`scripts/report/build_nature_recovery_v4_report.py`.

| file | headline numbers | feeds which draft |
|------|------------------|-------------------|
| `needle.json` | raw feed ~**0.3%** recovery (ADR-014); training enriched to **14.7%** MEDIUM+ (n=3892); only **2** articles in the 8–10 band | needle-in-haystack |
| `probe.json` | recall-first e5 probe: val recall **98.2%** on MEDIUM+ at threshold 3.225, routes **36%** to Stage 2; full recall curve | hybrid-two-stage, needle-in-haystack |
| `student.json` | held-out DeepSeek test (n=391): v4 **prec 0.848 / recall 0.672 / F1 0.750 / Spearman 0.821** vs v2 0.614/0.603/0.609/0.795 | needle-in-haystack |
| `gate.json` | ground-truth gate (ADR-021): v4 > v2 on every metric; the agreement_gate false-FAIL note | needle-in-haystack (V&V), + augmented-engineering#25 |
| `gate_v1_epoch3.json` | the original (flawed) agreement_gate output — the false FAIL, for the reproduce-don't-assess story | — |
| `label_consistency.json` | oracle self-MAE: Gemini **0.173** vs DeepSeek **0.380** (2.2×); cross-oracle generosity gap (Gemini mean WA 4.94 vs 4.09); under-fit articles both-oracles-surface 3/3 | oracle-consistency-beats-data-volume |
| `calibration.json` | per-dim isotonic; test MAE 0.7695→0.5990 (+22.2%); tier dist; curve anchors | cross-filter-normalization, needle |
| `cost.json` | $4.81 one-time teaching; $0/article local vs $0.0013–0.01 cloud/vendor; break-even ~3,700 articles | needle-in-haystack (why-build-not-buy) |
| `baselines.json` | v1→v2 ranking lineage (Recall@20 0.55→0.70, NDCG@10 0.71→0.86) | needle-in-haystack |
| `verdict.json` | deploy recommendation + v4-vs-v2 comparison table | report only |

**Caveat for citation:** `student.json`/`gate.json` are the *deployed* model (seed-42 scale-2.0,
test recall 0.672). Held-out test set is DeepSeek-labeled = v4's own oracle (home advantage on
MAE; the recall/precision gaps vs v2 are the like-for-like comparison against the chosen line).
