---
name: project_session_2026_08_03_evening
description: Gate verification (obituary/commerce/violence), commerce provenance fix, retired-filter removal, seeded cycle replay for #95 — four changes, two deployed
metadata:
  type: project
---

# Session 2026-08-03 (evening)

Follows the 16:25 curate close. Started as a cross-repo issue re-inventory,
became gate verification and four shipped changes.

## Shipped

| What | Where | Deployed? |
|---|---|---|
| Commerce provenance fix | NexusMind `c696ea3` | **yes**, sadalsuud |
| Seeded per-run shuffle (cycle replay) | NexusMind `f7fef85` | **yes**, sadalsuud |
| Score noise floor recorded | LD `efab69d` | n/a (docs) |
| sustech v3 + foresight v1 removed | LD `289bda1` | n/a |
| Chain 14 root filed | NM#292 | n/a |
| Writing rules for chat answers | LD `73f8fbd` | n/a |

## Gate verification (the session's main question: "is obit/violence/commerce OK?")

All three checked against the running box, not config.

- **Obituary — enforcing, provably.** `_obituary_model: v5` on 100% of 14,572
  live rows; 2,109 excluded at load in the 16:12 cycle. The decisive check:
  **max obituary score among surviving rows is 0.8488, zero survivors ≥ 0.85.**
  Nothing leaks past the threshold.
- **Commerce — enforcing, LD#80 pin holds.** `_commerce_model: v1` everywhere,
  no `gpu-server-unpinned`. 9,072 excluded at load.
- **Violence — inert by design.** `enforce: false`; stamps on 100% of rows;
  53–95 flagged per cycle (2.0–4.4%). Two gates before any flip: **#82** (audit
  unstarted; v1 recall 0.55) and **NM#286 item 3** (stamping skipped in three
  run modes — harmless while off, dangerous the moment it is on).

## The commerce defect, and why it was invisible

The already-scored guard keyed on `_commerce_score` alone, so any row scored
before the `_commerce_model` stamp existed (NM#281, 2026-08-01) was skipped
forever and could never be back-filled: **205,444 of 237,813 corpus rows
(86.4%)** had a verdict with no model version. Verdicts were never wrong — the
audit trail was missing, which is precisely what LD#80 added the stamp for.

Guard now requires both keys. Unstamped rows fall through to the **existing age
check**, so the one-time re-score is bounded to 21,024 rows (~15 min), not
205,444. A test pins that bound.

## Call path settled

The gpu-server scorer unit sets `PYTHONPATH=/home/hcl/NexusMind`, so it loads
`/home/hcl/NexusMind/filters/` — which carries the #93 changes.
**`/home/hcl/llm-distillery/` is on no path**: a stale decoy that reads as
authoritative. Worth deleting.

## #90 is not ready to start

Both candidate templates already passed ground-truth gates —
`nature_recovery v4` (recall 0.65 / prec 0.85 / F1 0.736, n=391) and
`solutions v6` (0.67 / 0.82 / F1 0.739, n=1032). So "do the latest scorers
work?" is answered. The real question is **which template elements are
load-bearing**: #94 (gatekeeper never binds in 191,616 articles) and #92
(short-content defect) say at least two of the six things #90 proposes copying
do not do what the config claims. Audit before spreading.

## Owner directions taken this session

- **Renaming `nature_recovery` → `recovery`** is right and already specified in
  #90; confirmed the tab name against ovr.news (`CLAUDE.md` lists the lens as
  **Recovery**). Per ADR-012 it executes at the v5 bump, not in place.
- **Chat answers were too dense** ("many times, I have no idea what you are
  talking about"). Rules written into CLAUDE.md → "How To Write Answers Here".
  The `i-have-adhd` plugin was installed, evaluated and removed — it fixes
  burying the answer, not undefined jargon, which was the actual complaint.

## NEXT SESSION

1. **Verify the next cycle**: a `Run seed: … (from clock)` banner line, and the
   commerce line showing `processed` ≈ 21,000 **once**, then back to normal. If
   `processed` stays high across several cycles, the stamp is not sticking.
2. **Audit which `solutions v6` template elements are load-bearing** before any
   #90 work. Start from #94 and #92.
3. **#82** — read the violence-flagged articles in
   `data/prefiltered_out/violence_promotion/`. Cheapest decision input on the
   board; decides whether that filter is worth keeping at all.
4. **Flagged, not done:** gpu-server still holds `foresight` and
   `sustainability_technology` filter packages under `~/NexusMind/filters/`.
   Deleting them is *not* obviously safe — `scripts/smoke_test.py` still
   exercises foresight (see NM#289), and the 2026-07-22 gotcha is a deploy that
   fail-closed for exactly this reason. Update the smoke path first.

## Related

- [[score-batch-shape-noise]] — the #95 finding and what replay does/doesn't fix
- [[cross-repo-prioritization]] — third pass, updated with all of the above
- [[filter-status]] — sustech/foresight marked REMOVED
- [[gotcha-log]] — four new entries, one recurrence
