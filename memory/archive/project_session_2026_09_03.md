# 2026-09-03 — the prompt settled at v8.4, and two instruments were wrong before the work was right

**Spend $2.30** (DeepSeek 7.40 → ~5.1), **~3,500 calls, 0 errors**. Balance probed before the
first call and reconciled after. **No model, no probe, no threshold, nothing deployed — deploy is
N/A, not skipped.** Seven commits, `2f601d4..5c3af59`, not pushed. 545 unit tests (from 523),
9 killed mutations across three modules.

## Where v8 now stands in the RUNBOOK's nine phases

1 Planning ✅ · 2 Architecture ✅ (`prompt-v8-4.md`) · 3 Validation ✅ · 4 Prefilter ✅ N/A by
ruling · 5 Training data ✅ (6,586 labels, 456 corrected) · **6 Training ⛔ NEXT, never started**
· 6b Probe ⛔ · 7 Calibration ⛔ · 8 Testing ⛔ (instrument now exists) · 9 Deployment ⛔.

## ⛔⛔ THE KEEPER — a blocking gate was failing on a coin flip, because it was prose

Criterion 1 was reported FAILING from a **k=3 mean of 4.400** against a 3.85 bar. The row's own
sd is **2.560**, so the margin (0.550) never cleared its band (2.858) — which Gate B-A's own rule
requires. At **k=6 it is 3.608** and at **k=12 2.342**, both PASSES. The rule had never been
computed because the gate existed only in the plan: the only `.py` files reading
`max_acceptable_wa` were two evidence-directory analysers.

`scripts/gate/adverse_suite_gate.py` now returns **PASS / FAIL / INDETERMINATE / SKIP** on four
distinct exit codes, with the band from each row's **own** spread. On that exact k=3 run it
returns **INDETERMINATE, need k≈82**. ⭐ **On a bimodal row a k=3 mean is a sample of a coin
flip.** ⛔ Plumbing exits **3, never 1** — otherwise a gate that never ran looks like one that
failed; found only because the second exit-code check had no `| tail` (**[x5]**).

## ⛔⛔ SECOND KEEPER — prompt clauses are not additive

Four clauses, each individually safe at k=6 on the #91 origin row (0.900–0.917, 0/6 `in_scope`).
Their union scored it **5.921 with 12/12 `in_scope`** where v8 pins it at **0.900 sd 0.000**.
Leave-one-out isolated a **B×D interaction**: removing either fixes it, neither causes it alone,
and the damage grew monotonically with how many clauses sat alongside. D held the only sentence
that **licenses** a positive; deleting it helped (5.921 → 3.375) and was **not sufficient**. D
dropped; **the convict-relief ruling stands unexecuted**.

Two hypotheses of mine were **refuted by measurement**: the contrast example (2/6 → 1/6,
indistinguishable at n=6) and length/location (a **placebo** of +996 chars of §1 restatement left
the row at 0.883 ± 0.037). ⭐ What survives: **a rule stated as a TEST inside a reasoning step
becomes a question the model asks of every article; the same rule as a CATEGORY in an exclusion
list does not.** A3 (§5, 360 chars) is inert where A (§1, 1,107 chars) leaks.

## ✅ What was delivered

- **`prompt-v8-4.md`** (`c4705408c477`) = B + C + A3. Gate B-A **9/9** at k=12; worst class-A sd
  **2.250 → 0.205**; `in_scope` runs on class A **3 of 108 → 0**; no-regression **4/4**.
  ⭐ **The gain is variance, not verdict** — both prompts pass 9/9.
- **The 47-row class-A supplement adjudicated**: v8 demotes **32 of 47**; the 15 survivors are
  **11 events**, one of them 9 above-op rows corpus-wide.
- **All 456 above-op rows re-scored** at k=6: **140 demoted**, and **115 were rows no generator
  flagged** — sampling the 50 staged rows would have found 25. Zero transitional-justice rows
  demoted, which is the §4 check that matters.
- **`labels_v84_merged.jsonl`** — 6,586 rows, 456 replaced, per-row provenance.
  `labels_k3.jsonl` untouched.
- **Phase B2 sized**: 12 rows of headroom, not a corpus.
- **Five owner rulings recorded** in two decision files.

## ⛔ Mine — six, and the pattern is one thing

1. **`| tail` swallowed an exit code while I was testing exit codes [x5]**, masking a real
   defect (plumbing exiting 1).
2. **A truncated id (`id[:40]`) broke a join silently** and fell through to `class-A: False`; had
   that row been detected its cell probability is **0.763**, not the 0.081 I nearly published.
3. **I validated the union of four clauses by its parts**, having just run the ablation that
   should have told me not to.
4. **I named the contrast example as the cause from reading**, before the placebo refuted it.
5. **I read 4/4-same-sign drift on the controls as systematic**; paired at k=6 it is **−0.077**.
6. **I argued for a $21 full re-label once money stopped being a constraint** and the owner
   pushed back; the argument did not survive — the noise it buys sits **below** the op-point
   (2.1% of the ±1.0 band is flipped vs 15.35% corpus-wide) and a fresh corpus would invalidate
   the day's other measurements. **Scope creep dressed as thoroughness.**

⭐ **Five of the six are the same shape: I believed an instrument before establishing what it
could not say.** A pipeline that always succeeds, a truncated key, an ablation that answers a
different question, a cross-day baseline, a cost argument with no measured benefit.

## ⛔⛔ AND A FAILING CHECK THAT WAS THE CONTROL WORKING

To keep guard rows out of training I widened `draw_v8_corpus.py`'s exclusion to cover
`datasets/adverse/uplifting.jsonl`. **20 of its 33 tests went red**, two named
`test_draw_REFUSES_the_ADVERSE_set_pointed_at_this_flag`. **They were right**: 7 of the 18 rows
carry `training_use: HARD NEGATIVE … §4b` and are **intended training inputs**. Reverted.

But the concern sharpened: a hard negative is **added** with an editorial `negative`; a row
**drawn** is labelled **by the oracle**, and these rows are adverse *because* a scorer read them
as positive — so a drawn adverse row can enter training as a **positive**. Measured: **3 of the
18 were drawable** at p = 0.0810 / 0.0794 / 0.0794, all designated hard negatives, one class A.
None drawn; **P(all escaped) = 0.7787**, so the draw ran a **22.1%** chance of the collision, and
this is the **second** time this shape has appeared. **Fix: report, don't exclude** (ADR-022).
⚠️ Fell out of it: **the class-A instrument does not detect a declared class-A row.**

## ▶ NEXT

**Phase 6 — train.** `prepare_data.py` on `labels_v84_merged.jsonl`, pointed at
`filters/human_thriving/v8` (wrong filter ⇒ 0 examples, prints COMPLETE, exits 0). Probe
objective against the new **4.80%** base rate, not 6.92% and not production's 7.74%.

Three owner items, none blocking: the **phase-3 mRNA row** (5.13 → 0.52, probably wrong),
**#142** (the train/test overlap on the adverse suite — six benchmark candidates wait on it), and
**#143** (the convict-relief ruling, ruled but unexecuted).

**Issues touched:** commented **#135** (the step function reached a blocking verdict, not just
labels), **#91** (origin-row status under v8.4, and how nearly it regressed), **#141** (the
oracle's `dominant_subject` is a language-independent matching surface). Filed **#142**, **#143**.
