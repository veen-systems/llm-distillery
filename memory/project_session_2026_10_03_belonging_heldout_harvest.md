---
name: project-session-2026-10-03-belonging-heldout-harvest
description: Session 2026-10-03 — belonging: v2.1/v2.2 blind relabels + owner rulings, pre-registered held-out (1,200 rows), harvest r1 (237 positives), v1 adjudication (804/859 moved out; ruled demote 238 / drop 566 / keep 55), gate pre-registered then re-ruled after review
metadata:
  type: project
---

# Session 2026-10-03: belonging, from a frozen rubric to retrain-ready labels

**Spend:**
- **Gemini, measured** (returned tokens × list price; billing NOT checked): $0.237 (v2.0 noise repeat) + $1.322
  (held-out) + $5.118 (harvest r1) = **$6.68**.
- **Plus ~$2.46 ESTIMATED, not measured:** the k=3 dimension labels, because `batch_scorer` logs no tokens.
- **Claude subagents,** about 12.6M tokens in total, as judges and reviewers.
- **No GPU. Nothing deployed;** belonging v1 stays live.

## The ask and the threads

The ask was "continue" (START HERE item 0.1), then "help me through the decisions" and "next step" several times.
- **Closed:** items 0.1–0.4 and phase 3; the gate pre-registration, re-ruled after review.
- **Open:** see Next.

## What happened (evidence: `docs/evidence/2026-10-0{2,3}-belonging-*/`)

1. **Gemini v2.0 noise floor:** 0/242 flips, so the v2.0 → v2.1 changes are the rubric. Blind v2.1 relabel: A/B
   237/242.
2. **Owner check.** The owner widened ruling 3 into **rubric v2.2** (a recurring peer setting counts). A second
   blind relabel followed. The judges were right on paid tutoring and on anonymous Reddit, and the owner revised
   both to out. **The judges stay the confirm step.**
3. **The held-out set**, pre-registered and committed BEFORE the draw: 1,200 production rows, 3 bands.
   - in-rate hi 8.7% / mid 2.2% / near 0%; Gemini hit 0.38 / 0.20 / 0
   - "Either judge" FAILED its owner bar → **both judges in**; v2.2 frozen
4. **Harvest r1 (hi band):** 4,591 rows → 930 Gemini-ins → **239 positives**; owner 10/10 in. k=3 v1 labels:
   **237 kept**. The hit rate was 0.257, against 0.38 in the held-out: Fisher p = 0.013, unexplained.
5. **v1 adjudication:** the judges move out **804/859** of v1's ≥ 3.5 rows.
   - The owner keeps ~half of those (13/25), but 0/5 of the both-`out_one_moment` rows.
   - **Ruled after the results:** demote 238 / drop 566 / keep 55. It is executable as `adjudicate.py ruling`.
6. **The gate** was pre-registered, then **refuted by review**: a lower-scoring model passes, and v1 itself passes
   at 5.8. The owner re-ruled: **pass rule v2**, at matched recall.

## Mine

- I recommended a gate rule that v1 passes against itself. Review caught it, not me, and not the owner.
- My harvest prediction was ~350 positives; 239 came in. My held-out prediction ("Gemini in ≈ in-rate + 5–8 pts")
  was wrong for hi (+14 points).
- My exclusion file carried 3 `ls` filenames as ids. Harmless, but hand-built.
- I wrote `except_sources`, a bypass that the next copied script would have inherited.
- The owner's ruling lived only in prose, while the code encoded the superseded rule.
- My AskUserQuestion options were too cryptic (two rows bundled into one option). The owner said so; see the
  user-memory feedback.

## Review at close (4 lenses: adversarial code, claims, reachability + guarantees, methodology), all fixed or ruled

- **Claims:** ~85 recomputed, all matching; TODO text was stale.
- **The code fixes:**
  - the ruling is executable, with its counts asserted
  - the rubric freeze is pinned by `tests/unit/test_belonging_rubric_frozen.py` (seeded red)
  - `assert_is_source` / `assert_fresh_draw` replace the bypass (4 mutations raise)
  - the recall lower bound is printed
- **Pre-existing:** 87 `test_commit_msg_hook.py` tests had been red since `4e88184` (the prior close), because the
  fixture did not copy the new forbidden-names script. Fixed. **Suite 1214 passed / 24 skipped.**

## Next: `docs/TODO.md` ▶ START HERE item 0

Decide hard negatives (the 615 harvest outs?) → build `belonging_v1_adj1` from `treatment.jsonl` + 237 positives,
writing training ids → retrain on b650 → calibration → **write the gate runner** to GATE.md § *Pass rule v2*.
