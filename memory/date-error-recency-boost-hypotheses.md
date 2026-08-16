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

## H-D1 — ✅ RESOLVED: it is FABRICATION, attributed by a fingerprint that no longer exists

**FluxusSource, 2026-08-14 late, 152,422 rows.** Resolved on the producer's own bytes
in the hour after this file was opened — and the discriminating evidence was **erased
by a deploy twenty minutes later**, so read the expiry note before quoting it.

### The fingerprint

`extract_date_from_rss_entry:106` fabricates with
`_utc_now_naive() - timedelta(hours=2)`. ⭐ **That retains MICROSECONDS. A date parsed
from a publisher's feed almost never does** — publishers emit second precision.

| | `published_date` HAS microseconds | has none |
|---|---|---|
| **gap ≈ 2h (±5s)** | **1,717** | 23 |
| everything else | 1,618 | 149,064 |

**Of rows at a ~2h gap, 98.7% carry microseconds.** ⭐ **A timezone misparse cannot
produce microseconds** — it shifts a publisher-supplied value that never had them.
Our own clock is the only thing in the system that writes sub-second precision into
`published_date`. **So H-D1a (fabrication) is confirmed and H-D1b (timezone misparse)
is excluded** for this population.

**Source concentration agrees**, exactly as H-D1a predicted: 77% of the 2h spike is
six date-less feeds — `french_le_parisien` (700), `south_asian_kathmandu_post` (171),
`china_nikkei_asia` (170), `austrian_vol_at` (124), `austrian_vienna_at` (116),
`baltic_baltic_times` (110).

**Useful contrast:** the 11h spike is 84% `science_arxiv_cs` — a genuine
publication-lag pattern, not an error. That is what a *real* gap looks like.

### ⚠️⚠️ THE FINGERPRINT IS GONE FROM THE `collection_20260814_193603` RUN ONWARD

FluxusSource deployed **timestamp canonicalization** to production, which strips
sub-second precision from every emitted timestamp. **Microseconds no longer
distinguish a fabricated date from a parsed one.**

⚠️ **The boundary is a RUN, not a wall-clock hour — and the hour first written here
was wrong by ~2.5h.** Measured on sadalsuud 2026-08-14 20:03 (llm-distillery
session), not taken on report:

| | `collected_date` spelling |
|---|---|
| `collection_20260814_161408` (pre) | **143 / 143 microseconds** |
| `collection_20260814_193603` (post) | **2,891 / 2,891 canonical**, both date fields |

FluxusSource's `src/models/content_item.py` on sadalsuud has mtime **19:20:42**, and sadalsuud is on
`6455c06` (contains `94e7337`). So the **16:02 and 16:14 runs still carry the
fingerprint** — this file previously told you they did not. Anything collected up to
and including `collection_20260814_161408` is quotable evidence.

⭐ **The fix itself is not an orphan and never was.** One site, `ContentItem._canonical_timestamp`
→ `utils/time_utils.canonical_timestamp`, exactly the single fix site predicted;
follow-up **FS#174** (tighten FluxusSource's `output_schema.json` pattern) deliberately held until
~2026-08-21 so the 7-day hot window can roll before the validator would start failing
every run.

1. **The ~2h gap signature survives** — both fields truncate to whole seconds, so a
   fabricated row still sits at 2h ± 1s. Microseconds were the *confirmation*, not the
   primary signal.
