# A scope gate is a step function, and a regression head cannot carry one — split it

**Date:** 2026-09-08
**Status:** Proposed — owner-originated, evidence attached, not implemented
**Issue:** llm-distillery#150 · **Evidence:** `docs/evidence/2026-09-08-thriving-harm-panel/`
**Supersedes nothing. Amends the reading of:** `docs/decisions/2025-11-13-regression-only-student-models.md`

## The problem, measured in production

`human_thriving v8`'s oracle prompt implements the harm rule as a **binary gate**: if
`scope_verdict` is anything other than `in_scope`, **all six dimensions are forced to 0–2**
(`prompt-v8-4.md:26-27`, `:199`, `:560`). That is a step function.

The student is a **regression head**. It cannot represent a discontinuity; it interpolates.

Re-scoring the articles a blind panel called harm-subject with **v8's own oracle**, k=3
(`oracle_recheck_run{1,2,3}.jsonl`):

| article | oracle `scope_verdict` | oracle wa | student raw | gap |
|---|---|---|---|---|
| How three people shaped by 9/11 live with the legacy | `harm_is_subject` (3/3) | **0.90** | **4.85** | **+3.95** |
| Frontex: 33,000 migrants deported from the EU | `harm_is_subject` | **0.90** | **4.66** | **+3.76** |
| Next dodges 'hammer blow' with equal pay court victory | `harm_is_subject` (3/3) | **0.80** | **4.84** | **+4.04** |

The oracle fires the gate. The student lands **just above the 4.50 operating point**.

⭐ **The leak is general, not specific to what v8 uniquely surfaces.** The same gap appears on
two `v7_only` rows (+3.00, +2.88) — there the interpolated values were 3.90 and 3.73, *below*
the op-point, so nothing reached a reader. **It only becomes visible when the smoothed value
happens to clear the bar.** A threshold move does not fix a leak whose size is ~4 points.

## We have been here before — three times, and none of the fixes transfers

⛔ **This is the point of the record. The diagnosis is not new; the situation is.**

| where | what was found | what was done |
|---|---|---|
| **ADR-015**, `thriving v1`, 2026-04-06 | *"bimodal oracle score distribution with a sparse 2-5 'dead zone' the student model couldn't learn"* — MAE 0.94 vs `uplifting v7`'s 0.67, on **this same lens** | **Deleted the clause that created the cliff.** The orthogonality exclusion ("this is NOT Belonging, score 0-2") was removed; lenses became overlapping perspectives |
| **`solutions` v4 → v6** | production distribution bimodal, median 0.0 with a spike at 7–10 | **Changed the corpus.** Probe-split training with false positives zeroed — 702 dropped, 2,401 re-scored, $2.96. Distribution became continuous (median 0.17) |
| **ADR-003**, needle-in-haystack | 94% of articles low-tier ⇒ the model learns "predict 2.0"; `evidence_quality` MAE **4.12** exactly on the 8–10 range that matters | **Enriched the training distribution** with a screening filter *before* oracle scoring |

**Every one of those fixed the TARGET so the student could learn it. None of them is available
here, and the reason is the same in all three cases:**

⭐ **`thriving v1`'s cliff was ACCIDENTAL — a prompt clause nobody needed — so ADR-015 could
delete it. `human_thriving v8`'s cliff is the HARM GATE, and it is the thing the owner
explicitly wants.** Owner, 2026-09-08: *"we optimised for precision. Reason being that very
adverse articles were presented as thriving in the past"* (llm-distillery#91 — `uplifting v7`
ranked a child-trafficking investigation in its top 6 of 3,530).

Smoothing v8's target means giving up the harm protection. Re-splitting the corpus does not
help: the discontinuity is in the label-generating function, not in the sample. Enriching the
dead zone does not help either — there **is** no dead zone to enrich, because the gate emits
`0–2` or a real score and nothing between.

⚠️ **And bimodality alone is not fatal**, which is why this needed the measurement rather than
the pattern: `uplifting v7` is itself bimodal (30–43% zeros per dimension,
`memory/uplifting-v7-training.md:34`) and shipped at MAE 0.67.

## The proposal

**Stop asking the regression head to carry the gate. Give the gate its own head.**

```
article ─→ Stage 1: e5 probe (recall-safe topical screen, ADR-006/011)
              │
              ├─ below → stage1_low, never surfaces
              ▼
           SCOPE GATE  (binary classifier: in_scope vs harm_is_subject /
              │         response_to_harm / no_person_benefits / out_of_scope)
              │
              ├─ gate fires → blocked, stamped, score not published
              ▼
           Stage 2: regression head, trained ONLY on in_scope rows
```

Two properties follow, and both are the point:

1. **The regression head's target becomes continuous.** Trained only on `in_scope` rows, it
   never sees the 0–2 spike, so there is no discontinuity to interpolate across. This is what
   `solutions v6` achieved by corpus surgery — here it falls out of the architecture.
2. **The gate becomes a classifier, which is the right estimator for a binary.** The 13% of
   rows where the oracle's own gate flips between identical runs (#135) is label noise a
   classifier can be trained against and calibrated on; a regression head can only average it
   into a mid-range number.

### Blocker or crude passer? — owner's framing, and the data settles it

