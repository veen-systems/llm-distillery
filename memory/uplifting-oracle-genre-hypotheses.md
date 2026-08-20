---
name: uplifting-oracle-genre-hypotheses
description: Why the Thriving lens over-surfaces research abstracts — the defect is in the ORACLE LABELS, not the student. Hypotheses H-UP1..H-UP6, the measurements, and the shadow instrument now stamping in NexusMind.
metadata:
  type: project
---

# uplifting v7 / Thriving — oracle genre bias (#125)

**Opened 2026-08-20** from an owner observation: *"the thriving lens gives too many
false positives."* Full evidence:
`docs/evidence/2026-08-20-uplifting-v7-oracle-genre-bias.md`.
Reproduce: `PYTHONPATH=. python3 scripts/analysis/uplifting_v7_genre_bias.py`

⛔ **This was NOT a new finding.** `datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md`
already recorded it ten days earlier — *"the dominant failure class among the 21 is
academic-abstract register — 9 of 21, 43% ... That is a different fix from lens
de-confliction and it should be tracked as its own thing."* Nobody opened the thing.
**The lesson that travels: prior findings live in adjudication artifacts too, and no
index points at `datasets/adverse/`.** Checking `memory/` and the issue tracker is not
checking prior work.

## Hypotheses

| id | claim | verdict |
|---|---|---|
| H-UP1 | the Thriving false positives are the STUDENT drifting from its labels | **REFUTED** — measured on the labels alone, no model involved |
| H-UP2 | the ORACLE PROMPT itself rates research artefacts as on-lens | **CONFIRMED** — 55.2% vs 30.6%, permutation p = 0.0001 |
| H-UP3 | raising the op-point would fix it | **REFUTED, and blocked anyway** |
| H-UP4 | research abstracts are the dominant false-positive class | **PARTIAL** — bounded at 13.6% of surfaced volume |
| H-UP5 | active learning on the CURRENT prompt would reinforce the bias, not remove it | ⏳ **OPEN — prediction, untested** |
| H-UP6 | a `primary_literature` cap removes the class without collateral damage | ⏳ **OPEN — shadow instrument shipped, no data yet** |

## H-UP1 / H-UP2 — the defect is in the labels

Held-out oracle test split, `datasets/training/uplifting_v7/test.jsonl`, n=660. The
weighted average is re-derived from the deployed `DIMENSION_WEIGHTS`, so the student is
not in the loop. On-lens is the ADR-021 gate's own cut, oracle weighted ≥ 4.0
(reproduces its 216/660 positive set exactly).

```
  academic-source rows   32/ 58 =  55.2% on-lens
  everything else       184/602 =  30.6% on-lens
  difference +0.246   permutation p = 0.0001 (one-sided, N=20000, seed=11)
```

**Mechanism — the weight arithmetic admits the genre by construction:**

| dimension | weight | acad | other | delta |
|---|---|---|---|---|
| human_wellbeing_impact | 0.30 | 4.55 | 2.84 | **+1.71** |
| social_cohesion_impact | 0.20 | 2.04 | 2.38 | −0.34 |
| justice_rights_impact | 0.15 | 2.11 | 2.64 | −0.53 |
| evidence_level | 0.10 | 4.76 | 2.92 | **+1.84** |
| benefit_distribution | 0.10 | 3.59 | 2.83 | +0.77 |
| change_durability | 0.15 | 3.93 | 2.87 | +1.06 |

The four dimensions a competent method paper maximises carry **65%** of the weight; the
two that encode *"for people"* carry **35%** and are the only two that fall.

Four sites in `filters/uplifting/v7/prompt-compressed.md`, worst first:
1. **Contrastive Example 5** anchors *"Open-source medical AI (global, verified)"* at
   overall **6.7**.
2. **`evidence_level`'s top bands describe what a paper IS** (7–8 *"peer-reviewed data"*,
   9–10 *"meta-analyses, independent verification, replicated results"*). It is also the
   **GATEKEEPER**, so the only dimension that could cap the total is the one the genre
   maximises — the restraint never engages.
3. **IN SCOPE** admits preprint servers: *"Knowledge freely shared (open access …)"*.
4. **OUT OF SCOPE cannot catch it**: *"Technical achievement alone … **without wellbeing
   impact**"* — a health/medical paper always asserts one. Pre-classification flags A–E
   have no research-artefact case.

## H-UP3 — refuted and blocked

Already swept to 5.00 on 2026-08-10 (`docs/evidence/2026-08-10-uplifting-v7-threshold-sweep-102.md`).
⛔ **Blocked above 4.5 regardless**: `MAX_NORMALIZATION_RAW_MIN = 4.5`
(`scripts/normalization/fit_normalization.py:61`); the production loader rejects a higher
fit and falls back to `score_scale_factor` with no symptom but a log line. 4.5 already
sits on the bound with zero margin. Ignoring the guard, 4.5 → 5.0 buys **1.57pp of FPR
for 13.4pp of recall** — a far worse trade than 4.0 → 4.5 was.

