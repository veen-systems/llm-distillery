# human_thriving v8 — the ADR-021 deploy gate, on CUDA (2026-09-06)

**The gate ran and v8 has a number: recall 0.343 / specificity 0.992 at the ruled
op-point 4.50, on 660 held-out oracle rows with a 5.30% positive rate (35/660).**
Report: `filters/human_thriving/v8/ground_truth_gate.json`. Inputs:
`DUMP_MANIFEST.md`.

## ⛔ Read the specificity first — we prioritise HIGH CERTAINTY over HIGH DETECTION

**That 0.343 is the decision working, not the model failing.** This project chooses being
right about what it surfaces over surfacing more of what it could (ADR-023): a false
positive reaches a reader and costs trust; a false negative is invisible and the slot
refills immediately. So **specificity is the criterion, recall is a constraint to satisfy**,
and the op-point was set at 4.50 by the owner after seeing the whole frontier
(`docs/decisions/2026-09-05-v8-op-point.md`) — every step from 3.75 up costs about one
agreed-good article per junk article removed, and a 1:1 trade breaks toward certainty.

In plain terms: **v8 surfaces about a third of what the oracle calls on-lens, and is right
about 70% of what it does surface.** It lets through 5 junk articles in 660 where the raw
arm lets through 9. Buying the missing recall means buying those back.

⛔ **Do not read this page as a scorecard to improve.** A change that raises recall at this
op-point is a regression under ADR-023 unless it also holds specificity, and "the recall is
low" is not on its own a finding.

## 1. What was run

| | |
|---|---|
| Split | `datasets/training/human_thriving_v8/test.jsonl`, 660 rows, held out from training **and** from the calibration fit |
| Truth | the ORACLE labels on that split, gatekeepered with v8's own config (ADR-021: never judged against `uplifting v7`) |
| Bar | 4.50 on the **calibrated** scale — the ruled op-point (`docs/decisions/2026-09-05-v8-op-point.md`), read from `config.yaml` by `--config`, not passed as a literal |
| Device | **CUDA**, on b650 with gpu-server's production pins |

```
model               n  recall    prec    spec      f1  spearman    mae
calibrated_cuda   660   0.343   0.706   0.992   0.462     0.807   0.541
raw_cuda          660   0.486   0.654   0.986   0.557     0.807   0.532
```

`calibrated_cuda` is the deploying arm: `calibration.json` is present, and
`filter_base_scorer.py` calibrates at `:315-317` before `_assign_tier` reads the value at
`:340`. `raw_cuda` is the same forward pass without the map, kept because **4.5 means two
different things on the two scales**.

⛔ **The two arms are NOT DISTINGUISHABLE here.** Recall, specificity and F1 bands all
overlap under the #95 batch-composition floor (0.16); 9 of 660 calibrated rows sit inside
the floor of 4.5 and are indeterminate. The arm was never this gate's choice — the runtime
applies calibration, so the calibrated row is the one that describes production.

⚠️ **Do not set 0.343 beside the fleet's 0.59–0.72.** v7 and v8 do not share a positive
class (Jaccard **0.246** on these same 660 rows): those are two quantities with one name.
And the rates are **unweighted sample** rates on a 25.1× design that over-samples
positives; design-weighted the base rate is 3.1638%, not 5.3030%.

## 2. Why the split was re-scored first

