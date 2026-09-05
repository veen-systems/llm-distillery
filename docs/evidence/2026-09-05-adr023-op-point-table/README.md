# The op-point table — what the operating point separates, and what it cannot

**2026-09-05. $0**, no oracle calls, no GPU. `EXP-024`. Arithmetic on per-row dumps that
already existed since `EXP-018`/`EXP-019`.

Raised by the owner while weighing a cheaper Stage 2: *"i wouldn't want to lose too much on
quality. Especially I do not want false positives."* That is ADR-023's criterion —
**specificity at the operating point** — and no artifact here had computed it **for a probe
arm** (`ground_truth_gate.py` and `phase_c_outcome.py` compute it for the student arms only).

⛔ **THIS DOCUMENT WAS WRONG IN FOUR PLACES BEFORE IT WAS FIRST COMMITTED**, and the
corrections are the useful part. A four-lens `/review-changes` run — after the mechanical
battery (registry check, both budget guards, doc-claims, 21/21 annotations, 667 tests) went
green and found **none** of them — established that:

1. **"AUC would have picked the wrong arm" was a coin flip published as an ordering.**
   Δ = **+0.0014**, 95% CI **[−0.0448, +0.0476]**, **P = 0.523**. Retracted; see §3.
2. **"The gate buys nothing — identical TP at all eight k" was FORCED.** The comparison
   could not have come out any other way below **k = 140**, and the grid stops at 60. The
   negative carried no information. See §4.
3. **The paired bootstrap was the wrong instrument** — frozen top-k masks, which emitted a
   **zero-width 95% CI** where two arms had no discordant rows. Replaced; see §2.
4. **Every figure was unweighted**, on a split drawn under a **25.1× design**. The weighted
   arm is now computed and it does not say the same thing. See §5.

⛔ **Read §6 before quoting anything here.**

Reproduce — ⚠️ **the dumps and labels are gitignored** (`.gitignore:76 datasets/*`; the
weights that produced the dumps are llm-distillery#97, the gitignore-the-model-weights
decision), so a fresh clone cannot run this without fetching them:

```bash
D=docs/evidence/2026-09-05-adr023-op-point-table
scp b650-gpu:'~/llm-distillery/ht_v8_test_dump/*.jsonl' /tmp/dump/
.venv/bin/python $D/adr023_op_point_table.py --dump-dir /tmp/dump \
    --labels datasets/training/human_thriving_v8/test.jsonl \
    --corpus datasets/scored/human_thriving_v8/corpus.jsonl \
    --out $D/adr023_op_point_table.json | tee $D/adr023_op_point_table.txt
```

⛔ **`.venv/bin/python`, not `python3`** — the system interpreter has no `sklearn`, and this
repo has previously mis-diagnosed that exact failure as "the environment".
⚠️ **Omitting `--corpus` silently drops the weighted arm** and every figure is then
unweighted; the script says so in its output rather than failing.

---

## 1. The control, and what it does not cover

The script recomputes all six arms' whole-split AUC and **aborts** unless each reproduces the
value published in `experiments/registry.jsonl` (EXP-018/EXP-019) and
`../2026-09-04-v8-probe-calibration/arms_as_rankers.json`. All six match at `d=0.0000`
(true max |Δ| **4.0e-5**, against `CONTROL_TOL = 5e-4`).

**Mutation-tested, not asserted**: perturbing a published AUC, `OP`, the dimension weights or
`GK_MIN` each makes it exit 1 and write **no** JSON. ⚠️ **`STAGE1_THRESHOLD` is outside its
reach** — 1.75 → 3.50 passes the control and writes a materially different §4. ⚠️ And AUC is
invariant to monotone rescaling, so the control says nothing about the **scale-dependent**
outputs: `flagged_at_op`, and everything in §4.

⚠️ It is a **reproduction** check, not an independent instrument: it re-reads the same dumps
that produced the published AUCs, so it cannot catch a defect shared with the EXP-018/019
computation.

## 2. Method

660-row `human_thriving v8` test split, **35 positives**, op-point 4.5.

Comparisons are at **matched flag count k** — flag the k highest-scoring rows in each arm, so
every arm surfaces the same volume and `FP = k − TP` identically. That is what makes a lost
true positive **also** a gained false positive here, and it removes the arms' very different
scales (§4). k=17 and k=26 are what `student_calibrated` and `student_raw` flag at the literal
4.5 bar.

