# Oracle canary set (#177) — design

Status: **design ruled 2026-10-16; build in progress.** Owner rulings it builds on: veen-systems/pipeline-atlas#169 (2026-10-15) — a
frozen ~100-item set per filter, judged by a cross-family LLM panel with chance-corrected agreement; the same set
is the canary; a one-off owner hand-label of ~30 items for the filter the Thriving tab reads, as a reference.

## Why #157 is not enough

#157 now stamps `served_model` on every label, but measured 2026-10-16 it is the TIER (`deepseek-flash`, bare
`gemini-2.5-flash`): the V4 → V4.1 swap of 2026-09-10 would not have shown. Measured the other way (EXP-042,
n=12): that swap alone moved 3 of 12 rows across the 4.5 op-point. A canary sees the swap as what it is — the
oracle's scores on frozen input moving — whatever the vendor calls the model.

## The two jobs, kept apart

| job | compares | detects | needs |
|---|---|---|---|
| **Drift (the canary)** | today's oracle vs **the same oracle's stored baseline** on the frozen set | the labelling function changed (model swap, prompt edit, decoding change) | a baseline and a measured re-run noise floor |
| **Accuracy (the anchor)** | the oracle vs **the cross-family panel** (+ owner slice) | the labelling function is wrong | the panel's labels and its own agreement (alpha) |

The canary does not need the panel to work; the panel does not need to be re-run per labelling run. Build the
canary first: it is the one with a call site.

## Design

1. **Set (per filter, starting with `human_thriving`, prompt `c4705408c477`):** 100 production articles, NOT in
   any training split (checked with EXP-051's e5 instrument at ≥ 0.93 and `gate3.py`'s lexical keys), stratified
   by current oracle score so flips are observable: ~30 near the op-point (3.5–5.5), ~30 above, ~40 below.
   Frozen as a content-hashed JSONL + manifest (id, sha256 of the exact text sent). ⚠️ v8's stored test labels
   are V4 labels — unusable as a baseline.
2. **Noise floor (paid, ~cents):** score the set **k = 3 times** on the current oracle, same day. Read the
   run-to-run **flip count at the op-point** and per-row |Δ| (#95's rule: flips, not max |Δ|).
3. **Pass bar (pre-registered after step 2's noise, before any canary verdict):** a run FAILS if its flip count
   against the baseline mean exceeds the noise floor's worst pairwise flip count + a margin, or if its mean signed
   Δ exceeds a stated bound. Stamped on the run.
4. **Call site:** `scripts/oracle/canary.py run --filter … --prompt …` writes a pass record keyed by
   `prompt_sha256` + `served_model` with date and verdict. `score_deepseek_production.py` and `batch_scorer` REFUSE
   to start without a pass for their own prompt digest younger than the freshness window, unless
   `--skip-canary "<reason>"` (the reason is stamped on every row of the run).
5. **Proof it fires (Done-when of #177):** a known label-changing prompt edit (the v8-5 scope edit, EXP-042's
   neighbour) must FAIL the canary; the unedited prompt must PASS.
6. **Panel (later, the anchor):** b650 local models + DeepSeek + Claude on the same 100, Krippendorff's alpha +
   AC1 (ovr's proposal), then the owner's ~30-item slice.

## Owner rulings (2026-10-16)

- **First filter: `human_thriving`** (prompt `c4705408c477`, DeepSeek).
- **Freshness: every labelling run.** The canary re-scores its set immediately before each run.
- **No fresh pass, or a FAIL: REFUSE**, with `--skip-canary "<reason>"`; the reason is stamped on every label.
- (#176 step 3, same sitting: `prepare_data.py` WARNS with its cross-split near-duplicate count; splits are not
  restructured.)
