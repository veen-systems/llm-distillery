# Belonging retrain gate: pre-registered (owner ruling 2026-10-03, written BEFORE any training)

**The question:** is the retrained Belonging student (`belonging_v1_adj1`, or whatever version number the build
assigns) better than the live v1? "Better" means it puts fewer non-belonging stories above the op-point while still
finding most real ones (ADR-023: specificity first).

## The set: this directory's held-out rows (owner chose option A)

- **The rows:** the 295 judge-labelled rows in `datasets/belonging_heldout/judges/`. These are all 145 Gemini-ins
  plus 50 sampled Gemini-outs per band, under frozen rubric v2.2 with two blind judges.
- **The labels:**
  - **positive** = both judges `in_scope`: 44 rows
  - **negative** = both judges out
  - **excluded:** the 13 splits and any `cannot_judge`
- **The weights** come from the design, as data in `heldout_rows.jsonl` and `judges/id_map.json`:
  - band scale = pool / 400
  - a sampled Gemini-out row is weighted further by the band's Gemini-outs / 50
  - a Gemini-in row has weight 1 within its band
  - specificity and recall are reported weighted AND unweighted
- **Never trained on:** the set is in `belonging_exclusions.py`, and the build MUST call `assert_disjoint()`.

**What this set cannot measure:**
- **Belonging the v1 student scored below 2.5.** Those rows are outside the population.
- **A fair recall comparison with v1.** The population was drawn on v1's own score bands, so **v1's recall here is
  1.0 by construction** (every positive sits in `hi`/`mid`, raw ≥ 4.0). The comparison is therefore on specificity.
- **Labels beyond the judges.** The labels are judge-relative; the owner checked 10 rows.

## Scoring

- **Both models, the same way:** each model's own filter package, `inference_hybrid.py` as production runs it, on
  the same device (b650 GPU), in the same order and batch size, in one session. So the #95 batch-composition term is
  the same for both.
- **"In" = raw weighted average ≥ the op-point**, read at gate time from the package's `base_scorer.py`
  `TIER_THRESHOLDS` "medium" (v1: 4.0; `normalization.json` `raw_min` 4.0). Never restated by hand.

## Pass rule (both must hold)

1. **Specificity is clearly better.** A paired bootstrap over the negatives (2,000 resamples, stratified by band,
   seed 20261009) gives the 95% interval of Δspec = spec(new) − spec(v1), weighted. **Its lower bound must be > 0.**
   The flip count at the op-point is reported beside it.
2. **Recall ≥ 0.70 on the 44 positives** (≥ 31 found), unweighted.

## Also reported (secondary, not gating)

- the specificity of both models on v1's own test split under the 2026-10-03 adjudication ruling (demoted rows =
  negatives; dropped rows excluded)
- the owner's 10 held-out rows (`owner_check_owner.tsv`) as a per-row table
