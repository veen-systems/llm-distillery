# Contract A, designed rather than patched

**Proposal, 2026-08-14. Not approved, not implemented.** Supersedes the incremental
fixes (#304's four corrected values) rather than building on them.

---

## The one rule this is built on

FluxusSource is **the only component that ever sees the network, the feed document,
and the raw bytes.** Everything it does not record at collection time is **lost
forever** — no consumer can recover it, at any cost, ever.

That gives two tests, and every field must pass both:

| test | question | if it fails |
|---|---|---|
| **1. Exclusive** | Can *only* the collector know this? | A consumer can recompute it. **Leave it out** — a stored copy of a derivable value is a second source of truth that will eventually disagree. |
| **2. Perishable** | Is it destroyed if not recorded now? | It can be recovered later. **Leave it out.** |

**A field belongs in Contract A if and only if it is exclusive AND perishable.**

Today's contract gets this backwards in both directions: it carries derivable values,
and it discards irrecoverable ones.

---

## What comes OUT (derivable — fails test 1)

| field | why | recompute by |
|---|---|---|
| `word_count` | The consumer has the text. Also the field that broke `required` — absent on 13,214 api and 892 social rows. | counting |
| `reading_time_minutes` | A derivation *of a derivation* — word_count ÷ 200. | arithmetic |
| `title_length` | trivially derivable | `len(title)` |
| `needs_sentiment_analysis` | a consumer's routing decision, not a fact about the article | consumer policy |

`raw_content_length` **stays** — it is the length *before cleaning*, which the
consumer never sees. That is perishable, and it passes.

**This is the important half of the redesign and it is counter-intuitive:** removing
`word_count` makes the contract *stronger*, because it removes the field that forced
`required` to be wrong, and it removes a number that can silently disagree with the
text beside it.

---

## What goes IN (exclusive + perishable)

### A. Time — the publisher's stated instant, not our interpretation of it

**The defect this fixes is live and measured.** `published_date` is parsed, converted
to UTC, and the offset is *stripped*. NexusMind then reads naive as UTC; ovr.news's
JavaScript reads the identical string as **local time**. Both apply the same
"boost under 24h" rule, so **one boosts an article the other does not** — and this has
been true for as long as both have existed.

⚠️ **No schema could have caught it.** Both hops are internally consistent, and a
declaration that `published_date` is a date-time string is satisfied by *both*
readings. **Type was declared; meaning never was.** This is the one defect class a
shape-only validator provably cannot see.

```
"published": {
  "instant":        RFC 3339 WITH OFFSET, required        // the answer
  "raw":            "Wed, 13 Aug 2026 16:10:06 +0200"     // exactly what the feed said
  "element":        "pubDate" | "dc:date" | "atom:updated" | "prism:publicationDate"
  "had_timezone":   true | false                          // ⭐ the load-bearing one
  "precision":      "second" | "minute" | "day"
  "fabricated":     true | false                          // we invented it; see below
}
```

- **`had_timezone` is the single most valuable new field in this document.** It
  separates *"the publisher stated UTC"* from *"the publisher stated nothing and we
  assumed"*. Today those are byte-identical downstream and the distinction is
  **unrecoverable by construction** — every row is naive by the time anyone sees it.
- **`precision`** — many feeds publish a *date*, no time. Storing that as midnight is
  a lie of ~12 hours, and every recency calculation inherits it.
- **`fabricated`** — the parser has a `now - 2h` fallback for date-less entries. A
  fabricated date currently looks exactly like a real one, and reads as *fresh*.
- **`raw`** — costs ~30 bytes and makes every other field in this block auditable.

### B. Language — separate the ANSWER from the INPUTS from the EVIDENCE

Today there are five language-ish fields and **two of them are inputs to the decision,
not answers** — so nesting them all together would invert the dataflow. The fix is to
say which is which.

```
"language": {
  "code":             "en" | "nl" | "zh" | "sr" | "unknown"  // THE ANSWER
  "script":           "Latn" | "Cyrl" | "Arab" | "Hans"      // ⭐ ISO 15924
  "scripts_present":  ["Hans", "Latn"]                       // mixed-script reality
  "declared_by_feed": "en-GB" | null                         // INPUT: what the feed claimed
  "method":           "detected" | "feed_declared" | "config_hint" | "fallback"
  "confidence":       0.0-1.0
  "sample_chars":     int                                    // ⭐ how much text the detector saw
}
```

- **`sample_chars`** is exclusive and perishable: a detection made on 40 characters
  and one made on 4,000 are not the same claim, and the consumer cannot tell them
  apart afterwards. With 25.7% of the corpus being sub-300-char headline echoes, this
  is not hypothetical.
- **`code` uses the reachable set, not BCP 47.** The producer deliberately folds
  `pt-BR` → `pt` because ovr dispatches translation on the bare code. Declaring BCP 47
  would promise consumers a value the producer removes. `zh-cn`/`zh-tw` are kept
  because they are legal and intended.
- ⚠️ **Never populate `code` from `declared_by_feed` without saying so** — that is
  what `method` is for. Feeds hardcode `en` incorrectly at scale.


**Script belongs here, and it fixes a conflation already in the data.** The producer
emits `zh-cn` / `zh-tw` — but Simplified vs Traditional is a **script** distinction
(`Hans`/`Hant`), not a region one. A Taiwanese publisher can emit Simplified and a
mainland one Traditional, so the region subtag carries a fact it does not describe.
Same shape as `source_group` mixing geography with topic. Splitting `code` from
`script` also makes Serbian, Kazakh, Uzbek and Punjabi representable at all.

⚠️ **`script` is the one field here that is arguably DERIVABLE** — a consumer can read
Unicode script properties off the stored text. It earns its place anyway:

1. **Removing `word_count` creates the obligation.** Whitespace tokenisation is invalid
   for Han, Kana and Thai. That bug shipped here once: `len(text.split())` scored a CJK
   feed at **2** words against a true **89**, and a minimum-length rule then dropped
   every such article. If we take the count away, we owe consumers the field that says
   how to compute it.
2. **Not recoverable from `code`.** Language does not imply script; script does not
   imply language.
3. **A corruption tripwire.** Mojibake has a script signature — UTF-8 misread as
   Latin-1 turns non-Latin text into Latin-supplement noise. A script recorded *at
   fetch* that disagrees with the stored text catches a mangling nothing else reports.

### C. Origin — geography, and split from topic

**Requested, and it is exactly the right kind of field: a property of the SOURCE, not
of the text.** A consumer cannot infer a publisher's country from an article, and
guessing it from language is wrong in both directions.

```
"origin": {
  "country":  "NG"                    // ISO 3166-1 alpha-2, the PUBLISHER
  "region":   "west_africa"
  "timezone": "Africa/Lagos"          // ⭐ IANA
}
```

- ⭐ **`origin.timezone` is what makes an offset-less date recoverable.** With it, a
  naive publisher date can be interpreted correctly *after the fact*; without it the
  ambiguity is permanent. It converts §A's worst case from unrecoverable into merely
  awkward.
- **This also fixes a real conflation.** `source_group` currently mixes three
  different axes — of 107 groups, **64 are geography, 37 subject, 6 collection
  method**. That is why nobody can answer "how much of our corpus is African
  publishers" without parsing config-file stems. Split it: `origin.*` for where,
  `topic_group` for what.
- It is **config data**, not detection — one line per source in the YAML the collector
  already reads.

### D. Fetch — the network transaction, which nothing downstream ever sees

```
"fetch": {
  "url_requested":    "https://news.google.com/rss/articles/CBM..."
  "url_final":        "https://guardian.com/..."     // after redirects
  "http_status":      200
  "charset_declared":  "iso-8859-1" | null           // ⭐ what the header SAID
  "charset_detected":  "utf-8"
  "charset_used":      "utf-8"                       // ⭐ what we decoded with
  "content_encoding":  "br" | "gzip" | null
  "at":                RFC 3339 with offset
}
```

- ⭐ **The charset triple fixes a measured, live corruption.** `requests` returns
  `ISO-8859-1` for a charset-less `text/*` response — **not `None`** — so
  `.decode(resp.encoding or "utf-8")` is dead code. Result: **5.6% of rows carry
  introduced mojibake, and non-English is hit 6.9× harder than English.** Recording
  all three values makes the bug *visible in the data* instead of requiring someone to
  notice mangled text months later.
- **`url_requested` vs `url_final`** matters because Google News is ~25% of the corpus
  and is *entirely* a redirect problem. Today `url` is one string and the question
  "what did this actually resolve to" has no answer.
- **`content_encoding`** — brotli silently broke **32% of feeds** once, and was
  misdiagnosed as Cloudflare interstitials for weeks.

### E. Content fidelity — what we actually got, stated rather than guessed

```
"content_meta": {
  "kind":            "full_text" | "feed_summary" | "headline_only"
  "truncated":       true | false
  "raw_length":      int                     // before cleaning
  "echoes_title":    true | false
}
```

⭐ **This retires the 300-character floor.** That threshold exists *only* because
nobody downstream can tell a full article from a headline stub, so length is used as a
proxy. **The collector knows which it is and simply never said.** A stated `kind` is
strictly better than a guessed length — and unlike the floor, it does not silently
double as a language and source filter.

### F. Feed — properties of the feed document itself

```
"feed": {
  "title":             "The Guardian — World news"
  "declared_language": "en-gb"
  "cadence_hours":     4.2        // measured, not declared
  "ttl_declared":      60         // the feed's own <ttl>
}
```

Only the collector ever opens the feed document. All four are perishable.


### G. The non-event — what was NOT collected, and why

⚠️ **Categories A–F all presuppose that a fetch happened.** The observation the
collector uniquely makes and never records is the one where there was **no transaction
at all**. *(Missed here entirely; supplied by pipeline-atlas from the chain model. The
six above came from defects tripped over — this one came from asking the map.)*

Two decision sites refuse work **before the network**:

| site | where | exits | records |
|---|---|---|---|
| **A** | `content_collection.py · select_sources_to_collect` | disabled · not due yet | **nothing at all** |
| **B** | `content_aggregator.py` | disabled · circuit open · plugin not found · no `run()` · no feeds due | `{items: 0, skipped: reason}`, **no error key** — reads as a successful visit that found nothing |

**Four states are indistinguishable downstream**: refused at A (no trace), refused at B
(mislabelled empty), fetched and the publisher had nothing, fetched and all dropped by
dedup. **Only the third is describable by anything above.**

⭐ **This is the highest-value non-reconstructible fact in the stage.** A consumer
counting rows per source per cycle cannot separate *"this publisher went quiet"* from
*"we stopped asking"* — **opposite editorial meanings.** One is news about the world;
the other is a bug in us.

```
collection (per source, per cycle — a sidecar, not a row field)
  outcome                 fetched | refused_pre_dispatch | refused_in_aggregator | empty
  refusal_site            "A" | "B" | null
  refusal_reason          disabled | not_due | circuit_open | no_feeds_due | ...
  health_state            HEALTHY | STALE | DEAD | THROTTLED | OVER_POLLED   measured, at fetch
  poll_interval_actual_h  4.0        OUR rhythm, not the feed's
  raw_item_count          37         BEFORE dedup
  items_emitted           12
  first_seen_run          "collection_20260801_120500"   for a re-offered item
```

- **Site A is the silent half.** A and B refusals have different fates — invisible vs
  mislabelled-as-empty. Recording only one records the wrong one.
- **`poll_interval_actual_h` is NOT §F's `cadence_hours`.** That is the *feed's* rhythm
  (the publisher); this is *ours* (our config). Conflating them is exactly what hides
  the overpoll fault, where a source with no scheduling metadata is collected **every
  tick**.
- **`health_state` is measured, not config.** The collection path *writes to* the health
  tracker and never queries it, so a source's condition at collection time reaches a
  human by digest email and never rides with the row.
- **Dedup provenance.** Dedup drops on `content_hash` *before reading any field*,
  cross-run, and `raw_item_count` never leaves the stats file. *"Offered again, first
  seen on run X"* is observed and destroyed — a fact about **publisher behaviour**
  (recirculation, silent edits, sticky items) visible only to the collector.

---

## What a redesign would INVALIDATE

*(pipeline-atlas, ranked by how quietly each breaks.)*

1. ⭐ **`validate_production_contract.py`'s strip list — breaks silently and blames the
   wrong repo.** It validates a *reconstruction* of Contract A after subtracting
   NexusMind's own stamps. Reshape without extending the strip list and it reports
   `additionalProperties` violations **against the producer, for keys the producer never
   emitted.** Put this in the definition of done.
2. **`_CONTRACT_A_REQUIRED` (`main.py:118`)** — a hand-copied `frozenset` synced **by a
   comment**, dropping rows on the production path. Diverges the moment a new required
   set lands; nothing compares them.
3. ⭐ **"Both schemas close the top level."** `additionalProperties: false` on producer
   *and* consumer, so any added field fails at the consumer unless both move together.
   **A redesign cannot ship incrementally under the current shape** — the envelope
   question arrives as a hard blocker, not a design choice.
4. **"`items_collected` is what survived, not what arrived."** Exists *only because*
   `raw_item_count` never escapes. Publishing it **dissolves** the trap and makes
   `items_collected + duplicates_removed = raw_item_count` checkable for the first time.
5. **"A stored row is not relabelled by re-collection."** Write-once, because
   `content_hash` is the dedup key — **load-bearing for repair planning**, since it is
   why a producer-side fix recovers nothing already written. If the redesign changes
   *what is hashed*, the dedup store's keys stop matching and the archive's semantics
   change underneath it.
6. **`reference/record.qmd`, entire** — obsoleted wholesale. The largest single
   documentation casualty; count it.

**And one control spent as a side effect:** `source_group` was the phase-0 acceptance
test *because* it was a defect class the check had never seen. A redesign moots it as
thoroughly as declaring it would have. Any surviving check needs a replacement control,
and it must be something equally unseen.

---

## Feasibility — answered by FluxusSource, 2026-08-14

**(a)** already emitted · **(b)** one line to capture · **(c)** real plumbing

| field | | where it already lives |
|---|---|---|
| `published.raw` `.element` `.had_timezone` `.precision` `.fabricated` | **(b)** | All five are **live inside `DateParser` at parse time and discarded**. `normalize_timezone` already branches on `had_timezone`; `ensure_valid_date` already knows when it returned `now−2h`. Threading out, not computing. |
| `language.method` `.confidence` `.sample_chars` | **(a)** | ⚠️ **Already exist** as `language_source`, `language_confidence`, `language_input_len`. **Do NOT rename** — two are inputs the aggregator hands the decision, and #149's floor is fitted on the other two. |
| `language.script` `.scripts_present` | **(b)** | `content_item.py` already runs per-script detection (`_KANA_PRESENCE`) and **reports only the verdict**. |
| `fetch.charset_*` `http_status` `content_encoding` | **(b)** | `RobustFeedParser` holds the response object. Brotli mis-decoding **silently zeroed 461 feeds in July**. |
| `fetch.url_requested` / `url_final` | **(b)/(c)** | A **4-strategy fallback ladder**, so "the URL" is per-attempt. ⭐ **Add the strategy that succeeded as its own field.** |
| `content_meta.kind` | **(b)** | Below. |
| `feed.declared_language` | **(a)** | Already emitted as `feed_declared_language`. |
| `feed.cadence_hours` | **(a)-ish** | `FeedHealthTracker` measures it — into the health report, **not** onto the row. |
| `origin.*` | **(c)** | Below. |

⭐ **`content_meta.kind` — yes, and it COLLAPSES.** FluxusSource **never fetches article
bodies**: `full_text_fetcher.py` was deleted and enrichment moved to NexusMind. So
`full_text` is **not a value this producer can legitimately emit**. `kind` reduces to
`feed_summary` vs `headline_only`, **both decidable at parse time**. **This retires the
300-char floor** — the distinction the threshold proxies for is directly observable.
*Caveat:* `content` is non-empty on **98.0%** of rows, so `headline_only` is small, and
API aggregators differ per source (arXiv abstracts; GDELT a title and a URL).

⚠️ **`origin.*` — the sequencing worry was the wrong SHAPE but the right SIZE.** No
country or timezone exists on a source anywhere. `source_group` is geographic for **64
of 107 shelves covering 932 of 1,872 feeds** — but it is a *shelf*, not a claim about
the publisher. **The unit is not ~30 aggregators — aggregators do not know this. It is
~1,872 per-source YAML entries**, ~932 bulk-seedable from their shelf, the rest needing
judgement. **The cost is editorial, not engineering.** Partial exception:
`metadata.source_country` already rides on GDELT rows.

### H. The one field this proposal MISSED — and it is the rule's clearest instance

```
collected.at            RFC 3339 with offset
collected.clock_source  "host_local" | "utc" | "source"    ← the missing field
```

⭐ **19 of 26 aggregators build `collected_date` from local `datetime.now()`.**
Downstream that is **byte-identical to a UTC value and wrong by the host offset**, and
no consumer can ever recover which it was. The same defect as `published_date`'s, but
on **our own** clock rather than the publisher's — and nobody had noticed.
*(Found by FluxusSource, not by this proposal.)*

---

## Logical grouping — by who knows it, not by type

The current shape is 12 flat fields plus a `metadata` bag holding **143 distinct
keys**. The bag is where everything undeclared accumulates.

**Group by provenance layer**, because that is what actually predicts a field's
reliability, lifetime, and owner:

```
{
  "id", "content_hash",
  "item":         { title, content, tags },      // what was published
  "source":       { name, type, topic_group, tier, credibility },
  "origin":       { country, region, timezone },
  "published":    { instant, raw, element, had_timezone, precision, fabricated },
  "collected":    { at },
  "language":     { code, declared_by_feed, method, confidence, sample_chars },
  "fetch":        { url_requested, url_final, http_status, charset_*, content_encoding },
  "content_meta": { kind, truncated, raw_length, echoes_title },
  "feed":         { title, declared_language, cadence_hours, ttl_declared },
  "payload":      { ... }                        // per-aggregator, open by design
}
```

**`payload` is deliberately open and deliberately walled off.** Of the 143 metadata
keys, **131 appear on under 10% of rows, and 114 of those never occur outside
`source_type: api`** — github rows carry `stars`/`forks`, pubmed carries
`pmid`/`mesh_terms`, arxiv carries `arxiv_id`/`pdf_url`. They are **one block per
aggregator**, not chaos. Enumerating them freezes a list that changes whenever an
aggregator is added; a stale enumeration is worse than an honestly open region. But
they must not sit in the same bag as `quality` and `source_category`, which every
consumer depends on.

---

## Migration — additive, never a flag day

Four repos read this stream and two of them are live. So:

1. **Add the new blocks alongside the old flat fields.** Nothing breaks; nothing has
   to move at once.
2. **Consumers migrate at their own pace.** The old fields keep working.
3. **Mark the old ones deprecated in the schema, with a date.**
4. **Remove them only when no consumer reads them** — checked by grep, not assumed.

⚠️ **The one thing that cannot be phased:** `published.instant` gaining a UTC offset
is a **lexicographic** change — `'…T20:00:00+02:00' > '…T19:00:00'` as a string while
being *earlier* in real time. Any consumer doing string comparison or `ORDER BY` on
that column breaks. ovr.news has ~20 such sites and has already shipped the parser fix
(`60ada82`); **that work must land everywhere before offsets are emitted.**

---

## What this is worth

| defect today | fixed by | currently |
|---|---|---|
| two hops disagree by 2h on article age | `published.instant` + `had_timezone` | live, affects which articles readers see |
| 5.6% of rows carry introduced mojibake | `fetch.charset_*` | live, 6.9× worse for non-English |
| a fabricated date is indistinguishable from a real one | `published.fabricated` | live, reads as maximally fresh |
| "is this an article or a headline?" | `content_meta.kind` | guessed from a 300-char threshold |
| "how much of our corpus is African publishers?" | `origin.country` | unanswerable without parsing config stems |
| a detection on 40 chars looks like one on 4,000 | `language.sample_chars` | invisible |
| a naive date is permanently ambiguous | `origin.timezone` | unrecoverable |

**Every one of these is a fact FluxusSource had at collection time and threw away.**
None is fixable downstream at any price, and none would have been surfaced by
correcting the four values in the existing schema.
