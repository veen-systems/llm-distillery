# Cultural Discovery Filter v5 — Calibration Report

**Date:** 2026-05-31 (draft, in progress)
**Oracle models:** Gemini Flash 2.5 + DeepSeek V4 Flash + Qwen3:14b (Ollama, gpu-server) + Phi4:14b (Ollama, gpu-server) — multi-oracle batch per ADR-020 draft
**Status:** 🟡 DRAFT — multi-oracle pass in progress (Qwen3 + Phi4 batching). Final Ready/Review/Block recommendation pending consensus + agent judges.
**Target deployment:** ovr.news Discovery tab (per ADR-038)
**Calibration sample:** 522 articles (canonical IDs frozen at `datasets/scored/cd_v5_522_for_softpenalty_rescore.jsonl`) = 49 hard-negatives (v5 prompt v1, 2026-05-29) + 473 active-learning lane (originally v4-scored, re-scored under v5 prompt)

---

## Executive Summary (PENDING FINAL DATA)

**Provisional verdict (pre-Qwen3/Phi4):** Strong signal favoring **DeepSeek V4 Flash** as production oracle for v5 retrain.

Evidence stack so far:
- Per-oracle accuracy on agent-judged truth set (n=30 disagreement cases, Opus agent): **DeepSeek 80.8% vs Gemini 19.2%** (4× accuracy gap)
- Earlier handjudge_30 (Opus agent, n=22): DeepSeek 12 / Gemini 6 / Unclear 4
- Pool A spot-check (Opus agent, n=15, false-negative check on DS): 13/15 CORRECT, 1 WRONG (Greek 25-March schoolchildren parade missed as G)
- Pool B spot-check (Opus agent, n=15, false-positive check on DS): 11/15 CORRECT, 4 WRONG (above 20% threshold but concentrated in K-boundary cases)
- Haiku cross-validation of Opus on handjudge_30: 77% agreement → agent layer validated
- Dimension redundancy: **DeepSeek 20%** pairs above |r|=0.7, **Gemini 60%** — DS scores more orthogonal (better student signal)
- F-K firing rate: Gemini-v3 (post-tightening) still 49.8%; DeepSeek-v3 29.7%. Tightening closed gap partially but not fully — supports the "Gemini's aggressive reading is stable disposition, not prompt-fixable" interpretation
- Cost: ~$2 (DS direct, with auto-caching) vs ~$15 (Gem Batch) for full 8K retrain

**Final decision deferred** until Qwen3 + Phi4 batch oracles complete + 4-oracle consensus + Opus/Haiku agents adjudicate hard cases.

---

## Problem Statement: Why v5 Was Needed

### v4 in production: discovery-lens leakage (#62)

The currently-deployed cd v4 model systematically scored institutional/reckoning content too high on the ovr.news Discovery tab. Examples leaking to production with weighted_avg ≥ 7.0:

| Article | v4 prod score | Issue |
|---|---|---|
| Pope Leo XIV apologizes for Church role in slavery | 9.65 | F: historical_harm_reckoning |
| Brussels cathedral pogrom-apology plaque | 9.08 | F |
| Belgium convicted: removing mixed-race children from mothers in colonial Congo | 8.37 | F |
| Antwerp memorial to Congolese WWII victims | 8.37 | G/F borderline |
| Dutch slavery toll five times official figure | 8.53 | F |
| Memorial unveiled to Congolese people who died at Antwerp World's Fair | 8.37 | G |

These are institutional acknowledgments of known wrongs — *reckoning trajectory*, not *discovery trajectory*. Per Discovery's "past opening up" bias-correction framing (ADR-038), they should land elsewhere (perhaps Thriving for "rights advancing" framing) — but with no lens-fit mechanism shipping, they leak into Discovery.

The downstream ovr.news Chief Editor LLM gate was rejecting ~38% of cd v4 candidates to fix this — meaning the scorer's signal was poor. v5 moves the policy upstream to the scorer itself.

### v5 design intent

