# 2026-08-30 — the four v8 owner decisions, ruled and executed

**Spend $0.** No model trained, no threshold moved, no probe touched, nothing under `filters/`
changed — **deploy is N/A, not skipped.** Two read-only scans of production output on sadalsuud
and one drawer run against the staged pool on b650; no oracle call.

Ruling record: `docs/decisions/2026-08-30-v8-phase-b-rulings.md`.
Evidence: `docs/evidence/2026-08-30-v8-no-regression-replacement/`. Registry: `EXP-006`.

---

## What was ruled

The session opened on the four owner decisions the 08-29 night session ended with. Two came back
ruled directly, two came back as *"what do you recommend?"* — and in **both** of those the option
list I had written was the wrong shape. That is the session's real content.

1. ✅ **Reordered oracle prompt ADOPTED** — on H-V8-9's **label** argument (4 stable op-point
   crossings, right on 3 of 4, neither §5b hazard suppressed), with the measured ≈$10.32 vs
   ≈$54.08 as a by-product. H-V8-3 had correctly refused it as a cost optimisation.
2. ✅ **Rwanda–EU row DROPPED and REPLACED by two.**
3. ✅ **3:1 class-A is about the corpus — which selects the 47-row supplement.**
4. ✅ **Phase B labels 6,590 rows** as drawn.

---

## ⛔⛔ THE KEEPER — nothing stopped a guard row being drawn into its own training corpus

`scripts/corpus/draw_v8_corpus.py` had **no exclusion for the acceptance-test rows**. The first
draw came out disjoint from the no-regression set only because all three rows in the set at the
time had **aged out of the archive window**, so the pool could not contain them.

**That is a negative carrying no information — the instrument could not have said yes.** It is
the same shape as the 08-28 cache measurement that re-sent identical articles and so could not
return a low hit rate, and it went unnoticed for the same reason: the check *passed*.

It matters now because the two rows added today **are** in the pool, in design cell
`pos_clear|latin|-`, inclusion probability **0.0794** — about a 1-in-13 chance per row that a
re-draw silently swallows a guard and hands it back to the gate as a training example it has
already seen. Nothing would have failed; Gate A would simply have started grading the model on
its own homework.

Now removed **before stratification**, with the draw refusing to run on a missing or empty set,
proven against the real 177,592-row pool (`4 declared / 2 removed`, `guard ids present: []`),
both refusals at **exit 1** with no output directory, exit status captured directly rather than
through a pipe. Nine tests, five mutations, all killed, the mutator asserting it applied.

---

## ⛔ Two of mine — both were option lists that framed the owner's choice wrongly

### 1. I offered a remedy that does not work

For criterion 2 I offered *"convert the assertion to a delta, as the Unifesp row's was"* as the
recommended option. **It fails too.** The Unifesp delta reads *"v8 must not score this LOWER than
v7"*; Rwanda–EU is **0.817 against v7's 1.600**, i.e. **−0.783** — past the oracle decoder floor
(0.436 mean / 0.687 max), so not noise. The delta rescued Unifesp only because that row sat
*above* its baseline, and I carried the precedent across without checking the sign.

⭐ **A precedent is a claim about a mechanism, not a template.** Both rows were "an assertion that
does not fit its article", but the fix depended on which side of the baseline the row sat, and
that is exactly the fact the precedent does not carry with it.

### 2. I read a manifest field's NAME instead of its note

Decision 3 was put to the owner as *"supplement or whole corpus, and the corpus reading is
unreachable — 75% of the target needs 62 above-op rows, the window holds 59."* That arithmetic
came from reading `corpus_level_tp_fp = 1.424` as a TP:FP miss. The field is **47/33** —
**above-op ÷ below-op** — and under the ruled table a below-op class-A row is **neither** TP
(harm answered) nor FP (harm dominant, scoring HIGH): it is a harm-lexicon row scoring low, which
is correct behaviour.

⛔ **The manifest's own `corpus_level_note` said so, in the same JSON object, and I had written
it.** The key was named `corpus_level_tp_fp` and the name won.

Once the ruling's own op-point clause is kept, both readings select the same 47 rows — the corpus
holds exactly 47 above-op class-A rows and the ordinary strata contributed **zero** of their own.
There was never a fork. The field is renamed `class_a_above_below_op` /
`corpus_level_above_below_op_ratio` with the trap inline, and a test now asserts the old name
cannot come back.

⭐ **The generalisable bit: a name is an assertion about a quantity, and it is read far more often
than the note beside it.** A field whose name misdescribes it will be quoted wrongly by the
person who wrote the disclaimer.

---

## ⭐ What the replacement search turned up

Selection criteria that did work (`docs/evidence/2026-08-30-v8-no-regression-replacement/`):

- **`stage_used == "stage2"` before any score is read** — a `stage1_low` row's score is an e5
  probe estimate. The skipped counts are not small: 155,221 non-stage-2 `solutions` rows.
- **Baseline recorded BEFORE the assertion** — the exact defect that killed Rwanda–EU.
- **Native producer text ≥ the 300-char floor**, so the row is reproducible without the enricher.
  This eliminated the single best candidate on the money-committed boundary — Die Presse's
  *Wohnschirm* row, money **spent** with 42,291 counted beneficiaries — whose producer text is
  **149 chars** against 2,033 after enrichment.
- **#107's narrowed predicate, not uplifting v7's behaviour.** ⛔ This eliminated every
  pure-ecology candidate (crane census, monkey-corridor bridges, oyster-shell restoration) despite
  uplifting v7 scoring them 6.28–6.77. **Selecting on the old model's behaviour rather than on the
  predicate the new one is trained to is the Unifesp error** — asserting an absolute band from a
  different prompt's score.
- **Disjoint from training, same population** — absent from the 6,590 corpus and the 600-row
  cohort, present in the 177,592-row pool.

Adopted both: Fast Company / London ULEZ (en, native 5,780, uplifting **6.683**) and Welingelichte
Kringen / Greek lignite closures (nl, native 2,601, uplifting **6.474**, above the op-point of
**four** lenses). ⚠️ I initially took these for two renderings of one story; they are two
independent studies of the same shape. Checking that is what made taking both worthwhile.

### #141 filed — the non-Latin hole is wider than class A

The corpus draw already records that the class-A signal is **0% non-Latin by construction**. New:
in the whole 14-day window there are only **27** non-Latin uplifting positives with native text
≥1,000 chars, and **every** cross-lens overlap among them comes from **one source**,
`china_sciencenet_cn`. ⛔ Deliberately **not** closed by adding a thin-margin non-Latin guard row —
that is how Rwanda–EU happened. ⚠️ Whether this is a collection property or a scoring property is
**not established**; the scan cannot separate them.

---

## Housekeeping

- The retired Rwanda–EU row is preserved **with its reason** in
  `datasets/adverse/uplifting_no_regression_retired.jsonl` — not left to `git log`, because
  *"why is there no lens-overlap row from before?"* will be asked again.
- `docs/HUMAN_THRIVING_V8_PLAN.md` §5b and acceptance criterion 2 updated to the ruled state; the
  criterion-2 cell no longer says the gate fails before v8 exists.
- ⚠️ One existing test failed on the manifest rewording and **it was the control working** — it
  guards the disclaimer text. Updated to the strengthened wording *and* given the assertion it
  lacked: the old key name must not return.
- 493 unit tests pass; all four index-budget targets and all doc-claim checks pass.

## ▶ NEXT

Phase B labelling: reordered prompt, k=3 with aggregation, 6,590 rows, ≈$10.32. Then adjudicate
the 47 class-A supplement rows and re-run Gate A against the 4-row no-regression set.
