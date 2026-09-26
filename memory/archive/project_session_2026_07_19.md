# Session 2026-07-19 — Solutions v4 corpus build EXECUTED (free), 4 poisons caught, turnkey to Part-B

**Branch:** `solutions-v4-calibration`. **Spend this session: $0** (all free telemetry).
**State: corpus build is one DeepSeek call from Part-B.** No model yet.

## What happened

Unblocked the two engineer inputs from 2026-07-18 (community seeds + exec defaults) by
actually running the free corpus build on gpu-server, and it turned into a four-poison
cleanup — each caught *before* any oracle spend.

**The reframe (engineer prompt):** production `pre_enrich` enriches every short article to
full text *before* scoring (`NexusMind scripts/main.py:821`). The plan had **no enrichment
step** → building on RSS stubs would bake in train/serve skew. Pivoted to **enrich-first**
from NexusMind's warm cache (118k entries, 81% hit) via the production `ArticleFetcher`.

**Pipeline run (sadalsuud raw pool → gpu-server GPU):**
- Enriched 171,050 survivors (121,888 to full text). Embedded on gpu-server GPU (~3 min vs
  ~4 h CPU on sadalsuud — access + env now in `gpu-server.md`).
- e5 per-type screening (tech/gov/community centroids), language-stratified.

**Four poisons caught + fixed (all on the free pass):**
1. **Thin RSS stubs** → enrich-first (above).
2. **Multilingual skew**: candidates were 2–10% non-EN vs 42% pool (nature_recovery trap in
   embedding form) → en/non-en stratified selection → 41.6% non-EN.
3. **Near-dup over-drop**: 0.93-vs-calib dropped 18% (topical neighbours = positives) → 0.97.
4. **Consent-wall poison**: enrichment itself introduced Google consent pages as "content"
   for 17.3% of the pool → **99% of candidates were junk** → reverted to raw stubs + detector
   → 0%. (See gotcha-log; also a live NexusMind `should_replace_content` bug.)

**Community seeds (the one manual-judgment cell):** 21 mined from the pool + **12 external
high-band** (Paris participatory budgeting, Nepal forestry, Brazil health agents, Amul,
Bangladesh CPP, Namibia conservancies, Rajasthan johads, US CLTs, Chile fisheries…) fetched
+ verified by a research subagent. = **33 community seeds.**

**Result:** Part-A gate PASS on 7,475 candidates (13k pre-dedup, ~40% cross-type overlap).

## Review battery (3 reviewers, Opus+Sonnet, reproduction-based) — verdict: corpus SOUND

- **Correctness (Opus):** final artifacts clean + row-aligned (fresh embed, no stale reuse);
  found 2 latent control weaknesses → fixed: Part-A "seeds present" gate was tautologically
  true; `--reuse-embeddings` had no fingerprint. Both fixes **watched failing** (round 2).
- **Reproduction (Sonnet):** 8/9 numbers reproduced exactly (re-embedded calib for near-dup);
  caught my false "0 Swahili in candidates" → real **10/331** (check-script bug).
- **Methodology (Opus):** execute after 2 free fixes, no redesign. → both applied:
  **#2 DONE** — drew a 1,500-row random holdout, ran train↔holdout near-dup, dropped **42
  syndicated leakers** (7,475→7,433). **#1/#3 STAGED turnkey** — `partB_gate.py` (counts
  non-EN *positives*, closing the gate blind spot), `partB_sample.py` (160-row sample drawn),
  `sample_negatives.py` (excludes reverted stubs). Full record: `DATA_SETUP_PLAN.md` Round 3.

## Also produced (docs)

- **`docs/ideas/access-bias-and-the-haystack.md`** — the paywall/consent walls *manufacture*
  part of the needle-in-haystack (non-random: they preferentially remove positives). Grew
  into **ovr position & proposition** material (the sorting: free=rage, paid=gated, a genuine
  dilemma not a morality play; ovr as counterweight to the *sorting*) + **3 article seeds** +
  a non-European-language source-expansion follow-up (Swahili: 331 in pool, 10 in candidates).

## Next session — turnkey to Part-B

Everything staged on `gpu-server:~/solutions_screen_work/`. The path is mechanical:
```
score partB_sample.jsonl (~$0.20)  →  python3 partB_gate.py partB_sample_scored.jsonl
   →  python3 sample_negatives.py <N from gate hint>  →  assemble final input
   →  full DeepSeek score (~$11–13, 7,433 cand + 33 seeds + negatives + holdout)
   →  prepare_data  →  train (gpu-server)  →  calibration  →  ground-truth gate (ADR-021)
```
Optional pre-spend: add non-EN boilerplate patterns to `is_scrape_junk`. Deploy: N/A this
session (no filter package/model/config/deploy-script touched).

## Cross-repo follow-up

**NexusMind enrichment bug**: `ArticleFetcher.should_replace_content` has no consent/paywall
guard → replaces real RSS summaries with Google consent pages for Google-News articles
(~17% of short articles). File an issue; it degrades live scoring input.
