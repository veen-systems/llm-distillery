---
name: project-session-2026-07-27
description: Solutions v6 production performance check, gate re-run, playbook update with probe-split retraining technique
metadata:
  type: project
---

# Session 2026-07-27

## What happened

- **Solutions v6 production performance**: Analyzed 3 overnight runs on sadalsuud. Score distribution is continuous (median 0.17, max ~5.0), much improved from v4's bimodal distribution. ~58 medium+ per run (3.3%).
- **Gate re-run**: Solutions v6 gate PASSED — recall 0.671, precision 0.824, F1 0.739 (vs v4: 0.559/0.768/0.647).
- **Normalization blocked**: Only 167 articles at ≥2.25 (need 200). Will hit threshold in 1-2 more runs.
- **nr v4 gate file**: Was overwritten with solutions v6 data (pre-existing from Jul 26). Restored from git.

## Documentation updates

- **FILTER_PLAYBOOK.md**: Added §4a (probe-split retraining), §5 (score compression), §7 (gate file hygiene), §9 (improvement loop).
- **CLAUDE.md**: Updated solutions v6 gate status, normalization pending.
- **docs/ideas/probe-split-iterative-improvement.md**: New paper idea.
- **memory/gotcha-log.md**: Gate file cross-contamination entry.
- **MEMORY.md**: Added 5 orphaned topic file entries.

## Cross-repo

- [augmented-engineering#32](https://github.com/ducroq/augmented-engineering/issues/32) — methodology pattern: probe-split retraining
- [llm-distillery#72](https://github.com/veen-systems/llm-distillery/issues/72#issuecomment-5087547202) — solutions v6 normalization added to issue

## Obituary detector (LD#51/#77 → NM#185)

- **ovr.news investigation**: Scored 203 Phase-1 borderlines with v3 MLP. 3/203 flagged at ≥0.95 (1.5%), all multilingual historical-legacy FPs. Model correctly passes 200/203. v3 generalizes well to ovr.news — the Phase-1 concern was driven by a different model (Claude screener), not the v3 MLP.
- **v3/inference.py**: Created `ObituaryDetectorV3` class mirroring `CommercePrefilterV2`. Hardened with multi-model review battery (4 reviewers: correctness, security, edge cases, integration → 8 issues fixed, 0 CRITICAL/HIGH remaining).
- **NexusMind NM#185**: Phase 3 deployed — owner gate removed. Pipeline enabled (`obituary_detector.enabled: true`). Next harvest cycle stamps `_obituary_score` / `_is_obituary` in shadow mode (drops nothing).
- **NexusMind `obituary.py:182`**: Fixed to use `result["is_obituary"]` instead of recalculating threshold.

## Documentation updates

- **FILTER_PLAYBOOK.md §4b**: Added "Production-feedback retraining" — generalizes probe-split pattern to single-stage filters without a runtime probe. Comparison table, composition rule (§4b → §4a escalation).
- **FILTER_PLAYBOOK.md quick-reference**: Added 5-step checklist for §4b path.
- **memory/project-obituary-detector.md**: New project memory — v3 status, NM#185 handoff, v4 corrective retrain plan, labeling rule, dependency chain.
- **memory/MEMORY.md**: Added obituary detector pointer, removed 3 dead links (standalone-outlets, session-close-ritual, github-push — files never created).
- **NexusMind `docs/obituary-detector-build-plan.md`**: Phase 3 marked deployed, owner gate removed.

## Cross-repo

- NexusMind `2e8c66e`: Phase 3 build plan updated
- NexusMind `36d1cdc`: obituary.py fix (use result["is_obituary"])
- NexusMind `scripts/main.py`: UNRELATED uncommitted change (atomic file writes #206) — left as-is

## Next session

- NexusMind: verify obituary shadow scores appear in next harvest cycle output
- Obituary v4 corrective retrain: add 8 ovr.news FPs as hard negatives (§4b), retrain, re-validate
- Solutions v6: fit normalization.json once ≥200 articles accumulate (~1-2 more runs)
- Nature_recovery v5 planning: apply probe-split technique to nr v4
- Quality monitoring: draft §8 of FILTER_PLAYBOOK.md (periodic filter health checks + retrain triggers)
