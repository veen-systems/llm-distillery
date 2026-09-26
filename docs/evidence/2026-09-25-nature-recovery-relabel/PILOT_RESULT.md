# Nature recovery relabel PILOT — FAILED its bar (2026-09-26)

| bar item | result |
|---|---|
| controls 4/4, both passes | ✅ 4/4, 4/4 |
| A vs B ≥ 0.90 | ✅ 0.98 (49/50) |
| owner agrees with the A∧B consensus on ≥ 9/10 | ⛔ **3/10** |
| presence (consensus ≠ oracle on ≥ 1 row) | ✅ 7 rows |

**Per PILOT_PREREGISTRATION.md the full relabel does NOT run.**

## What failed: the judges are STRICTER than the owner's concept of the lens
On the same 10 rows (7 of them the consensus-vs-oracle disagreements), the owner agrees with the **oracle 8/10**
and with the **judges 3/10**. The owner called IN, and the judges OUT: stork breeding success (Rust), a newly
found fungus killing an invasive moss, a giraffe translocation for herd genetics, a penguin colony established
and growing on a breakwater, and elephant-reserve expansion with carbon gains. The judges' rubric (the nr v4
prompt's STEP 1 + NR-1) is narrower than what the owner means by Nature recovery, so relabelling with it would move
the training labels AWAY from the owner. The oracle's v4 labels are, on this evidence, closer.

## ⚠️ Consequence for the miss audit (`../2026-09-25-nature-recovery-miss-audit-2/`)
Its "~47% of what nr publishes is in scope" (nr_passes stratum) came from this same instrument. The owner's 18/20
there was drawn mostly from clearly-off-topic strata, so it did not test borderline nature stories. That 47% is
very likely UNDERSTATED, and should not be quoted as nr's precision. The miss counts (13 at the cut-off, 22 in the
2.0–3.0 band) came from the same strict judge, so they are if anything conservative. The instrument's misses
lean the other way.

## Next (owner's call)
The disagreements name categories the rubric excludes and the owner includes: population/breeding counts,
reintroductions and translocations, natural (not human-made) recoveries, protected-area expansion. Either
(a) the owner rules on those and the pilot re-runs on a fresh sample, or (b) the relabel is dropped: the oracle
labels already match the owner 8/10.
