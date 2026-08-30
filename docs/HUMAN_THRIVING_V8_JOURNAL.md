# `human_thriving` v8 — build journal

**What this is.** One row per step of the v8 build, in the order it happened, with the
question the step asked, the verdict in one line, what it cost, and where the evidence lives.

**Why it exists.** Nine v8 evidence directories accumulated before this file did, with no
index and no ordering, so nothing said which finding superseded which. Every expensive failure
this project has had was a **lost decision, not a lost result** — a prefilter nobody could
prove ran, an assertion whose baseline was never established, a corpus whose provenance took
git archaeology plus a three-arm experiment to reconstruct. The filter package
(`memory/filter-doc-standard.md`, 6 files) documents the *finished* filter and is the right
shape for that job; it has no place to put *how the filter came to be that way*. This does.

⛔ **Rules for this file, because a journal decays faster than a plan.**
1. **A row is written when the step happens, not afterwards.** Retro-narration from memory is
   how confident-but-wrong history gets written. Rows for steps that predate this file
   (2026-08-20 → 2026-08-28) **link and quote their own headline**; they do not narrate.
2. **The verdict column is one line and it names the outcome, not the activity.** "Refuted:
   the prefilter never ran on this corpus" — not "investigated the corpus".
3. **Spend is stated for every row, including `$0`.** A `$0` row is a claim that no oracle was
   called and is checkable.
4. **A superseded row is struck through and left in place**, with the row that replaced it
   named. Deleting it loses the only record that the earlier reading was ever believed.
5. **This file is an index, not a summary.** If a number matters, it lives in the evidence
   document with its command; this file points at it.

---

## Phase 0 / Phase A — the prompt, the corpus, and what the oracle actually does

| # | Date | Question | Verdict | Spend | Evidence |
|---|---|---|---|---|---|
| 1 | 08-20 | Does the v7 oracle carry a genre bias? | *"…oracle genre bias"* — see doc | — | [`2026-08-20-uplifting-v7-oracle-genre-bias.md`](evidence/2026-08-20-uplifting-v7-oracle-genre-bias.md) |
| 2 | 08-20 | Which valence framing best separates class A? | class-A valence bake-off | — | [`2026-08-20-uplifting-v7-class-a-valence-bakeoff.md`](evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md) |
| 3 | 08-22 | Was the v7 training corpus keyword-prefiltered? | **REFUTED, premise and all** — *"The v7 corpus was never prefiltered — and it is missing the class-A shape"* | $0 | [`2026-08-22-uplifting-v7-corpus-provenance.md`](evidence/2026-08-22-uplifting-v7-corpus-provenance.md), runs in [`2026-08-22-hcv1-runs/`](evidence/2026-08-22-hcv1-runs) |
| 4 | 08-23 | Does the v8 prompt beat v7 on the two defect classes? | *"the prompt works on class B, not yet on class A"* | **$0.4711** | [`2026-08-23-gate-a-two-oracle-run.md`](evidence/2026-08-23-gate-a-two-oracle-run.md) |
| 5 | 08-23 | Can a free local judge run the gate? | *"the §5b no-regression set, assembled — and the free local judge fails it"* | $0 | [`2026-08-23-no-regression-set-and-local-judge.md`](evidence/2026-08-23-no-regression-set-and-local-judge.md) |
| 6 | 08-23 | What would a minimum-length floor cost, by script? | measured over **1,332,648** production rows | $0 | [`2026-08-23-length-floor-by-script.md`](evidence/2026-08-23-length-floor-by-script.md) |
| 7 | 08-23 | Why did Step 1 of the prompt fail on Gemini? | *"the blocker was five contradictions, not the wording"* | see doc | [`2026-08-23-step1-rewrite-r2-r3.md`](evidence/2026-08-23-step1-rewrite-r2-r3.md) |
| 8 | 08-28 | What population would a v8 draw actually sample? | **The Gate 0 targets were stated against the wrong population** — every target moved once `news.google.com` (22.1%) came out | $0 | [`2026-08-28-v8-phase0-drawable-population.md`](evidence/2026-08-28-v8-phase0-drawable-population.md), runs in [`2026-08-28-v8-phase0-runs/`](evidence/2026-08-28-v8-phase0-runs) |
| 9 | 08-28 | Is the v8 prompt's cache ceiling reachable, and is the reorder safe? | ceiling reachable (**0.0% → 90.2%**); reorder **inside its own null** at n=30 — superseded by #11 | $0.12 | [`2026-08-28-v8-prompt-order-probe/`](evidence/2026-08-28-v8-prompt-order-probe) |

