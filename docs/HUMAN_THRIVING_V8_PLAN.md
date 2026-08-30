# `human_thriving` v8 — build plan

📓 **What has actually been DONE, step by step, with spend and evidence:**
[`docs/HUMAN_THRIVING_V8_JOURNAL.md`](HUMAN_THRIVING_V8_JOURNAL.md). This plan says what
v8 *will* be and is edited as rulings land; the journal says what happened and is
append-only. **A step that is not in the journal did not happen.**

**Drafted 2026-08-20. Revised 2026-08-21** (fourth revision — this plan has been rewritten
each time a measurement landed; read §0b for what changed and why).

**Status: DRAFT, nothing built.** `filters/human_thriving/v8/` does not exist. No oracle
spend committed. Blockers in §7.

---

## 0. What v8 is

**Four changes, not one.** An earlier draft of this section called v8 "a relabelling …
not a modelling change". That was wrong on three counts and is corrected here.

1. **A rewritten oracle prompt** — the labels encode a narrowed predicate (§1e) and a
   *signed* valence, because the current axis cannot express harm at all (§1a).
2. **A rebuilt corpus** — no per-lens keyword prefilter shaping it (ruling 3).
3. **A retrained Stage-1 probe** — the old one inherited the same keyword-shaped
   population, and it is now the only layer carrying the multilingual load (Phase C).
4. **Hard negatives in training** (§4b) — because part of the defect is the *student*, not
   the labels (§1f), and no prompt reaches that.

Plus the settled `uplifting` → `human_thriving` rename (§3), and a package brought up to
`nature_recovery v4` parity (§F1).

**Still NOT in scope:** a threshold move (§2), a re-weighting (§2), and any change to the
commerce / obituary / violence gates.

## 0a. ⛔ The honest state of the diagnosis

**Class A's mechanism is not established.** Read this before trusting any phase below.

- **Confirmed:** the Thriving lens surfaces harm-adjacent articles near the top of the feed
  — a torture story at raw 5.976, normalized **8.284** (§1g).
- **Confirmed:** on 3 class-A rows, the *oracle* is right on 2 and the *student* is wrong on
  all 3 (§1f). So this is not purely a label defect.
- ⛔ **SETTLED 2026-08-22 — H-CV1 is REFUTED and its premise with it: the prefilter never
  ran on this corpus.** The March-2026 version blocks **15.493%** (1,021/6,590) of the corpus
  it supposedly built, so those rows could not be there had it run. Same instrument both
  sides, the corpus is **not depleted** (crime-violence 2.72% corpus vs 2.38% production).
  Evidence: `docs/evidence/2026-08-22-uplifting-v7-corpus-provenance.md`.
- ⚠️ **But the corpus is still wrong, differently (H-UP10, OPEN).** Four measured composition
  gaps: positive base rate **28.22% vs 7.74%**, class-A shape **0.46% vs 0.87%** with only
  **25 rows** teaching the fix, non-Latin **4.57% vs 7.26%**, median length **2× production**.
  **Untested as a CAUSE** — a composition gap is not a mechanism.
- **Therefore unexplained:** why. Untested candidates in Phase 0.

⚠️ **Consequence for planning: the rebuild is justified by ruling 3 (multilingual coverage),
NOT by a demonstrated corpus defect.** Do not assume it fixes class A. Phase B2 exists
precisely because it might not.

## 0b. What each revision changed

| when | change | driver |
|---|---|---|
| 08-20 | drafted, reconciling the 08-07 criteria, #125 and the playbook | — |
| 08-20 | **two** defect classes, class A prioritised | owner: *"reader-flagged are far far worse"* |
| 08-20 | strictness scoped to harm; ADR-023 beats ADR-020 §3 | owner ruling 2 |
| 08-20 | **Phase B2 added** — prompt alone fixes ~⅓ of class A | 3-oracle bake-off (§1f) |
| 08-21 | class-A slice 4 → **9**; 5 promoted as hard negatives (a 6th demoted during review) | owner: *bring them to the dataset* |
| 08-21 | **Phase 0 / 0b added** — corpus located, training host settled | owner: *we still need to assemble the corpus* |
| 08-21 | **prefilter dropped, probe retrained** | owner ruling 3 (multi-script) |
| 08-21 | **H-CV1 measured, then the measurement withdrawn** — the instrument was the selector, so it is **UNTESTED**, not refuted (§0a) | adversarial review |
| 08-22 | two owner-flagged rows promoted (class B → **9**); the **class-B score-band premise breaks**; ruling 4 (placement ≠ prompt), ruling 5 (enrichment noted, not measured) | owner |
| 08-22 | ⛔ **H-CV1 REFUTED — the prefilter NEVER RAN on the corpus**; Phase 0's premise was false and is rewritten. The rebuild now rests on **four measured composition gaps** (H-UP10), not depletion | measured, 3 arms |
| 08-21 | **F1 parity gate, F2 no prefilter**; doc standard 7→6 files; #126 | owner |

---

## 1. Why v8 exists — TWO defect classes, not one

⚠️ **Scope correction, 2026-08-20 (owner).** The first draft of this plan treated #125
(academic register) as *the* defect. It is one of **two**, it is the **lower-scoring** one,
and it is the one readers complain about **least**. Both must die in v8.

> ### ⭐ OWNER RULING 2026-08-20 — class A is the priority
> Verbatim: ***"the ones flagged by reader are actually far far worse."***
>
> **Ruled:** class A (harm-adjacent / dominant-subject) is the primary target of v8.
> Class B (academic register) is secondary — required, but it does not gate the release
> on its own.
>
> **My gloss, not the owner's words:** this is ADR-023's asymmetric loss applied to
> *severity as well as frequency*. A class-A row lands at **5.86–6.85**, i.e. near the
> top of the feed, and its subject is trafficking, rape or animal cruelty — a reader who
> meets one may not come back. A class-B row lands at **4.06–5.12**, barely over the
> 4.5 op-point, and its failure mode is *boring*, not *harmful*. Same false-positive
> count, wildly different cost per event.
>
> **Consequences that follow, and which the rest of this plan is written to:**
> 1. The prompt rewrite leads with the **dominant-subject** rule (§4 Phase A step 1),
>    not the `evidence_level` fix.
> 2. **Growing the class-A slice is the critical path** — not the re-score. Four
>    records is too thin to gate on, and the oracle cannot generate more (§1a).
> 3. **Gate B-A blocks the release. Gate B-B is reported, and a miss is escalated to
>    the owner rather than auto-failing** the build.

> ### ⭐ OWNER RULING 2026-08-20 (second) — strictness, scoped to harm
> Verbatim: ***"we want stricter, cause FP (when it comes to harm, violence and other
> thriving-opposites) is way worse than missed detections."***
>
> **Ruled:** on harm / violence / thriving-opposites, optimise against the false
> positive. Missed detections are the acceptable error.
>
> **This settles a live conflict between two ADRs, in ADR-023's favour.** ADR-020
> decision 3 (*"prefer the oracle that UNDER-fires on penalty flags"*) rests on the
> premise that demoting good content is the expensive error. ADR-023 and this ruling
> both say the opposite for this class. ADR-020 is also still **DRAFT/PROVISIONAL**
> and dated 2026-05-31; ADR-023 is settled and later. **ADR-023 wins here.**
> ⚠️ **Scope it, don't generalise it.** ADR-020 §3 still governs filters and flag
> classes where a false penalty is the expensive error — this ruling is about
> harm-adjacent content on the Thriving lens.
>
> **My gloss, not the owner's words:** strictness must be built into the *mechanism*,
> not bought by switching vendor. The 2026-08-20 bake-off (§1f) shows the worst row
> failing on **all three** oracles, so no purchase decision fixes it, and the
> smallest vendor-to-vendor gap on class-A means (Gemini↔DeepSeek, **0.18**) sits inside
> the 0.82 oracle noise. ⚠️ That is the *minimum* pairwise gap, not a typical one —
> Gemini↔qwen3 is **0.725**. The conclusion holds; the number was selectively quoted.
>
> ⚠️ **The guardrail this ruling makes MORE important, not less:** transitional-justice
> and recovery stories are *themselves* harm-adjacent. A stricter harm rule is exactly
> what suppresses them. **§5b is now load-bearing** — Gate B-C is not optional.

The evidence is `datasets/adverse/uplifting.jsonl` — **16 records** (11 through
2026-08-10, **+5 promoted 2026-08-21**, §1g), which split cleanly by score band **and** by
who found them. The four original class-A rows:

