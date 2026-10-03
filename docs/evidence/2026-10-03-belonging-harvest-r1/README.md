# Belonging harvest round 1: hi band (2026-10-03)

**Owner rulings (2026-10-03, after the held-out run, `../2026-10-03-belonging-heldout/README.md`):**
- **The positive rule:** BOTH blind judges say in.
- **The rubric:** v2.2 stays frozen; the anniversary-reunion conflict is left as is.
- **Round 1:** the `hi` band only (student raw ≥ 5.6), est. ~$5.50.

**Code:** `extract_hi.py` (sadalsuud) and `harvest.py` (`check`, `gemini`, `build-judges`, `import`), which reuses
the held-out run's Gemini call and judge batching. **Rows:** gitignored `datasets/belonging_harvest_r1/`.
The positives are `positives_r1.jsonl`.

## Population

- **The held-out window:** 159 files, `filtered_20260904_220817` .. `filtered_20261003_084553`, same filters.
- **Excluded:** 9,167 ids, which is `belonging_exclusions.py` including the 1,200 held-out rows, plus v1's
  train/val/test ids.
- **Result: 4,591 rows.** That is the held-out's `hi` pool of 4,991 minus its 400 drawn rows: they reconcile
  exactly.

## Stage A: Gemini 2.5 Flash, frozen v2.2

- **The call:** prompt sha `9a245a9dc5ee64eb`, the held-out settings.
- **Coverage:** 4,590 verdicts. 1 row came back empty twice (`no_reply`, counted not-in).
- **Gemini says in on 930 rows (20.3%).** The held-out `hi` band was 23%.
- **Cost:** 12,999,600 in / 487,171 out tokens = **$5.118 at list price**; billing unchecked.

## Stage B: two blind judge passes on the 930 Gemini-ins

- **Setup:** Claude Opus 5.5 subagents, `judge_instructions_v2.md` verbatim, 19 batches per pass.
- **Cost:** ~4.1M subagent tokens.
- **Agreement:** A/B binary 854/930 = 0.918 (held-out: 282/295 = 0.956).
- **Labels:** **239 in (both) / 76 split / 615 out.**
- **Spread:** the positives come from 124 distinct sources; the largest is Business Insider with 14 (first-person
  family and caregiving essays). Every positive's pass-A quote is verbatim in its content.

## ⚠️ Fewer positives than predicted

| | hit rate (both-in / Gemini-in) | interval |
|---|---|---|
| held-out `hi` | 35/92 = 0.38 | Wilson ≈ [0.29, 0.48] |
| this round | 239/930 = **0.257** | |

Predicted: ~350 positives. Measured: 239.

**The candidates:**
- **(a) Judge batch composition.** Here every batch was 100% Gemini-ins (all borderline). Held-out batches mixed
  them with clear outs. A contrast effect would make judges stricter in dense batches. This is the #95 mechanism
  (score depends on batch composition) applied to judges.
- **(b) Sampling variation,** at the held-out interval's edge.

Neither is tested. Testing (a) means re-judging a held-out subset inside dense batches.

**By raw sub-band:**

| raw | positives |
|---|---|
| 5.6–6.0 | 52/254 |
| 6.0–6.5 | 83/326 |
| ≥ 6.5 | 104/350 |

## Owner spot-check of the positives (2026-10-03)

10 positives drawn at random (seed 20261006; `owner_check_blind.tsv`, `owner_check_key.tsv`). The owner read
Claude's neutral summaries, each with an in and an out reading spelled out. **Result: 10/10 in, 0 out, 0 unsure**
(`owner_check_owner.tsv`).

**What that bounds:** for the out-rate among the 239 positives, 0 of 10 gives a 95% upper bound of ~28% (rule of
three: 3/10 = 30%; Wilson 27.8%). It confirms the positives are not junk; it does not measure a small error rate.

## Dimension labels for the positives (2026-10-03, owner-approved ~$2.50)

**The run:** `ground_truth.batch_scorer --filter filters/belonging/v1 --llm gemini-flash`, three independent runs
over the 239 positives (`dimscore/run{1,2,3}`), with 0 failures. `dimscore.py` combines them:
- **the label:** per-dimension mean of the 3 runs
- **the weighted average:** v1's weights and gatekeeper, read from `filters/belonging/v1/base_scorer.py`
- **a missing run raises** (mutation-tested: one batch file removed → exit 1)

**Result** (`positives_r1_labels.jsonl`, gitignored):
- **237 kept, 2 dropped** under 4.0. The dropped two: DW at 1.40, and a Better India row at 3.42, the gatekeeper cap
  (community_fabric < 3).
- **Weighted average:** median 6.76, range 1.40–8.58. 89 rows are ≥ 7.0 (v1's high tier).
- **Run-to-run spread of the weighted average:** median 0.23, max 1.08.

**Cost:** NOT measured; `batch_scorer` does not record token counts. The estimate from character counts (prompt
19,080 chars + content, chars/4, ~700 output tokens a call as a guess) is **≈ $2.46** at list price. Billing is
unchecked.
