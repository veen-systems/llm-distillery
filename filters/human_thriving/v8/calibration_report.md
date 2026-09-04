# human_thriving v8 — Calibration Report

Per-dimension isotonic regression (ADR-008), fit on the **658-row val split**, evaluated on
the **660-row test split** (untouched by training, by checkpoint selection, and by the fit).
Fitted **2026-09-04** on `b650-gpu`, **CPU**, `venv-prodparity`. `EXP-016`.
Model: epoch 4 of `EXP-015` (selected on `recall_medium` @ 4.5).

⛔ **This calibration does NOT improve held-out MAE, and that is not the reason to ship it.**
Read the two sections below before quoting any number here.

## The fit

**Val (the fit set) MAE 0.5805 → 0.5492 (+5.4%).** Expected, and not evidence: isotonic
regression is fit to minimise exactly this on exactly these rows.

| Dimension | val MAE before | val MAE after | Δ | **test** MAE before | **test** MAE after | Δ |
|---|---|---|---|---|---|---|
| human_wellbeing_impact | 0.5945 | 0.5687 | +0.0258 | 0.6169 | 0.6436 | **−0.0267** |
| social_cohesion_impact | 0.5255 | 0.4903 | +0.0352 | 0.5173 | 0.5329 | **−0.0156** |
| justice_rights_impact | 0.4351 | 0.3971 | +0.0380 | 0.4605 | 0.4619 | **−0.0014** |
| evidence_level | 0.6972 | 0.6769 | +0.0203 | 0.7245 | 0.7561 | **−0.0316** |
| benefit_distribution | 0.5955 | 0.5492 | +0.0463 | 0.6110 | 0.5956 | +0.0154 |
| change_durability | 0.6353 | 0.6128 | +0.0225 | 0.6872 | 0.6949 | **−0.0077** |
| **overall** | **0.5805** | **0.5492** | **+0.0313 (+5.4%)** | **0.6029** | **0.6142** | **−0.0113 (−1.9%)** |

**On the untouched test split the calibration makes MAE worse in 5 of 6 dimensions.**
For comparison, `nature_recovery v4`'s calibration improved *test* MAE by **+22.2%**. This
one does not generalise off its fit set.

⛔ **MAE is not the ranking criterion here (ADR-023) and is reported only because the
divergence between the two splits is the thing worth knowing.** Do not rank v8 against any
other filter on these numbers.

## What it does at the operating point — and what it does not

Both arms come from **one forward pass** (`scripts/analysis/dump_student_scores.py`), so the
#95 batch-composition term does not sit between them; they differ by calibration and by
nothing else. Judged with `scripts/gate/ground_truth_gate.py` at the inherited 4.5 bar
(n=660, 35 positives, 5.30%):

