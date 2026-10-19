# Session 2026-10-18/19: read surface round 8, H-CTX-3, #177 canary rollout, Scaleway trial, #179 audit

**Opening ask:** "continue" (TODO ▶ START HERE, top down). Later owner asks, in order: canaries for the live
filters → pause, talk to infra about other oracle hosts → "Resume the canaries as they are" + "Add an EU-hosted
oracle trial" (infra's Scaleway credit; models: my recommendation) → "Use b650 now" → "go" → "Start #179, read-only".

## Threads

| thread | state |
|---|---|
| #163 read surface, round 8 (`fb481b6`, 475,230 → 469,090) | closed |
| H-CTX-3 revisit (`3acf1a9`, supported, weakly) | closed |
| #177 canaries: belonging (Gemini), cd v5, nr v4, solutions v6 (DeepSeek), EXP-053 | closed: all LIVE at k = 1 |
| Scaleway EU oracle trial, EXP-054 (descriptive, not pre-registered) | closed, parked |
| #179 label audit, read-only, posted on the issue | closed; fixes await owner rulings |
| review battery (4 lenses + round 2) and its fixes (`4a92805`) | closed |
| #177 cross-family panel; #178 datasheets | open (not started) |
| review leftovers: `score_ollama_oracle.py` ungated; one-use race; served model unchecked at labelling | open, in TODO |
| host cleanup: b650 `runs/canary_177b` after the 10-20 12:00 snapshot; sadalsuud `~/canary_177b` | open; sadalsuud needs the owner's go |
| push | not yours: owner confirms |

## What landed

- Canary op-point is per filter (`--op`, cross-checked against `normalization.json` raw_min); `canary.py run`
  drives `batch_scorer` for Gemini filters. Five prompts guarded now; uplifting v7 is not (owner scope).
- Measured: noise F1 cd 5, nr 3, solutions 11, belonging 3; every P run FAILED at k = 1; L1 PASS ×4.
  solutions' P runs failed on shift alone (closest by 0.013); belonging 1.42× its bar. Spend ≈ $2.47 DeepSeek
  (scorer estimate) + Gemini (not estimated) + Scaleway ≈ €2.31 (infra's credit, estimate).
- Scaleway DeepSeek V4.1 Flash with `reasoning_effort: "none"` agrees with the DeepSeek API on human_thriving's set
  (4 flips, +0.02); Mistral Medium 3.5 does not; ~30× per canary without a cache discount (estimate).
- #179: human_thriving v9 training mixes two prompts (6,130 rows `003cd35a5122`, 1,079 `c4705408c477`), documented
  nowhere in the package.
- Review found two real gate holes, both fixed with seeded tests: a scrape-junk row left an older PASS admitting
  (two definitions of "done"); a Gemini thinking budget was not part of the oracle key.

## Mine (errors)

- Told infra 105/105 (was 106); #179 comment said "about 43,000" (44,423). Both corrected.
- README "about a quarter of the simulated drift" (wrong, 0.85) and "$2.56" (a sum I added twice) — caught by me
  before commit; "~20×" Scaleway ratio mixed currencies (≈30×) — caught by review.
- EXP-053/054 were corrected IN PLACE before the push (same session, unpushed); the append-only rule was read
  as protecting published readings.
