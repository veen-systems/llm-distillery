# Cross-Filter Score Normalization — The Method

**Status:** canonical method reference (final method as of 2026-07-16, op-point-anchored CDF).
**Audience:** (1) anyone fitting normalization for a new or retrained filter — follow §6 verbatim;
(2) article/source material — every number in here is from production or a committed artifact.
**Decision records:** ADR-014 (percentile normalization), ADR-008 (isotonic calibration).
**Operational shorthand:** `docs/FILTER_PLAYBOOK.md` §6. **Code:**
`filters/common/score_normalization.py` (math), `scripts/normalization/fit_normalization.py`
(fitter + guards), `tests/unit/test_normalization_invariant.py` (commit-time invariant),
NexusMind `src/scoring/production_scorer.py` (application site + load guards).

---

## 1. The problem

A portfolio of distilled scorers produces incomparable raw scores. Each filter's 0–10 output is
shaped by its own oracle prompt, training distribution, gatekeeper caps, and concept prevalence
in news. Measured across 182K production articles (2026-03-30):

| Filter | Pass rate (MEDIUM+) | Mean WA (MEDIUM+) |
|---|---|---|
| uplifting | 62.8% | 5.76 |
| sustainability_tech | 8.6% | 5.31 |
| cultural_discovery | 4.8% | 5.70 |
| belonging | 2.6% | 5.80 |
| nature_recovery | 0.3% | 5.16 |

Raw score 5.5 is a mediocre uplifting article and an exceptional nature_recovery one. Any
consumer that compares scores across filters — a shared HOME feed ranked by max-score, or
"open this article in the tab where it scores highest" — is systematically hijacked by the
loosest filter. Linear rescaling (`score_scale_factor`) makes it worse in the other direction:
stretching the compressed filter promotes its mediocre middle over other filters' genuine top
(we shipped that bug; ADR-014 superseded it).

**What normalization is NOT:** a filter-quality mechanism. It exists only for cross-lens
ranking and tab assignment. Tier is *reassigned* on the normalized score by design, so
`raw >= threshold` together with `tier: low` is correct behavior, not a bug (see playbook §6).

## 2. The two-stage recipe

Two different jobs, two different mappings, both monotone lookup tables:

1. **Calibration (ADR-008), within-filter.** Per-dimension isotonic regression fitted on the
   val set (student prediction → oracle score). Makes a score *honest* relative to the
   filter's own oracle. Does nothing for cross-filter comparability.
2. **Normalization (ADR-014), across filters.** Map the calibrated weighted average to its
   **percentile rank in that filter's own production MEDIUM+ population**, times 10.
   "Top 5% of Recovery" and "top 5% of Uplifting" then compare as equals.

Pipeline order (invariant): raw prediction → calibrate → weighted average → gatekeeper cap →
**normalize** → reassign tier on normalized → display_rank. Calibration and gatekeeper run in
shared code (`filter_base_scorer.py`); normalization and tier reassignment run only in
NexusMind's `ProductionScorer` wrapper. `raw_weighted_average` is preserved in the output for
audit and future refits.

## 3. The math

### 3.1 Fit (empirical CDF as a lookup table)

Given the fit population's weighted averages `w₁…wₙ` (see §4 for what the population must be):

1. Drop non-finite values (these are also excluded upstream at data load — §5.5).
2. Sort. Build `n_bins = 200` evenly spaced x-points over `[min(w), max(w)]`.
3. For each x: `y(x) = |{wᵢ ≤ x}| / n × 10` — i.e. `y = 10 × F̂(x)`, the empirical CDF
   (computed with `searchsorted(..., side="right")`, so ties share a value).
4. **Anchor (final method, 2026-07-16):** prepend the breakpoint `(op_point, 0.0)` when the
   sample minimum sits above the filter's operating point (the lowest non-zero tier
   threshold — the score at which an article first becomes visible). See §3.3.
5. Store as `normalization.json`: `x[]`, `y[]` (6-decimal), `n_articles`, provenance strings,
   and `stats{raw_min, sample_min, raw_max, raw_mean, raw_std, percentiles}`.

