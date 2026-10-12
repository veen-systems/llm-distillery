# Date errors and the 1.3× recency boost — hypotheses

**Opened 2026-08-14 (late).** Arose out of the Contract A redesign
(`docs/decisions/2026-08-14-contract-a-envelope.md`) but is **not part of it**: the
redesign only supplies the instrumentation that would settle it.

---

## The confirmed mechanism

**Measured by the NexusMind session in their own code, 2026-08-14** — not inferred
from config, and not taken on report.

`NexusMind/src/scoring/display_ranking.py`:

- `recency_threshold_hours: 24`
- `recency_boost: 1.3`
- applied as a **flat multiplier** when `age_hours < 24`
- `age_hours` derives from **`published_date`**

**So any row whose `published_date` lands inside 24h takes a 1.3× ranking
multiplier.** Under ADR-023 that is the *expensive* direction: a false positive
reaches a reader, a false negative is invisible.

## ⭐ The claim that holds WITHOUT attribution — build on this one

> **Any date error that lands a row inside 24h wins the 1.3× boost, invisibly and
> permanently.**

Fabrication is one member of that class, and on the producer's data it is **the
confirmed one** (H-D1 below). Timezone misparse was the competing candidate and is
**excluded** for that population.

⚠️ **This framing was written when the causes were unseparated, and it was too
cautious rather than wrong.** Keep the class-level claim — a remedy aimed at one
member still leaves the others — but do not cite "timezone misparse is the larger
spike" from it. That was the 6h reading, and **6h is now RESOLVED as arXiv's daily
04:00 announcement seen one collection period late (H-D2) — not an error at all.**

---

## ⭐⭐ THE INSTRUMENT ARRIVED — `collected.clock_source` and `published.fabricated` are LIVE (2026-08-16)

**Everything below this heading was inference from gap arithmetic. It no longer has to
be.** Contract A shipped 2026-08-15/16 and both fields now ride on delivered rows, so the
two quantities this file spent weeks estimating are read directly.

**FS#176 is now MEASURED, and the partition is exact — four consecutive deliveries:**

| delivery | `host_local` | `utc` | mixed |
|---|---|---|---|
| `…0815_200845` | 95 | 2,945 | **0** |
| `…0816_000647` | 82 | 2,236 | **0** |
| `…0816_040540` | 231 | 2,280 | **0** |
| `…0816_081046` | 231 | 1,831 | **0** |

<!-- verify: bash scripts/verification/check_clock_source_partition.sh -->
⭐ **`host_local` equals the API row count exactly, and `utc` equals rss + social exactly,
in every delivery.** Every API producer is on the host clock (CEST, +2h), every RSS one on
UTC, and there is **not one mixed case in ~9,800 rows**. ⭐ **A clean partition is
falsifiable in a way a percentage is not** — one mixed row refutes it, whereas "about 3.87%
of rows are skewed" survives almost any observation.

⛔⛔ **THE PARTITION ABOVE IS HISTORY, NOT STATE — superseded 2026-08-31, and it is obsolete
BY SUCCESS.** Census over every collection retained on the host (47 collections,
`collection_20260824_040945 .. collection_20260831_200757`, **158,656 rows**):
`api->utc` 5,512 · `rss->utc` 152,774 · `social->utc` 370 — **zero `host_local`, zero
unstamped.** FS#176's migration finished: the 2h host-clock skew is gone from delivered rows.
⭐ **And the stamp is truthful, not a relabelled host clock** — `collected_date` sits within
~6 minutes of each collection's own UTC start on the oldest, middle and newest delivery, where
a host-local clock would read **+120**. ⚠️ **The window cannot date the change**: `data/current`
retains ~8 days and its oldest directory is already fully `utc`, so the flip happened at or
before 2026-08-24 and nothing in this population can say when. ⛔ Do not write a flip date.

