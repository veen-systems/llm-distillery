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

- **Which copy of a duplicated wire story survives is decided by HTTP completion
  order — it is arbitrary, not a source policy.** Traced 2026-08-07 (night) by
  reading the call path, not by waiting for counts. `_deduplicate_by_hash`
  (`src/aggregators/content_aggregator.py:352`) keeps the **first item it meets
  in `all_items`**; there is no publisher preference anywhere in it. `all_items`
  is assembled in `enabled_sources` order (`content_aggregator.py:~683`,
  commented "Deterministic order preserves dedup semantics (first-seen wins)") —
  **but that ordering cannot explain the observed drops**, because both of them
  happened *inside a single source*. The 10 top-level sources are
  `concurrent_rss`, `bluesky`, `mastodon`, `devto`, `github`, `gdelt`,
  `gdelt_constructive`, `news`, `gnews_eval`, `newsdata_eval`;
  `gn_asia_gn_yemen` and `us_news_cnn` are **feeds inside `concurrent_rss`**
  (6,177 of 6,650 items that run). Within that aggregator, results are harvested
  by `concurrent.futures.as_completed()` and folded in with
  `all_items.extend(items)` (`concurrent_rss_aggregator.py:175` and `:91`), so
  feed order is **network latency on the night**. Same story, two outlets: the
  one whose HTTP fetch returns first wins, and the next run may reverse it.
  **This is LD#95's family — a reproducibility defect, not a systematic bias.**
- **Google News is not favoured by any mechanism.** Both observed survivors were
  `gn_*` feeds, which reads as favouritism at n=2 and is fully explained without
  it: GN contributes hundreds of feeds (FS#120: 240 of 312 GN sources are single
  named outlets), so GN has far more tickets in a lottery decided by which fetch
  returns first. A base-rate effect, not a policy. **Do not cite the n=2 pattern
  as evidence of GN precedence.**

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

- **Cross-lingual NER (`xlm-roberta-large-finetuned-conll03-english`).** The
  memo's own pre-committed next step, described as *"the cheapest intervention
  to verify — re-run `measure_matching_geometry.py` with the new NER model; no
  architecture change."* Step 4 of 8 in the next-phase plan; **needs no new
  labels**, and its outcome decides whether a labelling campaign is needed at all.
- **Wikidata QIDs instead of surface-token NER.** The measured failure was
  Latin-script token collision — ids fix that by construction, and fix the
  cross-language half at the same time ("Verenigde Naties" ↔ "United Nations").
  Raised in the next-phase plan; never tried.
- ~~**MinHash from FluxusSource.**~~ **RESOLVED 2026-08-07 (night): recommend
  DELETE, do not evaluate as a feature** (ducroq/FluxusSource#134). Four
  independent grounds, none of which need a measurement: (a) the signal already
  exists downstream and better — NexusMind `story_dedup.py` runs E5 multilingual
  cosine with a dedicated `cross_source_threshold=0.88`, and char-3-gram Jaccard
  is strictly weaker; (b) it **degrades cross-language** — running the real
  functions gives reworded-same-story 0.508, unrelated 0.023, but
  **cross-language same story 0.195**, nearer to unrelated than related, on a
  corpus that is multilingual by construction; (c) wiring it into collection-stage
  dedup makes corroboration **worse** — a fuzzier matcher drops *more* of the
  evidence FS#133 is about; (d) emitting the signature instead is blocked by a
  live bug (`numpy.uint64` is not JSON-serializable, while the code comment
  claims it is) and would cost ~19 MB/cycle and ~206 s of added CPU, **2619×**
  the current hash cost, on the must-not-fail stage.
  Correction to the claim as first written here: it is **not** literally zero
  call sites — `compute_all_hashes` calls it twice and 14 of 37 tests exercise
  it — but `compute_all_hashes` has no production caller, so the chain is dead
  from the top and has **never executed in ~8 months**. Deleting also drops
  `scipy` (nothing else needs it): **114 MB of a 450 MB venv**, and removes the
  module-level import that caused a **26-hour production outage** on 2026-06-30.
  The one honest gap: nobody has measured how many cross-source near-duplicates
  MinHash would catch above exact match. Not worth blocking the delete on.
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

**Refined 2026-08-07 (night), and the refinement matters for step 3.** The
deletion is *arbitrary with respect to publisher* (see the completion-order
entry under CONFIRMED), not slanted toward or away from any outlet. Two
consequences pull in opposite directions and both are load-bearing:

- **Good for step 3's validity**: the surviving copy is a uniform-ish draw from
  each duplicate set, so the corpus is **depleted, not skewed by source**. A
  source-conditioned feature (`source_pair_prior`, deferred to V2) is therefore
  not silently poisoned — the missing rows are missing at random across
  publishers, not concentrated in one.
- **Bad for step 3's power, and this is the binding one**: what is removed is
  one whole side of every easy positive *pair*. Corroboration labels are
  pair-shaped, so deleting either member destroys the pair outright. The loss is
  unbiased in *which* member goes and total in *whether the pair survives*.
  At n=23 with case_1 supplying 21, this is not a rounding error.

So: arbitrariness rescues the feature semantics and does nothing for the sample
size. **Still do this before trusting any n from step 3** — but expect the
answer to be "the pairs were never there", not "the pairs are biased".

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
3. mine the labels already held — hours of compute ← **the unblocker**
4. cross-lingual NER swap ← **the owner's question, answered cheaply**

Related: [[cd-v6-probe-hypotheses]] (the other place a probe/extractor choice was
decided by measurement), [[score-batch-shape-noise]] (any margin under 0.16 near
an op-point is noise, which binds every threshold in this file).
