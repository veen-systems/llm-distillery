---
name: project_session_2026_07_09
description: nature_recovery v4 — training → gate → oracle bias-vs-noise investigation → ground-truth gate → Hub-uploaded + staged (activation deferred, sadalsuud down)
metadata:
  type: project
---

# Session 2026-07-09 — nature_recovery v4 to the deploy boundary

**Outcome:** v4 is **gate-passed, Hub-uploaded, and STAGED** — production activation
deliberately deferred (sadalsuud was down + flaky link + discovery=latest landmine).
Completion runbook: `docs/nature_recovery_v4_DEPLOY_COMPLETION.md`.

## What shipped (committed acbfe7c..f2879d7)
- **Recall-first e5 probe** (`scripts/train_probe.py --objective recall`, H3 fix): 98.2%
  recall / 64% screened. Pure helpers unit-tested. [[feedback-probe-training-data]]
- **Student** (Gemma-1B+LoRA, scale 2.0, seed-42): held-out DeepSeek test **recall 0.672,
  precision 0.848, F1 0.750, Spearman 0.821** — beats v2 (0.603/0.614/0.609/0.795) on
  every metric. Operating point **3.75** (tuned; must stay above the 3.5 gatekeeper cap).
- **Ground-truth gate** (`scripts/gate/ground_truth_gate.py`, ADR-021): judge vs held-out
  ORACLE ground truth, not the prior model. Replaces `agreement_gate.py` (deprecated —
  it false-FAILed v4 vs a Gemini-labeled v2 reference cohort, `_v2_split`, +1.775 inflated).
- **Hub**: `jeergrvgreg/nature-recovery-filter-v4` uploaded + verified (OLD keys, all files).
- **Report**: `docs/reports/nature_recovery_v4_report.pdf` (9 sections, ELI15+detail).
- Memories created: [[feedback-oracle-bias-vs-noise]], [[feedback-claim-requires-verify]],
  [[feedback-probe-training-data]]. ADR-021 + draft-020 bias amendment. Article drafts
  synced (needle, oracle-consistency, hybrid, cross-filter) under `docs/articles/`.

## The load-bearing lessons (engineer caught the agent 2-3×)
1. **Oracle NOISE ≠ BIAS.** Agent recommended switching DeepSeek→Gemini on 2.2× lower
   self-MAE (0.17 vs 0.38); engineer caught that Gemini's low noise came with a *generous
   bias* (surfaces junk: changemaker profile 0→5.6). Cost the engineer $100-200 before.
   Choose oracle for bias; average k runs to cut noise, never switch. [[feedback-oracle-bias-vs-noise]]
2. **Reproduce-don't-assess.** Gate "FAIL" + "12/12 student errors" was an artifact of a
   Gemini-labeled reference; reading the labels showed 9/12 were v4 correctly rejecting
   generosity. Filed augmented-engineering #25/#26/#27.
3. **Averaging denoises but doesn't lift recall** (engineer caught this too) — the missed
   articles have stable labels; recall levers are threshold + medium-band data (v5, #71).

## State / open
- **Deploy activation pending** (sadalsuud up + someone watching a run) — see completion runbook.
- v5 = recall enrichment via active learning from saved NexusMind output (#71).
- Still referenced-but-absent memories: `feedback-multi-agent-review-default`,
  `feedback-regex-ignorecase-trap` (create or drop the references).
- `deploy_to_nexusmind.sh` needs Linux porting (`C:/local_dev` roots + `python`→`python3`).

<!-- verify staged: ssh gpu-server 'test -f ~/llm-distillery/filters/nature_recovery/v4/model/adapter_model.safetensors && echo STAGED_OK' -->
<!-- verify Hub: hf api /models/jeergrvgreg/nature-recovery-filter-v4 (private) OR list_repo_files -->
