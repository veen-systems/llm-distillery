# Session 2026-07-22 — Solutions v4 op-point 2.25, Hub published, 3-round review, DEPLOYED (armed for next cron)

**Branch:** `solutions-v4-calibration` → merged to `main` (pushed). **Spend: ~$0** (GPU rescore only; Hub free).
**State: solutions v4 committed to all 3 repos + pushed; deploy ARMED (fires on the next ~16:00 FluxusSource
cron). NexusMind `61ecc10`, ovr `c279dc4` (owner pushed) + `47cca67`, llm-distillery merged to main. Model
pre-placed on gpu-server, smoke-tested (wa 3.95 medium, dims differentiate). Retirement of sustech+foresight
is config-level (armed); package dirs KEPT on servers for rollback.**

> Update (session back-half): the "held for coordinated go" plan below was superseded — the owner returned,
> said "go ahead", and the cutover was EXECUTED: `deploy_to_nexusmind.sh` (Windows-path bug fixed to run on
> situla), clean staging (no weights, no obituary contamination), `test_filter_integrity` 8/8 + 872 unit
> tests green, model placed, smoke passed, all 3 repos pushed. Summarization bake-off moved to
> `ovr.news/docs/decisions/` + tracked as ovr.news #270. **Next session: verify solutions in the first
> post-16:00 `filtered_*.jsonl` → ADR-020 Accepted; then nr v4 #72 + the score_normalization.py sync.**

## What happened
Resumed at the solutions v4 deploy decision. Drove it end to end, then ran the engineer's requested
review loop (battery → fix critical→minor → battery → redo) to convergence, then prepped deploy.

**Deploy decision (engineer): op-point 2.25** over 3.0 / hold-for-v2. Compared to nature_recovery v4
(gate 0.65/0.85). 2.25 = best-F1 (recall 0.559 / prec 0.768 / F1 0.647, gate regenerated at 2.25).

**Built (all committed on the branch):**
- Op-point 2.25 → `config.yaml tiers.medium` + `base_scorer.py TIER_THRESHOLDS`; version 4.0.
- `score_scale_factor` 1.6093 → **1.0** (normalization.json is the scaling path; non-1.0 = the nr v2
  stale-inflation trap #167/#205).
- `normalization.json` fitted from a **40K non-commerce production rescore** (sadalsuud
  `content_items_*.jsonl`, seed 20260722 → 11,178 prefilter-passers → 536 ≥ 2.25). Anchored raw_min=2.25.
- `inference_hub.py` (`SolutionsScorerHub`). Hub `jeergrvgreg/solutions-filter-v4` **published + verified**
  (adapter hash == tested weights; card corrected to DeepSeek, no DRAFT).

**3-round multi-model review battery** (opus+sonnet+fable, adversarial verify, each finding by a
different model):
- **R1: 15 confirmed.** Scoring math CLEARED (no double-norm, ssf 1.0 correct, field-key `solutions`
  correct). Fixed: doc drift, wrong Hub card oracle, normalization provenance, + surfaced the
  raw-gate-vs-normalized-surfacing recall caveat.
- **R2: 31 confirmed, 15 defects-in-fixes.** CRITICAL: my R1 fail-closed `_resolve_filters` raise
  **halted the whole pipeline** + broke 2 tests — reverted (the existing `test_filter_integrity` is the
  right guard). Added `solutions` to the **missed `summarize.ts` production driver** + image/ops maps.
  Reverted the value-based artifact check (git-archive deploy already prevents lost-copy; it flagged the
  tracked nr v4 #72 gap). Fixed nr v4 + cd v5 Hub cards (same wrong-oracle bug).
- **R3: 7 confirmed, 0 blocking.** ovr `ScoreBlob` + `/lens` methodology page still used v3 dimensions →
  updated to solutions v4's 7 dims + nl/en translations. QA tooling + own exhaustive grep.

## Deploy state (HELD for coordinated go)
llm-distillery committed+pushed. ovr committed (`c279dc4`, not pushed). NexusMind: app.yaml +
main.py/filter_loader comment reverts staged (uncommitted). **`test_filter_integrity` is RED until the
solutions package is copied into NexusMind — this is the correct guard, resolves at deploy.**

**Coordinated cutover sequence (engineer, ~15 min):**
1. `deploy_to_nexusmind.sh --filter filters/solutions/v4` (copies package + `filters/common`, verifies,
   commits NexusMind WITH the staged app.yaml — atomic; `test_filter_integrity` then green).
2. Pre-place model: gpu-server `cp -r ~/llm-distillery/filters/solutions/v4/model
   ~/NexusMind/filters/solutions/v4/model` (survives the `*/model/` rsync exclude, checklist #5).
3. Smoke-test scoring on gpu-server (score a fixture; confirm sane).
4. Push NexusMind + ovr (`git push`) + merge llm-distillery branch → main. Next 4h cron deploys
   (CI-gated). foresight drains out of ovr's 10-day window automatically.
5. Live smoke on the next cycle's `filtered_*.jsonl`; ADR-020 PROVISIONAL→Accepted.

## Post-cutover ops note (2026-07-22 evening)
- **Smoke gate blocked the first cron** after `61ecc10`: retired sustech+foresight from
  `enabled_filters` but left their smoke fixtures → `deploy_filters.sh` name-alignment gate (fail-closed)
  aborted every cycle. Fixed in NexusMind `e2a102e` (repoint iron-air fixture → solutions, min_wa 2.5;
  drop foresight fixture). Fixtures now match enabled_filters 6/6. **Live smoke PASSED — `solutions
  wa=4.43 in expected range`; pipeline ran `['solutions', ...]`, sustech/foresight gone.**
- **First run w/ solutions is a one-time slow catch-up** (~1h20m+ vs ~16 min): 20,303 og:image backfills
  + 29,132 dedup clusters (10× normal) because solutions has no processing history. NOT a regression —
  next cron returns to normal. Expect one slow run per new-filter launch. See gotcha-log 2026-07-22.
- **git push once-and-for-all fix**: situla's github SSH path was fully broken (empty openssh_agent +
  GNOME-keyring gcr agent hangs on headless signing + passphrase-locked key). Routed git through the
  already-working `gh` token instead: `gh auth setup-git` + `git config --global
  url."https://github.com/".insteadOf "git@github.com:"`. All repos push over HTTPS now, no agent.

## Carried / report-only
- **nr v4 runs raw-passthrough in production** (no normalization.json, ssf 1.0 → method 'none';
  31,852/31,852 recent records). Tracked #72 — fit its normalization.json (content_items rescore, op 3.75).
- ovr content pages (`architecture.astro`, `lenses.astro`) + dev-analysis scripts + `db-articles.ts`
  narrow helper still say sustainability_technology — non-functional doc follow-ups.
- Recall caveat: production surfaces at effective raw ~2.64 (normalized tiering), so real recall < the
  raw-gate 0.559 — systemic, doesn't flip the 2.25 decision.
