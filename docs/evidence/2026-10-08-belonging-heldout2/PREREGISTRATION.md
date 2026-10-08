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

## Result

*(filled after the judges; N_POS is then written into gate2.py, before any candidate is scored)*
