# Nature recovery miss audit — RESULT WITHHELD: the owner check disagrees with the RUBRIC, not the judges (2026-09-25)

Controls **4/4**, drift **0.989** on 90 rows (the most self-consistent judging of the day). Owner check
**13/20**, below the ≥ 18 bar, so the figures below are **not reported as a measurement** (PREREGISTRATION.md).

## Why 13/20: all 7 disagreements run ONE way, owner IN, rubric OUT
Treaty ratification (High Seas; no area designated yet) · farmers stopping stubble burning · Qatar meadow
planting (no regeneration measured) · coral-spawning research · one-day car-free NO2 drop · monk-seal
reintroduction plan (early stage) · declining fire hotspots (mixed trend). Each is OUT under nature_recovery
v4's own STEP 1 (observed recovery or delivered in-force protection; pledges, plans, symbolic events and
research without outcomes are OUT). **The owner's concept of the lens is broader than the prompt that
defines it.** That is a definition question for the owner, not a judge error.
Also: in #9 and #10 the assistant's question text added its own gloss ("no outcome measurements reported",
"no recovery reported"). It leaned OUT, and the owner called both IN regardless. Recorded in `owner_check_calls.jsonl`.

## What the numbers say UNDER THE v4 RUBRIC (withheld as a measurement; `result.txt`)
| stratum | N/week | in scope | est./week |
|---|---|---|---|
| nr passes (precision control) | 155 | 12/30 = **40%** | 62 |
| near miss 3.0–3.75 (cut-off) | 61 | 7/59 | 7 |
| low 2.0–3.0 (model) | 210 | 2/47 | 9 |
| very low < 2.0 (model) | 14,082 | 0/60 | 0 |
| probe screened (probe) | 1,487 | **0/100** | 0 |

By its own definition nr misses ~16 stories/week that other lenses published (CI 5–31), none via the probe.
The prediction for the probe stratum (2–10%) was wrong. Only 40% of what nr publishes meets its own
strict definition: the filter is loose where it passes and tight in the prompt.

## Next — the owner's call
Rule on the seven categories above, i.e. decide the Nature recovery lens definition. That definition then
drives a prompt revision (nature_recovery v5, #71). Re-judging this same panel under the new definition
costs $0 and would give the miss rates the owner actually cares about.
Side note from the owner during the check: several articles were "a solution", and the Solutions lens may
need tuning too.
