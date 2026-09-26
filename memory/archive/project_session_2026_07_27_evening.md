---
name: project-session-2026-07-27-evening
description: Small LD issues sweep — #49 (superseded filter cleanup), #68 (verify description check), #63 (branded content prefilter), #57 (already done); cross-repo NM#276/NM#206 closed; curate
metadata:
  type: project
---

# Session 2026-07-27 (evening) — Small LD Issues Sweep

## What happened

Closed 4 small+high-ROI llm-distillery issues plus 2 NexusMind "done but not closed":

| Issue | What | Commit | Impact |
|-------|------|--------|--------|
| **LD#49** | Remove 6 superseded filter version dirs | `3e1ccec` | −61,314 lines, 10 stale refs cleaned, filters/README.md rewritten |
| **LD#68** | Per-dim `description` field check in verify | `c2ab571` | Catches silent KeyError before Hub upload |
| **LD#63** | Branded/sponsored URL blocking in uplifting v7 prefilter | `623ea51` | 12 URL patterns, 13/13 self-tests, blocks paid content from hero slot |
| **LD#57** | Schema gate for `source_filter:` block | — | Already implemented, closed |
| **NM#276** | Consent/paywall guard | — | Already committed (`d0f0d9c`), closed issue |
| **NM#206** | Filter timeout | — | Already committed (`9360b87`), was already closed |

### LD#63 notes
- The uplifting v7 prefilter now blocks publisher self-labeled paid content via URL path patterns: `/branded/`, `/sponsored/`, `/sponsored-content/`, `/advertorials/`, `/partner-content/`, `/brand-studio/`, `/paid-post/`, `/native-ad/`, `/promoted/`, `/patrocinado/`, `/publireportage/`
- Defense-in-depth layer 1 — catches URL-declared branded content before scoring
- Full v8 retrain with hard negatives deferred
- **NOT yet deployed** to NexusMind/gpu-server — the prefilter change is behavioral

## Curate findings

- **Verification**: All locally-runnable verify assertions PASS. CLAUDE.md at 15,443 bytes (well under budget).
- **Stale memory**: 3 files >30 days (calibration-history 52d, gemma3-model 58d, thriving-v1-scoring 99d) — all stable reference docs, intentionally preserved.
- **Gotchas**: No new entries. No unresolved lingering entries.
- **Hypotheses**: None open across any repo.
- **Doc sync**: TODO.md updated, filters/README.md rewritten, filter-status audit notes updated.

## Cross-repo

- Updated `memory/cross-repo-prioritization.md` — 6 items resolved, deploy-pending noted
- NM#276 + NM#206 confirmed done and closed

## Next session pickup

- **LD#80** — commerce v2 regression (P0, cross-cutting)
- **LD#76** — calibration audit umbrella (#74/#75/#72)
- **Deploy LD#63** — sync uplifting v7 prefilter to NexusMind → gpu-server
- **solutions v6 normalization** — fit once ≥200 articles accumulate
- **ovr.news small issues**: #263 (Healthchecks re-enable), #204 (remove hardcoded obit)