Owner, 2026-09-08: *"on the one hand you could call the first step a blocker. On the other hand
you could see it as a crude passer. In the sense that it asks: does this article even belong in
thriving? yes or no? Then if yes, a next step attaches scores to that."*

⭐ **Crude passer, and it is not a naming choice — it changes what the thing costs and where it
lives.**

**1. The oracle already answers exactly that question, and the labels already exist.**
`scope_verdict` is a five-way scope decision, not a junk flag, and it is present on **all 6,586
rows** of `datasets/scored/human_thriving_v8/labels_v84_merged.jsonl` — the exact file v8 was
trained on:

| verdict | rows | share |
|---|---|---|
| `out_of_scope` | 3,543 | 53.8% |
| **`in_scope`** | **1,572** | **23.9%** |
| `harm_is_subject` | 1,253 | 19.0% |
| `response_to_harm` | 188 | 2.9% |
| `no_person_benefits` | 30 | 0.5% |

**Training data for the classifier costs $0 and needs no re-labelling.** Binary balance is
23.9% / 76.1% — an ordinary classification problem, not a needle. (The 5-way version is
trainable except `no_person_benefits`, at 30 rows.)

⛔ **But `training/prepare_data.py` DROPS it** (llm-distillery#155). The field has zero
references there — `:415` builds each record as exactly `{id, title, content, url, labels,
dimension_names}` — so `datasets/training/human_thriving_v8/train.jsonl` carries only the six
dimension scores. **The signal is produced at label time and discarded at split time** — that is
the whole gap between here and a trainable gate, and it is the one blocking prerequisite.

⚠️ **Re-running `prepare_data.py` re-draws the splits.** The current 5,268/658/660 come from one
stratified split at seed 42, and every v8 number on record (`EXP-026`/`027`/`028`) is measured
against that test set. Regenerate to a new directory, or pin the seed and verify byte-identity,
before retraining anything — otherwise the deploy-gate numbers stop being comparable.

**2. The balance is a passer's, not a blocker's.** 76% of the corpus is *not* in scope. A
blocker implies most things pass and a few are removed; here most things do not belong and a
minority are admitted. Calling it a blocker would have sent us looking for junk examples to
label — money we do not need to spend.

**3. Scope is PER-LENS; junk is CROSS-LENS.** `obituary v5`, `violence_promotion v1` and
`commerce v1` are filter-agnostic — an obituary is an obituary whichever tab you are on, which
is why they sit in the shared gate layer. *"Does this belong in Thriving"* is meaningless
outside Thriving. **So the scope gate belongs INSIDE the filter package, versioned with the
prompt that defines it — not in the shared junk-gate layer.** This is the consequence the
blocker framing would have got wrong.

### ⚠️ Two screens in series with OPPOSITE objectives — do not copy the probe recipe

This is the trap worth writing down, because the recipes look interchangeable and are not:

| screen | error that is expensive | objective |
|---|---|---|
| **Stage 1 e5 probe** | a **false reject** — a candidate never reaches the scorer | **recall-first** (`train_probe.py --objective recall`) |
| **Scope gate** | a **false pass** — an off-lens article is scored, may surface, reaches a reader (#91) | **specificity-first** (ADR-023 applies) |

`CLAUDE.md` names the probe as *the* explicit exception to ADR-023. **The scope gate is not an
exception — it is the rule.** Anyone reusing `--objective recall` from the probe recipe will
tune this gate exactly backwards, and the failure is silent: it will pass more, which looks
like more supply.

**This is not a new architecture for this system.** `obituary v5`, `violence_promotion v1` and
`commerce v1` are already binary gates — enforced, stamped, config-gated per ADR-022
(*stamp always, decide once*). v8 is the outlier in expressing a hard gate as a score.

## ⚠️ A precedent that reads like a blocker and is not

`docs/decisions/2025-11-13-regression-only-student-models.md` is titled *"Use Regression-Only
Student Models"* and would be a natural citation against this proposal. **It does not apply.**
Its question is regression vs **generative** — whether the student should emit *reasoning text*
alongside scores — and it is decided on inference latency (200 ms vs 800 ms). It says nothing
about a classification head. An amendment note has been added to that record so it is not
misread later.

## What this does NOT claim

- **Not that v8 was a wrong turn.** On the panel, v8 delivers the tab's promise roughly twice
  as often as v7 does (`fits`+`weak`: 67.6% vs 33.3% under DeepSeek, 51.4% vs 28.3% under
  Gemini), and its `misleading` rate is a third of v7's under both judges (p = 0.0001 / 0.0101).
- **Not that the gate leak explains the panel's harm rate.** Three articles carry the ~4-point
  gap. The other harm-flagged rows are genuine definition disagreements between v8's oracle and
  a reader-facing harm rubric — those are prompt questions (#153, #143), not architecture.
- **Not measured: whether a two-head model scores better.** Nothing has been trained. The
  argument is that the current architecture *cannot* represent its own target, which is a
  statement about the estimator, not a benchmark result.

## Cost of being wrong

Low and reversible. The gate can ship as a **stamp-only** classifier first (ADR-022: stamp
always, decide once), so its blocking rate is measurable against production before any article
is withheld — the same path `obituary` took to v5 enforcement.
