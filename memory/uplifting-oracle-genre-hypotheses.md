---
name: uplifting-oracle-genre-hypotheses
description: Why the Thriving lens over-surfaces junk. TWO classes — harm-adjacent (class A, the priority) and academic register (class B). H-UP1..H-UP9 + H-CV1; class A is partly a STUDENT defect, which no prompt reaches.
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
| **H-UP7** | **the harm-adjacent class (class A) is the same label defect as class B** | ⛔ **REFUTED 2026-08-20** — 3-oracle bake-off: **1 of 3 rows fails on all three oracles (label defect), 2 of 3 are the STUDENT alone**. No prompt change reaches those two |
| **H-UP8** | **class A is worse than class B for readers** | ✅ **CONFIRMED + owner-ruled 2026-08-20**, but ⛔ **its BAND ARGUMENT is falsified (2026-08-22)**. The ruling stands on reader harm. The numbers cited with it do not: class A tops at raw 6.846 / normalized **9.862** (*not* 8.28 — that was the max of the newly-promoted subset), and class B is **not** confined to 4.06–5.12 — two owner-flagged non-outcome rows score raw **7.359** and **6.901**, above every class-A row. **The classes differ by SHAPE, not by band.** Owner: *"the ones flagged by reader are actually far far worse"* |
| **H-UP9** | **Thriving's top-scoring rows are disproportionately ENRICHED STUBS rather than publisher-delivered full text** | ⏳ **OPEN — noted, not measured (owner ruling 5, 2026-08-22).** All 3 owner-flagged rows are stubs: `feed_summary`, `feed_summary` (76 words → 2,638 ch), `headline_only` (`word_count: 0` → 4,894 ch). ⛔ **Proves nothing — hand-built population**: they were selected *because* they looked wrong ([[feedback-hand-built-population]]). See below |
| **H-CV1** | **the keyword prefilter depleted the v7 corpus of harm content, which is why the student fails on class A** | ⛔ **REFUTED 2026-08-22, premise and all — the prefilter NEVER RAN on this corpus.** The March-2026 version blocks **15.493%** (1,021/6,590) of the corpus it supposedly built. See below |
| **H-UP10** | **the corpus is unrepresentative of production, and that is why the student fails** | ⏳ **OPEN, and now the leading candidate.** Four gaps measured 2026-08-22: positive base rate **28.22% vs 7.74%** (3.6×), class-A shape **0.46% vs 0.87%** (1.9× under, only **25** rows teach the fix), non-Latin **4.57% vs 7.26%**, median length **2,658 vs 1,349 ch**. Untested as a *cause* |

## H-UP9 — are the top Thriving rows enriched stubs? OPEN, and deliberately unmeasured

**Registered 2026-08-22, owner ruling 5: *note it, measure later*.** Not part of Phase A.

Observation, n=3, all owner-flagged from the live lens:

| article | `content_meta.kind` | publisher delivered | scored on | raw |
|---|---|---|---|---|
| Dawn, "Curing the cause" | `feed_summary` | 7,194 ch | 6,737 ch | 7.359 |
| TSA, Algerian doctor | `feed_summary` | 485 ch (76 words) | 2,638 ch (`pre_enriched`) | 6.901 |
| ToI, Helsinki heat caverns | `headline_only` | **0 ch, `word_count: 0`** | 4,894 ch (`pre_enriched`) | 6.648 |

⛔ **This is not evidence and must not be quoted as a rate.** The owner picked these three
because they looked wrong on the page, so the population is selected on the outcome —
exactly [[feedback-hand-built-population]], the shape behind every measurement error this
project has made. Three for three is what a hand-picked set of three looks like.

**How to test it properly, when it is time:** take *all* Thriving rows at or above the 4.5
op-point over a stated window, and compare the `content_meta.kind` / `pre_enriched`
distribution against **all scored rows in the same window** — a pipeline-computed
denominator, both sides from the same instrument. Report the window and the file count
(the archive grows every 4h cycle). ⚠️ Condition on `stage_used` first: a `stage1_low` row's
score is an e5 probe estimate, not a Gemma score.

