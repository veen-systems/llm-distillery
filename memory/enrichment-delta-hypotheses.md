<!-- Hypotheses arising from the pre- vs post-enrichment score delta (2026-08-12).
     Written at the moment the claims were made, not reconstructed afterwards.
     Format: Position / Method / Alternative / Revisit trigger / Status. -->

# Enrichment-Delta Hypotheses (NM#310, ovr#312)

**Settled and NOT a hypothesis** — the headline is measured and lives in
`docs/evidence/2026-08-12-pre-post-enrichment-score-delta.md`: scoring an article
on its pre-enrichment stub rather than its enriched body costs **median +0.112**
raw score, moves **10 of 280 (3.6%)** across the raw op-point and **7 of 280
(2.5%)** across the normalized 4.0 gate, and moves **0 downward**. Control passed
(231/231 `stage2` rows within 0.16, median 0.0000). Own batch-composition floor
**0.000000**, so #95's 0.16 does not apply here.

Everything below is open.

---

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

## H-E2: Google News stubs would gain LESS than this corpus average, not more

**Position (provisional):** delta by stub length is **0–150 chars +0.216**,
150–300 **+0.258**, 300–600 **+0.426** — the shortest stubs gain the *least*. GN
stubs are median **89 characters**, inside the 0–150 band. So the extrapolation to
the population this design cannot reach predicts a *smaller* gain, which argues
NM#310 is a compute story for GN specifically and not only in aggregate.

**Method:** this cannot be tested directly and that is the point — GN is **0.0%
of the paired population (0 of 122,557)** because per NM#310 the redirect never
resolves, so no enriched body exists to pair against. The only test available is
to extend the slope: add a 0–100 char band once enough non-GN stubs that short
accumulate, and check the monotone trend holds down there rather than reversing.

**Alternative / counter-hypothesis:** the slope is a *content* effect, not a
length effect — 300–600 char stubs may be lead paragraphs from outlets whose full
bodies are richer, while 0–150 stubs come from outlets whose bodies are thin too.
In that case the slope says nothing about GN, whose bodies (if resolvable) might
be full articles. **This is the more likely failure and it is not controlled for.**

**Revisit trigger:** any GN resolution capability landing anywhere in the chain,
which would make a direct measurement possible for the first time.

**Status:** open, and the weaker of the two bridges. **Never quote the corpus-wide
delta for GN.**

---

## H-E3: DeepSeek and Gemini differ in SLOPE, not offset

**Position (provisional):** from #109 arm A. Corpus-wide, Gemini − DeepSeek was
**+0.030** on gate-refused rows and **+0.353** on passed rows; restricted to
stored ≥ 4.0 it flipped to **−0.952** and **−0.480**. Both oracles agree near
zero and diverge at the top, with DeepSeek scoring higher where scores are high
and lower where they are low. That is a slope difference — DeepSeek spreads the
scale wider — rather than a constant bias.

**Method:** regress Gemini score on stored DeepSeek score across the full range
and test whether the fitted slope differs from 1. The paired data to do it already
exists (arm A, 300 units; band-4 follow-up, 132 units) and costs nothing further.

**Alternative / counter-hypothesis:** two separate ceiling/floor effects rather
than one slope — both oracles compress near 0 and near 10, and the apparent slope
is the difference in where each starts compressing.

**Why it matters:** if it is slope, then a filter's **calibration** absorbs it and
a cross-oracle disagreement number is not evidence of a label problem at all. If
it is bias, calibration does not absorb it. This bears directly on whether #109
arm B needs a non-Gemini judge or merely a re-calibration.

**Revisit trigger:** before any cross-oracle number is used to argue about label
quality; and before #109 arm B is designed.

**Status:** open, **unregistered at the time both measurements were taken** — it
was noticed while writing them up, which is exactly the gap v1.25.0's
hypothesis-log trigger addresses.

---

## H-E4: `discovery_novelty` is where oracle-prompt work would pay for cd successors

**Position (provisional):** at the op-point, per-dimension cross-oracle MAD was
`discovery_novelty` **3.030 / 2.341** (refused/passed) against
`evidence_quality` 0.992 / 1.030. The filter's *defining* judgement is its least
reproducible dimension, and its **gatekeeper** dimension is its most reproducible.

**Method:** a repeated-draw design on `discovery_novelty` alone — score the same
articles k=4 times and partition the 3-point MAD into oracle instability versus
genuine inter-oracle disagreement. At ν₄ = 0.687 a single-shot design cannot
separate them.

**Alternative / counter-hypothesis:** `discovery_novelty` is simply the widest
dimension by construction — if its scores span more of 0–10 than
`evidence_quality`'s do, a larger absolute MAD is arithmetic, not disagreement.
**Check the per-dimension variance before believing this at all.**

**Revisit trigger:** `human_thriving` v8 prompt work, or any cd v7.

**Status:** open, and the counter-hypothesis is cheap enough that it should be run
first.

---

## Related

- `docs/evidence/2026-08-12-pre-post-enrichment-score-delta.md` — the measurement
- `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md` and
  `-op-point-band-followup.md` — where H-E3 and H-E4 come from
- [[nexusmind-data-sources]] — what each artefact excludes; `stage_used` must be
  conditioned on before `raw_weighted_average` is treated as a model output
- [[score-batch-shape-noise]] — the three distinct noise floors and why magnitude
  is not a way to pick between them
- [[google-news-corpus-hypotheses]] — the GN population H-E2 cannot reach
