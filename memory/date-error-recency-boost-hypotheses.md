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
spike" from it. That was the 6h reading, and 6h is now H-D2: **unreproducible on
producer bytes.**

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

### ⚠️⚠️ THE FINGERPRINT IS GONE FROM ROWS COLLECTED AFTER 2026-08-14 ~17:00

FluxusSource deployed **timestamp canonicalization** to production, which strips
sub-second precision from every emitted timestamp. **Microseconds no longer
distinguish a fabricated date from a parsed one.**

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

## ⏳ H-D2 — OPEN: the 6h spike is not in the producer's data at all

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

### The discriminating measurement, not yet run

**Condition the gap distribution on `source`.** The two hypotheses are cleanly
separable and nobody has separated them. Neither the NexusMind nor the llm-distillery
session would call it, deliberately — after a day in which every confident sentence
beside a sound number needed correcting.

⚠️ **Do not attribute the 6h spike to fabrication in any document until this is run.**

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
  ⚠️ **But it is NOT independent of H-D1**: it was **deployed 2026-08-14 ~17:00 and it
  erased H-D1's microsecond fingerprint.** Two correct, unrelated changes, one of which
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
