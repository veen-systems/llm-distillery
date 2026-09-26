# Session 2026-08-12 (afternoon) — three measurements, all pre-registered, none deployed

**Shape of the session:** owner said "go" three times and each time the answer was
a measurement rather than a change. **Nothing deployed, no filter package touched,
$1.63 of oracle spend.** 20 commits.

## What was measured

### 1. #109 arm A — `cultural_discovery v5` cross-oracle re-score: **WITHIN NOISE**

Gemini Flash against DeepSeek-stored labels, 150 pairs matched 1:1 on
(domain, stored-label band), 300/300 rows scored, 0 errors. `MAD_refused` 0.8325 vs
`MAD_passed` 0.8370 → **`D` = −0.0045, CI [−0.216, +0.195]**, against a measured
within-oracle floor **ν = 0.436**.

**A bounded null, not an underpowered one**: the CI's widest excursion sits *below*
the noise floor, so no interpretable effect can hide in the residual. Per #109's
pre-registered table this **closes #105's `cultural_discovery` half** — a retrain
there is a base-rate change, not a label-quality repair.

Scope, which is the easiest thing to lose: the estimand is the **pair-matchable**
refused population, **2,024 of 4,458 (45.4%)**. The other 54.6% has no passed rows
to match against and comes from outlets the lens gate refuses wholesale
(`eco.sapo.pt` 0.93, `theverge` 0.90, `ad.nl` 0.87).

Record: `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md`. Pre-registration
`6741da2` **before any score existed**; result `e01f1f1`.

### 2. The op-point follow-up — the `+1.044` did **not** replicate

Arm A's band table ended at `D` = +1.044 in `[4.0,10]` on **9 pairs**, which is the
only band ADR-023 cares about. Re-measured at n=66 (the whole pairable capacity, so
a near-census): **`D₄` = +0.3958, CI [+0.056, +0.750], ν₄ = 0.6869 → NOT MATERIAL /
not interpretable.** Not a clean refutation either — sign holds, CI excludes 0 —
the effect if real is below what the instrument sees.

**The instrument is the finding: ν₄ = 0.687 exceeds the 0.396 it was meant to
adjudicate.** So a single-shot cross-oracle comparison at this op-point is
unfalsifiable **at any `n`** — the floor is per-article and does not shrink with
sample size. `k = 4` averaged draws would put it near 0.34 for ~$1.05 (arithmetic,
assumes normality 40 pairs cannot establish).

Also measured and easy to misread: every row is stored ≥ 4.0 by construction, and
Gemini puts **37/66 refused (56%)** and **27/66 passed (41%)** back below it. That
is **cross-oracle disagreement, not error**.

Record: `docs/evidence/2026-08-12-cd-v5-op-point-band-followup.md`; pre-reg
`d79a4be`, result `c43ed66`.

### 3. Pre- vs post-enrichment score delta — **NM#310 is a compute story**

Owner-assigned via the NexusMind session. Pilot n=300 across all six filters,
scored on b650 `venv-prodparity` CPU.

**Control PASSED**: on rows where production ran the full model, **231/231 within
0.16, median \|Δ\| 0.0000** — so the result is production-anchored, not a bare
reproduction. Delta: mean +0.270, **median +0.112**, 26.4% negative, p95 +1.452.
**Crossings: 10/280 (3.6%) raw and 7/280 (2.5%) normalized, ALL UPWARD, 0
downward.** Under ADR-023 the direction matters — enrichment here cannot let junk
through, only surface what was already present.

**The finding that travels: the SHORTEST stubs gain the LEAST** — 0–150 chars
+0.216 against 300–600 +0.426. GN stubs are median 89 chars, so the extrapolation
to the population this design cannot reach predicts *less* gain. Logged as **H-E2**
with its own counter-hypothesis flagged as the likelier one (the slope may be a
*content* effect, uncontrolled).

Record: `docs/evidence/2026-08-12-pre-post-enrichment-score-delta.md`; hypotheses in
[[enrichment-delta-hypotheses]].

## Three things to carry, independent of the issues they came from

1. **The noise floor now has THREE sizes and picking by magnitude is not a method.**
   Batch composition 0.16 (student, `uplifting v7` held-out), cross-box 0.16, and
   **oracle decoder 0.436 corpus-wide / 0.687 at the op-point** (temperature 0.3,
   measured by scoring the same articles twice). And on the enrichment population
   the composition floor measured **0.000000** — so 0.16 did not apply there at
   all. Ask what varied in *your* comparison. → [[score-batch-shape-noise]]
