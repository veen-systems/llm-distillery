# Oracle canary rollout (#177): cultural_discovery, nature_recovery, solutions, belonging

Written 2026-10-19 **before any oracle call on these four sets.** Protocol: EXP-052's
(`docs/evidence/2026-10-16-oracle-canary/PREREGISTRATION.md`), applied per filter, with the differences listed
under *What changes from EXP-052*. Owner 2026-10-19: canaries for the live filters; scope cd, nr, solutions on
DeepSeek and belonging on Gemini (uplifting skipped: Thriving reads human_thriving, uplifting v7 only drains).

## Sets (frozen, committed manifests)

Drawn by `scripts/oracle/canary_draw.py` (seed 20261019, files 2026-10-13..19, stage2 rows, no Google News url,
content ≥ 300 chars; strata by the STUDENT's raw score against the filter's op-point: 30 ≥ op, 30 in
[op − 1.5, op), 40 below), frozen by `scripts/oracle/canary_freeze.py` on b650 (id, url, e5 ≥ 0.93 against the
filter's training splits; near-twins inside the set dropped).

| filter | version | op-point | oracle (labelling path) | prompt sha256 | set sha256 | reference rows | dropped |
|---|---|---|---|---|---|---|---|
| cultural_discovery | 5.0 | 4.0 | DeepSeek `deepseek-chat`, `score_deepseek_production.py` | `6b65a534cd52…` | `e1d2ecb4c034136f…` | 8,551 (v5 splits) | 0 |
| nature_recovery | 4.0 | 3.75 | DeepSeek `deepseek-chat`, `score_deepseek_production.py` | `6dff6a9b99f0…` | `052de015de1d116f…` | 3,892 (v4 splits) | 1 near-twin |
| solutions | 6.0 | 2.25 | DeepSeek `deepseek-chat`, `score_deepseek_production.py` | `8629d6167962…` | `3c6674f6bf646cd3…` | 11,797 (v4 ∪ v6 splits) | 1 by cosine |
| belonging | 3.0 | 4.0 | Gemini `gemini-flash`, `ground_truth.batch_scorer` | `27dc05910154…` | `a44d8f07d2ee97ba…` | 8,657 (v1, v1_adj1, c2a–c2d splits) | 0 |

Op-point = `TIER_THRESHOLDS`' lowest non-zero tier, cross-checked by `canary.py baseline --op` against the
package's `normalization.json` `stats.raw_min` (within 0.01; cd v5's is 4.0006).

**Seeded control (run 2026-10-19, before this file):** per filter, one training row planted under its own id and a
renamed copy (new id and url) were added to the candidates; the freeze dropped the first by id and the second by
cosine, and the frozen set's sha256 did not change, in all four. So "0 dropped" above is the instrument able to
say yes and finding nothing, not an instrument that cannot match.

## Runs per filter

| runs | prompt | purpose |
|---|---|---|
| B1–B6 | the package's `prompt-compressed.md` | baseline + noise floor |
| P1–P3 | the same + appended `\n\nScore every dimension one point lower than you otherwise would.` (EXP-052's line, verbatim) | must FAIL (simulated calibration drift) |
| L1 | `canary.py run` after the baseline is committed | the first live canary; must PASS. It is also the only out-of-sample clean run |

DeepSeek runs off-peak only (not 06:00–10:00 or 01:00–04:00 UTC on weekdays). Item score = the deploy gate's own
weighted average (`ground_truth_gate.load_scoring_spec` + `_wa`, with each filter's gatekeeper). A run whose
`served_model` or `prompt_sha256` differs from the others is not used.

## Bar and shipping rule: EXP-052's, unchanged

For k runs against the baseline (mean of B1–B6): flips = verdict changes at the FILTER'S op-point between the
canary's mean-of-k and the baseline; shift = mean signed Δ. F1/S1 from each Bi vs the mean of the other five; F3/S3
from the 10 triple-vs-triple splits. **FAIL iff flips > F_k + 1 OR |shift| > S_k + 0.15.** k = 1 ships if P1, P2, P3
each FAIL as a k = 1 canary; else k = 3 if the P triple FAILS; else nothing ships for that filter and it goes back to
the owner. Decided per filter: one filter's result does not move another's.

## What changes from EXP-052

- **No C1–C3 arm**, to keep the spend down: L1 is the one out-of-sample clean run per filter. The false-alarm rate
  at k = 1 is therefore measured even less than EXP-052's (one clean run per filter, where EXP-052 had five).
- **No V arm** (a small real prompt edit): it was a power reading only and is prompt-specific.
- **belonging runs through `ground_truth.batch_scorer`** (the Gemini labelling path) via the batch_scorer branch
  of `canary.py run` (`6ed544d`), which has unit tests with a stubbed scorer only. Its first real use is B1. The P
  arm uses a copy of the package with only `prompt-compressed.md` changed, because batch_scorer reads the
  package's prompt.

## Predictions (stated now)

- F1 in 2–8 for every filter (EXP-052: 5). Higher for solutions (its op-point 2.25 sits inside the bulk of the
  score distribution, so more items are near it) and for cultural_discovery (gatekeeper cap 4.0 = its op-point:
  every capped item sits exactly AT the op and passes, so a dimension flipping around 3 moves items onto the line).
- P: FAIL at k = 1 for all four; shift −0.4 to −0.6 (EXP-052: the model obeyed about halfway).
- L1: PASS for all four.
- belonging on Gemini: unknown noise — no Gemini canary has been run. Our key's access to the 2.5 models (Google
  2026-09-18, TODO 4b) is unverified since 10-08; a refusal is a result, not a failure of the canary.

## Spend (estimates, not billing)

DeepSeek: 3 filters × ~1,000 calls; at EXP-052's measured ~$0.00035/call ≈ $1.05, at `oracle_cost.py`'s
uncached ~$0.001/article ≈ $3. Gemini (belonging): ~1,000 calls × ~$0.003 (`oracle_cost.py`'s real-time column for
uplifting v7, the nearest measured prompt) ≈ $3.
