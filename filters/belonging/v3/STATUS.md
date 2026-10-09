# belonging v3: STATUS (2026-10-08, live 2026-10-09)

**State: LIVE since NexusMind run `bd00dad6-9dd8-4f95-b9f4-242ad90cab68` (2026-10-09 00:08–01:24 CEST),** replacing v1
(NexusMind PR #627, scorer image `nexusmind-scorer:facfa8ba21e2-we1173758`). Checked by Claude on sadalsuud: all 3,673 rows of
`data/filtered/belonging/filtered_20261009_012040.jsonl` carry `version "3.0"` (3,139 stage2, 534 stage1_low); 19 stage-2 rows
have raw ≥ 4.0 (0.52%; the 5,000-row pre-switch draw predicted 25/5,000 = 0.50%, v1 109/5,000). One cycle, so read it as the
direction only.

## What it is

belonging v1's architecture, prompt and dimensions (Gemma-3-1B + LoRA, hybrid e5 probe Stage 1, isotonic calibration), retrained
on reshaped data. It is **candidate 2b** ("c2b") of `docs/evidence/2026-10-08-belonging-candidate2-plan/PLAN.md`:
- v1's splits under the 2026-10-03 adjudication (238 positives demoted to ≤ 2.0, 566 dropped, 55 kept), minus 61 rows that
  evaluation sets were drawn from
- 237 harvest-r1 positives (two blind judges + owner check, rubric v2.2), with k=3 Gemini dimension labels on v1's prompt
- 135 hard negatives (both judges `out_gift_official` 46 / `out_harm_is_story` 89), capped at 2.0
- ~800 random production easy negatives (k=1), kept as labelled
- **NOT** the 121 `out_one_moment` hard negatives (owner: single-person stories stay an open question)

Trained at `49d52a9`, 6 epochs, `--select-metric last` (epoch 6), seed 42, head+tail 256+256 on b650 (RTX 5090). Built by
`docs/evidence/2026-10-08-belonging-candidate2-plan/build_cand2.py c2b`.

## Evidence

- **Gate (binding pass rule v2, held-out set 3): PASS.** k = 76/83 (bar 59); weighted Δspec vs v1 at matched recall +0.350,
  95% CI [+0.322, +0.376], both row orders, 0 order flips. ⚠️ The size is partly by construction (bands are v1's own score;
  v1's matched threshold ≈ 4.03). Read `docs/evidence/2026-10-08-belonging-candidate2-plan/PLAN.md` § 10 before quoting it.
  Output: `docs/evidence/2026-10-08-belonging-heldout3/result_v1_c2b.txt`.
- **Parity:** this package (renamed from the gated `v1_c2b`) re-scored all 585 judged set-3 rows on b650: 585/585
  identical, max |Δ| 0.0.
- **Free checks (b650 GPU):** leak check NOT LEAKED; proxy recall 23/23 (⚠️ the 23 come from the same harvest draw as the training positives, so not held-out; leak-check README); ovr.news EXP-028's 40 published stories:
  passes 9/27 panel-weak and keeps 9/13 panel-good (v1 by construction passes all 40); ovr EXP-029 panel picked c2b over c2a.

## ⚠️ Known effects (written before the switch; still true)

- **Volume:** 25 flags vs v1's 109 on a 5,000-row unseen production draw (measured), so roughly a quarter. Extrapolated, not
  measured: ovr's ~81/day published Belonging falls to ~20/day.
- **Normalization is v1's** (`normalization.json`, fitted 2026-07-31 on v1's production raws; its `filter_version` field says
  1.0). NexusMind's loader checks `n_articles` and `raw_min`, not the version, so it loads. But v3's normalized scores map
  through v1's CDF until a refit on v3's own production scores. ovr's normalized ≥ 4.5 display gate and NexusMind's
  enrichment `min_score` (NexusMind NM#319) read that number. Switch date posted on llm-distillery#170 2026-10-09; post the refit date there too.
- **Probe** (`probe/embedding_probe_e5small.pkl`) is v1's file, byte for byte, so Stage 1 cannot differ from v1 by
  construction. Where a split was observable, on the 5,000-row production draw (1,029 `stage1_low` rows, so it could have
  differed on any of 5,000), v1 and v3 split identically. The held-out sets are stage-2 rows by design, so they say nothing here.
- Op-point 4.0 (`base_scorer.py` TIER_THRESHOLDS), as v1; pinned in `tests/unit/test_normalization_op_point.py`.

## Switch steps (done)

Hub `jeergrvgreg/belonging-filter-v3` (adapter `c262424`); NexusMind built the scorer image and switched sadalsuud (PR #627).
Our RUNBOOK's gpu-server path was not used: it is stale since NexusMind NM#395 (`docs/TODO.md`).

## Switch decision and rollback rule (owner GO 2026-10-08; fixed BEFORE the switch)

The owner approved the switch on Claude's recommendation (ADR-023: a weak story costs a reader; v1's published Belonging is 27/40
weak on ovr.news's EXP-028 panel). Expected range, estimated, not measured: ~20–36 published Belonging stories/day, about half
of them good, vs ~81/day with ~26 good today. **Check:** ovr.news re-runs its EXP-028 panel on a fresh post-switch Belonging sample
~2 weeks after the switch. **Roll back to v1**: ⛔ NOT by removing `filters/belonging/v3` (corrected 2026-10-08 by NexusMind's review, PR #627: the v3 image
carries no v1 weights, so removing v3 on it stops the scorer and takes all six filters down). Rollback = the kept previous scorer
image plus a sadalsuud revert, or a new build; NexusMind owns it if good
stories per day fall clearly below ~26, or if the weak share does not fall below 27/40. "Clearly" means outside the panel's
95% interval.

## NexusMind review notes (PR #627, 2026-10-08), for the refit

- **Refit population:** `data/filtered/belonging` is keyed by filter NAME, so it mixes v1 and v3 rows. Fit only rows with
  `nexus_mind_attributes.belonging.version == "3.0"`.
- **Ceiling until the refit:** v3's calibration caps community_fabric at 6.33 and slow_presence at 6.78. Its highest weighted
  raw is ~7.79, below v1's fitted raw_max 7.97, so the top ~1% of v1's normalized curve is unreachable until the refit.
  Smoke article: v3 raw 5.71 → normalized 6.57; v1 raw 6.45 → 8.74.
- `filter_version: "1.0"` also sits in `calibration.json`, `normalization.json` and `training_metadata.json`, and the
  `inference_hybrid.py` docstrings say "v1" (the probe IS v1's). Nothing reads them. It is left as is
  because changing calibration.json would change the gated package's bytes; it gets fixed at the refit.
