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
- `docs/investigation/corroboration-next-phase-plan.md` — **DRAFT, its ordering
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
  <!-- verify: manual — rerun /tmp/ner_measure.py pattern on a fresh sample; the
       claim is about the extractor, so it should reproduce on any production day -->

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

From `corroboration-next-phase-plan.md`'s RECOMMENDED ORDER (8 steps). Verified
2026-08-07: **step 1 (Phase 4a, "stop asserting a count precision cannot
support") is already discharged** — the hedge is live in both languages
(`ovr.news/src/i18n/translations.ts:84/369`) and the boost ladder was replaced by
a flat 1.3× capped at 9 (`corroboration-boost.ts:61/69`). So the live front is:

2. settle representation (title vs title+body) — no new labels
3. mine the labels already held — hours of compute ← **NOW THE ONLY BLOCKER**
4. ~~cross-lingual NER swap~~ ← **DONE 2026-08-08, and it passed.** The
   extractor was the problem: median 2 → 12 entities/article, and unrelated-pair
   collisions went from `ej = 1.000` to **0 of 4,000 above 0.3**.

**So the ordering has collapsed to one item.** Step 4 was the cheap diagnostic and
it came back clean, which means the remaining question is entirely **sample
size** — n=23 with case_1 supplying 21. Step 3 is no longer one of several
parallel unknowns; it is the whole remaining path. Expect its yield to be a
**floor**, because FluxusSource deletes the easiest positives at collection
(see "the corpus is pre-depleted" above).

Related: [[cd-v6-probe-hypotheses]] (the other place a probe/extractor choice was
decided by measurement), [[score-batch-shape-noise]] (any margin under 0.16 near
an op-point is noise, which binds every threshold in this file).
