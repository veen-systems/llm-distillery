---
name: project_session_2026_07_30
description: "Session 2026-07-30 — obituary v4 op-point corrected to 0.90 via owner flag, swap committed (auto-deploys), FN-delta owner gate before enforcement"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0da48d0e-48d0-4cad-8b99-2417e6973314
  modified: 2026-07-30T17:54:05.330Z
---

# Session 2026-07-30

## What happened

Owner's 2026-07-29 ovr.news flag (Farouq Hilal tribute) proved obituary v4 at the planned 0.95 op-point would miss real obituaries (v3: 0.977, v4: 0.937). LD#83's "FN just wastes 5ms" framing was falsified — for a blocking prefilter, an FN is the product failure.

- **Evidence** (reviewer-reproduced): heldout 1,562 rows — v4's 5 FPs at 0.90 = identical set as at 0.95, recall 0.608→0.683; 4-model panel on the June [0.90,0.95) band: 35/37 genuine obituaries.
- **Executed**: NexusMind `02da4fe` — v3→v4 swap + threshold 0.90, SHADOW only. Auto-deploys next pipeline cycle (ExecStartPre auto-pull; `deploy/gpu-server/main.py` ∈ SCORER_PATHS — the RUNBOOK claim it doesn't propagate was stale, corrected in `c5f1df2`). llm-distillery `d4d0a5c` + `9a1492d`: artifacts, memory, curate.
- **3-reviewer battery** (correctness/methodology/deploy-risk): numbers reproduce exactly; all findings fixed or filed on LD#83.

## Owner decisions made

- #83 has priority (over LD#76 etc.).
- **FN-delta gate before enforcement**: quantify which obituaries v4@0.90 misses that v3@0.95 caught (~20 heldout) — owner explicitly asked for this investigation next session before trusting v4 over v3.

## Next session

1. Verify auto-deploy: `curl gpu-server:8000/health` → `obituary_detector_v4`; Farouq rescores 0.937 flagged. Never `git pull` on sadalsuud without `deploy_filters.sh` (pull-only = unvalidated v3@0.90).
2. FN-delta panel check (owner gate) → shadow flag-rate review → sign-off → enforce → ovr#204.
3. LD#83 carry-overs: `_obituary_model` stamp (v3/v4 stamps mixed ~7 days), panel-check the 5 surviving heldout FPs, dead `has_model` guard.
4. Queued: LD#76 calibration audit (P0), #82 violence shadow audit, NM#206.

## Related Memories

- [[project_session_2026_07_28]] — prior session (v4 trained)
- [[feedback-claim-requires-verify]] — extended with point 6 (prose describing code is a claim; read the implementation)
- [[cross-repo-prioritization]] — Chain 1 updated in repo memory

## Session 2 (same day, ~09:00-12:30)

- **v4@0.90 shadow deploy VERIFIED** (12:08 cycle: auto-pull clean ff, v4 loaded, Farouq 0.9372→flagged via deployed endpoint).
- **FN-delta owner gate FAILED**: 21/28 gap articles are real obituaries (4-model panel, 12 unanimous); five score <0.70 on v4 → threshold can't fix; **enforcement sign-off BLOCKED, v5 retrain needed** (21 panel-graded hard positives ready). FP5: 3/5 of v4's heldout "FPs" are oracle mislabels → true precision >0.979. All on LD#83 + llm-distillery aaef1d0.
- **Owner asked (LD#83)**: interim shadow — keep v4@0.90 or revert to v3@0.95?
- **DeepSeek-commit review (owner request)**: 4 parallel reviewers over Jul 26-30; fixes in llm-distillery 403429d, NexusMind 3f5c328+6728a77 (all pushed). Critical: LD#80 commerce rollback was a production NO-OP (fixed, verify next cycle: "LD#80: ignoring gpu-server" + zero /commerce/predict); code-drift check false-fired every run (fixed, hash verified vs deploy stamp); solutions v6 version/hub defects (v6 weights now on Hub). Issues: LD#84, NM#278.

## Session 3 (same day, ~16:00-20:30) — OBITUARY DONE THROUGH ENFORCEMENT

- 16:00-cycle review-fix verification: all green (LD#80 line at 16:08, zero /commerce/predict since 16:00, no drift lines, `_obituary_model: "v4"` on 4542/5320 rows, 778 absent = pre-stamp carryovers).
- **v5 trained on gpu-server** (v4 corpus + 21 FN-delta hard positives) → 3-reviewer battery (fable/opus/sonnet) → methodology reviewer found the excl-33 eval was biased both ways; corrected table (excl-24, n=1538) verified by hand; June-increment panel (40/65 flags): 0.71–0.83 precision, **threshold-insensitive**.
- **Owner adjudicated 14 boundary rows in-session**: grief-vs-news rule (block funerals/memorials/mourning ANY age; keep death-as-news) — flips BOTH sharpened-broad clauses → LD#85 (v6 relabel).
- **Owner went recall-first** ("I just hate obits coming through") → **ENFORCEMENT SIGNED OFF AND SHIPPED: v5 @ 0.85**, NexusMind `b904edc` (`obituary_blocked` in dedup gate after commerce, config-gated: rollback = `enforce: false`; stamps always written). 954 tests green. v5@0.92 shadow swap `89f3c58` preceded it same evening (vendored pkl+sha256, EXPECTED_HASHES swap map from deploy-risk reviewer).
- **b650 (Arian's 3090 Ti 24GB) commissioned**: account `jeroen`, uv venv (system venv broken), torch 2.13/cu130, sklearn pinned 1.8.0, corpora+v3/v4/v5 copied, 831 rows/s embed. ⚠️ ST 5.6.1 vs gpu-server 5.2.2 → cross-box score skew max 0.16: eval on the training box.
- Lens scoring is NOT an obit backstop (102 obit-flagged rows passed lens thresholds in one cycle, mostly belonging); violence filter is promotion/glorification, not death news (owner).
- **NEXT SESSION FIRST: verify first enforced cycle** — sadalsuud log "N obituary" in Loaded line + `obituary_blocked>0`; gpu-server health lists `obituary_detector_v5`; filtered rows `_obituary_model: "v5"`. Then ovr#204. LD#85 (v6) PARKED indefinitely by owner (~20:45) — reactivate only on an owner obit-flag or visible over-blocking harm. Queue after ovr#204: LD#76 (P0) → #82 → NM#206.
