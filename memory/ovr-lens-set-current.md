---
name: ovr-lens-set-current
description: Current ovr.news lens/tab set and which filter version powers each — the filter→lens mapping (authoritative tab config lives in ovr.news, not here)
metadata:
  type: reference
---

Filters are named to match ovr.news **lens/tab** names at version bumps (ADR-012), all English (ADR-013). Lenses are *perspectives, not partitions* — overlap between them is correct (ADR-015).

**Lens → filter powering it** (as of 2026-07-27; grounded in CLAUDE.md filter table):

| ovr.news tab/lens | Filter (version) | Note |
|---|---|---|
| **Thriving** | uplifting **v7** | thriving v1 PARKED (bimodal, ADR-015); uplifting stays as the Thriving tab |
| **Discovery** | cultural_discovery **v5** | resolves #62 leakage; DeepSeek oracle |
| **Solutions** | solutions **v6** | v6 trained + gate passed 2026-07-27 (F1 0.739); normalization pending. v5 serving as fallback. Replaces sustech v3 + foresight v1. |
| **Belonging** | belonging **v1** | |
| **Nature / Recovery** | nature_recovery **v4** | deployed 2026-07-10; v2 kept as fallback. DeepSeek oracle. v5 planned (#71). |

**Not ovr.news lenses:** investment-risk (separate use), ai-engineering-practice → augmented-engineering (separate product, not ovr.news). foresight v1 PARKED (folded into Solutions).

**Authority note:** the *definitive* tab set + ordering lives in the ovr.news repo, not here — this is the distillery-side mapping. Confirm against ovr.news before treating as canonical. Related: [[cd-v5-reference-status]], [[filter-doc-standard]].
