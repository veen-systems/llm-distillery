# Adverse examples

Articles that **look like a lens and are not** — curated from observed production
failures, one file per filter.

Unlike the rest of `datasets/`, these files **are committed**. They are a few
kilobytes, hand-curated, and cannot be regenerated: each one records a specific
failure someone noticed on a specific day. Losing them means losing the only
evidence of the boundary they mark.

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
  "id": "...", "title": "...", "url": "...", "content": "...",
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
not reproducible once the scorer moves on — but only the two 2026-08-02 rows
carry it; the three older rows predate the field. `issue` is the reverse: the
three older rows have it, the 2026-08-02 rows omit it because no issue was filed
for them. The block above is the uplifting row with `scorer_version` spliced in,
so it matches no single row on disk; treat it as the target shape, not a sample.
`scripts/flag-evidence.ts` in the ovr.news repo emits this shape directly from a
reader flag, leaving `why_adverse` and `misleading_features` as TODOs.

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
- **Not usable as training labels as-is.** Oracle-score them first if they are to
  become supervision, and put the resulting point labels somewhere else — do not
  overwrite the assertion with an inferred value.

`misleading_features` records *which surface signals* fooled the scorer. That is
the part worth generalising from: it says what a fix has to learn to discount.

## Current contents

| File                        | n   | Cases                                                                                 |
| --------------------------- | --- | ------------------------------------------------------------------------------------- |
| `uplifting.jsonl`           | 2   | child sex trafficking investigation (raw 6.77, 6th of 3,530); greyhound export (5.86) |
| `solutions.jsonl`           | 1   | greyhound export as "delivered solution" (raw 4.52, above p99)                        |
| `cultural_discovery.jsonl`  | 1   | Homo antecessor cannibalism find (raw 6.14, batch p99 4.92)                           |
| `belonging.jsonl`           | 1   | expropriated Venezuelan estate in ruins (raw 6.36, batch p99 5.10)                    |

The first two source articles scored high in **more than one lens simultaneously**,
which is why the greyhound case appears twice. The failure is not lens-specific.

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
