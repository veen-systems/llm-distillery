---
name: project-session-2026-10-09-belonging-v3-live
description: Session 2026-10-07/09 — belonging adj1 FAIL (set 1), c2a FAIL (set 2, recall), c2b PASS (set 3) → belonging v3 LIVE 2026-10-09 (NexusMind run bd00dad6); rollback mechanism corrected; a false early-refit trigger caught; TODO pruned 39.6 → 20.2 KB
metadata:
  type: project
---

# Session 2026-10-07 evening → 2026-10-09 morning

**Spend (Gemini, tokens × list price, billing UNCHECKED):** held-out set 2 $2.64, set 3 $2.64, 256 hard-negative k=3
labels ~$1.40 (estimated). Claude Opus judge subagents: 22 + 24 (set 2 / set 3, ~2.4M + ~2.6M tokens). b650 GPU: 4 trainings
(adj1 runs 1–3, c2a, c2b) plus scoring. **Deployed:** belonging v3, by NexusMind (PR #627), owner GO 2026-10-08.

## The ask and the threads

Opening ask: "pls continue. how is the darta quality?" → TODO item 0, the belonging retrain. Owner asked to be helped
through decisions; tired of spot checks (→ judge-statistics tripwire instead); delegated the c2a/c2b comparison to ovr
(EXP-029), then vetoed its pick (c2a gated first; failed); "why wait? we have a big database?" (→ set 3 from monthly archives);
GO on the switch; "talk to all the peers you need".

| Thread | State |
|---|---|
| belonging retrain → gated candidate | ✅ closed: v3 = c2b PASSED set 3 (k 76/83, Δspec +0.350 [+0.322, +0.376], partly by construction) |
| switch | ✅ closed: LIVE from NexusMind run `bd00dad6` (2026-10-09 00:08–01:24 CEST); 3 files measured (0.56% raw ≥ 4.0; v1 ~2.2%) |
| reader-side verdict | ⏳ open: ovr panel 2026-10-23 on v3-scored rows only → rollback rule (`filters/belonging/v3/STATUS.md`) |
| normalization refit | ⏳ open: ≥ 2026-10-24, `version == "3.0"` rows only |
| RUNBOOK deploy path (stale since NM#395) | ⏳ open: TODO item 2b; tell pipeline-atlas first |
| read surface (#163) | partial: TODO 39.6 → 20.2 KB; items c, d open |
| single-person stories; FM-S1; Gemini deprecation (4b); infra's oracle alternatives | not mine: owner |

## What to keep

- **Three held-out sets spent in one session.** Each gate was one-shot and pre-registered; set 3 came from NexusMind's
  monthly archives (`nexusmind_2026-08/-09`), wider and older than sets 1–2. Future gates need set 4 drawn fresh.
- **`--select-metric last`** (`20637ec`): `recall_medium` saturates on thin val positives (#144) and picked epoch 1.
- **Content-twin checks must run AFTER every drop** (a late footer twin refused run 2) — `build_adj1.py`, `gate.refuse_overlap`.
- **Rollback since NM#395 = previous scorer image + sadalsuud revert.** The image holds only the served version.
- **Early-refit trigger**: same measure both sides (v1 54%, v3 62% over 3 files; ledger `H-BB5`). The "< 100%" rule was mine and wrong.
- Peers: nexusmind-dc (deploy + run id), ovr-news-e2 (panel, display gate), pipeline-atlas-16 (atlas PR #122).

## Mine (what I got wrong)

The rollback mechanism (from the stale path); the population-mismatched trigger; a foreground ssh chain that died. All in
`gotcha-log.md` 2026-10-08/09.
