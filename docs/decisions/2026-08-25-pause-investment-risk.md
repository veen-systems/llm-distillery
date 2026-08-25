# Pause `investment_risk` — 2026-08-25

**Owner ruling, verbatim:** *"aegis is dormant, nobody reads it - pause it"*

**Status:** applied in NexusMind `config/app.yaml`. Not deployed at the time of
writing — the box was mid-cycle. **PAUSED, NOT REMOVED.**

## What was paused, and what was not

| | state |
|---|---|
| `pipeline.enabled_filters` | `investment_risk` commented out — 5 filters run, not 6 |
| `pipeline.aegis_export.enabled` | `false` — its only input was the paused filter |
| filter package `filters/investment_risk/v6/` | **kept** |
| HF Hub repo `jeergrvgreg/investment-risk-filter-v6` (private) | **kept** |
| Contract C (`contracts/nexusmind-aegis-export.schema.json`) | **kept** |
| `data/exports/aegis/archive/` — 251 daily files since 2025-12-07 | **kept** |
| ovr.news's `investment_risk` allow-list (3 files) | **kept — do not remove** |

⚠️ **The ovr.news allow-list must stay.** ovr validates every article in its
~10-day window, and rows already scored carry an `investment_risk` analysis
block. Removing the allow-list would make those rows fail validation as they
drain. It costs nothing to leave.

## Why the export was disabled in the same change

`scripts/export_aegis_narrative.py` aggregates **only** `investment_risk` output.
Left enabled it would run every cycle over zero rows and write a confident
`GREEN` file with nothing behind it. **A stale export that still looks live is
worse than one that stopped.**

⚠️ **The gist is frozen, not deleted.** Gist publishing is switched on via
`deploy/systemd/nexusmind.env` on sadalsuud. Disabling the export means the gist
keeps its 2026-08-25 contents indefinitely — anything still fetching it receives
that day's numbers forever. Deleting or emptying it is a separate decision.

## The evidence behind the ruling

Gathered before the decision, not after:

- **It was never an ovr.news lens.** ovr.news references the name in exactly 3
  files, all allow-lists; `validate.ts` calls it *"an Aegis-only filter"*. No
  tab, no feed, no reader.
- **Its consumer chain was real but one-sided.** The export ran every cycle,
  archived 251 daily files back to 2025-12-07, and published to a gist for an
  Aegis GH-Actions runner. The owner confirms nothing consumes it.
- **78.5% of its output landed in `unclassified`** on the last run — 6,224 of
  7,927 articles.

## Two consequences worth checking after the first paused cycle

1. **The ordering handicap should mostly disappear.** `investment_risk` was the
   dominant post-scoring enricher — 51 of 70 over a 12-cycle window — and it ran
   third, so `solutions` and `uplifting` (first and second) were persisted with
   the pre-enrichment text on 18 of 31,596 multi-lens articles (0.057%),
   `solutions` losing 18 of 18. With it gone, the remaining enrichers are
   `solutions` (15) and `uplifting` (4), which run first and second, so nothing
   should run ahead of an enricher. **Predicted, not measured — re-run
   `ordering_effect.py` after a few cycles rather than assuming.**
2. **Block-ledger `placements` drops from 6 to 5.** Expected, not a defect: the
   count is per enabled filter. A verifier reconciling `N articles × 6` must be
   read as `× 5` from the first paused cycle.

3. **Every measurement over `data/filtered/` keeps seeing `investment_risk` for
   up to 14 days.** Its directory stops being written but the existing files stay
   until cleanup ages them out, so the stamp census, the register and any
   multi-lens analysis will still report six lenses — with the sixth's newest file
   getting steadily older. ⛔ **A window is part of a source**: quote the window,
   and treat a "6 lenses" reading after 2026-08-25 as history, not state.

## What "un-pause" costs

Restore the `enabled_filters` line **and** `aegis_export.enabled: true`. Both are
config; no code, no deploy of a package. The model is still on the Hub.

## The reference-example question, answered separately

`investment_risk` is the only filter with its own downstream contract and its own
export path — the only complete instance of *llm-distillery builds → NexusMind
deploys → a non-ovr consumer eats it*. **A paused package documents that chain as
well as a running one does**, which is why nothing was deleted. If a live
demonstration of that pattern is wanted later, it should be built deliberately
rather than kept alive by inertia at six scoring passes a day.
