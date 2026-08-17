---
name: corroboration-feature-hypotheses
description: What is confirmed, refuted and untested about features for corroboration/story matching — cosine, time delta, NER entity overlap. Read before proposing any NER or matching-feature work.
metadata:
  type: project
---

# Corroboration feature hypotheses

**Created 2026-08-07 (late).** The owner asked whether NER could be "just another
feature" alongside the vector-space output and time dependency. It already is —
and the answer to whether it *works* is more settled than the board suggests.
This file exists because that finding was reachable only by reading two
NexusMind investigation docs that no chain on the board points at.

Canonical sources, both in NexusMind:
- `docs/investigation/story-dedup-feature-augmentation.md` — the design memo and
  the first-run readout (§P5.5). This is the one with the numbers.
- NexusMind `docs/investigation/corroboration-next-phase-plan.md` — **DRAFT, its ordering
  refuted by a review 2026-08-06**; read the `RECOMMENDED ORDER` block, not §2.
- Parent issue: **ducroq/NexusMind#188** (open) and **NM#301** (open). *NM#213 is
  the origin issue and has been **CLOSED/COMPLETED since 2026-05-23** — corrected
  2026-08-07 after it was cited as live in four places, including two issues filed
  the same day. Cite #188/#301 for anything actionable.*

## The feature set already exists, and it is exactly the obvious three

V1 per-pair features (memo §P3):

| feature | what it is |
|---|---|
| `title_cosine` | E5(title) cosine — the vector-space output |
| `pub_time_delta_hours` | absolute hours between publication timestamps |
| `entity_jaccard` | spaCy NER set Jaccard, with a one-token suffix fallback |
| `content_length_log_ratio_abs` | substrate mismatch (arXiv abstract vs news) |

`source_pair_prior` was deferred to V2. Model class is locked to L2-regularized
logistic regression on standardized features — inspectable coefficients were a
hard requirement, not a preference.

## CONFIRMED

- **The V1 experiment FAILED all four pre-committed ship-gate criteria.** LOCO
  cross-validation: precision **0.000**, recall **0.000**, 0 true positives
  across all 8 folds. Production's plain cosine-at-0.88 baseline scored
  **0.933 / 0.636** on the same slice. The dumb threshold beat the model.
- **The cause is sample size, not the features.** n=**23** should-cluster pairs,
  and **case_1 alone supplies 21 of them**. Hold case_1 out and training has two
  positives; inner-CV AUC on that fold is 0.379–0.478 — worse than random, with
  exploding coefficients (`ej=-6.728, dt=-7.132`). The memo's own carry-over
  says n=23 is "sufficient for direction-finding but insufficient for production
  threshold-locking", and calls it the load-bearing constraint.
- **`title_cosine` failed the same way NER did.** Single-feature `title_cosine`
  (baseline B3) also got 0 TP across LOCO — a topic-bucket attractor pushed
  negatives above real positives. **So this is not a story about NER being the
  weak feature.** Anyone re-reading the readout as "entity overlap doesn't work"
  is reading half of it.
- **`entity_jaccard` learned NEGATIVE in 7 of 8 folds**, and the mechanism is
  known: spaCy-small extracts a **median of 2 entities per article**, so
  unrelated articles reach `ej = 1.000` on Latin-script token collision. Two
  entities is not a fingerprint.
- **Widening the label set did not help.** PERSON/ORG/GPE/LOC/EVENT/NORP/FAC
  still yielded ~2 entities/article. The problem is the extractor, not the
  schema.
- **The 5,000-char NER cap is a locked constant for a DIFFERENT problem.**
  `scripts/research/measure_matching_geometry.py:98`, headed "V1 settings,
  locked at design time", English-only (`en_core_web_sm`). NM#232's promised
  type set was derived from this English-only script — which is the root of its
  multilingual label-set problem.
- **spaCy label sets, verified by installing spaCy and printing
  `nlp.get_pipe("ner").labels`** (not from documentation prose):
  `xx_ent_wiki_sm` emits **PER/LOC/ORG/MISC only**. **English and Dutch** carry
  the full 18-label OntoNotes-style set including GPE/DATE/EVENT; **de/fr/es/it/pt
  carry the coarse four at every model size.** Dutch has the richest schema and
  the *worst* accuracy — `ents_f` 0.715 (sm) / 0.764 (lg) vs English 0.855,
  es 0.897, pt 0.903; Dutch LOC is 0.208. **So the non-English disadvantage here
  is quality, not schema** — which argues for persisting per-entity confidence
  and having consumers gate on it.

- **Which copy of a duplicated wire story survives: THE QUESTION IS STILL OPEN.**
  *An earlier version of this entry claimed "decided by HTTP completion order —
  arbitrary, not a source policy" and filed it under CONFIRMED. An adversarial
  review refuted the evidence on 2026-08-07 (night). Kept here in corrected form
  because the failure is instructive.*

  **Why my evidence was circular.** The argument was: both observed drops
  happened inside `concurrent_rss`, so `enabled_sources` order cannot explain
  them, so the winner is `as_completed()` completion order. But a cross-source
  drop is only **detectable** when the incumbent hash carries a source, and
  sourced entries exist only from the single run that deployed the stamp:
  **4,116 of 40,693 hashes carry a source (10.1%); 36,577 (89.9%) are legacy bare
  floats.** Cross-run collisions are therefore *structurally undetectable* right
  now — "both drops were within one aggregator" is a restatement of what the
  detector can see, not a fact about the world. FS#133's own first comment said
  "do not conclude anything from `2` until roughly 2026-09-06". I concluded from
  those 2.

  **There are two mechanisms; I described the smaller one.**
  - *Within a run* — completion order via `as_completed()`. Arbitrary. This part
    stands, but it is **untestable with current instrumentation**: `feed_health.json`
    has 24 fields per feed and **none is a fetch duration**. I presented a guessed
    mechanism as a traced one.
  - *Across runs* — the larger and currently invisible population. `seen_hashes`
    persists (30-day TTL) and is consulted first, so the winner is whichever run
    **polled first**, set by `_filter_due_feeds` + per-feed `update_frequency`.
    Measured: GN-hosted feeds are **1 sub-12h, 201@24h, 110@≥48h**; non-GN are
    **159 sub-12h**. Cadence is a per-publisher property, so **cross-run loss is
    publisher-correlated, not unbiased.**

  **Two further claims of mine that are wrong.** (i) "The next run may reverse
  it" — false cross-run: a content-dropped item never reaches the `seen_urls`
  write, so its URL is never learned and it is **re-dropped every run until the
  TTL expires — sticky for up to 30 days**, deterministically. (ii) The base-rate
  dismissal was overstated: GN is **27.4% of items** in that run, all three
  sources in the two drops are GN-hosted, **p ≈ 0.02**. Not proof of precedence,
  but not the comfortable wash I claimed either. I over-corrected against my own
  earlier over-reading.

  **The finding that reframes the issue:** in the same run **6 cross-source
  syndicated stories SURVIVED dedup** (different snippet → different hash) against
  **2 dropped** — one survivor being the same story as one of the drops, via a
  third outlet. So exact-hash dedup is **not** what decides which outlet's copy
  reaches NexusMind. Near-duplicate survival, not exact-duplicate deletion, is
  probably where the corroboration evidence actually goes.

  **Consequence for step 3, correcting what this file said below:** the loss is
  **not** demonstrably unbiased across publishers, so a future `source_pair_prior`
  **cannot** yet be assumed safe from it.

- **STEP 4 RUN 2026-08-08 — the extractor was the problem, not the feature.**
  `xlm-roberta-large-finetuned-conll03-english` on **300 production articles**
  (60 each de/el/en/es/fr, from `filtered_20260808_170521`, 5,000-char budget to
  match V1):

  | | spaCy `en_core_web_sm` | XLM-R large |
  |---|---|---|
  | entities/article, median | **2** | **12** (mean 13.3, p10 6, p90 22) |
  | unrelated pairs at `ej = 1.000` | *the failure mode* | **0 of 4,000** |
  | unrelated pairs at `ej >= 0.3` | — | **0 of 4,000** (p99 0.056, max 0.200) |

  Per language: de 13.0, es 13.0, en 11.5, fr 11.5, **el 11.0**. **Greek —
  non-Latin script — matches the Latin-script languages**, so on entity *yield*
  there is no non-English disadvantage. Cross-language pairs (n=3,239): median
  0.0000, max 0.200, i.e. no spurious cross-script matching either.

  **This kills the token-collision mechanism outright.** V1's `entity_jaccard`
  learned negative in 7 of 8 folds because two entities collide; twelve do not.
  <!-- verify: manual — rerun /tmp/ner_measure.py pattern on a fresh sample; the claim is about the extractor, so it should reproduce on any production day -->

  **What it does NOT establish, and do not let it be quoted as if it does:** this
  measures only the **negative** side — that unrelated articles stop colliding. It
  says nothing about whether **true positives score high**, which needs the
  labelled pairs (step 3). The feature is now *plausibly usable*; it is not shown
  to work. **The n=23 / case_1-supplies-21 constraint is untouched by this.**

  Cost, since it bears on whether this can ship: **6 seconds for 300 articles** on
  one GPU after a 23s model load — ~50 articles/sec. Not a barrier.

## REFUTED

