# human_thriving v8 — the four Phase B rulings

**Date:** 2026-08-30 · **Ruled by:** owner · **Issue:** llm-distillery#127 (corpus provenance),
#135 (prompt instability) · **Supersedes nothing; unblocks Phase B labelling.**

The 2026-08-28 Gate 0 record (`2026-08-28-v8-gate0-corpus-spec.md`) settled the three reserved
corpus numbers. This record settles the four decisions that were left open when the corpus was
drawn on 2026-08-29 and the evidence for each landed on 2026-08-29/30.

⛔ **No oracle spend was incurred producing this record.** Every number below is read off work
already committed; the two production queries used to select the replacement row are read-only
scans of `data/filtered/` on sadalsuud.

---

## 1. The reordered oracle prompt — **ADOPTED**

**Ruled:** Phase B labels with the reordered v8 prompt (`prompt-candidate-tail.md`, the article
moved to just before §7), not the as-is one.

**On the label argument, not the cost one.** That distinction is the whole of it: H-V8-3
(2026-08-29) established that the reorder is **not label-neutral** — production-mix
mean(reordered − as-is) **−0.239** [−0.409, −0.080], permutation **p=0.0049**, which does *not*
clear 0.05/16 and was not pre-registered as a family. A cheaper prompt that moves labels cannot
be adopted *because* it is cheaper, and it was correctly refused on that basis for a day.

What changed is H-V8-9 (`docs/evidence/2026-08-29-v8-h-v8-9-adjudication/`): of the 12 op-point
crossings the reorder produces, only **4 are stable**, and on those the reorder is right **3 of
4**. Neither §5b hazard is suppressed, and on the transitional-justice row the reordered prompt
is the **best of the three** (+1.417 over v7, `in_scope` on 3/3 runs). Its one stable add is a
judged false positive, arguable on the record.

⇒ The reorder is a **stricter oracle that is more often right**, and its cost advantage is then a
by-product rather than the reason. Measured (H-V8-8): **≈$10.32 vs ≈$54.08** for a k=3 pass over
6,590 rows — **5.2×**, on never-before-scored articles.

⚠️ **Carry this caveat into Phase B:** the ≈$6.9 figure this project quoted for a k=3 corpus pass
was built on Phase A's "repeat discount", which was an artefact of re-scoring the **same 200
articles**. A corpus pass never repeats an article. Both affected documents are already corrected.

