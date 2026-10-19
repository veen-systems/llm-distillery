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

## H-UP7 ("class A is the same label defect as class B" ⛔ REFUTED: 1 of 3 rows fails on all three oracles, 2 of 3 are the STUDENT alone) — MOVED to [`archive/uplifting-oracle-genre-hypotheses-archive.md`](archive/uplifting-oracle-genre-hypotheses-archive.md) (2026-10-12)

## H-CV1 (⛔ REFUTED: the keyword prefilter never ran on the v7 corpus) — MOVED to [`archive/uplifting-oracle-genre-hypotheses-archive.md`](archive/uplifting-oracle-genre-hypotheses-archive.md) (2026-10-12)

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

## H-UP1 / H-UP2 (the defect is in the LABELS: 55.2% vs 30.6% on-lens, p = 0.0001; the weight arithmetic and the four prompt sites) — MOVED to [`archive/uplifting-oracle-genre-hypotheses-archive.md`](archive/uplifting-oracle-genre-hypotheses-archive.md) (2026-10-12)

## H-UP3 (⛔ REFUTED and blocked: `MAX_NORMALIZATION_RAW_MIN = 4.5`) — MOVED to [`archive/uplifting-oracle-genre-hypotheses-archive.md`](archive/uplifting-oracle-genre-hypotheses-archive.md) (2026-10-12)

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

**Order is therefore prompt first, then active learning** (ADR-010: a targeted 2–3K set stratified above the op-point should *replace* the 5,271, not add to it). The per-band primary-literature table and the superseded k=1 cost estimate — MOVED 2026-10-19 (#163 round 11) to `archive/uplifting-oracle-genre-hypotheses-archive.md` § *Moved 2026-10-19*.

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

Offline replay before deploy (uplifting would cap 347 surfacing rows = 13.6% of surfaced; belonging/solutions 0 as the negative control) and the 0-of-37,022 predicate-divergence null — MOVED 2026-10-19 to `archive/uplifting-oracle-genre-hypotheses-archive.md` § *Moved 2026-10-19*.

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

### H-UP11 (✅ CONFIRMED: the gatekeeper rewrite fixes class B) and H-UP12 as first written (REFUTED AS WRITTEN) — MOVED to [`archive/uplifting-oracle-genre-hypotheses-archive.md`](archive/uplifting-oracle-genre-hypotheses-archive.md) (2026-10-12)

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

### H-UP12 (✅ RESOLVED: "Gemini ignores step 1" was the wrong diagnosis) — MOVED to [`archive/uplifting-oracle-genre-hypotheses-archive.md`](archive/uplifting-oracle-genre-hypotheses-archive.md) (2026-10-12)

### ✅ H-UP14 and the accountability boundary — RULED 2026-08-23 (owner)

*"Money committed is not a protection established"* (funding pledged/mobilised scores as an announcement; Rwanda left the no-regression set), and BRAND.md's *"only"* makes the test **IS ANYONE BETTER OFF**, not "was it delivered". Full rulings verbatim — MOVED 2026-10-19 to `archive/uplifting-oracle-genre-hypotheses-archive.md` § *Moved 2026-10-19*.

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
