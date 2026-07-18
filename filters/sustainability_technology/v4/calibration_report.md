# Solutions v4 — Calibration Batch Report (2026-07-17)

**Status: batch COMPLETE, corpus re-score NOT started (engineer hold).**
This is the durable record; the raw sample and scored outputs live in
`datasets/calibration/` (gitignored per repo policy). Every number below was
independently re-verified from the on-disk artifacts by a claims-verification
agent (14/14 verified, including a live sadalsuud re-count).

## Why this batch matters beyond v4

This is the **ADR-020 validation case**: multi-oracle calibration scoring +
agent judging on the disagreement set, following cd v5's playbook. Outcome
feeds the PROVISIONAL → Accepted decision on ADR-020.

## Production context (investigated 2026-07-17, engineer-prompted)

ovr.news merges TWO scorers into the Solutions lens (`filters.ts:34-35`):
`sustainability_technology` v3 and `foresight` v1. Over the 24h before the
batch, foresight supplied **934** ovr-visible articles (wa ≥ 4.5) vs sustech's
**88** (~91% of the tab). Foresight also runs on a generous `scale_factor`
fallback (its CDF was rejected by the #205 raw_min guard). v4 replaces BOTH
scorers, so v4's capture of foresight-shaped content decides the tab's volume.

## What was scored

350 articles, 4 buckets (as-run composition in `config.yaml ::
calibration_batch`; deviations from the original 300-article spec documented
there): top-100 ST v3, top-100 foresight v1, 100 raw stream (random, seed 43),
top-50 belonging v1 (community-skewed). Sampled from ~134K unique production
articles (82 batches, 2026-07-03 → 07-17, sadalsuud). Both oracles scored the
same 350 with the same prompt (`prompt-compressed.md`):

| Oracle | Cost | Errors | Notes |
|---|---|---|---|
| DeepSeek V4 Flash (`deepseek-chat`) | $0.43 | 0 | 23% cache hit |
| Gemini 2.5 Flash (OpenAI-compat endpoint) | $0.56 | 40 transient (all recovered on retry) | needed `--max-tokens 16384` — reasoning tokens share the completion budget and truncate JSON at 4096 |

Scoring tool: `scripts/score_deepseek_production.py` (generalized 2026-07-17:
`--config/--base-url/--key-name/--max-tokens`, evidence + solution_type
passthrough). Analysis: `scripts/calibration_solutions_v4.py`.

## Decision-criteria tally (DeepSeek labels)

| Criterion | Result |
|---|---|
| Step-1 resolves >50% of raw stream to not_a_solution | **PASS** — 88% (Gemini 71%) |
| Cap adherence (arithmetic clamps, 2026-05-29 gotcha check) | **PASS** — 0 violations (Gemini: 2 → FAIL) |
| No bimodal per-dim distribution | **Mostly pass** — concreteness valley at 3-4 between peaks 0-2 / 5-7; watch |
| Mid-range >15% mass | **PASS** on type-matched populations (community dim: 35% mid among community/hybrid; governance: 55% among governance/hybrid) |
| Type distribution ~40/30/30 | tech 46% / gov 20% / comm 17% / hybrid 16% — governance lighter |
| Foresight capture (numeric gate) | **ENGINEER DECISION** — 31/100 killed at Step 1; survivors median batch percentile 38; 18/69 ≥ 4.5 raw |
| Pure-tech ≥60% at ≥7.0 | **FAIL — gate unsatisfiable as written** (0/95; ceiling arithmetic: pure-tech max 7.5 requires 9.33 avg). Gate must be rewritten (rank-based) or weights rebalanced |

Key distribution facts: DeepSeek max weighted average anywhere = **5.80**
(score compression is real); cross-oracle per-dim Pearson 0.64–0.76, wa MAE
1.10, 62/350 Step-1 flips.

## Oracle bake-off verdict (ADR-020 judging, 2 independent judges)

**Both judges recommend DeepSeek** (consistent with cd v5):

- **Editorial judge** (per-article on the top-30 disagreement set): DeepSeek 19,
  Gemini 7, toss-up 4. Gemini's systematic biases: Step-1 over-inclusion
  (culture/heritage/op-eds scored as solutions — lens-bleed) and an
  equity_access halo (8-9.5 on any marginalized-group article, 10% of its
  equity mass at 9-10). DeepSeek's bias (strict scope) matches the lens line;
  its cost is a small recall loss on borderline governance/lab content.
- **Label-quality judge**: DeepSeek follows the mechanical rules (router, type
  tags, clamps: 0 cap violations vs 2; hybrid tag 25 vs 69 — Gemini violates
  the tech-vs-hybrid tiebreak). DeepSeek's compression is monotone → benign
  under per-dim isotonic calibration; Gemini's false Step-1 passes are
  non-monotone label noise no calibration can remove. Do NOT average Gemini
  runs (bias, not noise — feedback-oracle-bias-vs-noise).

DeepSeek's known defects (fix in the prompt before corpus re-score):
1. Over-zeroes crisis-with-mediation / proposal shapes the router says should
   route to Flag A (bounded: correct label is capped ≤ 4.0-5.0 anyway).
2. Zeroed two genuine governance solutions (NZ legal-personhood reform,
   Ethiopia's deployed wheat program) — add a reinforcement line.
3. Scored a scraped cookie-consent page from its headline (anti-hallucination
   violation) — that's an INGESTION bug: add a scrape-junk check before
   oracle scoring.
4. Under-fires corporate_pr (5 vs Gemini's 53; judges found Gemini's
   aggressiveness partly right) — one line encouraging the flag's own test.

## Weight-vector analysis (labels are per-dim; weights are runtime — changeable without re-labeling)

Share of bucket ≥ 4.5 raw (DeepSeek, Step-1 survivors):

| Bucket | config weights | tech_rebalanced (.25/.25) | type-renormalized |
|---|---|---|---|
| st_v3_top100 (95 live) | 20 | 40 | **65** |
| foresight_top100 (69 live) | 18 | 20 | 22 |
| belonging_top50 (23 live) | 7 | 7 | 7 |

Type-renormalization (divide by applicable weight mass) restores tech ranking
best; nothing reaches 7.0 under config weights (absolute compression), which
percentile normalization at deploy largely neutralizes for ovr ranking —
but the config's absolute-tier gates need rewriting regardless.

## Engineer decisions — RESOLVED 2026-07-18

1. **Ratify DeepSeek as v4 oracle — DONE.** Both judges, cd v5 precedent,
   conservative-oracle rule. Single-run (not k=2); the compression is monotone
   and calibration-benign, so the k=2 majority-vote hedge was judged unneeded.
2. **Accept the thinner-but-cleaner tab — DONE.** Proceed with DeepSeek's strict
   scope; the foresight "loss" is mostly correct lens-bleed rejection. No
   recall-side prompt revision beyond the governance-recall reinforcement in
   fix (2) below.
3. **Weights/gates — DEFERRED to eval time (as designed; does not block the
   re-score).** The unsatisfiable pure-tech ≥7.0 gate still needs a rank-based
   rewrite and the config-vs-type-renormalized weighting choice still stands —
   both decidable post-labelling since labels are per-dim.
4. **Apply the 4 prompt/pipeline fixes, then re-score — fixes DONE 2026-07-18;
   re-score BLOCKED on corpus availability (see below).** The four fixes are
   applied and verified end-to-end against the live DeepSeek oracle (5-article
   smoke test: scrape-junk skipped without being scored; a governance op-ed that
   previously risked a false-zero scored governance_intervention_strength 6.5):
   - **(1) router-crisis** — "default to pass on mediation/proposal/response
     shapes; when uncertain between Step 1 and Flag A choose Flag A" line added
     to the Step-1/Flag-A router.
   - **(2) governance-recall** — legal-status/rights reforms (legal personhood,
     statutory rights) and deployed government programs with real output added
     to STEP 1 IN SCOPE as explicit do-not-zero cases.
   - **(3) corporate_pr** — "apply this test readily; it is the common case"
     encouragement added to Flag C.
   - **(4) scrape-junk** — `is_scrape_junk()` ingestion check
     (`ground_truth/text_cleaning.py`) wired into
     `scripts/score_deepseek_production.py` before oracle scoring; skipped rows
     are recorded (no analysis field) and counted/logged, never sent to the
     oracle. Unit test: `tests/unit/test_scrape_junk.py` (11 cases).

## BLOCKER — corpus re-score cannot run yet (2026-07-18)

The re-score reads article text from `datasets/scored/sustainability_technology_v3.jsonl`
(10.6K) + `datasets/scored/foresight_v1.jsonl` (3.5K) (RUNBOOK corpus convention).
Neither file is present on this host (`datasets/` is gitignored), on sadalsuud
(`~/local_dev/NexusMind/data/filtered/` holds only the production stream, not the
fixed training corpora), or in the veen-storagebox top-level backups. The
gpu-server — where training data lived and where training must run — is currently
ssh-unreachable (`hcl@gpu-server: Permission denied (publickey,password)`).

**Needs the engineer to either** (a) point to / restore the two scored corpus
JSONLs so the ~$10-15 DeepSeek re-score can run locally from this host, and/or
(b) restore gpu-server access (required for training regardless). Everything
upstream of the corpus is done and committed.

## Review provenance

- Round-1 prompt review: 3 agents (contract, oracle-behavior, editorial) —
  ~15 fixes applied before any spend.
- Round-2 review of the fixes (2026-07-17 wrap-up battery, 4 agents /
  2 models): 3 defects found in round-1 fixes (opinion-vs-router
  contradiction; community-governance change not fully propagated;
  proposed-bill anchor mismatch) — all fixed; code review of both scripts
  clean; claims verification 14/14; the round-2-finds-defects-in-fixes
  pattern held an **8th** consecutive time.
