# `uplifting v7`: the Thriving lens surfaces research abstracts because the ORACLE says they are on-lens

**Measured 2026-08-20.** Reproduce: `PYTHONPATH=. python3 scripts/analysis/uplifting_v7_genre_bias.py`

## One-line answer

**The student is faithfully reproducing its labels — the oracle prompt is the
defect.** On the held-out oracle test split, academic-source rows are on-lens at
**55.2%** against **30.6%** for everything else (permutation p = 0.0001). No
threshold move and no retrain on this label set can fix it.

## How this was reached

The owner reported, unprompted, that the Thriving lens gives too many false
positives. Two production measurements over the last 12 cycles
(2026-08-18 12:52 → 08-20 08:59, 36,516 scored rows per lens, read from
`sadalsuud:~/local_dev/NexusMind/data/filtered/`):

| lens | surfaced at its op-point | share of corpus | primary literature, share of surfaced |
|---|---|---|---|
| **uplifting** @4.5 | 2,543 | **6.96%** | **13.6%** |
| solutions @2.25 | 1,443 | 3.95% | 1.2% |
| belonging @4.0 | 799 | 2.19% | 0.6% |
| cultural_discovery @4.0 | 614 | 1.68% | 12.5% |
| nature_recovery @3.75 | 42 | 0.12% | — |

Primary literature is **11.7% of scored-and-persisted rows** — ⚠️ **not of the
corpus.** `filtered_*.jsonl` is 100% passers by construction and also drops
source-type exclusions (~80 prefiltered + ~78 source_filter per cycle against
~2,742 scored, so ~5% of input sits outside it at an unmeasured rate), and the
baseline is unstable across two reasonable constructions: 4,273/36,516 = 11.7%
counting rows with a score, 4,722/37,022 = 12.8% counting every row in the file.
**The cross-lens contrast is what carries the argument, not the baseline** — all
four lenses persist the same article set under the same construction and none
excludes `academic` source types (only `investment_risk v6` does). `belonging`
and `solutions` **deplete** it (0.6%, 1.2%); `uplifting` **enriches** it (13.6%).
Source of the stamp: `metadata.primary_literature.detected`, present on 100% of
rows — the same stamp NexusMind's academic dedup gate reads (NM#392).

`uplifting` also surfaces 3–7× more of the corpus than any other ovr lens. 36% of
that volume sits in the band 4.5–5.0 (915 distinct titles in two days), which on
a 40-row sample is dominated by research abstracts, administrative notices and
off-lens filler.

## The measurement that settles it

Held-out oracle test split, `datasets/training/uplifting_v7/test.jsonl`, n=660.
The weighted average is re-derived from the deployed `DIMENSION_WEIGHTS`, so
**nothing here involves the model**. On-lens is the gate's own truth cut, oracle
weighted ≥ 4.0.

```
oracle >= 4.0:  216/660 (32.7%)   <- reproduces the ADR-021 gate's positive set

  academic-source rows   32/ 58 =  55.2% on-lens
  everything else       184/602 =  30.6% on-lens
  difference +0.246   permutation p = 0.0001 (one-sided, N=20000, seed=11)
```

Per-source, `pubmed` is the **highest-scoring source in the split** at 77.8%
(7/9) — more than twice the base rate. `science_arxiv_cs` is 38.5% (5/13). Both
n are small; the 58-row aggregate is the number to quote.

### Which dimensions carry it — this is the mechanism

```
    dimension                  w      acad   other   delta
    human_wellbeing_impact   0.30     4.55    2.84   +1.71
    social_cohesion_impact   0.20     2.04    2.38   -0.34
    justice_rights_impact    0.15     2.11    2.64   -0.53
    evidence_level           0.10     4.76    2.92   +1.84
    benefit_distribution     0.10     3.59    2.83   +0.77
    change_durability        0.15     3.93    2.87   +1.06
```

**The four dimensions a competent method paper maximises carry 65% of the weight.
The two that encode "for people" carry 35%, and are the only two where academic
rows score LOWER.** 35% of weight cannot pull a total below 4.0 when the other
65% is elevated, so the arithmetic admits the genre by construction.

Oracle labels from the split, verbatim titles, all at or above the op-point:

