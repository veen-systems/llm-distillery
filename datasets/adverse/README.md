# Adverse examples

Articles that **look like a lens and are not** — curated from observed production
failures, one file per filter.

Unlike the rest of `datasets/`, these files **are committed**. They are a few
kilobytes, hand-curated, and cannot be regenerated: each one records a specific
failure someone noticed on a specific day. Losing them means losing the only
evidence of the boundary they mark.

## Adjudication notes

Some cases are considered and **rejected** — the article looks adverse and is not. That
reasoning is worth as much as an accepted row and has nowhere to live in the JSONL, so it
goes in a dated note beside it:

- [`2026-08-05-ovr-flag-adjudication.md`](2026-08-05-ovr-flag-adjudication.md) — five ovr.news
  reader flags; four accepted, one rejected (forensic accountability work qualifies for
  Discovery). Also records a scale caveat on the `nature_recovery` row.

## Why these are not sampled

`scripts/experiments/sample_v7_negatives.py` draws random negatives. Those teach
the boundary between "in the lens" and "unrelated" — a boundary the scorers already
handle well. They teach nothing about the boundary that actually fails in
production:

> a story **about** a good outcome, versus a story about harm that **contains** one

Every case here scored in the top decile of its lens. They are high-information
precisely because the current models rank them highest.

## Record shape

```json
{
  "id": "...", "title": "...", "url": "...",
  "content": "...",                          // 300-char excerpt, see below
  "content_excerpt": true,                   // present only when truncated
  "class": "A -- harm-adjacent ...",         // added 2026-08-21; A or B, on every row
  "training_use": "HARD NEGATIVE ...",       // added 2026-08-21; only on §4b rows
  "content_original_length": 3975,
  "filter": "uplifting",
  "label": "adverse",
  "max_acceptable_wa": 3.85,
  "max_acceptable_basis": "p90 of 1947 scored uplifting articles in filtered_20260801 (median 1.36, p99 6.25)",
  "observed": {
    "scorer_version": "5.0",
    "raw_weighted_average": 6.7661,
    "normalized_weighted_average": 9.8104,
    "tier": "high",
    "scores": { "human_wellbeing_impact": 7.75, "...": 0 },
    "observed_at": "2026-08-01",
    "batch": "NexusMind/data/filtered/uplifting/filtered_20260801_*.jsonl"
  },
  "why_adverse": "...",
  "misleading_features": ["...", "..."],
  "provenance": "...",
  "labelled_by": "editorial judgement — NOT oracle-scored",
  "issue": "https://github.com/veen-systems/llm-distillery/issues/91"
}
```

Two fields in that example are not present on every row. `observed.scorer_version`
records which model version produced the observed scores — without it the row is
not reproducible once the scorer moves on. **Re-counted 2026-08-21 (this prose had
drifted): `observed.scorer_version` is on 12 of 16 rows, `issue` on 14 of 16,
`class` on 16 of 16, `training_use` on 5 of 16.** The earlier "two … / three older"
description dated from when this file held 5 rows and was never updated
for them. The block above is the uplifting row with `scorer_version` spliced in,
so it matches no single row on disk; treat it as the target shape, not a sample.
`scripts/flag-evidence.ts` in the ovr.news repo emits this shape directly from a
reader flag, leaving `why_adverse` and `misleading_features` as TODOs.

### `content` is a 300-char excerpt, not the article

