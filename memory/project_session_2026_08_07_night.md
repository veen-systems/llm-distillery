---
name: project_session_2026_08_07_night
description: The dedup winner question answered by reading the call path instead of waiting a month; FS#120's eval found running on contaminated data 7 days from its gate; 13 stale cross-repo dependencies, two of them mine
metadata:
  type: project
---

# 2026-08-07 (night) — answered by mechanism, not by waiting

Fourth context on 2026-08-07. The session opened on a measurement that was
supposed to need a month of accumulation, and closed on a deadline item that
turned out to be measuring the wrong thing.

## The headline: the question did not need the wait

The previous session left a first command: read the cross-source dedup count off
the aggregator log, and treat it as a floor until ~2026-09-06 while 36,577
legacy source-less hash entries age out. The question was *"is Google News
consistently on the winning side, or is it arbitrary?"*

**The count is not readable and will not be for weeks** — one run has carried the
stamp (20:06), producing 2 drops; the timer is `OnCalendar=*-*-* 00/4:00:00`,
6 runs/day. A trap worth recording: `grep -r "Dedup cross-source drop:" logs/`
returns **4** lines, which is the *same 2 drops* written to both `aggregator.log`
and `scheduled_20260807.log`. Four is not an event count.

**But the question was answerable by reading the call path, and the answer is
ARBITRARY.** `_deduplicate_by_hash` keeps the first item it meets in `all_items`
and has no publisher preference. `all_items` is reduced in `enabled_sources`
order — deterministic, and the code comment says so — **but that cannot explain
the observed drops, because both happened inside a single source.** The ten
top-level sources are `concurrent_rss`, `bluesky`, `mastodon`, `devto`, `github`,
`gdelt`, `gdelt_constructive`, `news`, `gnews_eval`, `newsdata_eval`;
`gn_asia_gn_yemen` and `us_news_cnn` are **feeds inside `concurrent_rss`**
(6,177 of 6,650 items). Inside that aggregator, futures are harvested by
`concurrent.futures.as_completed()` and folded in with `all_items.extend(items)`
— so the winner is **whichever HTTP fetch returned first that night**, and the
next run may reverse it. This is [[score-batch-shape-noise]]'s family: a
reproducibility defect, not a structural bias.

**The tempting wrong reading:** both survivors were `gn_*` feeds. That is a
base-rate effect — GN contributes hundreds of feeds — not precedence. n=2.

*Method note worth keeping: the generalisable move was asking what ORDERS the
list, not what the dedup function does. The function was never the variable.*

## FS#120 is 7 days out and its eval is partly measuring noise

Went looking at the only calendar-bound item on the board (due ~2026-08-14) and
found two defects in the data it will be read from.

- **`newsdata_eval` is 77–97% off-topic.** On-topic share over 8 runs: Chad
  **23.1%** (15/65), Burundi **4.2%** (1/24), Madagascar **2.9%** (1/34). The
  20:06 Chad batch is entirely Somalia, Angola, South African mining, cricket and
  Pakistan. **This is the same defect already caught and fixed for GNews on
  2026-08-05** — `td: Chad` returning Chad Johnson and Chad le Clos — fixed there
  by adding `country_queries` with unambiguous exonyms. `newsdata_eval` has no
  such mapping. H3 and €/usable-article for NewsData are measuring a pan-African
  default feed.
  **Three caveats from the fact-check lens — the headline survives, the
  denominator is not what it looks like.** (i) Those denominators are **post-dedup
  persisted rows**, not API returns: the logs show `✓ newsdata_eval: 30 items` on
  all 8 runs = **240 fetched, 123 persisted**, so dedup removed 49% first — and
  off-topic syndicated wire copy is exactly what dedup removes. This is the
  on-topic rate *among survivors*. Measure at the API boundary before quoting a
  number to a vendor. (ii) All 15 Chad hits are French `Tchad`, matched only
  because `"chad"` is a substring of it — a word-boundary regex on the English
  name would have read as catastrophic. Right answer, fragile method.
  (iii) Burundi's `1/24` rests on **Gitega** being in the term list; with
  Bujumbura alone it is 0/24, and at n=24 those are the same number.
