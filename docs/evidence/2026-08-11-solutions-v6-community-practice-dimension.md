# solutions v6 — `community_practice_strength` is not dead

**Date:** 2026-08-11 (evening)
**Question asked:** the dimension is zero on 83% of on-topic articles while
carrying 10% of the score. Find 20 articles that should score high on it — easy
to find means a data gap worth fixing, hard to find means the dimension is not
real.
**Answer:** neither. The dimension is real, the misses are hard to find, and the
one defect that survives measurement is small and belongs to calibration.

Reproduce:

```bash
PYTHONPATH=. python3 scripts/research/solutions_v6_reweight_ablation.py
# on a GPU box, from the repo root:
PYTHONPATH=. TQDM_DISABLE=1 venv-prodparity/bin/python \
    scripts/research/solutions_v6_student_dim_fidelity.py
PYTHONPATH=. python3 scripts/research/solutions_v6_dim_fidelity_report.py
```

---

## 1. The 83% is base rate, and it is mandated

83.1% reproduces exactly (1,953 of 2,350 on-topic rows across all three splits).
Step 2 of the oracle prompt **forces** it: content_type `tech` sets both
governance and community to 0, `governance` sets community to 0.

⚠️ **A decomposition of that 83.1% into "40.0% tech-shaped + 43.1%
governance-shaped" is CIRCULAR** and was retracted the moment it was written.
Both categories are defined *using* `comm == 0`, so they sum to the zero rate by
construction. `content_type` is **not stored in the training splits**, so the
prompt's forcing rule cannot be verified as having fired correctly from this data.

The non-circular evidence that the dimension is real: when it fires it spreads
properly — n=397, mean 5.09, median 5.0, range 1–8.5 — and the exemplars are
coherent (Amul Dairy Cooperative 8.5, community forestry in Nepal 8.0, a
Rajasthan "River Parliament" allocating water across 70 villages 8.0, 30 years of
community health workers 8.5).

## 2. The misses are hard to find — 2, not 20

All 1,953 on-topic zeros were screened twice: a keyword pass (201 hits) and a
tighter actor-centred pass requiring the community to be the *doer* (112 hits, 42
at or above weighted 4.0). Hand-reading the strongest yielded **2 genuine misses**:

| article | scored | oracle's own analogue |
|---|---|---|
| Anyone in Paris Can Decide How the City Spends Its Money — 21,000 citizen proposals, 1,345 funded projects | comm **0**, gov 7.5 | Rajasthan River Parliament, comm **8.0** |
| Scaling field pea technology, Ethiopia — 109 farmers on 32.5 ha collectively, farmer-to-farmer seed diffusion | comm **0**, gov 0 | Amul Dairy Cooperative, comm **8.5** |

Both are **hybrid articles tagged single-type**. Step 2 makes `content_type` a
hard gate, so a tiebreak error does not shade the score — it deletes the dimension.

Screen noise worth knowing: a run of South African hits came from the
**Department of Co-operative Governance** matching `" co-op"`.

## 3. Re-weighting is inert — twice over

The weights sum to 1.00, so a mandated zero is a straight subtraction and the
score ceiling differs by solution type: **pure tech 7.50, governance 9.00,
community/hybrid 10.00**. That is arithmetic. It costs nothing:

- **Ranking.** At matched surfacing volume, renormalising over permitted
  dimensions swaps **11 of 1,628 articles (0.7%)**; dropping comm+gov entirely
  swaps 17 (1.0%). It is a near-monotone rescale — it does not reorder.
- **Absolute thresholds.** ≥4.0 moves 31.1% → 50.6% (tech alone: 15.6% → 56.8%).
  **This is an artifact, not a win.** NexusMind's enrichment gate reads
  `result["weighted_average"]` (`article_fetcher.py:1355`), and
  `production_scorer.py:16-17` overwrites that field with the **normalized**
  score. Normalization is a percentile CDF, so a monotone rescale maps back to
  the same percentiles and the effect vanishes at the next refit.

**No weighting change is worth making.** The apparent enrichment win was one read
of `production_scorer.py` away from being recommended — logged because the clean
measurement fit two mechanisms and only the code distinguished them.

Side result, unrelated to the weighting: normalized 4.0 corresponds to **raw
3.261**, and **75.6%** of surfacing training rows clear it. Whatever starves
`solutions v6` of enrichment (NM#319), the weighting scale is not it. That is a
prediction about production data and has **not** been tested against it.

## 4. The student learns it better than it learns the rest

1,032 test rows, b650, `venv-prodparity`, GPU.

| dimension | base rate | fires on positives | false-fire | **r on positives** | isotonic steps |
|---|---|---|---|---|---|
| solution_concreteness | 23.9% | 87.0% | 12.6% | 0.564 | 30 |
| systemic_impact | 23.9% | 91.1% | 15.5% | 0.486 | 37 |
| evidence_strength | 23.9% | 87.9% | 11.8% | 0.373 | 30 |
| governance_intervention | 12.5% | 72.1% | 8.5% | 0.487 | 24 |
| **community_practice** | **4.0%** | **80.5%** | **4.0%** | **0.622** | **16** |
| equity_access | 23.9% | 83.0% | 9.7% | 0.573 | 41 |
| economic_viability | 23.8% | 83.7% | 9.8% | 0.467 | 34 |

Highest conditional correlation and lowest false-fire rate in the filter — the
most *precise* dimension `solutions v6` has, which under ADR-023 is the property
worth having.

**`community_practice_strength` also has the lowest MAE (0.179) and that fact
carries no quality information.** It is zero on 96% of the split. This is the
ADR-023 trap in miniature; MAE is reported by the script as scale only.

## 5. The one real defect: calibration compression

On oracle-positive rows the student averages **2.69 against the oracle's 4.63** —
the dimension does ~58% of its designed work. It emits only **16 distinct
values**, fewest of the seven, with **13 of 41 positives pinned to exactly 1.90**,
because the isotonic fit had 21 breakpoints to work with.

Sized: **0.194 on the weighted score at weight 0.10, on 4.0% of rows** — just
above the #95 noise floor of 0.16. Real, but not worth its own deploy. Fold it
into the next calibration refit.

## 6. What actually limits this dimension

Re-weighting and recalibration are both downstream of one cause: **41 positives in
the test split, ~397 in the whole corpus.** Isotonic regression cannot build a
fine mapping from that and the model cannot learn magnitude from it.

Section 2 shows the positives are not hiding in the corpus. So this is real
scarcity, which makes it a **sourcing** question — which outlets carry
grassroots-practice stories — not a modelling one.

## Caveats

- **Cross-box** ⛔ *(mis-named; corrected 2026-08-29 — the host term is 0.0000 and this
  0.2008 is the LIBRARY STACK. See docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md)*: the Gemma-3-1B student is not probe-clean across boxes (b650 vs
  gpu-server ran to |0.2008| on uplifting v7, above the #95 floor). Fine for "does
  this dimension carry signal"; **no number here is production's** without
  re-running `scripts/verification/box_parity.py` at the threshold in question.
- **`content_type` is not in the splits**, so shape is a proxy throughout §1/§3
  and cannot distinguish a mandated zero from an honest one.
- **§3's enrichment claim is about NexusMind production data and was not tested
  against it** — only against this repo's training corpus and the normalization fit.
- No oracle spend. GPU time ≈ 4 minutes.