Truncated repo-wide on 2026-08-06 (#97). These rows previously carried complete
article bodies — median 3,975 characters here, several ending on a full sentence
— and this repository is public, so they were republication rather than evidence.
The excerpt keeps enough to recognise the article; `url` is the route to the rest.

`content_excerpt: true` and `content_original_length` appear only on rows that
were actually cut, so a short row is distinguishable from a truncated one. Nothing
else changed: `id`, `url`, `title`, every score, label and note is byte-identical.

**What this costs.** A row's `why_adverse` reasoning sometimes cites material past
character 300 — the reasoning still stands, but you can no longer check it against
the text without fetching the URL. That was the trade accepted when the excerpt
length was chosen; 300 matches the labelling-time floor used elsewhere in this
repo (#93) rather than being picked arbitrarily.

### `max_acceptable_wa` is an assertion, not a label

These are **not** oracle-scored, and the field is deliberately not called
`oracle_wa`. Nobody ran DeepSeek or Gemini over them and derived a point value; a
human read the article and decided it does not belong in the lens.

What is defensible without an oracle is an **upper bound**: this article must not
rank in the top decile of its lens. `max_acceptable_wa` is therefore the p90 of a
real scored batch, recorded with the batch it came from so the number is auditable
and re-derivable rather than invented.

Consequences:

- **Usable as gate probes now.** The assertion `predicted_wa <= max_acceptable_wa`
  is meaningful and directional.
- **Not usable as REGRESSION targets as-is.** `max_acceptable_wa` is an asserted
  upper bound, not a point label: oracle-score first if a numeric target is wanted,
  and put that value somewhere else — never overwrite the assertion with it.
  ⚠️ **Amended 2026-08-21:** the 6 rows carrying `training_use: HARD NEGATIVE` *are*
  intended as supervision, but as **binary negatives** (playbook §4b), which needs no
  oracle score. The two uses are different and the distinction is the whole point —
  a bound is not a label.

`misleading_features` records *which surface signals* fooled the scorer. That is
the part worth generalising from: it says what a fix has to learn to discount.

## Current contents

Kept current as of **2026-08-21**, and the counts below were read off disk on that
date rather than incremented by hand. This table has drifted **twice** now — it read
n=1 for `cultural_discovery` while four rows were on disk and omitted
`nature_recovery` entirely (fixed 2026-08-05), then read n=2 for `uplifting` and n=1
for `belonging` against 4 and 2 on disk (fixed 2026-08-10). **If you add a row, edit
this table in the same commit** — and verify with:

```bash
for f in datasets/adverse/*.jsonl; do echo "$(wc -l < "$f") $f"; done
```

| File                       | n   | Cases                                                                                                                                                                                                       |
| -------------------------- | --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cultural_discovery.jsonl` | 5   | Homo antecessor cannibalism (raw 6.14); smallpox genomes, DE + ES same study (6.56 / 6.67); Inca child sacrifice (6.44); **Kixikila, a living Angolan savings practice with no finding in it (6.78)**       |
| `uplifting.jsonl`          | 16  | child sex trafficking investigation (raw 6.77, 6th of 3,530); greyhound export (5.86); minor-rape arrests (Herald ZW); business-centre op-ed (Namibian); the 7 accepted 2026-08-10 (5.12 → 4.06) — **plus 5 promoted 2026-08-21 from the harm screen** (5.98 → 5.26; a 6th, UNODC meth, was demoted to `candidates/` during review — its own rationale conceded a true-positive reading), all `class: A`, all carrying `training_use: HARD NEGATIVE` |
| `solutions.jsonl`          | 2   | greyhound export as "delivered solution" (raw 4.51, above its batch p99 of 4.07); **Hong Kong AI facial-recognition enforcement drones, scored 9-12 months before they exist (4.68, batch p99 3.87)**        |
| `belonging.jsonl`          | 2   | expropriated Venezuelan estate in ruins (raw 6.36, batch p99 5.10); second row added 2026-08-05                                                                                                              |
| `nature_recovery.jsonl`    | 1   | Madagascar invasive rats blocking small-mammal recovery (raw 5.21 — **scale caveat**, see the 2026-08-05 adjudication note)                                                                                  |

### 2026-08-21 additions — the harm screen (uplifting, 5 rows)

Selected from **~14,000** distinct stage-2 rows at or above the 4.5 op-point ⚠️ (the screen logged 13,927; a re-run over the same window returns **14,031** distinct ids — the original scan read a cycle file mid-write, so 13,927 is not reproducible. No rate is derived from it, so nothing downstream moves.)
(sadalsuud `NexusMind/data/filtered/uplifting/`, 2026-08-07 → 08-21), harm-lexicon
screened over titles (158 hits), adjudicated on title + 340-char excerpt against the
owner's 2026-08-05 test — *does the article contain a process going well NOW?*
⚠️ The lexicon is a **candidate generator, not a population**; no rate is derived from it.
⚠️ Adjudicated on excerpts, not full text — the 2026-08-09 rule (*three of five drafts
reversed on full read*) means these should be re-read in full before they gate anything.

Three of the five normalize **above 7**, i.e. near the top of the Thriving feed; the
Sahiwal torture row normalizes to **8.284** with `human_wellbeing_impact` 6.05.

⭐ **Most harm-lexicon hits were TRUE positives** — rescues, survivor recovery, falling
murder rates, convictions delivered. The lens is largely right on harm-adjacent content.
That is why **6 rows were parked, rejected or demoted rather than kept**
(`candidates/2026-08-20-harm-screen-parked.jsonl`), each with its TP reading recorded.

⛔ **Standing rule (owner, 2026-08-20): a row with a serious true-positive reading is a
bad gate probe by construction** — it tests the boundary, and the boundary is where noise
makes the test meaningless. Pick the ones that are truly FP; do not escalate line calls.

⛔ **Do not read `cap_applied: null` as "no cap was warranted"** — it is null on
236,879 of 236,879 rows because `cap_triggers._TRIGGER_REGISTRY` is **empty by design**
(since 2026-07-14), so `detect_caps` returns `[]` for every filter. Disarmed, not broken. See
`docs/evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md` addendum.

The greyhound article appears in two files: it scored high in **more than one lens
simultaneously**, so that failure is not lens-specific. The smallpox pair is the same
study in two languages, which is a different thing — evidence for the cross-language
dedup gap (NexusMind#291/#295), not for a shared failure mode.

See [issue #91](https://github.com/veen-systems/llm-distillery/issues/91) for the
diagnosis.

### 2026-08-02 additions (reader flags, ovr.news)

Both came from the same 24h batch of owner flags and both are the *about vs contains*
shape, but they fail differently and are worth reading as a pair:

- **cultural_discovery** — the lens scored the article correctly on every dimension it
  has. Novelty, evidence and heritage are all really there; what is missing is any
  dimension that asks what the finding is *of*. A fix cannot come from discounting a
  misleading surface feature, because no feature is misleading. This is a **lens
  definition gap**, not a scoring error.
- **belonging** — a straightforward feature trap: `rootedness` 8.17 fired on a
  remembered place the article reports as destroyed. A fix can come from tense and
  loss-frame discounting.

The belonging case also shows a **ranking illusion worth checking before dismissing a
flag**: raw 6.36 is above its batch p99, but percentile normalization mapped it to
6.54 / tier `medium`. "The lens only scored it medium" was not true of the raw score.
When triaging a reader flag, compare the **raw** wa against the batch distribution;
the normalized number answers a different question (ADR-014).

Two obituaries in the same flag batch were deliberately **not** added here — that
shape is owned by the universal obituary detector, per the v5 hard-negative cohort
decision (#62). They are recorded as v5 production FNs in
`memory/obituary-v4-hypotheses.md` addendum 8.

### 2026-08-05 additions (second reader-flag batch, ovr.news)

Two rows from four flags. Both break the *about vs contains* pattern that every earlier
row shares, and each names a **different** failure layer:

- **cultural_discovery — Kixikila.** The first row in this file where the failure is
  neither a lens-definition gap nor a feature trap, but a **weighting** problem with a
  concrete target. `discovery_novelty` (5.58) is the lowest of the five dimensions and
  the only one encoding whether an epistemic event occurred; `cross_cultural_connection`
  (8.00) and `heritage_significance` (7.10) are the highest and both fire on subject
  matter. The lens-defining dimension was outvoted 2:1 by topic-proximity dimensions.
  Unlike the smallpox and Inca rows, a fix has something to grip.
- **solutions — Hong Kong enforcement drones.** A **temporal** failure the earlier rows
  do not cover: the intervention does not exist yet (9-12 months of research, zero fines
  issued on drone evidence), and `solution_concreteness` (6.56, the top dimension) fired
  on the enforcement statistics of the *already-live* smoking ban described in the same
  article. Generalisable shape: an article about a proposed extension to a working
  programme inherits the working programme's evidence.

Both rows carry explicit **scope warnings** in `why_adverse`, and they should survive any
distillation. Kixikila must not teach suppression of non-Western traditional practice —
the article is good and belongs in `belonging`, which lost the placement by 0.043. The
Hong Kong row must not teach that workplace-safety enforcement is adverse; the objection
is biometric surveillance as the mechanism, scored above p99 before it is built.

A **process note** that cost real accuracy: `scripts/flag-evidence.ts` emits its draft
`filter` from ovr.news `articles.filter`, which is a last-writer-wins ingestion artifact,
not the lens the article published under. It filed Kixikila as a **belonging** adverse
row. Belonging is the *correct* lens for that article — accepting the draft would have
trained belonging to reject something that genuinely belongs to it. Check the draft
`filter` against `published_observations.lens` and `article_filter_scores` before
appending anything this script produces.

The other two flags in the batch were image failures (a Times of India default share
image served as the hero on four articles) and are not lens adverse examples. They are
an ovr.news `domain_og_images` warm-up problem, tracked there.

### 2026-08-10 additions (first oracle-sourced batch — uplifting, 7 of 21)

The first rows here that did not come from a reader flag. Source: the ADR-023
active-learning batch of 2026-08-09, sampled **above** the op-point. Full
reasoning, including the 3 rejections and 11 holds, is in
[`2026-08-10-uplifting-oracle-batch-adjudication.md`](2026-08-10-uplifting-oracle-batch-adjudication.md).

Three things it established that outlive the batch:

- **`content_type: solutions_story` is the oracle's residual bucket, not a lens
  signal.** It is the tag on the prompt's own 7.3/10 and 5.8/10 *good* examples;
  it means "none of the five penalty caps applied". The claim that "uplifting is
  absorbing solutions-lens material" was an artifact of reading it as routing.
  The real dominant class among the 21 is **academic-abstract register** (9 of
  21; 6 of the 13 that sit in the 4.0–4.5 band) — abstract prose supplying benefit vocabulary and a high
  `evidence_level` with no beneficiary in the text.
- **`raw ≥ 4.01` is the admission bar for this file.** Promotion asserts
  `predicted_wa ≤ max_acceptable_wa` (3.85 for uplifting); if the observed score
  is nearer the bar than the #95 |0.16| batch-noise floor, the assertion is a
  coin flip, not a gate. One candidate was rejected on exactly this (raw 4.004,
  margin 0.154). New rows carry **`assertion_margin`** so the property is
  checkable instead of remembered.
- **A row whose `oracle_wa` lands in 3.5–4.0 is held, not labelled.** The batch
  selected on "oracle below 4.0", but 3.95 against a 4.0 cut is not a negative —
  one half-point increment on `human_wellbeing_impact` (weight 0.30) moves the
  average 0.15. Six rows are held on this, including the batch's one genuine
  ADR-015 case (Rwanda–EU agricultural financing).

Two accepted rows also document **oracle-prompt gaps** rather than student
errors, which is why they are worth more than their scores: the EBA ESG
dashboard (prudential regulation is not in the `corporate_finance` cap's list of
stock prices / earnings / funding rounds / valuations / M&A / IPO, so no cap
fired) and the Namibian minister's speech (check C, PURE SPECULATION, did not
fire on an aspiration with no programme behind it).

New optional fields on these rows: **`oracle`** (the gemini-flash label block —
explicitly *not* the source of `max_acceptable_wa`, which stays an editorial
assertion per the section above) and **`assertion_margin`**.

Four of the seven carry explicit **scope warnings** in `why_adverse`, following
the Kixikila / Hong-Kong-drones precedent. The boundaries asserted are
*preclinical vs delivered*, *announcement vs outcome*, *prototype vs delivered
benefit*, and *biography vs outcome* — none of them "medicine / gender-equality
policy / animal welfare / women in science is adverse".

## Adding a case

Add one when a scorer ranks something highly that plainly does not belong —
especially when a reader reports it. Record the observed scores **at the time**,
since re-scoring later with a different model loses the evidence. Write
`why_adverse` as what the article is *about* versus what the filter scored, and
list the surface features that misled it.

Source the observed block from the NexusMind filtered batch the article actually
went through (`NexusMind/data/filtered/<lens>/filtered_*.jsonl` on sadalsuud), not
from a rescore — the batch carries the production stamp and the population needed
for the p90 basis in the same file. Those batches roll over, so a case is only
recordable for as long as its batch survives.

`.gitignore` ignores `datasets/*` but re-includes `datasets/adverse/` explicitly, so
a new file here is committed like any other. Before 2026-08-02 it was not: the rule
was `datasets/` (whole-directory), which git will not descend into, and the two
original files had to be `git add -f`'d. A new case added in that window would have
been silently dropped.
