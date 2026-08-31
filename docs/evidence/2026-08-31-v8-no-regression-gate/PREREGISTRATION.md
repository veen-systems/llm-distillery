# Pre-registration — the no-regression gate re-run over the CURRENT 4-row set

**Written 2026-08-31, before any call.** Closes the last item of the 2026-08-30 ▶ NEXT list
("re-run Gate A against the 4-row no-regression set") and is a **precondition for the Phase B
spend**: the adopted prompt is about to label 6,590 rows, and two of the four rows it must not
regress on have **never been scored under it**.

## Why this run exists

`docs/evidence/2026-08-29-v8-h-v8-9-adjudication/no_regression_analyse.py` exits **2** against
today's set:

```
no-regression set: 4 rows   scored by this run: 2
  RETIRED since the run: west_african_benin_web_tv_e54737d450bf
  NOT SCORED BY THIS RUN: industry_intelligence_fast_company_5510f1117e34,
                          dutch_news_welingelichtekringen_760a0a956413
```

The two replacements were selected on 2026-08-30 from **`uplifting v7` student scores** (raw
6.683 and 6.474). ⚠️ **A student score is not an oracle score** — the Rappler row's stored
`observed` is 6.4864 from the deployed model and it scored **4.900** under the v8 reordered
prompt, 0.4 above the op-point. Nothing about the replacements' selection establishes that they
clear 4.5 *under the oracle prompt that Phase B will use*, and that is what criterion 2 asserts.

## Design — fixed here, before the calls

| | |
|---|---|
| population | the **live** `datasets/adverse/uplifting_no_regression.jsonl`, all 4 rows, full text (13,107 / 4,761 / 5,780 / 2,601 chars) |
| arms | **A** `filters/human_thriving/v8/prompt-candidate-tail.md` (reordered — the adopted one) · **B** `filters/human_thriving/v8/prompt-candidate.md` (as-is) · **V** `filters/uplifting/v7/prompt-compressed.md` (baseline) |
| judge | `deepseek-chat`, **one judge across all three arms** — the Unifesp assertion names the judge, and the judge spread on that row (2.2) is larger than the effect being tested (1.4) |
| k | **3 per arm**, interleaved A1 B1 V1 A2 B2 V2 A3 B3 V3 |
| config | `filters/uplifting/v7/config.yaml` (dimensions, analysis field) |
| assertions | **not restated here** — read per row off the live set by the 08-29 analyser, which imports weights, op-point and the gatekeeper from `filters/uplifting/v7/base_scorer.py` |
| verdict instrument | the **committed** `no_regression_analyse.py`, pointed at this run's directory |

⚠️ **All 4 rows are re-scored today.** The two carried over are *not* reused from the 08-29
files: a k=3 mean stitched from two dates across a decoder with a measured 0.436/0.687 run-to-run
floor is not a k=3 mean. The 08-29 numbers below are therefore also a **replication check** on
two rows, which is the only free control this design has.

## Predicted ranges — stated before looking

| row | arm A prediction | why |
|---|---|---|
| Rappler (recovery narratives) | **4.5–5.5**, PASS | 4.900 on 08-29; a replication, so the range is the decoder floor around it. ⚠️ Its margin (0.400) is **below** the 0.436 mean decoder floor — a PASS here is not a comfortable one |
| Unifesp (transitional justice) | delta **+0.8 to +2.0**, PASS | +1.417 on 08-29 |
| Fast Company (lens overlap, en, 5,780 ch) | **4.5–6.5**, PASS | inside the #107 predicate on the ruling's own reasoning; measured beneficiary is people |
| Welingelichte Kringen (lens overlap, nl, 2,601 ch) | **4.0–6.0**, PASS but the **most likely to fail** | shortest, non-English, and #135's scope gate is a step function — it either fires or it does not |

**A miss is reported as a miss.** If a replacement row fails under arm A, it is an owner call
(the Rwanda–EU precedent: the row left the set *with its reason*), **not** a silent drop and
**not** a softened assertion. ⛔ Phase B does not start on a failing criterion 2.

## Cost

36 calls. The 27-call 08-29 run of the same shape cost **$0.0208**; ~$0.03 expected, off-peak
(18:5x UTC Monday — the peak windows are 01:00–04:00 and 06:00–10:00 UTC Mon–Fri).
