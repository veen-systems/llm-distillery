---
name: project-session-2026-10-16-canary-lab
description: Session 2026-10-16 — #157 provenance stamps; read surface rounds 6-7; #176 near-dup leakage (EXP-051); #177 oracle canary LIVE for human_thriving (EXP-052); lab moved to ~/lab/llm-distillery; b650 standing rule + 3.0 GB cleanup
metadata:
  type: project
---

# Session 2026-10-16: provenance, the canary, the lab move

**Spend:** ~$0.55 DeepSeek + <$0.02 Gemini (scorer estimates, off-peak). **Deployed:** nothing (oracle-side only).
**Owner's machines:** lab `~/ld-lab` → `~/lab/llm-distillery` (clean cut); crontab line repointed (old line in the
session scratchpad, gone with it); b650: 785 files / 3.0 GB of finished results deleted (owner go, snapshot `c163fe7f`);
sadalsuud `~/ld-scratch` and `~/canary_177` deleted by the infra session. Commits `ae132c7` .. `d0f3270` + this close.

## Ask and threads

Ask: "continue" (TODO 0b first), then the owner's picks: #177 + #176, the lab move, wrap-up.
- #157 stamps (served model, full prompt sha256) → CLOSED for phase 1; issue open for the fingerprint question (H-OC3).
- #163 read surface rounds 6–7 (498,514 → 469,006) → PARTIAL, continues (TODO item 2).
- #176 near-dup leakage → CLOSED (EXP-051; warn-only report in prepare_data); owner to close the issue.
- #177 canary → LIVE for human_thriving (EXP-052); OPEN: cross-family panel, other filters; H-OC1/H-OC2.
- Lab move, b650 rule (CLAUDE.md + decision doc), b650/sadalsuud cleanup → CLOSED.
- OPEN, not started: #179 label audit, #178 datasheets; H-CTX-3 revisit overdue.

## Lessons (gotcha log 2026-10-16)

- A review found three holes in a gate that tests and live proof had passed (stripped-hash path unguarded, oracle not
  bound, NO-VERDICT missing): verification is not review, again.
- A mutant outlived its restore in a `.pyc` → mechanized (`tests/conftest.py`).
- A "6 h" freshness window was my gloss on the owner's "every labelling run" — caught by review, made single-use.
