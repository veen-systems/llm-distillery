# Belonging retrain gate: pre-registered (owner ruling 2026-10-03, written BEFORE any training)

> ✅ **Pass rule RE-RULED by the owner at the 2026-10-03 close, after review refuted the first version** (§ *Review*,
> kept below). The binding rule is § *Pass rule v2*. The first rule (§ *Pass rule*) is SUPERSEDED. Still before any
> training.

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

## Pass rule (SUPERSEDED: a lower-scoring model passes, see § Review)

1. **Specificity is clearly better.** A paired bootstrap over the negatives (2,000 resamples, stratified by band,
   seed 20261009) gives the 95% interval of Δspec = spec(new) − spec(v1), weighted. **Its lower bound must be > 0.**
   The flip count at the op-point is reported beside it.
2. **Recall ≥ 0.70 on the 44 positives** (≥ 31 found), unweighted.

## Also reported (secondary, not gating)

- the specificity of both models on v1's own test split under the 2026-10-03 adjudication ruling (demoted rows =
  negatives; dropped rows excluded)
- the owner's 10 held-out rows (`owner_check_owner.tsv`) as a per-row table

## Review (2026-10-03 close, 4 lenses): pass rule REFUTED, the owner re-rules

- **BLOCKER: a lower-scoring model passes.**
  - v1's own production scores on the 44/238 rows:
    | v1 op-point | recall | weighted spec | unweighted spec |
    |---|---|---|---|
    | 4.0 (live) | 1.000 | 0.509 | 0.244 |
    | 5.8 | 32/44 = 0.727 | 0.887 | 0.689 |
  - At 5.8, Δspec is about +0.38 with recall above 0.70, so **both conditions hold for v1 against itself.**
  - v1's specificity is fixed by construction, like its recall.
  - **Fix candidate:** compare at matched recall. Set v1's threshold so its recall on the 44 equals the new
    model's, then require Δspec > 0.
- **The negatives are disputed.** 74 of the 89 hard negatives (Gemini-in, both judges out) fall in the classes the
  owner's v1 ruling refused to train on as negatives. Report them apart, or exclude them.
- **The weighting is blind to the hard cases.** 51% of the negative weight sits in `near`, where v1 is right by
  construction; hard negatives carry 6%. Stratify the bootstrap by band × pick, and report hi+mid and the
  hard-negative stratum unweighted.
