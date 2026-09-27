# A lexical "clause survival" check for CLAUDE.md trims: REJECTED (2026-09-27)

**Result: word-overlap matching cannot tell a compressed clause from a lost one. Not shipped.** The script
(`check_claude_md_trim.py`, kept here unwired) was built for the `memory/gotcha-log.md` § Mechanized row
"a trim that keeps every token but drops an operative CLAUSE" (2026-09-26).

## Method
- **Operative clause:** a sentence of the old `CLAUDE.md` carrying ⛔, a bold imperative, or never / do not /
  must / NOT / ONLY.
- **Survival:** some paragraph of the new file (or a declared `--moved-to` file, or a file named on the
  clause's own line) holds at least *k* of the clause's content words, plus every polarity class
  (NEG, ONLY) the clause has.
- **Seeds** (built from `CLAUDE.md` at `a6cd7cf`; all three are known losses):
  - S1 deletes "Lenses are perspectives … never exclude adjacent lens content in oracle prompts (ADR-015)";
  - S2 deletes "Compare filters ONLY on recall + specificity (…)";
  - S3 flips "never rank filters on MAE" to "rank filters on MAE".
  S1 and S2 are the two clauses the 2026-09-26 trim is recorded as losing.
- **Control:** the reviewed 2026-09-26 trim, `fa6125c:CLAUDE.md` → `734b806:CLAUDE.md`, with
  `734b806:docs/decisions/framework-adoption-history.md` declared as the destination. Its five lost clauses
  were restored in that commit, so every flag on it is a false alarm.

## Measured
| stemming | k | seeds caught | identity flags | control false flags (of 125 clauses) |
|---|---|---|---|---|
| no | 0.4 | 1/3 | 0 | 32 |
| no | 0.5 | 1/3 | 0 | 42 |
| no | 0.6 | 2/3 | 0 | 56 |
| no | 0.7 | 2/3 | 0 | 77 |
| yes | 0.4 | 1/3 | 0 | 25 |
| yes | 0.5 | 1/3 | 0 | 40 |
| yes | 0.6 | 2/3 | 0 | 52 |
| yes | 0.7 | 2/3 | 0 | 71 |

No setting catches S3: the polarity flip survives because the same paragraph carries other negations. The
first draft extracted only BOLD imperatives and would have missed S1 entirely: in today's thinned `CLAUDE.md`
the ADR-015 rule is plain text.

## Why it fails, and what does work
Halving a file compresses clauses ("Dimensional scores (0-10), never tier/stage classifications" becomes
"0-10 per dimension, never tiers"). Word overlap scores that as a loss, and a paraphrase that keeps the
words while dropping the rule as a survival. The check that caught every real loss is a **clause-loss review
lens** that reads the old and new text: 5 clauses on 2026-09-26, 2 clauses plus a narrowed trigger on
2026-09-27. What can be mechanized is making sure that lens RUNS, not replacing it.