2. **`stage_used` must be conditioned on before `raw_weighted_average` is read as a
   model output.** A `stage1_low` row's persisted score is an **e5 probe estimate**
   (ADR-006), not a model score — 23% of pilot rows. Every control outlier was one,
   and none was a reproduction failure. → [[nexusmind-data-sources]]
3. **Empty pre-enrichment bodies are 7.71%** (9,455 units, 1,582 articles) and are
   a *different harm* from "scored on a blurb". `_validate_article` rejects empty
   content, so production could not have scored them either — enrichment is the
   difference between existing and being dropped, and ~790 reach ≥4. A score delta
   cannot express it.

## My own errors, and how each was caught

- **Recommended NM#302 first on stale logistics.** It had merged 2026-08-06 and
  been in production since 08-11. Second such correction in two days (NM#314 was
  the first). The peer diagnosed the cause better than I did: my cross-repo state
  lives in `docs/TODO.md` and [[cross-repo-prioritization]], which record
  peer-reported facts accurately and never re-verify. **Fixed the mechanism, not
  the entries** (`df07cea`): query the other repo before ranking work in it. The
  argument was right both times — *a sound argument on stale logistics is the
  failure mode that looks most like competence*.
- **Nearly published a false absence.** Told the strata were at
  `analysis.pre_enriched`, read it over 1,070,665 rows, got **0**, and almost
  reported a second NM#300. The flags are at
  `nexus_mind_attributes/<lens>/pre_enriched`. A wrong path and a dead field both
  read as zero and the wrong one is the more exciting finding.
- **My own pre-registration used the wrong instrument.** Arm A's primary is a
  matched MAD — MAE-shaped — and **ADR-023 says never rank on MAE**. Band matching
  kills its second objection but not its first: MAE weights every article equally
  while only the op-point band decides anything. Found on self-review after the
  result was in, written into the evidence doc (`6adc637`) rather than left as a
  lesson.
- **A first sampler allocated proportionally with largest remainders**; measurement
  killed it — 150 pairs over 342 cells sent **252 cells to zero** and produced
  weights spanning 4.0–17.0. Replaced with slot-based SRS (self-weighting).

## Peer work — four sessions, all four changed my output

- **NexusMind**: corrected me twice; established that a production reading cannot
  answer #310 *at all* (the post-scoring path is gated on having cleared
  `min_score` on the stub) and that `original_content` is the better route; filed
  **#331** (pre-enrichment score stamp, as *auditability*, with my survivorship
  point written in so nobody re-scopes it).
- **FluxusSource**: **#164 shipped as deletion** of the purge loop, protecting two
  llm-distillery dependencies (obituary detector on raw ingest; the
  normalization-bootstrap harvest at `docs/RUNBOOK.md:187`). **Their closing point
  is the most valuable thing I received today** — the archive survived *only*
  because the purge was broken, and the `.suffix` half looks exactly like a
  one-character typo fix. My register said *verify a mechanism runs*; it did not say
  **verify that a mechanism NOT running is what is protecting you.**
- **FS#144 answered**: verified but **re-scoped**. Only `investment_risk v6`
  enforces on `academic`/`proxy_aggregator`, so five of six filters **cannot** be
  affected. Per-source: **6 restored** (5 Guardian sections + Ars Technica), **0
  newly excluded**, ~12 `gn_*` feeds moved `academic → proxy_aggregator` — still
  excluded, now for the right reason.
- **ovr.news**: handed #312 (the intersection number the "should ovr enrich"
  decision waits on, with GN split out because it is a failure by construction) and
  #311's **324 already-published expanded summaries**, unowned.

## Next session

1. **Framework: pinned v1.23.0, upstream v1.25.0** — owner deferred adoption to
   next session. Pre-triage table is in `docs/TODO.md`; two adopt-on-sight
   (v1.24.0's metadata-not-documents `curate` read, v1.25.0's merged adversarial
   rule) and one that vindicates this repo (the gotcha-log 2–3 line rule is
   **withdrawn**, and llm-distillery is the cited evidence).
2. **H-E1, cheap**: `nature_recovery v4`'s +0.023 zero — run the per-dimension
   check before believing it. Paired scores already exist. → #71
3. **#109 arm B still held** on its unnamed judge. H-E3 (slope vs offset) should be
   settled first — it costs nothing and decides whether arm B needs a non-Gemini
   judge or merely a refit.
4. **#106 still awaiting the owner's one-line close.**

## Related

- [[enrichment-delta-hypotheses]] · [[score-batch-shape-noise]] ·
  [[nexusmind-data-sources]] · [[cross-repo-prioritization]] · [[gotcha-log]]
