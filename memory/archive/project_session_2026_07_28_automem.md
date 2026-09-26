---
name: project_session_2026_07_28
description: "Session 2026-07-28 — solutions score collapse, commerce v2→v1 rollback, a11y fixes, corroboration verification, NM#276 confirmed"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9802f59f-50f6-4e54-a1cc-ef7520dc0ed6
  modified: 2026-07-28T13:48:43.517Z
---

# Session 2026-07-28

## What We Fixed

### Solutions Lens Score Collapse
- **Root cause**: v6 compresses scores to 0-5, but `displayScoreThreshold` is 4.5 (0-10 scale). Only top ~1% cleared.
- **Fix**: `SCORE_SCALE_FACTORS{solutions: 2.0}` in ovr.news `summarize.ts` with `raw > 5.0` guard. Bridge until normalization.json is fitted.
- **Side effect**: First run double-scaled 90 old v5 articles (8-10 → 16-20). Fixed with guard + DB halving (`article_filter_scores` + `articles` tables).

### Commerce Prefilter v2 → v1 Rollback (LD#80)
- **Root cause**: v2 deployed without Phase 5 shadow comparison. 190-sample test set wasn't production-representative.
- v2 blocks 2.1% vs v1's 5.2%, and generates false positives on multilingual news (Greek/Hungarian).
- **Fix**: v1 weights (541MB DistilBERT) uploaded to HF Hub (`jeergrvgreg/commerce-prefilter-v1`) and copied to NexusMind. commerce.py switched from GPU v2 path to local CPU v1 path.

### A11y Smoke Test (ovr.news)
- **link-name**: Added `aria-label={title}` to standard-variant image links in `FeedItem.astro`
- **color-contrast**: Darkened `gradient-text` light-mode stops to sky-700/green-700

### Hot DB Creation Failure
- **Root cause**: `create-hot-db.ts` produced 0-byte file — cause not yet diagnosed.
- **Fix**: Manual hot DB recreate + R2 upload + Cloudflare deploy re-trigger.

### Corroboration System Verified
- 47% coverage (1,009/2,155 articles), cross-run persistence active (977 references), cluster sizes 2-691.
- Veurne procession cross-language miss = known NM#275 ceiling, not fixing.
- Metadata stored as `nexus_mind_attributes.{filter}.source_quality.corroborating_sources`.

### NM#276 Consent Guard Verified
- Already deployed Jul 26, actively working (161 quality rejects in latest pre-enrichment run).
- Cross-repo doc was stale — updated.

## State After Session

| System | Status |
|--------|--------|
| Solutions lens | ✅ Live, 69 recent articles, avg score 8.7 |
| Commerce prefilter | ✅ v1 active (next run picks it up) |
| A11y smoke test | ✅ Fixes deployed (tested Monday) |
| Corroboration | ✅ 47% coverage, cross-run active |
| QA health | ✅ Solutions avg 8.7 (WARN, was ERROR at 13.8) |
| NexusMind | ✅ Clean (violence_promotion committed, no uncommitted changes) |
| ovr.news | ✅ Clean, pushed to master |

## Next Session

- **LD#76 calibration audit** — umbrella for belonging/nature_recovery/cultural_discovery score boundary issues
- **NM#206 filter timeout handling** — production reliability
- **solutions normalization.json** — fit once ≥200 v6 articles accumulate at ≥2.25

## Related Memories

- [[cross-repo-prioritization]] — updated with LD#80 resolution, NM#276 verification
- [[gotcha-log]] — 4 new entries added
