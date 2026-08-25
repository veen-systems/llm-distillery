---
name: ovr-lens-set-current
description: Current ovr.news lens/tab set and which filter version powers each — the filter→lens mapping (authoritative tab config lives in ovr.news, not here)
metadata:
  type: reference
---

Filters are named to match ovr.news **lens/tab** names at version bumps (ADR-012), all English (ADR-013). Lenses are *perspectives, not partitions* — overlap between them is correct (ADR-015).

**A filter name and its lens name are allowed to differ, and for three of them they permanently will.** ADR-012 amended 2026-08-06 — the whole rename backlog is closed, so **do not re-open any of these at a version bump**:

| Lens | Filter name | Decision |
|---|---|---|
| Discovery | `cultural_discovery` | **Keeps its name.** Rename cancelled. |
| Recovery | `nature_recovery` | **Keeps its name.** Rename cancelled. |
| Solutions | `solutions` | **Confirmed as-is.** Already migrated once at v4; a second cross-repo field change is not worth the smallest descriptiveness gain of the set. |
| Thriving | `uplifting` → **`human_thriving`** | **Renames at v8**, not before. Not to bare `thriving` — that dir exists (parked, ADR-015). |
| Belonging | `belonging` | Already matches. |

The reason in one line: ADR-012's three stated audiences were all *internal*, and a HuggingFace repo page is a public standalone artefact where `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about. The rule that follows — rename to the lens name only if it stands alone; otherwise keep or build `{qualifier}_{lens}`.
<!-- verify: grep -q "human_thriving" docs/adr/012-lens-aligned-filter-naming.md && echo PASS || echo FAIL -->
<!-- verify: grep -q "renames to \`discovery\` and \`recovery\` are cancelled" docs/adr/012-lens-aligned-filter-naming.md && echo PASS || echo FAIL -->

**Lens → filter powering it** (as of 2026-07-27; grounded in CLAUDE.md filter table):

| ovr.news tab/lens | Filter (version) | Note |
|---|---|---|
| **Thriving** | uplifting **v7** | thriving v1 PARKED (bimodal, ADR-015); uplifting stays as the Thriving tab |
| **Discovery** | cultural_discovery **v5** | resolves #62 leakage; DeepSeek oracle |
| **Solutions** | solutions **v6** | v6 trained + gate passed 2026-07-27 (F1 0.739); normalization pending. v5 serving as fallback. Replaces sustech v3 + foresight v1. |
| **Belonging** | belonging **v1** | |
| **Nature / Recovery** | nature_recovery **v4** | deployed 2026-07-10; v2 kept as fallback. DeepSeek oracle. v5 planned (#71). |

**Not ovr.news lenses:** investment-risk (**PAUSED 2026-08-25** — its only consumer was the Aegis narrative-risk export, which the owner confirmed dormant; ovr allow-lists the name only so old rows in the 10-day window still validate, so **do not remove that allow-list**), ai-engineering-practice → augmented-engineering (separate product, not ovr.news). foresight v1 PARKED (folded into Solutions).

**Authority note:** the *definitive* tab set + ordering lives in the ovr.news repo, not here — this is the distillery-side mapping. Confirm against ovr.news before treating as canonical. Related: [[cd-v5-reference-status]], [[filter-doc-standard]].