⛔ **The guard on the line above has been FAIL-OPEN since it was written** (`943379b`,
2026-08-16), and was swallowing a real violation for **at least the last week** — the window
cannot say longer. Its remote block's
`sys.exit(1)` shared a `||` branch with an unreachable host, so a real violation printed
`MIXED CASES: {...}` and then **`CANNOT VERIFY: remote check did not run`, exit 0** — a
detection presenting as a transport failure, which is the harmless-looking half. Fixed, with
the FAIL branch **proven on a seeded fixture** (exit 1) rather than asserted, and the assertion
replaced by the strictly stronger post-migration invariant (*every row stamped, every stamp
`utc`* — one `host_local` row refutes it). Third instance of this shape after the `| grep` and
`| tail; echo $?` fail-opens of 2026-08-29. Evidence, controls and the census:
`docs/evidence/2026-08-31-clock-source-fail-open/`.

⚠️ **What this does NOT retire:** the gap-arithmetic history below, and the `published.fabricated`
findings, are untouched. What changes is that `clock_source` no longer *separates* anything on a
delivered row — every row says the same thing — so an analysis that planned to condition on it
gets no discrimination from it any more, and must not read a uniform column as a clean control.

⚠️ **This retires the gap heuristic as an ATTRIBUTION instrument, not as history.** Every
`collected − published` figure in this file was measuring a *sum* of a real age, a
possible fabrication and a possible 2h clock skew. `clock_source` now separates the third
term on the row itself, so a future analysis conditions on it instead of inferring it —
and the `2h ± 5s` fingerprint work below is superseded as a method while remaining the
record of how the mechanism was found.

**`published.fabricated` is live too, and its true branch was observed in a delivered run
for the first time on 2026-08-15 20:02: 44 rows across `austrian_vienna_at` (24),
`china_nikkei_asia` (10), `indonesian_mongabay_id` (7), `norwegian_dagbladet` (3)** — each
carrying `raw`/`element`/`had_timezone`/`precision` as **null**, which confirms Contract A
1.24.0's null⟺fabricated clause on live bytes. It had only ever been tested against a
hand-written row.

⚠️ **Per-run, not a rate.** The next delivery carried **0** fabricated rows and the one
after **37**. Which sources are due decides it, exactly as with `echoes_title` — do not
quote any single delivery's count as a corpus property.

⚠️ **A prediction failed here and the failure is the lesson.** FluxusSource predicted the
cheapest live positive would be `french_le_parisien`, due ~16:00. The true branch fired
four hours earlier from **four different sources, none of them le_parisien** — a
population assumed to be one of its members. Same hand-built-population shape this file
already carries twice.

## H-D1 · H-D2 · two superseded framings — RESOLVED, MOVED to [`archive/date-error-recency-boost-hypotheses-archive.md`](archive/date-error-recency-boost-hypotheses-archive.md) (2026-10-12)

- **H-D1 ✅ RESOLVED: the ~2h gap is FABRICATION** (`extract_date_from_rss_entry` emits `now − 2h`), attributed by a
  microsecond fingerprint that the canonical-serialization deploy ERASED from `collection_20260814_193603` on.
  `published.fabricated` replaces it (below).
- **H-D2 ✅ RESOLVED: the 6h spike is arXiv** (93.1% of the bin) — its daily 04:00 announcement seen one collection
  period late. Benign: the dates are right and the boost is earned. ⚠️ The 2h bin has at least THREE contributors and
  only one is fabrication; fabrication + 2h skew makes a 4h gap OUTSIDE the detection window.
- ⛔ **Never cite a whole-hour gap spike as a date defect without the `source` breakdown beside it.**

## ⭐ The replacement signal EXISTS AND IS BUILT — `published.fabricated`, 2026-08-15

H-D1's whole difficulty was that fabrication had to be *inferred* from a ~2h gap that at
least three other mechanisms also produce, and the microsecond fingerprint that once
attributed it **was erased in production** by the canonicalization deploy. **That is now
over: the producer states it on the row.** FluxusSource built Track A on 2026-08-15
(working tree, uncommitted, **not deployed** — the deploy is an owner decision).

**Presence counts on real rows** (live 45-feed sample + live academic APIs):

| population | `published` block | `raw` | `had_timezone` | `fabricated` | `fabricated=true` |
|---|---|---|---|---|---|
| RSS, 687 rows (`extract_date_from_rss_entry`) | 687/687 | 687/687 | 687/687 | 687/687 | **25/687 = 3.64%** |
| API, 101 rows (`ensure_valid_date`) | 101/101 | 76/101 | 76/101 | 101/101 | **1/101 = 0.99%** |

