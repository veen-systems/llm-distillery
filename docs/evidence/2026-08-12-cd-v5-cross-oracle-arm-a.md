# `cultural_discovery v5` cross-oracle re-score — #109 arm A

**Date:** 2026-08-12
**Issue:** #109 arm A (owner: **approved** 2026-08-12; arm B held)
**Status:** **PRE-REGISTERED — sample drawn, decision rule fixed, oracle not yet run.**
The results section below is empty on purpose. Everything above it was committed
before a single real score existed.
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

*Not yet run.* Populated by the analysis script above once the oracle pass and
the duplicate control complete.
