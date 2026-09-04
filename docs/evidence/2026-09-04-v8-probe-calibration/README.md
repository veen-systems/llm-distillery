# human_thriving v8 — Phase C, part 2: the Stage-1 probe and the calibration fit

**2026-09-04. `EXP-016`. $0 spend, no oracle calls.** Everything here ran on `b650-gpu`,
**CPU**, `venv-prodparity` (torch 2.11.0+cu130, transformers 5.0.0, sklearn 1.8.0).
⚠️ **"Production parity" names a HOST, and there is more than one candidate**
(`memory/b650-gpu.md`, corrected 2026-08-29): these are **gpu-server's** pins, not
sadalsuud's, which is what runs the pipeline. The two are different stacks, and the stack is
worth 3 verdict flips at 4.5. Phase 6b (probe) and phase 7 (calibration) of
`docs/RUNBOOK.md`.

⛔ **v8 still is not deployed and nothing in NexusMind was touched.** What changed is that
v8 can now *score*: before today it had weights and no calibration, no probe, no
`base_scorer.py`, no `inference.py`. Phase D (the ground-truth gate) has not run.

---

## What was missing, and now exists

| artifact | state before | state now |
|---|---|---|
| `base_scorer.py` | ⛔ absent — so `train_probe.py` could not even resolve MEDIUM | ✅ TIER_THRESHOLDS medium **4.5** (inherited from v7 #102, **not re-derived** — Phase D owes that) |
| `inference.py` | ⛔ absent — so `fit_calibration.py` had no scorer to load | ✅ `HumanThrivingScorer`, `use_prefilter=False` by default |
| `inference_hybrid.py` | ⛔ absent | ✅ `HumanThrivingHybridScorer`, **threshold read from `config.yaml`** |
| `probe/embedding_probe_e5small.pkl` | ⛔ absent | ✅ retrained, recall objective, **seeded** |
| `probe/…pkl.sha256` | ⛔ no filter in the repo has ever shipped one | ✅ shipped, and proven able to fail |
| `calibration.json` | ⛔ absent | ✅ per-dimension isotonic on the 658-row val split |
| `hybrid_inference:` in `config.yaml` | ⛔ deliberately absent | ✅ present **and live**, not documentation |

---

## Phase 6b — the probe

```
PYTHONPATH=. venv-prodparity/bin/python scripts/train_probe.py \
    --filter filters/human_thriving/v8 \
    --data-dir datasets/training/human_thriving_v8 \
    --embedding-model intfloat/multilingual-e5-small \
    --objective recall --target-fn 0.02 --device cpu --seed 42
```

`intfloat/multilingual-e5-small`, recall objective (class-weighted BCE on the weighted
average as a MEDIUM+ classifier). Early-stopped at **epoch 17**, best val BCE **0.9611**.
Train positives **250 / 5268 = 4.7%**, `pos_weight` 20.07; val positives **31 / 658**.

⛔ **ADR-023 does not apply to the probe.** For a recall-safe screen the false *negative*
is the expensive error, because a screened-out article can never surface no matter what
Stage 2 would have said. Hence `--objective recall`, and `FN@MEDIUM+` rather than probe MAE.

### The threshold is 1.75, and it is NOT the number the script selected

`train_probe.py --target-fn 0.02` selected **2.825**. That was not adopted.

The script's selection rule is *"the highest threshold whose val FN-rate ≤ target"* — a
**screening-savings** objective. The governing decision is different: the owner ruled on
**2026-08-28 (plan Phase 0, decision (e))** — ***hold near pass-through***: retrain the
probe but do **not** screen harder; re-derive the threshold only far enough to preserve
v7's ~**88.6%** Stage-2 routing. No Stage-2 cost constraint was claimed, so the FN risk
is not bought.

Measured with `scripts/analysis/probe_recall_report.py`, screening through the **real**
`filters/common/embedding_stage.EmbeddingStage` — the class production loads — not a
reimplementation of the weighted average:

| threshold | val stage-2 (wtd) | test stage-2 (wtd) | val FN | test FN |
|---|---|---|---|---|
| 1.00 (v7's deployed default) | 0.9877 | 0.9969 | 0/31 | 0/35 |
| **1.75 (adopted)** | **0.8876** | **0.8935** | **0/31** | **0/35** |
| 2.00 | 0.8216 | 0.8451 | 0/31 | **1**/35 |
| 2.825 (script's pick) | 0.5470 | 0.5210 | 0/31 | **1**/35 |

`wtd` = **Horvitz-Thompson**, weighting each row by `1/inclusion_probability` from
`corpus.jsonl`. The v8 corpus was drawn stratified (cell probabilities **0.0341–0.8571**,
class-A cells oversampled ~20×), so an **unweighted** split rate is a rate for the sample
and for no population the filter will ever meet. `train_probe.py` prints the unweighted
one; that is why this report exists.

⚠️ **The weighted numbers estimate the DRAWABLE population, not production.** The draw
excludes `news.google.com` — **22.1%** of production — plus everything else the draw's own
exclusions removed. v7's 88.6% was measured on production with v7's probe. The agreement
between 0.8876/0.8935 and 0.886 is reassuring; it is **not** a like-for-like comparison,
and no claim here should be read as "v8 routes exactly as v7 does in production".

⛔ **At 2.00 and above, the one test-split FN is a NON-LATIN positive** (1 of the 2
non-Latin positives on the test split). That is precisely the asymmetry ADR-018/019's
2026-08-21 amendment exists to prevent, appearing at the first threshold above the
adopted one. It is n=2 and therefore noise as a magnitude — but it is noise pointing the
way the ruling said to watch.

### FN@MEDIUM+ by script — and why this measurement has no power yet

The plan requires this split because, with the keyword prefilter dropped, the multilingual
probe is the **only** layer carrying multilingual selection: *"if it screens non-Latin
content harder than Latin, ruling 3 has been undone silently in a new place, and nothing
else in this plan would catch it."*

Pooling both splits at the adopted 1.75 (n=1,318):

| group | n | positives | FN | stage-2 routing (unweighted) | stage-2 routing (design-weighted) |
|---|---|---|---|---|---|
| Latin | 1,187 | 58 | **0** | 0.9090 | **0.8979** |
| non-Latin | 131 | 8 | **0** | 0.8397 | **0.8218** |

**The routing gap is real. Design-weighted (the primary figure): `0.0762` (7.62 pp),
Latin 0.8979 vs non-Latin 0.8218, pooled p = 0.8906, z = 2.65.** Unweighted, for
comparison: `0.0693` (6.93 pp), pooled p = 0.9021, SE 0.0274, z = 2.53. Reproduce with
`script_routing_gap.py` → `routing_gap.txt`.

⚠️ **Two honest caveats on that z.** (a) Both SEs are **binomial**, which is optimistic on a
stratified design; the measured Kish design effect is **1.068**, which moves the unweighted
z from 2.53 to **2.45**. (b) The first version of this test was **unweighted**, in a document
whose own thesis two sections above is that a sample rate describes no population — a
labelling defect found by review, not by me. Reweighting made the gap **larger**, so the
finding was never at risk; the reporting was. Σw is now recorded per group in the report
JSONs (`sum_weights*`) specifically so a weighted rate can be pooled across splits.
Per-split weighted gaps: **3.0 pp (val) and 11.0 pp (test)** — same sign, test larger.
Non-Latin content *is* screened harder. Per split the gap is 3.1 pp (val, z = 0.74, ns)
and 9.9 pp (test, z = 2.73, p ≈ 0.006) — consistent in sign, not in magnitude.

⛔ **But the FN half of the question is unanswered, and the zeros are why.** With **0 of 8**
non-Latin positives missed, the rule-of-three 95% upper bound on the non-Latin FN rate is
**0.375**. A non-Latin FN rate of thirty percent would have produced this exact table more
often than not. The Latin bound is 0.052 on 58 positives.

⭐ **So the honest reading is: routing asymmetry CONFIRMED at the screen; recall asymmetry
NOT MEASURED, and not measurable on 8 positives.** "0 FN in every language and script
cell" is true and nearly uninformative — the instrument could not have said otherwise.
Closing this needs non-Latin positives, which is what **llm-distillery#141** is about
(only **27** non-Latin uplifting positives with native ≥1,000 chars exist in the window).

⚠️ Per-language cells are worse. The largest non-English cell is **`es`** (val n=61 with 1
positive; test n=65 with 4); `de` is n=58 val with 2 positives and n=40 test with **0**.
They are in the JSON for completeness and must not be quoted as rates.

### Reproducibility: the probe was unseeded until today

`scripts/train_probe.py` set no seed — weight init and DataLoader shuffling were both free.
⚠️ **Inferred, not demonstrated:** no shipped probe was retrained to show it, and the eight
tracked probes are not established to have come from today's `train_probe.py`. What is
checkable is the code-absence half (no seeding anywhere in the file before this diff) plus
the seed-7 arm below, which shows how far two draws of the same recipe diverge. Added `--seed` (default 42), seeding `random` / `numpy` / `torch`, and recorded
in the pickle's own `metrics` as `seed`. Trained on **CPU deliberately**: CUDA reductions
are not deterministic under a seed (EXP-015 measured seed-42 Gemma runs at val MAE 0.5601
vs 0.5605), so a GPU-trained probe would carry a seed that does not deliver.

⚠️ **This does not retro-fix the six shipped probes** and it is not a reason to retrain
them — they are the artifacts that were gated and deployed. It fixes the next one.

**Proven, both directions** (`probe_rerun_seed42.log`, `probe_rerun_seed7.log`):

| run | val BCE | selected threshold |
|---|---|---|
| shipped, seed 42 | 0.9611 | 2.825 |
| **rerun, seed 42** | **0.9611** | **2.825** |
| rerun, seed 7 | 0.9209 | 2.550 |

All six weight tensors and the `StandardScaler` are **`np.array_equal` identical** between
the two seed-42 runs (`max|Δ| 0.000e+00`).

⛔ **But the PICKLE FILES are not byte-identical, and hashing is the wrong test.** The two
seed-42 files differ in **134 of 541,144 bytes**, all of them torch storage keys derived
from memory addresses (`94090181761856` vs `97139374751504`). A reproducibility check by
`sha256sum` would have reported "not reproducible" for a fully reproducible artifact — the
instrument would have been unable to say yes. Compare state_dicts, not hashes.

⚠️ **Provenance for that comparison, because it is the one claim here you cannot re-run from
this repo.** The comparand is `b650-gpu:/tmp/probe_seed42.pkl` (written 10:08) against the
shipped `filters/human_thriving/v8/probe/embedding_probe_e5small.pkl`; `/tmp` is ephemeral,
and the tensor-equality output was read from an interactive session rather than a log, so it
is **not reproduced by any committed artifact**. 541,144 bytes and the shipped hash are
checkable locally; the 134 and the `np.array_equal` result are not. To re-establish:
`ssh b650-gpu` and re-run `scripts/train_probe.py … --seed 42 --output /tmp/p.pkl`, then
compare `state_dict` tensors — not file hashes.

### ⛔⛔ THE KEEPER — the threshold belongs to the PROBE, not to the recipe

Seed 7's probe is a legitimate probe: same data, same objective, same code, **0 FN** at
1.75 on both splits, and a *better* val BCE. Screened at the **same configured 1.75**:

| probe | val stage-2 (wtd) | test stage-2 (wtd) | val FN | test FN |
|---|---|---|---|---|
| seed 42 (shipped) | **0.8876** | **0.8935** | 0/31 | 0/35 |
| seed 7 | **0.7406** | **0.7567** | 0/31 | 0/35 |

**A ~14 percentage-point collapse in Stage-2 routing from the seed alone** — the screened-out
share goes from 11.24% to 25.94% of the corpus, i.e. **+14.7 pp, which is +131% relative** —
while every recall number stays identical at 0. The probe's *score
scale* moves with the seed; its *ordering* does not.

⛔ **And Stage 1 is silent by design**: a screened-out article produces no output to
inspect, no log line, no score. There is no symptom. Retraining the probe and keeping 1.75
would have quietly tightened the screen by 14 points, in the layer that is now the only one
carrying multilingual selection.

✅ **Guarded, not just documented.** `config.yaml` records `probe_sha256` **beside the
threshold**, and `inference_hybrid.verify_probe_matches_threshold` refuses to construct the
scorer when the probe on disk does not match, with an error that names the re-derivation
procedure. ⚠️ **Deliberately a different pin from `probe/*.pkl.sha256`**: that companion
travels *with the probe* and a retrain regenerates it, so it can only catch corruption —
it cannot notice a valid-but-unpaired probe. This one travels *with the threshold*.
An explicit `threshold=` override skips the pin, because a sweep is exactly the act of
pointing a chosen threshold at a different probe.

Mutation-killed: replacing the verify call with `pass` fails
`test_unpaired_probe_refuses_to_construct`.

---

## Phase 7 — calibration

```
PYTHONPATH=. CUDA_VISIBLE_DEVICES= venv-prodparity/bin/python \
    scripts/calibration/fit_calibration.py \
    --filter filters/human_thriving/v8 \
    --data-dir datasets/training/human_thriving_v8 \
    --test-data datasets/training/human_thriving_v8/test.jsonl \
    --no-config-update
```

Per-dimension isotonic regression, student → oracle, fitted on the **658-row val split**
and evaluated on the **untouched 660-row test split**. Full numbers in
`filters/human_thriving/v8/calibration_report.md`.

### ⛔ It does not improve held-out MAE, and the op-point comparison is not distinguishable

| | val (the fit set) | **test (untouched)** |
|---|---|---|
| overall MAE | 0.5805 → 0.5492 (**+5.4%**) | 0.6029 → 0.6142 (**−1.9%**) |
| dimensions improved | 6 of 6 | **1 of 6** |

`nature_recovery v4`'s calibration improved *test* MAE by **+22.2%**. This one does not
generalise off its fit set. ⛔ MAE is not the ranking criterion (ADR-023); it is reported
because the divergence between the splits is the finding.

At the inherited 4.5 bar, both arms from **one forward pass** (so the #95
batch-composition term does not sit between them):

| arm | recall | recall band | specificity | spec band | precision |
|---|---|---|---|---|---|
| raw | 0.486 | [0.400, 0.514] | 0.9856 | [0.9792, 0.9888] | 0.654 |
| calibrated | 0.343 | [0.314, 0.400] | 0.9920 | [0.9872, 0.9952] | 0.706 |

The gate's own output: **recall, specificity and F1 bands all OVERLAP — NOT
DISTINGUISHABLE.** The 14-point recall gap is not reportable as an effect.

⭐ **CORRECTED 2026-09-04: "not distinguishable" was measured in the wrong place.** Aggregate
recall pools the rows v8 exists to demote with the rows it exists to keep, so it cannot see
the difference. Split them and the arms separate: on the 87 test rows v7 surfaced that the v8
oracle demotes, calibration removes **94.3%** against raw's **90.8%**, and AUC on the 117
disputed rows is **0.8521 vs 0.8454**. Small margins on small n, and this does NOT overturn
the band verdict — it relocates where the difference lives. `PHASE_C_REVIEW.md`.

⚠️ **Be precise about how thin two of those overlaps are.** On **recall** the bands
`[0.400, 0.514]` and `[0.314, 0.400]` touch at exactly **0.400** — 14 of 35 articles in
both — and the gate's test is inclusive, so the overlap is a **single shared endpoint**. On
specificity it is 0.0016 wide. Only F1 overlaps substantially. A noise floor a hair under
0.16 flips the recall headline to "distinguishable", so the verdict is correct at the
declared floor and is *not* robust to it. Only the ranker comparison below is.

⚠️ Note the raw arm reads **0.486** here where `EXP-015` reported **0.514** at 4.5 on the
same split. That is **one article** (17 vs 18 of 35), and 0.514 sits exactly at the top of
this run's band. The runs differ in **device** — EXP-015 on b650-CUDA (`device=cuda` in its
own dump), this one on CPU (`calibration.log`: `Device: cpu`) — which is measured.
⛔ **But naming CPU→CUDA as THE cause would be asserted, not measured**: the same dump was
never run on both devices, so no isolation exists, and EXP-015's own record documents a
competing explanation — seed 42 is not bit-reproducible on that box (val MAE 0.5601 vs
0.5605, identical code, data and seed). The 0.1956 figure is additionally a **max** over 660
rows (3 of which exceed 0.16), so invoking it as the mechanism for one unidentified row
overstates it. **Neither number is wrong; they are not the same measurement** — that is the
whole claim, and it needs no cause.

### ⭐⭐ The scale-free comparison: the two arms are the SAME MODEL

`compare_arms_as_rankers.py` → `arms_as_rankers.json`. Isotonic regression is monotone per
dimension, so a fixed-bar comparison can show a threshold shift as though it were a model
change. Asking the scale-free question instead:

- raw-vs-calibrated **Spearman 0.997688**; **1.95%** of sampled pairs discordant
- **AUC 0.9474 → 0.9488**; **AP 0.5474 → 0.5648** — calibration is marginally *better*
- at **matched flag count** (same surfaced volume, only ordering can differ) every
  difference is **≤2 articles and inconsistent in sign**: k=17 **+2**, 20 **0**, 26 **−1**,
  30 **0**, 35 **−1**, 43 **0**, 50 **−1**, 60 **+1**

⭐⭐ **So the recall drop at 4.5 is a THRESHOLD effect, not a model effect.** Calibration
compresses the top of the **weighted average**, so **4.5 calibrated is a stricter operating
point than 4.5 raw**: 17 rows flagged where raw flags 26, a **35% cut in surfaced volume**
(gate: raw tp 17 + fp 9 = 26; calibrated 12 + 5 = 17; 34.6%). Nothing was learned and
nothing was lost — the bar moved underneath the number.

⚠️ **Not every dimension compresses** — do not restate this as a per-dimension rule. On test,
`human_wellbeing_impact` goes 7.9 → 6.8 and `benefit_distribution` 6.2 → 5.7, but
`justice_rights_impact` **expands** 6.2 → 8.0 and `evidence_level` holds at 8.0. The
weighted average compresses because the heaviest dimension (0.30) does.
⚠️ **Those are TEST-split ranges.** `calibration.json` holds the **val** fit, where
`human_wellbeing_impact` reads 7.2188 → 6.7879. Name the split or the JSON looks wrong.

⛔ **Phase D must therefore re-derive the op-point on the CALIBRATED scale.** Carrying v7's
4.5 across is not "keeping the operating point"; it is silently tightening it. Indicative
sweep (test split, on-lens pinned at oracle ≥ 4.5, **not** the Phase D gate):

| student bar | raw recall / spec | calibrated recall / spec |
|---|---|---|
| 4.00 | 0.629 / 0.9664 | 0.514 / 0.9760 |
| 4.25 | 0.571 / 0.9728 | 0.457 / 0.9840 |
| **4.50** | **0.486 / 0.9856** | **0.343 / 0.9920** |
| 4.75 | 0.371 / 0.9888 | 0.257 / 0.9968 |

### It ships anyway, and not because it helped

ADR-008 and `CLAUDE.md`'s Hard Constraint require a fitted `calibration.json` per training
run; ADR-023's tie-break sends ties inside the #95 band to **specificity**, which the
calibrated arm wins at every bar; and it costs nothing in discrimination. ⚠️ **It is not
shipped because it improved anything measurable. It did not.**

### ⛔ `fit_calibration.py` would have shipped a 1.3787× score stretch

The script's default behaviour is to compute `10.0 / weighted_max` from the calibrated
maxima and **edit `config.yaml`** as a side effect. On this run it computed

```
score_scale_factor: 1.3787  (10.0 / 7.25 theoretical max from calibration)
```

⚠️ **That line is not an equation**: 10.0 / 7.25 = 1.3793. The real divisor is **7.2532**
(10.0 / 7.2532 = 1.3787); `7.25` is `fit_calibration.py`'s own `{weighted_max:.2f}`
rendering. Quote the factor, not the division.

`score_scale_factor` is **superseded by percentile normalization (ADR-014)**, and a filter
that ships a factor ≠ 1.0 with **no `normalization.json`** — which v8 is, until Phase E —
silently stretches every score and defeats the gatekeeper design (`FILTER_PLAYBOOK` §8).
The v8 plan says so explicitly: *"Ship `score_scale_factor: 1.0`."*

Added `--no-config-update` and used it. **Proven on this run, not argued:**
`sha256(config.yaml)` was `d64c48aff329…` immediately before and immediately after the
09:51 fit. ⚠️ **That hash no longer verifies** — the `hybrid_inference` block was added at
10:14, so the file now hashes `1697bd2ee015…`. The durable half is that `config.yaml` still
reads `score_scale_factor: 1.0` against the computed 1.3787, and `calibration.log` carries
the suppression line. The write path is untouched for every other caller — verified
separately by calling `_update_score_scale_factor` on a copy, which produced
`score_scale_factor: 1.3787  # 10.0 / 7.25 (calibrated max)` (the script's own 2-decimal
rendering; see the arithmetic note above).

⚠️ **This is not a v8 problem, it is a script default.** Any filter fitted before its
normalization gets the same edit. Not changed globally here: flipping a default is a
behaviour change for five other packages and belongs in its own decision.

### Device: CPU, on purpose

Fitted on **CPU** so that calibration and the Phase D gate share a device. The plan
mandates the gate run *"on CPU with `venv-prodparity`, or on gpu-server — never on b650's
GPU"*, because b650-GPU flips **3 verdicts at 4.5**, this filter's op-point.

⚠️ **Production serves on GPU**, so the shipped calibration carries the documented
**CPU→CUDA 0.1956** max-|Δ| term (`memory/score-batch-shape-noise.md`). That is a real,
named exposure, not an oversight: the alternative — fitting on b650-CUDA — adds a
**CUDA-to-CUDA-across-hosts term that has never been measured**. (Not "cross-box": that
label was retired 2026-08-29 because the host term measured **0.0000**, 660/660
bit-identical — with the device held at CPU.) Between a measured 0.1956 and an
unmeasured unknown, the measured one is the one to carry.

---

## The Stage-1 threshold is the first one in this repo that is not inert

Every other `inference_hybrid.py` carries a module-level `DEFAULT_THRESHOLD`, and nothing
passes `config.yaml`'s `hybrid_inference.stage1.threshold` into the constructor (verified
2026-08-21: no consumer in `filters/common/` or NexusMind's `filter_loader` /
`production_scorer`), so editing the config alone does nothing — a key that reads as an
enforcement point and enforces nothing, the 17th occurrence's twin.

⚠️ **The value is not uniform, and it is not harmless.** Measured over the 13 other packages
on 2026-09-04 (`grep -h '^DEFAULT_THRESHOLD' filters/*/v*/inference_hybrid.py`): **0.75**
(nature_recovery v1/v2/v4), **1.00** (belonging v1, uplifting v7), **1.225** (solutions
v5/v6), **1.25** (cultural_discovery v4/v5), **1.50** (investment_risk v6), **2.25**
(uplifting v6, thriving v1), **2.50** (cultural_discovery v6). Only **2 of 13** are 1.00.
⛔ And config-vs-code agrees on only nine of eleven: **`nature_recovery v4` ships
`threshold: 3.225` against a runtime 0.75** — literally the 3.225-vs-0.75 divergence this
paragraph names, live right now — and `thriving v1` ships `threshold: null` against 2.25.

v8 reads the config and **raises** when the key is missing, so the number lives in exactly
one place. `tests/unit/test_human_thriving_v8_stage1_threshold.py` proves the outcome
rather than the predicate, in three directions:

1. **present and different** — mutate the config to 0.25 / 1.75 / 3.5, assert the value
   reaching `EmbeddingStage` follows. **Mutation-killed**: hardcoding `self._threshold = 1.00`
   in `inference_hybrid.py` fails all three cases.
2. **present but malformed** — a missing block, a missing `threshold`, a missing file all
   raise rather than defaulting to a number nobody chose.
3. **mentioned but ABSENT** — asserts the module defines no `DEFAULT_THRESHOLD`, so a
   second copy of the number cannot creep back.

Deliberately **not** asserted: that the threshold equals 1.75. Pinning it would recreate
the second copy the file exists to prevent. The test bounds it to `(0, op_point)` instead;
the value's provenance is the config comment and this directory.

## The probe integrity check was dormant everywhere

`EmbeddingStage._load_probe` calls `_verify_pickle_integrity`, which compares against a
companion `.pkl.sha256` **if one exists** and otherwise only `logger.debug`s. `git ls-files`
finds **zero** such files: the check has been present, correct, reachable — and unable to
fail — since it was written. v8 ships one, and
`tests/unit/test_human_thriving_v8_probe_artifact.py` proves both halves separately,
because a passing integrity check also passes when the check is off:

- the shipped hash matches, and the probe loads through the real `EmbeddingStage`
- a **mismatched** `.sha256` raises `ValueError: … integrity check failed`
- an **absent** one still loads — documenting the dormant default rather than asserting it
  is good, since making it strict would break every other probe package

---

## Files

| file | what it is |
|---|---|
| `probe_recall_report_val.json` | full curve + per-group table, val split (n=658, 31 positives) |
| `probe_recall_report_test.json` | same, test split (n=660, 35 positives) — untouched by probe training and by threshold selection |
| `probe_recall_report_{val,test}_seed7.json` | the seed-7 probe at the same 1.75 — the routing-collapse control |
| `probe_rerun_seed42.log`, `probe_rerun_seed7.log` | the two reproducibility reruns |
| `calibration_arms_gate.json` | `ground_truth_gate.py` on both arms at 4.5, with the #95 bands |
| `threshold_sweep_test.json` | the 4.00/4.25/4.50/4.75 sweep, both arms — added after review found three of its four rows had no committed source |
| `arms_as_rankers.json` | the scale-free comparison: Spearman, discordance, AUC, AP, recall at matched flag count |
| `compare_arms_as_rankers.py` | the script that produced it — committed so the numbers above are reproducible |
| `script_routing_gap.py`, `routing_gap.txt` | the Latin/non-Latin routing test and the rule-of-three bounds |
| `PREDEPLOY_PARITY.md` | ⭐ **v8's scorer compared part-by-part against the five deployed packages** — what is missing, what is deliberate, and the two invariants it found unguarded |
| `PHASE_C_REVIEW.md` | ⭐ **the review of this whole phase** — what worked, the void fleet comparison, and the Phase 8 trade-off table |
| `phase_c_outcome.py`, `.json`, `.txt` | the analysis behind it, committed so every number reproduces |
| `probe_training.log` | `train_probe.py` output, seed 42 |
| `calibration.log` | `fit_calibration.py` output, including the suppressed 1.3787 |
| `probe_recall_report_test.json` | ⚠️ nearly lost: `.gitignore`'s `*_test.*` scratch rule matched it and `git add` omitted it silently. A `docs/evidence/**` negation was added; see `.gitignore`'s tail |

The per-row score arms (`scores_raw.jsonl`, `scores_calibrated.jsonl`, `raw_logits.jsonl`,
660 rows each) are **not committed** — they carry article ids for corpus rows whose text is
gitignored (#97). They live on `b650-gpu:~/llm-distillery/ht_v8_test_dump/`. `raw_logits.jsonl`
is kept there specifically so the 16-minute CPU pass never has to be repeated.

## What is still owed before Phase D

- **Re-derive the 4.5 op-point on v8's own held-out oracle split.** It is inherited from
  v7 (#102) and v8's score distribution is not v7's.
- **Re-derive Gate B-A's `k`** — the 2026-09-03 finding that a k=3 mean on a bimodal row
  is a sample of a coin flip (`INDETERMINATE, need k≈82` on that run).
- **Decide the traceability exception** — the weights were produced by a tree that `git
  commit --amend` orphaned (`0697f5a`, tagged `exp-015-training-code`). A retrain makes a
  *different* artifact, so this is a decision, not a cleanup. See `STATUS.md`.
- **Non-Latin positives** for the FN half of the multilingual question (#141).