| oracle | source | title |
|---|---|---|
| 6.00 | pubmed | RoentMod: a synthetic chest X-ray modification model… |
| 5.75 | science_arxiv_cs | AudAgent: Automated Auditing of Privacy Policy Compliance in AI Agents |
| 5.05 | science_biorxiv | Evaluating genome assemblies with HMM-Flagger |
| 5.05 | science_frontiers_medicine | A dual-branch deep learning framework with Mask-Guided Attention… |

## Where it is in the prompt

`filters/uplifting/v7/prompt-compressed.md`. Four sites, in descending order of
how much each one costs:

1. **Contrastive Example 5 anchors the genre at ~6.7.** *"Open-source medical AI
   (global, verified)"* → wellbeing 8.0, evidence 8.0, reach 9.0, durability 8.0,
   overall **6.7**. A medical/AI method abstract is a near-exact match to this
   anchor, and the calibration table is the strongest signal in an ADR-010 prompt.
2. **`evidence_level`'s top bands describe what a paper IS.** 7.0–8.0 is
   *"Peer-reviewed data… multiple independent sources"*; 9.0–10.0 is
   *"Meta-analyses, independent verification, replicated results"*. The dimension
   added in v7 to stop rewarding journalism quality now rewards **genre** instead
   — measured at **+1.84**, the largest single delta. Worse, it is the
   **GATEKEEPER**: the one dimension that can cap the overall score is the one the
   genre maximises, so the restraint never engages.
3. **IN SCOPE admits preprint servers directly.** *"Knowledge freely shared (open
   access, public education, citizen science)"* — arXiv, bioRxiv and medRxiv are
   open-access knowledge sharing on a literal reading.
4. **The OUT OF SCOPE line that should have caught it cannot.** *"Technical
   achievement alone — faster APIs, better code, new products **without wellbeing
   impact**"*. A health or medical method paper always asserts a wellbeing impact,
   so the qualifier exempts exactly the sub-genre that dominates the flagged rows.
   Pre-classification flags A–E (corporate finance, military, speculation, doom,
   individual crime) have **no research-artefact case**.

## What this rules out

- **Raising the op-point.** Already swept to 5.00 on 2026-08-10
  (`2026-08-10-uplifting-v7-threshold-sweep-102.md`) and **blocked above 4.5
  regardless**: `MAX_NORMALIZATION_RAW_MIN = 4.5`
  (`scripts/normalization/fit_normalization.py:61`) and the production loader
  rejects a fit above it, falling back to `score_scale_factor` with no symptom but
  a log line. 4.5 already sits on the bound with zero margin. Even ignoring the
  guard, 4.5 → 5.0 buys 1.57pp of FPR for 13.4pp of recall — a far worse trade
  than 4.0 → 4.5 was.
- **Retraining on the existing labels.** The labels are the thing that is wrong.
  A perfect student reproduces the bias exactly.

## What it does not establish

- **The academic/non-academic split in the script is a pattern list over source
  names**, not the `primary_literature` stamp (absent on training rows). On
  production rows the two instruments disagree — the pattern list read
  cultural_discovery at 36.3% where the stamp says 12.5%, because `science_*` and
  `healthcare_*` are source *groups* containing science journalism. **The
  direction is the finding; treat the magnitude as approximate.**
- **`n=58` academic rows.** The aggregate effect is strong (p = 0.0001) but no
  per-source rate in this split is worth quoting on its own.
- **Whether research abstracts are the LARGEST false-positive class.** They are
  13.6% of surfaced volume, so at most that. The 4.5–5.0 band also holds
  administrative notices and off-lens filler, unquantified — the sample was 40
  titles, eyeballed, not adjudicated.
- **That `filtered_*.jsonl` is the reader population.** It is a superset;
  `getArticlesForBuild` is the reader path (`memory/nexusmind-data-sources.md`).
  "Surfaced" here means raw ≥ op-point, the ADR-022 visibility rule.
- **`cultural_discovery` at 12.5% primary literature** is the same shape and was
  not investigated. It has its own evidence dimension and its own gatekeeper.

## Consequence

This is the specification for **v8 `human_thriving`** (the ADR-012 rename, now
load-bearing). It must be a **prompt change plus a re-score**, and it should be
written against ovr.news's narrowed Thriving predicate — *a process going well
**for people*** (ovr `BRAND.md` `a70609b`) — which is carried by precisely the two
dimensions the current oracle down-weights.

Related: **#91** (the same filter scoring narrative fragments rather than the
dominant subject) is a second symptom of one root cause — the prompt scores
*attributes present in the text* rather than *what the article is about*.