⚠️ **`raw`/`had_timezone` at 75.25% on the API side is DELIBERATE, not a gap.** PubMed's
date is **real but assembled** from separate `<Year>/<Month>/<Day>` elements, so no
publisher string exists to quote. Producer rule: **`null` ⟺ `fabricated`; an unrecorded
observation is OMITTED.** Nulling `raw` there would have put the fabricated spelling on a
non-fabricated row.

### A named live fabricator: `baltic_baltic_times`, 25/25

**Every `fabricated=true` row in the RSS sample came from one feed.** It is enabled, live,
and serves **nothing parseable in any of the 9 date elements**, so every row it emits is
`now − 2h` — previously indistinguishable from the three other ~2h mechanisms above, now
stated on the row. ⚠️ **The estate-wide fabricating population is NOT counted** — that
needs a production run, which is the deploy decision.

### ⚠️ The capture trap, and it is the MIRROR of the one that was warned about

The brief warned that capturing `had_timezone` too far out reads **FALSE on 100%** (by
`extract_date_from_rss_entry:110` the value is already naive). **The failure actually hit
reads TRUE on 100%**, and the first implementation did exactly that: **dateutil calls a
*callable* `tzinfos` even for a timezone-less string, with `(None, None)`**, and
`DateParser._get_tzinfos`'s inner `tzinfos()` ends with `return pytz.UTC` — verified here
at `src/utils/date_parser.py:296-312` — so **`parsed.tzinfo is not None` is True for every
dateutil-parsed string.**

⭐ **What makes this one nasty, and it is the transferable lesson: the true rate is very
high** (RFC 822 and RFC 3339 strings essentially always carry a zone), **so the broken
implementation and the correct one produce nearly the same headline number.** Only a
differently-derived check separates them — here, re-deriving the answer by regex over the
raw text: **0 disagreements over 737 non-fabricated raws, plus 12 hand-labelled cases of
which the broken reading gets 6 wrong.** Correct capture is **inside the tzinfos
callback**: `had_timezone = (abbrev is not None or offset is not None)`.

⚠️ **CORRECTED the same day, by the producer, and the correction is the sharper half.**
The rate was first written as **"expect ~100%"** off 662/662 and 737/737 — **those samples
simply contained no negatives, and the absolute was generalised from their absence.** An
independent second sample (25 random enabled non-GN feeds, 288 dated entries) reads
**280 true / 8 false = 97.2%**, and the API half is lower still: `semantic_scholar`'s
`publicationDate` and PatentsView's `patent_date` are bare `YYYY-MM-DD` ⇒ false.

⭐ **So the lesson is TWO-SIDED, and only the first side was filed initially:**
1. A broken instrument and a correct one can produce the same headline number — **only a
   differently-derived check separates them.**
2. **A sample with no negatives cannot license an absolute** — and **the check that
   catches the instrument is NOT the check that bounds the rate.** The regex cross-check
   was correctly differently-derived and *could not* have caught this: it validated
   agreement on the rows that were there, not the **representativeness of the rows
   chosen.** Same failure family as this project's hand-built-population rule, arriving
   through the back door of a *verification* rather than a measurement.

### ⛔ A FIFTH FABRICATION CLASS, AT ~0h — OUTSIDE THE 2h/4h TAXONOMY ENTIRELY

**Found 2026-08-15 by FluxusSource's own review battery. This is the most important
addition on this page**, because every detector discussed above is tuned to a *gap*.

    devto_api_aggregator.py:140
    fda_api_aggregator.py:133, :310
    clinicaltrials_gov_aggregator.py:147

