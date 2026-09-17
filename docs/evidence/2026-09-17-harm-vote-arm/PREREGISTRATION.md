# Pre-registration — the per-run-vote arm of the harm detector (`EXP-039`, 2026-09-17)

⛔ **Written and committed BEFORE the first training run**, the way `c54f595` did for the harm
panel and `f1ea988` did for `EXP-037`. A prediction that turns out wrong stays on the record as
wrong.

Issue: llm-distillery**#156** (cross-lens harm detector). Lane C step 2 in `docs/TODO.md`:
*"the remaining $0 arm — per-run scope disagreement."* Spend: **$0**, no oracle calls, no judge
calls, embedding compute only.

## The question

`EXP-037` trained on the corpus's **final** `scope_verdict` labels and partly worked: **2.0 of 9**
both-judge-flagged panel rows (band 0–3) against a shuffled-label null of **0.0**. `H-AP5` says why
it can only be partial — every final `harm_is_subject` label scores below `weighted_mean_all`
**2.7667**, so those positives are **harm the oracle already catches**, and the leak `#156` exists
to stamp is the opposite shape: harm the oracle's final label **misses**.

⭐ **The corpus holds a free proxy for exactly that shape, and nothing has trained on it.** The
per-run votes: **178** rows where at least one oracle run voted `harm_is_subject` and the final
verdict was something else. Those are rows where the labelling function itself nearly said harm and
then did not. If harm the final label misses is learnable at all from this corpus, it is learnable
from those rows — and if it is not, the free route is exhausted and the **~$3.2–3.6** production
pool spend is the route to new signal.

