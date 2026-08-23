# The v7 corpus was never prefiltered — and it is missing the class-A shape

**Measured 2026-08-22/23.** Raw logs: `docs/evidence/2026-08-22-hcv1-runs/`.
Scripts: `scripts/analysis/prefilter_removal_probe.py`, `prefilter_march_probe.py`,
`corpus_census.py`, `production_census.py`.

Two questions, answered in sequence. The second only became askable once the first
was settled, and the second is the one that changes the v8 plan.

---

## Q1 — did the keyword prefilter deplete the corpus of harm content? (H-CV1)

### Why the 2026-08-21 attempt could not answer it

It counted crime-violence matches **inside the corpus** (4.70%) and compared them to
production (3.26%). Invalid: the corpus is supposedly what *survived* the prefilter, so
its matching rows are **override survivors**. Measuring survivors measures the leak, not
the removal. Checker and checked were the same object.

### Design

Three arms. The decision function carried an identical fingerprint
(`938302d84050047a`) across arms A and B, so the same logic provably ran on both.
Every arm ran a **positive control first** — three articles that must be blocked, one
that must pass — because a zero from a blind instrument is indistinguishable from a
real zero.

Production is a valid instrument here for one specific reason: the per-lens prefilter
**has never executed in the production scoring path** (NM#284, dead since 2026-02-10),
so that population was not selected by the filter under test.

| arm | population | instrument | blocked |
|---|---|---|---|
| **A** | 235,905 production rows, 87 files, `filtered_20260808_170651`..`filtered_20260822_164733` | today's prefilter | **6.917%** |
| **B** | 6,590 v7 corpus rows (gpu-server) | today's prefilter | **9.074%** |
| **C** | the same 6,590 | **the March-2026 prefilter** (`991ffec`) | **15.493%** |

⭐ **Arm C is the one that settles it, and arm B alone would have been worthless.** The
corpus files are dated **2026-03-11**; `prefilter.py` was created **2026-03-09** and has
changed **four times since** (`3a688a3`/`d0916f4`/`ba03a75` 04-29 — declarative migration,
`\b` boundaries, base hoist; `623ea51` 07-27 branded content; `4d17e75` 08-03 length floor
removed by #93). Running today's version over a March corpus cannot establish what the
March version did.

### Result — the prefilter never ran

The March prefilter blocks **1,021 of the 6,590 rows (15.493%)**:

| reason | rows | share |
|---|---|---|
| crime_violence | 350 | 5.311% |
| military_security | 313 | 4.750% |
| corporate_finance | 188 | 2.853% |
| content_too_short | 114 | 1.730% |
| excluded_domain_code | 38 | 0.577% |
| excluded_domain_vc_startup | 9 | 0.137% |
| pure_speculation | 9 | 0.137% |

**Those 1,021 rows are in the training splits.** Had the prefilter run at build time they
could not be. A corroborating mechanism exists in code: `ground_truth/batch_scorer.py:1615`
carries a legacy `--prompt` mode marked **"NO PREFILTER SUPPORT"**. A second, independent
corroboration: the March prefilter enforced a 300-char floor inside `apply_filter`, and the
corpus contains rows as short as **35 characters**.

**H-CV1: REFUTED, and its premise with it.** With the same instrument on both sides the
corpus is *not* depleted — crime-violence matches **2.72%** of the corpus against **2.38%**
of production.

⛔ **Therefore `HUMAN_THRIVING_V8_PLAN.md` §Phase 0's claim — "the 6,590 rows were selected
with 74 Latin-script patterns applied" — is FALSE.** Corrected in the plan.

### Two corrections carried out of this

- The prefilter has **77** patterns (corporate_finance 21, military_security 19,
  **crime_violence 37**), not "74 … including 36".
- `corporate_finance` and `military_security` each block **more** than crime_violence, so
  the keyword-shaping story was never only about harm.

### Ruling 3 is untouched, and now has a number

It rests on multilingual coverage, which arm A measured directly. The prefilter is not
"Latin-script only" — it is a **four-language** instrument (EN/NL/DE/FR = **74.9%** of
production). The remaining **25.1% receives essentially no lens prefiltering**:

| lang | rows | removal | crime_violence match |
|---|---|---|---|
| fr | 9,366 | 11.86% | 7.60% |
| en | 145,993 | 8.89% | 2.86% |
| de | 14,454 | 8.44% | 2.30% |
| nl | 6,805 | 6.79% | 4.06% |
| **es** | **16,390** | **0.89%** | **0.05%** |
| it | 3,103 | 0.74% | 0.03% |
| ar | 3,471 | 0.06% | 0.06% |
| ko | 2,213 | 1.36% | **0.00%** |

Spanish is the second-largest language and is filtered **10× less** than English.

---

## Q2 — is the corpus a good corpus? (the question that actually matters)

H-CV1 being refuted does **not** clear the corpus. It closes one mechanism (removal) and
says nothing about **composition**. Owner, 2026-08-22: *"I do not want a keyword prefilter
anymore, and I want a proper data corpus to train on. It is my belief that the corpus
partly determines the quality of the result."* Measured, that belief holds.

⚠️ **A methodological correction inside this file.** Q1 counted crime-violence keywords
**anywhere in the body**. Class A needs harm to be the **dominant subject**, which is a
different quantity. Q2 therefore matches on the **title**.

### (a) The class-A shape is nearly absent

| | corpus (6,590) | production (205,939, stage2 only) |
|---|---|---|
| harm as dominant subject (title) | **30 (0.46%)** | 1,798 (0.87%) |
| …labelled/scored ≥ 4.5 | 4 (13.3%) | 91 (5.1%) |
| …labelled/scored < 3.85 | **25 (83.3%)** | 1,663 (92.5%) |

⭐⭐ **The corpus carries 25 rows teaching "harm story → score low."** Twenty-five, against
6,590. The shape is **1.9× under-represented** versus production. Nothing removed it — it
was never assembled in.

⚠️ **The 4 high-labelled rows are not defect-teaching.** They are restorative-justice
stories — a Brussels-attack survivor meeting the perpetrator in prison (6.55, and its
Dutch duplicate at 6.60), a $30M abuse settlement (5.85), a Myanmar amnesty (5.38). These
are the §5b shape the plan protects. **A supplement of FPs only would destroy them.**

⚠️ **Class A is a rare, expensive tail, not a bulk failure.** The student scores 92.5% of
harm-title rows below 3.85. The damage is **91 rows above the op-point in 14 days (~6.5/day)**
— exactly the ADR-023 asymmetry: a false positive reaches a reader.

### (b) Representativeness — four gaps

| | corpus | production | gap |
|---|---|---|---|
| **positive base rate (≥4.5)** | **28.22%** (1,860) | **7.74%** (15,935) | **3.6× enriched** |
| non-Latin script | 4.57% (301) | 7.26% (14,954) | 1.6× under |
| median content length | 2,658 ch | 1,349 ch | 2× longer |
| distinct domains / top-10 share | 697 / 16.2% | 1,389 / 37.2% | corpus more diverse |

⭐⭐ **The base rate is the largest defect.** The student is trained where positives are
~28% and serves where they are ~8%, which biases it toward predicting positive — the
expensive error under ADR-023.

⚠️ **This does NOT mean "match production."** ADR-003 screen+merge enrichment exists
*because* positives are rare; sampling at 7.74% spends most of the oracle budget on obvious
negatives. The defect is that 3.6× is **accidental and unstated**, not that enrichment is
wrong. Make it a chosen, recorded number and correct for it.

⚠️ Length matters more than it looks: every class-A row in the plan is a long article
(2,107–5,786 ch) and the corpus median is 2× production's. Production `p10 = 84 ch`. The
short-form regime is under-trained.

### A finding that cuts the other way, and is useful

The corpus **under**-represents primary literature: **arxiv.org 4.23% / pubmed 2.05%**
against production's **arxiv 7.92% / pubmed 0.83%**. So **class B (academic register) is
not a corpus-composition problem** — it is a prompt problem, exactly as #125 concluded.
The two defect classes have genuinely different causes, which is why one prompt rewrite
cannot be the whole of v8.

*(Production's top source is `news.google.com` at 22.44% — headline echoes that must never
be oracle-re-scored. Any production draw excludes them, so production percentages here are
not directly the percentages a rebuilt corpus should target.)*

---

## What this changes

1. **The rebuild is justified — but not by depletion.** Four measured reasons: base rate,
   class-A shape, non-Latin share, length distribution.
2. **The rebuild will not, on its own, fix class A.** The shape is absent, so supplementing
   it is necessary; but the student also fails on rows all three oracles get right (§1f),
   and no corpus change reaches that. **Phase B2 hard negatives stays load-bearing.**
3. **Class B is a prompt defect.** Do not spend corpus budget on it.
4. **The central mystery is unchanged and still open:** the student saw 350 harm rows
   (March reckoning), labelled conservatively, and still scores a torture story at 5.98.
   Every explanation offered so far has died under measurement, two of them mine.
