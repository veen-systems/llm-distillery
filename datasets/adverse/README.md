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
  "labelled_by": "editorial judgement — NOT oracle-scored"
}
```

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

| File             | n   | Cases                                                                                 |
| ---------------- | --- | ------------------------------------------------------------------------------------- |
| `uplifting.jsonl` | 2   | child sex trafficking investigation (raw 6.77, 6th of 3,530); greyhound export (5.86) |
| `solutions.jsonl` | 1   | greyhound export as "delivered solution" (raw 4.52, above p99)                        |

Both source articles scored high in **more than one lens simultaneously**, which is
why the greyhound case appears twice. The failure is not lens-specific.

See [issue #91](https://github.com/veen-systems/llm-distillery/issues/91) for the
diagnosis.

## Adding a case

Add one when a scorer ranks something highly that plainly does not belong —
especially when a reader reports it. Record the observed scores **at the time**,
since re-scoring later with a different model loses the evidence. Write
`why_adverse` as what the article is *about* versus what the filter scored, and
list the surface features that misled it.