Every v8 accuracy number before today was **CPU**-measured while production serves on
**GPU** (#104). CPU→CUDA is not free: `uplifting v7`'s 660 rows move by max |Δ| **0.1956**
with **3 verdict flips at 4.5**, and `EXP-015` saw CUDA give 18 TP against CPU's 17. A
deploy gate is the one artifact that must not inherit that caveat, so the CPU dumps already
on disk — which would have run fine — were not used.

### The device term, measured for v8

`device_delta.py` (output in `device_delta.txt`), reusing the gate's own `load_scores` so
the quantity compared is the one the gate thresholds:

| arm | bit-identical | p50 | p90 | p99 | MAX \|Δ\| | flips at 4.5 | surfaced |
|---|---|---|---|---|---|---|---|
| calibrated | 411/660 (62.3%) | 0.0000 | 0.0175 | 0.1083 | **0.1428** | **0** | 17 cpu / 17 cuda |
| raw | 8/660 (1.2%) | 0.0029 | 0.0129 | 0.0395 | **0.0508** | **0** | 26 cpu / 26 cuda |

✅ **CPU and CUDA agree on every verdict for v8 at 4.5** — identical confusion matrices,
the same 17 surfaced rows. This gate's numbers do not depend on the device.

⛔ **That is a result, not a licence.** It was worth measuring precisely because it could
have gone the other way, and on v7 at the same 4.5 it *did* — 0.1956 and 3 flips. A device
term belongs to a population, a model and a threshold; it is not inherited. The magnitude
here (0.1428 calibrated) is still **below** the #95 batch floor of 0.16, which is why zero
flips is the expected outcome rather than a surprising one.

⚠️ The p50 of exactly 0.0000 on the calibrated arm is the isotonic map's step structure,
not agreement: the raw arm — the same rows before calibration — is bit-identical on only
**8** of 660.

### ⛔ And it refutes something this repo had already written down

`STATUS.md` explained `EXP-015`'s raw recall of **0.514** (18 TP of 35) against this gate's
**0.486** (17) as *"a device difference — EXP-015 on b650-CUDA, this on CPU, i.e. the CPU→CUDA
0.1956 term landing near the bar."* **That explanation is wrong, and the measurement above is
what refutes it**: CPU and CUDA give 0 flips and the same 17 on this split, so the device
cannot produce 18.

Nor can the gatekeeper or the clamp: computing the plain dot product `(P·w)` — what
`eval_ht_v8.py` does — and the gate's gatekeepered, clamped WA over the same dump moves **0
rows** across 4.5, on either device.

What differs is **the program**, and it differs in at least three ways at once:

| | production path (this gate) | `eval_ht_v8.py` (EXP-015) |
|---|---|---|
| dtype | **342 bfloat16 params against 364 float32**, score head in bf16 — read off the loaded object on b650 | `torch_dtype=torch.float32`, passed explicitly |
| adapter load | `load_lora_local` → `get_peft_model` + a hand-rolled state-dict remap | `PeftModel.from_pretrained` |
| batch size | 16 | 8 |

⛔ **Only the dtype was measured to be present; it was not ISOLATED.** The circumstantial
case for it is good — bf16 quantises logits in ~0.03 steps, ample to move one row across a
bar, and the dump's 3,960 logits take only **1,161 distinct values**, the signature of
exactly that. But no arm was run holding the loading mechanism and the batch size fixed
while varying only the dtype, so "it is the dtype" is the leading candidate, not a
demonstrated cause. Registered as an open question rather than an answer.

✅ **What IS established, and it is the part that matters**: the device is excluded (0 flips,
measured above) and the gatekeeper and clamp are excluded (0 rows moved, `why_18_not_17.py`).
**Production serves bf16 through `load_lora_local` at batch 16 — this gate's own path — so
17 is production's number and 18 belongs to a program that is not what ships.** The two were
never the same measurement; the *reason* previously recorded for the gap was simply wrong,
and naming the right one exactly is a smaller claim than knowing which of three it is.

⚠️ `eval_ht_v8.py` is **not in this repo** — it lives on b650 at `~/llm-distillery/` and is
cited here from a read of that file, so a future reader cannot check its properties from the
repo alone.

⭐ *A dismissal is a claim.* "It's the device" closed the question for two days on a filter
whose whole remaining risk was a device caveat, and it survived because it named a real,
measured, plausible term — the one the reader was already primed for.

## 3. NM#319 — the enrichment gate, which the op-point ruling did not settle

**The answer is: nothing to do before deployment, and fitting normalization is what
changes it.** NexusMind gates post-scoring enrichment on `weighted_average >= 4.0`
(`src/enrichment/article_fetcher.py:1374`, `config/app.yaml:278`), and for a
`ProductionScorer` that field is the **normalized** score
(`src/scoring/production_scorer.py:17-18`).

- **Before Phase E** — v8 ships no `normalization.json` and `score_scale_factor: 1.0`, so
  the loader passes the raw score straight through. Every surfaced article (raw ≥ 4.5) is
  therefore ≥ 4.0 and enriches. There is no starvation risk at deploy time.
- **After Phase E** — the fitter *anchors* the CDF's lower edge to the op-point, so
  `stats.raw_min == 4.5` and **normalized(4.5) = 0.0 by construction**. The enrichment gate
  then bites in the middle of the surfaced population, not below it.

Measured on `uplifting v7`, which is already in exactly that state at the identical
op-point — 82 `filtered_*.jsonl` production cycles on sadalsuud, **2026-08-23 → 2026-09-06**,
251,461 rows carrying an `uplifting` block:

⚠️ **What that source excludes, stated before the numbers.** `filtered_*.jsonl` is written
under an `if result["passed_prefilter"]` guard, so it is 100% passers by construction — fine
here, because the question is about articles that reached a score, not about blocking. It
*also* drops source-type-excluded rows for filters that declare a `source_filter` block —
and `uplifting v7` declares none (`memory/nexusmind-data-sources.md`), so this particular
population is not subject to that trap. The window is 14 days and is part of the source: a
CDF fitted earlier is being read against a later population, which is exactly why the median
below is worth checking.

- **18,041 rows surface** (raw ≥ 4.5), 7.17% of the population. All 18,041 are
  `stage_used: stage2`, so `raw_weighted_average` really is a Gemma score here and not a
  probe estimate.
- **60.0% of surfaced rows (10,817) clear normalized ≥ 4.0. The other 40% — 7,224
  articles — are surfaced and silently un-enriched.**
- The gate's effective bar in raw terms is **raw ≈ 5.05–5.13** (n=938 rows within 0.25 of
  normalized 4.0), against an op-point of 4.5.
