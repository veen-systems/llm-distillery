# Belonging held-out set 2: pre-registration (2026-10-08)

*Written and committed BEFORE the draw, before any oracle call and before any judging. Owner 2026-10-08: a FRESH
held-out set at 2× the size of set 1 (set 1, `../2026-10-03-belonging-heldout/`, was spent by v1_adj1's FAIL); "only the size
changes". Plan: `../2026-10-08-belonging-candidate2-plan/PLAN.md` § 3, § 6.*

## What is the same as set 1 (copied, not re-designed)

- Rubric v2.2 (sha `d450b79510418cf7`), the oracle scope prompt, Gemini settings, `judge_instructions_v2.md` verbatim, Claude
  Opus 5.5 judge subagents, two blind passes on different shuffles with opaque ids. Judges and Gemini read the text cut at
  4,000 chars, exactly as in set 1. The gate scores FULL text (owner ruling 2026-10-07).
- The population rules (stage-2 belonging rows in sadalsuud's retained `data/filtered/belonging/`; no news.google.com;
  ≥ 300 chars; dedup by id then content_hash, after exclusion), bands on v1's production raw (`hi` ≥ 5.6, `mid` 4.0–5.6, `near` 2.5–4.0).
- **The pass rule, verbatim** (GATE.md § Pass rule v2, BINDING): positives = both judges in; deciding negatives = both out,
  except Gemini-in rows whose judge classes are other than `out_one_moment` ("disputed", reported, never deciding); matched
  recall t*; weighted Δspec, paired bootstrap stratified by band × pick, 2,000 resamples, 95% lower bound > 0; both row
  orders; one shot.

## What changes (size and seeds only)

| | set 1 | set 2 |
|---|---|---|
| rows per band | 400 | **800** (2,400 total) |
| sampled Gemini-outs per band | 50 | **100** |
| draw seed / out-sample seed / judge shuffles / bootstrap | 20261003 / 20261004 / 31, 32 / 20261009 | **20261010 / 20261011 / 41, 42 / 20261012** |
| recall bar | k ≥ 31 of 44 | **k ≥ ceil(31/44 × N_POS)** |

The recall bar is set 1's share (0.705), applied to set 2's positive count. This is Claude's translation of "only the size changes",
not an owner ruling.

## Exclusions (the draw refuses nothing silently: every source is a file)

`belonging_exclusions.excluded_ids()` (including set 1's 1,200), v1's three splits, harvest r1's 4,591 drawn rows, the easy-negative
draw (800), every row of the v1_adj1, c2a and c2b builds, the leak-check draw (5,000) and ovr.news EXP-028's 40 stories (by id
where found in production). After the draw, set 2's 2,400 ids become a `belonging_exclusions` source, so no build can train on them.

## No owner spot-check: a tripwire instead (owner 2026-10-08)

Set 1's and harvest r1's owner checks found 0 owner-outs among 14 "both judges in" rows; rubric, instructions and judge model are
unchanged. **STOP and bring the owner rows if EITHER:**
- judge A/B binary agreement is outside **[0.90, 0.97]** (seen: 0.918 harvest, 0.956 set 1), or
- the `hi` band's both-in rate among Gemini-ins is outside **[0.29, 0.48]** (set 1's Wilson interval, 35/92).

## Known before looking

- **Disputed classes hide part of candidate 2's target.** Candidate 2 adds hard negatives from `out_gift_official` and
  `out_harm_is_story`. A Gemini-in row judged in those classes is DISPUTED and does not decide; only Gemini-OUT sampled rows of
  those classes do. gate2.py therefore also reports the disputed rows **per judge class** (not deciding).
- **Power (estimate):** set 1's CI half-width was ~0.06 on 163 deciding negatives; ~2× rows → ~0.042.
- Only ONE candidate (the owner's pick of c2a / c2b) is scored on this set.

## Predictions (Claude's, before the draw)

Deciding negatives 300–360; positives 70–110; hi-band Gemini-in rate 0.18–0.28 (set 1: 0.23).

## Amendment 1 (2026-10-08, after the draw, BEFORE any oracle or judge call)

The draw excluded training rows by ID only. gate2's own overlap check then found 4 drawn rows that twin a v1_adj1/c2a/c2b
training row by title or content (`positive_news_upworthy_35dd196e7214` mid, `romanian_hotnews_1e3c52d614a9` near,
`british_irish_independent_uk_b7b6d44c13aa` mid, `austrian_krone_a1b472c6c601` mid). Some may be boilerplate false hits; none can be
held-out. They are DROPPED (`heldout2.DROPPED`). Nothing about them beyond title and band was looked at. Rows held: hi 800, mid 797,
near 799; design weights use the rows held per band. The alternative (retraining both variants without the 4 training twins)
was rejected: a retrain for 4 rows, and the drop costs no information.

Draw (measured): window `filtered_20260910_051711 .. filtered_20261008_093835` (157 files); pools hi 1,139 / mid 8,914 /
near 14,057. ⚠️ The hi draw takes 70% of its pool (harvest r1 took that band's earlier rows), so the bootstrap's
infinite-population assumption makes the hi stratum's interval CONSERVATIVE.

## Result

**Judged 2026-10-08, BEFORE any candidate was scored on this set** (judge outputs: 1,078 rows, 0 malformed, every quote verbatim).

- Stage A: Gemini said in on 239 of 2,396 (hi 138, mid 73, near 28); 0 errors; 6.72M in / 0.25M out tokens = **$2.64 at list**
  (billing unchecked). Judged: 239 Gemini-ins + 300 sampled outs = 539 rows × 2 passes (22 Opus subagents, ~2.4M tokens).
  The judge prompt was `judge_instructions_v2.md` verbatim plus one appended line naming the repo root for the relative rubric path.
- **Tripwire: PASSED, no owner check.** A/B binary agreement 521/539 = **0.967** (bound 0.97: inside, at the edge); hi both-in
  among Gemini-ins 47/138 = **0.341** (bound [0.29, 0.48]).
- **Labels:** pos **63**, deciding neg **326**, disputed **129**, excluded (split / cannot_judge) **21**.
  Disputed rows by judge class (a row counts once per distinct class across its two passes): {'out_gift_official': 20, 'out_culture_topic': 19, 'out_one_moment': 13, 'out_harm_is_story': 34, 'out_other': 57, 'out_event_spectated': 6}.
- **N_POS = 63 → K_MIN = ceil(31/44 × 63) = 45**, written into gate2.py.
- `gate2.py controls`: all four controls give their required verdict (v1 vs itself FAIL, refuted rule FAIL, perfect PASS,
  perfect-on-negatives with 44/63 FAIL).
- Predictions: deciding negatives 300–360 → **326, hit**; positives 70–110 → **63, miss (low)**; hi Gemini-in rate 0.18–0.28 →
  **0.17, miss (low)**.