| raw | article | class | found by |
|---|---|---|---|
| **6.85** | "Five men arrested… for raping a minor" | **A: harm-adjacent** | reader flag |
| **6.77** | "Celebrated at birth, pushed into sex work" (#91) | **A: harm-adjacent** | owner |
| **6.09** | "Rethink Business Centre Management" (complaint + proposal) | **A: harm-adjacent** | reader flag |
| **5.86** | Greyhounds to Australia as NZ racing ban begins | **A: harm-adjacent** | owner |
| 5.12 | "Boys must not be left behind," says minister | B: announcement-not-outcome | oracle batch |
| 4.94 | Sylvia Earle career profile | B: biography-not-outcome | oracle batch |
| 4.72 | Engineered nanovesicles / METTL3 | **B: academic** | oracle batch |
| 4.37 | Banana-pseudostem rodent enrichment LCA | **B: academic** | oracle batch |
| 4.29 | EBA ESG risk dashboard | B: regulator-not-rights | oracle batch |
| 4.13 | FAZ essay on punctuation | B: bland general news | oracle batch |
| 4.06 | Papaya seed oil solvent screening | **B: academic** | oracle batch |

**Class A scores 5.86–6.85; class B scores 4.06–5.12. The op-point is 4.5.** So class B
squeaks over the line while **class A lands near the top of the feed** — the #91 record led
the ovr.news homepage with a trafficking price list as its pull quote.


> ### ⭐ OWNER RULING 2026-08-21 (third) — drop the keyword prefilter, retrain the probe
> Verbatim: ***"we need to get rid of that pre-filter and retrain a probe."*** Reason
> given: keyword filtering ***"is not properly multi-lingual, multi-script."***
>
> **Ruled:** v8 ships **no per-lens keyword prefilter**, and the Stage-1 e5 probe is
> **retrained**, not inherited.
>
> **This ratifies an existing recommendation rather than opening a new direction.**
> `docs/TODO.md` decision 0 (2026-08-12) already said *"DELETE the per-lens prefilters
> rather than flip enforcement on"*, because enabling them would ship #99's English-only
> `DISCOVERY_PATTERNS` into production for the first time.
>
> **Measured, so this is not a preference:** `filters/uplifting/v7/prefilter.py` is 662
> lines and contains exactly two families of non-ASCII characters — **Latin (78) and
> em-dashes (30)**. No Cyrillic, Arabic, CJK, Devanagari, Greek or Hebrew. Coverage is
> EN + NL/DE/FR across **77** patterns in three categories (`crime_violence` **37**,
> `corporate_finance` 21, `military_security` **19**) — *counts corrected 2026-08-22 by
> loading the class; the 74/36/17 figures were wrong.* ⭐ **And "Latin script only"
> understates it: it is a FOUR-LANGUAGE instrument.** Measured over 235,905 production rows:
> EN/NL/DE/FR is **74.9%** of production, and the rest is barely touched — **Spanish (2nd
> largest, 16,390 rows) 0.89% removal against English's 8.89%**, Italian 0.74%, Arabic 0.06%,
> Korean and Croatian matching `crime_violence` at **0.00%**. For reference,
> enforcing `cultural_discovery`'s prefilter was measured to block **19.9% of non-English
> against 13.0% of English** articles.
>
> ⭐ **This is ADR-011 finally applied.** *"Embedding screening for needle filters — use
> Phase 3 positives as e5-small seeds to screen corpora; replaces keyword screening."*
> The probe already runs on `intfloat/multilingual-e5-**small**` — a multilingual encoder.
> Swapping Latin-script regex for a multilingual embedding screen is the architecture the
> ADR specified; v7 simply never completed the swap.
>
> ⛔ **What this ruling does NOT remove — three separate mechanisms, easy to conflate:**
> 1. **The 300-char oracle floor stays.** It lives in
>    `ground_truth.batch_scorer.make_oracle_prefilter`, not in the per-lens prefilter, and
>    its rationale is LLM framework leakage on short text — a property of the *prompt*
>    (#93). Dropping the lens prefilter does not touch it.
> 2. **`validate_article` stays.** It rejects *empty* content. **Empty is not short.**
> 3. **The commerce, obituary and violence gates stay.** Commerce is ADR-004's universal
>    prefilter; obituary and violence are separate shared gates, **not** ADR-004 — that ADR
>    says explicitly that other noise categories are *not* universal. All are shared
>    production machinery, unaffected by a per-lens prefilter decision, and they *do* run
>    in production — unlike the lens prefilter.
>
> ⚠️ **Nothing changes in production scoring on the day this lands**, because the lens
> prefilter never ran there (NM#284). **What changes is the corpus** — the oracle will
> label a population that is no longer keyword-shaped. That is the entire point.

### 1a. Class A — harm-adjacent / dominant subject (#91)

Stories **about harm** that contain a good-sounding fragment. The scorer rewards narrative
fragments over what the article is *about*. `belonging` shows the same shape at 7.04 for
*"community vows to unite"* — a phrase that exists **because** two people were murdered.

**No gatekeeper touches this class.** It is not a register problem and the §1c mechanism
does not explain it.

⛔ **The oracle is blind to class A by construction.** Measured 2026-08-09: the oracle
batch graded uplifting's ≥5.5 band **29/29 perfect** while readers were flagging three rows
*inside that band*. Five hand-checked reader flags yielded **3** accepted adverse rows;
**34** oracle-selected candidates yielded **0** of this class. Every class-A record above
came from a reader or the owner; every class-B record came from the oracle batch. That is
not a sampling coincidence — an oracle that defines the editorial line cannot see a blind
spot it shares.

**Consequence: reader flags are the only independent label source for class A**, which makes
the ovr.news flag endpoint a **v8 dependency**, not a nice-to-have (see B5).

### 1b. Class B — academic register and other non-outcomes (#125)

Measured on the held-out oracle test split (`datasets/training/uplifting_v7/test.jsonl`,
n=660), weighted average re-derived from the deployed `DIMENSION_WEIGHTS`, **no model in the
loop**:

```
oracle >= 4.0:  216/660 (32.7%)     <- the ADR-021 gate's own positive set
  academic-source rows   32/ 58 = 55.2% on-lens
  everything else       184/602 = 30.6% on-lens
  difference +0.246,  permutation p = 0.0001 (one-sided, N=20000, seed=11)
```

Reproduce: `PYTHONPATH=. python3 scripts/analysis/uplifting_v7_genre_bias.py`.

⚠️ **Academic is a plurality of class B, not all of it.** In the 21-row adjudication
(`datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md`) the shapes were:
academic abstract **9**, general news & features **7**, genuine solutions story **2**
(legitimate ADR-015 overlap, *not* a defect), body-extraction defect **3**. The labels
overlap; the column does not sum to 21.

Production corroboration (12 cycles, 2026-08-18 → 08-20, 36,516 scored rows/lens):
`uplifting` surfaces **6.96%** of the corpus — 3–7× every other ovr lens — and **enriches**
for primary literature (13.6%) where `belonging` (0.6%) and `solutions` (1.2%) deplete it.

### 1c. Class B's mechanism, verified in `config.yaml`

`evidence_level` is the **gatekeeper** (`gatekeeper: true`, `gatekeeper_threshold: 3`,
`gatekeeper_max_score: 3.0`) — the only dimension that can *cap* the weighted average.

A research abstract maximises exactly that dimension by construction: data citations,
verifiable outcomes, peer review. **So the one mechanism that could suppress the genre is
the one the genre saturates.** Structural, not a tuning miss.

Four named sites to rewrite live in `filters/uplifting/v7/prompt-compressed.md`; the worst
are **Contrastive Example 5** and the `evidence_level` scale. Hypotheses and ids:
`memory/uplifting-oracle-genre-hypotheses.md` (H-UP1..H-UP6).

### 1d. Not defects — three shapes that must NOT be "fixed"

1. **Extraction defects.** A paywall stub and a 56-character photo caption whose scored
   "body" was the comment thread both scored >4.0. **The fetch failed; the lens judgement
   was never made.** Labelling these adverse teaches the scorer that real articles are bad.
   → ducroq/NexusMind#306.
2. **Legitimate lens overlap.** Lenses are perspectives, not partitions (ADR-015). A genuine
   solutions story may also be uplifting. `content_type: solutions_story` is **not** a
   routing signal — it is the residual bucket meaning "no penalty cap applied", and the
   prompt's own *positive* examples carry it.
3. **Rank/framing complaints wearing a false-positive costume.** See §5b.

### 1e. The editorial target

The owner's own test, 2026-08-05, which settled four of five reader flags:

> **Does the article contain a process that is going well *now*?**

ovr later narrowed it to *a process going well **for people*** (`BRAND.md` `a70609b`,
2026-08-13), excluding harm-answered-only and institution-beneficiary items. **These are the
same rule and it is the organising principle of the v8 prompt** — not a carve-out appended
to the v7 list. #107 is scoped, not reversed: v7 faithfully serves a definition ovr never
published.

### 1f. ⭐⭐ Class A is BOTH a label defect and a student defect (measured 2026-08-20)

Full write-up: `docs/evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md`.
Three oracles, same v7 prompt, same text, bar 3.85:

| article | student | Gemini | DeepSeek | qwen3:14b | reading |
|---|---|---|---|---|---|
| Five men arrested … raping a minor | **6.85** | **7.62** | **6.25** | **7.30** | **all three fail — label defect** |
| Greyhounds / NZ racing ban | **5.86** | 2.30 | 3.95 ⚠️ | 2.00 | oracles right, **student is the outlier** |
| Rethink Business Centre Management | **6.09** | 1.55 | 1.80 | 4.35 | oracles right, **student is the outlier** |

⚠️ 3.95 is inside the ±0.16 band — indeterminate.

**One of three is a label defect; two of three are the student alone.** ⛔ **A
prompt-only v8 fixes about a third of class A.** The residue needs Phase B2 (§4).

**A secondary mechanism, recorded and deliberately not promoted.** Where a cap fired the
oracle was right; on the shared-failure row all three assigned the residual
`solutions_story` bucket, i.e. **`individual_crime` (max 3.0) did not fire on an article
headlined "Five men arrested."** Worth fixing — but a cap is a **clamp on a bad reading,
not a repair of it**, and it is irrelevant to the two rows where the oracle was already
right. ⚠️ **The defect is that the scorer reads harm as wellbeing** (`human_wellbeing_impact`
7.5 on that row). The prompt work that matters is the valence rule (§4 Phase A step 1).

⚠️ **A FOURTH noise floor, and it changes the gates.** Same oracle, same prompt, same
article, 10 days apart: **mean |Δ| 0.82, max 2.25** (n=7) — 5× the #95 batch floor.
**A single-run oracle score is not a measurement.** Every oracle-side gate below is
therefore a **k-run mean with a stated band**, never one run.

⚠️ n=3. Direction strong, estimate weak.

### 1g. The class-A slice, grown 2026-08-21 (4 → 9 records)

Owner instruction: *"if you find adverse examples bring them to the dataset we will use
for training the new scorer."* Done — promoted into `datasets/adverse/uplifting.jsonl`
with `training_use: HARD NEGATIVE ... per FILTER_PLAYBOOK 4b`.

Selected from **~14,000** distinct stage-2 production rows at or above the 4.5 op-point ⚠️ (logged 13,927; re-run returns **14,031** — a cycle file was read mid-write. Candidate generator only; no rate derives from it.)
(2026-08-07 → 08-21), harm-lexicon screened over titles (158 hits) and adjudicated by the
§1e test. ⚠️ The lexicon is a **candidate generator, not a population** — no rate is
derived from it.

| raw | normalized | tier | article |
|---|---|---|---|
| **5.976** | **8.284** | high | Woman 'tortured' for taking possession of grabbed land, Sahiwal |
| **5.748** | **7.461** | high | Children's helpline: calls about child domestic abuse up 80% in five years |
| **5.458** | **7.117** | high | Parents of baby girl killed at nursery fear unsafe sleeping 'rife' |
| 5.374 | 6.809 | medium | Domestic violence victim traumatised after Travelodge gave abuser room key |
| 5.260 | 5.023 | medium | Assault, harassment and stalking top calls to victim line |

**Three of the five normalize above 7 — near the top of the Thriving feed.** The torture story
normalizes to **8.284**. `human_wellbeing_impact` on it is **6.05**.

⭐ **The screen's main surprise: most harm-lexicon hits are TRUE positives** — rescues,
survivor recovery, falling murder rates, convictions delivered. The lens is largely right
on harm-adjacent content, which makes the false positives both rarer and more specific
than the class-A framing implies, and makes §5b's no-regression risk concrete rather than
theoretical.

**5 rows were parked or rejected, not brought to you as line calls**
(`datasets/adverse/candidates/2026-08-20-harm-screen-parked.jsonl`), each with its
true-positive reading recorded. ⛔ **Standing rule from the owner, 2026-08-20: a row with
a serious TP reading is a bad gate probe by construction** — it tests the boundary, and
the boundary is where noise makes the test meaningless. Do not escalate line calls; pick
the ones that are truly FP. *(This retires the Assyrian-genocide essay as a blocker: it is
genuinely two-sided and therefore simply not probe material.)*

⚠️ **Footnote, not a finding.** `cap_applied` is null on all 236,879 production rows
because `_TRIGGER_REGISTRY` in `NexusMind/src/scoring/cap_triggers.py` is **empty by design**
(since 2026-07-14; `climate_doom` retired at 3 bites / 3 FPs / 0 saves), so `detect_caps`
returns `[]` for every filter — it matches regex over title+content and **never reads
`content_type`**. The stamp is correct; the mechanism is **disarmed, not dead**, and one
registry line from live.
⛔ An earlier draft blamed `content_type` being an oracle-only field. That was wrong, and so
was the "populate it or delete it" recommendation that followed from it.
**Caps stay a mechanism detail; the defect is that the scorer reads harm as wellbeing.**

### 1h. ⭐⭐ Two owner-flagged rows, 2026-08-22 — and the class-B band premise breaks

Two rows pulled from the live Thriving lens by the owner. Both read **in full** from the
exact text the scorer saw (production rows on sadalsuud), not from excerpts.

| raw | norm | article | shape |
|---|---|---|---|
| **7.359** | **9.988** | Dawn, "Curing the cause" — op-ed on liberation psychology | **no live process at all** |
| **6.901** | **9.856** | TSA Algérie, Algerian doctor named GM of a new Ottawa clinic | **no outcome has occurred** |

⭐⭐ **These break the premise the A-over-B priority ruling rested on.** That ruling cited
class A at raw 5.86–6.85 against class B "barely over a 4.5 op-point" at 4.06–5.12. Both
rows above are **class-B-shaped — non-outcome, no harm content whatsoever** — and the Dawn
row is now the **highest-scoring row in `datasets/adverse/uplifting.jsonl` on both raw and
normalized**, above every class-A row. ⚠️ **The classes are distinguished by SHAPE, not by
band.** The priority ruling itself is untouched — class A remains the harm-adjacent class
and the reader-facing hazard — but "class B is the low-scoring one" is no longer true and
must not be repeated.

⛔ **Correction to a claim I made on 2026-08-22:** I stated the worst catalogued class-A row
normalizes to 8.284. It is **9.862** (Mashonaland Central). 8.284 is the maximum of §1g's
*newly promoted* rows only — a subset table read as the whole slice. The two rows above are
therefore *comparable to* the top of class A, not far above everything.

**What they share, and it is the rule Phase A must write.** Neither contains a harm subject,
so no class-A rule reaches them. Both score high because **the dimensions reward sustained
topical discussion of wellbeing rather than an occurring outcome**:

- Dawn: liberation psychology developed in 1970s–80s El Salvador; concrete examples from
  Colombia, Chile and Brazil, all decades old and elsewhere; every Pakistan sentence
  prescriptive (*"should become part of schools"*, *"urgently needs"*). Not one current,
  named, operating programme. `change_durability` **7.375** for a set of recommendations.
- TSA: an appointment. Degrees, an 18-year CV, two teaching awards, and a stated wish
  (*"son souhait … de bâtir une clinique accessible"*). No patient has been seen.
  `human_wellbeing_impact` **8.312** — the *"significant wellbeing improvement with
  measurable outcomes"* band — on health vocabulary alone.

⭐ **Both would have been capped by the gatekeeper that already exists.** `evidence_level`'s
own 0–2 band reads *"No uplifting outcome to verify, OR pure speculation"* — a literal
description of both articles. It scored **6.21** and **6.44**, so `GATEKEEPER_MIN = 3.0`
never tripped and `GATEKEEPER_CAP = 3.0` never applied
(`filters/uplifting/v7/base_scorer.py:52-54`; logic at
`filters/common/filter_base_scorer.py:331-335`). Had it fired, both land at **3.0** — under
the 4.5 op-point *and* under the 3.85 adverse bar. **Both fixed by a rule already written
and not followed.**

⚠️ **The cap is the lever, not the dimension value.** Scoring Dawn's `evidence_level` down to
2 *without* the gatekeeper firing moves raw only **7.359 → 6.938**. A 0.10-weight dimension
cannot move a 7.36 average. Phase A's job on this shape is to make the gatekeeper **fire**,
not to add dimensions. This is the same `evidence_level` defect as §1c seen from the other
side: §1c found research abstracts *saturate* it; these two show essays and announcements do
too. It is reading *"is this well-sourced?"* instead of *"did an outcome for people happen,
and is it verified?"*

**Both also over-score in `belonging`** (5.27 and 5.17), so this is not a Thriving-only
mechanism. Out of scope for v8; recorded for #61.

#### Owner rulings, 2026-08-22

4. **Lens misattribution is NOT a v8 prompt concern.** Probe article: Times of India /
   Helsinki heat caverns (raw **6.648** uplifting vs **4.095** solutions; the other four
   lenses ≤ 2.95). It passes §1e cleanly — a facility operating now, heating 25,000 homes —
   and is the twin of §5b's Rwanda–EU no-regression row, so under ADR-015 the score is
   **correct**. Owner: *"i think this belongs somewhere else indeed, there are more
   misattributions, and that is not our biggest concern right now."* **No prompt change.**
   ⚠️ *My gloss, not the ruling:* the capacity-vs-delivered refinement I proposed for that
   row is therefore dropped as a general rule. It does **not** weaken the "no outcome has
   occurred" rule for Dawn/TSA, which fail for the absence of *any* outcome, not for the
   difference between projected and delivered.
   **Verified while adjudicating it:** placement is a fixed map — `FILTER_TO_TAB` in
   ovr.news `src/lib/data/filters.ts:34` sends `uplifting → thriving` unconditionally — and
   the layer built to reassign, `lens_fit` (ADR-037 Phase 3), is **absent from the deployed
   `data/chief_editor_config.json`**, so it falls through to the code default
   `{enabled: false, audit_only: true}` and **has never run**. Nothing ever compared 9.617
   against 8.074. That is llm-distillery#96, and it is an **ovr.news** fix.
5. **The enrichment-stub hypothesis is NOTED, not measured.** All three articles the owner
   sent are enriched stubs — `feed_summary` (6,737 ch), `feed_summary` (76 words → 2,638 ch),
   `headline_only` (`word_count: 0` → 4,894 ch). ⛔ **Three for three, and it proves nothing:
   the owner selected them because they looked wrong, so this is a hand-built population**
   (`feedback-hand-built-population`). Registered as **H-UP9** in
   `memory/uplifting-oracle-genre-hypotheses.md`; test against all Thriving rows above the
   op-point with a pipeline-computed denominator, after Phase A.

## 2. Closed doors — do not reopen these

| Door | Why it is shut |
|---|---|
| **Move the op-point** | Already swept (2026-08-10, `docs/evidence/2026-08-10-uplifting-v7-threshold-sweep-102.md`). 5.0 is **blocked** by `MAX_NORMALIZATION_RAW_MIN = 4.5` in `scripts/normalization/fit_normalization.py:61`. The op-point is 4.5 already, at **zero margin** (strict `>`). |
| **Retrain on the v7 label set** | The defect is *in* those labels. A perfect student reproduces it. |
| **Re-weight the dimensions** | Same trap as `solutions v6`: re-weighting measured inert, and an apparent gain at an absolute threshold is an **artifact** — a percentile CDF removes any monotone rescale (`memory/solutions-v6-dimension-hypotheses.md` R3). Weights cannot fix a label defect. |
| **Active learning first** | ⭐⭐ **An instrument built from the thing under test cannot audit it.** The AL grader *is* the v7 oracle prompt, so it surfaces only student-vs-oracle disagreement and silently re-labels as positives the ~55% of class B the oracle **accepts** (H-UP5). **For class A it is worse than useless**: measured 2026-08-09, the oracle graded the ≥5.5 band **29/29 perfect** while readers flagged three rows inside it — 34 oracle candidates produced **0** class-A rows against 5 reader flags producing **3**. **Prompt first, then AL — and AL can never be the class-A source at all.** |
| **Assume the rebuild fixes class A** | ⚠️ **Still shut, for a NEW reason (2026-08-22).** H-CV1 is now REFUTED — the prefilter never ran, so there is no depletion to undo. The rebuild is justified by **four measured composition gaps** (H-UP10, Phase 0), but a composition gap is **not a demonstrated cause**: the student saw 350 harm rows, conservatively labelled, and still scores a torture story at 5.976. And §1f measured that **2 of 3 class-A rows are the STUDENT alone**, which no corpus change reaches. **Phase B2 stays load-bearing.** |
| **Ship an empty `prefilter.py`** | ⛔ Ruling 3 / §F2. Not an empty file, not commented-out rules — **no file**. A required artefact that does nothing is this repo's recurring failure mode (`expected_pass_rate`, `stage1.threshold`, `cap_applied` null on 236,879 rows). |
| **Playbook §4a as written** | ⛔ §4a step 4 says *"keep probe-high + model-high articles as-is — the model already gets them right."* That band is **exactly where #125 lives**. §4a re-scores only the ambiguous mid-range, so it would relabel the middle and preserve the biased top. §4a is correct for a *model* defect and wrong for a *label* defect — see §8. |

---

## 3. The rename — settled, and larger than ADR-012 says

**`uplifting` → `human_thriving` at v8.** ADR-012 as amended 2026-08-06, case 3: neither
the old name nor the bare lens name says *what* thrives. **Not** bare `thriving` —
`filters/thriving/v1` is an occupied, parked directory (ADR-015).

### 3a. It creates a seventh filter, automatically

`NexusMind/src/filters/filter_loader.py` `discover_filters()` iterates
`filters_dir.iterdir()` — **one entry per filter-name directory** — and sets
`"analysis_key": filter_name`. So dropping `filters/human_thriving/v8/` beside
`filters/uplifting/v7/` yields a **new filter scored in parallel**, emitting `human_thriving`
as its own analysis key, while v7 keeps emitting `uplifting`.

That *is* the parallel-running period ADR-012 requires, and it needs no build. The costs it
does carry, which ADR-012 does not mention:
- **Thriving-lens inference roughly doubles** for the duration.
- **Both keys reach ovr.news**, so the cross-lens `canonical-lens.ts` max-across-scorers
  pick sees two Thriving candidates. Decide the cutover date *before* deploying, not after.
- The gpu-server scorer **validates weights for every discovered filter at startup**, so a
  weightless `human_thriving/v8` means the scorer never starts and **all seven filters score
  nothing**, unattended. Guard D of `scripts/deployment/preflight_deploy_guards.py` now
  aborts on this — do not bypass it.

### 3b. ⚠️ ADR-012's site list is a snapshot, not an inventory

ADR-012 names three ovr.news files (`article-analysis.ts`, `types.ts`, `transform.ts`).
Measured 2026-08-20:

| Repo | Files mentioning `uplifting` | vs ADR-012 |
|---|---|---|
| `ovr.news/src` | **12** | names 3 |
| `NexusMind` (`src`,`scripts`,`config`) | **9** | names 0 |
| `llm-distillery` (code/tests, excl. docs + `filters/uplifting`) | **87** | — |

Top ovr sites by count: `article-analysis.ts` (6), `data/transform.ts` (3),
`data/filters.ts` (2), then nine singles including `curated-images.ts`,
`manual-suppression.ts`, `image-query-generator.ts` and `[lang]/lens/[lens].astro`.

**Step: re-run the enumeration at cutover time and work from that, not from this table** —
it will have drifted (`feedback-enumeration-is-not-inventory`). Historical scored rows keep
the `uplifting` key forever; nothing rewrites them.

### 3c. Hub

`uplifting v7` is **NO_HUB** (file-copy deploy). A Hub repo for v8 is therefore optional. If
one is ever created it must be `human-thriving-filter-v8` per #48, whose
`verify_filter_package.py` check fails when `repo_id` disagrees with the filter name.

---

## 4. Phases

### Phase 0 — assemble the corpus (no spend) ⭐ *added 2026-08-21*

**The v7 corpus is LOCATED — B1 cleared.** `gpu-server:~/llm-distillery/datasets/training/uplifting_v7/`:

| split | rows |
|---|---|
| `train.jsonl` | 5,271 |
| `val.jsonl` | 659 |
| `test.jsonl` | 660 (the only one mirrored on situla) |
| **total** | **6,590** — exactly the figure the cost estimate assumed |

Row shape: `{id, title, content, url, labels[6], dimension_names[6]}` — **full article
text is present**, so every row is re-scorable under a new prompt. ⚠️ It is *prepared*
data, not the raw scored JSONL: the oracle's `content_type` and per-dimension evidence
strings did **not** survive `prepare_data.py`. Only the six numeric labels did. If v8
wants to diff old-vs-new `content_type` (e.g. to check `individual_crime` now fires), the
raw scored file must be found separately or the diff is unavailable.

⛔ **Do not copy this corpus into the repo.** 22 MB of full article text is the hazard #97 surfaced
(#97 itself is the TDM-position assessment; the 812 committed rows of full text were a
finding inside it, not its subject). Stage it on the training host, keep the repo holding excerpts only.

**What Phase 0 does, now that the prefilter is dropped (ruling 3):**

⛔⛔ **CORRECTED 2026-08-22 — the sentence that stood here was FALSE.** It read: *"The v7
corpus is keyword-shaped and cannot be the backbone unchanged … the 6,590 rows were selected
with 74 Latin-script patterns applied."* **The prefilter never ran on this corpus.**

**H-CV1: REFUTED, premise and all.** Full write-up:
`docs/evidence/2026-08-22-uplifting-v7-corpus-provenance.md`; logs in
`docs/evidence/2026-08-22-hcv1-runs/`; reproduce with
`scripts/analysis/prefilter_march_probe.py`.

The corpus is dated **2026-03-11**; `prefilter.py` was created **2026-03-09** and changed
**four times since**, so today's rules cannot testify about March. Running the March version
(`991ffec`) over the corpus it supposedly built:

| arm | population | instrument | blocked |
|---|---|---|---|
| A | 235,905 production rows | today's prefilter | 6.917% |
| B | 6,590 corpus rows | today's prefilter | 9.074% |
| **C** | the same 6,590 | **March-2026 prefilter** | **15.493% — 1,021 rows** |

**Those 1,021 rows (350 `crime_violence`) are in the training splits.** A filter that ran
would have removed them. Corroborated twice: `ground_truth/batch_scorer.py:1615` has a legacy
`--prompt` mode marked **"NO PREFILTER SUPPORT"**, and the March prefilter enforced a 300-char
floor while the corpus holds rows of **35 characters**. Same instrument both sides, the corpus
is **not depleted**: crime-violence matches **2.72%** of it vs **2.38%** of production.

⚠️ Two numbers in this plan were wrong and are corrected: the prefilter has **77** patterns
(corporate_finance 21, military_security 19, **crime_violence 37**), not 74/36.

⚠️ **Ruling 3 is untouched and now has a figure.** The prefilter is a **four-language**
instrument (EN/NL/DE/FR = **74.9%** of production); Spanish, the 2nd-largest language at
16,390 rows, is filtered at **0.89%** against English's **8.89%**; Korean and Croatian match
`crime_violence` at **0.00%**.

### ⭐⭐ The rebuild is still right — for four MEASURED reasons, none of them depletion

Refuting H-CV1 closes **removal**. It says nothing about **composition**, which is where the
corpus argument actually lives (**H-UP10**). Owner, 2026-08-22: *"I do not want a keyword
prefilter anymore, and I want a proper data corpus to train on. It is my belief that the
corpus partly determines the quality of the result."* Measured, that holds:

| | corpus (6,590) | production (205,939 stage2) | gap |
|---|---|---|---|
| harm as **dominant subject** (title) | **0.46%** (30 rows) | 0.87% (1,798) | 1.9× under |
| …of those, teaching the FIX (< 3.85) | **25 rows** | 1,663 | — |
| **positive base rate (≥ 4.5)** | **28.22%** | **7.74%** | **3.6× enriched** |
| non-Latin script | 4.57% | 7.26% | 1.6× under |
| median content length | 2,658 ch | 1,349 ch | 2× longer |

⭐⭐ **25 rows are the entire training signal for class A.** Nothing removed them — they were
never assembled in. ⚠️ **This is a composition gap, NOT a demonstrated cause.** The student
saw 350 harm rows, conservatively labelled, and still scores a torture story at 5.976. **Do
not assume the rebuild fixes class A; Phase B2 stays load-bearing.**

⭐ **Class B is NOT a corpus problem.** The corpus *under*-represents primary literature
(arxiv 4.23% / pubmed 2.05% vs production's 7.92% / 0.83%), so #125's academic-register
defect is a **prompt** defect. Spend no corpus budget on it.

⛔⛔ **CORRECTED 2026-08-28 — four of these five targets were stated against a
population a draw cannot sample from.** They come from the production census, which
counts rows *including* `news.google.com`. GN is 22.1% of rows and is excluded from
every draw by rule, so excluding it moves every target: base rate **7.74% → 9.76%**
(enrichment 3.6× → **2.9×**), non-Latin **7.26% → 9.76%**, median length
**1,349 → 1,900** (corpus 2× → **1.37×**), class-A **0.87% → 0.70%**, and p10 length
**84 → 235 ch** with the sub-300-char share collapsing **30.8% → 11.9%** — so
"the short-form regime is under-trained" is largely a statement about headline echoes.
**The drawable population is n = 179,111** (distinct articles, GN excluded, all stages,
window 2026-08-14 → 08-28). Use the corrected column below; full table, method and the
window-stability check: `docs/evidence/2026-08-28-v8-phase0-drawable-population.md`.

⚠️ **Two further corrections from the same run.** (1) The archive window in step 5
below has **rolled** — it now holds `08-14 → 08-28`, not `08-07 → 08-21`, and the
236,879-row figure belongs to a window no longer on disk. (2) "91 harm rows above the
op-point in 14 days (~6.5/day)" is **window-dependent**: the current window gives 78
(~5.6/day). State it as **~5.6–6.5/day**. The ADR-023 argument is unaffected.

⭐ **Refuted, and it was the reason the drawable census got written:** an article is
scored **once**, not per cycle — 232,845 rows → 232,842 distinct ids. Row-vs-article
dedup is a no-op on this archive.

⭐ **Draw from the FULL pool, including `stage1_low`.** Conditioning on stage2 lets the
v7 e5 probe decide what a v8 corpus may contain — the same shape as the keyword
prefilter ruling 3 dropped. Measured, the probe is **composition-neutral on every axis
Gate 0 measures** (≤0.72pp on all of them), so this is a *coverage* argument, not a bias
one: stage2-only costs **11.5% of the pool and 95 domains** for no compositional gain.

**Gate 0 targets — state each as a chosen number before drawing:**

- ✅ **Positive base rate — DECIDED 2026-08-28: 19.5%, an enrichment factor of 2.0×
  recorded.** Owner ruling; record: `docs/decisions/2026-08-28-v8-gate0-corpus-spec.md` §1.
  Drawable production is **9.76%** (*corrected 08-28; 7.74% was the GN-inclusive figure*);
  v7 was 28.22%, i.e. **2.9× accidental and unstated** — that, not the enrichment itself,
  was the defect. ⚠️ "Match production" was and remains the WRONG fix: ADR-003 screen+merge
  enrichment exists *because* positives are rare, and a 9.76% draw spends the oracle budget
  on obvious negatives. **Correct for the recorded 2.0× downstream** (class weighting or
  calibration). *Derived, not ruled — check against the split:* with the mix held at
  63.5/36.5 this puts 4.5–5.5 at ≈12.4% and 5.5+ at ≈7.1% (≈2.0× production's 3.562%,
  down from today's 4.21×).
- ✅ **Class-A shape at ≥ production's 0.70%** (*corrected 08-28; 0.87% was GN-inclusive*),
  with **TPs as well as FPs — balance DECIDED 2026-08-28: 3:1, i.e. ~75% TP / ~25% FP**
  (owner ruling; record §3). Deliberately FP-richer than §1g's screen found reality to be
  (~9:1), because at 9:1 only one supplement row in ten carries the defect signal — and
  ⛔ no rate may be inherited from that screen regardless, the lexicon is a candidate
  generator, not a population. The 4 corpus rows
  labelled ≥4.5 are restorative-justice stories (Brussels survivor meets perpetrator 6.55,
  $30M abuse settlement 5.85, Myanmar amnesty 5.38), i.e. §5b shapes. **An FP-only supplement
  destroys the no-regression set.**
- **Non-Latin share at ≥ production's 9.76%** (*corrected 08-28; 7.26% was GN-inclusive,
  and the quantity is drifting up — Arabic 1.5% → 2.0% in two weeks*). Nothing else in this
  plan would notice if the rebuild stayed Latin-shaped.
- **Cover the short-form regime** (drawable `p10 = 235 ch`, median **1,900**; *corrected
  08-28 — `p10 = 84` / median 1,349 were GN-inclusive, and the sub-300-char share falls
  30.8% → 11.9% once GN is out, so this regime is **smaller than recorded, still real**:
  21,374 articles*) or state that the filter is trained for long-form only.
- ⛔ **Exclude `news.google.com`** — 22.1% of production and sub-300-char headline echoes, so
  production percentages are not directly the targets a draw should hit. **Measured 08-28:
  this single exclusion is what moves every other target on this list.**
- ⛔⛔ **SHAPE, not just rate — and the FN trap (measured 2026-08-28, owner flagged the
  risk).** The corpus is **4.21× over-weighted in 5.5–10** (15.8× at 7.0–7.5, 134× at
  7.5–8.0) and **thinnest at 1.5–3.5 (0.43×–0.68×)** — i.e. fat where the task is easy
  and thin where stage-2 false positives are born. ⛔ *This refutes the "over-sample the
  visible band" spec drafted earlier the same day: the corpus already has it.*
  **The stage-1 danger is the positive MIX**, not the positive rate: production's
  positives are **63.5% marginal (4.5–5.5)**, the corpus's are **46.8%** — skewed 1.36×
  toward easy positives, which are not the ones a screen misses. ⛔ **A recall figure
  measured on that val split is optimistic, and this is TRUE OF v7 TODAY.** What makes
  it survivable is only that the probe routes **88.6%** to stage 2 (threshold 1.00,
  calibrated when MEDIUM was 4.0, never re-derived after #102) — **a harder screen
  converts that slack into unrecoverable FNs.** Therefore: **(a)** add no mass above 5.5;
  **(b)** hold the positive mix at production's 63.5/36.5 — enrich the *rate*, never
  reshape the *class*; **(c)** spend the freed budget on 1.5–3.5; **(d)** validate
  FN@MEDIUM+ on a production-mix cohort via `train_probe.py --recall-check-file`, never
  on the enriched val split; **(e)** ✅ **stage-1 aggressiveness — DECIDED
  2026-08-28: HOLD NEAR PASS-THROUGH.** Retrain the probe on the v8 corpus but do **not**
  screen harder; re-derive the threshold only far enough to preserve today's 88.6% routing.
  No stage-2 cost constraint was claimed, so the FN risk is not bought (owner ruling; record
  §2). ⚠️ A v8 decision, not a permanent one — re-open only with a measured cost problem
  and an FN ceiling named *before* the sweep. Per-bin table and the arithmetic control (160,641 rows,
  max |Δ| 1.8e-15): `docs/evidence/2026-08-28-v8-phase0-drawable-population.md` §6.
- ⭐ **Write a `corpus_manifest.json` (llm-distillery#127).** Establishing that this corpus was
  *not* prefiltered took git archaeology plus a three-arm experiment; it should have been a
  file. v8 is the first corpus with a chance to record its own provenance, and Gate 0 already
  demands most of the numbers, so the marginal cost is near zero. ⚠️ The acceptance test is a
  manifest **on a freshly prepared split whose counts reconcile with the split**, not a
  `json.dump` in the code.

1. **Re-score the 6,590 under the v8 prompt anyway** — they are labelled articles with full
   text and they keep `test.jsonl` comparable to the #125 baseline every gate refers to.
   Treat them as a *seed*, not as the population.
   ⛔⛔ **AT k ≥ 3, NOT k = 1 (measured 2026-08-28).** Two runs of the identical prompt on
   identical articles disagree on **5/30 (17%) op-point crossings**, because
   `scope_verdict` is a binary that zeroes all six dimensions: **gate-stable rows move a
   median 0.100, gate-flipped rows 3.750**, and the gate flips on **13%** of re-runs. A k=1
   re-score labels ~860 of 6,590 rows by a coin toss, at the boundary. Gate A missed it by
   averaging k=3.
   ⚠️ **Re-measured 2026-08-29 at n=200: 5.3% production-mix ([2.7%, 8.4%]), 6.7% (as-is)
   and 9.3% (reordered) at the boundary, per identical-run pair.** ⛔ **This is NOT a
   refutation of the 13%** — that came off 4/30, whose Clopper-Pearson CI is **[3.8%, 30.7%]**
   and contains every estimate above (Fisher p=0.118 like-for-like; **p=0.4648** against the
   boundary stratum, the population an op-point-weighted panel actually sampled — the earlier
   **0.722** named no cell and used a non-comparable one). The
   design-weighting explanation is plausible and **not distinguishable from n=30 noise**;
   what n=200 buys is a usable interval. The ~860 figure inherits the panel's weighting. ⛔ The
   conclusion is unchanged (**k ≥ 3, not k = 1**): 8.0% of production-mix rows and 10–14% of
   boundary rows are non-unanimous over three runs, and the k=3 majority differs from run 1
   on 3 of 7 boundary non-unanimous rows. What changed is the size, not the sign.
   ⛔⛔ **PARITY SETTLED 2026-08-29, AND IT FAILED. Do not adopt the reorder as a cost
   optimisation.** At n=200, with the null measured on the same rows at the same pair level,
   moving the article to the end **changes the labels**: mean(reordered − as-is) **−0.239**
   on the production-mix stratum (95% CI [−0.409, −0.080]), which survives a sign-flip
   permutation (p=0.0049) and source clustering ([−0.410, −0.078]); and **−0.443** at the
   boundary (p=0.0063). ⛔ **NOT multiplicity-robust**: p(R)=0.0049 does not clear
   0.05/16, the family this analysis actually prints. No family was pre-registered.
   Rows above the op-point at k=3, **per stratum**: **8/150 vs 11/150** (production mix) and
   **7/50 vs 12/50** (boundary). The reordered prompt is a **stricter oracle**, not a cheaper
   copy of this one. Its price advantage is real — run-1 **$0.000519 vs $0.002736/article**,
   so k=3 on 6,590 rows is **≈$6.9 vs ≈$21.7** — but that is a price difference between two
   different labelling functions, and **≈$15 is small against the adjudication time this plan
   already calls "the real cost"**. Adopting it is a scoring decision for the owner, not a
   budgeting one.
   ⛔ **Two claims from the first write-up are WITHDRAWN (review, same day).** *"The shift
   survives on the 41 rows both arms call `in_scope`, so it is not just the gate"* pooled the
   two strata — per stratum it is R n=21 **[−0.516, +0.036], includes zero** — and it
   conditions on `scope_verdict`, **an outcome the treatment changes** (16 rows unanimous
   `in_scope` under as-is only, 8 under reordered only), so it is a collider, not a subgroup.
   And *"15 vs 23 rows above the op-point"* was pooled across a uniform-random stratum and one
   oversampled **4.4×**, inflating both levels ~40%.
   ⛔ The k=3 repeat discount is **UNPROVEN at corpus scale** (runs 2–3 came ~1 min apart, a
   corpus pass is ~30 min, and DeepSeek's cache TTL was never measured). Scheduling k=3 as
   three back-to-back calls **per article**, instead of three passes over the corpus, removes
   the assumption.
   Probes: `docs/evidence/2026-08-28-v8-prompt-order-probe/` (n=30, could not see it) and
   `docs/evidence/2026-08-29-v8-phase-a-k3/` (n=200, resolves it).
2. **Rebuild the population without keyword selection.** Draw from FluxusSource raw and the
   NexusMind archive with **no lens prefilter applied**, so the oracle sees what production
   sees. The 300-char oracle floor still applies (ruling 3, exclusion 1).
3. **Supplement deliberately with the class-A shape — both FPs and TPs.** §1g's screen
   found most harm-lexicon hits above the op-point were *true* positives. A corpus carrying
   only the FPs teaches "harm words → suppress" and destroys §5b.
4. **Sample above the op-point** for the supplement (ADR-023): that is where junk reaches
   readers, not below it.
5. ⚠️ **The archive window bounds any production draw — and it ROLLS.**
   `sadalsuud:~/local_dev/NexusMind/data/filtered/uplifting/` holds **~14 days**.
   ⛔ *Corrected 2026-08-28: the window is now* **`08-14 → 08-28`** *(83 files, 232,845
   scored rows, 1.7 GB) — the `08-07 → 08-21` / 236,879-row figure names a window no
   longer on disk.* Re-enumerate before every draw; **a draw taken next week is a
   different population**, so the manifest records the window, not just the counts.
   Measured on a cycle file (n=2,991): **100% `passed_prefilter`, 100% `prefilter_reason`
   null, 100% `disposition: kept`** — so the archive also excludes **every gate-blocked
   article**. Those are now recoverable from the block ledger (2026-08-24), which they
   were not when this step was written. Older material must come from FluxusSource raw.
6. ⛔ **Do not copy any of it into the repo** — full article text at scale is the hazard
   surfaced under #97 (812 committed rows). Stage on the training host; the repo keeps
   300-char excerpts.

**Gate 0:** the corpus is staged on the training host; row count and split sizes recorded;
the class-A supplement's TP/FP balance stated (✅ **3:1**, above); **and the language/script distribution
reported against production's** — the whole point of ruling 3 is that the corpus stops
being Latin-shaped, and nothing else in this plan would notice if it still were. All
**before** any oracle spend.

### Phase 0H — the training host ⭐ *added 2026-08-21*

**Train on b650** (`ssh b650-gpu`, RTX 3090 Ti **24 GB**). It exists for this: its stated
purpose is *"training node (ends Ollama-vs-training contention on gpu-server)"*, and
gpu-server has **16 GB** while also running the production scorer and Ollama.

- **venv: `~/llm-distillery/venv-prodparity`** — py 3.11, torch 2.11.0+cu130,
  transformers 5.0.0, peft 0.18.1, sklearn 1.8.0. GPU works. ⛔ **Not** `~/llm-distillery/venv`
  (CPU-only, kept solely as provenance for the 2026-08-09 parity dumps).
- **b650 is cleared to train the e5 probe for gpu-server** — probe path measured
  bit-identical (max |Δ| 4.2e-6, zero screening flips).

⛔⛔ **THE ONE THAT WILL BITE: b650's GPU is NOT production-exact for the Gemma student,
and it diverges precisely at 4.5 — which is this filter's op-point.** Measured 2026-08-09
on uplifting v7's 660 held-out rows:

| | at 4.0 | at 4.5 |
|---|---|---|
| verdict flips, b650-GPU vs gpu-server | 1 | **3** |
| specificity | — | gpu-server **0.9730** vs b650 **0.9662** |

On **CPU** with `venv-prodparity` b650 is **bit-identical to production** — 660/660 rows,
0 flips at every threshold — and its numbers may be quoted without qualification.

**Rule for v8, non-negotiable:** *train* and iterate on b650 **GPU** for speed (~2 min per
660 rows vs ~16 on CPU, ~30 on gpu-server CPU), but **run the ADR-021 gate and every
op-point number on CPU with `venv-prodparity`, or on gpu-server.** A gate specificity
quoted off b650-GPU at 4.5 is wrong by ~0.007 and three articles. Re-run
`scripts/verification/box_parity.py` + `diff_box_parity.py` at whatever threshold v8
lands on — **a box is cleared AT A THRESHOLD, never in general.**

⚠️ `p50 |Δ| = 0.0000` is a trap: raw logits are bf16-quantised (~0.03 steps), so most
disagreements are hidden, not absent. Only 2.3% of rows are bit-identical on GPU.

### Phase A — prompt rewrite (no spend)

**Organising principle, replacing v7's carve-out list:** *does the article contain a
process that is going well **for people**, **now**?* (§1e). Everything below serves that
question; nothing is appended to v7's five penalty checks as a sixth.

1. **Class A first — the dominant-subject rule.** The score must follow what the article is
   *about*, not the best phrase in it. A story whose subject is a crime, an abuse or a
   harm does not become uplifting because it contains an arrest, a vow, a proposal or a
   ban. ⚠️ **This is the hard one to write without over-reaching** — see the
   no-regression set in §5b, which the rule must not catch.
2. **Class B — break the gatekeeper trap** (§1c). `evidence_level` must measure *evidence
   for a human outcome*, not evidence quality in general, and must be able to score **low
   on a rigorous paper that reports no outcome for people**.
2b. ⭐⭐ **The live-process rule — the single highest-value change, and it is a GATEKEEPER
   change, not a new dimension** (§1h). `evidence_level` must be **forced to its 0–2 band
   whenever no outcome for people has occurred**, which is what its own scale already says
   and what the oracle is not doing. Three shapes must land there, each with a contrastive
   example:

   - **No live process.** An essay, op-ed, explainer or history whose concrete instances are
     past or elsewhere, and whose present-tense content is prescriptive. *(Dawn, raw 7.359.)*
   - **No outcome yet.** An appointment, a launch, a funding round, a pledge, a plan, a
     ribbon-cutting. Something has been *announced* or *staffed*, not *delivered*.
     *(TSA, raw 6.901; the Namibian minister, raw 5.117.)*
   - **No beneficiary.** An award, an honour, a career profile or a biography, where the
     subject is a person's standing rather than anyone's changed circumstances.
     *(Sylvia Earle, raw 4.939.)*

   ⚠️ **Write it as "is the process live", NEVER as "is the subject recent".** The owner's
   framing on 2026-08-22 was *"thriving should be about today, not the past"* and the
   defect is real, but a recency rule keyed on when the events happened would suppress
   **transitional justice** — §5b's Unifesp/DOI-Codi row is a 1970s crime and a **living**
   process, and §5b calls it *"the purest correction for presentism"*. The discriminator is
   **a named actor doing something now, with someone it reaches**, not the age of the
   subject matter.

   ⚠️ **Do not write a "large groups, not individuals" rule.** The owner raised it on
   2026-08-22 and the measurement kills that implementation: `benefit_distribution` already
   carries beneficiary breadth, and **zeroing it entirely moves the TSA row only
   6.901 → 6.280**, still tier high. It is weight 0.10 against `human_wellbeing_impact` at
   0.30, and re-weighting is closed (§2). What the example actually wants is
   **beneficiary count, not protagonist count** — an individual is frequently the *vehicle*
   for a collective process ("one nurse's clinic now serves 4,000 people"), and a rule keyed
   on whether a person is named would destroy that. Handle it under "no beneficiary" above.
3. **Close the two documented cap gaps**, both found in the 2026-08-10 adjudication:
   `corporate_finance` (max 2.0) enumerates stock prices, earnings, funding rounds,
   valuations, M&A, IPO — **prudential regulation is none of them**, so no cap fired on
   the EBA dashboard and `justice_rights_impact` returned 5.00 on an article with no
   rights claim. And `PURE SPECULATION` (cap 3.0) did not fire on a "could have
   consequences" ministerial aspiration with no programme behind it.
4. Caps must be **arithmetic** ("no dimension may exceed X") or per-dimension
   **subtractions** — an advisory `max_score` is read as advice and ignored (playbook §1).
   Enumerate carve-outs exhaustively, one contrastive example each.
5. **Verify on a ~30-article calibration sample before any batch run** (playbook §1). The
   sample must contain: all **18** adverse records (9 class A, 9 class B), the **§5b no-regression set**, and a
   hand-picked set of research abstracts.
6. Revisit the dimension set. ⚠️ **ADR-012's boundary map is stale**: it lists Thriving as
   `human_wellbeing 0.40 / justice_rights 0.25 / evidence_level 0.10 / benefit_distribution
   0.10 / change_durability 0.15` and states *"social_cohesion_impact removed from Thriving
   in v1"*. **v7 ships `social_cohesion_impact` at 0.20, its second-highest weight** — and
   it is the dimension class A rides ("community vows to unite" earned 6.38 on a row whose
   only event was a meeting). The Thriving↔Belonging boundary rule rests on a map that does
   not describe the deployed filter. Resolve this in the ADR as part of v8 — a *definition*
   question, in scope, unlike the re-weighting closed in §2.

**Gate A:** owner reads the new prompt and the 30-article calibration output before any
paid run. No exceptions — playbook: *run the review battery BEFORE the paid oracle run.*

### Phase B — relabel
Full re-score under the new prompt. **Do not** re-score only the mid-range (§2, last row).
- **Oracle: not yet decided, and n=3 is not enough to decide it.** Measured 2026-08-20
  (§1f): **Gemini fires 3/10 caps vs DeepSeek 1/10 vs qwen3:14b 0/10 — over all ten rows
  (3 class A + 7 class B), not class A alone**; one of Gemini's three is `corporate_finance`
  on a class-B row. On the three class-A rows specifically, Gemini fired `doom_framed` twice
  and DeepSeek once — replicating the `cultural_discovery` v5 result (Gemini 60% /
  DeepSeek 26%). So **on this filter's priority class Gemini is the stricter arm**, which
  is the opposite of the standing preference for DeepSeek. ⚠️ Class-A means differ by
  0.18, well **inside** the 0.82 oracle noise, so this is a hint, not a decision. Run the
  ADR-020 bake-off properly on a harm-weighted sample with k-run averaging before
  committing the full relabel. Cost note: DeepSeek is **~7× cheaper** (cd v5: ~$11 vs
  ~$25), so if it wins on bias it wins outright — but **strictness comes from the
  mechanism, not the vendor** (§1f: the worst row fails on all three).
- **qwen3:14b on b650 is a working free arm** — 10 articles in ~2 min on the idle 3090 Ti.
  Ollama there is **localhost-only**; tunnel with
  `ssh -f -N -L 11435:localhost:11434 b650-gpu`. It fired **0/10** caps, so it is a
  consensus arm, not a candidate primary for a penalty-flag filter.
- Volume estimate **≈$12 for ~6,590 rows** ⛔ **SUPERSEDED 2026-08-29 — measured: ≈$6.9 reordered / ≈$21.7 as-is at k=3; see §6**. The **row count is now confirmed** (Phase 0: 5,271 + 659 + 660). ⚠️ **The $12 itself is still unverified** — it is an estimate nobody has priced against a real batch.
- ⛔ **Never oracle-re-score a `gn_*` row** — they are sub-300-char headline echoes
  (`memory/google-news-corpus-hypotheses.md`).
- The 300-char floor applies here and **only** here:
  `ground_truth.batch_scorer.make_oracle_prefilter`. Do not put it in a prefilter (#93).

**Gate B-A — BLOCKING (class A).** Every class-A record scores below `max_acceptable_wa`
= **3.85**. ⛔ **As a k-run mean, never a single run** — oracle run-to-run noise is
**0.82 mean / 2.25 max** (§1f), so a one-shot "below 3.85" is not a measurement. Use
k ≥ 3 and report the band; the margin must clear the band, not the #95 0.16 floor, which
is the wrong floor for this population (`feedback-noise-floor-per-population`).
⚠️ Judged against
**editorial upper bounds, not oracle ground truth** — the records are `labelled_by`
editorial judgement and the oracle is blind to this class (§1a). **Say so in the report;
do not imply ADR-021 coverage it does not have.** ⚠️ **B5 is only partially cleared**: the slice is **9** class-A records (§1g), not 4, but 9 is still thin for a blocking gate and 5 of them carry **editorial** labels
adjudicated on **300–340-char excerpts**, against full-text articles of 2,107–5,786
chars (6–16% read). The repo's own rule — *excerpts are not sufficient; three of five
drafts reversed on full read* (`datasets/adverse/2026-08-09-reader-flags.md`) — applies
here and is **not yet discharged**. Re-read all 10 in full before this gate blocks anything.

**Gate B-B — REPORTED (class B).** Re-run the §1b measurement on the *new* labels, same
script, same seed, same permutation design. **The academic/non-academic on-lens gap must be
inside noise.** Per the owner ruling, a miss here is escalated for a call, not an automatic
fail.

**Gate B-C — no-regression (§5b).** Every row in the no-regression set still scores **above**
the op-point. A v8 that fixes class A by suppressing transitional justice or recovery
narratives has failed, whatever Gate B-A says.

### Phase B2 — hard negatives for the student residue (playbook §4b, $0 oracle)

**Why this phase exists:** §1f measured that two of three class-A rows are the *student*
disagreeing with all three oracles. **No prompt change reaches them.** Playbook **§4b
production-feedback retraining** is the pattern that does, and it costs nothing in oracle
budget because the labels come from adjudication, not re-scoring.

1. Collect the student's production positives above the op-point on the class-A shapes.
2. **Panel-verify** a sample (multi-model blind panel or owner spot-check) against the
   §1e test. ⚠️ **Full text, not excerpts** — three of five drafts reversed on reading
   the article in the 2026-08-09 pass.
3. Add each confirmed FP as a **hard negative** (`label: negative`, same features).
4. Retrain on the augmented corpus alongside the Phase B relabel.

⛔ **Not §4a.** Probe-split keeps probe-high + model-high rows "as-is", which is exactly
where class A lives (§2).

⚠️ **Guard against over-correction here specifically.** Hard negatives teach a pattern,
not an instance. Every §5b no-regression row must be scored before and after this phase.

### Phase C — train, probe, calibrate
- `load_base_model_for_seq_cls()`; PEFT adapters in **old key format**; never
  `resave_adapter.py`.
**The probe is RETRAINED, not inherited (ruling 3).**
⛔ **The reason given here on 2026-08-21 was WRONG and is replaced.** It said the probe's
training data "was selected by the same 74 Latin-script patterns". It was not — the prefilter
never ran on this corpus at all (H-CV1 refuted 2026-08-22, Phase 0). *There is no
keyword-shaped population being carried forward.*

**The retrain still stands, on the surviving reasons:** (1) the corpus is being rebuilt
against four measured composition gaps (H-UP10, Phase 0), so a probe trained on the old
population would screen for the wrong distribution — in particular a **28.22%** positive base
rate against production's **7.74%**; (2) with the keyword rules gone the probe becomes the
**only** layer carrying multilingual selection, and the corpus it inherits is **4.57%**
non-Latin against production's **7.26%**.

- **Recall-first**, `scripts/train_probe.py --objective recall`: binary MEDIUM+ target,
  class-weighted BCE, threshold from the val recall curve at a target FN. ⛔ **Not** by
  minimising error — an L1-regression probe floor-collapses and drops needles.
- **Report FN@MEDIUM+, never probe MAE.** ADR-023's specificity rule does **not** apply
  here: for a recall-safe screen the false *negative* is the expensive error, because a
  screened-out article can never surface no matter what Stage 2 would have said.
- **Commit the `.pkl`** (`filters/human_thriving/v8/probe/*.pkl`, ~0.5 MB). The package is
  not reproducible without it; `.gitignore` already negates for this path.
- ⚠️ **Re-derive the threshold; do not carry 1.00 over.** v7's "0.9% FN on MEDIUM+" was
  calibrated when the op-point was **4.0**, before #102 moved it to 4.5 — the config
  comment says so itself. And at 1.00 the measured speedup is only **~1.05×** on a probe
  with MAE 1.04, i.e. v7's probe was barely earning its place.
- ⛔ **The threshold lives in CODE, not config.** `inference_hybrid.py` hardcodes
  `DEFAULT_THRESHOLD = 1.00` and **nothing passes `config.yaml`'s
  `hybrid_inference.stage1.threshold` into the constructor** (verified 2026-08-21 — no
  consumer in `filters/common/` or NexusMind's loader/`production_scorer`). They agree
  today so it is harmless *now*, but this is the `nature_recovery` 3.225-vs-0.75 shape:
  **editing the config value alone will do nothing.** Change both, or wire one to the other.
- ✅ **Train the probe on b650 — it is cleared for this.** The e5 path is bit-identical
  across boxes (max |Δ| 4.2e-6, zero screening flips, identical embedding checksums). The
  Gemma student is *not* — see Phase 0H.
- ⭐ **This is the layer that has to carry the multilingual load now.** The regex is gone;
  `multilingual-e5-small` is what replaces it. **Report the probe's FN@MEDIUM+ split by
  language and by script** — if it screens non-Latin content harder than Latin, ruling 3
  has been undone silently in a new place, and nothing else in this plan would catch it.
- Fit `calibration.json` (per-dim isotonic on val). Commit it.
- Ship `score_scale_factor: 1.0`. ⚠️ **v7 ships `1.1976`** — inert only because v7 has a
  `normalization.json`. Copying v7's config into v8 and shipping before normalization is
  fitted would silently stretch every score and defeat the gatekeeper design (playbook §8).

### Phase D — the gate
⛔ **Run this on CPU with `venv-prodparity`, or on gpu-server — never on b650's GPU**
(Phase 0H). b650-GPU flips **3 verdicts at 4.5**, this filter's op-point, and reports
specificity 0.9662 where production reports 0.9730.

`scripts/gate/ground_truth_gate.py` against **held-out oracle ground truth** (ADR-021),
never against v7. `--noise-floor 0.16` (default). Verify the report writes to
`filters/human_thriving/v8/ground_truth_gate.json` and that its threshold, model name and
`n_labeled` match this filter — gate files have cross-contaminated before.

**Report recall + specificity with the split's positive rate. Never rank on MAE** (ADR-023).

### Phase E — normalization
- `MIN_NORMALIZATION_ARTICLES = 200`; below it production **silently** falls back to
  `score_scale_factor`.
- **Close the cold-start at deploy** by rescoring a production-representative historical
  harvest, not the enriched val set (playbook §6). A fresh name means a fresh
  `data/filtered/human_thriving/` — there is no live history to fit against, so this is
  mandatory, not optional.
- Fit anchored at the op-point. `raw_min == op_point` by construction; **4.5 is accepted
  with zero margin**, so the op-point cannot rise.
- An op-point move touches **four** places in one commit: `TIER_THRESHOLDS` in
  `base_scorer.py` (the runtime one), `config.yaml scoring.tiers` (documentation),
  `normalization.json stats.raw_min`, and `tests/unit/test_normalization_op_point.py`.

### Phase F — deploy
Follow `docs/FILTER_PLAYBOOK.md` "Deploy safety checklist" in full (8 items). Additionally:

#### F1 — package parity gate ⭐ *added 2026-08-21 (owner)*

⛔ **v8 does not ship until its package matches `nature_recovery v4`.** Measured
2026-08-21, only **two** of six live packages are complete — `nature_recovery v4` and
`cultural_discovery v5`. `uplifting v7` is the worst at **7 of 14 artefacts missing**, and
it is the oldest filter: the learning accumulated into the newer packages and uplifting
never received it. Remediation for the others is llm-distillery#126.

| artefact | v8 must ship | note |
|---|---|---|
| `config.yaml` | ✅ | per-dim `description:` is a **Hub-upload requirement** |
| `prompt-compressed.md` | ✅ | |
| `README.md` | ✅ | |
| **`DEEP_ROOTS.md`** | ✅ | ⭐ **the one that matters.** v8's whole point is the narrowed predicate (§1e); `uplifting` has never had a file stating what the lens is *for*, which is arguably upstream of #107 — the scorer faithfully served a definition nobody had written down |
| **`STATUS.md`** | ✅ | deployment state, op-point, gate date |
| **`README_MODEL.md`** | ✅ | Hub model-card source (needed even under NO_HUB — §3c) |
| **`training_metadata.json`** | ✅ | model, epochs, LR, batch, max_length, warmup, train/val counts, trainable params. **v7's training run is not reproducible from its package** |
| **`training_history.json`** | ✅ | per-epoch train/val MAE + per-dimension MAE |
| `calibration.json` | ✅ | + **`calibration_report.md`** — v8 has a rewritten prompt and a retrained probe, so the narrative is not optional here |
| `ground_truth_gate.json` | ✅ | ⚠️ verify threshold / model / `n_labeled` match **this** filter — gate files have cross-contaminated before |
| `normalization.json` | ✅ | fitted at deploy from a historical rescore (Phase E) |
| `probe/*.pkl` | ✅ | retrained (Phase C); package is not reproducible without it |
| `__init__.py` | ✅ | |
| `base_scorer.py` | ✅ | ⚠️ **added during review** — an `ls` pass over docs alone can bless a package that cannot score |
| `inference.py`, `inference_hybrid.py` | ✅ | `filter_loader` sets `hybrid_class` from the **presence** of `inference_hybrid.py`, so omitting it silently disables two-stage scoring |
| `model/adapter_config.json`, `model/adapter_model.safetensors`, `model/tokenizer*.json` | ✅ | pre-placed on gpu-server (F3); gitignored locally, must exist on the box |
| ~~`prefilter.py`~~ | ⛔ **NO** | see F2 |

**Verify by `ls`, not by assertion** — the same discipline llm-distillery#126 records.

#### F2 — v8 ships NO `prefilter.py` ⭐ *owner ruling 2026-08-21*

Not an empty prefilter, not one with the lens rules commented out — **no file**. A required
artefact that exists and does nothing is this repo's recurring failure mode: `expected_pass_rate`
declaring gates that did not exist, `hybrid_inference.stage1.threshold` that no code reads,
`cap_applied` stamped on 236,879 rows and never once populated.

⛔⛔ **`_load_prefilter` is an `@abstractmethod`** on `FilterBaseScorer`
(`filters/common/filter_base_scorer.py:229-232`). Dropping the *file* is safe — every loader
guards on `.exists()` and `verify_filter_package.py` never mentions it — but a v8
`base_scorer.py` that omits the *method* **cannot be instantiated**: `TypeError` at scorer
startup, and per §3a the gpu-server scorer validates every discovered filter at startup, so
**all filters score nothing**, unattended. v8 must define:

```python
def _load_prefilter(self):
    self.prefilter = None   # owner ruling 2026-08-21: no per-lens keyword prefilter
```

⛔ **`scripts/analysis/filter_completeness.py` listed `prefilter.py` in `core`** — the very
tool F1 invokes would have reported a correct v8 as INCOMPLETE. Removed 2026-08-21; if it is
back, this ruling was reverted.

⚠️ **Both recommended copy-from templates (`nature_recovery v4`, `cultural_discovery v5`)
still ship a `prefilter.py`.** Copying either re-introduces it — delete after copying.

`memory/filter-doc-standard.md` was amended the same day: the core is now **6 files**, and a
per-lens prefilter is optional with omission as the default for new filters.

⚠️ **Three mechanisms this does NOT remove** — restated here because Phase F is where
someone will reach for the missing file: the **300-char oracle floor**
(`make_oracle_prefilter`, #93), **`validate_article`**'s empty-content check (**empty is not
short**), and the shared **commerce** gate (ADR-004, commerce-only by its own terms) and the separate
**obituary / violence** gates — all of which, unlike the lens prefilter, actually run in
production.

#### F3 — rename mechanics

- Decide and write down the cutover date **before** deploy (§3a) — dropping
  `filters/human_thriving/v8/` beside `filters/uplifting/v7/` creates a **seventh filter**
  scored in parallel, automatically.
- Coordinate the ovr.news field change against a **re-run** of the §3b enumeration.
- Keep `uplifting v7` in place as the rollback; rollback = delete the v8 dir.
- ⛔ **Pre-place `model/` on gpu-server before `deploy_filters.sh`** — guard D aborts
  without it, and a weightless highest-version means the scorer never starts and **all
  filters score nothing**, unattended.

## 5. Acceptance criteria

Owner decision 2026-08-07: the open v7 fidelity defects **are not separate work — they die
in this retrain or they do not**. Each becomes a held-out eval slice, and each carries the
**±0.16** band: an article predicted within 0.16 of a bar is **indeterminate** and cannot be
counted as a pass. Ordered by the 2026-08-20 priority ruling.

| # | Criterion | Slice | Judged against | Blocking? |
|---|---|---|---|---|
| **1** | **Class A dies.** Every harm-adjacent record scores below **3.85**, clear of the noise floor | `datasets/adverse/uplifting.jsonl`, class-A rows — **9** (`class` starts with 'A' — present on every row since 2026-08-21, so the slice is machine-selectable) | editorial upper bound (⚠️ **not** ADR-021 oracle truth — the oracle is blind here) | **YES** |
| **2** | ✅ **RESOLVED 2026-08-30 — the criterion no longer fails before v8 exists.** The Rwanda–EU row was DROPPED (it failed `raw > 4.5` under every prompt including v7, and a delta conversion fails too at −0.783) and REPLACED by two rows; see §5b and `docs/decisions/2026-08-30-v8-phase-b-rulings.md` §2. **No regression.** Every no-regression row still satisfies its own `assertion` — ⚠️ **not a uniform "above the op-point"**: the Unifesp row is a **delta**, the rest are `raw > 4.5`. See §5b | `datasets/adverse/uplifting_no_regression.jsonl` — ⛔ **this cell states no row count and no tally of assertion types, deliberately.** Both were stated here before and both went stale on 2026-08-30 when the set changed; a count in a document is a second copy of a fact that lives in a file. `wc -l` it. | editorial judgement, owner-confirmed | **YES** |
| **2b** | **The student agrees with its own oracle on class A.** For every class-A record, `\|student_raw − oracle_k_run_mean\|` is inside the oracle band. *New 2026-08-20: two of three class-A rows are the STUDENT disagreeing with all three oracles (§1f) — a criterion judged only on labels would pass a v8 that still ships them* | class-A slice | k-run oracle mean | **YES** |
| **3** | **Class B shrinks.** Academic/non-academic on-lens gap inside noise on the new labels | 660-row held-out oracle split | ADR-021 oracle ground truth | reported; miss → owner call |
| **4** | **Class B, adverse rows.** The **9** class-B records score below 3.85 | `uplifting.jsonl`, class-B rows | editorial upper bound | reported — ⚠️ **status needs an owner call**, see §1h: two of the nine are owner-flagged and outscore every class-A row |
| **5** | **NM#231 — non-English.** The 19 panel-confirmed articles clear the op-point, **and** the English/non-English mean gap is reported on one denominator — *reported*, not "improved", so v9 has a baseline | 19 articles | panel | ⛔ **blocked, see B2** |

⚠️ **Criteria 1 and 5 pull against each other.** Class A wants the scorer to attend to the
dominant subject; NM#231 wants it to stop discounting non-English framing. **A threshold
move trades them against each other.** Do not resolve either that way.

⚠️ **Criterion 1's bar does not travel.** `raw ≥ max_acceptable_wa + 0.16` = **4.01** is
specific to uplifting's 3.85. Other filters' bars are far lower (`nature_recovery` 0.6414,
`solutions` 1.0918–1.13, `belonging` 1.6446, `cultural_discovery` 1.6154–2.1867). Nothing
enforces either form in code — `grep -r 'assertion_margin\|max_acceptable_wa'` over `*.py`
returns **zero hits**, so the stored margins are documentation of a check that was made, not
a check. **v8 should close that**: make the adverse suite an executable test.

### 5b. The no-regression set — things that LOOK like false positives and are not

⭐ **ASSEMBLED 2026-08-23 as `datasets/adverse/uplifting_no_regression.jsonl`.** Until then
this set existed only as the table below — prose, referenced by three separate gates (step A5,
Gate B-C, and acceptance criterion 2, which is marked **BLOCKING**) and executable by none of
them. Same shape as §5's own note that the stored `assertion_margin` values are *"documentation
of a check that was made, not a check"*.

⛔ **The Namibian row in the table below is NOT an article and is not in the file.** *Namibian
child-welfare / gender-equality policy items* has **no article behind it**. Its only concrete
instance, `south_african_namibian_6ec2eb173e48` ("Boys must not be left behind, says child
welfare minister"), is one of the **18 accepted adverse rows** (class B, raw 5.1166), where it
carries a *scope warning* — "the boundary is announcement vs outcome, not 'policy is adverse'".
That is a **labelling caveat on an adverse row**, not a row that must score above the op-point,
which is why its "reader's real objection" cell is `—`. **Criterion 2 cannot be evaluated
against it.**

⚠️ **This paragraph read *"it is THREE articles, not four — do not re-count this set as four"*
until 2026-08-30, and that wording is retired, not reversed.** It was correct about the
*Namibian* row and it is still correct about it. But it stated a COUNT to make a point about
MEMBERSHIP, and the count went stale the moment the set changed: the file now holds **four**
articles (Rwanda–EU out, two lens-overlap rows in), so a reader following the old sentence would
have "corrected" a right number to a wrong one. ⛔ **Do not restate the count here at all** —
`wc -l datasets/adverse/uplifting_no_regression.jsonl` is the answer, and the reason this
document should not carry a second copy of it.

✅ **RULED 2026-08-30 — the Rwanda–EU row is DROPPED and REPLACED; criterion 2 no longer
fails.** Measured 2026-08-29 under one judge (`deepseek-chat`), k=3, full article text: **v7
prompt 1.600**, v8 as-is **0.817**, v8 reordered **0.817**, against an asserted `raw > 4.5`. Its
`assertion_basis` had said the baseline was never recorded and had to be established first; it
now is, and it is **2.9 points below the op-point the row was asserted to clear**. ⛔ **The
delta conversion — the correction the Unifesp row received on 2026-08-23 — does NOT rescue it:**
v8 − v7 is **−0.783**, i.e. lower, and that exceeds the oracle decoder run-to-run floor (0.436
mean / 0.687 max), so it is not noise; both v8 arms landing on **exactly** 0.817 is the scope
gate firing deterministically. **No assertion this set can express is satisfiable for that row.**

The cause is a collision between two rulings both dated 2026-08-23 — this section keeps the row
as legitimate lens overlap (ADR-015), while *"money committed is not a protection established"*
(§1) covers its headline exactly: *"46 millions de dollars **mobilisés** auprès de l'UE"*. Under
that ruling **0.817 is the prompt working as instructed**. ⛔ **The money-committed rule was NOT
softened** — three of the four stable step-1 op-point crossings depend on it. The retired row
keeps its full reason in `datasets/adverse/uplifting_no_regression_retired.jsonl`. Evidence:
`docs/evidence/2026-08-29-v8-h-v8-9-adjudication/` § *Step 2*; ruling:
`docs/decisions/2026-08-30-v8-phase-b-rulings.md` §2.

✅ **Two replacement rows carry the ADR-015 lens-overlap guard**, both selected with the baseline
recorded BEFORE the assertion was written, both `stage_used == "stage2"` on every lens read, both
with native text clearing the 300-char oracle floor without the enricher, and both verified
absent from the drawn corpus and the held-out cohort while present in the drawable pool:

| row | lang | native ch | uplifting v7 raw | also above its own op-point |
|---|---|---|---|---|
| Fast Company, *"London's ULEZ cleaned up the city's air. Then children's lungs got bigger"* | en | 5,780 | **6.683** (+2.183) | solutions 5.032, cultural_discovery 4.391 |
| Welingelichte Kringen, Greek lignite closures → up to 42% fewer cardiac admissions | nl | 2,601 | **6.474** (+1.974) | solutions 5.280, nature_recovery 4.497, cultural_discovery 4.907 |

⛔ **Both had to clear the #107 narrowing, not merely uplifting v7's scoring behaviour** — the
Thriving lens is *a process going well **for people***, excluding harm-answered-only and
institution-beneficiary. That criterion eliminated every pure-ecology candidate (a crane census,
monkey-corridor bridges, oyster-shell reef restoration) despite all of them scoring well above
the op-point on uplifting v7. ⚠️ It also eliminated the sharpest available test of the
money-committed boundary — Die Presse's *"18.736 Haushalten bleibt die Delogierung erspart"*
(uplifting 6.352, solutions 5.805, money **spent** with 42,291 counted beneficiaries) — because
its **producer text is 149 chars** and its 2,033 are enrichment.

⛔ **The corpus drawer now excludes the no-regression ids by construction** and refuses to run
without the set. Before 2026-08-30 nothing did: the first draw was disjoint only because every
row then in the set had aged out of the window. The two new rows ARE in the pool, in a design
cell whose inclusion probability is **0.0794**.

✅ **The two rows that were in the set at the time of the 2026-08-29 run PASS under both v8
arms** (same run): Rappler **4.900** reordered / **5.350** as-is, every individual run clear of
the op-point; Unifesp **4.367** reordered / **3.983** as-is against a v7-prompt **2.950** — i.e. the reorder scores the transitional-justice
row **+1.417 above v7**, the best of the three prompts tested. **Neither §5b hazard is
suppressed by the reorder.**

⚠️ **The rows carry DIFFERENT assertions — do not read the set as a uniform "above the
op-point".** The Unifesp row is a **delta**: it was scored by `cultural_discovery` and never by
`uplifting`, so "above the uplifting op-point" is not a claim its history supports; what it tests
is that the v8 rule does not suppress transitional justice. The other rows carry `raw > 4.5`.
⛔ **Read the per-row `assertion` / `assertion_basis` fields — this paragraph deliberately states
no tally**, because the previous version's *"only two are op-point assertions"* went stale on
2026-08-30 along with the row count above it.

⛔ **The lesson the dropped Rwanda–EU row leaves behind, which is why it is worth this much
space:** it was admitted with an assertion and **no `observed` block**, because it had been
*rejected* as adverse and no baseline was ever recorded. Its own `assertion_basis` said to
establish one first. Nobody did, for a week, and the gate that depended on it was marked
BLOCKING the whole time. **A row without a recorded baseline above the line cannot detect a
regression, and admitting one is admitting a gate that cannot fail for the right reason.** Both
2026-08-30 replacements had their baselines recorded before their assertions were written.

Each of these was flagged (twice, for the first) and **adjudicated not-adverse**. A v8 that
suppresses them has traded a reader-facing defect for a worse one: defining a whole category
of constructive journalism out of the lens.

| article | why it belongs | the reader's real objection |
|---|---|---|
| Unifesp forensic work at the DOI-Codi/SP dictatorship torture site (`cultural_discovery`, raw 6.11) | a **living** university doing forensic work on state crime **today** — a process going well now, and the purest correction for presentism | the ovr **summary title** led with the blood residue and buried the accountability → ovr.news#298 |
| Rappler, "The silent crisis on our plates" (`uplifting`, raw 6.49) | read in full (13,107 chars) it is a **recovery** — closes on "learning how to simply enjoy eating again" plus a help-seeking note | **rank**, not membership: a harm-heavy opening carried it to the top of the feed |
| ~~Rwanda–EU $46M agricultural resilience financing~~ **DROPPED 2026-08-30** | was: a genuine solutions story that may **legitimately** also be uplifting (ADR-015) | none — but it scored 1.600 under v7 itself, so it could never test that. Replaced by the two rows above |
| Namibian child-welfare / gender-equality policy items | the boundary is **announcement vs outcome**, *not* "policy is adverse" | — |

⛔ **Two hazards this set exists to prevent**, both recorded on 2026-08-05 and 2026-08-09:
suppressing **transitional justice** (truth commissions, mass-grave identification,
war-crimes forensics) and suppressing **recovery narratives** as a category. Also live but
**RETIRED as a probe candidate 2026-08-20 (owner):** the Global Voices Assyrian-genocide
essay (`belonging` raw 7.67 → normalized 9.93). The owner's position is that it reads as
both false positive and true positive. ⛔ **A two-sided row is not probe material** — it
tests the boundary, and the boundary is where noise makes the test meaningless — so it needs
no ruling and is **not** a blocker on Phase A. It stays in `candidates/` as history.

⚠️ **Method rule from the same adjudication: excerpts are not sufficient.** Three of five
drafts reversed on reading the full article. The Rappler row was drafted "probable adverse"
off a 190-character excerpt and is now a no-regression row.

---

## 6. Costs

| Item | Estimate | Confidence |
|---|---|---|
| Phase A prompt + calibration | **$0.87 SPENT** (n=200, k=3, both arms, 1,200 calls) | measured 2026-08-29 |
| Phase B full re-score, k=3 | **≈$6.9 reordered / ≈$21.7 as-is** | measured $/article; ⚠️ the k=3 repeat discount is UNPROVEN at corpus scale (without it ≈$10.3 / ≈$54.1) |
| Phase C training (b650, 3090 Ti 24 GB — Phase 0H) | ~0 marginal | reliable |
| Adjudication time | **the real cost** | owner's call |

*"Nothing verifies an estimate"* — three cost estimates were wrong in one evening on
2026-08-17, every correction from measuring. B1 confirmed the 6,590 rows; the old **≈$12**
was never confirmed and is now superseded by measured per-article prices (2026-08-29).
⛔ **And the measurement itself was wrong once**: the first write-up divided a `$0.02f`
ROUNDED DISPLAY by 200 instead of re-deriving from the token counts in the same file —
$0.85 vs a true $0.867, and 5.5× vs a true 5.27×. Re-derive from `usage`, never from the
summary line.

---

## 7. Blockers — clear these before Phase B

- ✅ **B1 — CLEARED 2026-08-21.** The v7 corpus is on **gpu-server** at
  `~/llm-distillery/datasets/training/uplifting_v7/` — train 5,271 / val 659 /
  test 660 = **6,590 rows**, matching the cost estimate exactly, with full article
  text present on every row. See **Phase 0**. Residual: the *raw scored* file (with
  `content_type` and evidence strings) has not been located — only the prepared
  splits, which keep the six numeric labels alone.
- **B2 — NM#231's slice cannot be enumerated.** `data/held-out/golden-uplifting-2026-06-12.jsonl`
  is neither on disk nor tracked in git (`git log --all` on `data/held-out/*` returns
  nothing), despite NM#231 describing it as "(committed)". **Recover or rebuild it, or
  criterion **5** (NM#231) is unjudgeable.**
- **B3 — `datasets/adverse/` is unreachable from any index.** #125's finding was already
  recorded there on 2026-08-10 — mechanism included — and was re-discovered as new on
  2026-08-20 because checking `memory/` and the tracker is not checking `datasets/adverse/`.
  Add the pointer. ⚠️ `CLAUDE.md` is at its character budget (#123) — run
  `python3 scripts/verification/check_index_budget.py` before adding a row there; the
  `docs/TODO.md` top block is the cheaper home.
- **B4 — a missing `calibration.json` does not block anything.**
  `NexusMind/src/filters/filter_loader.py:_check_required_artifacts` **does** check for it —
  but only `logger.warning`s and returns the config anyway, and `_load_calibration` fails
  silent. Nothing in `llm-distillery/scripts/deployment/` mentions `calibration.json` at all
  (`grep -rn "calibration.json" scripts/deployment/` → empty). This is the `cd v6` failure
  mode of 2026-08-13 and it is still open. **Fix before Phase F**, as a preflight guard.
- 🟡 **B5 — the class-A slice: 4 → 9 records (2026-08-21, §1g). Partially cleared.**
  Criterion 1 is now judgeable, though 9 is still thin for a blocking gate and the five
  new rows carry **editorial** labels adjudicated on excerpts, not oracle ones. Reader flags are the **only**
  independent source (§1a), so growing the slice means pulling ovr.news flags
  (`GET /api/flag`, read-only — 89 pulled on 2026-08-09, 35 with free text, **15 off-lens
  complaints**) and adjudicating them against the §1e test. **This is the critical path
  under the 2026-08-20 ruling, ahead of the re-score.** Two limits of the source, both
  measured: ovr no longer records a reason category (the `wrong_lens` counter on
  `/ops/flags` reads 0 and is **vestigial** — do not read it as "no lens complaints"), and
  **the flag does not record which lens the reader was viewing**, so lens attribution is
  inferred from where the article scored highest above its own p99.

---

## 8. What this plan changes about the playbook

`docs/FILTER_PLAYBOOK.md` was last touched **2026-08-13**, seven days before the #125
diagnosis, and neither 2026-08-20 finding is in it. Items 1–2 are **owed once v8 validates**
them — deliberately **not** made yet, because the playbook records *proven* lessons:

1. **§4a needs a precondition.** "Improve a deployed filter" assumes a **model** defect. If
   the defect is in the **labels**, step 4 ("keep probe-high + model-high as-is") preserves
   it and step 2 (zero the probe-negatives) bakes it in. Add: *establish whether the defect
   is in the model or the labels first — re-derive the weighted average from the oracle
   labels with no model in the loop, as #125 did.*
2. **A serialization boundary is part of the call path.** `deploy/gpu-server/main.py:1325`
   rebuilds the scorer payload as `{"title", "content"}`, so `metadata.*` never crosses.
   Two designs for a primary-literature cap would each have read `None` on 100% of rows
   while passing every unit test. 6th occurrence of the verify-call-path rule.

---


**Item 3 is already done, not owed:**

3. **The filter documentation standard changed (done 2026-08-21).**
   `memory/filter-doc-standard.md`'s core dropped from **7 files to 6**: a per-lens
   `prefilter.py` is now optional, with omission the default for new filters. It also now
   warns that **`belonging v1` — the template the standard was written from — does not
   satisfy its own core** (no `README_MODEL.md`); copy from `nature_recovery v4` or
   `cultural_discovery v5`, the only two complete packages. **llm-distillery#126 covers
   `solutions v6` only** — its own Scope section says so; the fleet matrix is context there,
   not committed work. `uplifting v7`'s gaps are handled by F1 in this plan.

## 9. Open questions for the owner

1. **Oracle choice for the full relabel.** Measured on n=3, **Gemini is the stricter arm
   on class A** (caps 3/10 vs DeepSeek 1/10), which cuts against the standing DeepSeek
   preference — but the gap is inside the 0.82 oracle noise. **Run the ADR-020 bake-off
   on a harm-weighted sample with k-run averaging first, or pick now and accept the risk?**
2. ~~The Assyrian-genocide essay.~~ **RETIRED as a blocker 2026-08-20** — the owner's
   position is that it reads as both FP and TP. A two-sided row is not probe material, so
   it needs no ruling; it stays in `candidates/` as history. *(It also stops being needed:
   §1g's six promotions now set how far the class-A rule reaches, using unambiguous rows.)*
3. **Cutover shape** — parallel-run `uplifting v7` and `human_thriving v8` for a fixed
   window, or cut straight over? Parallel is safer and roughly doubles Thriving inference.
4. **Dimension set (§4 Phase A step 6)** — is `social_cohesion_impact` at 0.20 intended
   for Thriving, given ADR-012's boundary map says it was removed at v1 and the
   Thriving↔Belonging rule depends on that? It is also the dimension class A rides.
5. ~~B1 — where is the v7 training corpus?~~ **ANSWERED 2026-08-21**: gpu-server, `~/llm-distillery/datasets/training/uplifting_v7/` (Phase 0). Residual question: the *raw scored* file with `content_type` and evidence strings is still unlocated.