- **`items/day` is censored.** Every eval identity is capped per run
  (`max_articles: 10` × 3 countries = 30; GDELT `max_records` 30–50, hardcoded).
  `gnews_eval` sat at exactly 30 in **13 of 44 runs**, and returned only 10 in
  **21 of 44** — two of three countries yielding nothing. 30 is the ceiling by
  arithmetic (3 × `max_articles: 10`), not an empirical finding. The 55 GN country
  proxies are RSS with no equivalent cap, so the readout compares tier ceilings
  against editorial supply.

## The error I made, and how it was caught

I posted **"61 of 84 GDELT attempts = 72.6% zero-yield, 2026-08-01…08-07"** to
FS#120. It was wrong in two ways at once: the window **straddles FS#125**, closed
COMPLETED on 2026-08-06 06:15 with a strategy-rotation fix, so most of the sample
is pre-fix; and it pooled `gdelt` with `gdelt_constructive`, whose identical fix
was **deferred as FS#132**. Corrected per source:

| source | pre-fix (08-01…08-05) | post-fix (08-07) |
|---|---|---|
| `gdelt` (FS#125 applied) | 23/30 = **76%** | 4/6 = **66%** |
| `gdelt_constructive` (deferred) | 20/30 = 66% | 4/6 = 66% |

So the fix is real but partial, and FS#125 was closed on a 3-tick post-deploy
sample. Correction posted.

**How I found it: by accident**, while fixing an unrelated stale board entry that
listed FS#125 as open. Nothing in my method would have caught it. This is the
"establish what a source excludes" rule with **time** as the exclusion — a fix
inside the measurement window silently averages two different systems.

Two further defects in the same numbers, found by an independent re-derivation
(the fact-check lens re-derived all 13 claims; 11 reproduced exactly):

- **I double-counted the very trap I had just documented.** `gnews_eval` sat at
  30 in **13 of 44 runs**, not "26 of 59" — the 26 is the double-counted 13,
  and 59 reconciles with nothing at all. I wrote the warning about
  `aggregator.log` + `scheduled_*.log` double-writing **in the same comment**
  where I made the error. Knowing a trap and applying it are different acts.
- **The 429-per-day series is scheduler-scoped**, so Aug 4's real total is **87**,
  not 56 (manual runs at 18:xx/19:xx are absent from the per-day file). The
  apparent downward trend is therefore partly an artifact of which runs the
  source captures, not purely the fix landing.
- Presentational: my pre/post windows silently omitted **Aug 6**, the day of the
  fix. Its values (5/6 and 5/6) are consistent, so nothing changes — but a
  contiguous log presented as two windows with a hole invites the reader to
  assume the hole was inconvenient.

**The rule that would have caught all three: any count over `logs/` must dedupe
by timestamp before reporting, and must state which runs its source captures.**

## 13 stale cross-repo dependencies — two of them mine, filed the same day

An audit of every cross-repo dependency assertion found **13 live instances of an
OPEN issue citing a CLOSED dependency**, which makes the citing issue read as
unblocked. `FluxusSource#85` alone has **five** dependents (NM#223, ovr#222,
ovr#223, ovr#231, ovr#232), of which three had no correcting comment.

**FS#133 and FS#134 both cite NM#213 as the live downstream consumer. NM#213 has
been CLOSED since 2026-05-23.** I filed both, the previous session, in the same
pass that documented this exact trap. Knowing the failure mode did not prevent
it — the same lesson as `cultural_discovery v6`. Corrections filed on all of
them; the board, `docs/TODO.md`, the gotcha log and
[[corroboration-feature-hypotheses]] all now point at NM#188/NM#301.

Also corrected on the board: NM#220, NM#91 (closed *and* mis-described — it is
"Pipeline-run summary notification", nothing to do with healthcheck drift),
LD#43, LD#49, FS#125, FS#126. And a count error — **198 open, not 195**: the
coverage pass never re-counted after filing FS#133 and FS#134, so the two issues
it says are covered are missing from the total it cites.

## Board maintenance done

NM#225 → **Chain 15, re-dated 2026-05-28**: the chain is **71 days old, not 2**,
and NM#225 is its root and the most actionable of the three derivations — it
names audit *targets* (tier assignment mixing filters, `toCanonicalLens`,
"primary topic" logic) rather than one instance. NM#226 → Chain 13, where it is
the missing write-up artefact for "which invariant changed at which step".
NM#254 → Chain 16, because it holds the SemEval-2023 taxonomy decision (6 coarse
categories, not 23 fine; α = 0.342 vs a 0.667 threshold). **Chain 17 (NER)
promoted** from a narrative draft into the canonical chain list, with five
dependents and ovr#223 given its number.

