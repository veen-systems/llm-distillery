# Session 2026-07-20 — Solutions v4 corpus SCORED + train-ready (~$14), paused at train boundary

**Branch:** `solutions-v4-calibration`. **Spend: ~$14.3** ($0.19×2 Part-B + $5.95 partial + $7.98 resume).
**State: corpus fully scored + prepped into train/val/test. No model yet.** Deploy N/A.

## What happened (drove Part-B → full score → prepare_data)

Ran the paid pipeline from the turnkey Part-B state. Two staged-gate bugs, an arXiv-fix rethink,
a community-hunt that came up dry, a mid-run balance crash + recovery, then prepare_data.

**Part-B gate had 2 real bugs (the "control is decoration" class, again):**
1. Negative sentinel wrong — gate used `solution_type != "not_a_solution"` but the v4 prompt emits
   `"none"` (calib gold too). Uncorrected → reported **100% positive → PASS** (nonsense). Fixed.
2. `solution_concreteness` is a nested `{score,evidence}` dim; gate did `(…or 0)>=7` on the dict →
   `TypeError`. Fixed to unwrap `.score`. (Both fixes are in the scratch `partB_gate.py` only.)

**Part-B corrected: 39% positive / 61% not_a_solution → literal `<50%` HARD gate FAIL.** Free
diagnosis: e5 gradient is **flat** (all candidates sim 0.887-0.920, constant ~39% positive) →
tightening can't help. 39% *beats* the reviewers' ~15% forecast + exceeds the 15-30% training
target. **`<50%` is unachievable-by-design for this broad lens → reframed, NOT a corpus fault.**
Engineer chose "arXiv fix + re-check + proceed" over chasing >50%.

**arXiv fix (data-quality win, kept):** governance centroid pulled in **18,628 off-lens
arxiv/pubmed/github rows** (the ST-v3 contamination). Added `OFF_LENS` source mask to the screener
*before* top-k (backfills quota, reuses cached emb). Re-screen → 7,386 cand, Part-A PASS. Re-check
Part-B: **40% positive** — improved quality but NOT positive rate (backfill news equally mixed →
empirically confirms the flat-gradient ceiling). **Follow-up: upstream OFF_LENS into
`scripts/screening/embedding_screener.py`.**

**Community high-band hunt (free, answered "should we find them first?"):** high-concreteness
community centroid (46 anchors) retrieved from pool → dominated by github/arxiv noise; 1,208 of top
ranks already candidates. **Pool is DRY** for new high-band community — thin because the feed is
thin, not the screen. → external source-expansion only (a v2 item), NOT a v1 blocker. (Full 10K
corpus still has **90 high-band community/hybrid** — "0 in samples" was rare-cell sampling noise.)

**Holdout + negatives:** re-drew 1,500 unscreened holdout (40.9% non-EN), dropped **82 train↔holdout
leakers** → 7,304 clean candidates. 3,000 random negatives (excl reverted stubs/<200char/cand/
holdout/calib) → ~28% train mix.

**Full DeepSeek score:** crashed at 5,106 rows on **HTTP 402 Insufficient Balance** ($5.95). After
top-up, resumed (error rows auto-retry — `load_already_scored` excludes them) in **valley pricing**
→ 10,297 + 1,500, 0 errors. **DeepSeek peak/valley (mid-Jul 2026): peak 2× at UTC 01-04 + 06-10 =
CEST 03:00-06:00 + 08:00-12:00; score in valley** (CEST 00-03, 06-08, 12-24).

**prepare_data → train 9,265 / val 1,032 / test 1,500.** Test = isolated holdout via two runs
(trainval with `--test-ratio 0`, holdout with `--train-ratio 1.0` → renamed to `test.jsonl`).
Train mix 31.5% pos (gov 1,568/tech 1,203/comm 283/hybrid 191, 670 high-band); holdout 11.5% pos
(true prod base rate), 44% non-EN positives. Validated: acceptable.

## Committed this session
- `ground_truth/text_cleaning.py` + `tests/unit/test_scrape_junk.py` — **non-EN scrape-junk
  patterns** (es/it/de/nl/pt/fr: JS-disabled + Google-consent as STRONG; cookie/subscribe/not-found
  as WEAK), 24 tests pass. The pre-spend `is_scrape_junk` hardening.
- `DATA_SETUP_PLAN.md` Round 4 + `CLAUDE.md` solutions row/date.

## NEXT SESSION — train (careful gpu-server sync FIRST)
gpu-server `~/llm-distillery` is a **non-git file-copy** (no `.git`) and lacks `filters/solutions/v4`.
Sync the filter package + verify `train.py`/import currency vs this branch BEFORE training (else
stale-code model). GPU was free at pause. Then:
```
train.py --filter filters/solutions/v4 --data-dir datasets/training/solutions_v4 --output-dir filters/solutions/v4/model
  → fit_calibration.py (--test-data test.jsonl)  → holdout recall gate (ADR-021)
  → deploy: wire SolutionsPreFilterV4, retire foresight (NexusMind app.yaml + ovr filters.ts),
    normalization from production-base-rate rescore (NOT enriched corpus), Hub repo `solutions`.
```
**Scored corpus is gitignored** → only copies are local disk + `gpu-server:~/solutions_screen_work/
scored_backup/`. Training splits are reproducible from it via prepare_data (seed 42).

## Cross-repo follow-up (still open from 2026-07-19)
NexusMind `ArticleFetcher.should_replace_content` consent-guard bug (replaces real RSS summaries
with Google consent pages for ~17% of short Google-News articles). File the issue.