- **"NER is a bad corroboration feature."** Not established. It was measured
  once, at n=23, with an extractor that produced two entities per article, in a
  run where the cosine feature failed identically. That is not a test of the
  feature.
- **"Showing readers shared entities addresses NM#301."** ovr#222 is display-layer
  by its own description. NM#301 measures merged-pair precision at **0.560** on
  2-source clusters; rendering entity evidence under a claim that is right half
  the time makes it look substantiated rather than making it correct. Six-reviewer
  battery 2026-08-07 confirmed this as the strongest objection to the plan.
- **"Compute entity overlap inside the dedup stage instead — it's cheaper."**
  Refuted on five independent grounds the same day. Decisive one: the data is
  not there. Over 4,866 rows carrying `other_sources`, **85.5% of credited
  sources are an integer with no record at all**, and only 7.8% have full text
  (`SavedCluster` persists no member content or ids). Also: dedup runs *before*
  pre-enrich, so it would run on stubs; and a spaCy OOM inside dedup takes out
  deduplication for the whole cycle.

## UNTESTED — and this is where the value is

- ~~**Cross-lingual NER (`xlm-roberta-large-finetuned-conll03-english`).**~~
  **RUN 2026-08-08 — the extractor was the problem, not the feature.** See the
  CONFIRMED entry below.
- **Wikidata QIDs instead of surface-token NER.** The measured failure was
  Latin-script token collision — ids fix that by construction, and fix the
  cross-language half at the same time ("Verenigde Naties" ↔ "United Nations").
  Raised in the next-phase plan; never tried.