## FS#134: delete

Recommended DELETE on four independent grounds — the signal exists downstream and
better (E5 cosine at `cross_source_threshold=0.88`), it **degrades
cross-language** (0.195, nearer unrelated than related), wiring it into dedup
makes corroboration *worse*, and the emit-instead option is blocked by a live
`numpy.uint64` JSON bug whose own comment claims the opposite. Deleting drops
`scipy` — **114 MB of a 450 MB venv**, re-verified directly on sadalsuud.

**Two corrections to my own FS#134 comment, both found by verifying an agent's
claims instead of repeating them. Repeating them is exactly what I did first.**

- **The outage argument is WRONG and I published it.** I wrote that deleting
  removes "the module-level import that caused a 26-hour production outage"
  (2026-06-30). The outage is real — FS `memory/gotcha-log.md:159` — but its
  cause was a **renamed venv**: `bin/activate` kept a dead `.venv` path, so
  `python3` fell through to *system* Python, and `from datasketch import MinHash`
  was merely **the first missing import to raise**. `feedparser` is equally
  absent from system Python and would have failed next. Removing `datasketch`
  would not have prevented that outage or any repeat of it. **Three grounds
  survive; this fourth one does not.** It is the "green check answered a
  different question" shape, inverted — a red failure blamed on the line that
  reported it.
- **The scipy claim holds, but not as stated.** Three packages name scipy;
  `pandas` and `yfinance` name it only under optional extras (`computation`,
  `repair`) which are **not** requested in `requirements.txt`. `datasketch` is
  the only *unconditional* requirer — right conclusion, wrong sentence. Removing
  it should also drop `scipy==1.18.0` from `requirements-lock.txt`. Correction to the issue's
own framing: not literally zero call sites (`compute_all_hashes` calls it twice,
14 tests exercise it) — but that has no production caller, so the chain has
**never executed in ~8 months**.

## Framework adoption — verified by content

`agent-ready-projects` v1.15.1 genuinely installed: five v1.15.1 marker strings
present in the global `audit-context`, and its mtime matches the commit **to the
second**. `curate` body byte-identical to the template. No global
`review-changes` shadowing the project-local adaptation (the 2026-08-06 trap).
All four skills carry `disable-model-invocation: false`. `agent-ready-papers` is
at v2.4.0 + 2 doc-only commits, **not adopted here by design**.

## NEXT SESSION

1. **Give FluxusSource its own session.** It holds the only deadline (FS#120,
   ~2026-08-14) and the fixes are FS-side code. Local clone is clean and current.
   First job: `country_queries` for `newsdata_eval`, then re-baseline.
2. **FS#134: execute the delete** (~80 LOC, 14 tests, `datasketch` +
   `requirements-lock`, and swap the `scheduled_collection.sh` preflight canary
   to `feedparser`).
3. **Corroboration step 3 is still gated** on the FS#133 floor — but expect the
   answer "the pairs were never there", not "the pairs are biased".
4. **Owner call still open**: does `ducroq/augmented-engineering` (34 open, 1
   closed ever) belong on the board?

Related: [[corroboration-feature-hypotheses]], [[cross-repo-prioritization]],
[[score-batch-shape-noise]], [[nexusmind-data-sources]].
