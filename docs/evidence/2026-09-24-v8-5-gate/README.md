# v8-5 prompt test — the bar is NOT MET, and the oracle swap moved more than the prompt did

**2026-09-24, pre-registered in [`PREREGISTRATION.md`](PREREGISTRATION.md) before any call.
Spend ≈ $0.17** (token-counted at V4.1 off-peak rates: $0.13 for the arms plus the $0.04 smoke
run, `smoke_not_an_arm.jsonl`, which counts toward nothing). Registry: `EXP-042`.

## Verdict: v8-5 FAILS its bar — no relabel follows from it

| bar item | result |
|---|---|
| 1. 13-row suite passes under v8-5 | **INDETERMINATE**, the same row under both prompts: *The silent crisis on our plates* (no-regression, `raw > 4.5`), v8-4 4.575, v8-5 4.550 — V4 scored it 4.879 on 2026-09-03. Not a v8-5 regression; the model moved it (`gate_G4.txt`, `gate_G5.txt`) |
| 2+3. ≥3 of the 4 targets below 4.5 by margin, and above it under v8-4 | **0 of 4 credited** (`flips_result.txt`) |

Per target, k=6, v8-4 → v8-5 (V4.1 both):

| target | v8-4 | v8-5 | reading |
|---|---|---|---|
| Houston AC law | 5.908 ± 0.184 | 3.583 ± **1.931**, 3/6 `in_scope` | moved, but a **coin toss**, not a verdict |
| Mentawai petition | 5.425 ± 0.471 | 3.396 ± **1.608**, 3/6 | same — bimodal |
| Madras HC permission | 5.308 ± 0.146 | 5.221 ± 0.327, 6/6 | **the edit did nothing** |
| Kyrgyz water systems | **1.096** ± 0.327 | 0.817 | **already out under v8-4** — see below |

The eight non-target flips moved as predicted (not at all, within noise), except Bihar floods
2.871 → 3.908, still below the op-point.

## ⭐ The finding that travels: the V4 → V4.1 swap alone crossed the op-point on 3 of 12

Same prompt (`prompt-v8-4.md`, `c4705408c477`), same text, same k=6, same script — only the model
behind the `deepseek-chat` alias differs (EXP-029 ran on V4, 2026-09-08; this is V4.1, #157):

| article | V4 | V4.1 |
|---|---|---|
| Kyrgyz water systems "to be built" | 4.850, in_scope | **1.096**, 0/6 |
| 5-year-old rescued from sludge | 4.917, in_scope | **1.183**, 0/6 |
| Bihar floods, community kitchens | 4.942, in_scope | **2.871**, 3/6 |

The model swap moved **more** rows across the op-point than the prompt edit did. Consequences:
- **The 6,586 v8 labels are V4 labels.** Any relabel is under V4.1 whatever the prompt, and a
  prompt comparison is only valid inside ONE model version — which is why v8-4 was re-run here
  rather than reused.
- **The alias can move again under us** (#157). A multi-day relabel is exposed to that.
- EXP-029's picture of *which* live passers are wrong is a V4 picture.

## What this does NOT show
- Twelve articles, one cycle's panel. The V4/V4.1 table compares two runs taken 16 days apart;
  the script and text are identical, but that is not a controlled swap.
- The documented rubric (EXP-029 arm B) is itself a judge with κ = 0.587 against Gemini; the
  flips are pattern-level evidence, not per-row truth.

Files: `run.sh` (arms), `analyse_flips.py` (bar items 2–3), `runs/` (raw; three runs carry one
failed-parse line each, filled by resume), `runs_gate/` (the same runs with those error lines
removed, which `adverse_suite_gate.py` requires), `flip_input.jsonl` (the 12 flips' text).
