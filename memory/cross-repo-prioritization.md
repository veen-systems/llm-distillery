---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

**Last updated: 2026-07-28** (post-session wrap-up: LD#80 resolved, NM#276 verified, solutions score collapse fixed, corroboration confirmed)

Covers: **llm-distillery** (30 open), **NexusMind** (36 open), **ovr.news** (73 open), **FluxusSource** (6 open).

## Changes Since 2026-07-27 Session

| What | Was (Jul 27) | Now (Jul 28) |
|------|-------------|--------------|
| **LD#80 commerce v2→v1** | P0 — v2 underperforms v1 | **RESOLVED** — v1 rolled back, weights on HF Hub + NexusMind. v2 was deployed without Phase 5 shadow comparison. |
| **solutions score collapse** | v6 compressed scores (0-5) vs 4.5 threshold | **FIXED** — score_scale_factor=2.0 with raw>5.0 guard in summarize.ts. 69 articles live on site. |
| **Hot DB creation** | Silent 0-byte failure during fix run | **FIXED** — manual recreate + R2 upload. Root cause not yet diagnosed. |
| **NM#276 consent guard** | Listed as P0 | **VERIFIED WORKING** — deployed Jul 26, 161 quality rejects/run. Doc was stale. |
| **Corroboration system** | NM#275 title-only E5 deployed | **VERIFIED** — 47% coverage, cross-run persistence active, cross-language ceiling at ~0.84 (Veurne procession = known edge case, not fixing). |
| **A11y smoke test** | 2 WCAG violations (link-name, color-contrast) | **FIXED** — aria-label on article links, darker gradient-text stops. |
| **LD#77 obituary v4 retrain** | 8 ovr.news FPs + 4 heldout FPs to fix | **TRAINED 2026-07-28** — 12 hard negatives, all resolved (max score 0.65). Heldout precision 0.977 (v3: 0.973), FP 5 (v3: 7). |

## Cross-Repo Dependency Chains

Chains that must be sequenced in order. Each `→` means "blocked on" or "feeds into."

### Chain 1: Obituary Detector (ACTIVE — v4 trained, pending enforcement)
```
LD#51 (design) ✅ → LD#77 (v3 classifier) ✅ → NM#185 (shadow wiring) ✅ → v4 corrective retrain ✅ → ovr#204 (remove hardcoded)
                                                                              │
                                                                              └─ EXECUTED 2026-07-28: 12 hard negatives, all resolved
```
**Status:** v3 shadow live (NM#185). v4 trained, ready to replace v3. Next: ≥1 production cycle → v4 replace v3 shadow → enforce → ovr#204.

### Chain 2: Armed Conflict Prefilter (NOT STARTED)
```
LD#73 (classifier build) → NM#274 (shadow/stamp wiring) → ovr.news (consumer-side exclusion, issue not yet filed)
```
**Status:** NM blocked until LD classifier exists. Lowest urgency of the active chains.

### Chain 3: Normalization Refits (SHARED ROOT CAUSE)
```
LD#76 (calibration audit — umbrella) → LD#74 (belonging boundary) + LD#75 (nr raw-scale collapse) + LD#72 (nr v4 normalization) + LD#64 (foresight refit)
                                        ↔ NM#205 (foresight normalization) ↔ NM#167 (general normalization tracking)
```
**Status:** All share the raw_min-drift root cause (#161, #205 pattern). LD#76 is the umbrella — fix the method, then refit all affected filters.

### Chain 4: Source Classification (FluxusSource → NexusMind)
```
FS source_classification (state-media/bias tags) → NM#253 (consume in downstream scoring)
```
**Status:** FluxusSource produces the data; NexusMind consumes it. Neither side is urgent.

### Chain 5: Solutions Lens Evolution (LARGELY COMPLETE)
```
LD#43 (broaden Solutions) → solutions v4 (deployed Jul 22) → solutions v6 (gate passed Jul 27) → NM#204 (dedicated solutions lens — likely superseded)
```
**Status:** v6 trained, gate passed. Normalization pending. NM#204 likely closable as superseded.

### Chain 6: Commerce Prefilter v2 Regression (RESOLVED — v1 rollback)
```
LD#80 (v2 underperforms v1) → ROLLED BACK to v1 (2026-07-28). v1 weights on HF Hub + NexusMind.
Root cause: v2 deployed without Phase 5 shadow comparison. 190-sample test set was not production-representative.
```
**Status:** v1 active. v2 code retained for reference. Revisit only if v1 shows quality gaps on production data.

### Chain 7: Summarizer Model Swap (ovr.news standalone, low dep)
```
ovr#270 (swap gemma3:27b → gpt-oss:20b) ↔ ovr#235 (held-out validation gate) ↔ ovr#267 (summarizer audit findings)
```
**Status:** Self-contained in ovr.news. Test with #235 gate.

## Priority Rankings

### P0 — Active / Blocking / Revenue-Affecting

| ID | Repo | Title | Why P0 |
|----|------|-------|--------|
| **LD#76** | llm-distillery | Calibration audit: deployed filters crush good content below medium boundary | Umbrella for #74/#75/#72. Likely ONE raw_min-drift root cause. |
| **LD#74** | llm-distillery | Belonging v1: raw ordering intact, medium boundary too high | Good content scoring 3-4, should be higher. |
| **LD#75** | llm-distillery | nature_recovery v2/v4: raw-scale collapse | Model fires near-zero for ~everything. |
| **LD#72** | llm-distillery | nr v4 normalization — running raw-passthrough, 31,852 records under-ranked | Blocked on ≥200 articles at ≥2.25 (currently 167). |
| **NM#206** | NexusMind | Filter timeout handling | Production reliability. |

### P1 — Important / This Quarter

| ID | Repo | Title | Why P1 |
|----|------|-------|--------|
| **NM#96** | NexusMind | GPU scoring: migrate from borrowed gpu-server to sustainable solution | Bus-factor — current gpu-server is borrowed. |
| **NM#221** | NexusMind | Multi-tenant GPU architecture + explicit VRAM management | OOM contention risk as filter count grows. |
| **NM#244** | NexusMind | gpu-server 422s drop whole chunks, reason not logged | Silent data loss in scoring pipeline. |
| **NM#220** | NexusMind | Ollama coexistence investigation | GPU resource contention between Ollama and scorer. |
| **ovr#262** | ovr.news | Data archiving is lossy & unreliable — full content + editorial rejects pruned | Irreplaceable editorial signal lost forever. |
| OPS | — | Catch-up budget: sadalsuud healthcheck drift (NM#91), uplifting v7 NO_HUB backup, cd v5 config-schema exemptions | Operator decisions parked from prior sessions. |

### P2 — Next / This Month

| ID | Repo | Title | Why P2 |
|----|------|-------|--------|
| **ovr#270** | ovr.news | Swap summarizer model: gemma3:27b → gpt-oss:20b (9.2× throughput) | Cheap win, fully on-GPU. Test with #235 gate. |
| **ovr#235** | ovr.news | Held-out validation set + deploy gate for prompt changes | Quality gate for all summarizer changes. |
| **LD#51/#77→NM#185→ovr#204** | chain | Obituary detector chain (see Chain 1) | Phase 3 deployed; **v4 trained 2026-07-28** (12 hard negatives, all resolved). v4 shadow replace + enforce next, then ovr#204. |
| **LD#73→NM#274** | chain | Armed conflict prefilter (see Chain 2) | Biggest build, lowest urgency. NM blocked on LD. |
| **NM#275** | NexusMind | Cross-language story dedup (MapBiomas case) | Content quality — EN orphaned from NL/ES/PT clusters. |
| **ovr#214** | ovr.news | Summarizer returns source-language output in english_* fields | Content quality bug. |
| **LD#23** | llm-distillery | Fix cultural-discovery evidence_quality dimension (MAE 1.31) | Long-standing scoring quality gap. |
| **LD#71** | llm-distillery | nature_recovery v5: lift recall via medium-band enrichment | Follow-on from v4. |
| **LD#70** | llm-distillery | nr v4: admit delivered protection wins (MPAs / protected acreage) | Scope gap in v4 oracle prompt. |
| **ovr#255** | ovr.news | Academic articles get irrelevant stock photos | Content presentation. |
| **ovr#256** | ovr.news | US-centric abbreviations in titles | International readability. |
| **NM#231** | NexusMind | uplifting v7 under-scores non-English documented-outcome news | 19 panel-confirmed examples. |
| **ovr#204** | ovr.news | Remove hardcoded obituary detection (NM#185 Phase 3 shipped) | **Updated today** — unblocked, waiting for shadow accumulation. |

### P3 — Later / Backlog

| ID | Repo | Title |
|----|------|-------|
| **FS#11** | FluxusSource | Split UnifiedConfigManager (God object, 998 lines) |
| **FS#107** | FluxusSource | Retain measurement time-series (overwritten every run) |
| **FS#103** | FluxusSource | Feed-health: make dead feeds actionable (prune recommendations) |
| **FS#114** | FluxusSource | il Fatto Quotidiano feed body corruption (Adnkronos wire swap) |
| **LD#52** | llm-distillery | Harmonize prefilter structure (remaining: class-name drift cleanup) |
| **LD#66** | llm-distillery | Fully-declarative prefilter migration for remaining filters |
| **NM#196** | NexusMind | Architectural simplification review |
| **NM#82** | NexusMind | Dockerize NexusMind pipeline |
| **NM#23** | NexusMind | Decouple sync logic from pipeline |
| **ovr#63** | ovr.news | E2E tests with Playwright |
| **ovr#55** | ovr.news | Manual test checklist + Lighthouse CI |
| **ovr#19** | ovr.news | Integration tests for summarize.ts |
| **FS#105 + ovr#254** | both | Version systemd units in-repo (both repos have same gap) |

### P4 — Future / Nice-to-Have

| ID | Repo | Title |
|----|------|-------|
| **LD#38** | llm-distillery | Breakthroughs filter (blocked on science journalism full-text harvesting) |
| **LD#40** | llm-distillery | Resilience lens investigation |
| **LD#43** | llm-distillery | Broaden Solutions lens (v4/v6 deployed; issue tracks remaining scope) |
| **ovr#232** | ovr.news | Reader-facing Pagefind search |
| **ovr#223** | ovr.news | Places/{country} discovery surface |
| **ovr#211** | ovr.news | PWA candidate |
| **ovr#213** | ovr.news | Web Push notifications |
| **ovr#242** | ovr.news | Continuation threads |
| **ovr#133** | ovr.news | Story-location world map |
| **LD#24** | llm-distillery | Energy-efficient inference (ONNX, smaller models) |

## Sequenced Work Batches (Recommended Execution Order)

### Batch A: This Week (remaining after 2026-07-28 session)

1. **LD#76 calibration audit** — diagnose root cause across #74/#75/#72
2. **solutions v6 normalization** — fit when ≥200 articles at ≥2.25 accumulate
3. **NM#206 filter timeout handling** — production reliability

### Batch B: This Week (normalization + obituary enforcement)

1. **LD#72 nr v4 normalization** — fit once ≥200 articles accumulate (~1-2 more runs)
2. **solutions v6 normalization** — same, fit when ≥200 articles at ≥2.25
3. **LD#77 obituary v4 retrain** — ✅ DONE 2026-07-28 (12 hard negatives, all resolved)
4. **Obituary v4 → enforce** — after ≥1 production cycle of shadow accumulation, replace v3 with v4 in NexusMind, then flip enforcement
5. **ovr#204 remove hardcoded obit** — after v4 enforced
6. **LD#74/#75 calibration fixes** — apply root-cause fix from #76 audit

### Batch C: Content Quality Sweep

1. **solutions v4 quality gate** — full-content read + oracle re-score sample (owed since Jul 22)
2. **ovr#270 + ovr#235** — summarizer model swap + validation gate
3. **ovr#256 + ovr#255** — abbreviations + academic stock photos
4. **NM#231** — uplifting non-English under-scoring
5. **ovr#214** — summarizer source-language leak

### Batch D: Infrastructure Hardening

1. **NM#244 + NM#206** — 422 logging + filter timeout
2. **NM#221** — multi-tenant GPU architecture
3. **NM#96** — sustainable GPU hosting (longer-term)
4. **ovr#262** — data archiving fix
5. **FS#107** — measurement time-series retention

### Batch E: New Filter Builds (lower urgency)

1. **LD#73 → NM#274** — armed_conflict classifier → shadow wiring
2. **LD#71 + LD#70** — nature_recovery v5 recall lift + protection scope
3. **LD#23** — cultural-discovery evidence_quality fix

## Housekeeping (do opportunistically)

- **~2026-08-01**: Delete retired sustech/foresight dirs (post-drain)
- **Sync `score_normalization.py`**: 44-line divergence between llm-distillery and NexusMind
- **NM#91**: sadalsuud healthcheck drift (operator decision)
- **LD#49**: Remove broken/superseded filter versions from repo
- **LD#48**: Normalize HF Hub repo naming convention
- **FS#105 + ovr#254**: Version systemd units in-repo (both repos)

## Standing Operator Decisions (Jeroen's call)

- NM#91 sadalsuud healthcheck drift (`enabled: true→false`) — confirm intent
- uplifting v7 NO_HUB backup — only copies on gpu-server + old Windows box
- cd v5 config-schema exemptions — reconcile or document
- FluxusSource: 71 DEAD disable candidates from Jul 26 triage
- FluxusSource: OVER_POLLED audit after frequency bumps
- FluxusSource: verify global broadening feeds are yielding

## Related Memories

- [[project_session_2026_07_26]] — baseline triage this updates
- [[project_session_2026_07_27]] — today's session (solutions v6 gate, obituary Phase 3)
- [[project-obituary-detector]] — Chain 1 details
- [[filter-status]] — per-filter MAE/status
- [[ovr-lens-set-current]] — lens→filter mapping
- [[calibration-history]] — Dead Ends section for #76 audit
