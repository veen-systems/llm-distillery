---
name: ovr-lens-set-current
description: Current ovr.news lens/tab set and which filter version powers each — the filter→lens mapping (authoritative tab config lives in ovr.news, not here)
metadata:
  type: reference
---

Filters are named to match ovr.news **lens/tab** names at version bumps (ADR-012), all English (ADR-013). Lenses are *perspectives, not partitions* — overlap between them is correct (ADR-015).

**Lens → filter powering it** (as of 2026-05-31; grounded in CLAUDE.md filter table):

| ovr.news tab/lens | Filter (version) | Note |
|---|---|---|
| **Thriving** | uplifting **v7** | thriving v1 PARKED (bimodal, ADR-015); uplifting stays as the Thriving tab |
| **Discovery** | cultural_discovery **v5** | resolves #62 leakage; DeepSeek oracle |
| **Solutions** | sustainability_technology **v3** → **solutions v4** (in dev) | broadening clean-tech → governance/community solutions (#43); foresight v1 merges in here |
| **Belonging** | belonging **v1** | |
| **Nature / Recovery** | nature_recovery **v2** | |

**Not ovr.news lenses:** investment-risk (separate use), ai-engineering-practice → augmented-engineering (separate product, not ovr.news). foresight v1 PARKED (folding into Solutions).

**Authority note:** the *definitive* tab set + ordering lives in the ovr.news repo, not here — this is the distillery-side mapping. Confirm against ovr.news before treating as canonical. Related: [[cd-v5-reference-status]], [[filter-doc-standard]].

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; listed in that recap but never committed. Grounded in CLAUDE.md filter table + ADR-012/013/015. -->
