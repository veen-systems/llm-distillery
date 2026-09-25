# Nature recovery miss audit — RE-JUDGE under ruling NR-1: RESULT (2026-09-25)

**Measured, and reportable:** owner check **18/20** (bar ≥ 18), controls 4/4, drift A-vs-B **0.967** on 90 rows.
Same panel (301 + 4 controls) and `analyse.py` as the first run; the judges also applied NR-1 (completed
restoration/protection steps count before recovery is measured; plans, short-lived gains and research
without outcomes stay out). Output: `result.txt`.

## What Nature recovery misses: articles another lens published that week, judged in scope under NR-1
| where it leaks | stratum | per week (point) | 95% range (N × Wilson) |
|---|---|---|---|
| cut-off | nr 3.0–3.75 (near miss) | **13** | 8 – 21 |
| model | nr 2.0–3.0 | **22** | 10 – 47 |
| model | nr < 2.0 | 0 observed (0/59) | 0 – ~860 |
| probe | screened out by nr's probe | 0 observed (0/100) | 0 – ~55 |

**Point estimate: ~36 missed per week (~0.9 per 4-hour cycle).** For scale: nr publishes ~4.1 per cycle, and only
~47% of those (14/30, 0.302–0.639) are in scope by the same definition, i.e. ~1.9 good stories per cycle. So it misses
roughly one good story for every two it catches, and half of what it does publish is not Nature recovery.

⚠️ **Correction to `analyse.py`'s own printout.** It prints `0 [0, 0]` for the two zero strata and a total
interval of 18–57. That comes from a percentile bootstrap, which is **degenerate at 0 positives**, so those
bounds are wrong. The table above uses N × Wilson instead. It follows that **the total's upper bound is not
18–57; the very-low stratum is too thinly sampled (59 of 14,082) to rule out rare misses.** The first run's
"none via the probe" had the same flaw and is corrected in its README: it should read "none observed".

## Owner check notes
The 2 disagreements were both the owner calling IN what NR-1's own wording keeps OUT: #6 Peru's Sierra Verde
*relaunch announced* (a plan), #18 a climate *speech*. The owner flagged many panel articles as "solution?".
That is the Solutions lens's question; for this lens they were OUT. The odd-looking articles are by design:
the panel samples every nr score level, including the very-low and probe-screened strata, to test for misses there.

## What it means for the prompt question (owner: "wait for the re-judge first")
NR-1 moves real stories. Most misses sit just below the cut-off or in the 2.0–3.0 band, i.e. the MODEL scores
completed restoration steps too low, which is what NR-1 changes. It is not the probe. That supports route B
(re-adjudicate labels under NR-1 and retrain, as for human_thriving v9) before any v5 prompt spend. Owner's call.