## Phase A — the reorder decision (2026-08-29)

| # | Date | Question | Verdict | Spend | Evidence |
|---|---|---|---|---|---|
| 10 | 08-29 | Is the reorder label-neutral, at n=200 with a matched null? | ⛔ **NO — it changes the labels.** mean(reordered − as-is) **−0.239** [−0.409, −0.080] production-mix; **not** multiplicity-robust, no family pre-registered | **$0.867** | [`2026-08-29-v8-phase-a-k3/`](evidence/2026-08-29-v8-phase-a-k3) |
| 11 | 08-29 | Are the reorder's stricter labels **better**, or just lower? | **Better, narrowly.** Of 12 op-point crossings only **4 are stable**; on those the reorder is right **3 of 4** (drops a 2060 projection, an ODA funding plan, a mentorship guidebook) and its one stable add is a judged false positive | $0 | [`2026-08-29-v8-h-v8-9-adjudication/`](evidence/2026-08-29-v8-h-v8-9-adjudication) § step 1 |
| 12 | 08-29 | Does the reorder suppress either §5b hazard? | ✅ **No.** Recovery narrative clears the op-point in both arms; on the transitional-justice row the reorder is **best of three prompts** (+1.417 over v7). ⛔ Third row fails under **v7 too** → a defect in acceptance criterion 2 | **$0.0208** | [`2026-08-29-v8-h-v8-9-adjudication/`](evidence/2026-08-29-v8-h-v8-9-adjudication) § step 2 |
| 13 | 08-29 | Is **k=3** enough repetition, and what would k=5 buy? | **k=3 is the stopping point.** Residual **2.39%** (reordered, production-mix); k=5 removes **32 rows of 6,590** for 1.67× the bill. ⚠️ The k=1→k=3 prize is **~83 rows**, a third the size the plan's flip-rate argument implies | $0 | [`2026-08-29-v8-k3-residual/`](evidence/2026-08-29-v8-k3-residual) |
| 14 | 08-29 | Does the prompt-cache discount survive the gap between corpus passes? | ✅ **Prefix cache: YES** — 200 calls at t+0/30/60/90 min, every row hitting exactly 10,368 tokens, zero cold-prefix rows. ⛔ **Repeat discount: NO, and it never existed for a corpus pass** — Phase A's cheap repeats were re-scores of the SAME articles. **k=3 is ≈$10.32 reordered / ≈$54.08 as-is, not $6.92.** Revision 1 was confounded and killed after one pass | **$0.1044** | [`2026-08-29-v8-cache-ttl/`](evidence/2026-08-29-v8-cache-ttl) |