Add five new pre-classification trigger flags (F/G/H/I/K) that *demote* (originally cap, now penalty per ADR-015) articles whose trajectory is reckoning / commemoration / perpetrator / decline / launch. Carve-outs preserve in-scope content (repatriation tied to commemoration, victim names surfaced for first time by local research, explainer pieces about commemorative practice mechanics).

---

## Calibration Process

### Iteration 1: Hard-cap mechanism (2026-05-29)

- 49 hard-negatives (`datasets/raw/cd_v5_hard_negatives_candidates.jsonl`) collected from production v4 leakage examples
- 473 active-learning lane articles re-scored under v5 prompt
- Mechanism: `max_score = N` (clamp all dims to N)
- Outputs: `datasets/scored/cd_v5_hard_negatives/`, `datasets/scored/active_learning_cd_v5_rescored/`

### Iteration 2: Soft-penalty conversion + G carve-out broadening (2026-05-30)

- **Critical lens-design audit** found Antwerp/Stolperstein/Muslim-memorial articles hitting G cap despite arguably falling in carve-out intent → G carve-out broadened to include local-journalism victim research + commemorative-practice explainers + first-of-kind regional practices
- **Soft-penalty conversion per ADR-015** (cliffs hurt MAE; thriving v1 was parked at MAE 0.94 for this failure mode). F/G/H/I/K converted from `max_score` (clamp) to `penalty` (subtract from each dim, floor 0). Penalty values: F=2.5, G=2.5, H=3.5 (strictest), I=2.0 (lightest), K=2.5.
- Same 522 re-scored: `datasets/scored/cd_v5_softpenalty_rescored/`
- DeepSeek V4 Flash validation run: `datasets/scored/cd_v5_softpenalty_deepseek/` — finding: Gemini 60% F-K firing rate vs DeepSeek 26% (same prompt, 2.3× difference)

### Iteration 3: OUT-OF-SCOPE restructure + F-K tightening (2026-05-31)

- **OUT-OF-SCOPE split** into CATEGORY A (inherently low-substance, max_score) vs CATEGORY B (high-substance wrong-trajectory, penalty) with explicit "may fit other ovr.news lenses" framing. Fixed Gemini's spurious reclassification of political_conflict / tourism_fluff articles as cultural_discovery.
- **F-K trigger tightening** per Opus hand-judge agent finding (DS 12, Gem 6, Unclear 4 of 22):
  - K narrowed: explicit anti-triggers — award ceremonies, individual speeches, opinion essays, book/film/theater reviews of already-released works, retrospective coverage, obituaries are NOT K
  - I tightened: explicit "ends on rebound" carve-out + paleontological/archaeological prehistoric-extinction exclusion + "READ THE FINAL PARAGRAPHS" test
  - G explicit obit exclusion: "G does NOT fire on obituaries of recently-deceased public figures"
- 522 re-scored:
  - Gemini v3: `datasets/scored/cd_v5_softpenalty_rescored_v3/`
  - DeepSeek v3: `datasets/scored/cd_v5_softpenalty_deepseek_v3/`

### Multi-oracle batch calibration (PHASE — in progress)

Per ADR-020 draft methodology: extend single-oracle Phase 3 to 4-oracle batch + 2-agent adjudication for needle-in-haystack filters with complex penalty mechanics.

| Oracle | Source | Status |
|---|---|---|
| Gemini Flash 2.5 v3 | cloud (Google) | ✅ 522/522 |
| DeepSeek V4 Flash v3 | cloud (DeepSeek) | ✅ 522/522 |
| Qwen3:14b | gpu-server Ollama | 🟡 in progress (~30/522 at 11:00) |
| Phi4:14b | gpu-server Ollama | ⏳ queued after Qwen3 |
| Opus agent (hard cases) | Claude Code harness | ⏳ awaits consensus |
| Haiku agent (hard cases) | Claude Code harness | ⏳ awaits consensus |

---

## Findings So Far (single + two-oracle level)

### Per-oracle flag-firing rates (post-tightening, v3)

| Oracle | F-K rate | A-E rate | cultural_discovery count |
|---|---|---|---|
| Gemini Flash 2.5 v3 | 49.8% | 9.0% | 86 |
| DeepSeek V4 Flash v3 | 29.7% | 8.6% | 135 |
| (Gemini hard-cap v1, reference) | 62.6% | 7.9% | 121 |