The bootstrap **re-selects the top-k inside each replicate** (`reselect_ci`). ⛔ The first
version froze both masks on the full sample and resampled only row indices — a McNemar
discordant-pair interval on a *fixed* classifier, when top-k is sample-dependent. It reported
`student_raw` at k=30 and k=43 as **`[+0,+0]`**, a zero-width 95% interval, which is proof an
interval is not measuring sampling variability; and measured, **90.6%** of its replicates did
not surface k rows at all. A **null control** (an arm against itself) now runs every time and
must return exactly `[0,0]` — it does.

## 3. What the operating point separates

TP / specificity %, production-faithful scoring (student gated, probes not):

| arm | k=17 | k=26 | k=30 | k=43 | k=60 | AUC | AP |
|---|---|---|---|---|---|---|---|
| `student_calibrated` | **12** / 99.200 | 16 / 98.400 | 18 / 98.080 | 22 / 96.640 | 26 / 94.560 | 0.9488 | 0.5648 |
| `student_raw` | 10 / 98.880 | **17** / 98.560 | 18 / 98.080 | 22 / 96.640 | 25 / 94.400 | 0.9474 | 0.5474 |
| **`probe_reg_large`** | **12** / 99.200 | 16 / 98.400 | 18 / 98.080 | 21 / 96.480 | 21 / 93.760 | 0.9021 | 0.5209 |
| `probe_reg_small` | 6 / 98.240 | 12 / 97.760 | 12 / 97.120 | 15 / 95.520 | 21 / 93.760 | **0.9035** | 0.4055 |

Paired re-selection bootstrap, `student_calibrated TP − arm TP`, 10,000 resamples, seed 42:

| arm | k=17 | k=26 | k=35 | k=43 | k=60 |
|---|---|---|---|---|---|
| `probe_reg_large` | +0 `[−4,+4]` | +0 `[−4,+4]` | +0 `[−4,+5]` | +1 `[−4,+6]` | +5 `[−1,+9]` |
| `probe_reg_small` | +6 `[+1,+9]` ✱ | +4 `[+0,+11]` | +6 `[+1,+12]` ✱ | +7 `[+1,+12]` ✱ | +5 `[+0,+11]` |
| `probe_recall_small` (shipped) | +3 `[−2,+8]` | +6 `[+0,+11]` | +8 `[+2,+14]` ✱ | +7 `[+2,+14]` ✱ | +10 `[+3,+15]` ✱ |
| `student_raw` | +2 `[−3,+4]` | −1 `[−4,+2]` | −1 `[−3,+2]` | +0 `[−2,+2]` | +1 `[−2,+3]` |

✱ = 95% CI excludes zero. `probe_reg_large`'s CI includes zero at **all eight** k.

### ⛔ The AUC claim, retracted

The first version of this file said whole-split AUC "would have picked the wrong arm",
because `probe_reg_small` scores 0.9035 against `probe_reg_large`'s 0.9021. With its band:

| comparison | Δ | 95% CI | P |
|---|---|---|---|
| AUC, reg_small − reg_large | **+0.0014** | `[−0.0448, +0.0476]` | 0.523 |
| AP, reg_small − reg_large | **−0.1154** | `[−0.2587, +0.0210]` | 0.052 |
| AUC, student_cal − reg_large | **+0.0467** | `[+0.0108, +0.0863]` | 0.995 |

**AUC did not pick the wrong arm. AUC did not pick** — its band is ~30× the gap, and
CLAUDE.md's own rule applies: *two models whose bands overlap are NOT DISTINGUISHABLE
whatever their point estimates say*. ⚠️ **AP does not settle it either** at 95% (P = 0.052),
though it leans the right way; the earlier draft called AP "the metric that gets it right",
which is one hedge short.

⭐ **What survives, and it is narrower than what was claimed:** at k=17 the two regression
arms differ by **6 articles, CI `[+1,+9]`, excluding zero** — *the operating-point test
separates them where the whole-split ranking metrics cannot.* That is a real argument for
ADR-023's criterion.