⚠️ **Predict the range before looking.** Enrichment is documented as *beneficial* on
evidence-quality dimensions (H-E1, `memory/enrichment-delta-hypotheses.md`: `cultural_discovery`'s
`evidence_quality` **+1.433**, 46/47 rows positive), so a plausible prior is that enriched
rows score *higher everywhere* and Thriving is not special. **A finding that enrichment
inflates Thriving specifically needs a non-Thriving control lens**, or it is just H-E1 again.

## H-UP7 — class A is BOTH a label defect and a student defect ⭐⭐

**Measured 2026-08-20.** `docs/evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md`.
Reproduce: `scripts/analysis/valence_bakeoff.py` (three arms; reproduce steps in its header).

Three oracles, same v7 prompt, same text, bar `max_acceptable_wa` = 3.85:

| article | student | Gemini | DeepSeek | qwen3:14b | reading |
|---|---|---|---|---|---|
| Five men arrested … raping a minor | 6.85 | **7.62** | **6.25** | **7.30** | all three fail — **label defect** |
| Greyhounds / NZ racing ban | 5.86 | 2.30 | 3.95 ⚠️ | 2.00 | oracles right, **student is the outlier** |
| Rethink Business Centre Management | 6.09 | 1.55 | 1.80 | 4.35 | oracles right, **student is the outlier** |

⚠️ 3.95 is 0.10 over the bar — inside ±0.16, indeterminate. ⚠️ n=3.

⛔ **Consequence: a prompt-only v8 fixes about a third of class A.** The residue needs
playbook §4b hard negatives, at $0 oracle cost. This is why `docs/HUMAN_THRIVING_V8_PLAN.md`
carries a Phase B2 at all.

⚠️ **A FOURTH noise floor, and it invalidates single-run gates.** Same oracle, same prompt,
same article, 10 days apart: **mean |Δ| 0.82, max 2.25** (n=7) — 5× the #95 batch floor.
**A single-run oracle score is not a measurement.** Every oracle-side acceptance gate must
be a k-run mean with a stated band. (`feedback-noise-floor-per-population`: a floor belongs
to a population and a mechanism, not to a project.)

⭐ **Vendor choice is second-order.** Gemini fires caps 3/10 vs DeepSeek 1/10 vs qwen3 0/10
over all ten rows — replicating the `cultural_discovery v5` result (Gemini 60% / DeepSeek
26%) on a different filter and prompt. But the worst row fails on **all three**, and the
smallest pairwise gap (0.18) sits inside the 0.82 noise. **Build strictness into the
mechanism, not the purchase order.**

## H-CV1 — did the keyword prefilter deplete the corpus? ⛔ REFUTED — it never ran