The F-K tightening reduced Gemini from 62.6% → 49.8% (closing ~25% of gap with DS) but didn't fully converge.

### Dimension redundancy (per-oracle)

| Oracle | Pairs above \|r\|=0.7 | Redundancy ratio | Max pairwise \|r\| |
|---|---|---|---|
| Gemini-v3 | 6/10 | **60%** | 0.844 (dn ↔ eq) |
| DeepSeek-v3 | 2/10 | **20%** | 0.841 (dn ↔ eq) |

DeepSeek produces more orthogonal dim signals (better for distilled student training — finer-grained distinctions to learn).

### Gatekeeper enforcement check

Both oracles: **0 violations** (articles with evidence_quality < 3.0 that exceeded overall=3.0 cap). ✅

### Tier distribution vs target

| Bin | Gem-v3 | DS-v3 |
|---|---|---|
| very_low | 38.5% | 41.4% |
| low | 30.5% | 29.5% |
| medium | 19.9% | 19.7% |
| high | 10.9% | 9.2% |
| very_high | 0.2% | 0.2% |

Both reasonable for needle filter. very_high count low (~1/522) reflects the calibration sample's enrichment toward borderline-and-negative content — broader retrain corpus will have more positives.

### Agent verdicts on disagreement subsets

**handjudge_30 (Opus, n=22 cd v5 F-K disagreements):** DS 12 / Gem 6 / Unclear 4
**Haiku cross-validation of same 22:** 77% exact agreement with Opus, 95% incl. shared ambiguities — **agent layer reliable**
**broader 2-oracle disagreement (Opus, n=30 stratified, after v3 tightening):**
- DS correct 21, Gem correct 5, Unclear 2, Both wrong 2
- Per-oracle accuracy: DS 80.8% / Gem 19.2% (4× gap)
- Per-flag pattern: Gem 0/9 on G (over-fires on obits, statues, rituals, UNESCO recognition); 0/6 on K (recurring ceremonies, live festivals, delivered research); 1/6 on I (ignores rebound carve-out)
**DeepSeek spot-check Pool A (false-negative, Opus, n=15):** 13 CORRECT / 1 WRONG / 1 UNCLEAR — restraint genuine, not leakage
**DeepSeek spot-check Pool B (false-positive, Opus, n=15):** 11 CORRECT / 4 WRONG — above 20% reconsider threshold; concentrated in K boundary (award ceremonies, delivered outcomes) and individual-allegation F mis-bucketing

---

## Bugs Fixed During Calibration

| Bug | Where | Fix |
|---|---|---|
| G carve-out parsed too narrowly — Antwerp 7-Congolese memorial, Stolperstein explainer, Muslim WWII memorial, Ghanaian genocide monument incorrectly hit G cap | `prompt-compressed.md` G section (line 224-229) | Mirror F's broadening pattern: explicit INCLUDING for local-journalism victim research, commemorative-practice explainers, first-of-kind regional practices |
| Hard-cap mechanism creates cliff (ADR-015 failure mode — thriving v1 MAE 0.94) | `prompt-compressed.md` F-K definitions | Soft-penalty conversion: subtract from each dim, floor 0; preserves gradient |
| Gemini reclassifying tourism_fluff / political_conflict articles as cultural_discovery under new framing (A-E under-application) | `prompt-compressed.md` Section 1 OUT-OF-SCOPE block | Split into CATEGORY A (max_score) vs CATEGORY B (penalty); explicit "may fit other lenses" is downstream-routing info, not penalty escape |
| K (launch_announcement) over-fires on event coverage: theater premieres, film reviews, opinion essays, awards | `prompt-compressed.md` K section | 7 explicit anti-triggers added; K narrowed to "future-tense institutional initiatives" |
| I (decline_loss) ignores "ends on rebound" carve-out | `prompt-compressed.md` I section | Explicit READ THE FINAL PARAGRAPHS test + 4 carve-out examples (oldest American mall, Catholic resurgence, Neanderthal extinction, vanishing Welsh dialects) |
| G fires on obituaries of public figures despite obit detector being upstream | `prompt-compressed.md` G section | Explicit lead-in: "G does NOT fire on obituaries" with named examples |