- Normalized among surfaced: p10 1.00 · p25 2.46 · **p50 4.97** · p75 7.48 · p90 8.92. A
  median of 4.97 against a percentile CDF's ideal 5.00 is a check that v7's fitted map
  still tracks its current population.

⚠️ **So Phase E is the step that takes ~40% of surfaced articles below the enrichment
gate** — it is not a v8 regression, it is what percentile normalization plus a 4.0 gate
already does to v7 today, and v8 inherits it. Whether that is the intended behaviour is an
owner question, not a filter question: it is the same shape NM#319 names, seen from the
surfaced side.

⚠️ **This is v7's CDF, used as a proxy.** v8's own map does not exist and cannot be fitted
yet (§4), so the *share* will differ; the *mechanism* — anchoring puts the op-point at
normalized 0.0 — is structural and will not.

## 4. Phase E is BLOCKED, and the ordering is the reason

`fit_normalization.py` fits the CDF **from production data** — NexusMind's
`data/filtered/{name}/filtered_*.jsonl` — and requires at least
`MIN_NORMALIZATION_ARTICLES = 200` rows above the op-point. Verified on sadalsuud
2026-09-06: `data/filtered/` holds `belonging`, `cultural_discovery`, `investment_risk`,
`nature_recovery`, `solutions`, `uplifting` — **no `human_thriving`**, and
`NexusMind/filters/` has no `human_thriving` package either.

There is no v8 production data because v8 is not deployed, so **Phase E comes after
deployment, not before it** — which is how `solutions v6` went (gate 2026-07-27, deployed,
normalization fitted 2026-07-28). ⛔ Do not substitute the test split or the draw corpus
for the production population: it is a 25.1× design-weighted sample, and a CDF fitted on it
would describe a population that does not exist.

## 5. What this does not say

- It does not say v8 is better than v7. Different positive class (§1); ADR-021 forbids the
  comparison and the Jaccard says why.
- It does not rank the arms (§1), and MAE is printed only because the gate prints it —
  ADR-023 forbids ranking on it.
- It measures no CUDA-to-CUDA cross-box term. b650 ran both passes; gpu-server's serving
  configuration is still unmeasured against it on GPU.
