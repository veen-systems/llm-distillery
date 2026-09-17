# The per-run-vote arm is a dead end, and one of its three arms could not have said yes (`EXP-039`, 2026-09-17)

⛔ **Headline: adding the corpus's per-run harm votes to the positive class buys nothing.** The
**178** rows where ≥1 oracle run voted `harm_is_subject` and the final verdict did not move the
held-out panel catch by **−0.4 of 9, paired per seed** — the pre-registered decision rule's bottom
bucket (**≤ +0.9**) — and cost **~30% more panel flags for the same catch** at every shared
threshold. ⇒ **The free route is exhausted as specified, so the ~$3.2–3.6 production pool is the
route to new signal**, and that is now an owner decision rather than a ranked option.

⚠️ **"As specified" is load-bearing, not a hedge.** One free variant remains untested because its
own control failed — arm C with a positive class large enough to train (see below). This result
says the votes do not help **as extra positives beside the final labels**; it does not say the 178
rows are empty.

⛔ **Read the second finding too, because it is the methodological one: arm C could not have said
yes.** Training on the 178 rows alone caught **0 of 9** — but its test recall is **0.0417–0.0833**
and it flags **0.00% of the panel at every threshold ≥ 0.40**. The pre-registration's own positive
control (control 1) fails, so that zero is a statement about **136 positives being too few for this
architecture**, not about what those rows contain. `H-HD11` is **NOT ANSWERED**.

Spend: **$0** — no oracle calls, no judge calls, embedding compute only.
Pre-registration: `PREREGISTRATION.md`, committed at `151250e` **before** the first run.
Reproduce: `train_vote_arms.py` (committed `3f1b7af`, provenance stamped into `report.json`).

## What ran

Three positive-class definitions, **one process, one set of embeddings, five seeds each**, a
shuffled-label null arm per arm, and `EXP-031`'s 137-row judged panel (32 Gemini-harmful, 9
both-judge-harmful) as the held-out arbiter. The architecture is **imported** from
`filters/common/harm_detector/training/train_v1.py`, not copied.