## H-UP4 — bounded, not settled

13.6% of surfaced volume, so at most that. The 4.5–5.0 band (36% of surfaced volume,
915 distinct titles in two days) also holds administrative notices and off-lens filler,
**unquantified** — 40 titles eyeballed, not adjudicated.

## H-UP5 — the instrument shares the defect ⭐

**The active-learning grader IS the v7 oracle prompt** (2026-08-09 batch: 170 production
rows, 144 graded, gemini-flash — DeepSeek would not match a Gemini-fitted calibration).
So it can only surface rows where the *student* disagrees with the *oracle*. On this
genre the oracle is **inconsistent, not blind** — it rejected 9 academic abstracts in
that batch while rating academic rows on-lens at 55% overall. Active learning on the
current prompt therefore catches the subset the oracle rejects and **silently re-labels
the ~55% it accepts as positives.**

The genre concentrates exactly where that batch measured the worst precision:

| band | n (12 cycles) | primary literature | 2026-08-09 AL precision |
|---|---|---|---|
| 4.0–4.5 | 1,029 | **17.1%** | 0.571 |
| 4.5–5.5 | 1,670 | **17.3%** | 0.705 |
| ≥5.5 | 873 | 6.6% | 1.000 |

**Order is therefore prompt first, then active learning.** ADR-010 says prompt precision
beats dataset size, so a targeted 2–3K set stratified above the op-point should *replace*
the 5,271, not add to it. Oracle spend is not the constraint: cd v5's actual was $10.36
per 8K; Gemini Batch ≈ $14.40 per 8K; a full 6,590-row re-score ≈ **$12**. The cost is
adjudication time.

**Generalises beyond this filter: an instrument built from the thing under test cannot
audit it.**

## H-UP6 — the shadow instrument (shipped, no data yet)

`NexusMind/src/scoring/primary_literature_cap.py`, stamping from
`scripts/main.py` inside `run_filter`. **Stamp-only — there is deliberately no
enforcement branch**, because visibility is decided on **raw** (ADR-022) while
normalization already ran on gpu-server and NexusMind's existing `content_type_caps`
caps the **normalized** score (NM#280). Which an enforcement point should use is
unresolved, and this shadow is what resolves it.

⚠️ **It had to go in `main.py`, not in the filter package or `ProductionScorer._post_process`.**
`deploy/gpu-server/main.py` rebuilds the scorer payload as `{"title", "content"}`, so
`metadata.primary_literature` **never crosses the REST boundary**. Both earlier designs
would have read `None` on 100% of rows while passing every test.
**A serialization boundary is part of the call path** — 6th occurrence of
`feedback-verify-call-path`.

Offline replay over 12 cycles, before deploy:

| filter | detected | would cap | of those, surfacing | share of surfaced |
|---|---|---|---|---|
| uplifting | 4,273 | 1,562 | **347** | **13.6%** |
| cultural_discovery | 4,273 | 639 | 77 | 12.5% |
| belonging | 4,273 | 0 | 0 | 0% |
| solutions | 4,273 | 0 | 0 | 0% |

The two zeros are the scope gate working as a negative control.

**Measured null worth keeping:** this module's predicate (`is True`) is stricter than
`story_dedup._is_primary_literature`'s (`bool(...)`), which would split the shadow count
from the academic dedup gate's population. **0 divergent rows of 37,022** (32,300 False /
4,722 True). Bounded null, not a guarantee; verify command in the module docstring.

## ⛔ Traps

- **`filtered_*.jsonl` is not the corpus.** 100% passers by construction, and it drops
  source-type exclusions (~80 prefiltered + ~78 `source_filter` per cycle against ~2,742
  scored — ~5% of input at an **unmeasured** primary-literature rate). The baseline is
  also unstable across constructions: **11.7%** (4,273/36,516, rows with a score) vs
  **12.8%** (4,722/37,022, every row in the file). **The cross-lens contrast carries the
  argument, not the baseline** — all four lenses persist the same set under the same
  construction and none excludes `academic` (only `investment_risk v6` does).
- ⚠️ **The detector certification is a CITATION.** *"1.000 recall on arXiv/PubMed/trials,
  0.000 on Guardian/Ars/Smithsonian/STAT/ScienceAlert, 0 faults over 167,234 rows"* is
  quoted from `story_dedup._is_primary_literature`'s docstring. A grep across both repos
  returns only that docstring — **no evidence file, no verify command.**
- **The academic/non-academic split in the analysis script is a pattern list over source
  names**, not the stamp (absent on training rows). The two disagree on production rows
  (list 36.3% for cd, stamp 12.5%). Direction is the finding; magnitude is approximate.
- `scripts/run_filters.py` is a second path that persists `nexus_mind_attributes` without
  the stamp. Not in systemd, not called from `main.py`, and its own examples reference
  `sustainability_technology` — removed 2026-08-03. Legacy.

Related: [[uplifting-v7-training]], [[filter-status]], [[hypothesis-ledger]], #91, #125.