**Full write-up: `docs/evidence/2026-08-22-uplifting-v7-corpus-provenance.md`.** Raw logs:
`docs/evidence/2026-08-22-hcv1-runs/`. Reproduce:
`scripts/analysis/prefilter_removal_probe.py` (today's rules),
`scripts/analysis/prefilter_march_probe.py` (the rules that existed at corpus build time).

**The tempting story:** `uplifting v7`'s prefilter carries **37 `crime_violence` patterns**
(*not* 36 — the file has **77** patterns total, not 74), class A is harm-adjacent, so perhaps
the student never learned the shape.

### The answer, and it is upstream of the question

The corpus files are dated **2026-03-11**. `prefilter.py` was created **2026-03-09** and has
changed **four times since**. Running today's rules over a March corpus settles nothing, so
the March version (`991ffec`) was checked out of git and run:

| arm | population | instrument | blocked |
|---|---|---|---|
| A | 235,905 production rows | today's prefilter | 6.917% |
| B | 6,590 corpus rows | today's prefilter | 9.074% |
| **C** | the same 6,590 | **March-2026 prefilter** | **15.493% (1,021 rows)** |

**Those 1,021 rows — 350 of them `crime_violence` — are in the training splits.** A filter
that had run would have removed them. Corroborated twice over: `batch_scorer.py:1615` carries
a legacy `--prompt` mode marked **"NO PREFILTER SUPPORT"**, and the March prefilter enforced a
300-char floor while the corpus contains rows of **35 characters**.

Same instrument both sides, the corpus is **not depleted**: crime-violence matches **2.72%**
of the corpus vs **2.38%** of production.

⛔ **`HUMAN_THRIVING_V8_PLAN.md` Phase 0's "the 6,590 rows were selected with 74 Latin-script
patterns applied" is FALSE.** Corrected there 2026-08-22.

### Why the 2026-08-21 measurement could not have answered it

It inspected corpus rows that *matched* `crime_violence` — but those are **override survivors**
of the filter under test, so it measured the override leak, not removal. Checker and checked
were the same object. *(That objection also dissolves once the filter is shown never to have
run: 112 rows it blocks are present.)*

⚠️ **Ruling 3 (drop the prefilter) never depended on this** and is unaffected. It rests on
coverage, now quantified: the prefilter is a **four-language** instrument (EN/NL/DE/FR =
**74.9%** of production). Spanish — the 2nd-largest language, 16,390 rows — is filtered at
**0.89% against English's 8.89%**; Korean and Croatian match `crime_violence` at **0.00%**.

### ⚠️ What refuting H-CV1 does NOT buy

It closes **removal**. It says nothing about **composition** — see **H-UP10**, which is where
the corpus argument actually lives, and which survived measurement.

## H-UP10 — is the corpus unrepresentative? ⏳ OPEN, leading candidate

**Measured 2026-08-22**, same evidence file. Owner: *"I want a proper data corpus to train on.
It is my belief that the corpus partly determines the quality of the result."*

⚠️ **Method note:** H-CV1 matched harm keywords **anywhere in the body**. Class A needs harm
to be the **dominant subject**, so this matches on the **title** — a different quantity, and
the body figure (2.72%) must not be quoted for this question.

| | corpus (6,590) | production (205,939 stage2) | gap |
|---|---|---|---|
| harm as dominant subject | **0.46%** (30) | 0.87% (1,798) | 1.9× under |
| …of those, teaching the FIX (< 3.85) | **25 rows** | 1,663 | — |
| **positive base rate (≥ 4.5)** | **28.22%** | **7.74%** | **3.6× enriched** |
| non-Latin script | 4.57% | 7.26% | 1.6× under |
| median content length | 2,658 ch | 1,349 ch | 2× longer |

⭐⭐ **25 rows are the entire training signal for class A.** Nothing removed them; they were
never assembled in.

⚠️ **The 4 harm-title rows labelled ≥4.5 are NOT defect-teaching** — restorative-justice
stories (Brussels survivor meets perpetrator 6.55, $30M abuse settlement 5.85, Myanmar amnesty
5.38). **A supplement of false positives only would destroy the §5b no-regression set.**

⚠️ **Base rate is the biggest gap and "match production" is the WRONG fix.** ADR-003
screen+merge enrichment exists because positives are rare; drawing at 7.74% spends the oracle
budget on obvious negatives. The defect is that 3.6× is **accidental and unstated**.

⭐ **Cuts the other way for class B:** the corpus *under*-represents primary literature
(arxiv **4.23%** / pubmed 2.05% vs production's arxiv **7.92%** / pubmed 0.83%). **Class B is
a prompt defect, not a corpus defect** — consistent with #125. Do not spend corpus budget on it.

⛔ **Still untested as a CAUSE.** These are composition gaps, not a demonstrated mechanism for
the class-A failure. The student saw 350 harm rows (March reckoning), conservatively labelled,
and still scores a torture story at **5.976** (normalized 8.284). **Every explanation offered
so far has died under measurement, two of them mine.** A rebuild is justified by the gaps; it
is **not** established that it fixes class A, which is why Phase B2 stays load-bearing.

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
per 8K; Gemini Batch ≈ $14.40 per 8K; a full 6,590-row re-score ≈ **$12** ⛔ *(k=1 estimate, SUPERSEDED 2026-08-29 — measured k=3 is ≈$6.9 reordered / ≈$21.7 as-is; `docs/evidence/2026-08-29-v8-phase-a-k3/`)*. The cost is
adjudication time.

**Generalises beyond this filter: an instrument built from the thing under test cannot
audit it.**

## H-UP6 — the shadow instrument (shipped, no data yet)

`NexusMind/src/scoring/primary_literature_cap.py`, stamping from
NexusMind's `scripts/main.py` inside `run_filter`. **Stamp-only — there is deliberately no
enforcement branch**, because visibility is decided on **raw** (ADR-022) while
normalization already ran on gpu-server and NexusMind's existing `content_type_caps`
caps the **normalized** score (NM#280). Which an enforcement point should use is
unresolved, and this shadow is what resolves it.

⚠️ **It had to go in NexusMind's `scripts/main.py`, not in the filter package or `ProductionScorer._post_process`.**
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
- NexusMind's `scripts/run_filters.py` is a second path that persists `nexus_mind_attributes` without
  the stamp. Not in systemd, not called from `scripts/main.py`, and its own examples reference
  `sustainability_technology` — removed 2026-08-03. Legacy.

Related: [[uplifting-v7-training]], [[filter-status]], [[hypothesis-ledger]], #91, #125.

---

## 2026-08-23 — Gate A measured on TWO oracles ($0.4711)

Evidence: `docs/evidence/2026-08-23-gate-a-two-oracle-run.md`. 15 rows × k=3 × 2 prompts ×
2 oracles, 0 errors. Prompt arms: `filters/uplifting/v7/prompt-compressed.md` vs
`filters/human_thriving/v8/prompt-candidate.md` (Phase A steps 1 + 2b spliced).

### ✅ H-UP11 CONFIRMED — the gatekeeper rewrite (step 2b) fixes class B

Class B **1/3 → 3/3 on both oracles**. The two owner-flagged rows of 08-22 collapse:
Dawn 5.98 → **3.00** (DeepSeek) / 7.36 → **1.60** (Gemini); TSA appointment 4.63 → **2.53** /
5.53 → **0.00**. The `3.00` is `GATEKEEPER_CAP` firing, exactly as §1h predicted.
⚠️ **Directional only: 3 of 9 class-B rows** — the other 6 could not be hydrated (aged out).

### ⚠️ H-UP12 REFUTED AS WRITTEN — a prompt rule is not a rule both oracles follow

Class A improves (4/9 → **7/9** DeepSeek, 4/9 → **6/9** Gemini) and does not clear. The
finding is the **disagreement**: *"Five men arrested for raping a minor"* goes
**7.05 → 3.00 on DeepSeek** (capped) and **7.23 → 7.43 on Gemini** (*rises*) — a **4.4-point**
gap on the most reader-offensive row in the set. Step 1's text names "individual
arrest/sentencing" explicitly; DeepSeek applies it, Gemini ignores it.
⭐ **Consequence: this decides Phase B's open oracle question.** A prompt-only fix is only as
good as the oracle's willingness to follow it.

### ⛔ H-UP13 — acceptance criterion 2's bars are broken, and **v7 proves it**

v7 *also* fails the no-regression set (1/3 DeepSeek, 2/3 Gemini). **A criterion the incumbent
fails is a broken criterion, not a failing candidate.** Against bars with evidence behind them:
Rappler passes both (⚠️ DeepSeek's 4.65 sits 0.15 over the op-point inside a 0.543 spread —
**indeterminate**); Unifesp passes its **delta** on both (+0.77, +0.13) ⇒ **transitional
justice is NOT suppressed**.

### ⛔ H-UP14 OPEN — v8 caps the Rwanda row on both oracles, exactly as written

Rwanda–EU $46M → **3.00 on both**. v8 is behaving *correctly*: mobilised funding is
**announced, not delivered**, which step 2b Shape 2 catches by design. Either §5b
mis-adjudicated the row, or the rule over-reaches on development finance. **Owner call**, and
it is the same boundary as the open delivered-accountability question: *what counts as
delivery.*

### ⛔ Traps found the hard way

- **All 18 adverse rows on disk are 300-char excerpts** (originals 620–28,905). Scoring them
  tests **ledes, not articles** — fatal where class A turns on the *dominant subject*.
  Hydrate from `ovr.db`'s `articles` table; class A is complete 9/9 there.
- **`gemini_api_key` is FREE-TIER.** First run: 429 RESOURCE_EXHAUSTED, 14/45 and 8/45
  succeeded, and **k=3 silently became k=1 on 8 articles** — a partially-populated result set
  that still looks like a run. Use `gemini_billing_api_key`.
- ⛔ **`grep -rl <article_id>` returned three files not containing the article** — the id
  appeared inside a *different* row's `nexus_mind_attributes` as a cluster co-member. A grep
  for a string is not a grep for a row.
- ⛔ **A local judge must clear the no-regression set before its verdict means anything.**
  `qwen3:14b` zeroed class A *and* all three true positives (spread 1.700 mean / 2.950 max);
  `qwen2.5:14b` is 4.4× tighter (0.383 / 0.650) and clears one assertion. Model-specific,
  not "local judges".

---

## 2026-08-23 evening — H-UP12 RESOLVED, H-UP14 RULED, and the diagnosis was wrong

Evidence: `docs/evidence/2026-08-23-step1-rewrite-r2-r3.md`. Two Gate A re-runs of the **v8 arm
only** (the v7 control file is untouched; its numbers are the earlier run). 45/45 both oracles,
0 errors, ≈**$0.47 estimated**.

### ✅ H-UP12 RESOLVED — and "Gemini ignores step 1" was the WRONG DIAGNOSIS

⭐⭐ **Step 1 was not ignored. It was OUTVOTED by five later instructions**, found by reading
**dimension-level** output instead of the weighted average: Gemini's v8 scores on the arrest row
were *identical to v7* (`evidence_level` **7.0 every run**, so the gatekeeper never got a
chance), and DeepSeek's "pass" came from step 2b alone — its non-evidence dims sat at 5–6.
**Step 1 fired on neither oracle.**

The six contradictions, five of them *after* step 1 in the prompt:

| where | what it said |
|---|---|
| `STEP 2` opening | *"Rate the six dimensions **COMPLETELY INDEPENDENTLY**"* — cancels "score ALL dimensions 0-2" |
| §4-D | the old `>50%` doom test → `max_score = 4.0` (step 1 §1 had deleted it) |
| §4-D exception | *"investigative journalism → score Justice normally"* |
| §4-E | individual crime → `max_score = 3.0`, laxer than 0-2 |
| §7 reminders 8–9 | restate both, in the **recency position** |
| output schema | recorded **no scope decision at all** |

⛔ **And every cap was inert.** `content_type` is emitted and consumed by nothing:
`filters/uplifting/v7/config.yaml:174` declares `content_type_caps`, **v7 ships no
`postfilter.py`**, and the only implementations (v1, v4) are imported by nothing. DeepSeek's
`3.00` looked like §4-E working; it was the **gatekeeper**. Two mechanisms sharing the constant 3.0.

**Fix:** all six, plus `dominant_subject` + `scope_verdict` as the **first two JSON keys** binding
every dimension, plus the **occasion test** (*the event that caused publication today; background
does not displace it; **length does not vote***).

**Result — class A 4/9 → 9/9 (DeepSeek), 4/9 → 8/9 (Gemini); class B 3/3 both.** The 4.4-point
disagreement is **closed**: arrest row **1.00 / 1.05**, both via `harm_is_subject` with
`gatekeeper_applied: False` — carried by the dimensions, the only channel any code reads.

⭐ **Unprompted side effect: run-to-run spread collapsed.** Gemini max **5.25 → 0.80**, DeepSeek
mean 0.543 → 0.237. Committing the verdict to an output field appears to *stabilise* the
judgement, not merely record it. One run each side — suggestive, not established.

### ✅ H-UP14 RULED (owner, 2026-08-23) — money is not a protection

> *"Money committed is not a protection established."* Funding secured, mobilised, pledged or
> allocated scores as an **announcement**, whatever the sum. A facility **operating**, a law
> **enacted**, a service **running** is a different thing. **Rwanda leaves the no-regression set
> as out-of-lens** — it was rejected as adverse and never had an observed production score.

### ✅ The accountability boundary RULED — and BRAND.md is more precise than the paraphrase

ovr.news `docs/BRAND.md` verbatim: *"…or a protection established that will improve them. It does not
qualify when the event **only** establishes that a harm occurred, or that one has been answered."*

⭐ **The word "only" means the test was never "was it delivered" — it is IS ANYONE BETTER OFF.**
A conviction reported as an event with no named beneficiary is still harm answered → 0-2. A
settlement **paid to survivors**, an amnesty that **releases people**, a restorative-justice
meeting **held**, remains **returned to families** are in — *because someone is better off*, not
because the process finished. My "arrest out, conviction in" reconciliation was slightly too
generous and is superseded.

### ⛔ Open — and the honest caveats

- **The accountability ruling has NO TEST.** The 15-row gate set contains no accountability row;
  re-running Gate A would not exercise it. Candidates for a control set are in `ovr.db`
  (*"Peruvian cardinal hails $150m lead poisoning settlement for 1,300 people"*, uplifting 6.80).
  ⚠️ Keyword-matched, contains at least one false match. **This is the oldest open debt.**
- **One class-A row still fails on Gemini** — *"Celebrated at birth, pushed into sex work"*
  (6.53). Gemini returns `in_scope` / *"the intergenerational practice of sex work in the
  Banchhada community"*; DeepSeek returns `harm_is_subject` / *"the exploitation of Banchhada
  women and girls"*. **Gemini adopts the article's own euphemism**, and neither the harm-event nor
  the occasion rule bites because there is no *event* — it is an ongoing condition. A rule for
  **harm as an ongoing practice or custom** is the r4 candidate; not written.
- ⚠️ **Unifesp fails its delta on Gemini (4.88 → 4.25, −0.63).** Not the occasion rule misfiring:
  all six r3 runs return `in_scope` with the right `dominant_subject`, so the **guard held**. The
  drop comes from the tightened IMPACT rubrics. Still 4.25 — above the bar and above ovr's 4.0
  enrichment gate.
- ⛔ **Three iterations against the same 15 rows is how a prompt overfits.** Read 9/9 and 8/9 as
  measured-on-the-training-set.
- ⛔ **A hypothesis of mine, refuted before publication:** that the arrest row was *mislabelled*
  from its 300-char excerpt (two thirds of the full article is a community campaign — exactly what
  Gemini named). The record says `labelled_by: editorial judgement (ovr.news owner) … **after
  full-text review**`. **The label stands; Gemini's reading was the error.**
- ⛔ **Leaked tool-call scaffolding** (`</content></invoke>`) removed from the v8 candidate. It is
  still in the **deployed** `filters/uplifting/v7/prompt-compressed.md`, so it has been appended to
  every uplifting v7 oracle label ever collected. Present in **both** arms, so it did not confound
  the comparison. Left in v7 deliberately — it is the baseline that produced those labels.
