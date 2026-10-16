# Near-duplicate leakage into gate and test sets (#176) — result

**Answer: neither live gate is inflated by near-duplicate leakage at this instrument.** human_thriving v9's gate set
holds 5–6 leaked rows (depending on the instrument); re-running the gate's own code without them leaves v9's
verdict a **WIN, unchanged**. belonging v3's gate set has none at ≥ 0.93. Both test splits that `prepare_data.py`
made carry ~5% of rows with a train row at ≥ 0.93. Pre-registered in `PREREGISTRATION.md` (commit `2c44256`,
before any data). $0; e5-small on b650; data in the lab at `experiments/2026-10-16-near-dup-leakage/`
(`MANIFEST.json`).

## Counts (`report.txt`)

| arm | query vs train | ≥ 0.90 | ≥ 0.93 | ≥ 0.95 | median max cos | predicted (≥ 0.93) |
|---|---|---|---|---|---|---|
| A1 | v9's gate set (v8 test, 660) vs `adj3` train (5,768) | 147/660 | **35/660 = 5.30%** | 11/660 | 0.8815 | 0.5–5% — at the top edge |
| A2 | `adj3` test (723) vs `adj3` train | 153/723 | 36/723 = 4.98% | 12/723 | 0.8811 | 0.5–5% |
| B1 | belonging gate set 3 (2,397) vs `c2b` train (6,331) | 57/2397 | **0/2397 = 0.00%** | 0/2397 | 0.8684 | 0–1% |
| B2 | `c2b` test (780) vs `c2b` train | 216/780 | 36/780 = 4.62% | 14/780 | 0.8850 | 0.5–5% |

Exact id overlap: 0 in every arm. Presence control: 5 exact copies scored 1.0000 in every arm.

## A1's 35 pairs at ≥ 0.93 — which are leaks

Two instruments, because each fails in a different direction:

- **Full-text 8-word shared share** (`classify_pairs.py` → `classify_pairs.txt`, LEAK iff ≥ 0.5, a post-hoc cut):
  5 pairs — sugar-rationing study via Hacker News (0.88) and via ScienceDaily (0.78; both copies of one
  Conversation piece, and a first-600-chars comparison missed the second behind ScienceDaily's header), Syria off
  the terror list (wire, 0.93), colon-cancer immune evasion (press release vs repost, 0.62), and **NYT Connections
  hints, 0.79 — a TEMPLATE, a different day's puzzle, so a false leak.** Every other pair ≤ 0.16.
- **Reading:** the Yonhap AIM-9X story re-run by the Korea Herald is the same article rewritten — share 0.13, so the
  shingle instrument misses it.

The pre-registration classed pairs by reading only; the shingle number and the "template" class were added after a
review (2026-10-16) found the missed ScienceDaily leak. **Deviation stated, not hidden.**

## The pre-registered recompute (`gate_excluded.py` → `gate_excluded.txt`)

`scripts/gate/ground_truth_gate.py` run exactly as `docs/evidence/2026-09-25-v8-adj-retrain-gate/` ran it
(adjudicated labels, `--recompute-model-wa`, op 4.5, gatekeeper cap 3.0, floor 0.16), on arms v8 and adj3 (= v9),
excluding the **union** of both instruments (6 rows — the conservative set).

| arm | all 660 (CONTROL: reproduces `gate_adjudicated.json`) | 6 leaks excluded (654) |
|---|---|---|
| v8 | tp 9 / fp 11 / tn 626, spec 0.9827 [0.9812, 0.9890] | tp 9 / fp **10** / tn 621, spec 0.9842 [0.9826, 0.9905] |
| adj3 (v9) | tp 8 / fp 1 / tn 636, spec 0.9984 | tp 8 / fp 1 / tn 630, spec 0.9984 |

The one cell that moves is v8's: the Hacker News sugar-rationing row was a v8 false positive. The pre-registered
WIN rule (adj3 spec lo > v8 spec hi, adj3 recall hi ≥ v8 recall lo): **0.9984 > 0.9905 and 0.3478 ≥ 0.3478 → WIN,
unchanged.** `gate_impact.py`/`.txt` (v9's cells only; all TN) is kept as the first, narrower check.

## Caveats — what this does NOT show

- **0.93 is not a complete twin detector.** The rewrite control (title replaced, first 300 chars dropped) scored
  **0.8333–0.9757**, so a re-edited copy can sit below 0.93. B1's zero excludes close copies, not rewritten ones;
  its 57 rows at ≥ 0.90 were not read. belonging's gate also had `gate3.py`'s lexical guard (id / url / title /
  content window), which this does not replace.
- **A2/B2's leak share is inferred, not read.** A1 measured 5–6 leaks in 660 rows (0.76–0.91%), i.e. 5–6 of its 35
  pairs at ≥ 0.93; carrying that ratio to A2 (human_thriving) and to B2 (belonging, a different corpus) is a guess.
- v9 = `adj3` was matched by row counts (5,768 / 720) — v9's package records no split dir (#127). belonging v3
  ships `filters/belonging/v3/training_manifest.jsonl`, which holds exactly `c2b`'s train + val + test ids.
- Two filters, one embedding model, one threshold family. Other live filters were not measured.

## What it leaves for the owner (#176 step 3)

Prevention by construction (`prepare_data.py` grouping near-duplicates into one split, or raising) is now a
cost/benefit call. The measured exposure is small: ~5% of test rows have a ≥ 0.93 neighbour, and in the one set read
closely under 1% are real leaks, none of which moves a verdict. The `prepare_data.py` comment that claimed pool
assembly handles near-duplicates has been corrected.