| 15 | 08-29 | Draw the Gate 0 corpus and give it a manifest (#127) | ✅ **6,590 rows + a 600-row held-out cohort, drawn and staged on b650; all six checks pass** — including the two SHAPE clauses that had no implementation. Visible band **3.74× → 1.95×**, low-middle **0.61× → 1.00×** (parity). ⛔ Three lenses found **3 blockers** in the first draw: the class-A arm was sampled BELOW the op-point against a verbatim ⛔, clause (c) never executed, and the FN cohort was silently deferred. ⛔ My 'control' was false — the census table and mine differ by **34 rows** because **CPython 3.12 changed `sum()` to compensated summation**; and my non-Latin detector was not the census's, which **retracts** one of the questions I put to the owner | $0 | [`2026-08-29-v8-corpus-draw/`](evidence/2026-08-29-v8-corpus-draw) |

| 16 | 08-30 | The four open decisions — put to the owner, ruled, and executed | ✅ **All four ruled.** (1) **Reordered prompt ADOPTED**, on H-V8-9's label argument; the 5.2× is a by-product, not the reason. (2) **Rwanda–EU row DROPPED and REPLACED by two** — ⛔ the delta option does **not** work, v8−v7 is **−0.783**, past the 0.436/0.687 decoder floor, so the row fails in *every* form the set can express. (3) **3:1 is about the corpus — and that selects the 47-row supplement**, because the ordinary strata contributed **zero** above-op class-A rows; ⛔ the *"unreachable, 62 of 59"* arithmetic is **retired**, it read `corpus_level_tp_fp = 47/33` (above:below op-point) as a TP:FP miss when a below-op class-A row is **neither** under the ruled table. (4) **6,590 rows** as drawn. ⛔ Found while executing (2): **nothing excluded the acceptance-test rows from the corpus draw** — the first draw was disjoint only because all three rows had aged out; the two new ones sit in a cell with inclusion probability **0.0794**. Now enforced, refuses to run without the set, proven on the real 177,592-row pool: **4 declared / 2 removed, 0 in the drawn 6,590** | $0 | [`2026-08-30-v8-phase-b-rulings.md`](decisions/2026-08-30-v8-phase-b-rulings.md) |

## Open decisions — ✅ ALL FOUR RULED 2026-08-30

Record with the reasoning for each: **`docs/decisions/2026-08-30-v8-phase-b-rulings.md`**.

1. **Reordered prompt — ADOPTED.** On the label argument (H-V8-9: 4 stable op-point crossings,
   right on 3 of 4, neither §5b hazard suppressed), with the measured **≈$10.32 vs ≈$54.08**
   as a by-product. k=3 with aggregation is not optional (#135's scope gate is a step function).
2. **Rwanda–EU row — DROPPED, and two replacements added.** Retired with its reason in
   `datasets/adverse/uplifting_no_regression_retired.jsonl`. Criterion 2 no longer fails before
   v8 exists. The money-committed rule was **not** softened.
3. **3:1 class-A — about the corpus, which selects the supplement.** Adjudicate the 47 rows at
   labelling time. Short-form stays excluded: v8 is trained for long-form only.
4. **Phase B labels 6,590 rows** — the corpus as drawn and staged.

### Still open, deliberately
- **Adjudication of the 47 class-A supplement rows** — a labelling-time task, not a draw-time one.
- **The non-Latin class-A hole (0% by construction).** A scan on 08-30 found it is worse than a
  class-A problem: the window holds **27** non-Latin uplifting positives with native text ≥1,000
  chars, and **every** cross-lens overlap among them is from **one source**. Filed separately.
  ⛔ Not to be closed by adding a thin-margin guard row.
- **H-V8-3's multiplicity question.** The reorder is adopted on adjudication, not on p=0.0049.

## Machine-readable index

Every step above that was an experiment also has a one-line row in
[`experiments/registry.jsonl`](../experiments/registry.jsonl) — stable `EXP-NNN` id, decision,
spend, and pointers. That file answers *"across everything, what did we decide and what did it
cost?"* in one `grep`; this journal answers *"what happened, in order, on v8"*. Neither restates
a number: both point at the evidence directory that holds it.

## What is deliberately NOT here

- **Numbers.** Every figure above is a pointer to a document that carries the figure *with the
  command that reproduces it*. Two hand-maintained copies of a number disagree the moment one
  is updated — the reason `CLAUDE.md` states no counts either.
- **The plan.** `docs/HUMAN_THRIVING_V8_PLAN.md` says what v8 *will* be and is edited as
  rulings land. This file says what was *done* and is append-only.
