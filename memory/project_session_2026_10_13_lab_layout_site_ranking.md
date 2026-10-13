---
name: project-session-2026-10-13-lab-layout-site-ranking
description: Session 2026-10-13 — lab layout rules + `lab.py move` (TODO 00 done, 10-12 data re-homed, training sets in the lab); ovr.news's Belonging ranking reproduced offline (recency is H-BB7's reorderer); four candidate formulas replayed for ovr.news; daily baseline pre-registered, awaiting b650
metadata:
  type: project
---

# Session 2026-10-13: lab layout, site ranking, formula replay

**Spend:** $0 oracle. Read-only ovr.db queries and page fetches; one sadalsuud scratch dir
(`~/ld-scratch/2026-10-13-belonging-daily-baseline`, pulled to the lab). **Deployed:** nothing.
Commits `4700963` .. this close.

**Ask (owner):** "continue" → TODO 00; "pls do that" → 0a option 1 (rebuild the check on the site's ranking); "talk to
the peer sessions"; "continue the work you can do without me" (owner away for the day).

| thread | state |
|---|---|
| TODO 00 lab layout: guards, `lab.py move`, checks 3 + 4, registry `lab` field | ✅ every guard mutation-tested; 2 review lenses |
| 10-12 data → `experiments/2026-10-12-belonging-c2c/`, draw → `datasets/belonging_comp_draw/v1`; c2a/c2b/c2c/adj1 → `datasets/*/v1` | ✅ verified, cited |
| EXP-048 `lab` field | open: owner (a/b/c), since the registry is append-only |
| H-BB7: page order = normalized × 0.85^d × 1.3 (< 24 h) | ✅ 507/507 live, 30/30 on 10-12 (fit); review re-derived it from the source |
| Editor boosts are a no-op (re-sort) | ovr.news#390, owner chose to correct the explainer page |
| Formula replay A/B/C/H for ovr.news | ✅ for the owner's later review; H = C's top-30 set |
| Daily baseline of v3's personal count | pre-registered `3b6bd6e`; populations built; qwen waits for ovr.news's b650 release |

**Lessons:** a post-hoc label correction kept only in prose (gotcha 2026-10-13; now `owner_corrections.tsv`).
⛔ **Mine:** sent ovr.news owner counts 1 low (uncorrected labels) before review; a registry test that read the live
registry; an in-place registry edit reverted for the owner's call.
