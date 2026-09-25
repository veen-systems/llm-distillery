# adj3 band audit — RUN NOT USED: the drift check failed (2026-09-25)

**Pass A vs pass B agreed on 0.844 of 32 rows; the pre-registered stop is 0.90.** Per
PREREGISTRATION.md the run is **not used, and is reported, not repaired**. No junk-per-cut-off
table is published from it. `result.txt` is `analyse.py`'s own output; controls were 4/4.

## What disagreed (5 of 32) — genuine margin cases, not noise in one direction
| sub-band | pass A | pass B | what the article is |
|---|---|---|---|
| [4.0, 4.25) | response_to_harm | in_scope | a men's centre opened in a town with high domestic violence |
| [4.0, 4.25) | in_scope | out_of_scope | karting season results |
| [4.25, 4.5) | in_scope | cannot_judge | paywalled teaser: a refugee now a medical assistant |
| [4.25, 4.5) | in_scope | out_of_scope | government round-up of infrastructure cutting travel times |
| [3.5, 3.75) | in_scope | out_of_scope | athlete's world record after illness |

Two are **sports results**, one is a **paywalled teaser**. Neither has an explicit ruling. The live
audit's owner check also split on sport (judo medal, owner OUT). Below adj3's op-point the articles are
more borderline by construction, and the rubric's unruled categories show up as judge disagreement.

## Owner check
14/20 blind (below 18); after rulings the judges are 19/20 (`owner_check_resolution.md`). Moot for
the numbers, since the run is not used, but it holds two lessons: #12 was the assistant's summary
leaving out a material fact, and #5 may refine the court-ruling ruling.

## Next — the owner's call
Rule on the unruled categories (sport results, paywalled teasers), then re-run on a FRESH sample with a
new pre-registration, or choose a cut-off without this measurement.