| arm | recall | recall band (#95) | specificity | spec band | precision |
|---|---|---|---|---|---|
| raw | 0.486 | [0.400, 0.514] | 0.9856 | [0.9792, 0.9888] | 0.654 |
| calibrated | 0.343 | [0.314, 0.400] | 0.9920 | [0.9872, 0.9952] | 0.706 |

⛔ **The bands OVERLAP on recall, specificity and F1 — the gate's own output says NOT
DISTINGUISHABLE, and the owner's 2026-08-06 rule says two models whose bands overlap are
not distinguishable whatever their point estimates say.** So the 14-point recall gap is not
reportable as an effect.

⚠️ **The recall overlap is a single shared endpoint**: `[0.400, 0.514]` and
`[0.314, 0.400]` meet at exactly 0.400 (14/35 both) and the gate's comparison is inclusive.
Specificity overlaps by 0.0016. **A noise floor slightly below 0.16 would flip this to
"distinguishable"**, so lean on the ranker comparison above, which is scale-free and does
not depend on the floor.

⭐ **And the scale-free comparison shows why: the two arms are the same model.**
(`docs/evidence/2026-09-04-v8-probe-calibration/arms_as_rankers.json`)

- raw-vs-calibrated **Spearman 0.9977**, only **1.95%** of sampled pairs discordant
- **AUC 0.9474 → 0.9488**; average precision **0.5474 → 0.5648**
- at **matched flag count** — flag the k highest-scoring rows in each arm, so both surface
  the same volume — every difference is **≤ 2 articles and inconsistent in sign**
  (k=17 +2, k=20 0, k=26 −1, k=30 0, k=35 −1, k=43 0, k=50 −1, k=60 +1)

⭐⭐ **The recall drop at a fixed 4.5 is a THRESHOLD effect, not a model effect.** Isotonic
regression compresses the top of the **weighted average**, so **4.5 on the calibrated scale
is a stricter operating point than 4.5 on the raw scale** — it flags 17 rows where raw flags
26 (raw tp 17 + fp 9; calibrated 12 + 5), a 34.6% cut in surfaced volume. Nothing was
learned and nothing was lost; the bar moved.

⚠️ **Per dimension it is not uniform** — on the **test** split 3 of 6 top ends *expand*
(`justice_rights_impact` 6.2 → 8.0, `evidence_level` 8.0 → 8.0) while
`benefit_distribution` compresses 6.2 → 5.7. The weighted average compresses because the
0.30-weighted `human_wellbeing_impact` does (7.9 → 6.8). Do not restate this as a
per-dimension rule.
⚠️ **Every range here is TEST** (`calibration.log`'s test block). `calibration.json` holds
the **val** fit, where `human_wellbeing_impact` reads `student_max 7.2188 →
calibrated_max 6.7879` — so a reader checking the JSON finds 7.2, not 7.9. Both are right
for their own split; name the split.

## The consequence Phase D must not inherit

⛔ **Do NOT carry 4.5 onto the calibrated scale as though it were the same operating point.**
It is v7's raw-scale number (#102, 2026-08-10) and v8 ships a different calibration on a
different corpus. ⚠️ `base_scorer.py`'s comment tells you to re-derive the op-point on v8's
own split; it does **not** yet say anything about the calibrated scale, which is this
paragraph's point. Indicative sweep on the test split (student bar swept, on-lens pinned at
oracle ≥ 4.5; source `docs/evidence/2026-09-04-v8-probe-calibration/threshold_sweep_test.json`):

| student bar | raw recall / spec | calibrated recall / spec |
|---|---|---|
| 4.00 | 0.629 / 0.9664 | 0.514 / 0.9760 |
| 4.25 | 0.571 / 0.9728 | 0.457 / 0.9840 |
| **4.50** | **0.486 / 0.9856** | **0.343 / 0.9920** |
| 4.75 | 0.371 / 0.9888 | 0.257 / 0.9968 |

⚠️ **Indicative only — this is not the Phase D gate.** It is one split, one device, and the
op-point decision needs the #95 band per candidate plus the positive rate, which the gate
prints and this table does not.

## Why it ships anyway

1. `CLAUDE.md` Hard Constraint: *"Fit `calibration.json` after every training run. Isotonic
   regression on the val set. Commit with the filter package."* ADR-008 is settled.
2. ADR-023's tie-break: ties inside the #95 band **go to specificity**, and the calibrated
   arm has the higher specificity point estimate at every bar swept.
3. It costs nothing in discrimination — AUC and AP are marginally *higher* calibrated.

⚠️ **It is NOT shipped because it improved aggregate MAE or aggregate recall.** It did not.

⭐ **CORRECTED 2026-09-04: it DOES improve the thing this filter exists to do.** Aggregate
recall pools the rows v8 exists to demote with the rows it exists to keep, so it could not see
the difference. Split them, on held-out data: of the **87** test rows `uplifting v7` surfaced
that the v8 oracle demotes, the calibrated arm removes **82 (94.3%)** against raw's **79
(90.8%)**; AUC on those 117 disputed rows is **0.8521 calibrated vs 0.8454 raw** (v7's own
score: 0.7218); and it demotes one of the two class-A rows the raw student still surfaces.
⚠️ Small margins on small n, and the #95 bands on aggregate recall/specificity still overlap —
this does not overturn "not distinguishable", it relocates where the difference lives.
`docs/evidence/2026-09-04-v8-probe-calibration/PHASE_C_REVIEW.md`.

## Provenance

- `calibration.json` — `n_samples: 658`, `sha256 23c40f41cffe…`
- `score_scale_factor` stays **1.0**. `fit_calibration.py` computed **1.3787** and would
  have written it into `config.yaml` as a side effect; suppressed with the new
  `--no-config-update`, because `score_scale_factor` is superseded by percentile
  normalization (ADR-014) and a factor ≠ 1.0 with no `normalization.json` silently stretches
  every score (`FILTER_PLAYBOOK` §8). ⚠️ The log prints `(10.0 / 7.25 …)`, which is **not an
  equation** — 10.0/7.25 = 1.3793; the real divisor is **7.2532**, and `7.25` is the
  script's own 2-decimal rendering. Proven suppressed: `sha256(config.yaml)` was identical
  immediately before and after the run (`d64c48aff329…`) and the file still reads
  `score_scale_factor: 1.0`. ⚠️ That hash no longer matches today — the `hybrid_inference`
  block landed later the same day — so verify the *value*, not the hash.
- Full evidence, logs and the reproduction script:
  `docs/evidence/2026-09-04-v8-probe-calibration/`
