# Session 2026-09-08 (second) — the cutover is a 7× cut, and a step function distilled into a regression head

**Spend: $0.35** (harm panel two arms $0.34, oracle re-check k=3 ~$0.01). Registry **EXP-030**
and **EXP-031**. Evidence `docs/evidence/2026-09-08-v7-v8-same-articles/` and
`docs/evidence/2026-09-08-thriving-harm-panel/`. New issues **#154**, **#155**, **#156**.
Decision records `2026-09-08-scope-gate-two-head.md` (new) and an amendment to
`2025-11-13-regression-only-student-models.md`. Pushed through **`9386017`**.

⛔ **Two owner rulings landed mid-session and reframe everything below: production FREEZES
as-is, and a redo is `human_thriving/v9` — a VERSION, not a name.** Sections 1–2 were written
before the freeze and are kept as-is; the "Second half" section carries the rulings.

## What was picked up

`docs/TODO.md` flagged two things. Both were attempted; one delivered, one turned out to be
blocked by our own code.

## 1. The free comparison (`EXP-030`) — the measurement #151 step 5 was missing

Both lenses are enabled and score every article of every cycle, so this is arithmetic over
output NexusMind had already written. Four consecutive cycles, **15,372 articles**, both lenses.

⛔ **The cutover is not a swap, it is a 7× cut.** v7 surfaces **1,184**, v8 **168**; v8 is nearly
a **subset** (152/168 = 90.5%), so the Thriving tab loses **1,032** and gains **16**.
Jaccard **0.127**; v8 produced **no `high` tier at all** (max raw 6.222 vs v7's 7.560).

⛔ **And lowering v8's op-point does not fix it — tested against a null that could have said so.**
On the clean both-stage2 frame, volume-matching (op-point 2.820) recovers **57.5%** of v7's
passers where a Spearman-matched *"v8 = noisy rescaled v7"* null gives **76.8%**; within-union
Spearman **0.3436** against the null's **0.5630**.

⭐ **Where the dropped rows go, also free:** 44.7% of the 1,032 are already surfaced by another
lens (baseline **7.65%**), so ~55.3% are surfaced by **no** other lens — **242 · 128 · 96 · 105**
per cycle, 110 on the three normal ones. ⛔ That is *surfacing*, not a claim about readers.

⚠️ **None of it says which lens is RIGHT.** No labels. Judging the 1,032 is the unfunded half.

## 2. Phase E: the rows arrived, the fitter refused them (#154)

The 09:30 cycle took the cumulative count to **202 of 200**. `fit_normalization.py` fits cleanly
(n=202, `raw_min` **4.5** exactly, a file both consumer guards accept) and then hard-errors on its
own #205 check: it compares `sample_min` (**4.5069**) against an **absolute**
`MAX_NORMALIZATION_RAW_MIN = 4.5` — which **is** this filter's op-point. Gap to anchor **0.0069**
against the advisory tier's 0.5.

⭐ **At a 4.5 op-point that guard is a sample-DENSITY test, not the bias test it documents.** Its
own comment names the expired premise: *"no false-block possible for any real op-point
(3.75/4.0)"*, written 2026-07-16 before #102. `uplifting v7` passed it in August with a true
`sample_min` of **4.500027** on 15,698 rows — and **a refit of v7 on these four cycles would fail
it** (min 4.5018). Same filter, same op-point, opposite verdict.

⛔ **Not changed** — deploy-path guard, owner ruling. ⛔ **And the fix is two files**:
`tests/unit/test_normalization_invariant.py:190` asserts the same bound on every committed
package, so a fitter-only change leaves the output uncommittable.

⚠️ NM#319 quantified: **60.4%** (122/202) would clear the normalized 4.0 enrichment gate against
100% today, effective raw bar **4.872**. ⛔ **In-sample and near-tautological** — normalized 4.0
*is* those rows' own 40th percentile. A projection, not a measurement.

## ⛔⛔ VERIFICATION IS NOT REVIEW — 8th session running, and this time it changed the answer

762 tests, the registry checker, doc-claims, claim-shapes, both budget guards and the
filter-table check all green. A four-lens `/review-changes` returned **FOUR BLOCKERS, all in this
session's own code**, two of which changed a published conclusion:

1. ⭐⭐ **THE KEEPER — section 2 mixed two instruments, and on the frame I published my own
   headline was not established.** 3,162 rows carry an **e5 probe estimate** in
   `raw_weighted_average`. On that frame the noise null gives within-union rho **0.3654
   [0.3281, 0.4172]** against an actual **0.3463** — *inside the null*. On the clean frame it is
   excluded decisively. **The conclusion was right; the evidence for it was not.** And the
   control written to prevent exactly this was a **`print`, not an `assert`**, in a section headed
   *"they run in `compare.py` and assert"* — with a gloss true in its first clause and false in
   its second.
2. **"Spearman 0.224" was not Spearman** — global ranks correlated inside a subset. It is 0.3463.
3. **"The prompt work is not what separates the lenses"** was a count comparison across a 6-vs-56
   denominator; on rates it points the **other** way (33.3% vs 17.9%, 1.87×, Fisher p = 0.328).
4. **"55% would leave ovr.news entirely, ≈143/cycle"** — a surfacing measurement stated as
   reader-facing, with a per-cycle rate that averaged in the backlog cycle.

Also corrected: the 0.246-vs-0.127 reconciliation named a *population* difference where the two
are different **quantities** (oracle labels vs student surfacing); "5.30% design-weighted" was the
**unweighted** rate (design-weighted is 3.1638%); the 0.16 noise floor was imported unnamed and is
the **smallest** measured term (sensitivity now published); `extract.py` used `.get()` where its
docstring promised a raise; the cross-lens join and the lens set were unasserted; the window was
published as 17h against an actual **11h38m**.

⭐ **What made the keeper findable was mutating the world the code runs in** — building the null
nobody had built — not re-reading the lines. Same lesson as 2026-09-06's detached-HEAD finding.

## Corrections published

Both #151 and #154 had already been commented before the review, so both carry a correcting
follow-up rather than an edit. Four superseded surfaces updated: `CLAUDE.md`,
`memory/filter-status.md`, `filters/human_thriving/v8/STATUS.md` and `docs/TODO.md`'s 09-07
sizing projection (which predicted 2–3 cycles at v7's 5.81%; v8's measured rate is **1.093%** and
it took five).

## Second half — the harm panel, and the answer to "what went wrong with v8"

⛔ **OWNER RULINGS, both relayed through the session and recorded in `docs/TODO.md`:**
**production FREEZES as-is** (no cutover, no Phase E fit, no config change; both lenses keep
scoring), and **a redo is `human_thriving/v9` — a new VERSION, not a new name**, because
`NexusMind/scripts/main.py:415` keys `.processed_ids_<name>.json` on the filter NAME, so a
rename re-creates the 2026-09-07 outage while a version bump makes it **absent, not mitigated**.

**`EXP-031` — the harm panel, $0.35, owner-authorised.** The question no precision number here
had asked: not *is this on-lens* but *would a reader be harmed seeing this under Thriving*
(#91). Pre-registered in `c54f595` **before any call**, with a named failure condition.

⛔ **MY PRIMARY PREDICTION WAS REFUTED, under both judges.** `harmful` on what each lens uniquely
surfaces: v7-only **3.3%** vs v8-only **10.8%** (DeepSeek, p=0.198); **23.3%** vs **27.0%**
(Gemini, p=0.809). **v8 is NOT safer per article than v7 on harm.** ⚠️ Neither difference is
distinguishable — the point estimates reverse the prediction, the tests do not establish that v8
is worse. ⭐ What v8 *does* win under both judges: `misleading` **21.6%** vs 63.3%/48.3%
(p=0.0001/0.0101), on-promise 67.6%/51.4% vs 33.3%/28.3%. **v8 is substantially better at what
the tab promises and is not better at avoiding harm — separable axes, and reporting either alone
misleads in opposite directions.**

⭐⭐ **THE KEEPER — the answer to the owner's "what went wrong": a step function distilled into a
regression head.** Re-scoring the flagged rows with **v8's own oracle** at k=3: it fires
`harm_is_subject` at wa **0.80–0.90** on three articles where the student returns **4.66–4.85** —
gaps of **+3.76 to +4.04**, landing just above the 4.50 op-point. v8's prompt forces all six
dimensions to 0–2 when the scope gate fires; a regression head cannot represent a discontinuity
and interpolates across it. ⭐ **The leak is GENERAL** — the same gap appears on two v7-only rows
(+3.00, +2.88) where the interpolated value landed *below* the op-point and harmed nobody. **A
threshold move cannot fix a 4-point leak.**

⭐ **The owner recognised the shape, and the record was sharper than either of us recalled.** We
have hit bimodality three times — **ADR-015 on `thriving v1`, the SAME lens** (*"a sparse 2-5 dead
zone the student model couldn't learn"*), `solutions` v4→v6, and ADR-003's needle-in-haystack.
**Every prior fix changed the TARGET so the student could learn it, and none transfers**:
`thriving v1`'s cliff was an accidental orthogonality clause ADR-015 simply deleted, whereas
**v8's cliff IS the harm gate #91 says we need**. Written up as
`docs/decisions/2026-09-08-scope-gate-two-head.md`.

⭐ **Owner's framing — "a crude passer, not a blocker" — was load-bearing, not semantics.**
`scope_verdict` is a five-way scope decision on **all 6,586 rows** of `labels_v84_merged.jsonl`
(`in_scope` 23.9%, `harm_is_subject` 19.0%), so the classifier needs **no re-labelling and costs
$0** — but `training/prepare_data.py` **drops it at split time** (**#155**, the one blocking
prerequisite). Two consequences the blocker framing would have got wrong: **scope is per-lens,
junk is cross-lens**, so the gate belongs inside the filter package; and the scope gate is
**specificity-first** where the Stage-1 probe is recall-first, so reusing the probe recipe tunes
it exactly backwards.

⭐ **And the owner's second idea beat my write-up**: a **cross-lens harm detector** (**#156**).
Measured: of the 9 articles both judges called harmful, **6 are already on `solutions` or
`belonging`** — at a 53% cross-lens rate against a **58% panel baseline**, i.e. harm-subject
content is as cross-lens as anything else. ⛔ **Which is why it must STAMP, not block**: "Bihar
copes with floods" betrays Thriving and is arguably right under Solutions; Recovery is *about*
recovering from damage. **It gates `uplifting v7` — the lens actually serving readers — without
retraining anything**, which a per-lens v9 gate cannot do.

⚙️ Also: `docs/decisions/2025-11-13-regression-only-student-models.md` now carries an **amendment
note** — its title reads as a blocker for the two-head proposal and it is not; it decides
regression vs *generative* on inference latency.

## Cross-session

Five exchanges with `nexusmind-0a`. ⭐ **They independently reproduced `EXP-030` exactly**
(1,184/168/152/1,032/16, Jaccard 0.127) before my message arrived. ⛔ **They corrected me once and
were wrong** (`raw_min` vs `sample_min` — two fields, two guards; their own 4.503588 measurement
was the best evidence *for* the density reading they were arguing against), and ⛔ **they caught
a real ambiguity in mine** — a handover figure written as "what the lens uniquely surfaces"
without naming the lens, where the two readings point opposite ways. They blocked rather than
guessed. Also corrected my symbol name (`_build_filter_config`, not `load_filter`), and I
corrected their "no staging exists" (the `version_dir` pin, and `uplifting` already runs v6+v7).

⚠️ **Their per-lens rate table was wrong** — a uniform `raw >= 4.5` applied to five lenses it does
not belong to (`solutions` 0.21% vs the true 4.31%); the diagnostic that found it was that **the
two lenses we both measured directly agreed exactly and the four reached by a retyped threshold
did not**. Retracted in three places on their side.

## State at close

- ⛔ **FROZEN**: #151 cutover, Phase E (202/200, blocked by #154), #154 itself — parked, owner
  *"don't know"*, and **possibly moot** if v9 takes an op-point other than 4.5.
- ▶ **START AT #156** (harm detector), first step **#155**, which the v9 redo needs anyway.
- **`docs/TODO.md`'s top block was rewritten** into three lanes so a cold session opens in the
  right place — it had still been opening on Phase E and the cutover, both frozen.
- Everything pushed through `9386017`. Nothing deployed, enabled or fitted; sadalsuud untouched
  beyond reads.
- **Nothing was pushed**, and nothing on sadalsuud was touched.
- **Carried from the 09-08 first session:** the `_wa` aggregation control is still not in the test
  suite; an authorship-independent judge is still blocked.