All shaped `published_date = parse_date_string(...)` then
`if not published_date: published_date = datetime.now()`. **Not `now − 2h` — a ~0h gap**,
and on the **host local clock** (FS#176), so it is not even measured against the same
clock as everything else.

- ⭐ **A gap detector tuned to 2h/4h cannot see this class at all.** This is not a wrong
  constant — **the signal is at zero.** It strengthens rather than weakens the
  "inference cannot substitute" argument.
- ⚠️ **These sources emit no `published` block, so `fabricated` is UNDEFINED for them, not
  false.** 555 rows in the 7-day hot window (devto 69, clinicaltrials 486).
- **Latent, not observed:** 0 rows currently at `|collected − published| < 120s`, so the
  fallback exists and has not fired in this window.
- **Instrumenting them is NOT done** — beyond Track A, a different mechanism, wants its
  own decision.

### ⛔ A THIRD SUBSTITUTION SITE, which the `published` block itself does not account for

**`date_normalized`.** When a publisher date is **>1 day in the future**, `to_dict` emits
**`collected_date` AS `published_date`** and moves the parsed value to
`original_published_date`. `published.raw` describes **that** field.

⭐ **So on those rows `fabricated: false` means "the publisher gave us a date", NOT
"`published_date` is what the publisher said"** — which is exactly the reading the block's
headline invites. **329 such rows in the 7-day window**, 6 RSS and instrumented today; the
other 323 are the advance-publication-date class (crossref / openalex / clinicaltrials /
owid), **not instrumented yet — so the intersection GROWS with coverage.** Documented and
pinned by a test on the producer side.

### Smaller, but real — carry these caveats

- ⚠️ **Pre-existing FluxusSource bug, found in passing, NOT filed and not theirs:** `CEST`
  maps through `DateParser.TIMEZONE_MAP` to an **LMT** offset, so
  `'... 09:15:00 CEST'` parses to **09:06**. ⭐ **A wrongly-converted `published_date` can
  therefore ride a perfectly correct `had_timezone: true`.** Worth an issue.
- ⚠️ **The patent arm has NO production data behind it.** `patentsview` and `epo_ops`
  produced **0 rows** in the 7-day window, so *"every EPO row is fabricated"* is proven by
  test only. Carry this caveat if the EPO line is ever filed.
- **`fabricated` is stamped at THREE producer sites, not two** — the EPO paths call
  `fabricated_provenance()` directly and unconditionally.
- **Storage, measured not estimated:** ~20 ms per run (0.006% of a 324.7 s run), but rows
  grow **~95 bytes (+6%)** because `raw` echoes the publisher's date string —
  **~1.5 MB/day against archives kept indefinitely since #164.** ⚠️ **A storage commitment
  nobody has agreed to yet**, and it is in the producer's deploy note rather than assumed.

### ⚠️ Do not cite "99.22% of production rows carry no offset" for this field

It is in NexusMind's `had_timezone` description in Contract A 1.22.0 and **it is about the
wrong field.** That figure describes **our emitted `published_date`, which we strip**;
**publisher INPUT is ~100% timezone-bearing.** Anyone reading the declaration will expect
~1%, see ~100%, and conclude the producer is broken. A reword is with NexusMind.

---

## Related, and deliberately separate

- **The canonical-serialization defect** — FluxusSource emits four spellings of
  `published_date` (2.805% non-canonical, largest class *microseconds with no offset*,
  207 sources). A **text-shape** problem affecting sorts and `DELETE`s, not a
  wrong-instant problem, so it is a different defect with a different fix site.
  ⚠️ **But it is NOT independent of H-D1**: it was **deployed 2026-08-14 19:20 (first
  clean run `collection_20260814_193603`) and it erased H-D1's microsecond
  fingerprint.** Two correct, unrelated changes, one of which
  silently destroyed the other's evidence — which is the argument for explicit fields
  over accidental signals. See `docs/CONTRACTS_PLAN-rounds-archive.md` § *Round 3*.
- **The two-hop 2h disagreement** (NexusMind reads naive as UTC, ovr's JavaScript reads
  it as local) is a **consumer** bug with a one-line fix on ovr's side. It is *not*
  H-D1b, though the two share a vocabulary and were conflated for most of 2026-08-14.

## Verify commands

```bash
# The mechanism (NexusMind checkout)
grep -n "recency_threshold_hours\|recency_boost" src/scoring/display_ranking.py

# The gap distribution — re-derive before quoting; the numbers above are one
# 7,478-row live sample and this is a rate, so it needs its population stated.
# The discriminating version adds a GROUP BY source.
```

⚠️ **Every figure here belongs to one corpus.** Three RSS shares, three GN ratios and
one tie count all needed correcting on 2026-08-14 for exactly this reason. **The
denominator travels with the number, or the number does not travel.**
