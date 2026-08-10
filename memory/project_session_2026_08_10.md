---
name: project_session_2026_08_10
description: "#102 steps 2+3 measured, 21 adverse candidates adjudicated, b650's GPU commissioned and cross-box disagreement decomposed — plus a 6-lens review that found 3 blockers in the same day's work"
metadata:
  type: project
---

# 2026-08-10 — measured a lot, and got three things wrong before the review caught them

**NOTHING WAS DEPLOYED.** No config edit, no refit, no filter sync. 8 commits,
`d27cc31..a45cbda`, pushed.

## The one-line version

`uplifting v7` at 4.5 would cut FPR 8.11% → 2.70% for 24 fewer false positives
against 27 more false negatives; **b650 on production's pins is now bit-identical
to production** and can be used as a measuring instrument; and the review battery
found that a guard I shipped did not guard, an artifact I committed could stop the
production scorer, and a causal claim I hardened into a rule was backwards.

## What is now settled

**#102 (uplifting v7 specificity) steps 2 and 3.**
`docs/evidence/2026-08-10-uplifting-v7-threshold-sweep-102.md`, JSON beside it.
Sweep ran through the ADR-021 gate on production's own committed predictions —
no re-scoring. **Control passed**: at 4.0 it reproduces the committed
`ground_truth_gate.json` exactly (tp=159 fn=57 fp=36 tn=408, indeterminate 37).

- Feed impact: **1,193 → 870 surfacing per 6 cycles** (≈199 → ≈145/cycle, −27%);
  **off-lens reaching readers 25.3% → 18.8%**, 46% fewer; on-lens retained 79%.
- The 27 lost TPs are the weakest quarter (oracle median 5.00, **none above
  6.5**) and are enriched in academic/preprint sources — 22.2% vs 7.9% of the
  split, **n=6, Fisher p=0.22, so directional only**.
- **Hard ceiling found: `MAX_NORMALIZATION_RAW_MIN = 4.5`.** 4.5 is reachable
  with **zero margin**; 4.75 and 5.0 are not, without changing the constant in
  both repos. Any op-point move must refit `normalization.json` in the same change.

**The 21 `solutions_story` adverse candidates: 7 accepted, 3 rejected, 11 held.**
`datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md`;
`uplifting.jsonl` 4 → 11 rows. The framing correction outlives the batch:
**`content_type: solutions_story` is the oracle's residual bucket**, not a lens
signal — it is the tag the prompt puts on its own 7.3/10 and 5.8/10 *good*
examples. The ADR-015 overlap defence covers **2 rows, not 21**.

**Cross-box disagreement, decomposed one variable at a time** (the day's most
reusable result):

| change | bit-identical | flips @4.0 | flips @4.5 |
|---|---|---|---|
| **host** (gpu-server CPU → b650 CPU, pins held) | **660/660** | **0** | **0** |
| library stack | 15/660 | 0 | 3 |
| device (CPU → CUDA) | 4/660 | **1** | 3 |

**Pinning production's library versions clears a box completely.** b650 on
`~/llm-distillery/venv-prodparity`, CPU, is a **production-exact measuring
instrument** — that removes the "only free between pipeline cycles" constraint
from every future threshold question. Its GPU was commissioned the same day and
needed **no sudo**: `uv python install 3.11` ships the headers triton wants.

## Three things I got wrong, and how they were caught

None of these was caught by the test suite, which was green (270→273) throughout.

1. **Wrong instrument.** Retracted a correct finding because #95 bands overlapped
   — but #95 quantifies batch-composition variance and parity runs hold batch
   composition fixed. Withdrew the retraction the same afternoon. **Third misuse
   of that band in one day**, the third sitting directly above the apology for
   the second.
2. **Confounded comparison.** Published "matching the library stack made
   agreement WORSE" and hardened it into a rule across five surfaces. The two
   arms differed in stack *and* device. The missing fourth run — ~16 min on a
   free box — reversed it.
3. **A guard that did not guard.** `parity_dump_to_gate_input.py` checked that
   `load_calibration` returned something truthy; a partial `dimensions` block is
   truthy, and the raw logits went through under a printed success line
   (spec 0.914 vs the true 0.919). **Its error message cited #98 — the exact
   shape it missed.** 9th entry in the unreachable-mechanism catalogue.

Plus: `threshold_sweep.json` committed **inside** `filters/uplifting/v7/`, where a
deploy `--dry-run` would leave it untracked and `scorer_untracked_blocking()`
would **stop the production scorer from starting**. Moved to `docs/evidence/`.
**`ground_truth_gate.json` still carries that hazard, in every filter package.**

## Open, for the owner

1. **The op-point call** — is a ~145-article/cycle uplifting feed acceptable for
   46% less junk? Product judgement, not a metrics one.
2. **The adjacent-lens ruling** — three held rows are good articles in another
   lens (coffee frog, Buenos Aires estancia, Antalya nomadic tents). One ruling
   covers the class.
3. **gpu-server disk** — the FluxusSource session reclaimed 5.3 G → 21 G, but
   the box is an **LXC container on a 207 G rootfs**; the ceiling is host-side
   (`pct set 108 -mp0 …`). Reclaim buys headroom, not capacity.

## The new open question nobody has answered

**CPU vs CUDA on the student is worth 1 verdict flip at the deployed 4.0
op-point** (max |Δ| 0.1956, 3 rows above the #95 floor). **Production serves on
GPU, while `ground_truth_gate.json` and the entire #102 sweep were measured on
CPU.** The deployed accuracy numbers carry that term and it has never been
quantified end-to-end.

## Also

- `constraints/production-gpu-server.txt`'s documented install command is
  **unsatisfiable** — found by running it. Header now carries one that works.
- A spam comment on #95 was minimized and the account blocked (org + personal),
  at the owner's request; GitHub's search API already refuses to return it.
- `datasets/adverse/README.md`'s contents table had drifted a **second** time.
  Now carries the one-liner that regenerates its counts.
