---
name: score-batch-shape-noise
description: A student score is not a function of the article alone — batch composition moves it up to 0.16, flipping 7-9% of near-boundary surfacing decisions (#95); cycles are replayable since 2026-08-03 but scores are not stable. FOUR noise populations now, and the fourth is not a floor at all: human_thriving v8's scope gate is a STEP FUNCTION (13% of identical re-runs flip a binary verdict worth a median 3.75, while gate-stable rows move 0.100) — so 1/sqrt(k) averaging does not touch it and "noise floor" language misleads
metadata:
  type: project
---

# Batch-Shape Score Noise (#95)

**Date:** 2026-08-03. Found while smoke-testing #93 on gpu-server; **not caused
by #93** — measured with every #93 code path inert.

## The finding

Same article, same model, same weights, same box, same process. Only
`batch_size` differs. Scores move.

| filter | op-point | corpus | in ±0.30 band | flipped tier/op-point | share of band | share of corpus |
|---|---|---|---|---|---|---|
| solutions v6 | 2.252 | 2,814 | 28 | 2 | **7.1%** | 0.07% |
| uplifting v7 | 4.0 | 950 | 33 | 3 | **9.1%** | 0.32% |

```
solutions [3]  bs1=2.1745(low)  bs4=2.3398(medium)  bs8=2.3080(medium)  bs16=2.1745(low)
uplifting [9]  bs1=4.0390(medium)  bs4=3.9193(low)  bs8=3.9012(low)  bs16=4.0390(medium)
```

Magnitude over 120 articles: **max |Δ| 0.162, mean |Δ| 0.004**, ~40% of articles
affected at all. Consistent with GPU kernel reduction order varying with the
batch dimension. `score_article` vs `score_batch` disagree the same way and by
the same amounts — the API difference is incidental, the batch *shape* is the
cause.
<!-- verify: test -f scripts/diagnostics/measure_batch_shape_flips.py && echo PASS || echo FAIL -->

## What follows, and what does not

- **Aggregates are safe.** Mean 0.004 washes out at n=60. #92's DiD, MAE
  figures and calibration fits are unaffected.
- **Threshold tests are not.** Under ADR-022 visibility is `raw >= op-point`,
  so a flip is a *surfacing* flip. Tier, op-point and any per-article
  before/after comparison inherit a noise floor of **0.16** worst case (the
  measured max is 0.162 — do not round it up to 0.17, as an earlier draft of
  this file and its description did).

## What shipped 2026-08-03 evening

- **Seeded per-run shuffle** (NexusMind `f7fef85`, deployed). The variable was
  never batch *size* — `DEFAULT_BATCH_SIZE = 16` is fixed and never varies in
  production. It was batch *composition*, from an unseeded
  `random.shuffle(articles)` in NexusMind's `scripts/main.py`. Now seeded per (run, filter),
  logged in the start banner, replayable via `NEXUSMIND_RUN_SEED`.
  **This is replay, not stability** — the next cycle reshuffles and the article
  moves again. Do not cite it as a fix for #95.
- **Noise floor recorded** (LD `efab69d`) in `docs/FILTER_PLAYBOOK.md` §7, the
  `ground_truth_gate.py` docstring, and CLAUDE.md's hard constraints.

## The owner decision, 2026-08-06 (#95 step 2)

**Budget for the floor; do not try to remove it.** Options put to the owner were
(a) declare a noise margin, (b) test the fixed-length-padding hypothesis first,
(c) both. Chosen: **(a), no experiment.** The padding test stays unrun.

Note the option that was *not* available: "pin a batch size in production."
`DEFAULT_BATCH_SIZE = 16` (`filters/common/filter_base_scorer.py:50`) is already
fixed and never varies in production — the variable is batch *composition*, which
is what the seeding addressed. #95's own "suggested next steps" text offered
pinning as a live option; it was not one.

**The rule, as shipped:** an article predicted within **0.16** of the surfacing
threshold is *indeterminate* — the batch decided it, not the model. Every metric
computed at that threshold carries a band, and **two models whose bands overlap
are NOT DISTINGUISHABLE**. Binds the ground-truth gate, FN-deltas, op-point
re-derivations (#87) and short-content cap measurements (#93 step 4).

`scripts/gate/ground_truth_gate.py` computes it (`--noise-floor`, default 0.16;
`0` reproduces pre-2026-08-06 runs). Worked example — `solutions v6` on its own
held-out test set, 19 of 1,032 indeterminate:

```
F1     0.739 [0.712, 0.771]
recall 0.671 [0.659, 0.707]
prec   0.824 [0.775, 0.849]
```

A candidate landing anywhere inside that band has not beaten v6.
<!-- verify: grep -q "NOT DISTINGUISHABLE" scripts/gate/ground_truth_gate.py && echo PASS || echo FAIL -->

**Still open:** whether scores can be made a function of the article alone.
Untested hypothesis — if batches pad to the longest article *in the batch*, an
article's computation depends on its batch-mates, and fixed-length padding
would remove the dependence. Falsifiable in a few hours on GPU; deferred until
something needs batch-invariant scores.
- **The #92 second-op-point re-run is directly exposed** — it selects on
  "clears the op-point" and re-selects at another op-point, which is exactly
  the movement measured here. Pin `batch_size` for that test, or treat the
  boundary as fuzzy to ±0.08.

## Does it change a decision? Yes — measured 2026-08-03

The first pass (120 articles) found 0 tier flips **and 0 articles within 0.05 of
the op-point**, so it could not have found one. Re-run against the band where a
flip is possible (`scripts/diagnostics/measure_batch_shape_flips.py`):

| filter | op-point | in ±0.30 band | flipped | share of band | share of corpus |
|---|---|---|---|---|---|
| solutions v6 | 2.252 | 28 | 2 | **7.1%** | 0.07% |
| uplifting v7 | 4.0 | 33 | 3 | **9.1%** | 0.32% |

```
solutions [3]  bs1=2.1745(low)  bs4=2.3398(medium)  bs8=2.3080(medium)  bs16=2.1745(low)
uplifting [9]  bs1=4.0390(medium)  bs4=3.9193(low)   bs8=3.9012(low)     bs16=4.0390(medium)
```

Flips occur within 0.077 (solutions) / 0.039 (uplifting) of the op-point.

## Not measured

Whether the *same* batch_size with different batch *membership* (which is what
production actually varies, cycle to cycle) produces the same effect. Almost
certainly yes — membership changes the shape the same way — but it is inferred,
not measured. The production-relevant number is therefore an estimate.

## Distinguish from its two cousins

- **Training-time CUDA nondeterminism** (gotcha 2026-07-09): same seed, fresh
  re-train, different *weights*. This one is fixed weights at inference.
- **Stack / device skew — NOT "cross-box"; the name was wrong for 26 days and is
  corrected here 2026-08-29.** Originally recorded as |0.16| between gpu-server
  and b650 (gotcha 2026-07-30) from a sentence-transformers version difference —
  which is already the tell: *a version difference is not a machine*.
  ⛔ **The host term is exactly 0.0000.** `docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md`
  ran four runs on the same 660-row split changing one variable at a time:
  **P→C (host isolated, device + stack held) is 660/660 bit-identical**, across two
  different physical machines with different CPUs and different python patch levels.
  The two real terms are the **library stack** (max |Δ| **0.2008**, 3 flips at 4.5)
  and the **device, CPU→CUDA** (max |Δ| **0.1956**, 1 flip at 4.0, 3 at 4.5) — so
  *"same magnitude as 0.16"* was wrong as well: both exceed it.
  ⚠️ Everything below was measured 2026-08-09 with the **stack unmatched**, so read
  it as the stack term, not a box term.
  **NOW MEASURED FOR THE GEMMA STUDENT TOO (2026-08-09 night)**, and it is the
  same order as this floor rather than smaller: uplifting v7's 660 held-out rows,
  b650 vs gpu-server's serving venv, model weights + all filter/`common/` code +
  split md5-identical, CPU both sides — **max calibrated |Δ| 0.2008, i.e. ABOVE
  the 0.16 floor**, p99 0.1198, p90 0.0345, p50 0.0000, only 2.3% of rows
  bit-identical, signed mean +0.00018 (noise, not a shift). **Decision impact is
  threshold-dependent: 0 verdict flips at the 4.0 op-point (identical confusion
  matrix — ⚠️ **but 4.0 has not been the op-point since 2026-08-11, #102**, so that
  reassurance no longer describes the deployed cut) and 3 flips at 4.5,
  splitting specificity 0.9730 vs 0.9662.** So the two noise sources *stack*, and
  **a box is cleared at a threshold, never in general**. The e5 probe's clean
  4.2e-6 result does NOT transfer to the student. Beware the p50 of exactly
  0.0000 — raw logits are bf16-quantised (~0.03 steps), so most disagreements are
  hidden, not absent. Harness: `scripts/verification/box_parity.py` +
  `diff_box_parity.py`; record:
  `docs/evidence/2026-08-09-cross-box-parity-uplifting-v7.md`.
  ⛔ *That last line read "still unmeasured for the student: CPU vs CUDA" until
  2026-08-29. It was measured the NEXT DAY at **0.1956**, 1 flip at 4.0 and 3 at
  4.5 — see the correction block above.*

## A THIRD cousin, and it is 4× larger: ORACLE run-to-run noise (measured 2026-08-12)

**This file's 0.16 is a STUDENT number. It says nothing about the oracle, and it
had been reached for as if it did.** Measured for the first time on 2026-08-12 in
#109 arm A, by scoring the same articles twice with Gemini Flash 2.5 at
temperature 0.3 — same prompt, same code path, same machine, nothing varying but
the sampling:

| population | n | mean \|Δ\| | max |
|---|---|---|---|
| `cultural_discovery v5`, all bands | 40 | **0.4356** | 2.10 |
| — off-lens (gate-refused) rows | 20 | 0.2375 | — |
| — on-lens (gate-passed) rows | 20 | 0.6338 | — |
| **at and above the op-point (stored ≥ 4.0)** | 40 | **0.6869** | **3.40** |

Four things follow, and the last one is the expensive one:

1. **Never quote 0.16 for an oracle comparison.** The oracle floor is 2.7×–4.3×
   larger depending on where you measure it. They are different mechanisms: 0.16
   is batch composition at fixed weights; this is decoder sampling.
2. **It is population-dependent, so it must be re-measured per band.** Off-lens
   rows return zeros from both runs and agree almost trivially (0.238); on-lens
   rows carry live dimensional judgement (0.634). Inheriting a corpus-wide ν for
   an op-point question understates the floor by ~1.6×.
3. **At the op-point the floor EXCEEDED the effect it was meant to adjudicate**
   (0.687 vs a between-arm difference of 0.396). A single-shot cross-oracle
   comparison there is unfalsifiable *at any sample size* — the floor is
   per-article and does not shrink with `n`. More articles buy nothing.
4. **The fix is repeated draws, not more rows.** Averaging `k` scores per article
   scales σ by `1/√k`: at `k = 4` the comparable floor falls to ≈0.34, under the
   0.396 observed. Arithmetic, not measurement — it assumes per-article normality
   that 40 pairs cannot establish.

Consequence for the same-day trap this file exists to prevent: **the wrong
instrument now has FOUR sizes, and picking by magnitude is not a method.** Ask
what varied — batch composition (0.16), the **library stack** (0.2008), the
**device** CPU→CUDA (0.1956), or the oracle's decoder (0.44–0.69) — and measure the
one that varied in *your* comparison. ⛔ **"The machine" is not on that list**: with
pins and device matched, two machines are bit-identical.

### ⚠️ What `k=3` actually leaves — first measured 2026-08-31, n=6 pairs

Item 4 above is **arithmetic**. The first direct look at the residual came from re-scoring the
`human_thriving v8` no-regression rows on a second day, which is a paired design nobody set out
to run: two rows × three prompt arms were scored k=3 on **2026-08-29** and k=3 again on
**2026-08-31**, with judge (`deepseek-chat`), prompt file **and its sha256**, article text,
weights and op-point all held fixed.

| | |
|---|---|
| pairs | **6** (2 rows × 3 arms) — small, and the interval is not reportable at that n |
| movement of the **k=3 mean** | +0.200, −0.067, **+0.484**, +0.383, −0.233, −0.050 |
| max | **0.484** — *above* the 0.436 single-draw mean floor, below the 0.687 op-point-band one |

⛔ **`k=3` averages the decoder; it does not pin it.** ⚠️ **The comparison is NOT like-for-like
and must not be quoted as one**: 0.484 is a **max over 6 pairs**, 0.436 is a **mean |Δ|** over 40
single-draw pairs — different sets, different quantities, and a max is expected above a mean
even with the spread unchanged — so this does **not** refute `1/√k`,
and `ν/√3 ≈ 0.25` is quoted for scale only. The claim that survives is narrow and sufficient:
**a k=3 mean can move about half a point between days.** Small n, a population difference
(`uplifting`-prompt rows, not the `cultural_discovery v5` ones 0.436 was measured on) and a
server-side model change — **`deepseek-chat` is a moving pointer, not a pinned version** — are
**not separable from six pairs**.

**Consequence, and it is the usable part:** do not read a **≤0.5 movement of a k=3 oracle mean**
on this population as an effect. Every k=3 verdict in the v8 gate is unchanged across the two
days; the three-digit numbers are not. Record: `docs/evidence/2026-08-31-v8-no-regression-gate/`
§3.

Records: `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md` (ν = 0.436) and
`docs/evidence/2026-08-12-cd-v5-op-point-band-followup.md` (ν₄ = 0.687).
Harness: `scripts/research/cd_v5_arm_a_sample.py --noise-pairs` emits the
duplicate control; `cd_v5_arm_a_analyze.py --noise-scored` measures it.

## A FOURTH, and it is NOT A FLOOR — it is a step function (`human_thriving v8`, 2026-08-28)

⛔ **Do not add this to the list above and pick by magnitude. It is a different SHAPE, and
a mean \|Δ\| describes it wrongly.** Measured on the real call site with DeepSeek at
temperature 0.3, same prompt, same 30 articles, second run — the null arm of the prompt-order
probe (`docs/evidence/2026-08-28-v8-prompt-order-probe/`):

| | value |
|---|---|
| rows crossing the 4.5 op-point between identical runs | **5 / 30 (17%)** |
| rows where the scope gate (all six dimensions ≤ 2) flips | **4 / 30 (13%)** |
| median \|Δ\| on **gate-stable** rows | **0.100** — *inside this file's 0.16* |
| median \|Δ\| on **gate-flipped** rows | **3.750** |
| of the 5 rows moving \|Δ\| > 1.0, gate flips | **4** |
| of the 25 rows moving \|Δ\| ≤ 1.0, gate flips | **0** |

**Mechanism.** The v8 prompt's `scope_verdict` is a binary whose consequence is *"ALL six
dimensions 0–2"*. So the variance is not decoder jitter smeared over a dimension vector — it
is one latent coin flip, amplified into a ~3.75 jump. The distribution is **bimodal**: on the
87% of rows where the verdict is stable this prompt is *better* than the batch floor
(0.100 < 0.16), and on the other 13% nothing in the 0.44–0.69 range describes it.

Four consequences:

1. **A mean or an SD is the wrong summary.** The whole-cohort SD is 1.44 and no row behaves
   like 1.44. Report the mixture: P(flip) and the conditional medians.
2. **`k = 4` averaging does NOT fix it the way cousin 3 says.** That arithmetic assumes
   per-article normality; this is a Bernoulli on a binary verdict. What helps is a **majority
   vote on `scope_verdict` itself**, not a mean over dimensions — untested.
3. **It is a property of the PROMPT, not of the oracle.** Steps 1 + 2b introduced the gate;
   `uplifting v7` has no such construct. So it cannot be inherited across prompts, in either
   direction. ⚠️ **Gate A did not see it — it ran k=3 and averaged over exactly this.**
4. **A k=1 v8 re-score labels ~13% of rows by a toss** — ~860 of 6,590, concentrated at the
   boundary, which under ADR-023 is where the expensive error lives.

⭐ **The general lesson, which is why this sits in this file at all: a "noise floor" presumes
the error is additive and roughly symmetric. When a prompt contains a hard gate, that
presumption fails and the floor language actively misleads** — it invites `1/√k` reasoning
against a mechanism `1/√k` does not touch. **Ask what varied AND what shape it varies in.**

⚠️ n = 30, k = 2, one cohort, one prompt. The 13% is a point estimate with a wide interval;
it is enough to change the re-score design and not enough to quote as a rate.

## A FIFTH candidate term, unisolated: the PROGRAM (dtype / loader / batch), 2026-09-06

⛔ **Not a floor, and not yet a term — a candidate with two rivals excluded.** `EXP-026`
found `human_thriving v8`'s raw recall differing by **one article** between two ways of
scoring the same 660 rows with the same weights: `eval_ht_v8.py` gives **18 TP**, the
production inference path **17**.

Excluded by measurement:

- **the device** — CPU vs CUDA, same box, same dumps: **0 verdict flips on both arms**,
  max \|Δ\| **0.1428** calibrated / **0.0508** raw, the same 17 and 26 surfaced
  (`docs/evidence/2026-09-06-v8-deploy-gate/device_delta.py`). ⛔ Note that 0.1428 is
  **below** the #95 batch floor of 0.16, so zero flips is the expected outcome here, not a
  surprising one — this measurement bounds the device term for THIS population, it does not
  overturn the 0.1956 measured on `uplifting v7`.
- **the gatekeeper and the clamp** — applying or removing them moves **0 rows** across 4.5
  on either device (`why_18_not_17.py`).

Still confounded, all three at once: **dtype** (production holds 342 bfloat16 parameters
against 364 float32, score head in bf16; the other path forces `torch_dtype=torch.float32`),
**adapter loading** (`load_lora_local` → `get_peft_model` + a hand-rolled remap vs
`PeftModel.from_pretrained`) and **batch size** (16 vs 8 — itself a #95 composition term).
The quantisation signature is real — 3,960 logits taking **1,161 distinct values** — but it
shows bf16 is present, not that it is the cause.

⚠️ **The lesson this file exists for applies to itself here.** *A floor belongs to a
population and a mechanism*: naming this "the dtype term" and giving it a magnitude would
create a sixth quotable number out of an unisolated comparison. It is `H-V8-23`, open, with
a falsifier — **not a term to quote.**

⭐ **What travels instead**: when two numbers for "the same model on the same rows" disagree,
**the device is now the LEAST likely explanation in this repo and the program is the most** —
and the previously recorded explanation for this exact gap was the device. Ask which program
produced each number before reaching for a measured term that happens to be near the gap.

## Related

- [[project_session_2026_08_03]]
- #95 — the issue, with the fix options (pin batch_size first)
- #109 — arm A, where the oracle floor was first measured

### Re-measured at n=200, 2026-08-29 — smaller, same shape

`docs/evidence/2026-08-29-v8-phase-a-k3/`. The 30-row panel above was **stratified across
the v7 score range and weighted to the op-point**, so its 13% is that panel's rate. Two
strata, drawn and reported separately, never pooled:

| | production-mix (n=150) | boundary [4.0,5.0) (n=50) |
|---|---|---|
| scope-binary disagreement, per identical-run pair | **5.3%** [2.7%, 8.4%] | **6.7–9.3%** |
| rows non-unanimous over 3 identical runs | **8.0%** | **10–14%** |
| op-point crossing between identical runs | **2.4%** | **12.7%** |
| k=1 and k=3 disagree on the op-point | **1.3%** | **4.0%** |

⭐ **The shape claim survives; the magnitude is NOT refuted, only given an interval.** It is
still a Bernoulli on a binary verdict, `1/√k` still does not apply, and k ≥ 3 still stands.
⛔ **Do not write "smaller than 13%".** 4/30 carries a Clopper-Pearson CI of **[3.8%, 30.7%]**
which contains every number in the table above; Fisher's exact gives **p = 0.118**
like-for-like and **p = 0.4648** against the like-for-like boundary cell (the earlier
**0.722** named no cell and used a non-comparable one) — the population an
op-point-weighted panel actually sampled. The design-weighting story is plausible and
**indistinguishable from n=30 sampling noise**; a dismissal is a claim and this one has not
been measured. The ~860-of-6,590 figure inherits the panel's weighting either way, and
neither number was measured on the v7 corpus, which is a third population again.

⛔ **And one more thing that is not noise at all, found in the same run: PROMPT POSITION.**
*(Deliberately un-numbered: this file and the memory index were counting the same list from
two different bases — "a fifth" here against "a sixth" there. A hand-maintained ordinal in
two files disagrees the moment one is edited.)*
Moving the article from char 617 to char 40,626 of the same prompt — content-preserving to
one `---` — shifts the score by **−0.239** on the production mix (95% CI [−0.409, −0.080];
sign-flip permutation p=0.0049, source-clustered [−0.410, −0.078] — but ⛔ **NOT
multiplicity-robust**: 0.0049 does not clear 0.05/16, the family the script prints, and no
family was pre-registered), against a
within-arm null of 0.312 mean |Δ| measured on the same rows. That is **bias, not a floor**:
it is directional and no amount of k removes it. **Never treat a prompt edit as
noise-equivalent because its |Δ| looks like the noise band — check the sign.**
⚠️ The claim that it also holds *within* the gate-stable rows (−0.235) was **withdrawn on
review**: it pooled two strata and conditioned on `scope_verdict`, which the treatment
changes. Per stratum the gate-stable effect includes zero on the production mix. The
position effect is established; *where it acts* is not.