⚠️ **k=3 with aggregation is not optional** (#135): the v8 prompt's binary scope gate makes a k=1
label a coin toss on ~5.3% of production-mix rows and 6.7–9.3% at the boundary — a **step
function**, so `1/√k` does not describe it. k=3 is the stopping point: residual **3.750% →
2.452% → 1.945%** for k=1/3/5.

---

## 2. Acceptance criterion 2 — **the Rwanda–EU row is DROPPED and REPLACED**

**Ruled:** remove `west_african_benin_web_tv_e54737d450bf` from
`datasets/adverse/uplifting_no_regression.jsonl`; add two replacement rows for the ADR-015
lens-overlap guard it carried.

### Why not a delta, which was the obvious option

The Unifesp row's assertion was converted to a delta on 2026-08-23 (*"v8 must not score this
LOWER than v7, same judge"*), and the same conversion was the natural remedy here. **It does not
work.** Measured, same judge, k=3:

| prompt | Rwanda–EU raw |
|---|---|
| v7 | **1.600** |
| v8 as-is | **0.817** |
| v8 reordered | **0.817** |

- As an **absolute bar** (`raw > 4.5`) it fails under **every prompt tested, v7 included**.
- As a **delta** it fails too: v8 − v7 = **−0.783**, which is *lower*, and which exceeds the
  recorded oracle decoder run-to-run floor (**0.436** mean / **0.687** max,
  `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md` and `…-op-point-band-followup.md`).
  It is not noise. Both v8 arms landing on **exactly** 0.817 is the scope gate firing
  deterministically, not jitter.

The delta only rescued Unifesp because that row sat *above* its baseline. Rwanda–EU sits below
the line under its own baseline, so no assertion the set can express is satisfiable.

### Why the row was never able to detect a regression

Its own `assertion_basis` said so: *"Observed raw NOT recorded — it was REJECTED as adverse, so
no observed block was written. Score it under v7 to establish the baseline before asserting."*
That baseline is now established — **1.600**, 2.9 points below the op-point it was asserted to
clear. **A row with no baseline above the line cannot regress from one.**

### The root cause is a ruling collision, and the money-committed rule was NOT touched

- **§5b (2026-08-23)** keeps the row as *"a genuine solutions story that may legitimately also be
  uplifting"* — ADR-015 overlap working as designed.
- **The money-committed ruling (2026-08-23, same day)**: *"funding secured, mobilised, pledged or
  allocated improves nobody's circumstances yet"* — and the headline is literally *"46 millions
  de dollars **mobilisés** auprès de l'UE"*.

Under the second, **0.817 is the v8 prompt working exactly as instructed.** ⛔ The money-committed
rule is **not softened**: three of the four stable step-1 op-point crossings depend on it.

The retired row is preserved with its full reason in
`datasets/adverse/uplifting_no_regression_retired.jsonl` — not left to `git log`, because the
question *"why isn't there a lens-overlap row from before?"* will be asked again.

### The two replacements

Selected from a read-only scan of NexusMind's `data/filtered/` on sadalsuud over the window
**`filtered_20260816_124523` .. `filtered_20260830_090728` (83 cycle files)**. ⚠️ The archive
**rolls** — re-enumerate before re-deriving any of this.

| | row | lang | native ch | uplifting v7 raw | also above its own op-point |
|---|---|---|---|---|---|
| **A** | Fast Company, *"London's Ultra Low Emission Zone cleaned up the city's air. Then children's lungs got bigger"* | en | 5,780 | **6.683** (+2.183) | solutions 5.032 (op 2.25), cultural_discovery 4.391 (op 4.0) |
| **B** | Welingelichte Kringen, Greek lignite closures → up to 42% fewer cardiac admissions | nl | 2,601 | **6.474** (+1.974) | solutions 5.280, nature_recovery 4.497 (op 3.75), cultural_discovery 4.907 |

Both were taken because neither is then load-bearing alone, and they guard the same shape through
two different mechanisms in two languages.

Every selection criterion, and why each one exists:

1. **`stage_used == "stage2"` on every lens read.** A `stage1_low` row's `raw_weighted_average`
   is an **e5 probe estimate**, not a Gemma score. The scan conditions on this before reading
   any score.
2. **Baseline recorded BEFORE the assertion is written** — the exact defect that killed
   Rwanda–EU.
3. **Margin far outside every applicable noise term** — +2.183 and +1.974 against the #95 batch
   band (0.16) and the oracle decoder floor (0.436/0.687).
4. **Native text clears the 300-char oracle floor without the enricher** (5,780 and 2,601 chars,
   `pre_enriched` not set). This ruled out an otherwise excellent candidate — Die Presse's
   *"18.736 Haushalten bleibt die Delogierung erspart"* (uplifting 6.352, solutions 5.805), which
   is the sharpest available test of the money-committed boundary (money **spent** with 42,291
   counted beneficiaries) but whose **producer text is 149 chars**; its 2,033 chars are
   enrichment, so the row is not reproducible from producer bytes.
5. **Inside the #107 narrowed predicate**, not merely inside uplifting v7's scoring behaviour.
   The Thriving lens is *a process going well **for people***, which excludes **harm-answered-only**
   and **institution-beneficiary**. Both rows have people as the measured beneficiary (3,400+
   children's lung growth over five years, Lancet Public Health; ~200,000 residents' cardiac
   admissions) and both tell the outcome rather than the wrong. ⛔ This criterion is what
   eliminated every pure-ecology candidate — the crane census, the monkey bridges, the oyster-shell
   restoration all score high on uplifting v7 and are **not** obviously inside the predicate v8
   is being trained to.
6. **Disjoint from training, drawn from the same population.** Verified 2026-08-30: absent from
   `corpus_v8_final.jsonl` (6,590) and `recall_cohort_final.jsonl` (600), present in
   `pool_v2.jsonl` (177,593).

### ⛔ And the disjointness was luck, so it is now enforced

Nothing in `scripts/corpus/draw_v8_corpus.py` excluded the acceptance-test rows. The first draw
came out disjoint only because all three rows in the set at the time had **aged out of the
window**, so the pool could not contain them. The two rows added today **are** in the pool, in
design cell `pos_clear|latin|-`, whose inclusion probability is **0.0794** — roughly a 1-in-13
chance per row that a re-draw silently swallows a guard and hands it to the gate as a training
example it has already seen.

The drawer now removes every id in the no-regression set **before stratification**, and
**refuses to run** if the set is missing or empty. Proven on the real 177,593-row pool, not on a
predicate:

```
no-regression set: 4 ids declared, 2 removed from the pool (2 not in this window)
corpus.jsonl: 6590 rows, guard ids present: []
manifest exclusions: … "no_regression_ids_declared": 4, "no_regression_rows_removed": 2
```

Controls, exit status captured directly (**not** through a pipe — `| tail; echo $?` reports
`tail`'s status, a defect this project has shipped twice):

| control | result |
|---|---|
| `--no-regression-set /does/not/exist.jsonl` | `FATAL: no-regression set not found…`, **exit 1** |
| set file present but empty | `FATAL: … holds no rows. Refusing…`, **exit 1** |
| either refusal | **no output directory created** |

The "4 declared / 2 removed" split is printed on purpose: *declared* and *removed* differ
whenever a guard row has aged out, and only the second number proves the filter did anything.

---

## 3. The 3:1 class-A ratio — **it is about the corpus, and that selects the supplement**

**Ruled:** the 3:1 applies to the corpus's class-A rows. ⭐ **Under the ruling's own definitions
that is exactly the 47-row supplement, so the two readings do not differ.**

The Gate 0 spec (§3) defines TP and FP by **shape** — TP = *harm answered*, FP = *harm is the
dominant subject, the positive incidental or absent* — and then says ⛔ **sample the supplement
ABOVE the op-point**. Keeping that op-point clause:

- The corpus holds **47** class-A rows above the op-point: `pos_clear|latin|classA` 18 +
  `pos_marginal|latin|classA` 29.
- The supplement is **47** rows, drawn `harm-title AND stage2 AND v7_score >= 4.5`.
- They are the same rows. **The ordinary strata contributed zero above-op class-A rows of their
  own.**

⛔ **The "unreachable — needs 62 above-op rows, the window holds 59" arithmetic is retired.** It
came from reading `corpus_level_tp_fp = 1.424` as a TP:FP miss. That number is **47/33** —
above-op ÷ below-op — and a below-op class-A row is **neither** TP nor FP under the ruled table:
it is a harm-lexicon row scoring low, which is correct behaviour, not the class-A defect. The
manifest's own `corpus_level_note` said as much and was not read. The field is renamed
`class_a_above_below_op` / `corpus_level_above_below_op_ratio` with the trap stated inline, so it
cannot be quoted as compliance or as a miss.

**Execution:** adjudicate the 47 supplement rows at labelling time for ~75% harm-answered vs ~25%
harm-dominant. The manifest already records `tp_fp_status: adjudication-pending` rather than a
score proxy that reads like compliance — that stays until the adjudication lands.

⚠️ **Supply is nearly exhausted and this is a design ceiling, not a slack figure:** the window
holds **59** above-op class-A rows and the draw takes **47 (80%)**. **Above ~8,400 corpus rows
the design fails, loudly** — which is one more reason the size below is not a free parameter.

---

## 4. Phase B size — **6,590 rows, the corpus as drawn**

**Ruled:** label the 6,590 rows already drawn, manifested (`sha256 5e2cf729…`) and staged at
`b650-gpu:~/v8_corpus/`, alongside the reserved **600-row held-out production-mix cohort**
(`48d740a7…`) at production's positive rate (10.8%, not the corpus's 19.5%).

It matches the v7 seed count, every Gate 0 target is met at that size, and the two SHAPE clauses
that previously had no implementation are implemented and checked. At k=3 with the adopted
prompt the bill is **≈$10.32** — measured, not estimated.

⚠️ A subset is **not** a truncation: the shape targets (positive rate 19.5%, mix 63.5/36.5,
non-Latin ≥9.76%, clause (a) and clause (c)) are properties of the whole draw and would each need
re-checking. And the class-A supply ceiling above makes a *larger* corpus the direction that
breaks first.

---

## What this unblocks, and what it does not

✅ **Unblocked:** Phase B labelling — reordered prompt, k=3 with aggregation, 6,590 rows,
≈$10.32.

⛔ **Still open, deliberately:**
- The **adjudication** of the 47 class-A supplement rows (§3) — a labelling-time task, not a
  draw-time one.
- The **non-Latin class-A hole**, which is **0% by construction**: `crime_violence` matches 0 of
  14,660 non-Latin pool rows, and the no-regression set is Latin-only, so neither can detect it.
  A candidate scan on 2026-08-30 found this is worse than a class-A problem — in the whole 14-day
  window there are only **27** non-Latin uplifting positives with native text ≥1,000 chars, and
  **every** cross-lens overlap among them comes from **one source**, `china_sciencenet_cn`. Filed
  separately; ⛔ **not** to be closed by adding a thin-margin guard row, which is how the
  Rwanda–EU row happened.
- H-V8-3's **multiplicity** question. The reorder is adopted on H-V8-9's adjudication, not on
  p=0.0049. If a pre-registered family is ever needed for publication, it has not been run.
