# The cross-lens harm detector, free arm — `EXP-037` (2026-09-10)

⛔ **Headline: the free route WORKS, PARTLY — and the decision rule I fixed in advance says
"stamp anyway, and the $3.2–3.6 pool spend becomes a ranked option rather than the only route."**
Pre-registration: `PREREGISTRATION.md`, committed before the first training run.

⛔ **One pre-registered prediction was REFUTED and one was WRONG FOR A REASON WORTH KEEPING.**
Both are on the record below. **Spend: $0.**

## What was asked

`#156` wants `harm_is_subject` stamped on every article so each lens can decide by config
(ADR-022). The labels exist — 1,253 of 6,586 rows. **`H-AP5` says they may be the wrong
positives**: every one scores below `weighted_mean_all` 2.7667 and none reaches 4.0, so they are
**harm the oracle already catches**. The leak `#156` exists to stamp is the opposite shape — the
*student* scoring harm content ≥4.5 — and this corpus cannot contain one, because its labels
**are** the oracle's output. **The test split cannot tell us**, because it shares the corpus and
the labelling function.

## The arbiter, and why it is trustworthy

The 137-row `EXP-031` harm panel: display-eligible production rows, judged blind against a rubric
taken from the reader-facing tab copy, by both oracle families. Two properties checked **before**
training, because #142 is exactly this trap:

- ✅ **0 of 137 panel ids appear in the 6,586-row training corpus.**
- ✅ **9/9 panel bodies archived locally are byte-identical to what the judges read.** The other
  128 came through the same pull; their text is not independently checkable.

## Results — at the PRE-REGISTERED threshold rule (lowest val threshold with specificity ≥0.98)

5 seeds. Band, then mean. ⭐ **`H-DET2`: a single-seed detector number is not a result.**

| | real | null (shuffled labels) |
|---|---|---|
| **PRIMARY — of the 9 both-judge `harmful`** | **0–3 (mean 2.0)** | **0–0 (mean 0.0)** |
| of the 32 Gemini `harmful` | 0–3 (mean 2.0) | 0–3 (mean **1.6**) |
| panel flag rate | 0.73–2.92% (mean 2.04%) | 1.46–5.84% (mean **4.09%**) |
| panel specificity on the 105 unflagged | 0.9905–1.0 | 0.9429–0.981 |
| test specificity | 0.9656–0.9847 (mean 0.9767) | 0.9732–0.9809 |
| test recall (137 positives) | 0.4599–0.5766 (mean 0.5139) | 0.0146–0.0511 |

⭐ **Read the null arm first. It fires at TWICE the real arm's rate and touches the 9 zero times
out of five seeds.** That is what makes mean 2.0 a signal rather than a volume artifact — the
comparison is against 0.0, not against zero-by-assumption.

⚠️ **But on the 32, real (2.0) and null (1.6) are not distinguishable.** Every panel row the real
detector caught that a judge flagged was in the **9**; it caught **none** of the 23 rows only
Gemini called harmful. The detector agrees with judge *consensus*, not with the wider Gemini net.

## The threshold sweep — because my own uninformative clause fired

The pre-registration said: *if the chosen threshold flags <2% or >40% of the panel, the catch
count is a property of the threshold, not the detector — report the sweep, no headline.* **Three
of five seeds landed at or under 2%.** So:

| thr | flagged /137 | rate | of 9 (null) | of 32 (null) | panel precision | test spec | test recall |
|---|---|---|---|---|---|---|---|
| 0.30 | 10.6 | 7.74% | 3–4 (0.6) | 7–9 (4.6) | 0.743 | 0.9227 | 0.7445 |
| **0.50** | **7.6** | **5.55%** | **3–4 (0.0)** | **5–8 (1.0)** | **0.841** | 0.9495 | 0.6773 |
| 0.65 | 5.4 | 3.94% | 2–3 (0.0) | 3–5 (0.0) | 0.776 | 0.9614 | 0.6116 |
| 0.80 | 3.0 | 2.19% | 0–3 (0.0) | 0–4 (0.0) | 0.543 | 0.9759 | 0.5066 |
| 0.90 | 1.6 | 1.17% | 0–2 (0.0) | 0–2 (0.0) | 0.542 | 0.9847 | 0.3971 |

⭐ **The seed instability at the operating point was largely a THRESHOLD artifact.** At the
val-picked threshold the band on the 9 includes **0**; at 0.50 it is **3–4 with no seed at zero**,
and the null is still 0.0. The detector is more stable than its operating point suggested.

