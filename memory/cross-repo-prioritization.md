---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

**Last updated: 2026-07-30 evening** (re-triage against live issue lists; LD#83 CLOSED — obituary enforcement live v5@0.85; LD#85 opened+parked; ovr#204 unblocked; LD#72 closed; new: LD#84, NM#278/#279, FS#118)

Covers: **llm-distillery** (29 open), **NexusMind** (34 open), **ovr.news** (76 open), **FluxusSource** (7 open). Repos: veen-systems/llm-distillery, ducroq/{NexusMind,ovr.news,FluxusSource}.

## Changes 2026-07-30 evening (session 3)

| What | Now |
|------|-----|
| **LD#83 obituary chain** | **CLOSED** — v5 trained + 3-reviewer battery + owner adjudication (grief-vs-news rule) + recall-first sign-off → **enforcement live v5@0.85** (b904edc; 1,158 blocked in 20:12 cycle, verified). |
| **LD#85 (v6 relabel)** | Opened + **PARKED indefinitely** (owner) — reactivate on obit-flag or visible over-block harm. |
| **ovr#204** | UNBLOCKED — the hardcoded ovr.news filter is now redundant. |
| **LD#72** | CLOSED (normalization refit superseded). |
| **b650 (Arian's 3090 Ti)** | Commissioned as training node — see `memory/b650-gpu.md`. |
| **New issues** | LD#84 (solutions prompt router), NM#278 (dedup retune), NM#279 (stale normalizations — Chain 3), FS#118 (GN redirect — Chain 8). |

## Changes Since 2026-07-27 Session

| What | Was (Jul 27) | Now (Jul 28) |
|------|-------------|--------------|
| **LD#80 commerce v2→v1** | P0 — v2 underperforms v1 | **RESOLVED 2026-07-30** (not 07-28: the a7771c9 rollback was a no-op — `if False:` gated a branch production never takes; gpu-server v2 kept scoring, 66 calls on 07-30. Real fix NexusMind 96d9acc forces local v1. Verify first cycle post-deploy: journal shows 'LD#80: ignoring gpu-server' + zero POST /commerce/predict.) |
| **solutions score collapse** | v6 compressed scores (0-5) vs 4.5 threshold | **FIXED** — score_scale_factor=2.0 with raw>5.0 guard in summarize.ts. 69 articles live on site. |
| **Hot DB creation** | Silent 0-byte failure during fix run | **FIXED** — manual recreate + R2 upload. Root cause not yet diagnosed. |
| **NM#276 consent guard** | Listed as P0 | **VERIFIED WORKING** — deployed Jul 26, 161 quality rejects/run. Doc was stale. |
| **Corroboration system** | NM#275 title-only E5 deployed | **VERIFIED** — 47% coverage, cross-run persistence active, cross-language ceiling at ~0.84 (Veurne procession = known edge case, not fixing). |
| **A11y smoke test** | 2 WCAG violations (link-name, color-contrast) | **FIXED** — aria-label on article links, darker gradient-text stops. |
| **LD#77 obituary v4 retrain** | 8 ovr.news FPs + 4 heldout FPs to fix | **TRAINED 2026-07-28** — 12 hard negatives, all resolved (max score 0.65). Heldout precision 0.977 (v3: 0.973), FP 5 (v3: 7). |
| **NM#274 violence_promotion v1** | Classifier built but not enabled in NexusMind | **SHADOW-DEPLOYED 2026-07-28** — first run: 53/4,864 (1.1%) flagged. #82 open for audit. |
| **solutions v6 normalization** | Normalization pending, needed ≥200 articles at ≥2.25 | **FITTED 2026-07-28** — 845 articles, percentile CDF deployed. Scorer restarted. |
| **Pipeline health** | First run with violence + normalization | **RUNNING 2026-07-28** — obituary OK (15 flagged), violence OK (53 flagged), solutions scoring in progress. sklearn 1.8→1.9 warning (#81). |

## Cross-Repo Dependency Chains

Chains that must be sequenced in order. Each `→` means "blocked on" or "feeds into."

### Chain 1: Obituary Detector (COMPLETE 2026-07-30 — enforcement live)
```
LD#51 ✅ → LD#77 (v3) ✅ → NM#185 (shadow) ✅ → v4 retrain ✅ → LD#83: v5 retrain + battery + owner adjudication + ENFORCE v5@0.85 ✅ CLOSED → ovr#204 (remove hardcoded) ← ONLY REMAINING LINK
```
**Status (2026-07-30 evening):** Enforcement live and verified (NexusMind `b904edc`; 20:12 cycle blocked 1,158 obituary-flagged articles; health = `obituary_detector_v5`). Rollback = `pipeline.obituary_detector.enforce: false`. LD#85 (v6 relabel under the owner's grief-vs-news rule) opened and **PARKED indefinitely** — reactivate only on an owner obit-flag or visible over-blocking harm. Next action in this chain: **ovr#204**.

### Chain 2: Armed Conflict / Violence Promotion Prefilter (ACTIVE — v1 shadow-deployed)
```
LD#73 (classifier build) ✅ → NM#274 (shadow wiring) ✅ → shadow accumulation → validate → enforce
```
**Status:** v1 shadow-deployed 2026-07-28. Code + models already in NexusMind; config enabled (stamp-only, no drops). Next: let shadow accumulate → panel-validate top scorers → retrain if needed → enforce.

### Chain 3: Normalization Refits (SHARED ROOT CAUSE)
```
LD#76 (calibration audit — umbrella) → LD#74 (belonging boundary) + LD#75 (nr raw-scale collapse) + LD#72 (nr v4 normalization) + LD#64 (foresight refit)
                                        ↔ NM#205 (foresight normalization) ↔ NM#167 (general normalization tracking) + NM#279 (stale uplifting-v7/belonging-v1 normalization — NEW 2026-07-30)
```
**Status: AUDITED 2026-07-31** (11-agent battery, all classifications adversarially verified — full synthesis on LD#76 issuecomment-5140079896). **The "one shared root cause" hypothesis is WRONG.** Findings: (1) `% norm<0.5` is a metric artifact — ≈ 1−base-rate for any anchored-CDF filter; healthy investment_risk is itself 75% "invisible" by it; (2) **stale normalization PROVEN for uplifting v7** (unit mismatch: Apr fit window contained score_scale_factor-stretched scores ×1.1976; 62% of MEDIUM+ demoted) **and belonging v1** (real drift, survivors under-ranked +1.0–2.1 norm pts) = NM#279; (3) **the only shared mechanism is NexusMind `production_scorer.py::_assign_tier`** applying raw-scale tier thresholds to NORMALIZED scores — structurally demotes bottom ~40% of every filter's passing population (product decision needed); (4) cd v5: dead prefilter (2828/2828 pass vs expected 0.15) + lens-fidelity dilution; the 3.5 op-point idea was REFUTED; (5) **nature_recovery v4 is HEALTHY — #75 was a measurement artifact** (94% of rows are probe outputs capped 0.75; the Jul-21 files predate normalization). Fix plan: refit uplifting + belonging (proven, sanctioned), NM tier-semantics ticket (owner decision), cd prefilter bugfix ticket, close #75. No retrains needed anywhere. Note LD#72 CLOSED (superseded/refit done).

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
LD#80 (v2 underperforms v1) → rollback COMMITTED 2026-07-28 but was a production no-op; actually fixed 2026-07-30 (NexusMind 96d9acc). v1 weights on HF Hub + NexusMind.
Root cause: v2 deployed without Phase 5 shadow comparison. 190-sample test set was not production-representative.
```
**Status:** v1 active, VERIFIED 2026-07-30 16:00 cycle (log "LD#80: ignoring gpu-server", zero /commerce/predict on gpu-server since). v2 code retained for reference.

### Chain 7: Summarizer Model Swap (ovr.news standalone, low dep)
```
ovr#270 (swap gemma3:27b → gpt-oss:20b) ↔ ovr#235 (held-out validation gate) ↔ ovr#267 (summarizer audit findings)
```
**Status:** Self-contained in ovr.news. Test with #235 gate.

### Chain 8: Google News Stub Fix (NEW 2026-07-30 — ovr#275 root cause)
```
FS#118 (resolve CBMi redirect at collection time) → ovr#275 (gn_* stubs never get summaries) [+ NM#278 dedup-threshold retune catches the dup-stub symptom]
```
**Status:** Owner leaned toward ingestion-time resolution (session 2026-07-30). FS#118 is the implementation home; ovr#275 closes behind it.

## Priority Rankings

### P0 — Active / Blocking / Revenue-Affecting

| ID | Repo | Title | Why P0 |
|----|------|-------|--------|
| **LD#76** | llm-distillery | Calibration audit: deployed filters crush good content below medium boundary | Umbrella for #74/#75/#72. Likely ONE raw_min-drift root cause. |
| **LD#74** | llm-distillery | Belonging v1: raw ordering intact, medium boundary too high | Good content scoring 3-4, should be higher. |
| **LD#75** | llm-distillery | nature_recovery v2/v4: raw-scale collapse | Model fires near-zero for ~everything. |
| **NM#206** | NexusMind | Filter timeout handling | Production reliability. |
| **NM#279** | NexusMind | Stale normalization: uplifting v7 (Apr 6) + belonging v1 (Mar 30) | NEW — same refit pass as LD#76 umbrella. |

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
| **LD#73→NM#274** | chain | Armed conflict / violence promotion prefilter (see Chain 2) | **v1 shadow-deployed 2026-07-28** — code + models already in NexusMind; config enabled. Shadow accumulation next. |
| **NM#275** | NexusMind | Cross-language story dedup (MapBiomas case) | Content quality — EN orphaned from NL/ES/PT clusters. |
| **ovr#214** | ovr.news | Summarizer returns source-language output in english_* fields | Content quality bug. |
| **LD#23** | llm-distillery | Fix cultural-discovery evidence_quality dimension (MAE 1.31) | Long-standing scoring quality gap. |
| **LD#71** | llm-distillery | nature_recovery v5: lift recall via medium-band enrichment | Follow-on from v4. |
| **LD#70** | llm-distillery | nr v4: admit delivered protection wins (MPAs / protected acreage) | Scope gap in v4 oracle prompt. |
| **ovr#255** | ovr.news | Academic articles get irrelevant stock photos | Content presentation. |
| **ovr#256** | ovr.news | US-centric abbreviations in titles | International readability. |
| **NM#231** | NexusMind | uplifting v7 under-scores non-English documented-outcome news | 19 panel-confirmed examples. |
| **ovr#204** | ovr.news | Remove hardcoded obituary detection | **UNBLOCKED 2026-07-30** — enforcement live upstream; do after one overnight sanity check. Effectively P1. |

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

### Batch A: Next Session

1. **Overnight enforcement sanity check** (15 min) — blocked-count stable, spot-read ~10 blocked titles
2. **ovr#204** — remove ovr.news hardcoded obituary filter (Chain 1 final link)
3. **LD#76 calibration audit (P0)** — diagnose root cause across #74/#75/#64; fold NM#279 refits into the fix pass
4. **LD#82 violence v1 shadow audit** — 53 flagged articles from first run
5. **NM#206 filter timeout handling** — production reliability

### Batch B: Shortly After

1. **LD#74/#75 + NM#205/#279 refits** — apply the root-cause fix from the #76 audit across all stale filters
2. **LD#84** — solutions oracle prompt router fix (v7 prompt only; do NOT edit committed v5/v6 prompts)
3. **LD#81** — pin/align sklearn across training+inference (b650 skew gotcha 2026-07-30 is corroborating evidence)
4. **FS#118 → ovr#275** — Google News redirect resolution at collection (Chain 8)
5. **NM#278** — dedup threshold retune for title-only E5 space

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

1. **LD#73 → NM#274** — ✅ DONE 2026-07-28: violence_promotion v1 shadow-deployed
2. **violence_promotion v2** — shadow accumulation → panel validate → retrain with more data (currently 1,957 samples, recall 0.55)
3. **LD#71 + LD#70** — nature_recovery v5 recall lift + protection scope
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