- ~~**MinHash from FluxusSource.**~~ **RESOLVED 2026-08-07 (night): DELETE, and
  the recommendation is now measurement-backed** (ducroq/FluxusSource#134).
  The measurement the issue named as its own honest gap was run: on one
  production collection (4,109 items, post-exact-dedup), MinHash over
  **cross-source pairs only** gives 51 pairs at 0.4, 4 at 0.5, **3 at 0.6** (one
  of those a false positive at 0.688 — two AFCON fixture lists 17 years apart),
  1 at 0.7, 0 at 0.8. That is **~2 true positives per cycle against the ~2 the
  exact matcher already finds**. A full day (25,482 rows) gives 11 pairs at 0.6
  and **zero cross-language**. On real production text, 1,074 candidate
  same-story cross-language pairs land at **0.094–0.297** — below the 0.4
  threshold that already yields mostly junk. **MinHash cannot separate same-story
  from unrelated on this corpus at any threshold.**
  Also confirmed live: `jaccard('','') == 1.0`, and **1,374 of 25,482 rows in a
  real day have empty content** — run unguarded that is ~866,000 spurious
  "identical" cross-source pairs. Deleting drops `scipy`, **114 MB of a 450 MB
  venv**, nothing else needs it.

  **FOUR of my own supporting claims here were wrong; the conclusion never moved.**
  Recording them because the pattern matters more than the outcome:
  - ~~"cross-language same story scores 0.195"~~ — **no script, notebook or data
    file produced it**; it was one hand-written sentence pair, and different
    hand-written sentences give 0.078. **Never quote 0.195 again.** The direction
    replicates on real data; the number is not evidence.
  - ~~"~206 s/cycle, 2619× the current hash cost"~~ — overstated **~11×**;
    measured 4.34 ms/doc → **~19 s/cycle**.
  - ~~"the signal exists downstream and better — strictly weaker"~~ — *inferred*.
    NexusMind `story_dedup.py` is live at `cross_source_threshold=0.88` but embeds
    **title-only**; MinHash is full-content. Not a like-for-like comparison.
  - ~~"it removes the import that caused a 26-hour outage"~~ — **withdrawn**. That
    outage was a renamed venv; `datasketch` merely raised first, and `feedparser`
    would have failed next.
  Independent third datum against wiring it up: lexical Jaccard was already tried
  downstream and **disabled** as ineffective for paraphrased titles
  (`ovr.news/src/lib/data/editor/config.ts:67`). And the delete does **not** serve
  NM#170 / NM#291, which want more signal than a title.
  Stale docs to fix regardless: `NexusMind/docs/ARCHITECTURE.md:56`,
  `NexusMind/docs/downstream-apps/business/pitch-document.md:39` (a business pitch
  claiming a capability that has never executed), and this repo's
  `docs/article-metadata-schema.md:216` (`minhash_signature`, no producer, no
  reader, and unemittable given the uint64 bug).
- **Whether the labelled set is even representative.** See below — this may
  invalidate the denominator for everything above.

## The constraint nobody had stated: the corpus is pre-depleted

FluxusSource drops on `md5(title + content[:500])` **with no source comparison**,
so two outlets carrying the same wire copy collide and the second never enters
the pipeline (ducroq/FluxusSource#133). Those are the *easiest* corroboration
positives, removed at collection.

Consequence for this file: **the next-phase plan's step 3 ("mine the labels we
already hold") draws from a corpus that has already had its easiest positives
deleted.** Any feature measured on that set is measured on a depleted sample,
and the depletion runs against exactly the signal being tested. A cross-source
stamp shipped 2026-08-07 (`4994d61`, FluxusSource) so the size becomes knowable;
the count is a floor for ~30 days while the hash store turns over.

**Refined 2026-08-07 (night) — then the refinement was REFUTED the same night.**
I wrote that the deletion is "arbitrary with respect to publisher", so the corpus
is "depleted, not skewed by source", and therefore a future `source_pair_prior`
is "not silently poisoned". **Do not rely on that.** The arbitrariness claim
rested on evidence that an adversarial review showed to be an instrument artefact
(see the corrected entry under CONFIRMED). What is actually known:

- **Cross-run loss is publisher-correlated, not unbiased.** `seen_hashes` persists
  30 days and is consulted first, so a story is claimed by whichever *run* saw it
  first — set by per-feed `update_frequency`. GN-hosted feeds: **1 sub-12h,
  201@24h, 110@≥48h**. Non-GN: **159 sub-12h**. Cadence is a per-publisher
  property. **So `source_pair_prior` cannot yet be assumed safe from this.**
- **The loss is sticky, not a coin flip.** A content-dropped item never reaches
  the `seen_urls` write, so it is re-dropped every run until the TTL expires —
  **up to 30 days**, deterministically.
- **What survives unchanged, and is the binding constraint for step 3**: whatever
  the mechanism, what is removed is one whole side of an easy positive *pair*.
  Corroboration labels are pair-shaped, so deleting either member destroys the
  pair outright. At n=23 with case_1 supplying 21, that is not a rounding error.

So: the sample-size problem is real and unaffected by the retraction; the
"semantics are safe" reassurance is withdrawn. **Expect "the pairs were never
there" rather than "the pairs are biased" — but do not assume the survivors are
an unbiased draw either.**

**And a finding that may matter more than either:** in the 20:06 run, **6
cross-source syndicated stories SURVIVED dedup against 2 dropped** — different
snippet, different hash — one survivor being the same story as one of the drops
via a third outlet. Exact-hash dedup may simply not be where the corroboration
evidence goes; near-duplicate *survival* is the larger population and nobody has
measured it.

**Status of the measurement (2026-08-07 21:00):** not yet answerable
empirically, and it will not be for weeks. Only **one** collection run has
carried the stamp (20:06), yielding **2** cross-source drops. The timer is
`fluxus-collection.timer`, `OnCalendar=*-*-* 00/4:00:00` — **6 runs/day**,
next at 00:02. The 4 grep hits in `logs/` are those same 2 drops written to both
`aggregator.log` and `scheduled_20260807.log`; **do not read 4 as a count of
events.** The mechanism above was settled by reading the call path instead, which
is why it did not need the wait.

## Sequencing as it stands

From NexusMind's `corroboration-next-phase-plan.md`'s RECOMMENDED ORDER (8 steps). Verified
2026-08-07: **step 1 (Phase 4a, "stop asserting a count precision cannot
support") is already discharged** — the hedge is live in both languages
(`ovr.news/src/i18n/translations.ts:84/369`) and the boost ladder was replaced by
a flat 1.3× capped at 9 (`corroboration-boost.ts:61/69`). So the live front is:

2. settle representation (title vs title+body) — no new labels
3. mine the labels already held — hours of compute ← **NOW THE ONLY BLOCKER**
4. ~~cross-lingual NER swap~~ ← **DONE 2026-08-08, and it passed.** The
   extractor was the problem: median 2 → 12 entities/article, and unrelated-pair
   collisions went from `ej = 1.000` to **0 of 4,000 above 0.3**.

**Corrections after reading the plan properly (2026-08-08, same evening):**

- **Step 2 comes before step 3 and is a hard prerequisite** (via MECH-1). I had
  written that step 3 was "the whole remaining path" — wrong.
- **Step 2 is already half answered.** OBS-17 measured **title+body as the better
  representation, AUROC 0.791 vs 0.771**. What is open is only its **threshold**;
  production runs **title-only at `cross_source_threshold=0.88`**.
- **Step 3's labels are not a cluster store.** It names *SemEval per-pair sims,
  `per_probe.jsonl` <!-- placeholder -->, and cosines on the adjudicated 300* — not `SavedCluster`.
  (The 8 hand-written cases in `measure_matching_geometry.py:111-190`, sourced
  verbatim from NM#170/#188 issue text, are V1's *test* cases and are where n=23
  comes from. Do not confuse the two.)
- **Step 4 sits after step 3 in the plan and I ran it first.** Legitimate — the
  plan itself calls it "direction-finding, valid at n=23 per §P7.1, no new
  labels" — but note the order when citing.

## STEP 2 — representation ANSWERED, threshold was WRONG, turn-over measured 2026-08-09

**READ THIS BEFORE THE SECTION BELOW.** The SemEval table below is correct and
still stands as an *external-gold* result. Its operating point does **not**
transfer to production, and the section as originally written would have shipped
the wrong change.

- **Which variant production embeds: `title_raw`.** `story_dedup._prepare_text`
  returns `f"query: {title}"` — the raw title, no suffix stripping. The
  `_normalize_title()` in `scripts/main.py:152` is for exact duplicate-title
  rejection and never touches the embedding. **The table below quotes
  `title_stripped` for the live row** (P 0.8116 / R 0.4909); the real live row is
  `title_raw` (P 0.8124 / R 0.4864). Immaterial to the ordering, but do not quote
  the stripped row as production.
- **0.96/0.92 is REFUTED on production** (registry OBS-13/28, PROP-6 status
  2026-08-06). It rejects 70% genuinely-same-story pairs at its own margin and
  merges 86% fewer pairs.
- **Turn-over point measured 2026-08-09** on a fresh 680-pair panel (v3, seed
  20260808, `data/research/precision_panel_v3/` in NexusMind, gitignored):

  | config | merged pairs | precision (95% CI) | near-miss discarded | est. true pairs | largest | ≥20 |
  |---|---|---|---|---|---|---|
  | title@0.92/0.88 (LIVE) | 948,399 | 0.173 [0.083,0.326] | 10% | 164,123 | 592 | 95 |
  | title_body@0.92/0.88 | **17,692,176** | 0.004 [0.000,0.138] | 10% | 74,666 | 1051 | 128 |
  | **title_body@0.94/0.90** | 496,299 | 0.344 [0.226,0.485] | 20% | **170,681** | 422 | 52 |
  | title_body@0.96/0.92 | 134,012 | 0.451 [0.349,0.558] | 30% | 60,459 | 129 | 12 |

  **0.94/0.90 is the turn-over point** — the only config passing all three
  pre-registered gates (`docs/investigation/2026-08-08-turnover-prereg.md` in
  NexusMind). **But it is NOT proven more precise than live**: by the #95
  standard (overlapping intervals → not distinguishable) it ties. The live
  baseline itself moved **0.283 (v2) → 0.173 (v3)** at n_eff 36, because 83% of
  pair mass sits in giant clusters sampled only 25 deep. **Deepen the giant
  stratum before this gates a deploy.** `title_body@0.92/0.88` is decisively dead
  (17.7M pairs, giant stratum 0/25).
- **`title_body@0.96/0.92` IS significantly more precise than live** on v3
  (disjoint CIs) — it buys that by going quiet, finding 60k true pairs vs 164k.

### Original SemEval section, retained — external gold, not a production op-point

## STEP 2 IS ANSWERED — title+body @ 0.92 beats title-only @ 0.88 (2026-08-08)

**There is no n=23 problem for representation.** The labels are **SemEval-2022
Task 8**, on b650 at `~/nm-sweep/semeval/final_eval_data.csv` — **4,902 pairs**
(4,597 scored, **2,422 positives**, 1,355 cross-language), human-rated, with
per-dimension GEO/ENT/TIME/NAR/STYLE/TONE columns. Already scored by
`~/nm-sweep/semeval/score_semeval.py` → `semeval_scores.json` <!-- placeholder -->.

| variant | AUROC | AUROC xlang | AUROC samelang | pearson r |
|---|---|---|---|---|
| `title_raw` | 0.7689 | 0.8622 | 0.7411 | 0.491 |
| `title_stripped` | 0.7707 | 0.8657 | 0.7421 | 0.496 |
| **`title_body`** | **0.7912** | **0.8874** | **0.7967** | **0.536** |

**The operating point production should move to:**

| representation | threshold | precision | recall | tp / fp / fn |
|---|---|---|---|---|
| title-only (**live today**) | 0.88 | 0.8116 | **0.4909** | 1189 / 276 / 1233 |
| **title+body** | **0.92** | 0.8105 | **0.6552** | 1587 / 371 / 835 |

**Precision is unchanged (Δ 0.001); recall goes 0.491 → 0.655, +33% relative.**
That is ~400 more true corroborations per 2,422 at no precision cost, and it
needs no new labels and no model — only a representation and threshold change in
NexusMind's `story_dedup.py` (live at `cross_source_threshold=0.88`, title-only).

Cross-language gains more than same-language (0.8657 → 0.8874 vs 0.7421 →
0.7967), which matters for a multilingual corpus.

**Caveats before shipping.** This is SemEval external gold, **not** the
production distribution — production is pre-depleted (see below) and its pair
mix differs, so treat the *ordering* of the two representations as the robust
result and the exact threshold as needing a production check. Confirm also which
variant production actually embeds (`title_raw` vs `title_stripped` differ by
0.002 AUROC — immaterial here, but name it before quoting). #95's 0.16 noise
floor does **not** apply: these are embedding cosines, not student scores.

## WHERE THE CORROBORATION DATA ACTUALLY LIVES (inventoried 2026-08-08)

**It is on `b650-gpu:/home/jeroen/nm-sweep/out/`, NOT on sadalsuud.** I first
concluded "the precision panel does not exist" after checking sadalsuud and
gpu-server — the owner said "it could be on one of the GPUs" and it was.
`data/` is gitignored on sadalsuud (`.gitignore:230`), so nothing about that box
tells you the panel was ever built. **Check b650-gpu before concluding any
corroboration artefact is missing.** Access: `ssh b650-gpu` works from this
workstation as `jeroen`; it does **not** work from sadalsuud (tries `jwasys`,
publickey denied) — `memory/b650-gpu.md` says otherwise and is wrong on that
point.

| artefact | state |
|---|---|
| `precision_panel/` (v1) | 299 pairs, both representation stores |
| `precision_panel_v2/` | **340 pairs**, 6 strata × 50 + 40 near-miss controls, balanced 170/170 across configs |
| `store_title_92_88.npz` | title-only representation, both frames |
| `store_title_body_96_92.npz` | **title+body** representation, both frames |
| `per_probe.jsonl` <!-- placeholder --> | exists in `recall_probe_48/`, `probe_smoke/`, `probe_smoke2/` |
| `recall_disputed.json` <!-- placeholder -->, `recall_grid.json` <!-- placeholder -->, `rg_A_*.npz` | present |

**~~THE BLOCKER: the panel is UNADJUDICATED.~~ WRONG — CORRECTED 2026-08-09.**
The panels **were** adjudicated on 2026-08-06 by the DeepSeek judge
(`scripts/research/judge_pairs.py`) and scored. The verdicts live in the
**NexusMind checkout** at `data/research/precision_panel{,_v2,_v3}/judge_verdicts.jsonl`
— which is gitignored (`.gitignore:230 data/`) **and was never copied to b650**.
The b650 `adjudicate.csv` <!-- placeholder --> is the *human* sheet, which is legitimately empty
because the standing instruction is no hand-labelling.

**This is the `feedback-enumeration-is-not-inventory` failure again**: I
inventoried b650, found no verdicts, and concluded none existed. b650 excludes
them by construction. Establish what a source excludes *before* using its silence
as evidence.

`answer_key.json` <!-- placeholder --> genuinely is the sampling design, not an answer key — that part
was right.

## 2026-08-17 — ⭐⭐ the sub-threshold pairs are BOTH mechanisms, and COMBINING features beats the threshold

**No filter, no model, no deploy, zero spend.** Everything below is measured on this
workstation, sadalsuud (read-only) and b650. Nothing was committed to NexusMind.

### ⭐⭐ The 79.3% splits into two mechanisms that need DIFFERENT fixes

Ran the **deployed** `story_dedup.py` (md5 `d6f1a3cb5ddfe888bad787a35299967f`, fetched
from sadalsuud — ⚠️ **b650's own NexusMind checkout predates the academic gate and is
the WRONG code for this**) over one real batch: 3,399 articles,
`content_items_20260817_120713`, window 10:02→12:02 UTC. For every within-cluster pair
below its applicable bar, asked whether the endpoints are connected by a path of
≥bar edges.

| config | below-bar pairs | CHAINED (same component) | DRIFT (not connected at all) |
|---|---|---|---|
| production (cap 25, gate on) | 854 of 2,151 = 39.7% | **63.8%** | **36.2%** |
| cap off, gate off | 1,090 of 2,494 = 43.7% | 58.0% | 42.0% |

- **Chaining is SHALLOW: 94.75% of chained pairs are exactly 2 hops** (3 hops 5.0%,
  4 hops 0.25%, sample 400 of 545). One bridge article. A fix need not reason about
  long chains.
- **Drift is ~36–42% and the chaining literature does not describe it.** Those pairs
  are unreachable at the bar by any path; membership came from matching a *mean*.
- Controls: above-bar pairs same-component 100% (an edge is its own path); **random
  cross-cluster pairs same-component 0 of 5,000**. The instrument can say both.
- ⛔ **39.7% is NOT a correction to the 79.3% — it is a different population.** Run with
  `cluster_path=None`, so **no cross-run seeds**; production loads 134,858 saved
  clusters and inherits membership across runs. The cross-run seeding path is
  **untested** and is plausibly where the rest of the sub-threshold mass lives.
  Also one batch, one 2-hour window.

⭐ **The bar is where cross-language corroboration dies, and the below-bar pairs are
what currently recover it.** Baseline cross-language share of all article pairs in the
batch: **63.0%**. Above-bar pairs: **38.9% — depleted**. Chained 72.1%, drift 67.3%.
Third independent arrival at the same place as "0.88→0.92 destroys 94% of
cross-language corroboration" and cross-language merge precision 0.685 vs 0.391.
**Consequence: complete-linkage removes BOTH mechanisms, so the known ~39% merge
decline is likely concentrated in cross-language corroboration.** That argues for
**correlation clustering** (minimise disagreement) over a hard clique constraint that
requires every pair to clear a bar systematically unreachable for exactly the pairs
worth keeping.
<!-- verify: manual — /tmp scripts are ephemeral; re-derive by running the deployed
     story_dedup over a fresh raw batch with cluster_path=None and comparing
     within-cluster pairs against connected components of the thresholded graph -->

### ⛔ MY FRAMING WAS WRONG: under-merge was NOT "measured nowhere"

*(Corrected 2026-08-17 evening by ovr's pre-commit review, after I asserted it repeatedly
all day — in this file, to three peer sessions, and to the owner.)*

**`INST-4` (`recall_probe.py`, 2026-08-05) is a recall instrument** and has been in the
registry since before this session started: pairwise recall over **2,471 labelled pairs**,
decomposed by failure cause, certified, and explicitly scoped as *recall-only*. I read
that row this morning and then spent the day saying the direction had never been measured.

**What was actually missing was a POPULATION, not a direction** — nobody had measured
under-merge on the *standing reader-facing feed*. The pitch's §6a says *"every measurement
**in this pitch** scores precision"*, which is true and scoped; I generalised it from the
pitch to the whole registry without checking the registry I had open.

⭐ **Same shape as the ART-11 error, hours apart: the source was in front of me and I
asserted from the summary.**

### ⚠️ ovr's under-merge figure moved FOUR times in one day — never quote it bare

| revision | stories | redundant cards | rate | why it moved |
|---|---|---|---|---|
| first pass | 51 | 99 | 3.77% | — |
| iranintl retraction | 50 | 96 | 3.66% | 4 cards were an ovr summarizer defect, not under-merge |
| original-title re-audit | 48 | 93 | 3.54% | components had been built on English rewrites |
| **reachability correction** | **40** | **82** | **3.94%** | **denominator was wrong** |

⛔ **The denominator was the real error.** The feed was reconstructed through the summary
gate only; both `[lang]/index.astro` and `[lang]/[tab].astro` additionally apply
`MAX_PER_SOURCE = 5` and `.slice(0, 1000)`. **Only 2,082 of the 2,624 cards are reachable
— 542 render on no page a reader can navigate to.** The caps de-fragment 8 small stories
and cost 11 cards; **every large story survives whole** (Venezuela 11, Sicily 9, Lebanon 8,
EU packaging 7), so the correction *strengthens* the finding. **3.54% and 3.94% are the
same 93 cards over different denominators.** Use **3.94%** for anything reader-facing, and
never state either without its denominator. Also English surface only — the `nl` branch
needs a Dutch summary with no English fallback, so it has ~2 displayable ids.

⚠️ **And "clears NexusMind's own bar" overclaims.** ovr's arm models a *pairwise* cosine
threshold; production compares an article to a **pinned seed centroid**, greedily, with a
**source-aware per-cluster** threshold (strict when the article's source is already in the
candidate *cluster*, and when either source id is empty — **not** when the two articles
share a source), plus the 25-member cap, the `max_articles_cpu: 1000` CPU bypass, and the
academic gate. So "131 pairs NM's rule says should have merged" is really **"131 pairs the
embedding space could see"**. The 32.3%-clear figure stands as a statement about the
*space*, which is what the text-shape conclusion actually rests on.

⭐ **Their reviewer turned the Lebanon case against them, correctly, and it favours
H-MERGE:** under a pairwise thresholder, 8 cards in 8 clusters with all 28 pairs above the
bar is **impossible**; under greedy centroid assignment it is an **ordinary** outcome. So
that case is not independent evidence alongside NexusMind's trace — it is evidence *for*
it.

⛔ **The ~5% ceiling is withdrawn.** Two of its three probes were hand samples never
implemented in either script, so they are not reproducible; the third is underpowered by
its own arithmetic — at the ~2.3% density credited to that band, 40 draws expect 0.9 hits
and **P(0) ≈ 0.40**, so finding none is routine rather than informative, and the sampling
was systematic by card position rather than random. **A hand census of one day's feed
(~250 cards) is the only thing that would bound it.**

### ⭐ COMBINING features beats the production threshold — n=1,196, replicated 3 panels

V1 combined four features and got precision 0.000 / recall 0.000, but at **n=23** with
an extractor giving 2 entities/article. Both constraints are gone. Re-asked with
7 cheap pairwise features (cosine, `−log1p Δt`, cross-language, not-same-source,
numeric Jaccard, token Jaccard, length ratio) in an L2 logistic regression, grouped
5-fold CV with folds split on connected components over article ids:

| panel | n | `sim` only (production) | combined |
|---|---|---|---|
| precision_panel | 297 | 0.7277 | 0.8681 |
| precision_panel_v2 | 300 | 0.7205 | 0.8521 |
| precision_panel_v3 | 599 | 0.8037 | 0.9162 |
| **pooled** | **1,196** | **0.7701** | **0.8827** |

Null arm: 50 label permutations through the same folds and fit → mean 0.4846,
max 0.5271. Clears decisively. Precision at matched recall (pooled, base rate 0.465):
keep 75% of true merges → 0.685 (`sim`) vs **0.848** (combined).

⭐ **The sign flip only visible in combination:** token overlap has single-feature AUC
0.642 but coefficient **−0.675** in the joint fit. Given the cosine, extra literal
token overlap is evidence *against* a true merge — the templated-title collisions
(`"Green forest fire notification in Angola"` ×214). **A per-feature AUC table cannot
show this**, and the 2026-08-09 probe was exactly such a table.

⚠️ Binding caveats: negative class is **false merges**, so this filters bad merges and
is NOT shown to find new ones; panels are **stratified toward giant clusters**, so the
precision-at-recall rows are design-weighted and AUC is the portable half; labels are
LLM judge verdicts. ⛔ **Built and reported by the same session — needs a non-author
check before it drives anything.**

### Records are NOT the CDCR blocker — the input FMEA nobody had run

⭐ **`_run_shared_dedup` (scripts/main.py:3315) runs BEFORE `_run_shared_pre_enrich`
(:3377), and `_prepare_text` is TITLE-ONLY (NM#275). So enrichment quality cannot
affect matching at all, by construction.** Over 96 files / 324,941 rows / 17 days
(2026-07-31→08-17): titles missing **0**; `published_date` missing or unparseable
**0**; title mojibake **~0.11–0.13%** *(⛔ 0.094% too low, 0.159% too high — both retracted, see below)*; title
markup **0.498%**; non-NFC titles 0.095%
(ko 1.94%, fr 1.39%, ar 1.22%). Contamination is source-concentrated —
`mexican_excelsior` **648/648** and `portuguese_cmjornal` **253/253** carry a raw
`<![CDATA[` wrapper *inside the title*, which goes into the embedding verbatim.
**The one real record hazard is duplicate-title mass: 22.97% of rows carry a title
seen more than once; 22,382 rows across 9,144 titles are cross-source duplicates.**

NM#338 (enricher mojibake) is **fixed and verified on production rows, not on issue
state**: post-enrichment body mojibake 1.686% → 0.593%, step on 2026-08-14
(1.137% → 0.081%), 0.023% on 08-17. 516 files, 1,356,767 rows.

### Traps found — each would have produced a confident wrong number

- ⛔ **`sim` in `precision_panel_v3/answer_key.json` exists on only 80 of 680 rows, and
  those 80 are exactly the `near_miss_control` rows the analysis discards.** v1/v2 keys
  have no `sim` at all. A cosine baseline read off the key is computed on thrown-away
  rows. Recomputed for all 1,319 with the production model and `_prepare_text`.
- ⛔ **The adjudicated verdicts are on NEITHER GPU box.** Not sadalsuud, not b650 —
  they are in the **workstation** NexusMind checkout at
  `data/research/precision_panel{,_v2,_v3}/judge_verdicts.jsonl` (1,409 rows, 1,316
  with S/D). This file previously said "the NexusMind checkout", which is ambiguous
  across three machines.
- ⛔ **Panel `item_id`s COLLIDE across panels** — all three start at `P0001`. A flat key
  silently overwrites v1 with v3.
- ⛔⛔ **NEVER HAND-WRITE A MOJIBAKE CHARACTER CLASS. GENERATE IT.** FS#124 is
  UTF-8-as-MacRoman (`años`→`a√±os`); NM#338 is UTF-8-as-cp1252 (`aÃ±os`). My first pass
  wrote only cp1252 and read 0.019%; my second added hand-written MacRoman classes and
  read 0.094%. **Both were undercounts, and the second one by 65.1% of its own count.**
  A hand-maintained class cannot enumerate what a codec does — mine was missing `ã`, so
  rows whose only artefact was a mis-decoded zero-width space were invisible.
  **The fix is derivation, not a longer class:** for every character in a realistic
  inventory and every legacy codec, compute `ch.encode("utf-8").decode(codec)` and match
  on the resulting strings. 2,914 signatures from 5 codecs, nothing guessed.
  → `NexusMind/scripts/research/nm188_mojibake_derived.py`.
  ⭐ **It also carries the control the hand-written versions never had, and the control
  is free:** every mojibake signature is non-ASCII by construction, so the detector must
  return **exactly 0 on the pure-ASCII subset** — 0 of 193,983 titles, 59.7% of the
  corpus. A structural control you get for nothing beats a sampled one you have to build.
  ⚠️ It also avoids the round-trip detector's known false-positive bias (FluxusSource
  measured it firing on clean apostrophe-bearing Romance titles); both of their examples
  are asserted as absence controls and both pass.

- ⛔⛔ **RETRACTED WITHIN THE HOUR — the "Cyrillic and Greek dominate" reversal was 140
  FALSE POSITIVES.** *(Claimed and pushed in `c5ad67b`; refuted by the NexusMind session
  the same evening, verified here independently before accepting.)*

  ~~Mojibake is not a Spanish/Portuguese problem; the missed rows are ru 62 · el 42 ·
  en 33 · mk 22 · es 21 · uk 13, so Cyrillic and Greek dominate.~~

  **The mechanism, traced to the generation step.** The inventory includes Latin
  Extended-B (U+0180–U+024F) and the punctuation `«»`. Those characters' UTF-8 bytes,
  read through `cp1251` / `mac_cyrillic` / `mac_roman`, produce **two-character
  signatures that are ordinary text in Cyrillic and Greek** — `«Б` from U+01C1 via
  mac_cyrillic, `«π` from U+01F9 via mac_roman, `ИЈ` from U+0223 via cp1251. **Guillemets
  are the standard quotation mark in Russian and Greek**, so every quoted headline in
  those languages matched. Verified by codec inversion: all of them invert under **no**
  codec, i.e. they are clean text. Cross-tabulated by NexusMind: es 201/201 and en 145/146
  confirm as real; ru, el, mk, uk, de confirm at **0 of 140**.

  ⭐⭐ **WHY THE CONTROLS COULD NOT CATCH IT, and this is the keeper.** The structural
  control — *"every signature is non-ASCII, so the detector must return 0 on the
  pure-ASCII subset"* — is true, free, and **one-sided in exactly the direction that
  matters. It proves the detector does not fire on the 59.6% of the corpus where it
  structurally CANNOT. All 140 false positives live in the non-ASCII 40.4%, which the
  control never examines. It is a control that can only pass.** The absence arm had the
  same shape: 8 clean strings, every one Latin. **An absence control drawn from the
  scripts the instrument was DESIGNED for cannot test the scripts it is RUN against.**

  ⭐ **And the fix inverted the error rather than escaping it.** I wrote *"an instrument
  that can only see one script will report that the problem is in that script"* — then
  shipped an instrument that fires on scripts it was not designed for and reports the
  problem is in *those*. Same error class, opposite sign, one commit apart.

  **THE SOUND FORM IS SCREEN-THEN-VERIFY** — the generated signature set as a complete
  but unsound screen, then codec inversion as the exact check on survivors. That is the
  block-then-verify pattern from the record-linkage literature surfaced this same day
  (Papadakis et al., ACM CSUR 53(2) 2020; canopy clustering, McCallum et al. KDD 2000),
  and neither half is correct alone: signatures are complete and unsound, inversion is
  sound but has no cheap candidate set.

  **The defensible number: ~0.11–0.13% of titles, and both figures are FLOORS** — screen
  +verify gives **0.110%** (362 of 328,460), NexusMind's inversion-only gives **0.129%**
  (418 rows). Neither sees double-encoded or lossy corruption. **0.094% was too low,
  0.159% was too high.** Population is Latin-script, **Spanish and English dominant** —
  roughly where the morning started, though the old detector *was* genuinely undercounting
  by ~18%. The recall fix was right; only the population claim was wrong.

  Genuine finds the hand-written classes missed and that survive verification: `MƒÅori`
  (Māori macron in NZ English) and `â€”` / `‚Äî` em-dashes in English headlines.
- ⚠️ The panel's `lang_1`/`lang_2` column **mixes ISO codes with English names**
  (`en` and `English` both appear), so a naive `lang_1 != lang_2` inflates
  cross-language. Cost: 0.672 → **0.685** after normalising.
- ⚠️ **The panel cannot answer the non-Latin question**: 57 of 1,316 pairs (4.3%) are
  anything other than both-Latin (Hangul 16, mixed-script 17, Greek 14, Han 4,
  Cyrillic 3, Hebrew 3).
- ⛔ **`SavedCluster` persists no member ids**, so production data cannot answer "which
  languages ended up in one cluster" at all. Every multilingual number we hold is from
  SemEval external gold or a b650 replay; **none from production.** Persisting member
  ids is one field and unblocks the multilingual cut, the complete-linkage shadow, and
  merge-evidence retention at once.

### Literature — six lenses, 2026-08-17

⭐⭐ **Our clusterer IS single-linkage at the bar, mathematically.** Zadeh,
*Similarity Relations and Fuzzy Orderings*, Information Sciences 3(2):177–200, 1971
(reflexive+symmetric without max-min transitivity is a *proximity* relation);
Tamura, Higuchi & Tanaka, IEEE Trans. SMC-1:61–66, 1971; IEEE Trans. SMC 2010 (Xplore
5409141) proves **α-cut of the max-min transitive closure = connected components of the
α-thresholded graph**. Plainly: Jain & Dubes 1988, Everitt et al. 2011 ch.4.
**Hartigan (1981, JASA)** proved single-linkage is inconsistent in d≥2 *via continuum
percolation* — the formal mechanism, not an analogy. Our threshold graph is a random
geometric (Gilbert) graph; Penrose, *Random Geometric Graphs*, Oxford 2003.
⚠️ **But the 36–42% drift share means our clusterer is LOOSER than single-linkage**, so
these citations cover only part of it.

⭐ **Everyone replaces the threshold with a learned pairwise decision.** Held, Iter &
Jurafsky, EMNLP 2021 — our exact architecture (bi-encoder + FAISS prune + classifier);
**oracle bound: 5 neighbours retrieved + perfect classifier → F1 98.1. Retrieval is not
the bottleneck, the classifier is.** Miranda et al., EMNLP 2018 — grid-searched τ →
learned merge classifier, **F1 82.8 → 94.1**. Saravanakumar et al., EACL 2021 — weighted
linear combination of per-representation similarities, SVM-learned, plus a separate
join-or-found network. CD²CR (Ravenscroft et al., EACL 2021) — a raw BERT-cosine
threshold scores **B³ F1 = 0.00** at MUC recall 0.94.

⛔ **`sigma_hours: 72.0` has a published provenance and it does not transfer.**
Miranda et al. tune their temporal Gaussian to **σ=72h** — but inside a 12-feature
SVM-Rank, not as a ±0.04 additive nudge on a single cosine. Our own sweep refutes 72
(99.1/20.6) and prefers σ=18 (83.6/85.9). **A constant tuned inside one similarity
function does not transfer to another.** Who put 72.0 in `config/app.yaml` is unchecked.

- **Hubness is the attractor's real name.** Radovanović, Nanopoulos & Ivanović, JMLR 11
  (2010) — k-occurrence skew; points near the corpus centroid become everyone's
  neighbour. Fix with **ratio margin**: Artetxe & Schwenk, ACL 2019 (arXiv:1811.01136),
  `margin(cos(x,y), Σ_{NN_k(x)}cos/2k + Σ_{NN_k(y)}cos/2k)`, k=4 bidirectional, ratio
  variant best. BUCC train EN-DE **82.8 → 94.8**, EN-FR 80.9 → 91.9. Also CSLS
  (Conneau et al., ICLR 2018), Mutual Proximity (Schnitzer et al., JMLR 2012),
  All-but-the-Top (Mu & Viswanath, ICLR 2018), Nielsen & Hansen NLDL 2024
  (arXiv:2311.18364, hubness −75% on an SBERT model).
  ⚠️ **Steck, Ekanadham & Kallus, WWW 2024 (arXiv:2403.05440)** — cosine of embeddings
  can be arbitrary and non-unique under regularisation. The citation for why 0.88 was
  never a portable constant.
- **Correlation clustering is the right formulation** (Bansal, Blum & Chawla, Machine
  Learning 56, 2004); **PIVOT** (Ailon, Charikar & Newman, JACM 55(5) 2008) is
  near-linear, one-pass, expected 3-approximation. Complete-linkage is its
  hard-constraint special case. **Leiden** beats Louvain on speed and a real
  correctness bug. Record linkage has the vocabulary: Fellegi & Sunter (1969) m/u
  decomposition, Splink, blocking survey Papadakis et al. ACM CSUR 53(2) 2020,
  canopy clustering McCallum/Nigam/Ungar KDD 2000.
- ⛔ **The ECB+ lemma baseline invalidates most CDCR headline numbers.** Bugert, Reimers
  & Gurevych, Computational Linguistics 47(3) 2021: lemma-δ scores **74.4** CoNLL F1
  against their full system's **74.8** — "performs on par". Their masking ablations:
  action/trigger dominates (ECB+ −13.57, GVC −19.12); **location is ~0 everywhere**;
  publication date is worth −6.64 on GVC and **exactly +0.00 on FCC-T**.
- **Entity grounding buys less than hoped.** GateNLP-UShef at SemEval-2022 measured
  entity enrichment on a trained LaBSE model at **+0.00075 Pearson**. Entity-only
  Pearson: ORG 0.455, DATE 0.435, QTY 0.358, GEO 0.267. **Our numeric-overlap
  0.503–0.581 is consistent with the literature — we did not measure it wrong.**
  ⚠️ But there are **three** numeral-normalisation failure modes (digit script,
  decimal separator, CJK numeral words) and our feature normalises none; `uroman`
  handles the first for free.
- **Tooling gap for our 35+ languages:** ReFinED, BLINK, SpEL are English-only;
  DBpedia Spotlight ships no zh/ja/ko/ar/el/he model; mGENRE (105 languages,
  Mewsli-9 macro 92.3%) is the only realistic candidate and has no published
  throughput.
- ⛔ **Applied category theory for data works one level ABOVE this problem.** Spivak's
  functorial data migration (Information and Computation 217, 2012), CQL, Patterson's
  Algebraic Property Graphs (Uber's Dragon) are all **schema**-level; a direct search
  for categorical entity resolution / functorial record linkage found **nothing**.
  Documented absence, not a search failure. What tolerance theory *does* give:
  correct structure recovery is **maximal cliques ("blocks"), which OVERLAP and do not
  partition** (Zeeman 1962; Information Sciences 195, 2012) — the same shape as
  ADR-015. And one implementable alternative from rough sets: **Słowiński &
  Vanderpooten, IEEE TKDE 12(2):331–336, 2000** generalises to a reflexive-only
  relation, giving a **core/penumbra** pair instead of one hard class.
- ⚠️ **Provenance semirings** (Green, Karvounarakis & Tannen, PODS 2007) are the right
  algebraic shape for "merges compose only when their justifications compose", and are
  implemented (Orchestra) — but **no paper connects them to record linkage.** Extending
  them would be synthesis, not adoption. ⛔ Correspondingly: an exhaustive search found
  **no system outside proof assistants that stores an identity witness and uses it
  downstream**, so "keep the witness" is our design decision, with no precedent.

### Untested, in priority order

1. **Cross-run seeded clustering** — the population the 79.3% actually came from, and
   the one my chain test excludes.
2. **Ratio-margin `sim`** recomputed over a production neighbour pool, dropped into the
   same 1,196-pair harness. Tests the strongest published fix on our own labels.
3. **XLM-R entity Jaccard on the 1,316 adjudicated pairs**, scored against the judge
   verdicts — entities from an independent extractor, labels from the judge, so not
   circular. The 2026-08-08 rerun measured only the negative side and **no entity
   feature appears in either `b650:~/nm-sweep/feature_probe.py` or `feature_probe2.py`**
   (grepped: only `numeric_jaccard`). ⚠️ **No NER script persists anywhere** — the
   XLM-R run was executed from a `/tmp` file that is gone.
4. **Numeral normalisation** before re-measuring numeric overlap.

## 2026-08-16/17 — ⭐⭐ THE HEADLINE IS NOT THE GATE: **production is 79.3% sub-threshold artefact**

**The academic gate was BUILT, accepted and enabled — and the finding that matters is the
baseline it exposed.** Measured by the NexusMind session on a real 3,835-article batch,
merge-pairs by pairwise cosine against the 0.88 bar:

| population | n | below 0.88 | mean cos |
|---|---|---|---|
| OLD merge-pairs (gate off) | 122,901 | **97,492 = 79.3%** | 0.8672 |
| NEW merge-pairs (gate on) | 4,075 | 1,429 = **35.1%** | 0.8898 |
| newly KEPT (the 302) | 302 | 299 = 99.0% | 0.8186 |
| newly REFUSED | 119,128 | 96,362 = 80.9% | 0.8664 |

⛔ **FOUR FIFTHS OF WHAT PRODUCTION CALLS A MERGE IS NOT A MERGE DECISION.** All 30 sampled
newly-kept pairs sit **below** the bar (0.772–0.873): an article matches a cluster's
**centroid** ≥0.88 and inherits co-membership with items it is nowhere near. Attractors are
visible at n=30 — one WWII-motorcycle article in **6 of 30** pairs, an mpox preprint in 4.
That is how a German heatwave story merges with a motorcycle pulled from a Hungarian river.
**This is NM#188/#228/#278 and it dwarfs the academic question.** The gate improves it
79.3% → 35.1% *as a side effect*; it is not the fix.

⭐ **`largest_cluster` 456 → 43 is now CORROBORATED from a second independent direction**
(the sub-threshold rate), so my earlier "observed and deliberately not banked" is upgraded:
still not part of the gate's justification — the gate does not need it and mixing them
muddies both — but it is evidence in its own right and belongs on NM#188.

**The gate as shipped:** both-sides semantics (refuse only when *both* articles carry
`metadata.primary_literature.detected`), reads the stamp and never re-derives,
`pipeline.story_dedup.academic_gate.enabled`, ADR-022 stamp-always, in `_cluster_articles`'s
join scan. Suite **1403 green**, **five** mutations each caught by a named test (delete ·
**OR instead of BOTH** · re-derive from slug · enforce-while-disabled · re-introduce the
cascade). Value: **`pl_pl` 0 correct of 28** (⚠️ rule-of-three upper bound ~**10.7%** — never
quote 0.0% bare); `pl_news` 23.1% of 26; `news_news` 49.5% of 545. Cost **322:1** — 299
sub-threshold pairs added against 96,362 removed.
⚠️ **One batch, deliberately the DENSEST available (29.4% PL vs ~10% typical).** Benefit and
cost both scale down; a typical batch is unmeasured.

### The three method findings, all worth more than the gate

⛔ **1. My acceptance criterion was UNACHIEVABLE and I nearly blocked a good gate on it
forever.** I demanded `pairs newly kept == 0` as non-negotiable. **Refusing any join in a
greedy centroid clusterer reshuffles everything downstream, so zero is unreachable for any
gate.** ⭐ **The three-arm control is the reusable pattern — and the third arm is the one most
would skip:** off-vs-off = **0** (the instrument *can* return zero, so this is not
determinism) · off-vs-gate = **302** · off-vs-**RANDOM refusals at matched prevalence** =
**37,692 from FEWER refusals (392 vs 904)**. That converts "fails, cause unknown" into "the
criterion is unreachable and this gate is **125× better than a generic intervention of the
same size**". **A null arm that shares the MECHANISM but not the HYPOTHESIS.**
⭐⭐ **The rule, and it is the mirror of one this project already enforces:** we say *before
believing a negative, prove the instrument could have said yes.* **The inverse was never
written: before DEMANDING a zero, prove a zero is ACHIEVABLE.**

⚠️ **2. ADR-022's stamp-always shadow pattern has a limit, and here is its testable form.**
`academic_gate_candidates` read **885 disabled / 22,335 enabled — 25×** — because a refused
article kept scanning and met more academic clusters, so the shadow counter was *endogenous
to the decision it was meant to forecast*. Barring the cascade took it to **885 / 904**.
⭐ **Sharpened by NexusMind, and their form supersedes mine:** the pattern is sound
**provided the mechanism terminates its own scan**. Mine ("does not perturb its own inputs")
was a vibe; theirs is mechanistic and testable.

⛔ **3. A gate that refuses a merge must not CAUSE a different merge.** The first build used
`continue`, so a refused article cascaded into a different cluster and invented merges — 247
news↔news, plus refusals spilling into cells both-sides semantics cannot touch (5,997
`pl_news`, 486 `news_news`). Fixed with `break`: a refused article founds its own cluster.
**The refusal count alone looked excellent and would have shipped.** ⚠️ A locked-founder
variant was tested and **reverted** (302 → 288, nothing) — recorded so nobody re-proposes it.

⚠️ **Predictions, both refuted, both on record beforehand.** Mine: *the 302 contain a real
fraction of genuinely GOOD merges* (bridge/attractor removal letting related news find each
other) — **0 of 30**. NexusMind's: *garbage is the minority, ~1/3* — **28 of 30**. The
mechanism neither of us named is the sub-threshold one above. ⭐ And NexusMind **corrected
their own framing against their own number**: "7.4% of surviving merges are invented" was
true, badly framed, and handed to me as the number to argue about — then they measured the
denominator instead of assuming the 302 were a new class of defect. **A ratio only exists
once someone measures the baseline, and nobody had.**

⚠️ **Fifth structural zero of the week, caught not accepted:** the first acceptance run
returned `newly refused 0 / newly kept 0` on a 2,101-article batch that was **0.43% primary
literature** with `academic_gate_candidates == 0` — a *clean-looking pass*, which is worse
than a suspicious blank. An **ABORT on `candidates == 0`** now exists.

## 2026-08-16 — the academic stamp ARRIVES and is UNREAD; the gate's value is UNMEASURED

**Census run by the NexusMind session on sadalsuud** (⚠️ *not* locally — their
`data/raw` ends 07-26 and the stamp shipped **08-09**, so a local run reads 0% and
**the zero is the window, not transport**). Distinct ids, `collected_date >= 08-10`:

| boundary | distinct ids | stamp ABSENT | `detected: true` |
|---|---|---|---|
| `data/raw` | 132,474 | **0 (0.000%)** | 13,379 = **10.10%** |
| `data/filtered` | 114,080 | **0 (0.000%)** | 12,992 = **11.39%** |

Ramp is the right shape: 0.00% daily 07-31→08-08, **55.94%** on 08-09 (ship day,
partial), **100.00%** from 08-10. ⚠️ **Report per-day, never blended** — a window
straddling the ship date understates by construction (blended reads 43.95% and
means nothing). 10.10% vs FluxusSource's 8.94% is *higher*, so nothing is lost;
raw→filtered 10.10→11.39 is survivorship. **Stage trap survived as predicted:**
`arxiv_announce` 9,584 raw → 9,545 filtered, passing through as a *stamp* even
though the prefix re-derives to 0.000 post-enrichment. Verify the field, never
re-derive the evidence.

⛔ **CONSUMERS: ZERO, at three hops.** `grep primary_literature` over NexusMind
`.py`/`.yaml`/`.json` = 0; over ovr.news `.ts`/`.astro`/`.sql` = 0.

⛔ **"Within PL, merge only on byte-identical title" is REFUTED — it is not a
discriminator, it is an OFF-SWITCH.** It would refuse **4,470 of 4,630 PL
merge-links (96.5%)**, keeping 160. ⭐ **The control is the finding: news sits at
3.22% identical-title against PL's 3.46%** — statistically the same, so identical
title is neither an academic marker nor a property of genuine merges (96.8% of news
merges, largely legitimate corroboration, have non-identical titles). The 6/6 came
from a panel of *genuine academic same-story pairs*, a 3.46% slice at production
scale. **The three-line rule and the exclusion are the SAME INTERVENTION** — evaluate
it as the exclusion; it keeps its 160 good links by coincidence of rarity, not by
discriminating.

⚠️⚠️ **THE 20.6–30.4% AND THE 0.344 → 0.459 ARE BOTH UNUSABLE AS THE GATE'S VALUE.**
NexusMind measures PL at **8.05% of everything merged** (4.82% by links) against the
panel's 20.6–30.4%.

⛔ **My "the label is `type_classification`-derived and contaminated by news"
hypothesis is REFUTED** (stated at ~75%, and the label is **narrower and purer** than
`primary_literature`, not broader). The label is `b650:~/nm-sweep/feature_probe2.py` line 90 —
`any(t in _s for t in ("arxiv","pubmed","biorxiv","medrxiv","clinicaltrials","ssrn"))`
over `source_1 + " " + source_2`, a **6-term slug substring match OR'd across both
sides of the pair**. Smithsonian/ScienceAlert/STAT cannot enter it. Measured leak the
other way: **5 of 508 panel-"news" pairs (1.0%)**. ⚠️ **The panel itself carries NO
academic label** — `NexusMind/scripts/research/judge_pairs.py` / `NexusMind/scripts/research/build_precision_panel.py` have zero "academic"
references and `NexusMind/data/research/precision_panel_v3/answer_key.json` strata are cluster-**size** only; the cut is applied
downstream in the probe. ⚠️ **And the `feature_probe` script this file cited as its
reproduction does not contain the cut at all** — it is the `feature_probe2` variant with the `all|news|acad` argv switch.

⭐⭐ **THE 3× IS STRATIFICATION, AND IT IS THE KEEPER OF THE ARC.** The panel draws
~100 pairs from *every* cluster-size stratum regardless of production frequency;
**54% of academic pairs sit in `giant`**; production is overwhelmingly small
clusters. **Three numbers, all correct for their own population: 15.2% panel
unweighted · 20.6–30.4% stratum-weighted · 8.05% production.** ⭐ The probe's own
header says *"the panel is stratified toward giant clusters"* — **the warning was
present, correct, adjacent, and never applied to this number.** General form, now in
the auto-memory as `feedback-sample-carries-its-design-weighting`: **a sample built
CORRECTLY for one question carries its design weighting into every number derived for
another, and because nothing is wrong with the sample there is nothing for review to
find.**

⛔ **Reweighting does NOT rescue it, because the two populations CROSS rather than
nest** (NexusMind's route, better than mine): the slug label **misses** PLOS / MDPI /
Frontiers / Nature / OpenAlex — `science_plos_one` is a **top-8 detected source in
production** and "plos" is not in the term list — and **adds** pairs where only *one*
side is academic, which is plausibly where false merges concentrate and which a
per-article gate treats differently. **So `0.344 → 0.459` and "0–14% correct"
describe a 6-slug population while the gate would read a DOI/API-derived one. Neither
number may travel as the gate's value.**

⛔ **DO NOT BUILD THE GATE.** Blast radius is measured; **value is not measured
against the field it would use.** No labelled academic pair exists in the stamped
window (panels are 08-05/06/08, stamp shipped 08-09), so closing this needs a
re-adjudication on stamped rows.

## 2026-08-09 — the biggest lever is a GATE, not a similarity feature

**Primary scientific documents are 20.6–30.4% of everything the system merges and
are 0–14% correct at every threshold.** Excluding them beats any threshold move:
weighted precision 0.344 → **0.459** at `title_body@0.94/0.90`, 0.173 → 0.216 at
live. Reason is structural, not tuning: a paper is a *primary document*, not a
report of an event, so two outlets never independently "corroborate" it. True
corroboration rate is near zero by construction.

- **All 6 academic pairs judged genuinely same-story were byte-identical titles**
  — the same arXiv paper via two of our own overlapping feeds. Duplication, not
  corroboration. **0 of the 85 false academic merges had identical titles.**
- **Root cause is upstream: ducroq/FluxusSource#143.** Category feeds prefix the
  body with `arXiv:NNNN.NNNNNvN Announce Type:`, which shifts `content[:500]`, so
  FluxusSource's `md5(title+content[:500])` never collides. **600 duplicate papers
  per 48 cycles** (all same paper id AND same version — checked against arXiv's
  `replace` semantics).

  **~~Dropping the plain `arxiv` feed removes 100% of the class for 77 papers/8
  days; 0 titles appear in ≥2 category feeds.~~ BOTH HALVES REFUTED 2026-08-09**,
  by the FluxusSource session, while executing the drop the owner had authorised.
  The feed **was** dropped (`754a4fe`, deployed, gated by config rather than
  deleted) and the drop **is** justified — but not for either reason stated here,
  and this entry was the source the owner decided on. Recorded because the failure
  is the point: *I relayed a prior session's measurement as fact without
  re-deriving it, inside a question that drove an owner decision.*

  | claim | status |
  |---|---|
  | "0 titles appear in ≥2 category feeds" | **FALSE.** The category feeds duplicate *each other* **738 times in 7 days** — `cs_lg`×`cs` 452, `cs`×`math` 64, `cs`×`physics` 41, `cs_ai`×`cs` 43 — by the identical mechanism (`Announce Type: new` vs `cross` shifts the same 500-char window) |
  | "removes 100% of the class" | **FALSE.** It removed **one contributor**, not the cause. The 738 remain |
  | "nothing survives the drop" | **FALSE.** **123 titles were unique to the dropped feed**, and non-randomly so — the archives no other feed subscribes to (`cond-mat` 34, `astro-ph` 15, `quant-ph` 8, `stat` 8, `econ` 3, `q-bio` 3, `q-fin` 1). 7 substitute archive feeds added (`50b9150`) |
  | the drop is justified | **TRUE, on other evidence** — 592 of the plain feed's 715 distinct titles (82.8%) were already in a category feed |

  **Consequence for this file, and it is not cosmetic:** if arXiv duplicate pairs
  are being counted as corroboration noise, **738 pairs/7 days is still there and
  is larger than what the drop removed.** Do not treat FS#143 as having closed the
  arXiv contribution to the primary-literature merge problem — it did not.

  Separate mechanism found in the same pass, worth knowing before reading any
  arXiv volume figure: arXiv RSS is a **daily REPLACED batch**, so at
  `update_frequency` 24h with ±25% jitter two polls can land 30h apart and skip a
  whole batch entirely. That is why 40 of the 123 "unique" titles were `cs`, an
  archive already subscribed. All 14 arXiv feeds moved to 12h.

  *Attribution: measured by the FluxusSource session, not re-derived here. Their
  own caveat carries: measured on the post-FS#142 hot window, which inherits the
  dedup-store-reset contamination.*
- **Do NOT implement the exclusion on `type_classification`** —
  ducroq/FluxusSource#144. 308 Google News feeds collide on domain `google.com`;
  86% of `academic` rows are Global South news. And the root defect needs no
  collision: `smithsonianmag.com`/`sciencealert.com`/`statnews.com` have ONE
  category each and are `academic` because they *write about* science. MDPI and
  Frontiers are right **for the same wrong reason**.
- **Use article-derived features instead — ducroq/NexusMind#305.** Union of
  academic-API metadata (`source_api`/`authors`/`paper_type`), `[Clinical Trial]`
  title prefix, and DOI presence: **1.000 recall on arXiv/PubMed/trials, 0.000 on
  Guardian/Ars/Smithsonian/STAT/ScienceAlert.** Its apparent 1.8% FP is mostly
  CrossRef/OpenAlex/Semantic Scholar/Nature — primary literature the source list
  missed. Gap: MDPI/Frontiers RSS at 0.241. Never `required` initially (NM#300).

  **~~Contract A is `additionalProperties: false` → stamping at collection
  REQUIRES a schema change.~~ REFUTED 2026-08-09.** `metadata` is **open**
  (`additionalProperties: true`) in *both* contracts, so the stamp needed no
  amendment at all; #305 assumed a **top-level** field and I repeated that to the
  owner as the reason to prefer post-enrichment. It was declared in both schemas
  anyway so NexusMind's `stamp_census.py` can see it. **SHIPPED AT COLLECTION** — FluxusSource
  `33c7f41`, `metadata.primary_literature`, stamp-only with no consumer; replayed
  over 167,234 rows at **8.94% detected, 0 faults**. Evidence classes:
  `arxiv_announce` 10,049 / `doi_url` 2,516 / `academic_api` 1,799 / `doi_field`
  857 / `clinical_trial_prefix` 584 / `doi_text` 454 (weak, never decisive).

  **Two of #305's own features were wrong as written**, both corrected there:
  `metadata.source_api` is **generic provenance, not academic** (newsapi / github /
  hackernews / owid set it on 4,906 hot-window rows, so the feature as defined
  false-positives on all of them) — narrowed to an allowlist of our own academic
  aggregators; and **MDPI is not undetectable** — its feed declares `prism:doi` and
  we were discarding the field, 1,069 rows/week recovered by capturing what the
  publisher already sends. ScienceDaily, the false-positive shape #305 worried
  about, publishes no DOI anywhere and is a clean negative.

  **Why collection beat post-enrichment, since this repo's session argued the
  opposite:** a post-enrichment measurement on 2,178 scored rows gave 65/65 recall
  and looked decisive — but that sample contained **zero arXiv rows**, and
  `arxiv_announce` is the single largest evidence class by a factor of four *and*
  reads **0.000 after enrichment*. The gap was flagged when the decision was put to
  the owner and was still recommended past. **A named gap is not a discharged one.**

  Known limitation, accepted deliberately: publishers mint DOIs for journalism too
  (Nature News carries `prism_doi 10.1038/d41586-…`), so `doi_field` fires on it.
  The DOI is kept in `metadata['doi']`, so that slice stays measurable by registrant
  without a re-run.
- **STAGE TRAP, recorded because it nearly cost a dead detector:** the arXiv
  prefix is 91.6% reliable at collection and reads **0.000** in NexusMind
  production — enrichment re-fetches the body. Measure a feature at the stage it
  will run.

## 2026-08-09 — candidate features probed on 599 adjudicated production pairs

News-only cut (n=505, academic excluded). Negative class is **false merges**, not
random pairs, so these say "separates good merges from bad", not "finds merges".

| feature | AUC |
|---|---|
| **time proximity** (−\|Δh\|) | **0.809** |
| numeric overlap title+body | 0.581 |
| is_cross_language | 0.570 |
| not_same_source | 0.554 |
| rare numbers (≥4 digits, non-year) | 0.503 |
| length agreement | 0.453 (inverted) |

- **REFUTED — shared numbers.** The argument was good (digits survive
  translation; unrelated papers don't share a casualty count) and the data says
  0.581, with the sharpest variant at **0.503 = nothing**. No confirmed
  explanation; plausibly the negative class already shares dates/quantities.
- **CONFIRMED — time is the feature.** 0.809 here vs INST-10's 0.798 unweighted,
  different panel/seed/sample, and it *improves* when academic pairs are removed.
  ⛔ **"Blocked only on certification by a non-author" was STALE and is RETRACTED
  2026-08-16.** INST-10 was **certified 2026-08-09 by a non-author — a session of
  *this* repo** (NexusMind `b90ba9e`, registry row 131, note at
  `docs/vv/corroboration-dedup-registry.md:189`): AUC 0.798/0.767, `med_D > med_S`
  in 6/6 strata, Kish ESS 36.1, 5,000-draw permutation collapses to ~0.5, robust to
  the date-only confound. Two instrument defects found and fixed during it.
  ⚠️ **And the independence runs the OPPOSITE way to how this entry read: 0.798 IS
  INST-10**, authored by the author of the implementation it evaluates. **The 0.809
  measured here is the genuinely separate instrument.**

  **THE REAL BLOCKERS ARE THREE, and none is certification** (NexusMind, 2026-08-16):
  1. **The certification is PRECISION-SIDE ONLY and explicitly does not authorise
     enabling** — INST-10's blind spot is recall *entirely*, because every pair it
     scores is one the system already merged.
  2. **The recall test has never been run**, and its instrument is not ready: needs
     INST-4 (certified, recall-only) plus INST-2/**INST-3**, and INST-3 is
     **uncertified** (certifier `author`, control not run) and lives only on b650,
     off the deploy host.
  3. ⛔ **The shipped σ is the REFUTED value.** `NexusMind/config/app.yaml` has
     `sigma_hours: 72.0`. Sweep: σ=6 → 52.1/98.2 · σ=18 → **83.6/85.9** · σ=36 →
     97.8/56.8 · **σ=72 → 99.1/20.6 (FAILS)** · σ=120 → 100.0/9.2. Flipping
     `enabled: true` today ships a width where the term degenerates into a
     near-uniform `+max_adjustment` — **arithmetically a threshold decrease, the
     axis already measured dead.** "Flip temporal.enabled" was never one decision.

  ⭐⭐ **AND THE AUC CANNOT ARBITRATE σ AT ALL — it is σ-INVARIANT BY CONSTRUCTION**
  (registry blind spot (d)): it ranks on Δt and the adjustment is monotone in Δt.
  So the headline number is *silent on the only parameter that would ship*, while
  being cited as support for shipping. **New variant of the can-only-return-zero
  trap: a number that cannot vary with the decision variable.** ⚠️ Also blind spot
  (c): `_temporal_adjustment` compares a candidate to the **cluster reference
  (newest)**, not to a partner, so a *pairwise* AUC does not transfer to the
  variable production actually uses. Any before/after merge-set delta must run at
  **σ∈[12,24]**, never the shipped 72.
- Cross-language is a mild genuine positive (0.570), consistent with merged
  cross-language precision 0.857 vs same-language 0.426 at 0.94/0.90.
- Academic subset had **6 positives** — nothing reported from it; the 0.878 that
  appeared there is noise.
- Reproduction: `b650:~/nm-sweep/feature_probe.py`.

**Still untouched and now the top per-pair lever: PROP-2 ratio-margin scoring**
(ART-11: BUCC EN-DE F1 **77.0 → 94.8** on the train set, *same embeddings*). Attacks
hubness, which is what a 592-member attractor is. Needs no new labels.

⛔⛔ **THE ORIGINAL 77.0 WAS CORRECT. I "corrected" it to 82.8 on 2026-08-17 and that
was the error — retracted the same day.** Table 2 carries **four** cosine-baseline rows,
one per retrieval strategy, and four ratio rows:

| Func. | Retrieval | EN-DE F1 | EN-FR F1 |
|---|---|---|---|
| Abs. (cos) | **Forward** | **77.0** | 77.9 |
| Abs. (cos) | Backward | 75.9 | 74.7 |
| Abs. (cos) | Intersection | 82.8 | 80.9 |
| Abs. (cos) | Max. score | 80.1 | 79.2 |
| Ratio | all four | **94.8** | 91.8–91.9 |

`77.0 → 94.8` is forward-to-forward, a like-for-like comparison and the closest analogue
to what production does (a single directional scan). `82.8 → 94.8` is
intersection-to-intersection, equally valid and a different question. **Neither is wrong;
quoting one while naming the other's retrieval strategy is.** Always name the retrieval
variant.

⚠️ Table 3 is the **test** set and a **different comparison** — proposed vs *prior
published best*, not vs its own baseline: EN-DE 85.5 (Azpeitia et al. 2018) → 95.6;
EN-FR 81.5 → 92.9; EN-RU 81.3 → 92.0; EN-ZH 77.5 → 92.6. Schwenk (2018)'s EN-DE is 76.9,
adjacent to 77.0 and a plausible source of future confusion.

⭐ **The lesson, and it is the fourth occurrence of one root in a single day.** The
"transposed from EN-ZH's 77.5" story was a *guess dressed as a diagnosis*, and the
replacement number came from an automated PDF extraction — a derived surface — which I
had flagged as a failure class three times that same day before committing it a fourth
time, in the act of correcting someone else. **A correction is a claim and needs the same
verification as the claim it replaces.** Resolved by reading the rendered ar5iv tables.

Related: [[cd-v6-probe-hypotheses]] (the other place a probe/extractor choice was
decided by measurement), [[score-batch-shape-noise]] (any margin under 0.16 near
an op-point is noise, which binds every threshold in this file).