---

## Multi-Oracle Consensus + Per-Oracle Alignment (PENDING — Qwen3/Phi4)

Will populate when 4-oracle batch completes:
- 4-oracle consensus per dim (median) + per content_type (majority ≥3/4)
- Hard-case count (articles where <3/4 agree on content_type)
- Per-oracle alignment with consensus: per-dim Pearson, content_type agreement rate
- **Production-oracle decision rule** (per data-analyzer reviewer): Bayesian update on agent-judged hard cases (truth set), not just consensus-alignment (which would select for centrality, not accuracy)

---

## Decision Criteria

| Threshold | Met so far? |
|---|---|
| Success rate >95% (no JSON parse failures, no oracle refusals) | ✅ Gem v3 100%, DS v3 100% (522/522 each, 0 errors) |
| Score distribution non-degenerate (not all 0s or 10s) | ✅ both oracles span 0-9.5 across all dims |
| Gatekeeper enforcement working | ✅ 0 violations both oracles |
| Tier distribution reasonable | ✅ no single bin >70% |
| Pool A false-negative rate ≤ 20% | ✅ DS Pool A: 6.7% (1/15) |
| Pool B false-positive rate ≤ 20% | 🟡 DS Pool B: 26.7% (4/15) — above threshold but K-boundary cases |
| Agent layer validated (Haiku-Opus agreement ≥ 75%) | ✅ 77% |
| 4-oracle consensus computed | ⏳ pending Qwen3 + Phi4 |
| Per-oracle agent-judged accuracy > 75% on truth set | ✅ DS 80.8%, ❌ Gem 19.2% |

---

## Recommendations (PROVISIONAL)

### Immediate
1. **Wait for Qwen3 + Phi4 completion** — closes the 4-oracle batch calibration loop. Either confirms DS as outlier-correct (3/4 oracles align conservative) or surfaces DS as outlier-wrong (3/4 align with Gemini's aggressive reading).
2. **Fire Opus + Haiku agents on consensus hard cases** when batch oracles complete.
3. **Compile final verdict + Ready/Review/Block** based on 4-oracle data.

### If DS confirmed as production oracle (likely):
4. Re-score 8K v4 records with DeepSeek V4 Flash under the v5 prompt (cost ~$2, time ~2hr with concurrency)
5. Re-run merge + prepare_data → splits in `datasets/training/cultural-discovery_v5/`
6. Train Gemma-3-1B + LoRA on gpu-server (Phase 5)
7. Fit calibration.json (Phase 6a) + normalization.json (Phase 6b, after production CDF accumulates)
8. Hub upload + NexusMind deploy

### If Qwen3/Phi4 align with Gemini (3/4 aggressive):
9. Reconsider — DS may be the outlier. Investigate hand-cases more deeply, possibly tighten F-K further, or accept Gemini's reading style as the production standard.

### v6 future iterations
- The K-boundary cases that broke Pool B (award ceremonies, delivered outcomes) suggest K's definition still leaves ambiguity. Consider further narrowing or splitting K into K1 (institutional rollout) and K2 (programmatic announcement).
- Investigate whether the conservative-oracle principle generalizes to other needle filters (foresight, belonging, nature_recovery) — would inform standardizing ADR-020 methodology.

---

## Cost Summary (calibration phase, 2026-05-30/31)

| Item | Cost |
|---|---|
| Gemini Flash 2.5: 522 × 3 prompt iterations | ~$5.50 |
| DeepSeek V4 Flash: 522 × 3 prompt iterations | ~$1.50 |
| Qwen3:14b + Phi4:14b on gpu-server | ~$0 (self-hosted, gpu-server time) |
| Opus agent (hand-judge + Pool A + Pool B + broader truth set) | within Claude Code harness allowance |
| Haiku agent (cross-validation) | within Claude Code harness allowance |
| **Total calibration cost** | **~$7** plus gpu-server time + harness allowance |

vs the eventual production retrain: ~$2 (DS direct) or ~$15 (Gem Batch) for 8K-article corpus.
