# `cultural_discovery v5` cross-oracle re-score — #109 arm A

**Date:** 2026-08-12
**Issue:** #109 arm A (owner: **approved** 2026-08-12; arm B held)
**Status:** **COMPLETE — verdict WITHIN NOISE.** Everything above the Results
section was committed in `6741da2` *before* a single real score existed; the
decision rule was not fitted to the answer.
**Reproduce (sampling):**
`PYTHONPATH=. python3 scripts/research/cd_v5_arm_a_sample.py --splits-dir <splits> --meta <merged-scored> --out-dir <scratch>`
**Reproduce (analysis):**
`PYTHONPATH=. python3 scripts/research/cd_v5_arm_a_analyze.py --design <scratch>/design.json --scored <scratch>/scored.jsonl --noise-scored <scratch>/noise_scored.jsonl`
**Source:** `cultural_discovery v5`'s own training splits (`train`/`val`/`test`,
8,551 rows) from `gpu-server`/`b650-gpu`, joined on `id` to
`cd_v5_deepseek_merged_for_training.jsonl` for source/date/language. Article text
lives only in a session scratchpad — never in this repo (#97).

## The question this settles, and the one it does not

#105 measured that today's labelling gate refuses **52.2%** of the corpus
`cultural_discovery v5` was trained on, and that refused rows carry **lower**
stored labels (mean 1.102 vs 2.214). #105 stopped exactly there, because that
compares *distributions*, not *truth*: it cannot distinguish "the rule tightened
and the labels were always fine" from "the labels on those rows were never
defensible". The two readings have opposite consequences for a retrain.

Arm A asks the narrower answerable question: **do the refused rows' stored labels
survive a second oracle's judgement as well as comparable passed rows' do?**

It cannot establish that either oracle is right. It replaces one model's opinion
with another's and measures only *disagreement* — if both are wrong in the same
direction it returns a clean result and is wrong. That limit is inherited from
`feedback-oracle-not-ground-truth` and is not fixable within this design.

## Why cross-oracle, and why Gemini specifically

v5 was labelled by **DeepSeek** (ADR-020). Re-scoring with DeepSeek would measure
self-consistency and is blind to systematic error, so the instrument is **Gemini
Flash 2.5** — this repo's other production oracle. The prompt, text cleaning,
800-word compression and JSON parsing are the *same code path* that produced the
DeepSeek labels (`scripts/score_deepseek_production.py` against
`filters/cultural_discovery/v5/prompt-compressed.md`), pointed at Gemini's
OpenAI-compatible endpoint. **The oracle is the only variable.**

That code path had never been executed against Gemini — only DeepSeek — so it was
smoke-tested on 2 rows first and the parsed output inspected before any sample
spend. 10.1k input / 382 output tokens per row; projected ~$1.35 for all 340
calls, against #109's ~$1.20 estimate.

Metadata symmetry matters and is why the `--meta` join exists: the training
splits carry no `source`/`published_date`, and a prompt reading `Source: N/A`
differs from the one the labelling oracle saw. The join is **100% complete
(8,551/8,551)** and a miss is fatal rather than defaulted.

## Design — 1:1 matched on (domain, stored-label band)

Both variables, because each alone has already cost this repo a result.

- **Band**, because #105 showed the arms' label distributions differ sharply; an
  unmatched comparison would re-measure that gap instead of label quality.
  Bands: `[0,0.5) [0.5,1.5) [1.5,2.5) [2.5,4.0) [4.0,10]`, the top band starting
  at the **runtime** op-point (`base_scorer.py TIER_THRESHOLDS` medium = 4.0),
  not `config.yaml`'s copy of it.
- **Domain**, because #108 died precisely here: a clean corpus-level result
  evaporated once the treatment turned out near-collinear with source. In this
  population refusal *is* source-linked — `eco.sapo.pt` 198 refused / 14 passed,
  `www.ad.nl` 213 / 32. Source is a confounder here, not a caveat.

Matching worked: the sampled arms' mean stored label is **1.511 vs 1.548**
(against 1.102 vs 2.214 unmatched), band counts are **identical by
construction**, and language balances at en 108/111, nl 17/15, pt 9/9.

**Sampling.** 150 pairs drawn by simple random sampling over *pair slots* — each
(domain, band) cell contributes `min(n_refused, n_passed)` slots. Every slot
therefore has the same inclusion probability, the design is self-weighting
(Horvitz-Thompson weight **13.493** for every pair), and no cell can be dropped
by construction. A first version allocated proportionally with largest
remainders; measurement killed it — 150 pairs over 342 cells sent **252 cells to
zero** and produced weights spanning 4.0–17.0. Proportional rounding at this
ratio does not approximate a size-proportional sample, it deletes every cell
smaller than one unit.

**Rows under 300 chars are excluded from both arms.** Only 6 refused rows are
length-refused, so this costs nothing here, and it keeps the oracle inside the
range the floor exists to protect (#93, #92).

## What the estimand excludes — enumerated, not assumed away

The estimand is the **pair-matchable refused population: 2,024 of 4,458 rows
(45.4%)**.

A (domain, band) cell with no passed row admits no matched pair. Those
**2,434 rows (54.6%)** are excluded, and they are not a random half — they
concentrate in the domains the lens gate refuses almost totally:

| domain | unmatchable refused rows |
|---|---|
| `eco.sapo.pt` | 184 |
| `www.ad.nl` | 181 |
| `nos.nl` | 151 |
| `www.scmp.com` | 148 |
| `www.reddit.com` | 126 |
| `canaltech.com.br` | 119 |

Weighting the matched sample up to the full refused population would assume the
unmatchable cells behave like the matchable ones — the assumption #108 refuted.
So the result is reported for the matchable population and **the excluded half is
stated, never extrapolated over**. Any reading of arm A that generalises to "the
refused corpus" is over-claiming; the honest scope is "the refused rows that come
from outlets the lens gate does not refuse wholesale".

## Decision rule — fixed before any score was seen

**Primary estimand:** `D = MAD_refused − MAD_passed`, where
`MAD_g = mean |gemini_weighted − stored_weighted|` over arm *g*, taken **within
cell** and bootstrapped over the 150 pairs (10,000 resamples, seed 20260812).

**MATERIAL iff both hold:**

1. the paired bootstrap 95% CI for `D` excludes 0, **and**
2. `|D| ≥ ν`

where **ν is the within-oracle mean `|Δ|`, measured on this same population** by
re-scoring 40 of the sampled rows (20 per arm) a second time.

ν is measured rather than borrowed on purpose. #95's `0.16` is a **student
batch-composition** figure and says nothing about oracle sampling at
temperature 0.3; importing it here would be the wrong instrument, which this
repo has already done three times in one day
(`memory/score-batch-shape-noise.md`). Without a measured ν, #109's "gap within
noise" branch is unfalsifiable — which is why the duplicate control is spent
before the verdict is read, not after.

**Required secondary outputs** (per #109, outputs not caveats): signed bias per
arm and its difference (the #92 inflation signature has a *direction*);
op-point crossing tables at raw 4.0; per-dimension MAD; **per-domain `D` for
every domain with ≥5 pairs, with sign agreement against the headline**;
per-language and per-band `D`; and full coverage accounting — missing rows,
broken pairs and oracle errors are counted and printed, never silently dropped.

## Pre-registered consequences (from #109)

| result | consequence |
|---|---|
| `D` within noise | `cultural_discovery v5`'s corpus is trustworthy on the matchable half; #105's cd half closes; a retrain is a base-rate change only |
| `D` material, refused worse | The lens gate refuses rows whose labels are *also* unreliable; #98's probe replacement is being designed on a corpus with a second problem |
| `D` material, refused **better** | Not in #109's table, and it would be a finding: the gate is discarding the corpus's better-labelled rows |
| per-domain signs disagree with the headline | The headline is a source artefact, as in #108, and must not be reported as a corpus property |

## Results

**Ran 2026-08-12. 300/300 sample rows and 40/40 duplicate-control rows scored,
0 errors, 0 missing, 0 broken pairs, 150/150 pairs analysed.** Actual spend
$1.21 for the sample (3,093,922 input + 112,359 output tokens) and $0.16 for the
control — **$1.37 total**, against #109's ~$1.20 estimate.

### Primary — WITHIN NOISE

| quantity | value |
|---|---|
| `MAD_refused` | **0.8325** |
| `MAD_passed` | **0.8370** |
| `D = MAD_refused − MAD_passed` | **−0.0045** |
| paired bootstrap 95% CI | **[−0.216, +0.195]** |
| `ν` (within-oracle mean \|Δ\|, n=40) | **0.4356** |
| CI excludes 0 | no |
| \|D\| ≥ ν | no |
| **verdict** | **WITHIN NOISE** |

**This is a bounded null, not merely an underpowered one.** The CI's widest
excursion is 0.216, and the oracle's own run-to-run spread on this population is
0.436 — so the entire range of effects this sample could not rule out lies
*below* the floor at which any difference becomes interpretable. Refused and
passed rows' stored labels survive a second oracle equally well, and no gap
large enough to matter can be hiding in the residual.

**Per #109's pre-registered table, this closes #105's `cultural_discovery` half:
the corpus is trustworthy on the matchable population, and a retrain there is a
base-rate change, not a label-quality repair.**

### ν is large, and that is a finding about the instrument

`ν = 0.436` mean, **max 2.10**, measured by scoring 40 of these same articles
twice at temperature 0.3. Two consequences worth carrying:

- **Any future cross-oracle claim on this filter needs a gap above ~0.44 to mean
  anything.** This is a *different* quantity from #95's 0.16 student band and
  much larger. It is a per-article oracle-sampling floor, and nothing in this
  repo had measured it before today.
- **It is arm-asymmetric: 0.238 on refused rows vs 0.634 on passed rows** (n=20
  each — thin). The mechanism is visible in the transcripts: refused rows are
  mostly off-lens, where both runs return zeros and agree trivially; passed rows
  carry live dimensional judgement.

### The registered primary is an MAE-shaped metric, and ADR-023 warns against exactly that

Recorded because it is a defect in this design, found by self-review after the
result was in, not a caveat invented to soften it.

ADR-023 says never rank on MAE, for two reasons. The **second** — that each
population's positive rate makes per-article error incomparable — is neutralised
here by band matching, which is why a matched MAD is defensible at all. The
**first** is not neutralised: MAE weights every article equally while the product
only cares about the thin band at the operating point. `MAD_refused` and
`MAD_passed` are averages over 150 pairs of which **9** sit at or above raw 4.0.

So the pre-registered primary answers "are these labels equally defensible
*overall*", and the question ADR-023 says matters is "are they equally defensible
*where a decision gets made*". The band table below is that warning firing. The
null stands for what it measures; it is not evidence about the op-point, and the
follow-up is not optional politeness.

### Two observations the registered test does not cover

Both are flagged as hypotheses. Neither was pre-registered, so neither is a
result, and reporting them as findings would be fitting the analysis to the data
after the fact.

**1. The op-point band moves the other way, on 9 pairs.** `D` by stored-label
band:

| band | pairs | `D` |
|---|---|---|
| `[0,0.5)` | 28 | −0.102 |
| `[0.5,1.5)` | 62 | −0.164 |
| `[1.5,2.5)` | 33 | −0.072 |
| `[2.5,4.0)` | 18 | +0.294 |
| **`[4.0,10]`** | **9** | **+1.044** |

ADR-023 says only the thin band at the operating point decides anything, and the
registered primary is a corpus-wide mean that drowns it: 9 of 150 pairs sit at or
above raw 4.0. The point estimate there is 2.4× ν and in the direction that would
implicate refused labels. **It is 9 pairs and could be noise.** It is also cheap
to settle — band-4 pair capacity is **88**, so a dedicated op-point sample costs
roughly **$0.40**. Carried as the one follow-up arm A justifies.

**2. Normalised by each arm's own noise, the arms are not equal.** `MAD/ν` is
3.51 refused vs 1.32 passed. If that survived a larger control it would say the
refused arm carries more cross-oracle disagreement *relative to how easy its rows
are* — which the registered absolute-MAD comparison cannot see. On 20 rows per
arm it is not worth acting on; a 100-row control would settle it.

### Secondary outputs (all required by #109)

**Signed bias.** Gemini − stored: **+0.030 on refused**, **+0.353 on passed**;
difference **−0.323**, CI [−0.551, −0.104]. The CI excludes 0 — but 0.323 is
**below ν = 0.436**, so by the same rule applied to the primary it is **not
interpretable**, and it is reported here rather than promoted. Its direction, if
it were real, points *away* from the #92 inflation signature: it would say
Gemini scores the **passed** rows higher than DeepSeek did, i.e. mild
under-labelling of on-lens content, with refused rows agreeing almost exactly.

**Op-point crossings at raw 4.0** (of 150 per arm):

| | stored ≥ op, Gemini < op | stored < op, Gemini ≥ op |
|---|---|---|
| refused | 5 | 4 |
| passed | 3 | 13 |

Consistent with the signed bias: Gemini would surface 13 passed rows DeepSeek
kept below the line, against 4 refused rows.

**Per dimension** (MAD refused vs passed): `discovery_novelty` 1.290/1.287,
`heritage_significance` 0.773/0.927, `cross_cultural_connection` 0.497/0.613,
`human_resonance` 1.003/1.070, `evidence_quality` 1.493/1.497. No dimension
shows refused rows disagreeing more; the two largest disagreements
(`evidence_quality`, `discovery_novelty`) are equal across arms.

**Per source — the required re-check.** `D` by domain, ≥5 pairs:
`pubmed.ncbi.nlm.nih.gov` +0.331 (17), `www.engadget.com` +0.071 (13),
`www.reddit.com` +0.163 (13), `nos.nl` −0.177 (11), `www.fastcompany.com`
−0.116 (11), `canaltech.com.br` +0.571 (7), `www.scmp.com` +0.500 (5).
**Sign agreement with the headline: 2/7.** For a null that scatter is what should
happen — but it also means no per-source reading may be lifted out of this table
as a finding. `canaltech.com.br` +0.571 and `www.scmp.com` +0.500 exceed ν on 7
and 5 pairs respectively; that is the #108 shape and would need its own sample.

**Per language:** en +0.116 (108), nl −0.479 (17), pt +0.342 (9), es −0.461 (7),
fr −0.244 (4), it −0.217 (3), de −1.625 (2). Scattered around zero, and every
non-English cell is too small to read. Relevant to #108 only as an absence: this
sample shows no non-English penalty on cd v5's *full-length* rows.

### Scope, restated

The estimand is the **pair-matchable refused population, 2,024 of 4,458 rows
(45.4%)**. The other 54.6% comes from outlets the lens gate refuses wholesale
(`eco.sapo.pt`, `www.ad.nl`, `nos.nl`, `www.scmp.com`, `www.reddit.com`,
`canaltech.com.br`) and is **not covered by this result**. Those domains have no
passed rows to match against, so the question "are their labels defensible?" is
unanswerable by a matched design and needs a different instrument.