**Reproduced before writing this** (control, and it is the reason this arm is worth running): the
three populations `EXP-032` published off `labels_v84_merged.jsonl` are present in the rebuilt
`#155` splits and sum exactly — **136 + 18 + 24 = 178** minority-harm-vote rows, **146 + 14 + 18 =
178** harm rows with split votes, **851 + 119 + 109 = 1,079** `scope_flipped`. `scope_verdicts_per_run`
is a list on **6,586/6,586** rows, including the 456 where `runs` is an int, so it is the safe field
to read (the trainer's own warning about `oracle_meta` heterogeneity).

## The three arms — one changed variable, everything else identical

| arm | positive class | train / val / test positives |
|---|---|---|
| **A** `final` | `scope_verdict == harm_is_subject` — `EXP-037`'s rule, **re-run, not cited** | 1,011 / 105 / 137 |
| **B** `vote_union` | A **∪** ≥1 `harm_is_subject` run vote | 1,147 / 123 / 161 |
| **C** `vote_only` | the minority-vote rows **alone**; the 1,011 final-harm rows are **removed from the corpus**, not relabelled negative | 136 / 18 / 24 |

⛔ **Arm A is re-run in the same process, not quoted from `EXP-037`'s `report.json`.** Two reasons,
both mandatory here: the comparison must be **paired** (same embeddings, same seeds, same session),
and b650's GPU was swapped 3090 Ti → RTX 5090 on 2026-09-17, so `EXP-038`'s rule applies —
**stored b650-CUDA artefacts may not be diffed against new ones, re-dump instead**.

Everything else is `filters/common/harm_detector/training/train_v1.py`, **imported, not copied**:
frozen `paraphrase-multilingual-mpnet-base-v2` → `StandardScaler` → `MLPClassifier((256,128))`,
5 seeds, val-picked threshold at specificity ≥0.98, the `EXP-031` panel as the held-out arbiter,
and a shuffled-label null arm per arm. Texts are embedded **once** and the arms index into the same
matrices, so no arm can differ by an embedding.

⚠️ **Only the PANEL numbers are comparable across arms.** Each arm's test split carries its own
labels, so test recall and test specificity describe agreement with **that arm's own labelling
function** and nothing else. The panel is the same 137 rows and the same 9/32 judge labels for all
three.

## Predictions, stated before looking

| quantity | predicted | reasoning |
|---|---|---|
| **A replication**, `panel_caught_both9` band | **0–3**, mean **1.5–2.5** | `EXP-037` measured exactly this on the old GPU. A mean outside the band is a **hardware/stack** finding (`H-HD12`), not a label finding |
| ⭐ **PRIMARY — B − A, paired per seed, on the 9** | **+0 to +1** | the 136 extra rows are still this corpus and still the oracle's own votes; `H-AP5`'s argument weakens for them but does not vanish |
| **C**, `panel_caught_both9` band | **0–2**, band including 0 | 136 positives is thin, and `H-DET2` says thin + seeded ⇒ wide |
| all arms, panel specificity on the 105 unflagged rows | **≥0.85** | `EXP-037`'s validity floor, unchanged |
| B train positives | **1,147** | arithmetic (1,011 + 136), asserted at load, not predicted |

## Decision rule, fixed in advance

Read on the **paired per-seed difference B − A** on the 9, at each arm's own val-picked threshold,
with panel specificity ≥0.85:

| B − A paired mean | decision |
|---|---|
| **≥ +2.0** | the per-run votes carry signal the final labels do not. Fold them into `#156`'s positive class, rebuild the detector as v2, and re-cost the pool spend as possibly avoidable |
| **+1.0 to +1.9** | partial. Record it; **do not** rebuild the shipped `harm_detector/v1` on it; the pool stays a ranked option |
| **≤ +0.9** | ⛔ **the free route is exhausted on this corpus.** The ~$3.2–3.6 production pool is the route to new signal, and that goes to the owner as the decision |

C decides nothing on its own. If C's mean reaches A's with **7× fewer positives**, that is a
finding about label efficiency, recorded and not deployed.

## Controls — a number here can be produced by four things that are not signal

1. **Positive control.** Each arm must separate its own test split at all. Test recall ≈0 ⇒ that
   arm is dead and its panel number carries nothing either way.
2. **NULL ARM, per arm.** Shuffled labels, same seeds, same threshold rule. ⛔ **And its FIRING
   RATE is reported beside its catch count** — `H-HD5`, the `EXP-037` keeper: above 0.65 the null
   flagged 0 of 137 rows on all five seeds, so its zero was *arithmetically forced*. A null that
   cannot fire is not a control.
3. ⭐ **RATE-MATCHED comparison — the control this arm specifically needs.** B has 13.4% more
   positives than A, so it may fire more and catch more *by volume*. For each seed, take arm A's
   panel flag count `k`, take arm B's **top-k** panel rows by probability, and count how many are
   in the 9. If B's advantage disappears under top-k, the advantage was the firing rate.
4. **Loader control.** The new label loader must reproduce `train_v1.load_split`'s `final` vector
   **exactly** — same texts, same y — asserted at load, or the run aborts. The shipped loader is
   the reference object; my loader is the thing being checked.

## What this CANNOT establish

- **A production harm rate.** Nothing here reads the NexusMind pool.
- **Recall of anything.** Every population is selected on having been surfaced or labelled.
- **Student/oracle disagreement.** `H-AP5`'s defensible core is untouched by this arm: the
  corpus's final labels are the oracle's own output. The per-run votes are *oracle* disagreement
  with itself, which is a different quantity and a weaker proxy.
- **Anything about the other five lenses.** The panel is `human_thriving`/`uplifting` rows.
- ⚠️ **n = 9 on the primary.** The nesting behind it is bounded, not shown — 0 misses in 9,
  rule-of-three 95% upper bound **33%** (`H-AP3`).
- ⚠️ The panel is **stratified** 60 v7_only / 40 both / 37 v8_only against production's
  523 / 131 / 37. A flag rate read off it carries the panel's design weighting.

## If it is uninformative

`EXP-037`'s escape hatch, unchanged: if a chosen threshold flags **<2%** or **>40%** of the panel,
the catch count is a property of the threshold, not of the detector. Report the whole sweep and no
headline.
