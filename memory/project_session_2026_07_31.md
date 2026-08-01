---
name: project_session_2026_07_31
description: "Session 2026-07-31 — obituary carryover diagnosed (47 shadow-era + 2 v5 FNs), LD#76 audit (11 agents) overturned the shared-root-cause premise, both refits + cd topic gate + NM#280 tier fix EXECUTED AND DEPLOYED, ADR-022 written, harmonization program filed (LD#90)"
metadata:
  type: project
---

# Session 2026-07-31

## Morning: obituary enforcement aftermath

- **Overnight sanity check PASSED**: blocked 1158→1208→1249 across 3 cycles, all-v5 stamps, v5 hash-verified. Learned + recorded: gpu-server scorer is DOWN between cycles by design (static unit, per-cycle lifecycle, ExecStopPost → ollama; logs UTC = local−2) — `memory/gpu-server.md`.
- **Owner obit sighting diagnosed — NOT an enforcement failure**: 47 shadow-era carryovers live on ovr.news (all ≥0.85, would block today; site `live_articles` view = 14d by published_date → washout ~Aug 13) + **2 true v5 FNs**: Yves Devos community-mourning (v3 .68 → v4 .44 → **v5 .12 — monotone regression**, hard-negative interference) and Teresa Alonso biography-rich obit (~0.28 all versions — stable blind spot). Rescore reproduced production stamp to 4 decimals. Owner: "it is what it is" — no purge, LD#85 stays parked; evidence banked on #85 + `obituary-v4-hypotheses.md` addendum 7.
- ovr-side session cross-verified (their 1,249 count matched; downstream death-rate 7.9%→2.9% past the boundary). Three washout windows reconciled on ovr#204: sentinel (3d) ~Aug 2-3, pipeline max_age (7d) ~Aug 6, site view (14d) ~Aug 13.

## LD#76 calibration audit (11-agent battery, all verdicts adversarially verified)

**"One shared root cause" FALSIFIED.** Full synthesis: LD#76 issuecomment-5140079896.
- `% norm<0.5` is a metric artifact (≈1−base rate; healthy ir is 75% "invisible" by it) — Dead Ends entry added.
- **uplifting v7: PROVEN unit-mismatch fit** (Apr-06 window contained ×1.1976 score_scale_factor-stretched scores; raw_max 9.54 > ceiling 8.35 impossible). **belonging v1: real drift** (+1.0–2.1 norm under-ranking).
- **Only shared mechanism: NexusMind `_assign_tier` double-cut** (raw thresholds on normalized scores → bottom ~40% of every filter's passers demoted).
- cd v5: dead prefilter (2828/2828 pass) + lens dilution; 3.5-op-point idea REFUTED by verifier.
- **nature_recovery v4 HEALTHY** — #75 was a measurement artifact (94% probe-capped rows + files predating normalization) — Dead Ends entry (probe-provenance trap).

## Owner decisions + EXECUTION (all deployed same session)

1. **#75 CLOSED** as measurement artifact.
2. **Both refits EXECUTED**: uplifting 18,130 arts (raw 5.0 → norm 5.17, was ~3.0), belonging 4,827. llm-distillery `bbe1d78`, NexusMind `0c35731`, byte-verified 3 locations; **live in the 08:12 cycle** (scorer log "fitted 2026-07-31T07:14").
3. **LD#86 cd topic gate FIXED + DEPLOYED** (`cfafde2`/`f0d6cc6`): multilingual TOPIC_GATE_PATTERNS (~120 stems incl. CJK/Cyrillic/Greek/Arabic), validated on 14,923 production rows: pass 24.5% (was ~100%), 0.23% model-visible collateral (mostly off-lens science). 13/13 self-tests.
4. **NM#280 tier fix IMPLEMENTED + DEPLOYED** (`73c1ec3`): visibility = raw ≥ op-point; normalized grades passers; caps keep legacy suppression; rollback env `NM_TIER_RAW_VISIBILITY_GATE=0`. Failure-set diff vs baseline: identical (35 pre-existing env fails). *[CORRECTED 2026-08-01: those 35 never existed — situla's bare `python` is the system interpreter, which lacks `trafilatura`; the repo's `venv/bin/python` runs 969 passed / 0 failed. NM#280 is fine, but it was verified against a phantom baseline. See gotcha-log.]*
5. **ADR-022 "Stamp Always, Decide Once"** written + Accepted: stamp triple + one config-gated drop point + config-flip reversibility. Violence gate verified NON-EXISTENT (no `enforce` key; config comment even prescribed consumer-side exclusion — the failed pattern). Filed **NM#281** (stamp triples + violence gate wiring) and **LD#89** (shared mpnet embed pass).
6. **Owner directive → LD#90 harmonization program**: all lens filters to the successful template + **renames**: uplifting→thriving, cultural_discovery→discovery, nature_recovery→recovery (at version bumps, ADR-012).

## NEXT SESSION FIRST: verify the ~12:00 cycle (three checks in one)

1. **Refits §6 step-4**: live uplifting row raw≈5.0 → norm≈5.2, `normalization_method: percentile`; belonging MEDIUM+ p90 norm → ~9.
2. **cd gate**: cd filtered file has `no_cultural_topic_signal` blocks > 0, pass ≈0.25; gpu-server log `prefilter_blocked > 0`. Then close #86.
3. **NM#280**: per filter `count(tier != low) == count(raw >= op-point)` (modulo caps); nr visible +27–37%. Then close NM#279 + LD#74 ("explained"); LD#76 umbrella closes when NM#280 verifies.
- ovr.news heads-up given: every lens's surfaced volume rises this cycle (refits + tier gate) — their volume sentinels may move.
- Queue after verification: NM#281 → LD#82 violence shadow audit → NM#206 → LD#90 program (start with cd v6 per #87). Aug 6: ovr sentinel re-derivation (ovr-side).

## Related Memories

- [[project_session_2026_07_30]] — prior session (obituary enforcement)
- [[cross-repo-prioritization]] — Chain 3 updated with audit + execution
- [[calibration-history]] — 2 new Dead Ends entries
- [[obituary-v4-hypotheses]] — addendum 7 (v5 FN classes)
