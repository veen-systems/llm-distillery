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

## Next session

- Fit normalization.json once ≥200 v6 articles accumulate (~1-2 more runs)
- Nature_recovery v5 planning: apply probe-split technique to nr v4
