---
name: cd-v5-reference-status
description: cultural_discovery v5 is the reference example for DeepSeek-as-default-oracle and the ADR-020 multi-oracle calibration methodology
metadata:
  type: reference
---

**cultural_discovery v5** (deployed 2026-05-31) is the project's **reference example** for two things:

1. **DeepSeek-as-default-oracle.** First non-Gemini lineage in production. DeepSeek V4 Flash was chosen over Gemini Flash 2.5 after a multi-oracle calibration + agent-judging bake-off (see [[feedback-oracle-selection-criteria]]). ~7x cheaper than Gemini; val MAE 0.697 (better than v4's 0.74). Economics validated: v4→v5 dev cost ~$11 vs v4's ~$25 under Gemini.
2. **ADR-020 methodology** (`docs/adr/draft-020-extended-oracle-calibration.md`, PROVISIONAL) — multi-oracle batch scoring + Opus/Haiku agent judging on a disagreement set. cd v5 is the *worked example*; **solutions v4 is the validation case** that graduates ADR-020 from PROVISIONAL → Accepted (or forces a revision).

Also the reference for soft-penalty flag design (F–K converted from hard `max_score` caps to per-dim penalties per ADR-015 — cliffs hurt MAE; thriving v1 was parked at 0.94 for that failure mode) and for the [[feedback-conservative-oracle-better]] principle.

Deployed: HF Hub (`jeergrvgreg/cultural-discovery-filter-v5`, private) + gpu-server. Resolves #62 discovery-lens leakage end-to-end (Pope apology 9.65→2.31, Indus/Sumer 9.12).

Related: [[oracle-pricing-scheduling]] (DeepSeek off-peak batch scheduling), [[filter-doc-standard]] (cd v5's doc extensions).

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; the file was listed in that recap but never committed. Content grounded in CLAUDE.md + MEMORY.md recaps. -->
