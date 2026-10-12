---
name: project-session-2026-10-12-belonging-c2c
description: Session 2026-10-12 (afternoon/evening) — belonging focus tag ruled and tested (v3 fails the ≤ 6/30 bar, owner 10/30); candidate c2c (personal training rows scaled down, $0) FAILED its pre-registered recall guard; review found a gatekeeper build defect; read surface round 3 (→ 519,680 at close)
metadata:
  type: project
---

# Session 2026-10-12 (afternoon / evening): belonging focus tag and candidate c2c

**Spend:** $0 oracle (owner: no paid oracle). Local qwen3.8:27b + training on b650. Two Claude review subagents at
close (code correctness, claim consistency). **Deployed:** nothing; v3 stays live. Commits `a4b2d48` .. `764813a` + close.

**Ask (owner):** "continue" (TODO START HERE) → item 2 read surface round 2, then item 0a. Later: "no paid oracle …
go through our training data on the B650 and reduce the score for the personal ones"; at close: wrap up, prune.

| thread | state |
|---|---|
| Item 2 read surface, rounds 2 + 3 | ✅ 603,408 → 514,588 after the moves (519,680 at close); ceiling 524,900 |
| 0a: how "personal" is measured | ✅ owner RULED a separate `focus` tag |
| 0a: v3 vs the bar | ✅ owner 9/30 (10 corrected) → v3 FAILS ≤ 6 |
| Local tagger | ✅ qwen passes rule 2 vs 9; FAILS the ±2 half vs the corrected 10 (undercounts, a floor) |
| Candidate c2c | ✅ FAILED (recall guard 0.807 / 0.862 < 0.9); build defect: 11/42 rows trained to 3.42 |
| Next belonging step | open — owner's choice (TODO 0a ▶ NEXT) |
| `test_framework_language` ('Herstel' quoted in the 10-10 session file) | open — owner not answered |

**Lessons (gotcha log, 2026-10-12):** a `cp -r` package loads the source's model; label scaling must assert the
EFFECTIVE (gatekeeper-capped) score; `lab.py pull` dest is relative to the lab root.
⛔ **Mine:** a build defect (the gatekeeper) that review found only after the verdict; the README first claimed every
arm passes after the owner's correction (qwen fails the count half); swapped seed MAEs; a guess (seed band) written as fact.
**Measured, worth keeping:** all 30 live-page rows were in the 33,393-row draw, but only 7 were in v3's raw top 30
(H-BB7): the site's ranking, not only v3's score, shapes the page top.
