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