- **Batch noise (#95) does not cancel.** It is per model. Score under 2 batch orders and require the pass under
  both. Report flips within ±0.16. The lowest positive's production raw is 4.079, so v1's recall is ≈ 1.0, not
  exactly 1.0.
- **One shot.** A second candidate needs a new held-out set. These positives come from the same Gemini + judge
  chain as the training positives, so recall here means agreement with that chain.
- **Weights:** the Gemini-outs/50 factor is computed by `heldout.py analyse` from `gemini_v2_2.jsonl`; it is not
  stored. `no_reply` counts as out.
- **No runner exists yet.** Condition on `stage_used`: a `stage1_low` row's raw is an e5 estimate.

## Pass rule v2 (owner, 2026-10-03 close): BINDING

**Deciding negatives:**
- every both-judges-out row **except** Gemini-in rows whose judge classes are disputed
- "disputed" means any class other than `out_one_moment`, on either pass: the classes the owner kept about half the
  time in the v1 ruling
- the disputed hard negatives are **reported separately and do not decide**

**Matched recall:**
- The new model says "in" at its own op-point, read from its `base_scorer.py` `TIER_THRESHOLDS` "medium".
- Let **k** be the number of the 44 positives it finds.
- v1's comparison threshold **t\*** is the HIGHEST threshold at which v1 still finds ≥ k of the 44.
- Both models are then compared on the deciding negatives: the new model at its op-point, v1 at t\*.

**Scoring:**
- Both packages run through `inference_hybrid.py` on b650 GPU, in **two row orders** (forward and reversed, at the
  package's default batch size).
- A row's "in" is read from `raw_weighted_average` only where `stage_used == "stage2"`. A `stage1_low` row is "out".

**Pass, under BOTH orders:**
1. Δspec = spec(new) − spec(v1 at t\*), weighted by the design (band scale × Gemini-out/50 for sampled outs).
   - Use a paired bootstrap stratified by **band × pick** (6 strata), 2,000 resamples, seed 20261009.
   - **The lower bound of the 95% interval must be > 0.**
2. **k ≥ 31 of 44.**

⚠️ At exactly 31/44 the Wilson interval is about [0.56, 0.82].

**Also reported (not deciding):**
- the flip count within ±0.16 of each threshold
- unweighted figures
- hi+mid only
- the disputed-negative stratum
- v1's test split under `treatment.jsonl`
- the owner's 10 rows

**One shot.** A second candidate needs a fresh held-out set.

**Before scoring:** the gate refuses any package whose training ids (written by the build) intersect these 295 rows.

## The runner (`gate.py`, written 2026-10-07, before any candidate exists)

Pass rule v2 as code; `tests/unit/test_belonging_gate.py` pins it (15 tests; 9 hand-made mutations of the rule each
turn a test red: stage1_low counted, disputed rows deciding, t\* lowest instead of highest, `≥ 0` instead of `> 0`,
k ≥ 30, no resampling, either-pass undisputed, splits kept, a 90% interval).

- `gate.py score --package … --order forward|reversed --out …` on b650 GPU; refuses without CUDA. It writes per-row
  `stage_used` + `weighted_average` with the package fingerprint, device, library versions, host and peak VRAM.
- `gate.py evaluate --candidate filters/belonging/vN` reads both orders for both packages. It refuses if a package
  changed since it was scored, or if the two were scored on different stacks. Exit 0 = PASS.
- `gate.py controls` runs the rule on v1's **production** raws. Required and observed, 2026-10-07:
  | control | k | Δspec 95% CI | verdict |
  |---|---|---|---|
  | v1 vs itself at 4.0 | 44 | [−0.050, −0.006] | FAIL ✓ |
  | v1 at 5.8 vs v1 (the refuted rule's pass) | 32 | [−0.010, +0.000] | FAIL ✓ |
  | a perfect candidate | 44 | [+0.425, +0.469] | PASS ✓ |
  | perfect on negatives, 30/44 found | 30 | [+0.068, +0.110] | FAIL ✓ (k) |

**The build's contract:** the candidate package must carry `training_ids.txt`, one training id per line. The gate
refuses a package without it, and any package whose ids touch the 1,200 held-out rows (a superset of the 295).

**Counts the rule produces** (labels 44 pos / 163 deciding neg / 75 disputed / 13 excluded): 14 of the 89 hard
negatives decide, because both passes say `out_one_moment`. ⚠️ § *Review* above says 74 disputed; the literal v2 rule
("any class other than `out_one_moment`, on EITHER pass") gives **75**. The extra rows have one pass
`out_one_moment` and one other (6 rows). The runner follows the rule text; the review's 74 could not be reproduced.

**Not computed by the runner** ("Also reported"): v1's test split under `treatment.jsonl` (plan phase 6,
`ground_truth_gate.py`), and the owner's 10 rows as a per-row table.

## v1 reference run (b650, 2026-10-07 06:22 UTC, `d3b4e4e`)

`gate.py score --package filters/belonging/v1`, both orders. RTX 5090, venv-prodparity (torch 2.11.0+cu130,
transformers 5.0.0, peft 0.18.1), 295/295 stage 2, 5 s per order, **peak VRAM 3,647 MiB** (the first measurement
`memory/b650-gpu.md` asked for). The files are in gitignored `datasets/belonging_gate/v1_{forward,reversed}.jsonl`,
on b650 and here; the v1 package fingerprint `bee0f4aafc6bd5d6` is identical on both machines.

**Harness check against production's own raws (`heldout_rows.jsonl` `raw`):**

| rows | n | median \|Δ\| | p95 | max | verdict flips at 4.0 |
|---|---|---|---|---|---|
| content < 4,000 chars | 162 | 0.0000 | 0.081 | 0.234 | 0 |
| content cut at 4,000 chars | 133 | 0.518 | 2.483 | **3.731** | **20** |

- **The cause is the draw's 4,000-char cut (`draw_heldout.py:63`) meeting belonging's head+tail input.** The model
  reads the first 256 and the LAST 256 tokens (`config.yaml` `preprocessing.head_tail`). For a cut article, the
  "tail" is text from around char 4,000, not the real ending. On uncut rows the harness reproduces production.
- **What it means for the gate:** the comparison is internally fair, because both models and both judges saw the
  same cut text. But for 133/295 rows the gate measures behaviour on text production never scores, and v1's
  verdict there already differs from production's on 20 rows. **Owner's call, not changed here:** accept the gate
  as "on the judged text", or re-fetch full content (NexusMind `filtered_*.jsonl`, the row's `file`) for those 133
  rows. The judges' labels were made on the cut text either way.
- ⚠️ **The same cut is in harvest r1** (`extract_hi.py`: "cut at 4,000 chars, as in the held-out run"). If the build
  trains on that text, the 237 positives' tails are not their real endings.
- **Order noise (#95):** forward vs reversed max |Δ| **0.453**, 2 rows above 0.16, 12 above 0.01; **0 verdict
  flips at 4.0.** The ±0.16 report under-covers this term, so the runner also prints order-to-order flips.
- v1 finds 44/44 positives at 4.0 in both orders (lowest 4.058; production 4.079).

**The cut is the cause, proven (2026-10-07, b650, same stack):** v1 scored on the FULL text of the 117 judged cut
rows still on sadalsuud reproduces production; on the cut text it does not.

| text | n | median \|Δ\| vs production | p95 | max | flips at 4.0 |
|---|---|---|---|---|---|
| full (recovered) | 117 | 0.0000 | 0.087 | 0.262 | **0** |
| cut at 4,000 (as judged) | 117 | 0.508 | 2.692 | 3.731 | **18** |

**Full text recovered and kept** (gitignored, `datasets/belonging_heldout/cut_rows_full_content.jsonl`, here and on
b650): 442 of the 1,200 draw's 509 cut rows. Every row starts with exactly the held-out text. The other 67 rows
(23 files, 2026-09-04..08) are already gone from sadalsuud, whose `filtered/belonging/` keeps ~28 days. Of the 295
judged rows, 117/133 cut rows are recovered and 16 are lost: 11 neg, 2 disputed, 2 excluded, 1 pos.
