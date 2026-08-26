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

Restore the `enabled_filters` line, `aegis_export.enabled: true`, **and the smoke
fixture row** — see the incident below. No code, no deploy of a package; the model
is still on the Hub.

⛔ **THE PAUSE ITSELF NEEDED A THIRD FILE, AND FINDING OUT COST A PRODUCTION CYCLE.**
`nexusmind.service` FAILED at 2026-08-25 20:09:54 and the 20:03 cycle never ran:

```
ERROR: smoke fixture references filters not in app.yaml enabled_filters: ['investment_risk']
  enabled_filters = ['belonging', 'cultural_discovery', 'nature_recovery', 'solutions', 'uplifting']
```

`deploy/smoke_test_articles.jsonl` still carried an `investment_risk` row, and
`deploy_filters.sh` refuses to deploy when a fixture names a filter the pipeline no
longer loads — the post-deploy smoke test addresses `/filter/{name}/score` and would
404. ⭐ **The gate is the control working**, fail-closed by design since 2026-07-17,
and it caught a real inconsistency the same evening it was created.

The row was removed rather than the gate weakened (NexusMind `5c94a0e`). That is the
reversible direction: with the row gone, an un-pause that forgets to restore it
produces a **WARN** ("enabled filter has no smoke fixture"), never a hard failure.
Recover it with `git show c7af891:deploy/smoke_test_articles.jsonl`.

⚠️ **Nothing in the config names that fixture, and no test covers the pair.** The
only thing that knows they must agree is a bash gate that runs at service start —
which is why a two-line config change surfaced as a missed production cycle almost
three hours later instead of at commit time. No data was lost: `fluxus-collection`
succeeded at 20:03, its output sat on disk, and the next cycle reads the whole
14-day raw window. One cycle of latency, and the 00:00 and 04:00 cycles both ran
clean with "All smoke tests passed".

⛔ **Found the same evening, and it nearly made that paragraph false.** The
filter's memory of what it has already scored is
`data/raw/.processed_ids_investment_risk.json` (29.4 MB). The raw cleanup sweep
globs `("*.jsonl", "*.jsonl.bak", "*.json")`, and **`pathlib.Path.glob` matches
dotfiles** — `glob.glob` does not, which is what makes the pattern read as safe.
A *running* filter rewrites its store every cycle, so the mtime is never stale
and the sweep never touched it; **a paused filter's store ages**, and at
`temporal.cleanup_older_than_days: 14` it would have been deleted around
**2026-09-08**. Un-pausing after that date would silently mean re-scoring the
whole 14-day raw window — not two config lines. The store is not archived either
(the archiver globs `content_items_*.jsonl`), so it would simply be gone.

Fixed in NexusMind `96b29f3`: the sweep skips names starting with `.`, with a
test that fails against the previous code and a control proving the sweep still
deletes real stale data. **A data sweep must not reach state.** With the guard
deployed, un-pause is what this section says it is, on any date.

## The reference-example question, answered separately

`investment_risk` is the only filter with its own downstream contract and its own
export path — the only complete instance of *llm-distillery builds → NexusMind
deploys → a non-ovr consumer eats it*. **A paused package documents that chain as
well as a running one does**, which is why nothing was deleted. If a live
demonstration of that pattern is wanted later, it should be built deliberately
rather than kept alive by inertia at six scoring passes a day.