⛔ **But it does not generalise into "AUC is the wrong metric".** The third row above is the
counter-example: **AUC separates the student from `probe_reg_large` (P = 0.995) where the
op-point test cannot** (CI includes zero at all eight k). Neither metric dominates; they have
power in different comparisons. Nothing here distinguishes *"the op-point is the right
criterion"* from *"the op-point test has ~8 discordant rows and no power"*, and §6.1 is the
honest reading.

⚠️ **"Six articles worse" is the k=17 figure.** At k=26 it is 4 (CI includes zero) and at
k=60 it is 0. Quote it with its k.

## 4. The gate: a forced comparison, and what stands anyway

⛔ **RETRACTED AS EVIDENCE.** Composed end to end, `B_gate_to_probe_reg_large` and
`C_probe_reg_large_alone` give identical TP at all eight k — but the highest
`probe_reg_large` score among the 64 screened rows is **1.4921**, while the k-th highest
score is **2.7787 even at k=60**. The smallest k at which a screened row could enter is
**140**. The equality was guaranteed before the data were read, with 1.29 score points of
margin. This is this repo's first working rule — *the instrument was pointed somewhere that
cannot produce a positive, so the negative carried no information* — and the script now
prints that k beside the verdict so the next reader cannot repeat it.

**What does stand, independently:** stage-1 at 1.75 routes **90.3%** onward (unweighted;
**89.35%** design-weighted — the figure `config.yaml` records) and screens out **0 of 35**
positives; and the cost arithmetic, which needs no data: a gate in front of a 16.417 ms stage 2
pays only while routing `r < (16.417 − 2.345)/16.417 = 85.7%`. At ~89–90% routing the gate
**costs** money. That is a sufficient argument for dropping it from a `→ e5-large` cascade;
the TP-equality never was.

⚠️ **Routing-rate conditional.** EXP-021's fleet-wide `stage1_low` rate is 35.16% (~64.8%
routed) — on the **paying** side of that break-even. Different filters and thresholds, so not
a contradiction, but the cost claim is about *this* filter at *this* threshold.

**The gatekeeper silently disappears in any probe-only architecture.**
`filters/human_thriving/v8/base_scorer.py` applies `evidence_level < 3.0 → cap the weighted
average at 3.0`; `filters/common/embedding_stage.py:243 _compute_weighted_avg` does not, and
`hybrid_scorer.py` publishes that ungated value for a `stage1_low` row. ✅ **Benign today, and
guarded** — `tests/unit/test_filter_package_consistency.py:131`
`test_stage1_threshold_stays_below_the_gatekeeper_cap` enforces `stage1 < 3.0`, so a screened
row's score cannot exceed the cap. ⚠️ **That guard is 0.04 from binding**: H-V8-20 names 52%
routing as the move if a Stage-2 cost constraint appears, which is a threshold of 2.960; at
48% routing it is 3.047 and the invariant breaks.

**Scale** — the arms are nowhere near a common scale, which is why a fixed 4.5 bar cannot
compare them:

| arm | median | max | flagged @4.5 |
|---|---|---|---|
| `student_calibrated` | 0.828 | 6.321 | 17 |
| `student_raw` | 0.816 | 5.838 | 26 |
| `probe_reg_large` | 0.747 | 6.707 | **14** |
| `probe_reg_small` | 0.667 | 7.948 | **5** |
| `probe_recall_small` (shipped) | 3.011 | 7.434 | **96** |
| `probe_recall_large` | 2.269 | 8.042 | 61 |

## 5. ⛔ Design weighting — the numbers above describe the sample, not the population

The v8 test split is a **design-weighted sample**.
`datasets/scored/human_thriving_v8/corpus.jsonl` carries `inclusion_probability` for **all
660** rows, spanning **25.1×** (HT weights 1.17–29.32) over 16 design cells. The previous
day's artifact on the *same rows*
(`../2026-09-04-v8-probe-calibration/scripts/gating_tradeoff.py:118`) used Horvitz–Thompson
weights deliberately. The first version of this one used none.

| quantity | unweighted | design-weighted |
|---|---|---|
| positive rate | **5.3030%** | **3.1638%** |
| stage-1 routing @1.75 | **90.3030%** | **89.3480%** |

