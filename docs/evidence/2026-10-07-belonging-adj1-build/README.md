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
| FM-L5 | **accepted by owner 2026-10-07** (easy negatives at k=1); 796 of 798 scored. The 2 failures (`south_african_mail_guardian_df80259e0965`, `greek_to_vima_d5748141857e`) were **dropped 2026-10-08** from `datasets/belonging_easyneg_articles.jsonl`: each failed every attempt in ~3.6–3.7 s across the overnight loop (`distillation.log`), so the failure is deterministic and a retry buys nothing. Cause still not logged |
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

**Built 2026-10-08** after owner rulings 1b = (a), drop all 61 v1 rows that an evaluation set was drawn from (pinned in
`build_adj1.py` as `V1_EXCLUDED_DROP`), and 1c = train anyway and let the gate judge. `build_adj1.py` exit 0;
`validate_training_data.py --production-sample ...` exit 0, no critical issues.

- **Splits:** train 6,322 / val 768 / test 778; MEDIUM+ labels 266 / 29 / 28 (323 total: 236 harvest, 44 easy
  negatives, 43 v1). Dropped: 61 v1 (ruling 1b), 1 held-out twin, 28 cross-split twins (val/test copy).
- **FM-T1: still coupled, ACCEPTED (ruling 1c).** Training median 894 chars vs production 2,235. Positive share
  0.7 / 2.0 / 10.6 / 15.9 / 18.6% at <1k / 1–2k / 2–4k / 4–8k / >8k (production 5.8 / 10.6 / 12.7% at the top three bins).
  Cause: 73% of positives are harvest rows (recent, full text), while 85% of rows are v1's older, shorter articles.
- **FM-D2: language skew found here, not previously listed.** Among STAMPED rows only (v1 rows are mostly unstamped),
  French is 14.5% of positives vs 3.6% of negatives and ~5% of production. 30 of the 33 French positives are harvest rows,
  mostly Walloon local news (source id `belgian_dh_les_sports`, 4% of positives; the titles read as genuine
  community stories). Risk: "French local news ⇒ belonging". Not acted on; read the gate's false positives by language.
- **FM-D3:** boilerplate markers 2.1%, mostly-shared 0.3%.
- **Validator warnings:** 1,392 all-zero rows (v1 1,269 = 19% of v1, easy 123 = 15.5%: the oracle's normal output for
  off-topic rows, not a failure); no `oracle_meta` (llm-distillery#155, the scope_verdict stamp). belonging v1 does not use it.
