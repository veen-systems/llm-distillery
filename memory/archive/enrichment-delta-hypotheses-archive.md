# Enrichment-delta hypotheses — archive of closed entries

*Moved VERBATIM from `memory/enrichment-delta-hypotheses.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read surface), under
the 2026-09-27 ledger rule: entries whose verdict is closed (CONFIRMED / REFUTED / SETTLED / RESOLVED) move; open
entries, rulings and standing traps stay. Order kept; a block from inside a section repeats that section's heading.
H-E2..H-E4 (all open) stay live.*

## H-E1: `nature_recovery v4`'s delta is genuinely zero, not an artefact of its thin fit

**Position (provisional):** `nature_recovery v4` returned mean **+0.023** /
median +0.033 with 39.6% negatives — indistinguishable from zero, against
`cultural_discovery v5`'s +0.409 and `uplifting v7`'s +0.428. The likeliest
reading is that enrichment genuinely adds nothing this lens responds to: its
signal is ecological-outcome vocabulary that a headline echo already carries, so
a longer body adds length without adding lens-relevant evidence.

**Method:** the delta was computed on **raw** scores, so the 397-row
normalization fit cannot be the cause — normalization is applied after. That rules
the fit out for the delta itself but *not* for the crossing count, which is 0
gained / 0 lost for this lens at both thresholds. So: recompute per-dimension
deltas for `nature_recovery` and compare against `cultural_discovery`'s. If the
zero is real, no dimension moves. If one dimension moves and another compensates,
the aggregate zero is a cancellation and the lens is not inert.

**Alternative / counter-hypothesis:** n=48 with the effect concentrated in a top
decile elsewhere — `uplifting` has the largest mean and a +0.101 median, i.e. an
entirely tail-driven effect. `nature_recovery` may simply have missed its tail at
this n. That would make the zero a sampling result, not a property.

**Revisit trigger:** any `nature_recovery v5` work (#71), or a scale-up of this
pilot past n≈200 for that lens.

**Status: RESOLVED 2026-08-12 — the aggregate zero IS a cancellation. The "delta
is genuinely zero" position is REFUTED; the lens is not inert.**

Per-dimension deltas (body − stub) on the existing paired scores, n=48, no new
compute — `~/enrich_pilot/scored.jsonl` on b650 already carried
`stub_single_dims` / `body_single_dims`:

| dimension | mean | median | +/−/0 |
|---|---|---|---|
| restoration_scale | **+0.084** | +0.000 | 23/11/14 |
| measurable_outcomes | **+0.063** | +0.000 | 23/14/11 |
| human_agency | **+0.055** | +0.000 | 21/13/14 |
| ecological_significance | **+0.049** | +0.001 | 26/8/14 |
| recovery_evidence | −0.001 | +0.000 | 21/16/11 |
| **protection_durability** | **−0.173** | −0.006 | **10/24** |

Five dimensions move up, one moves down hard enough to cancel them. So enrichment
does affect this lens; the aggregate hides it.

**And the comparison is the finding that travels.** `cultural_discovery`'s
`evidence_quality` gains **+1.433** (median +1.536, **46 of 47 rows positive** —
the largest single-dimension effect in the pilot) and `uplifting`'s `evidence_level`
+0.525. **Enrichment's dominant effect is on evidence-quality-type dimensions, and
`nature_recovery v4` has no evidence dimension at all.** That is a better
explanation of its flat aggregate than "the lens does not respond to length", and
it predicts which future lenses will and will not gain from enrichment.

**Superseded caveat:** the counter-hypothesis above (a missed tail at n=48) is not
needed — the per-dimension split explains the aggregate without it, though it
remains true that n=48 cannot resolve the tail.

**New question, carried to #71 rather than answered here:** why does
`protection_durability` *degrade* on longer text (min −2.29, 24 of 48 negative)?
Hypothesis, untested: a headline asserting a protection outcome scores high, and
the body reveals the protection is proposed, partial or contested — i.e. enrichment
is *correcting* an over-score rather than damaging it. If that is right the
dimension is working and the aggregate zero is two correct effects, not a defect.
**Do not "fix" the negative before establishing its direction is wrong.**

---

