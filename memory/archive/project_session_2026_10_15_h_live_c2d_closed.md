---
name: project-session-2026-10-15-h-live-c2d-closed
description: Session 2026-10-14/15 — ovr's data-quality issues #176–#179 filed, Kev base-model experiment #180; EXP-049 H replay; ranking H LIVE on ovr.news; daily five-lens page capture (user crontab, until 11-15); c2d EXP-050 not worth a gate, owner CLOSED the lowering lever; read surface round 5; cp -r package gotcha mechanized
metadata:
  type: project
---

# Session 2026-10-14/15: H live, c2d closed, the lowering lever closed

**Spend:** $0 oracle. b650 GPU only (2 c2d seeds trained, 3 packages scored, qwen tagging). **Deployed:** nothing from
this repo. **Owner's machine:** one user crontab line on situla (below). Commits `a86f0af` .. this close.

## Threads (closed / partial / open)

- **ovr's data-quality checklist** → CLOSED: #176 (near-dup leakage across splits), #177 (oracle canary set), #178
  (datasheets), #179 (label-quality audit), each with ovr's pointers; linked to veen-systems/pipeline-atlas#169.
- **NexusMind requests** → CLOSED: six questions answered; review posted on ducroq/NexusMind#669 (Contract D); correction:
  human_thriving v9's "adjudicated" labels are blind Claude adjudication under the owner's rubric, not a human anchor set.
- **Kev / Jev** → FILED, not scheduled: #180, ledger H-SB1 (Qwen3.5 base vs Gemma-3-1B, judged on specificity).
- **EXP-049, belonging v3 on ranking H, offline** → CLOSED: floor means H 5.20 / old ranking 6.40 (dated, post hoc):
  the old ranking fails the bar even on qwen's undercount; H undetermined.
- **Ranking H LIVE** on ovr.news 2026-10-15 (commit `07cdb7e0`, first build 07:40:42Z), recorded in
  veen-systems/pipeline-atlas#170 by the ovr session.
- **Daily page capture** → RUNNING until 2026-11-15: user crontab on situla, five lens pages at 16:30 local into
  `~/ld-lab/inbox/ovr-lens-pages/`; hardened at close (`curl -fsSL --retry 2`, errors to `curl.err`). Serves the
  Belonging re-baseline (≥ 10-22) and lens assignment (H-LA2; the owner: "sometimes, I really wonder").
  ⛔ Remove after 11-15 (`crontab -r`, the only line).
- **c2d, EXP-050** → CLOSED, owner RULED: lever CLOSED. Recall guard 0.902 / 0.804 (bar 0.9); H top-30 qwen personal
  6.14 → 1.29, but qwen chose the lowered rows and counts them, and c2d thins the display-eligible pool to 0.38–0.70.
- **Read surface (#163) round 5** → 505,983 → see TODO item 2 for the close figure.
- **OPEN:** the on-site re-baseline (≥ 10-22, TODO 0a); ovr's rollback panel 10-23; normalization refit ≥ 10-24;
  b650 / sadalsuud scratch copies of 10-15 (lab holds them; deletion needs a restic snapshot + the owner's go per item).

## Lessons (detail in `memory/gotcha-log.md`)

- A written gotcha did not stop a recurrence: the `cp -r` package import bug of 10-12 hit c2d. Mechanized:
  `train.py` `assert_package_imports_self()`, seeded-positive test, two mutants killed.
- A pre-registered control printed only in the transcript is not evidence; the report script must print it.
- A prediction miss of 2–3× (c2d's 4.86 vs 0–2) was the instrument signal: the judge had picked the training target.
