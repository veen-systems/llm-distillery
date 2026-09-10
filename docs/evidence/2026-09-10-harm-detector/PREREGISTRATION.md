# Pre-registration — cross-lens harm detector, free arm (`EXP-037`, 2026-09-10)

⛔ **Written and committed BEFORE the first training run.** The point of this file is that a
prediction which turns out wrong stays on the record as wrong. `EXP-030`'s band-share prediction
failed and that failure was more useful than its successes.

Issue: llm-distillery**#156** (cross-lens harm detector — stamp `harm_is_subject` on every
article, let each lens decide by config, ADR-022). Lane C in `docs/TODO.md`.

## The question, and why it is genuinely open

`#156` says the labels already exist: `datasets/scored/human_thriving_v8/labels_v84_merged.jsonl`
carries `scope_verdict` on all 6,586 rows, **1,253** of them `harm_is_subject`.

⛔ **`H-AP5` says those labels may be the wrong positives.** Every one of them scores below
`weighted_mean_all` **2.7667**; there are **0** at ≥4.0; and **all 316 rows at or above the 4.50
op-point are `in_scope`**. So the training positives are **harm the oracle already catches**. The
leak `#156` exists to stamp is the opposite shape — *the student scoring harm content ≥4.5* — and
this corpus cannot contain an example of it, because its labels **are** the oracle's output.

**A detector trained on these labels may therefore learn the oracle's own gate and be blind to the
leak. The test split cannot tell us**, because it is drawn from the same corpus and the same
labelling function. That is the whole reason this experiment needs an out-of-corpus arbiter.

## The arbiter: the `EXP-031` harm panel, verified held-out today

`docs/evidence/2026-09-08-thriving-harm-panel/` — 137 display-eligible production rows, judged
blind against a rubric taken from the reader-facing tab copy, by both oracle families.

Two properties checked **before** any training run, because #142 is exactly this trap (*"Gate B-A
judges against rows that are also training inputs"*):

- ✅ **0 of 137 panel ids appear in the 6,586-row training corpus.** Genuinely held out.
- ✅ **9/9 panel bodies that are archived locally are byte-identical to what the judges read**
  (`oracle_recheck_input.jsonl` vs the text pulled from sadalsuud today). The other 128 came
  through the same pull; their text is not independently checkable.

Panel positives: **32** Gemini k=1 `harmful`, **9** DeepSeek k=3 `harmful`, and the 9 are a
**subset** of the 32 (`H-AP3`: 0 reversals). ⚠️ **Safety of that nesting is bounded, not shown** —
0 misses in 9, rule-of-three 95% upper bound on the miss rate **33%**.

## Method

1. Rebuild splits with `training/prepare_data.py --seed 42` into
   **`datasets/training/human_thriving_v8_scoped/`**. ⛔ Never overwrite
   `datasets/training/human_thriving_v8/` — it is what every v8 gate number is measured against.
   Expected, from `#155`: **5,268 / 658 / 660** rows, `harm_is_subject` **1,011 / 105 / 137**.
2. Positive class = `oracle_meta["scope_verdict"] == "harm_is_subject"`. ⚠️ `oracle_meta` is
   verbatim and heterogeneous — `scope_verdict` is the only non-dimension key measured present on
   all 6,586. Condition on shape before reading anything else from it.
3. Architecture, mirroring `violence_promotion/v1` and `obituary v5`: frozen
   `paraphrase-multilingual-mpnet-base-v2` → `StandardScaler` → `MLPClassifier((256,128))`,
   text = `f"{title} {content}"`.
4. ⭐ **FIVE SEEDS. A BAND, NOT A POINT.** `H-DET2`, measured earlier today: `early_stopping=True`
   lets `random_state` pick the validation split, so obituary recall at 0.85 spans
   **0.6599–0.8081** with everything else fixed. **As of 2026-09-10 a single-seed detector number
   is not a result in this repo.** Report min / mean / max for every metric below.
5. Operating threshold picked **on the val split**: the lowest threshold reaching
   **specificity ≥ 0.98** (ADR-023 — specificity first; 0.98 is where the deployed filters sit).

## Predictions, stated before looking

| quantity | predicted | reasoning |
|---|---|---|
| test-split specificity | ≥0.98 | true by construction — this is how the threshold is chosen, and it is **not** evidence |
| test-split recall (137 positives) | **0.45–0.75** | in-corpus, same labelling function; where the other detectors land |
| ⭐ **PRIMARY — both-judge panel rows caught, of 9** | **2–5** | `H-AP5` says the training positives are the oracle's own catches. I expect partial transfer: neither none nor most |
| Gemini-flagged panel rows caught, of 32 | **6–16** | same reasoning, wider net |
| panel specificity on the 105 unflagged rows | **≥0.85** | the panel is display-eligible uplift content; a detector firing widely here is unusable whatever its recall |

⛔ **The primary is deliberately a MIDDLING prediction, and both tails are informative.** ≥6 of 9
would mean `H-AP5`'s "the corpus cannot teach the leak" is weaker than it reads and the
**$3.2–3.6** pool spend may be avoidable. 0–1 of 9 would mean the detector reproduces the oracle's
gate and the pool is the route.

## Decision rule, fixed in advance

| both-judge catch (of 9), at panel specificity ≥0.85 | decision |
|---|---|
| **≥5** | proceed to shadow-stamp in NexusMind (`#156` step 1). No new spend. |
| **2–4** | free route is partial. Stamp anyway — it is free and ADR-022 says stamp always — and the pool spend becomes a *ranked option*, not the only route. |
| **0–1** | `H-AP5`'s core stands. Do not ship a detector on these labels; the production-scored pool is the route. |

## Controls — because a number here can be produced by three things that are not signal

1. **Positive control (could the instrument say yes?).** The detector must separate the *test
   split* positives at all. If test recall is ≈0 the model is dead and the panel number carries
   nothing either way.
2. **NULL ARM (could the instrument say yes by accident?).** Retrain on **shuffled labels**, same
   five seeds, same threshold rule. ⛔ **The primary is read against the null arm's catch count,
   not against zero.** A detector with no signal still catches some of 9 at any firing rate.
3. **Firing-rate control.** Report the detector's overall flag rate across all 137 panel rows. A
   detector that flags 60% of the panel "catches 5 of 9" by volume alone.

## What would make this uninformative

If the chosen threshold flags **<2%** or **>40%** of the panel, the catch count is a property of
the threshold rather than of the detector. In that case report the whole sweep and no headline.

## Spend

**$0.** No oracle calls, no judge calls. Embedding compute only. The panel labels already exist
and were paid for by `EXP-031` ($0.35).
