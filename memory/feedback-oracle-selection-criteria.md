---
name: feedback-oracle-selection-criteria
description: How to pick an oracle for a new filter — multi-oracle calibration + agent judging on a disagreement set, weighing consistency/conservativism/cost, not a single-oracle guess
metadata:
  type: feedback
---

Don't default to one oracle out of habit. **Select** it per filter via a small bake-off. This is the ADR-020 method, first run for cd v5.

**Why:** Oracle choice sets the student's MAE floor ([[feedback-oracle-not-ground-truth]]) and dominates per-article cost. cd v5's bake-off flipped the default from Gemini to DeepSeek and cut dev cost ~2x — a decision a single-oracle guess would have missed.

**How to apply (cd v5 playbook):**
1. **Calibration batch**: score a stratified sample (~300 articles) with **each candidate oracle**. cd v5 used 4: Gemini Flash 2.5, DeepSeek V4 Flash, Qwen3:14b, Phi4:14b.
2. **Disagreement set**: take the ~30 articles where oracles disagree most.
3. **Agent judging**: have strong models (Opus + Haiku) judge which oracle scored each disagreement better. cd v5: **DeepSeek won 80.8% vs Gemini 19.2%**.
4. **Weigh**: consistency (MAE floor), **conservativism on penalty flags** ([[feedback-conservative-oracle-better]]) — this *precedes* raw consensus-alignment when they conflict — and cost/latency ([[oracle-pricing-scheduling]] for DeepSeek off-peak batching).

Precedent + validation: [[cd-v5-reference-status]]. solutions v4 is the case that graduates ADR-020 out of PROVISIONAL.

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; listed in that recap but never committed. Grounded in MEMORY.md 2026-05-31 recap + draft ADR-020. -->