### 3.2 Apply (inference)

`normalized = np.interp(wa, x, y)` — linear interpolation between breakpoints; queries below
`x[0]` clip to `y[0]`, above `x[-1]` to `y[-1]` (→ 10.0 at the top by construction).
Properties: monotone (within-filter ordering preserved); distribution-agnostic (works for
uplifting's near-normal, nature_recovery's heavy skew, thriving's bimodal); independent per
filter (adding/refitting one filter never invalidates another).

### 3.3 The anchor — why and how

`stats.raw_min` (= `x[0]`) is the CDF's lower coverage edge. Pre-anchor, it floated to the
*sample minimum*, which made it density-dependent: a dense fit lands ~0.0003–0.0006 above the
op-point, a sparse needle fit can land arbitrarily higher, and everything in
`[op_point, raw_min)` clips to `y[0]` at inference. Both production incidents this mechanism
ever had were `raw_min` off the op-point (§5.1–5.2), and no static tolerance can separate
"legitimately sparse" from "drifted": an equality test false-fails jitter, a 0.25 margin
false-fails sparse needle fits, a 4.5 bound blesses silent clamping.

The final method dissolves this: `fit_normalization(anchor_min=op_point)` **prepends**
`(op_point, 0.0)` to the table. Consequences, all verified:

- `raw_min == op_point` **by construction**, dense or sparse — the fit-convention invariant
  became deterministic, and the commit-time test asserts near-equality (`±0.01`, single-sourced
  as `OP_POINT_EPS` from the fitter so test and fitter cannot disagree).
- The original 200-point grid is **bit-identical** to an unanchored fit (prepend, not re-span):
  behavioral delta is exactly 0 for every score ≥ the sample minimum. Verified old-vs-new on
  one identical live cultural_discovery v5 pull (n=2,283): grid identical as suffix; below the
  sample minimum the delta is bounded by the old clip value `y[0]` (0.0044 normalized).
- The band `[op_point, sample_min)` becomes a linear ramp from percentile 0 instead of a clip —
  the honest reading: nothing in the reference population scored there.
- The bias signal that `raw_min` used to carry *incidentally* moves to the new
  `stats.sample_min` (lowest score actually observed), which is explicitly guarded (§5.2).

Scale check on "no behavior change": production data drift alone (26 new articles in 6 days on
cd v5's rolling window) moves the fitted curve by up to **0.195 normalized** — 44× the anchor's
maximum effect. Byte-identity of a refit against a committed file is therefore unachievable for
*any* fitter; the meaningful comparison is code-isolated (same input, old vs new code).

## 4. The fit convention (what the reference population must be)

**Population = production MEDIUM+ output of THIS filter version: `raw_weighted_average >= the
filter's op-point`, one `filter_version`, ≥ 200 articles, at the production base rate.**

Each clause exists because violating it produced a real failure:

- **`raw >= op-point`** — the population is "articles worth showing"; that is the ranking
  competition normalization arbitrates. Fitting lower puts sub-visibility content in the
  reference population (#161, §5.1). The fitter resolves the op-point from `base_scorer.py`
  `TIER_THRESHOLDS` via AST parse (the runtime source; `config.yaml` is documentation, is
  cross-checked, and has shipped stale values — 3.0 vs a live 4.0 on two filters).
- **One version** — different versions are different models with different distributions; a
  blend is bimodal and ranks this version's articles against another model's population. The
  live rolling window straddles cutovers: fitting nature_recovery v4 unscoped would pull in
  114,252 foreign-version articles. Default is scoped from the config's own version.
- **≥ 200 articles** (`MIN_NORMALIZATION_ARTICLES`, mirrored in the loader) — below this the
  CDF is sampling noise; the loader silently rejects and falls back, so a thin fit is a file
  that *looks* deployed and is inert.
- **Production base rate, never the enriched training/val set** — screen+merge and active
  learning make val sets ~30× richer in positives than production for a needle filter;
  a val-set CDF is not the population users see (tested: 54% of nature_recovery articles
  collapsed to one normalized value). Also tested-dead: z-score (skew → p95 reaches only
  6.84), p99 linear scaling (p90 → 1.94), full-corpus inference (costly and includes 90%+
  noise articles that are never shown).
- **New filter cold start:** don't wait weeks for live accumulation (nature ≈ 0.3% MEDIUM+ →
  3–4 articles/batch). Rescore a *production-representative historical harvest* with the new
  model to synthesize the production CDF **before go-live** (~145K articles to reach 200
  MEDIUM+ at 0.3%). Shipping raw while every other lens ships normalized under-ranks the new
  filter on every cross-lens surface for weeks (observed live, 2026-07-11: fresh v4 out-ranked
  by inflated still-in-window v2 scores → "no new nature articles" while v4 produced more
  genuine MEDIUM+ than v2).

## 5. Failure modes and the guard architecture

### 5.1 Fit below the op-point — NexusMind#161

nature_recovery v2 was fitted at `raw >= 1.5` (fit-set median 2.19). Doom articles the model
*correctly* scored 2.2–3.3 mapped to normalized 5.2–8.3 and reached the Recovery lens at up to
8.34/10. Misdiagnosed as a model failure; patched with a keyword cap that took 14 months to
retire (0 saves, 3 false positives in production). The model was never wrong — the reference
population was.

### 5.2 Fit population never reaches the op-point (biased sample) — NexusMind#205

foresight v1 was fitted from already-filtered output: lowest article 5.01. Everything the CDF
didn't cover clipped to ~0 — raw 4.60 → normalized 0.02. The loader now rejects
`raw_min > 4.5` (`MAX_NORMALIZATION_RAW_MIN`, strict `>`), but anchoring makes such files
*loadable* (`raw_min == op_point`), so the detection had to move with the signal: the fitter
hard-blocks `sample_min > 4.5` on the deploy path, and the invariant test asserts the same on
every committed package. **Residual, accepted gap:** a *subtly* biased sample (`sample_min ≤
4.5`, ≤ 0.5 above the op-point) is statistically indistinguishable from a legitimately sparse
needle fit — `sample_min` is recorded for audit, a > 0.5 gap warns, and representativeness
stays an operator check (rescore provenance, playbook §6).

### 5.3 The guard table

One contract, enforced at four layers. `--analysis-only` (which requires an `--out` that is
not, and does not resolve to, a file named `normalization.json`) is the ONLY relaxation, and it
exists so inspection fits of deliberately-bad populations remain possible without ever
producing a deployable file.

| Layer | Guard | Catches |
|---|---|---|
| fitter, pre-fit | deploy path requires a resolved op-point | unvalidatable fits (op-point is also what the test needs) |
| fitter, pre-fit | `--min-score` < op-point refused (`--allow-below-op-point` ⇒ analysis-only) | #161 |
| fitter, pre-fit | `--min-score` > op-point refused on deploy path | deliberate visible-band exclusion |
| fitter, pre-fit | anchor > 4.5 refused (advice: fix `TIER_THRESHOLDS`, not `--min-score`) | op-point itself above the loader bound |
| fitter, pre-fit | `--all-versions` / `--allow-thin-fit` ⇒ analysis-only; `--out` cannot target another package's `normalization.json` | version blends, thin fits, cross-package writes |
| fitter, load | non-finite scores excluded (they pass `wa < min_score` and would inflate the article floor); only this filter's attribute block matched (hyphen/underscore-normalized) | NaN-shrunk fits, foreign-filter blends |
| fitter, post-fit | `abs(raw_min − op_point) ≤ 0.01`; `sample_min ≤ 4.5` | anything that slipped through; biased samples (§5.2) |
| commit time | `tests/unit/test_normalization_invariant.py` — same two assertions, EPS imported from the fitter, globbed over every `filters/*/v*/normalization.json` (no hand-maintained list); exemptions must cite their incident and go stale-red if they start conforming | drifted or hand-placed files, whatever their origin |
| load time (NexusMind) | `n_articles ≥ 200`; `raw_min ≤ 4.5` (else silent fallback to `score_scale_factor`); missing file → raw passthrough | thin fits, gross drift, safe rollout |

Meta-lesson (2026-07-16, worth keeping): **a root fix that changes what a value means silently
retires every guard that keyed on that value for a different purpose.** Anchoring fixed
`raw_min` drift and thereby disabled the biased-sample detection that `raw_min > 4.5` had been
providing by accident. Found by an adversarial reviewer executing attack invocations, not by
the fix's own verification gates — the gates tested what the fix should do, not what the old
code incidentally protected.

## 6. Reproducing for a new (or retrained) filter

Prerequisites: `base_scorer.py` has one literal `TIER_THRESHOLDS`; `config.yaml` has
`filter.version` matching what production writes (e.g. `"4.0"`); calibration already fitted
(normalization consumes *calibrated* weighted averages).

**A. Established filter, ≥ 200 live production MEDIUM+ articles:**

```bash
MSYS_NO_PATHCONV=1 PYTHONPATH=. python scripts/normalization/fit_normalization.py \
    --filter filters/{name}/v{N} --ssh sadalsuud \
    --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/{name}
```

The fitter resolves op-point and version itself and refuses to run when it can't. Legitimate
deploy-path extras are only `--filter-version` (override the config's version string) and
`--n-bins`; a `--min-score` is allowed only equal to the op-point (below is refused, above is
refused). `--allow-*`/`--all-versions` all force the analysis path by design.

**B. New version (cold start):** rescore a production-representative historical harvest with
the new model until ≥ 200 MEDIUM+ accumulate (playbook §6 has corpus locations), write the
scored output as `filtered_*.jsonl`, then fit with `--data-dir` instead of `--ssh`. Ship
`normalization.json` in the filter package *at* go-live, not after.

**Verify (all four, every time):**
1. Fitter log: article count, `raw_min == op_point`, `sample_min` close above it, and the
   sample-mapping table looks sane (op-point → 0.0; top of range → ~10).
2. `PYTHONPATH=. python -m pytest tests/unit/test_normalization_invariant.py` — green, and
   your filter appears in the parametrized list (the glob picked it up).
3. Commit `normalization.json` with the filter package; deploy to both targets.
4. Post-deploy: one live article's output shows `normalization_method: "percentile"`,
   `raw_weighted_average` populated, and tier coherent with the *normalized* score.

**Refit when:** the filter is retrained (new model = new distribution — always, a new version
NEVER inherits the old version's file), pass rate drifts > 20% relative, or annually.

## 7. Numbers for the article (all reproducible from committed artifacts)

- 10 fitted packages in-repo; every conforming one has `raw_min` within +0.0006 of its
  op-point (pre-anchor fits) or exactly on it (anchored). Three exemptions, each a preserved
  incident: foresight v1 (5.01, #205), nature_recovery v1/v2 (1.51/1.50, #161).
- #161: fit floor 1.5 vs op-point 4.0 → doom at raw 2.2–3.3 surfaced at 5.2–8.3; 14-month cap.
- #205: `raw_min` 5.01 → raw 4.60 → normalized 0.02.
- Anchor inertness: behavioral delta 0 above sample_min; ≤ 0.0044 below (cd v5, n=2,283).
- Data drift dwarfs code effects: 0.195 normalized from 6 days of window roll (44×).
- Review hardening: 3-model battery, 11 findings, 1 regression-created-by-the-root-fix
  (§5.3 meta-lesson); 6 consecutive review rounds each found defects in the prior round.
- Needle economics: 0.3% MEDIUM+ → ~145K rescored articles for a 200-article fit population.

---
*History: docs/adr/014 (2026-03-30, decision) → score_scale_factor retired → #161/#205
incidents → fit-convention made executable (2026-07-14) → op-point anchor + guard architecture
(2026-07-16, `docs/normalization-deploy-hardening-plan.md` Fix A addendum).*
