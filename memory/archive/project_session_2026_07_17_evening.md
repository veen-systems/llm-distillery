# Session 2026-07-17 (evening) — Solutions v4: investigation, prompt, calibration batch

**Arc: #43 solutions v4 went from empty scaffold to calibrated-and-judged in one
session, $1.00 oracle spend, stopping exactly at the engineer sign-off gate.**

## 1. Foresight/Solutions mixing investigation (engineer-prompted)

Engineer's hunch confirmed and quantified: ovr.news maps BOTH
`sustainability_technology` AND `foresight` to the `solutions` tab
(`ovr.news/src/lib/data/filters.ts:34-35`); foresight v1 runs live in every
NexusMind 4h cycle. Last-24h production: **foresight 934 ovr-visible articles
(wa≥4.5) vs sustech v3's 88 — the Solutions tab is ~91% foresight-fed**, partly
because foresight runs on the generous linear `scale_factor` fallback (its CDF
was rejected by the #205 raw_min=5.01 guard). Consequence: v4 (which replaces
BOTH per the #43 Fork 3 sign-off) must capture foresight-shaped content or the
tab starves; normalization-at-deploy is mandatory. Verified live twice (claims
agent re-counted 934/88 on the same window).

## 2. Prompt drafted + two review rounds

`filters/solutions/v4/prompt-compressed.md` drafted (Step-1
scope check + deterministic Step-1/Flag-A router with opinion exception, Step-2
type tag with tech-vs-hybrid tiebreak, 7 dims, A/B/C soft caps with arithmetic
clamps, binding-clamp validation example, multilingual-safe critical filters).
Round-1 battery (3 agents: contract, oracle-behavior, editorial) → ~15 fixes
incl. a config `systemic_impact` description that contradicted its own
critical_filters, the `not_a_solution_article` inert-gate string, and the
gatekeeper `<=`-vs-runtime-`<` mismatch. Round-2 battery (wrap-up, 4 agents /
2 models) found **3 defects inside round-1's fixes** (pattern's 8th consecutive
hold) — all fixed. Code review of session scripts: clean. Claims verification:
14/14.

## 3. Calibration batch (ADR-020 validation case) — COMPLETE

350 articles (top-100 ST v3 + top-100 foresight + 100 raw + top-50 belonging
community; as-run composition recorded in config.yaml), scored by DeepSeek
($0.43, 0 err) AND Gemini 2.5 Flash ($0.56; 39 truncation errors → gotcha →
`--max-tokens` fix → all recovered). Analysis
(`scripts/calibration_solutions_v4.py`) + two-judge disagreement review:

- **Both judges → DeepSeek** (editorial 19-7-4; label-quality: rule-faithful,
  0 cap violations, compression is monotone→isotonic-benign; Gemini shows
  Step-1 lens-bleed + equity halo = uncalibratable bias).
- Criteria: raw-stream precision PASS (88%), cap adherence PASS, distributions
  healthy on type-matched slices; **pure-tech ≥7.0 gate empirically confirmed
  unsatisfiable** (0/95, max wa anywhere 5.80); foresight capture = engineer
  decision (31% Step-1 kill judged mostly-correct rejection of lens-bleed).
- Full record: `filters/solutions/v4/calibration_report.md`
  (durable; raw jsonl in gitignored `datasets/calibration/`).

## 4. Session engineering artifacts

- `scripts/score_deepseek_production.py` generalized (--base-url/--key-name/
  --oracle-label/--max-tokens; evidence + solution_type passthrough) —
  back-compat with cd v5 verified by code review.
- `scripts/calibration_solutions_v4.py` new (criteria tally, weight-vector
  alternatives incl. type-renormalization, cross-oracle stats, disagreement
  export).
- Gotchas logged: Gemini reasoning-token/max_tokens truncation; gate defined
  over a string the oracle never emits.

## Stopped at (engineer holds, in calibration_report.md "Open engineer decisions")

1. Ratify DeepSeek as v4 oracle. 2. Accept thinner-but-cleaner tab. 3. Rewrite
the unsatisfiable tech gate / choose weighting (post-hoc, doesn't block).
4. Then: 4 small prompt/pipeline fixes (router-crisis reinforcement, NZ/Ethiopia
recall line, corporate_pr encouragement, scrape-junk ingestion check) → corpus
re-score ST v3 10.6K + foresight 3.5K, DeepSeek off-peak, ~$10-15 → training.
ADR-020 graduation call comes after the full pipeline lands.
