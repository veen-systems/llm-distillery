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

`src/models/content_item.py` on sadalsuud has mtime **19:20:42**, and sadalsuud is on
`6455c06` (contains `94e7337`). So the **16:02 and 16:14 runs still carry the
fingerprint** — this file previously told you they did not. Anything collected up to
and including `collection_20260814_161408` is quotable evidence.

⭐ **The fix itself is not an orphan and never was.** One site, `ContentItem._canonical_timestamp`
→ `utils/time_utils.canonical_timestamp`, exactly the single fix site predicted;
follow-up **FS#174** (tighten `output_schema.json`'s pattern) deliberately held until
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
(`content_items_20260814_121003.jsonl` + `…_160810.jsonl`). Not a 7-day window, not a
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

⚠️⚠️ **But the collision is latent, not absent.** `+1.98h` and the fabrication
signature's `2h` are **the same number to within 72 seconds**. The only thing
separating them is that NewsAPI happens to return ~28h-old articles — *a property of
the upstream API's result set, not of our code*. Any NewsAPI query returning fresh
items puts a whole slice at ~1.98h, indistinguishable from fabrication. **Same shape
as the arXiv trap, different mechanism, and it would arrive without any change on our
side.**

⭐ **And canonicalization made it invisible.** Before `94e7337` that `collected_date`
carried microseconds and looked visibly odd; now it has the **identical shape** to a
correct UTC value, so only cross-source comparison *inside a single run* exposes it.
That is the third time in one day that removing an incidental signal cost the only
available discriminator — which is the argument for `collected.clock_source` as an
explicit field, on the same grounds as `published.fabricated`.

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