Matched **weighted** surfaced share → weighted recall / weighted specificity:

| arm | 1.58% | 3.16% (≈ weighted positive rate) | 6.33% |
|---|---|---|---|
| `student_calibrated` | 0.329 / 0.99419 | **0.529** / 0.98394 | **0.733** / 0.95796 |
| `student_raw` | 0.354 / 0.99481 | 0.554 / 0.98489 | 0.708 / 0.95709 |
| `probe_reg_large` | 0.301 / 0.99197 | **0.478** / 0.98264 | **0.551** / 0.95178 |
| `probe_reg_small` | 0.152 / 0.98843 | 0.302 / 0.97702 | 0.551 / 0.95229 |

⭐ **Weighted, the student leads `probe_reg_large` at every share tested**, and by 0.18 of the
positive mass at the widest. The unweighted "not distinguishable" is a statement about the
*sample*. ⚠️ **No CIs on the weighted arm** — the point estimates are consistent in direction
(as are the unweighted ones, 8 of 8 non-negative), and that is all that is claimed.

## 6. ⛔ What this does NOT establish

1. **Not distinguishable ≠ equal, and underpowered is the live alternative.** 35 positives;
   CIs ±4–9 articles. `student_calibrated − probe_reg_large` is ≥ 0 at **8 of 8** k, strictly
   > 0 at **4 of 8**, and non-decreasing **from k=26 onward** (0, 0, 0, +1, +2, +5). ⚠️ An
   earlier draft said "6 of 8" and "monotonically"; both were wrong — 6 of 8 is the figure for
   `student_raw`, a different arm. Combined with §3's AUC row, the reading that the op-point
   test simply lacks power is not excluded by anything here.
2. **One seed.** `probe_reg_large` is seed 42, trained once. EXP-016 measured seed 7 moving
   stage-2 routing ~14 pp at the same threshold.
3. **No calibration.** It has no `calibration.json` and its own scale (14 flags at 4.5 against
   the student's 17). Adopting it re-runs phase 7 and re-derives the op-point.
4. **Test split only**, one filter. Not a production measurement. The #95 batch-composition
   band is not in these numbers — all arms come from one dump each, so composition is held
   fixed, not varied.
5. **Matched-k is not the op-point.** It is scale-free *because* it refuses each arm's own
   threshold; it answers "at equal surfaced volume, who surfaces more junk".
6. **The dumps' provenance is not checkable from this repo.** `probe_scores_reg_large.jsonl`
   is untracked, has no committed hash, and the committed
   `../2026-09-05-scorer-device-throughput/rescued_probes_manifest.txt` records
   `probe_e5large.pkl` (recall) and `probe_reg_large.pkl` (regression) **both** as
   `1024 6 mlp` — so the manifest cannot tell them apart. Confirmed off-repo only, via
   `b650-gpu:~/llm-distillery/logs/exp019_dump.log` and the rescued probe's own metadata.
7. **Duplicate ids would pass silently.** `load_scores` keeps the last row per id and the
   guard checks `len(ids) != 660` on the intersection, so a `>>`-instead-of-`>` rerun
   substitutes values with a green control.

## 7. What it changes

**Nothing ships on this, and it is weaker than the first draft claimed.** `probe_reg_large`
moves from *ruled out on cost* (EXP-018's actual ground: 11.1× to encode — not on AUC, as an
earlier draft said) to *a candidate the operating-point test cannot separate from the student
on this sample, and that the design-weighted point estimates do separate.* Settling it needs
a powered, multi-seed, calibrated, design-weighted evaluation.

The reason to want it is not today's compute — scoring is 53.5% of a 5.57% duty cycle
(EXP-021) — but the marginal cost of the **Nth** filter, where a shared encoder pass plus a
head (measured free: full e5-large probe 16.417 against encoder-only 16.514) beats a
per-filter student.

⚠️ Timings are `EXP-023`'s, on `b650-gpu`, batch 64, load excluded: e5-small **2.345**,
e5-large full probe **16.417**, student **24.740** ms/article. **Quote the ratio, not the
absolute** (H-V8-21): the same e5-small arm read 2.332 / 4.746 / 2.345 across three runs on
one box in one day, a 2.04× spread. At 4.746 the §4 break-even is 71.1%, still below routing.