⛔ **0.50 is POST-HOC.** It is not the pre-registered rule and no decision may be taken on it
without a fresh pre-registered threshold rule. It is reported because the clause required it.

## What the flag rate means in production — re-weighted, because the panel is stratified

The panel is **60 v7_only / 40 both / 37 v8_only**; production over the same four cycles was
**523 / 131 / 37**, so `v8_only` is **27.0% of the panel and 5.4% of production**. A rate read
straight off the panel carries the panel's design weighting (`feedback-sample-carries-its-design-weighting`).

| threshold | panel (unweighted) | **design-weighted** |
|---|---|---|
| 0.50 | 4.38–6.57% (mean 5.55%) | **4.55–7.54% (mean 6.09%)** |
| 0.65 | 2.92–5.11% (mean 3.94%) | 2.02–5.02% (mean 3.48%) |
| 0.80 | 0.73–3.65% (mean 2.19%) | 0.47–2.50% (mean 1.28%) |

⚠️ **The re-weighting moves it only modestly here, and that is itself the finding**: per-stratum
flag rates are close (v7_only 6.67%, both 4.00%, v8_only 5.41% at 0.50), so harm-subject content
is roughly as common in what v7 uniquely surfaces as in what v8 does. **Do not generalise from
"the weighting barely moved this number" to any other number off this panel** — `EXP-031`'s
on-promise axis reverses sign within stratum.

`#156` predicted the honest answer would be *"blocks a few percent"*. **6.09% design-weighted at
0.50** is that answer.

## Scorecard against the pre-registration

| prediction | outcome |
|---|---|
| test recall **0.45–0.75** | ✅ 0.4599–0.5766 — inside, at the bottom |
| **PRIMARY: 2–5 of the 9** | ✅ mean **2.0** (band 0–3) at the pre-registered rule — inside, at the bottom |
| panel specificity on the 105 **≥0.85** | ✅ 0.9905–1.0, comfortably |
| **6–16 of the 32** | ⛔ **REFUTED — 2.0 (band 0–3)**, and not distinguishable from the null's 1.6. It reaches 6.4 only at the post-hoc 0.50 |
| test specificity **≥0.98 "by construction"** | ⛔ **WRONG, and the reason matters: a specificity constraint enforced on VAL does not transfer to TEST.** 3 of 5 seeds came in below 0.98 (0.9656–0.9847). "By construction" was the tell — I asserted a number instead of measuring it |

## Decision, per the rule fixed in advance

Both readings land in the same bucket: **2.0 of 9** at the pre-registered rule, **3.2 of 9** at
0.50. The rule says **2–4 → "the free route is partial. Stamp anyway — it is free and ADR-022 says
stamp always — and the pool spend becomes a *ranked option*, not the only route."**

⛔ **That is the decision. It is not upgraded because the sweep looks better.**

## What this does NOT establish

- **n=9.** Three or four of nine is a wide interval on any account. This measures direction, not a
  deployable recall.
- **The 9 are DeepSeek k=3 ∩ Gemini k=1.** Safety of that nesting is *bounded, not shown* —
  0 misses in 9, rule-of-three 95% upper bound **33%** (`H-AP3`).
- **The panel is `uplifting v7` / `human_thriving v8` display-eligible rows only.** It says nothing
  about `solutions`, `belonging`, `nature_recovery` or `cultural_discovery`, which `#156` also
  wants stamped — and "Bihar copes with floods" is arguably constitutive under Solutions.
- **One box.** Trained and evaluated entirely on b650-gpu. The **library-stack** noise floor of
  **0.2008** was measured on exactly this architecture (mpnet + sklearn MLP), so these numbers may
  not be compared against a run from another stack.
- **No model artifact was kept and nothing was deployed.** This arm answers "is the free route
  worth pursuing", not "ship this".

## Reproduce

```bash
# b650-gpu, venv-prodparity. Splits rebuilt with prepare_data.py --seed 42 (#155).
python3 filters/common/harm_detector/training/train_v1.py \
    --splits datasets/training/human_thriving_v8_scoped \
    --panel-content datasets/panel/panel_content.jsonl \
    --panel-judges docs/evidence/2026-09-08-thriving-harm-panel \
    --out docs/evidence/2026-09-10-harm-detector/report.json
```

`report.json` carries every per-seed number, the full sweep, and per-row panel probabilities so
the rate can be re-weighted without retraining.
