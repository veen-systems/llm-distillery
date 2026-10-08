# Belonging adj1 build (2026-10-07)

**What:** the training data for the belonging retrain, `build_adj1.py` → `datasets/training/belonging_v1_adj1/`
(gitignored). Owner rulings: 2026-10-03 (adjudication), 2026-10-07 (full text; hard negatives = the 121 one-moment
rows; ~800 production easy negatives at k=1).

**Data FMEA:** the failure modes and their checks are the repo-wide checklist `docs/checklists/training-data-fmea.md`
(owner: "this should be part of the runbook"). The build runs FM-T2, FM-H1, FM-H2, FM-L1, FM-L2, FM-P1 itself and
drops FM-D1 twins; `training/validate_training_data.py --production-sample` runs the rest. This README records THIS
build's result per row.

## Per-row status for this build

| id | Status |
|---|---|
| FM-T1 | found 2026-10-07 (owner asked); addressed by the easy negatives — **result below** |
| FM-T2 | full text for every cut row (509 held-out, 2,251 harvest; 393 from the monthly archive) |
| FM-T3 | **accepted by owner 2026-10-07** (113 positives' labels made on cut text) |
| FM-D1, FM-D2, FM-D3 | **result below** |
| FM-H1 | the build drops `gate.content_twins`; the gate refuses on overlap |
| FM-H2 | `assert_disjoint` on every id |
| FM-L1..L3, FM-P1 | raised by the build (exact counts: 237 positives, treatment 238/566/55, oracle covers every row) |
| FM-L4 | not mechanized; measured: one `prompt_hash` (`99ea1765a7ea`) across the hard and easy negatives |
| FM-L5 | **accepted by owner 2026-10-07** (easy negatives at k=1); 796 of 798 scored, 2 failed permanently |
| FM-S1 | **open** (TODO item 0.5) |
| FM-S2 | the easy-negative draw excludes `news.google.com` |
| FM-S3 | **open**, not mechanized (cost here: 393 rows briefly called lost) |
| FM-G1, FM-G2 | `gate.py` refusals; two scoring orders |

## Inputs and cost

- **Hard negatives:** Gemini Flash, belonging v1's prompt, k=3 over 121 rows on full text; 3 × 121/121, 0 failures.
  Cost NOT measured (`batch_scorer` records no tokens); estimate ~$1.25.
- **Easy negatives:** `draw_easy_negatives.py` on sadalsuud: 800 of 439,704 distinct rows (window
  `filtered_20260909_052755 .. filtered_20261007_173310`, 160 files; 63,979 GN and 69,521 short rows excluded);
  2 held-out twins dropped → 798; k=1 oracle. Cost estimate ~$2.80, not measured.
- **Language stamps:** the collector's `language` field, recovered from FluxusSource's 1,814 collection archives by id
  (`datasets/belonging_language_stamps.json`): v1 rows 251/7,370 stamped (they predate the archives), harvest
  3,998/4,591, easy negatives 548/800, held-out 1,065/1,200.

## Result

**Not built yet (2026-10-08).** Two blockers, both in `docs/TODO.md` item 0: the 2 unscored easy negatives,
and `assert_disjoint` refusing 61 of v1's own surviving rows (pilot, calibration and v2-test ids drawn FROM v1's splits;
6 are v2-test rows). A reviewer's scratch build (2 easy negatives dropped, the disjoint check on new rows only) gave:
train 6,365 / val 778 / test 781 rows; MEDIUM+ labels 273 / 32 / 30; 44 of 794 easy negatives labelled positive; 1 held-out
twin and 33 cross-split twins dropped; FM-T1 still coupled (training median 900 chars vs 2,235 production; positive share
10.7 / 15.6 / 18.9% at 2–4k / 4–8k / >8k vs production 5.8 / 10.6 / 12.7%). Not an official run: re-run after the rulings.
