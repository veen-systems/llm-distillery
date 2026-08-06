---
name: ovr-lens-set-current
description: Current ovr.news lens/tab set and which filter version powers each — the filter→lens mapping (authoritative tab config lives in ovr.news, not here)
metadata:
  type: reference
---

Filters are named to match ovr.news **lens/tab** names at version bumps (ADR-012), all English (ADR-013). Lenses are *perspectives, not partitions* — overlap between them is correct (ADR-015).

**A filter name and its lens name are allowed to differ, and for two of them they permanently do.** ADR-012 amended 2026-08-06: `cultural_discovery` (Discovery lens) and `nature_recovery` (Recovery lens) **keep their names** — their HuggingFace repos are public standalone artefacts, and `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about. ADR-012's three stated audiences were all internal, so the Hub was never weighed. Neither rename had happened, so nothing was undone. **Do not re-open either at the next version bump.** Still open: uplifting → thriving, which the Hub argument does not touch (uplifting is NO_HUB) but which collides with the real parked `filters/thriving/v1` directory.
<!-- verify: grep -q "renames to \`discovery\` and \`recovery\` are cancelled" docs/adr/012-lens-aligned-filter-naming.md && echo PASS || echo FAIL -->

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
