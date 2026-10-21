# EXP-055: cross-family panel for human_thriving (#177 step 6), IN PROGRESS

The pre-registration is `PREREGISTRATION.md`. The analysis is `analyse.py`, committed before any panel score was
read (`1185a13`). A bug fix after that commit made the pass/block ratings explicit strings, because the
agreement library refuses bools; it changes no measure.

## State, 2026-10-21

**Interim, local members only: `result-interim-locals.txt`.**
- L1 (qwen3.8:27b) is INELIGIBLE under the pre-registered 95% parse bar. Only 85 of 100 items have both
  runs. On some items it thinks until it fills the 16K context: 15 empty replies and 6 cut-off JSONs (21 failed rows: 11 in run 1, 10 in run 2). No
  prompt was truncated; the longest is 13.3K tokens.
- L2 and L3 agree with each other at alpha 0.695 (nominal). Both pass far more than the oracle does: L2 62 of
  the 95 items it parsed, L3 55 of 100, against the oracle's 30 of 100.
- Against their majority, the oracle's specificity is 1.000 (0 false positives of 33; the exact 95% bound is
  ≥ 0.894, added after review, not pre-registered) and its recall 0.528. With two members the "majority" is
  unanimity: all 14 disagreements are ties and are left out. That follows the pre-registration's "ties counted
  as their own row": they are reported, not voted.

⚠️ **This is not a verdict.** The majority is two local models with a shared lenient bias, and the cloud
member is missing. "The oracle blocks what the panel passes" also fits a deliberately conservative oracle
(memory: conservative oracle prompts produce better students). The final reading waits for P1.

**Interim 2, with P2 (Claude Sonnet 5.5, k = 2): `result-interim-with-P2.txt`. Still NOT a verdict.**
- P2 is ELIGIBLE: 100/100 parsed in both runs, and 3 self-flips (bar 7).
- **P2 passes only 9 of 100, the STRICTEST member.** The oracle passes 30, L3 55 and L2 62. The families disagree on
  WHERE the bar sits, not only on items.
- **P2 is closest to the oracle:** P2–oracle AC1 0.694, raw 0.790. P2 against the local members: AC1 −0.049 (L2) and
  0.186 (L3).
- Panel alpha (pass/block) over L2, L3 and P2 is 0.199. That is poor agreement, so a majority of these three is a
  weak anchor.
- Against that majority (3 ties left out), the oracle's specificity is 0.957 [0.889, 1.000] and its recall 0.560.
  "Panel positive" is driven by the two lenient local members.
- **Reading:** the oracle sits BETWEEN a lenient local pair and a strict Claude. Nothing so far says the oracle is
  wrong; it says the anchor is not settled. P1 (Gemini) is the tiebreak family.
- **Spend:** P2 cost $4.12 of the promo credit (smoke $0.04 + 2 × $2.04, Batch card from returned usage); the cap
  is $12. Lab: `experiments/2026-10-21-cross-family-panel/{P2-run1,P2-run2}`.

**P1 (Gemini 2.5 Flash):** 20 of 100 items done.
- The billing key's prepay is depleted (HTTP 402).
- The other key is free tier, limited to 20 requests per day. The owner chose (2026-10-21) to finish on it
  over 4 days: a transient user timer, `ld-exp055-p1b.timer`, runs 10-22 to 10-25 at 09:30 and appends to
  `~/lab/llm-distillery/inbox/situla/2026-10-21-exp055-P1-work/P1.jsonl` (moved out of /tmp at close).
- ⚠️ This is a deviation: D2 ruled Gemini with a cost check against the paid realtime card, and D3 capped
  "paid calls"; the free tier costs $0. Free-tier terms may let the vendor use submitted content
  (from memory, unverified).
- To undo: `systemctl --user stop ld-exp055-p1b.timer`.

Data: lab `experiments/2026-10-21-cross-family-panel/{L1,L2,L3}` (hash-verified pulls). P1's working file is
in the lab inbox above until it finishes.
