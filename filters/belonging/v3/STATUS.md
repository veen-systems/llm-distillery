# belonging v3: STATUS (2026-10-08)

**State: GATE PASSED, NOT DEPLOYED.** Production runs belonging **v1**. Switching is the owner's decision, separate from the
gate (it weighs volume and the score-scale shift below). NexusMind loads the HIGHEST `vN` on disk, so landing this directory in
NexusMind makes it live on the next cycle: there is no separate cutover step.

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
- **Free checks (b650 GPU):** leak check NOT LEAKED; proxy recall 23/23; ovr.news EXP-028's 40 published stories:
  passes 9/27 panel-weak and keeps 9/13 panel-good (v1 by construction passes all 40); ovr EXP-029 panel picked c2b over c2a.

## ⚠️ Before any switch: known effects

- **Volume:** 25 flags vs v1's 109 on a 5,000-row unseen production draw (measured), so roughly a quarter. Extrapolated, not
  measured: ovr's ~81/day published Belonging falls to ~20/day.
- **Normalization is v1's** (`normalization.json`, fitted 2026-07-31 on v1's production raws; its `filter_version` field says
  1.0). NexusMind's loader checks `n_articles` and `raw_min`, not the version, so it loads. But v3's normalized scores map
  through v1's CDF until a refit on v3's own production scores. ovr's normalized ≥ 4.5 display gate and NexusMind's
  enrichment `min_score` (NexusMind NM#319) read that number. Post the switch and refit dates on llm-distillery#170.
- **Probe** (`probe/embedding_probe_e5small.pkl`) is v1's file, byte for byte, so Stage 1 cannot differ from v1 by
  construction. Where a split was observable, on the 5,000-row production draw (1,029 `stage1_low` rows, so it could have
  differed on any of 5,000), v1 and v3 split identically. The held-out sets are stage-2 rows by design, so they say nothing here.
- Op-point 4.0 (`base_scorer.py` TIER_THRESHOLDS), as v1; pinned in `tests/unit/test_normalization_op_point.py`.

## Not done (deploy steps, owner's go required)

Hub upload (`jeergrvgreg/belonging-filter-v3`), pre-placing the adapter on gpu-server, `deploy_to_nexusmind.sh belonging v3
--dry-run` + diff, NexusMind PR. RUNBOOK § Deployment to NexusMind.
