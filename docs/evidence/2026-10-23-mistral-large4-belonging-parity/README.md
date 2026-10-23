# Mistral Large 4 as an oracle on belonging v3 — label parity, 2026-10-23 (EXP-060)

**Answer: FAIL, and not close.** On belonging v3's 100-item canary set, `mistral-large-4-0` (reasoning off) scores
every dimension at about half of Gemini Flash's level. The mean of 3 runs shifts −1.9144 against the committed
Gemini baseline, with 30 flips at the 4.0 op-point (the k=3 bar fails above 3 flips or |shift| 0.1996). All 30 flips
go one way: Gemini passes, Mistral blocks. Mistral passes 17 of the 100, Gemini 47.

Pre-registered in `PREREGISTRATION.md` (commit `d6b0034`) before any call. The decision rule, set, baseline and
request are the ones fixed there. My prediction was wrong in direction (I predicted a positive shift).

## What was measured (`result.txt`, from `analyse.py` over the lab copies)

| | |
|---|---|
| primary, mean of M1–M3 vs baseline (k=3 bar) | **FAIL**, flips 30, shift −1.9144 |
| each run alone (k=1 bar) | M1 FAIL 31 / −1.9074; M2 FAIL 29 / −1.8811; M3 FAIL 30 / −1.9549 |
| Mistral vs itself (each run vs the other two) | 1 flip each; shift +0.0106 / +0.0500 / −0.0606 |
| at ≥ 4.0, same 100 items | Mistral 17, Gemini 47 |
| \|Δ\| median / max | 1.00 / 5.94 |
| parse | 300 of 300 scored; 1 bad-JSON call in M2, re-scored on the second pass |
| served model | `mistral-large-4-0` on every scored row |

Per-dimension means, Gemini run B1 against Mistral M1 (same 100 items; an inline check, not in `result.txt`):
intergenerational_bonds 3.06 → 1.39, community_fabric 3.98 → 1.79, reciprocal_care 2.87 → 1.08,
rootedness 3.60 → 1.77, purpose_beyond_self 4.07 → 2.00, slow_presence 2.92 → 1.28. Uniform, so this is not one
dimension or a parsing fault. Because community_fabric < 3 triggers the gatekeeper cap (3.42), Mistral's lower
community_fabric also pulls many weighted averages under 4.0.

**Mistral is very stable** (1 flip run to run, against Gemini's own 3). It is a consistent, stricter reader of this
prompt, not a noisy one.

## Probe (3 calls) and the reasoning switch

- Default (reasoning on): 6,189 in / 5,376 out, of which 5,079 reasoning tokens.
- `reasoning_effort: "none"`: accepted, 0 reasoning tokens, 430 out. So by the pre-registered rule the full runs
  used reasoning off, matching the baseline's thinking off.
- On that one article, reasoning ON scored LOWER than reasoning off on 3 of 6 dimensions (e.g. rootedness 2.0 vs 6.0).
  One article, so no claim; but nothing suggests reasoning on would close the gap.

## Cost (ESTIMATE; the bill is Mistral's usage page)

304 billed calls, 1,792,067 in / 81,867 out: **$2.78 ≈ €2.40** at $1.36/$4.18 per M. That price comes from web
aggregators via infra and is not verified against docs.mistral.ai. Which allowance the key bills is still unverified.
Per article with reasoning off ≈ €0.0078, so about 3,261 articles per €25.50 monthly allowance. Tokens per article
are close to Gemini's (≈5,900 in, ≈250 out), as the owner hoped; the quality question is what failed.

## What it does NOT show

- **Which oracle is right.** The oracle is not ground truth. Gemini passes 47 of 100 on this set; Mistral 17. The
  owner's own reading (EXP-059) found the shared tagger prompt reads "personal" more narrowly than the owner, which is
  a different task and a different prompt, so it does not settle this either.
- **Whether a monotone remap would work.** All flips go one way and Mistral is stable, so a lower Mistral op-point
  might reproduce Gemini's calls. That was not pre-registered, and fitting it on these 100 items would be fitting on
  the test set. Untested.
- One filter, one prompt, one set. Other prompts (human_thriving, solutions) are untested on Large 4.
- Switching would in any case be a new oracle key with rebuilt baselines (`canary.py` refuses another oracle).

## Files

`run_mistral.py` (prompt bytes from `batch_scorer.build_prompt`, digest-checked against the baseline), `analyse.py`,
`result.txt`, `MANIFEST.json` (lab citations). Raw rows: lab
`experiments/2026-10-23-mistral-large4-belonging-parity/raw/` (`_LAB_MANIFEST.json`). Gemini's billing key returned
HTTP 402 on a 2026-10-23 check call, so the baseline itself could not be re-run; none was needed.

## Follow-up (EXP-061, $0): a lower Mistral threshold does not rescue it

Owner asked on 2026-10-23 to test a lower Mistral threshold on existing Gemini data. Before spending, `remap_check.py`
(output `remap_result.txt`) fitted the threshold IN-SAMPLE on this canary set, the most favourable case:

- Best plain threshold: **1.40**, still **12 flips** per 100 (11 Gemini-pass / Mistral-block, 1 the other way).
- A per-dimension linear remap before the weighted average lands on the same floor: 12 flips.
- The bar, Gemini against itself single run vs single run (all 15 pairs of B1–B6): max 4, mean 2.27.

So no threshold or per-dimension linear remap gets within the bar even when fitted on the test items themselves; a
held-out set can only do worse in expectation. The out-of-sample run (about 260 Gemini-stamped rows in
`datasets/scored/belonging_v1_{prodheldout,control}_20261001`, none in the canary set) was therefore NOT run.

The remap's intercepts are about +2 on every dimension: where Mistral scores ~0 (out of scope), Gemini gives modest
scores. The 12 remaining flips are articles the two rank differently (Spearman 0.86 on the weighted averages, an
inline check), which no threshold can fix. Not pre-registered: the fit rule (fewest flips, ties to the higher
threshold) was chosen at the time, on data already seen.
