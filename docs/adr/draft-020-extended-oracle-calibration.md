# ADR-020 (DRAFT): Phase 3 Oracle Calibration — Extended Methodology

**Date:** 2026-05-31
**Status:** DRAFT — under review
**Supersedes (in part):** docs/agents/filter-development-guide.md Phase 3 (extends, doesn't replace)
**Related:** ADR-015 (lenses as perspectives, not partitions), ADR-017 (inter-oracle MAE floor), ADR-010 (oracle consistency over data volume), ADR-021 (ground-truth deploy gate)

> **Amendment 2026-07-09 — separate NOISE from BIAS in oracle selection.** The multi-oracle
> calibration below (decision 2) implicitly optimizes *agreement/consistency*. nature_recovery
> v4 surfaced a sharp lesson worth folding in: **self-consistency (noise) and editorial
> alignment (bias) are orthogonal, and bias is the primary criterion.** DeepSeek vs Gemini on
> the same 65 articles — Gemini 2.2× *less* noisy (WA self-MAE 0.17 vs 0.38) yet systematically
> *more generous*, surfacing promo/how-to/listicle content the filter rejects. Selecting the
> low-noise oracle would have distilled the wrong judgment. Rule: **choose the oracle for bias
> (per filter), then cut noise by averaging k runs of the correctly-biased oracle — never by
> switching to a cleaner-but-differently-biased one.** Self-consistency is easy to compute and
> therefore seductive; bias requires reading the disagreement set. Composes with the
> conservative-oracle principle (decision 3). See `memory/feedback-oracle-bias-vs-noise`,
> augmented-engineering#26.

---

## Context

The original Phase 3 ("Oracle Calibration") in `docs/agents/filter-development-guide.md` prescribes a **single-oracle calibration** flow: sample 50-100 articles, score with one oracle (Gemini Flash or Pro), validate success rate / JSON parsing / distribution / gatekeeper / tier, then proceed to training data collection.

The cultural_discovery v5 calibration journey (2026-05-30/31) revealed five gaps in this flow:

### Gap 1: No ground truth means inter-oracle correlation is misleading
- ADR-017 already established that inter-oracle MAE is 0.6-1.0 per dim — frontier LLMs genuinely disagree.
- When choosing between two oracles, "DeepSeek agrees with Gemini at r=0.71" is meaningless without an external reference.
- We initially used Pearson-with-Gemini as a decision rule for DeepSeek validation. This was circular — it presumed Gemini-as-truth.

### Gap 2: Single-oracle calibration can't catch oracle-specific bias
- cultural_discovery v5: Gemini fires F-K penalty flags on 60% of articles; DeepSeek on 26% (same prompt). 
- Without a 3rd reference, we couldn't tell whether Gemini over-applies or DeepSeek under-applies.
- Hand-judging 22 disagreement cases (via opus agent) showed Gemini's over-application was the bug (DS 12 / Gem 6 / Unclear 4).
- This kind of failure is invisible to single-oracle calibration.

### Gap 3: Hard caps create gradient cliffs that hurt student MAE
- v5 originally specified `max_score = N` for F-K flags → all dims clamped to N.
- Per ADR-015, orthogonal lens design (which hard caps approximate) caused thriving v1 MAE 0.94 (vs uplifting v7's 0.67) — permanent park.
- The same shape applies to cd v5: hard cap = cliff = bimodal distribution = harder to learn.
- The fix is soft penalty (subtract uniformly, floor at 0) — preserves gradient.

### Gap 4: Flag-trigger language is read very differently by different oracles
- Same prompt, same articles, two oracles diverge 2.3× on F-K firing rate. 
- Iterating prompt tightenings (3 rounds for cd v5) closes the gap partially but not fully — some oracles inherently read more liberally than others.
- The right move is to pick the oracle most aligned with consensus, not iterate prompt forever.

### Gap 5: Spot-checking via casual eye-balling doesn't scale
- Generating a sample, reading 30 articles, judging consistently against a complex prompt — a Claude agent does this faster and more rigorously than a human can on the 5th iteration.
- Two complementary agent perspectives (Opus + Haiku, or two opus agents with different framings) triangulate well.

---

## Decision

**Extend Phase 3 with a multi-oracle calibration sub-phase, applied to needle-in-haystack filters with complex penalty/cap mechanics.**

### 1. Use soft penalty (subtract + floor 0) instead of hard cap (clamp) for trigger flags whose underlying content has real substance

**When to apply:**
- The flag is meant to demote content that's substantive but wrong-trajectory (e.g., slavery reckoning IS heritage-significant, but is reckoning not discovery)
- NOT for flags where content is genuinely low-value across all dims (tourism listicles, celebrity gossip — those get hard max_score caps)

**Mechanism:**
- Honest dim scoring (LLM gives 0-10 per dim based on intrinsic qualities)
- Apply penalty: `score = max(0, honest_score - penalty)`
- Multiple flags fire: highest penalty among them
- Mixed flags (max_score + penalty): clamp first, then subtract

**Why:**
- Preserves rank ordering across dims (heritage > novelty for slavery content stays meaningful)
- Avoids ADR-015 cliff failure mode
- Plays nicely with downstream lens-fit reassignment (when it ships) — capped articles stay in the candidate pool

### 2. Multi-oracle batch calibration (5-batch + 2-agent for needle filters)

**The 5 batch oracles** (score all calibration articles):
- 2 cloud oracles from different vendors: e.g., Gemini Flash 2.5 + DeepSeek V4 Flash
- 2-3 self-hosted oracles (Ollama on gpu-server): e.g., Gemma 3 27B + Qwen 3 14B + (optional Phi 4 14B)
- Different vendor + architecture + size mix triangulates better than 5 cloud APIs

**The 2 agent judges** (read disagreement subset with reasoning):
- Claude Opus via Agent tool (deepest reading)
- Claude Haiku via Agent tool (faster, independent perspective)
- Read the prompt fully, judge per the prompt as written

**Consensus mechanism:**
- Per dim: median of 5 batch oracle scores (robust to single-oracle outlier)
- Per content_type: majority vote (5 oracles → require ≥3 agreement; ties broken by agent judges)
- "High-confidence label" = ≥4 batch oracles agree; "Hard case" = <3 agree → goes to agent judge layer

**Decision rule for which single oracle to use for production retrain:**
- Compute per-oracle alignment with consensus (rank correlation per dim, exact agreement rate on content_type)
- Pick the oracle most aligned with consensus
- That oracle becomes the production labeler for the full 8K+ training set

### 3. Conservative-oracle principle for penalty flags (needle filters)

When two oracles produce different penalty-flag firing rates on the same prompt, **prefer the more conservative oracle** (fewer fires). 

**Why:**
- False positives (over-firing) → legitimate content gets demoted and effectively disappears from the lens (without lens-fit shipping, this is irreversible at the user-facing level)
- False negatives (under-firing) → some wrong-trajectory content stays at higher scores (this is the existing v4 baseline behavior — acceptable, not great)
- Asymmetry: FP is worse than FN. Under-firing is the safer default failure mode.

**Scope:** Applies only to F-K-style penalty flags on needle-in-haystack filters. Not for general-purpose filters where over-applying max_score caps is just being correct about low-quality content.

### 4. Two-pool spot-check pattern after multi-oracle consensus

After picking the production oracle, run two parallel agent spot-checks:
- **Pool A (false-negative check):** N=15 articles the oracle called in-scope with high score. Should any have been penalty-flagged?
- **Pool B (false-positive check):** N=15 articles the oracle penalty-flagged, stratified across flags. Is the flag correct per the prompt?

**Decision thresholds:**
- WRONG ≥ 3/15 (20%) in either pool → reconsider; oracle has systematic blind spot
- WRONG ≤ 1/15 → safe for production retrain
- 2/15 → borderline; report cases, user decides

### 5. Calibration report artifact

Every filter calibration generates `filters/{name}/v{N}/calibration_report.md` containing:
- Sample composition + counts
- Per-oracle batch results (success rate, distribution, flag firing rates)
- Consensus metrics (per-dim median, content_type majority, disagreement rate)
- Agent judge verdicts (Pool A + Pool B + hard cases)
- Dimension redundancy check (pairwise Pearson + redundancy ratio)
- Gatekeeper enforcement verification
- Tier distribution vs target
- **Formal go/no-go**: Ready / Review / Block
- Cost summary

---

## Consequences

### Positive
- Eliminates "no ground truth" concern by triangulating consensus
- Catches oracle-specific bias (over/under-application) that single-oracle can't see
- Gradient-preserving soft penalty avoids ADR-015 cliff failure mode
- Conservative-oracle principle gives a default tiebreaker
- Formal calibration_report.md artifact = reviewable single source of truth
- Methodology is reproducible — future filters get the benefit

### Negative
- Calibration cost rises from ~$0.10 (single oracle, 100 articles) to ~$12 (5-batch + 2-agent, 500+ articles)
- Calibration time rises from ~20 min to ~3-4 hours (mostly gpu-server inference + agent runtime)
- Requires Ollama models pre-loaded on gpu-server (gemma3:27b, qwen3:14b at minimum)
- More moving parts means more places for things to go wrong (per-oracle JSON parsing, GPU memory contention, agent tool quotas)

### Neutral
- Production retrain cost unchanged (single-oracle scaling)
- Existing filters need not be re-calibrated (apply to new filters or major prompt revisions)
- The methodology is opt-in for needle filters specifically — not mandatory for every filter

---

## Worked Example: cultural_discovery v5 (2026-05-30/31)

| Step | Status | Artifact |
|---|---|---|
| Soft penalty conversion | Done | `filters/cultural_discovery/v5/prompt-compressed.md` v3 |
| 5-oracle batch calibration | In progress | scripts/calibration_v5_phase3.py |
| Gemini Flash 2.5 score | Done (522 articles) | `datasets/scored/cd_v5_softpenalty_rescored_v3/` |
| DeepSeek V4 Flash score | Done (522 articles) | `datasets/scored/cd_v5_softpenalty_deepseek_v3/` |
| Gemma 3 27B (gpu-server) | TODO | `datasets/scored/cd_v5_gemma_27b/` (planned) |
| Qwen 3 14B (gpu-server) | TODO | `datasets/scored/cd_v5_qwen3_14b/` (planned) |
| Opus agent (hard cases) | TODO | `datasets/scored/cd_v5_opus_agent_verdict.md` (planned) |
| Haiku agent (hard cases) | TODO | `datasets/scored/cd_v5_haiku_agent_verdict.md` (planned) |
| Consensus + per-oracle alignment | TODO | embedded in calibration_report.md |
| Pool A/B spot-checks | Done (v1 data) | `datasets/scored/cd_v5_ds_spotcheck_A_falseneg_verdict.md`, `B_falsepos_verdict.md` |
| Calibration report artifact | TODO | `filters/cultural_discovery/v5/calibration_report.md` |

**Findings so far (single-oracle level, before consensus):**
- Gemini F-K firing rate: 60% (over-applies per opus agent hand-judge)
- DeepSeek F-K firing rate: 26% (under-applies for individual allegations, but more aligned with prompt overall)
- Dimension redundancy: Gemini 60% of pairs above |r|=0.7; DeepSeek 20%
- After prompt tightening (v3): Gemini drops to 50%, DeepSeek rises to 30% (gap closed ~50%)

**Expected outcome of full multi-oracle pass:** DeepSeek emerges as the production oracle for v5 retrain. Cost saving vs Gemini Batch: ~$13 per 8K-article retrain.

---

## Alternatives Considered

### Alternative 1: Stay with single-oracle Phase 3 (status quo)
Don't add multi-oracle complexity; trust Gemini Flash 2.5 as default.

**Pros:** Simpler. Faster calibration. No new tooling.

**Cons:** v5 journey already demonstrated this approach fails for needle filters with complex penalty mechanics. Gemini over-fires F-K and we wouldn't have caught it. Would ship a student with the same over-firing baked in.

**Why not chosen:** The failure mode (silent oracle-specific bias becoming training-data bias becoming student bias) is exactly what calibration is meant to prevent.

### Alternative 2: Pairwise comparison (2 oracles)
Cheaper than 5-oracle (just Gemini + DeepSeek).

**Pros:** Already roughly what we did informally. Half the cost.

**Cons:** Two oracles can be correlated-wrong (especially if same vendor family or similar architecture). 5-oracle triangulation catches this.

**Why not chosen:** Marginal cost of adding 2-3 self-hosted gpu-server oracles is ~$0 (already paid for hardware). The robustness gain is high.

### Alternative 3: Multi-oracle batch for production retrain too
Use all 5 oracles to score the full 8K, take consensus labels.

**Pros:** Every training label is a consensus. Most robust possible.

**Cons:** 5× cost at scale ($75-150 per 8K vs $2-15 single-oracle). Adds noise from oracles that disagree with majority. Requires bigger consensus-disagreement-arbitration logic at scale.

**Why not chosen:** Diminishing returns. The single oracle most aligned with calibration consensus is "good enough" for production scoring. The cost saving compounds across filters.

### Alternative 4: Use Claude Opus as direct labeling oracle
If Opus agent is the most rigorous reader, why not use it as the production oracle?

**Pros:** Highest reasoning quality per call.

**Cons:** ~10-50× cost vs Gemini Flash / DeepSeek Flash. Slow (multi-step reasoning). Not feasible at 8K scale.

**Why not chosen:** Use Opus where it adds most value (judging hard cases, ~30 articles), use cheap oracles where they suffice (scoring 8K).

---

## Implementation Notes

### Required tooling (gap fillers vs existing scripts)
- `scripts/calibration_v5_phase3.py` — exists, inline analyses for v5
- `scripts/score_ollama_oracle.py` — TODO, generic Ollama-based scorer (Gemma/Qwen/Phi)
- `scripts/multi_oracle_consensus.py` — TODO, computes consensus + per-oracle alignment
- `scripts/build_handjudge_*.py` — exists, builds disagreement task markdown for agents
- `scripts/build_ds_spotcheck.py` — exists, builds Pool A/B task files for spot-check agents

### Decision thresholds (defaults for needle filters)
- Pool A false-negative rate threshold: 20% WRONG → reconsider
- Pool B false-positive rate threshold: 20% WRONG → reconsider
- Dimension redundancy threshold: 50% of pairs above |r|=0.7 → re-design dims (per ADR Phase 1)
- Consensus disagreement rate: >40% of articles with <3-oracle agreement → prompt is ambiguous, tighten before retrain

### When to apply (scope)
- **Needle-in-haystack filters** (cultural_discovery, foresight, belonging, nature_recovery) — yes
- **General-purpose dense filters** (uplifting, sustainability_technology) — optional, simpler Phase 3 likely sufficient
- **Filters with hard caps only (no soft penalty mechanism)** — single-oracle Phase 3 is fine

### Dependencies
- gpu-server with Ollama + gemma3:27b + qwen3:14b pre-loaded (verify before starting calibration)
- Anthropic API key configured (for Opus + Haiku agents)
- DeepSeek API key configured (for batch oracle layer)
- Gemini API key configured

---

## References

- ADR-015: Lenses as perspectives, not partitions (cliff failure mode)
- ADR-017: Inter-oracle MAE as distillation floor (multi-oracle context)
- ADR-010: Oracle consistency over data volume (prompt quality matters more)
- `docs/agents/filter-development-guide.md` Phase 3 (the doc this extends)
- `docs/agents/templates/oracle-calibration-agent.md` (single-oracle template)
- `docs/agents/templates/prompt-calibration-agent.md` (single-oracle template)
- Memory: `feedback-conservative-oracle-better.md` (2026-05-31)
- Memory: `feedback-oracle-not-ground-truth.md` (2026-05-31)
- Memory: `feedback-oracle-selection-criteria.md` (2026-05-30)
