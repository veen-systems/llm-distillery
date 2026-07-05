---
name: feedback-conservative-oracle-better
description: On penalty/exclusion flags, prefer the oracle that under-fires — a conservative oracle beats an eager one for student MAE
metadata:
  type: feedback
---

When choosing or tuning an oracle for a filter that uses **penalty or exclusion flags** (e.g. cultural_discovery's F–K hard-negative flags), prefer the oracle that **under-fires** the flag over one that over-fires it. In the cd v5 bake-off, DeepSeek's conservativism on penalty flags was the deciding advantage over Gemini.

**Why:** A false penalty (flag fired when it shouldn't) demotes a genuinely-good article below threshold — a visible, high-cost error the student then learns to reproduce. A missed penalty is a softer failure (the article scores slightly high but isn't wrongly excluded). Asymmetric costs → prefer the conservative side. This also composes with soft-penalty design (ADR-015): penalties subtract-and-floor rather than hard-cap, so an over-eager flag on a conservative oracle does less damage still.

**How to apply:** During multi-oracle calibration, score the disagreement set and check *which direction* each oracle errs on penalty flags. Favor the under-firing oracle even at equal overall agreement. Precedence rule: conservative-oracle wins over raw consensus-alignment when they conflict. See [[feedback-oracle-selection-criteria]], [[cd-v5-reference-status]].

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; listed in that recap but never committed. Grounded in CLAUDE.md cd v5 entry + MEMORY.md recap. -->