2. **The archive keeps the evidence.** `data/archived/` is retained indefinitely
   (FS#164), so every pre-deploy row still carries the fingerprint and the attribution
   above is reproducible against it **forever**. Quote it against the archive, never
   against current rows.
3. ⭐ **It was an ACCIDENTAL signal — undocumented, unowned, and it vanished the moment
   someone touched serialization for an unrelated reason.** That is the argument for
   shipping `published.fabricated` as an **explicit** field promptly, not an argument
   against the canonicalization.

⭐ **This changes WHY the three fields ship together.** They are no longer needed to
*separate* the two causes — the fingerprint did that. They are needed because **the
fingerprint is now gone from new rows and `published.fabricated` is what replaces it,
permanently and on purpose.**

## H-D2 — ✅ RESOLVED: the 6h spike is arXiv, and it WALKS WITH THE COLLECTION TIMER

**Measured 2026-08-14 ~20:10 by the llm-distillery session, on sadalsuud
`NexusMind/data/raw/`.** Both candidates below were right, and the mechanism is
neither fabrication nor timezone misparse.

### The population, recovered exactly — and the original numbers reproduce digit for digit

**7,478 = 3,835 + 3,643** — the two most recent NexusMind raw deliveries
(`content_items_20260814_121003.jsonl` <!-- placeholder --> + `…_160810.jsonl`). Not a 7-day window, not a
sample: **two files**. That alone is why FluxusSource's 152,422-row / 47-run window did
not contain it.

Re-run on exactly those two files: **6.0 → 1,046 / 13.99%, 10.0 → 237 / 3.17%, 2.0 →
236 / 3.16%** — identical to the table in *Superseded* below. **Same instrument, same
bytes**, so nothing here rests on a re-derivation that might differ from theirs.

### The attribution

**974 of the 1,046 rows in the 6.0 bin (93.1%) are arXiv feeds** —
`science_arxiv_cs` 526/526, `ai_arxiv_cs_ai` 261/261, `science_arxiv_eess` 67/67,
`ai_arxiv_stat_ml` 47/47, plus four smaller arXiv categories, **every one of them 100%
of that source's rows in the file**. And **983 carry the same `published_date`:
`2026-08-14T04:00`** — arXiv's daily announcement moment. They were collected
10:04–10:07.

### ⭐ The mechanism, and why the two windows disagreed

arXiv publishes **once a day at a fixed instant**. The gap is therefore just *"how long
ago was 04:00 when this run collected"* — so it **increments by one timer period per
delivery**:

| delivery | arXiv rows | gap p50 | published hour |
|---|---|---|---|
| 08-13 20:07 | 14 | 14.08h | 08-13T04 |
| 08-14 00:06 | 0 | — | — |
| 08-14 04:10 | 0 | — | — |
| 08-14 08:07 | 17 | **2.06h** | 08-14T04 |
| 08-14 12:10 | **989** | **6.12h** | 08-14T04 |
| 08-14 16:08 | 136 | 10.10h | 08-14T04 |

**+4h per delivery, exactly the `fluxus-collection` period.** FluxusSource's own
"11h spike is 84% `science_arxiv_cs`" is this same batch read at their run cadence —
the two sides were describing one phenomenon at two phases, not two phenomena.

### ⚠️⚠️ THE TRAP — this artifact passes through 2h once a day

Read the 08:07 delivery instead of the 12:10 one and arXiv sits at **2.06h**: the
fabrication signature's own bin. **`collected_date − published_date` is NOT a usable
instrument for detecting fabrication without conditioning on `source`** — a
fixed-publication-moment source will impersonate the `now − 2h` fallback for one
delivery in every daily cycle.

⭐⭐ **H-D1 survives — but NOT by a margin, and "margin" was the wrong frame.**
*(Corrected 2026-08-14 ~20:30 by the FluxusSource session, who reproduced the
mechanism on their own corpus rather than adopting these numbers. Their sharpening is
the load-bearing half.)*

H-D1's window was **2h ± 5s** and arXiv fell outside it — by **216s** in the NexusMind
delivery measured here, by **452s** in FluxusSource's own run. ⚠️ **Those two numbers
disagreeing is itself the finding**: the separation is not a property of arXiv or of
the fabrication, so it cannot be relied on.

**It is intra-run latency, and the coincidence is scheduled, not hypothetical:**

- arXiv announces at **04:00 UTC**
- the collection timer fires at **06:00 UTC** (08:00 Europe/Amsterdam, FS#132) — a
  real tick on the schedule, one of six a day
- **06:00 − 04:00 is exactly 2h.** The 755 rows in their run sat at 2h + 452s *only
  because the run reached the arXiv aggregator at 06:07:32*

So the sole thing holding an entire announcement batch out of the fabrication window
is **how long a run takes to reach that one aggregator** — no invariant guarantees it,
and any concurrency or source-ordering change moves it freely. I first wrote this as
"a run beginning near 06:00 UTC *would* contaminate it"; the conditional was wrong.
**That run is on the timer.**

⭐ **Hence the conclusion in its correct form, which is stronger than the margin
version:** `published.fabricated` must be stamped **at the point of fabrication**,
because **no downstream rule can separate a fabricated date from a real one that is
genuinely 2h old.** The microsecond fingerprint was never a margin either — it was a
different kind of evidence, and it is gone (see above).

### ⭐ THE 2h BIN HAS AT LEAST THREE CONTRIBUTORS, AND ONLY ONE IS FABRICATION

*(Found 2026-08-14 ~20:45, prompted by the FluxusSource session; measured here on
`collection_20260814_193603`, 2,891 rows, by per-source median offset — a different
construction from theirs, so the two are independent.)*

| mechanism | how it manufactures ~2h | status |
|---|---|---|
| **fabrication** | `extract_date_from_rss_entry:106` writes `now − 2h` | the real defect (FS#173) |
| **fixed-announcement source** | arXiv publishes 04:00 UTC, the timer ticks 06:00 UTC | benign; H-D2 above |
| **local-clock `collected_date`** | `newsapi_general` stamps the **local** clock, **+1.98h** ahead of UTC | benign *today*, latent |

The third is the new one. Exactly **88 / 2,891 = 3.04%** of that run — one source,
`newsapi_general`, at **+1.98h** against the run median (`2026-08-14T17:31:55`), every
other source within ±0.03h. **Consistent with `CLAUDE.md`'s standing clock finding**
(3.87% of rows at +1.98h across 14 families, `newsapi_general` the largest).

⚠️ **It does NOT contaminate FS#173 today, and I checked rather than assumed:**
**0 of the 88** skewed rows fall in `2h ± 5s`. They sit at **28.5–30.5h**, because
NewsAPI returns day-old articles. The clean population had **1**.

### ❌ RETRACTED: my "latent false-positive collision" — and the truth is a FALSE NEGATIVE that is ACTIVE

*(Corrected 2026-08-14 ~21:00 by the FluxusSource session; **both halves re-verified
here on their evidence, not adopted.** Recorded in FS#173.)*

**What I claimed and why it was wrong, in two parts:**

1. ⚠️ **The `+1.98h` was an artifact of my own construction.** I compared each source's
   median `collected_date` to the **run** median. NewsAPI **runs first in the cycle**,
   so I measured *the clock offset minus its head start*. Verified: NewsAPI's earliest
   `collected_date` is `19:30:54` local = **17:30:54 UTC**, while the earliest of every
   other source is `17:30:56`. The true offset is **exactly 2h** (CEST = UTC+2). My run
   median was `17:31:55`, 61s later → `2h − 61s = 1.983h`. **The 72-second "gap to
   fabrication" was my denominator, not the data.**
2. ⚠️ **False positives were never the risk.** For a skewed producer the emitted gap is
   `true_age + 2h`, so a *real* article reaches `2h ± 5s` **only if it is under 5
   seconds old**. Fresh items land just *above* 2h by exactly their age — a 10-minute-old
   article sits at 2.17h, already 600s clear. My "any NewsAPI query returning fresh
   items drops a slice at ~1.98h" is false as arithmetic.

### ⭐ The real interaction: fabrication + skew = a 4h gap, OUTSIDE the detection window

`DateParser.ensure_valid_date` (`date_parser.py:217`) is a **second fabrication site**,
called from the `news_api`, `github`, `academic` and `patent` aggregators — **several
of which are exactly the clock-skewed ones**. For those producers:

```
published = UTC_now − 2h    (fabricated, UTC)
collected = UTC_now + 2h    (local clock)
gap       = 4h              ← two hours OUTSIDE FS#173's 2h ± 5s window
```

**Verified independently here, hot window, 155,513 rows: 46 rows at `4h ± 5s`, 32 of
them `semantic_scholar`** (skewed `+2.00h`, `academic_api_aggregator.py:684,830,1023`,
and an `ensure_valid_date` caller). Those runs predate `94e7337`, so the microsecond
fingerprint still adjudicates — and it is unambiguous: **32/32 carry microseconds on
`published_date`**, with published and collected sharing them to ~35µs:

```
published=2026-08-09T12:04:32.536201
collected=2026-08-09T16:04:32.536236
```

**One instant, stamped from two clocks.** ⭐ The fingerprint also *discriminates within*
the 46: exactly the 32 `semantic_scholar` rows carry microseconds; the other 14
(`el_comercio_pe`, `gn_bangladesh`, `sueddeutsche`, …) do not and are genuine 4h-old
articles.

⇒ **FS#173's table UNDERCOUNTS fabrication.** 8 of 768 sources carry the skew
(`newsapi_general`, `github`, `hackernews`, `stackoverflow`, `ourworldindata`, NASA
APOD, two Dev.to author-named sources).

### ⭐ What this does to the conclusion — it strengthens it on different grounds

**A detector keyed on a fixed gap is keyed on the PRODUCER'S CLOCK.** It needs a
different constant per aggregator, **and another after every DST transition** — these
rows sit at 4h in CEST and would sit at 3h in CET. That is a stronger argument for
stamping at the point of fabrication than either side had.

⚠️ **So the clock defect is a correctness bug in its own right, not
discriminator-hygiene** — which is *not* the reasoning I used when I suggested moving
`collected.clock_source` up the (b) sequence. **That suggestion is withdrawn as
argued**; the field is still justified, on this ground instead, and the sequencing is
FluxusSource's call. Canonicalization did remove the incidental oddness of the skewed
value (it now has the identical *shape* to a correct UTC one), but that is a reason to
stamp the clock explicitly, not evidence of a 2h collision.

### Also: "6.00h" was never a whole-hour spike

Quarter-hour binning did that. Actual gaps in the bin: **min 5.8752, p50 6.1220, max
6.1243**, and only **5 of 1,006** rows sit within ±72s of 6.00h. A round number in a
binned histogram is a property of the bins.

### Consequences

- **Benign.** These dates are correct, the lag is real, and the 1.3× boost they take
  under 24h is earned. Nothing to fix.
- The conjecture *"6h = the producer's 2h + one timer period"* is **REFUTED**. It has
  the right arithmetic and the wrong referent: the +4h is real, but it is added to
  arXiv's 04:00, not to a fabricated `now − 2h`.
- **Do not cite a whole-hour gap spike as evidence of a date defect** without the
  source breakdown beside it.

---

## Superseded framing of H-D2 — the 6h spike is not in the producer's data at all

⚠️ **FluxusSource cannot reproduce NexusMind's 6h spike.** Whole-hour gaps on their
152,422-row window: **2h → 1,805 (1.18%)**, 0h → 341, 11h → 214, 4h → 107. **There is
no 6h spike — not smaller, absent.**

So NexusMind's **6.00h / 13.99% on 7,478 rows** is measuring something the producer's
window does not contain. Candidates, neither checked:

- the 7,478-row sample is a different population;
- the gap computed there is not `collected_date − published_date` on producer bytes.

⚠️ Their collection interval is 4h, which would make **6h = the producer's 2h + one
timer period** — suggestive, not established.

⚠️ **Do not let either number displace the other.** Two windows, two corpora; each
side is reporting what its own data contains, not what the other's does not.

---

## Superseded — the original framing, kept because it was wrong in an instructive way

Gaps between `collected_date` and `published_date`, **7,478 live rows**
(sadalsuud, 2026-08-14), quarter-hour bins:

| gap | rows | share |
|---|---|---|
| **6.00h** | 1,046 | **13.99%** |
| 10.00h | 237 | 3.17% |
| 2.00h | 236 | 3.16% |

⚠️ **The dominant whole-hour spike is at 6h, not 2h** — so it is **not** dominated by
the `now − 2h` fabrication fallback, which is what everyone assumed.

Two candidates, equally consistent with the aggregate:

| hypothesis | what it predicts |
|---|---|
| **H-D1a — fabrication** (`extract_date_from_rss_entry:106` invents `now − 2h`) | the spike concentrates in **date-less feeds** |
| **H-D1b — timezone misparse** (naive local time read as UTC) | the spike concentrates **by publisher offset** |

⚠️ **NM#354 records *"each naive instant IS UTC"* as explicitly UNMEASURED**, so H-D1b
has never been excluded.

### The discriminating measurement — ✅ RUN 2026-08-14 ~20:10, see H-D2 above

**Condition the gap distribution on `source`.** It was the right instrument and it
answered in one query: the 6h bin is **93.1% arXiv**, and neither H-D1a nor H-D1b is
the cause. Cost: four `ssh` reads. ⭐ **It had been deferred as delicate, and the
delicacy was in the write-up, not the measurement** — the caution that made both
sessions hold was about *attributing* a number, and the fix for that is to condition
it, not to leave it unmeasured.

⚠️ **Do not attribute a whole-hour gap spike to fabrication in any document.** The
source breakdown must travel with it, because a fixed-publication-moment source
imitates the fabrication signature once per daily cycle.

### What would settle it, once the producer emits

`published.fabricated`, `published.had_timezone` and `published.raw` — **all three
declared on `main` today (Contract A 1.20.0) and populated by nothing.** They are
exactly what separates the two causes:

- `fabricated` alone says *"we invented this date"* — but a fabricated flag on a row
  whose real problem was a misparsed offset tells the wrong story.
- `had_timezone` separates *"the publisher stated UTC"* from *"the publisher stated
  nothing and we assumed"*.
- `raw` is the publisher's literal string and makes both auditable.

⭐ **Hence the sequencing rule for the producer: build those three TOGETHER, not
`fabricated` first.** `fabricated` cannot be interpreted without the other two.

---

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
  over accidental signals. See `docs/CONTRACTS_PLAN.md` § *Round 3*.
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
