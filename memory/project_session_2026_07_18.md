# Session 2026-07-18 — solutions v4: decisions ratified, corpus trap caught, rename, pipeline scaffolded

**Headline:** the 4 engineer decisions were ratified and the "re-score the old
corpora" plan was caught as a ~85%-noise trap *before* spending. The filter was
renamed sustainability_technology → **solutions** (ADR-012), the multilingual
prefilter drafted, and the corpus pipeline replanned + scaffolded. **Zero oracle
spend beyond ~$0.20 of diagnostics.** Everything committed + pushed to
`solutions-v4-calibration` (`70473ca..dfc9937`).

## What happened

1. **Engineer decisions (#43) ratified:** DeepSeek oracle (both ADR-020 judges),
   thinner-but-cleaner tab accepted, go. Gate/weight rewrite deferred to eval
   time (per-dim labels).
2. **4 calibration fixes applied + verified against the LIVE oracle** (5-article
   smoke): router default-to-pass on mediation/proposal shapes, governance-recall
   in-scope cases (legal-personhood, deployed gov programs), corporate_pr
   encouragement, and a **scrape-junk ingestion check** (`is_scrape_junk` in
   `ground_truth/text_cleaning.py`, wired into `score_deepseek_production.py`).
3. **The corpus trap.** The plan was to re-score old ST v3 + foresight r2
   corpora (13,796 unique) as-is. Located them on gpu-server (reachable once the
   engineer `ssh-add`ed the key). A 5.5K-arXiv composition looked wrong → an
   80-article diagnostic ($0.09) showed **85% not_a_solution under the Solutions
   lens**. Stopped the ~$18 re-score. See gotcha-log 2026-07-18.
4. **Data-setup plan (v2.1)** — `filters/solutions/v4/DATA_SETUP_PLAN.md`:
   seed → per-type e5 screen → enriched corpus → score → train → active-learn.
   Hardened across **two multi-model review batteries**: round 2 caught that my
   own stratified pre-spend gate was self-contradictory (hard-blocking on a
   high-band-community cell the plan says may be unreachable = unpassable) →
   split into deterministic Part A + warning Part B. (Round-2-finds-defects-in-
   round-1-fixes pattern held a 9th time.)
5. **Multilingual audit** (engineer flagged the nr #70 scar). Production is ~29%
   non-English. Findings: e5 screener is multilingual; seeds are 31% non-English;
   scrape-junk char-gate does NOT drop non-English real content. **Action:**
   drafted `prefilter.py` (`SolutionsPreFilterV4`) on the nr v4 template —
   commerce-only pass-through, multilingual `POSITIVE_PATTERNS` with an
   inflection regression test (which immediately caught `desplegar→despliega`).
6. **Rename sustainability_technology → solutions (ADR-012)** — done now,
   pre-corpus-scoring, so the analysis-field migration touched only 2 calib files
   (not a scored 14K corpus). Dir moved (v1–v3 stay), `filter.name=solutions`,
   field `solutions_analysis`, class `SolutionsPreFilterV4`. Verified: field
   derives, 42 tests pass, no dangling refs.
7. **Corpus-build tooling** (free groundwork): `extract_solution_seeds.py`
   (per-type seeds: tech 73 / gov 57 / community 52, each 21–44% non-English) +
   `near_dup_filter.py` (multilingual-e5 cosine ≥0.93 vs calib). Pool identified:
   `NexusMind/data/raw` (83 files, carries `_is_commerce`).

## State: labeling designed, model NOT built

The filter has config/prompt/prefilter/calibration_report/plan. It has **no
model, no training corpus, no calibration.json, no inference stack** — all gated
on the corpus build. Honest inventory in DATA_SETUP_PLAN.md + README.md.

## Next session pickup

**Blocked on 2 engineer inputs** (task #8) before the corpus build can run:
1. **~20–30 hand-curated high-concreteness community seeds** — the one input
   e5 screening + active learning can't manufacture (that cell is the known soft
   spot; I offered to draft candidates for approval).
2. **Sign-off on the pinned Execution defaults** (top-k splits tech3000/gov3000/
   community2000, ~2000 random + ~1000 hard negatives, near-dup 0.93).

Then (all on gpu-server / mostly free until the one paid step):
per-type e5 screen (+ near-dup) over `NexusMind/data/raw` (commerce-filtered) →
assemble enriched corpus + Step-2.5 random unscreened test holdout →
**deterministic Part-A gate (free)** → **~$0.20 Part-B gate** → only if both pass,
the **~$13–18 DeepSeek score** (off-peak) → prepare_data → train → calibrate →
ground-truth gate (ADR-021) → wire base_scorer/inference → go-live.

**Go-live reminders:** wire `SolutionsPreFilterV4` into the NexusMind loader;
retire foresight (NexusMind app.yaml + ovr filters.ts); fit normalization from a
production-base-rate rescore (NOT the enriched corpus); Hub repo name `solutions`.

**Carried:** ADR-020 PROVISIONAL→Accepted after the pipeline lands (+ revise
draft-020 per the standing 4-reviewer feedback); #72 nr v4 normalization refit
still unblocked; sadalsuud app.yaml healthcheck.enabled drift (#91); uplifting v7
NO_HUB backup decision; cd v5's 5 config-schema exemptions.
