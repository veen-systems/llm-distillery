---
name: project_session_2026_09_26_decisions_v10
description: Session 2026-09-26 afternoon → 09-27 — START HERE A verified, owner rulings B1–B4, ≥7 pool, runtime-only deploy (#164 closed, #165 filed), Thriving cutover live, v10 trained and NOT DISTINGUISHABLE, diagnostic adj4p running
metadata:
  type: project
---

# 2026-09-26 (afternoon) → 09-27 — decisions, the ≥ 7 pool, v10

**Spend: ≈ $1.11 oracle** (DeepSeek, off-peak, counted tokens). **GPU: b650** (v10 51 min; adj4p running).
**Deploys: ovr.news#373 merged by the owner** (Thriving reads human_thriving v9, v7 drains); NexusMind#536 (runtime-only
`filters/common`) merged by the NexusMind session. llm-distillery: deploy script changed, nothing deployed from here.

## Arc
Opening ask: "continue" (START HERE A, then B). Then "help me make decisions", then each follow-up.

| Thread | State |
|---|---|
| A: verify #372 / harm cap 6000 / v9 live, from outcomes | **closed** (TODO A; #372 124/124; 16 blocked by ovr.news#304) |
| B1 cutover #151 | **closed**: ruled, #373 merged, outcome checks on #151 |
| B2 ≥ 7 pool + hard negatives | **closed** (`docs/evidence/2026-09-26-thriving-ge7-pool/`) |
| B3 compensation ruling | **closed** (rulings file § 6) |
| B4 #164 | **closed**: runtime-only deploy (`356cd70`, fixes `054a0a3`), #165 filed |
| Review of `356cd70` | **partial**: round 1 (7 lenses) done + fixed; **round 2 NOT run** |
| v10 (adj4) | **closed**: NOT DISTINGUISHABLE, v9 stays (`docs/evidence/2026-09-26-v10-retrain-gate/`) |
| Diagnostic (b) adj4p | **open**: training on b650 since 09-27 09:59; pickup in TODO 2b |
| Owner's 3 reader flags | **closed**: v7 drain; v9 and v10 reject all 3 (must-reject check) |
| Other lenses (adjudication) | **not yours**: advised measure → pilot → relabel; NR pilot already failed |
| TODO item −1 (thin `memory/MEMORY.md`) | **open**, untouched |

## Findings worth keeping
- **The ≥ 7 pool did not buy volume.** v10 on its own held-out rows was STRICTER (recall 0.60 vs 0.87). Among
  production ≥ 7 articles, uplifting-only ones were 44.8% in scope (vs 11.5% at its op-point), and the oracle
  called 41.8% of the not-in-scope ones in scope.
- **Detector weights reach NexusMind only through the deploy copy**, and NexusMind's per-file `.sha256` sidecars
  would break a retrained detector at load (reproduced by a review lens). Guard: deploy step 0.6. Real fix: #165.
- **v7 and v9 share dimension names**; I asserted otherwise (gotcha).