| arm | positive class | train / val / test | positives |
|---|---|---|---|
| **A** `final` | `scope_verdict == harm_is_subject` (`EXP-037`'s rule, **re-run**) | 5268 / 658 / 660 | 1011 / 105 / 137 |
| **B** `vote_union` | A ∪ ≥1 `harm_is_subject` run vote | 5268 / 658 / 660 | **1147 / 123 / 161** |
| **C** `vote_only` | minority-vote rows alone, final-harm rows **removed** | 4257 / 553 / 523 | **136 / 18 / 24** |

Every count above is asserted by the script at load, and the four pre-registered controls ran:
the loader reproduced `train_v1.load_split`'s texts and `final` labels **exactly on all three
splits**; a missing `scope_verdicts_per_run` raises rather than becoming a zero; arm C removes
rather than relabels; and the rate-matched top-k control is computed per seed.

## The primary — paired per seed, on the 9

| | seed 0 | 1 | 2 | 3 | 4 | mean |
|---|---|---|---|---|---|---|
| **A** catch of 9 | 2 | 1 | 3 | 3 | 2 | **2.2** |
| **B** catch of 9 | 1 | 1 | 2 | 2 | 3 | **1.8** |
| **B − A** | −1 | 0 | −1 | −1 | +1 | ⭐ **−0.4** |
| **B at A's flag count (top-k)** | 1 | 1 | 2 | 2 | 1 | **1.4** |

⚠️ **−0.4 does NOT mean B is worse.** The bands overlap completely (both **1–3**) and four of five
paired differences are within ±1 — this is the seed noise `H-DET2` describes. **The claim this
supports is the one the decision rule needed: B is not better, and is nowhere near +1.0.**

⭐ **What IS separable is cost per flag.** At every shared threshold B fires more for the same
catch — at 0.50, A catches 3.2 of 9 flagging **5.40%** of the panel while B catches 3.2 flagging
**7.15%**. Under ADR-023 (specificity first) that is strictly worse, and it is the same story the
rate-matched top-k tells: **1.4 against A's 2.2 at identical flag counts**.

## The full sweep, because the escape hatch fired

The pre-registration said: a threshold flagging **<2%** or **>40%** of the panel makes the catch a
property of the threshold, so report the sweep and no headline. It fired on A's seed 4 (1.46%), B's
seeds 0–1 (1.46%) and **all five of C's**.

| threshold | A catch / flag | B catch / flag | C catch / flag | A null | B null |
|---|---|---|---|---|---|
| 0.30 | 3.4 / 7.15% | 3.6 / 10.66% | 0.0 / 0.29% | 0.6 @ 16.4% | 1.4 @ 15.3% |
| 0.40 | 3.2 / 6.42% | 3.4 / 8.47% | 0.0 / **0.00%** | 0.2 @ 5.4% | 0.8 @ 2.9% |
| 0.50 | 3.2 / 5.40% | 3.2 / 7.15% | 0.0 / **0.00%** | 0.0 @ 1.0% | 0.0 @ 0.7% |
| 0.65 | 3.0 / 4.09% | 2.8 / 5.26% | 0.0 / **0.00%** | 0.0 @ 0.0% | 0.0 @ 0.1% |
| 0.80 | 2.0 / 2.48% | 2.0 / 3.50% | 0.0 / **0.00%** | 0.0 @ 0.0% | 0.0 @ 0.0% |
| 0.95 | 0.4 / 0.58% | 1.0 / 1.46% | 0.0 / **0.00%** | 0.0 @ 0.0% | 0.0 @ 0.0% |

Over `EXP-037`'s 0.30–0.70 plateau: **A spans 2–4, mean 3.10; B spans 2–5, mean 3.07.** B's higher
maximum is one seed at one threshold and is not a result.

⛔ **C's column is the `H-HD5` shape exactly** — a zero produced by an instrument that cannot fire.
Report a null arm's **firing rate** beside its catch, and report a real arm's too.

## The replication control — `H-HD12` holds, and HOW it holds is the keeper

Arm A on the **RTX 5090** against `EXP-037` on the 3090 Ti, per seed, same splits (sha256-checked
both sides), same venv, same architecture object:

| seed | `EXP-037` (3090 Ti) | `EXP-039` arm A (5090) |
|---|---|---|
| 0 | t=0.76 · catch 2 · flag 2.19% | **identical** |
| 1 | t=0.795 · catch **0** · flag 0.73% | ⚠️ **t=0.905 · catch 1 · flag 2.19%** |
| 2 | t=0.655 · catch 3 · flag 2.92% | **identical** |
| 3 | t=0.795 · catch 3 · flag 2.92% | **identical** |
| 4 | t=0.985 · catch 2 · flag 1.46% | **identical** |
| band | **0–3, mean 2.0** | **1–3, mean 2.2** |

⭐ **THE KEEPER — a sub-0.01 probability perturbation moved the OPERATING POINT, and that is what
changed the headline, not the model.** Four of five seeds reproduce **exactly**: same threshold,
same catch, same test recall, same flag rate. On seed 1 the val-picked threshold moved
**0.795 → 0.905** and the catch went **0 → 1**, taking the band's minimum with it. Panel
probabilities on seed 0 are **identical on only 8 of 137 rows**, median |Δ| **4.3e-05**, max |Δ|
**0.0101** — far below any decision scale, and yet `pick_threshold` is a **selection** step, so it
converts a 1e-4 wobble into a 0.11 threshold move. **The same shape as `H-HD4`** (the seed
instability is a property of the threshold) arriving from a completely different direction: the
**device**.

⛔ **Test recall is IDENTICAL on all five seeds — so a metric that looks stable across the swap
tells you nothing about whether the flagged SET is stable.** Per seed, both runs:
**0.5182 / 0.4599 / 0.5766 / 0.5547 / 0.4599**. ⚠️ **The range over which it could have differed is not zero, and printing it is
the point**: test recall on 137 positives moves in steps of **1/137 = 0.0073**, and these same
five models span **0.4599–0.5766** across seeds — **0.1167**, sixteen steps. A device effect one
sixteenth the size of the seed spread would have shown here and did not, while on the same run the
panel flag set moved on seed 1 and **1 verdict flip** followed. Only the threshold-mediated quantities moved.

⭐ **This is also the first parity datapoint for THIS architecture across the GPU swap.**
`EXP-038`'s terms (Ampere→Blackwell max |Δ| **0.2357**, 2 flips at 4.0) are the **Gemma-3-1B
student's**; mpnet + sklearn MLP was unmeasured. It now has a number — **max |Δ| 0.0101 on 137
panel probabilities, 8/137 bit-identical** — and ⚠️ **it is incidental, not a parity dump**: one
seed's panel set, not `box_parity.py`, and a different script on each side. Treat it as a floor on
what the swap does here, not as a measured parity term. ⛔ **And it already produced one verdict
change out of five seeds, so "0.0101 is small" is exactly the reasoning `EXP-038` forbids —
read the flip count, not the magnitude.**

⚠️ **The paired design is immune to all of this.** A, B and C share one set of embeddings inside
one process, so the B − A difference cannot carry a device term.

## What this does NOT establish

- **That the 178 minority-vote rows contain nothing.** Arm C's positive control failed; the honest
  verdict is *not measured*. A larger positive class or a different head could still answer it.
- **A production harm rate**, or recall of anything. Every population here is selected on having
  been surfaced or labelled.
- **Student/oracle disagreement.** `H-AP5`'s defensible core stands untouched: these are the
  oracle disagreeing with **itself**, a weaker proxy, and this arm is why that distinction mattered.
- **Anything about the other five lenses.** The panel is `human_thriving`/`uplifting` rows,
  stratified 60/40/37 against production's 523/131/37.
- ⚠️ **n = 9 on the primary**, and the nesting behind it is bounded not shown (0 misses in 9,
  rule-of-three 95% upper bound **33%**, `H-AP3`).

## Environment

b650-gpu (`jwasys-B650-EAGLE-AX`), `venv-prodparity` — the venv `EXP-037` used (sklearn **1.8.0**,
sentence-transformers **5.2.2**, torch 2.11.0+cu130), device **cuda** on the RTX 5090. Box HEAD
`7dd6ba6`; the script ran as an untracked copy and its sha256 is stamped in `report.json`
alongside `train_v1.py`'s, because the checkout was ahead of the box.

⭐ **The three split files are byte-identical on the workstation and on b650** (sha256 checked both
sides before the run), so arm A's inputs are `EXP-037`'s inputs.

## Files

`PREREGISTRATION.md` · `train_vote_arms.py` · `report.json` (per-seed, per-threshold, per-arm,
including every panel probability) · this README. Registry: `EXP-039`.
Ledger: `H-HD10` (refuted), `H-HD11` (not answered), `H-HD12` (holds). Issue: llm-distillery#156.
