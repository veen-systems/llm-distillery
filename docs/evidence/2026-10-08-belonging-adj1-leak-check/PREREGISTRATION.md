# belonging adj1: pre-gate leak check (pre-registered 2026-10-08, before any candidate score exists)

**Why:** the adj1 build has two measured skews (build README § *Result*): positives are longer than production's
(FM-T1), and French is ~4× over-represented among positives (FM-D2). The held-out gate is ONE SHOT. Owner 2026-10-08:
train, run this check, and only then gate.

**Population:** a uniform random draw of N = 5,000 distinct production belonging rows from sadalsuud
`data/filtered/belonging/` (same rules as `draw_easy_negatives.py`: no news.google.com, content ≥ 300 chars,
dedup by id then content_hash), seed 20261008. It EXCLUDES every id in: v1's three splits (all of them, dropped rows included),
the adj1 build, harvest r1's full draw, the easy-negative draw, and `belonging_exclusions.excluded_ids()`
(pilot/exemplar/test/calibration/held-out). No labels: the check needs none.

**Instrument:** both packages (`filters/belonging/v1` and `filters/belonging/v1_adj1`) are scored on b650 GPU in the same
process environment, same ids, same order, with the package's hybrid scorer at its default batch size (as `gate.py`).
Flag = the scorer's `weighted_average` (calibrated raw, before NexusMind normalization) ≥ 4.0 (the op-point) on a `stage2` row. The candidate is scored only AFTER its calibration.json is fitted. A `stage1_low` row is not flagged. Both packages carry
the same probe, so the stage-1 split should be identical, and the script REPORTS it if not.
Language = the row's own `language` field (counts by `metadata.language_source` reported). This is NOT FM-D2's
instrument (the collector stamp recovered from archives); it is the same field on both arms.

**Groups:** LONG = content > 4,000 chars; FRENCH = `language == "fr"`. Reported for context, not decisive: every
length bin of FM-T1, the top languages, and all rows.

**Rule (owner 2026-10-08, fixed before looking):** LEAKED if, in LONG or in FRENCH, the candidate's flag rate is
≥ 1.5 × v1's AND the paired bootstrap 95% CI (10,000 resamples of rows, seed 20261008) of (candidate − v1) excludes 0.
1.5× is a judgement call, not a measured figure.
*Ruled by the owner: the 1.5× + CI rule, LONG > 4k, FRENCH. Mine, not ruled: N = 5,000, the seeds, 10,000 resamples,
"v1 flags 0 in a group ⇒ the ratio condition is met", and the row's own `language` field as the language instrument.*
→ LEAKED: buy ~1,900 long production negatives (~$6.70 est., k=1), rebuild, retrain, re-check. NOT LEAKED: run the gate.

**Known limits:** one batch order (a row near 4.0 can flip on batch composition, #95 (the batch-composition noise
floor)); the bootstrap covers sampling, not that term. A higher candidate rate on LONG is not wrong in itself
(the oracle's production positive share also rises with length); the comparison is against v1, the model it replaces.
