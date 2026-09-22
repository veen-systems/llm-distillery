# Phase E is fitted, and the guard that blocked it measured the wrong quantity

*2026-09-22. Decider: Jeroen Veen. Three rulings, all given **in the session that asked**,
after the same three arrived earlier that day via the NexusMind peer session and were
**refused as relays** — see `docs/TODO.md`'s handoff block and commit `89c0cf8`.*

## What was ruled

| # | Question | Ruling |
|---|---|---|
| 1 | `ADR-022` amendment: signals inside it **(a)** or a separate ADR **(b)** | **(a)**, as drafted |
| 2 | llm-distillery#154, the fit guard | **Option 1** — test the gap, not the bound |
| 3 | NexusMind#319, enrichment starvation after a fit | **Accept** — parity with `uplifting v7` |

## 1. ADR-022 — ruled (a)

The DRAFT line at `:13` is struck and the amendment is citable from 2026-09-22.
`deciders:` was **already** `[Jeroen Veen]` and was never the evidence of settledness —
that field reads identically on settled and draft ADRs, which is the confusion the queue
item itself warned about.

⚠️ **The trade-off was stated before the ruling, not discovered after it.** Under (a), a
future *"that is ADR-022"* citation for a signal shape becomes roughly right, which sits
uncomfortably close to vindicating the four citations that were wrong. It does not: they
predate the amendment and cited the Gate-Module Contract, whose three clauses harm
violates. *What this does NOT license* is what keeps (a) from becoming an escape hatch.

✅ **Clause 4's prerequisite discharged the same day**: `NM 007be0a`, Contract B **1.21.0**
writes the declaration rule NM#521 asked for. Clause 4 is **unblocked but unimplemented** —
no lens records its harm evaluation yet.

✅ The one outstanding citation, **#156's body**, is corrected in place with a dated
correction block rather than a silent rewrite.

## 2. llm-distillery#154 — the guard was a density test at a 4.5 op-point

`fit_normalization.py` hard-errored on `sample_min > MAX_NORMALIZATION_RAW_MIN`, reusing
the **loader's** bound (which is about `raw_min`, and is still checked separately) as if it
were a margin. That holds only while the op-point sits under 4.5. Both sides are now
measured on the same filter, same op-point, same anchoring:

| population | `sample_min` | gap to anchor | old guard |
|---|---|---|---|
| 202 rows (2026-09-08 window) | 4.5069 | 0.0069 | ⛔ **hard-blocked** |
| 2,976 rows (today) | 4.5 | 0.000042 | ✅ allowed |

⭐ **The second row is the finding, and it is worse than the first.** The true minimum was
**4.500042** (the CDF's `x[1]`; nothing on disk carries more precision, so do not quote more), and `stats.sample_min` is `round(x, 4)` — so the fit was permitted because
the lowest article of 2,976 fell inside a **5e-5** rounding window. Measured density at the
bar is 51 rows per 0.01, i.e. ~5,100 rows per unit raw; under an exponential spacing
approximation that window is hit with probability **~22%** *(inferred from the measured
density, not itself measured)*. **The verdict on a production fit was decided at the 5th
decimal.** A guard whose answer is a coin flip is not enforcing the policy it documents.

⛔ **My own prior claim, corrected:** before running it I said the larger population "does
not rescue" the fit and would need ~34,000 rows. The run refuted that — it passed at 2,976.
The error was assuming uniform spacing across the whole range instead of measuring the
density at the bar. ⚠️ **Both figures need their range named, which the first version omitted:**
~34,000 and "~3× higher" are against the **202-row** fit's range of 1.72. Against the shipped
2,976-row fit's range of **2.252** the same arithmetic gives **45,040** and **3.86×**.

### What shipped

`MAX_SAMPLE_GAP = 0.5`, a **separate constant** from `MAX_NORMALIZATION_RAW_MIN`, tested as
`sample_min - anchor`.

⛔ **It is identical at op-point 4.0 and NOWHERE ELSE, and the first version of this record
said "3.75/4.0 … unchanged", which is false.** `sample_min > 4.5` means `gap > (4.5 -
op_point)`, so a flat 0.5 is:

| op-point | old fired at | new fires at | |
|---|---|---|---|
| 2.25 (`solutions v4/v6`) | gap > 2.25 | gap > 0.5 | **stricter** |
| 3.75 (`nature_recovery v4`) | gap > 0.75 | gap > 0.5 | **stricter** |
| 4.0 (most filters) | gap > 0.5 | gap > 0.5 | identical |
| 4.25 (`investment_risk v6`) | gap > 0.25 | gap > 0.5 | **looser** |
| 4.5 (`human_thriving v8`, `uplifting v7`) | gap > 0.0 | gap > 0.5 | looser — the fix |

No committed package is affected either way; the largest gap on disk is `nature_recovery v4`
at 0.0438. But `nature_recovery v5` (#71) is the filter that would meet the tightening, and
`investment_risk v6` is the one the widening covers. **All three directions are now pinned by
their own test**, so none of them can be relaxed silently.

⚠️ **The deleted advisory carried an argument that promoting it does not answer.** The old
comment said no static threshold separates a subtly biased sample from a legitimately sparse
needle fit — *"they are indistinguishable in the data"* — which is why 0.5 WARNED rather than
blocked. Making it the error asserts the opposite with no new evidence.

⛔ **And deleting it outright was a real regression, caught in review.** At a 4.5 op-point the
old code errored on every gap; the new one admits everything under 0.5, so the whole `[0, 0.5]`
band went from "always blocked" to **silent**. The concrete attack is in this document's own
numbers: a fit drawn from *enriched* output starts at v8's enrichment bar, **raw 4.794** — a gap
of just 0.294, under the limit, while missing 13% of the fitted span. That is #205's literal
root cause, and it would have passed without a word. Shipped instead: a **span-relative
advisory** (`SAMPLE_GAP_ADVISORY_SPAN_SHARE = 0.05`) on the unobserved `[anchor, sample_min)`
band as a share of `[anchor, raw_max]`. It blocks nothing and is computable from the fit alone.

⚠️ **OPEN, and deliberately not settled here:** the hard limit is a **raw-score distance**
while the harm is a **share of the population**, and the two diverge with a filter's spread —
`human_thriving v8` has the narrowest distribution in the repo (`raw_std` 0.368). Whether the
limit should be a percentile is an owner question. It cannot simply be computed: a first fit
has no rows below its own `sample_min`, so the missing share is not derivable from its own
sample.

⛔ **The rule lived in TWO executable places** — the fitter and
`tests/unit/test_normalization_invariant.py`'s committed-package invariant — and both moved in
one commit. ⚠️ It lived in **four more documentary ones** that the first version of this
change missed, and a review census found them: `docs/NORMALIZATION_METHOD.md` (§5.2 and the
§5.3 guard table), `docs/FILTER_PLAYBOOK.md`, `docs/RUNBOOK.md`, and the `human_thriving v8`
package's own `STATUS.md` / `README.md` / `config.yaml` / `base_scorer.py`. All are corrected
here. *Enumeration is not inventory — and the surface that states a rule is not the surface
that enforces it.*
⚠️ **Correction to a claim made in the first version**: "changing only the fitter would have
left the repo rejecting what its own fitter writes" is true as a general statement about the
two-place rule, but **not of the file actually committed** — v8's `sample_min` rounds to 4.5,
so it passes under both the old and the new invariant. The test edit unblocks the NEXT such
fit, not this one.

### Outcome proof, not predicate proof

Two fixtures through the real CLI, before and after:

| fixture | shape | old code | new code |
|---|---|---|---|
| `fx_needle` | 250 rows, min 4.5069, op-point 4.5 | exit 1, nothing written | **exit 0, written** |
| `fx_biased` | 250 rows, min 5.2, op-point 4.5 (the NM#205 root cause) | exit 1, nothing written | **exit 1, nothing written** |

Before the change both produced the *identical* error message — the guard could not tell a
legitimate sparse needle fit from a biased population.

⚠️ **Those fixtures are now a committed test, not a scratchpad artifact.**
`tests/unit/test_fit_normalization_guard.py` runs the real CLI end-to-end over all three
shapes (written-silent / written-with-advisory / refused) plus the `--analysis-only` bypass.
The first version of this change left the only proof of the **deploy-path** guard in an
ephemeral directory, where no later session could re-run it and a future edit could break the
branch with a green suite. *The verified artifact must be the shipped one.*

**Mutation check, with the mutation named** — the count depends on which one you apply, and
the first version of this record gave only the narrow reading:

| mutation | red |
|---|---|
| predicate only (`sample_gap <= MAX_SAMPLE_GAP` → `sample_min <= MAX_RAW_MIN`), message kept | **1** — the #154 regression test alone |
| the whole old block, message included | **3** — two others match on `MAX_SAMPLE_GAP` appearing in the text |

The second pair are therefore partly coupled to message wording and would also redden on a
pure rename. Six regression tests in total across the two files.

## 3. Phase E — `human_thriving v8` is fitted

```
n_articles 2976              raw range 4.50 - 6.752   mean 4.9731 (std 0.368)
raw_min    4.5               sample_min 4.5
```

**Reproduce** (the first version of this record shipped no command for any of its numbers):

```bash
PYTHONPATH=. python3 scripts/normalization/fit_normalization.py \
    --filter filters/human_thriving/v8 --ssh sadalsuud \
    --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/human_thriving
# density at the bar, the 22% window, and the enrichment share, all from the committed file:
PYTHONPATH=. python3 -c "import json,numpy as np; d=json.load(open('filters/human_thriving/v8/normalization.json')); \
  x,y=np.array(d['x']),np.array(d['y']); print('raw at normalized 4.0 =', np.interp(4.0,y,x))"
```

⚠️ **Population provenance, stated because the first version asserted a number it could not
source.** The fitter reports `2,976` retained and `293,660` excluded below the op-point; the
**296,636** total is those two added, which equals "scored" only if the fitter's three other
exclusion counters (foreign attribute block, non-finite, wrong `filter_version`) were all zero
— not shown. `normalization.json` records `fitted_from` (the remote directory) and `fitted_at`
(one instant) but **no cycle window**, so the span behind 2,976 is not stated anywhere.

⛔ **Asserted as EXACT equality, not "under the cap"** — the loader's test is a strict `>`,
so 4.5 is accepted with **zero margin** and a failure would be silent (fall back to
`score_scale_factor`, not a refusal):

```
resolve_op_point(filters/human_thriving/v8)  ->  4.5
stats.raw_min                                ->  4.5
raw_min == op_point                          ->  True   (exact, not within EPS)
```

`tests/unit/test_normalization_invariant.py` now parametrizes `human_thriving-v8` and
passes.

⛔ **NOT a cutover.** `uplifting v7` is still what scores. The switch remains gated on the
same-articles comparison and has no date.

⛔ **Two corrections to the first version of this paragraph, both caught in review, and both
the same shape — a citation attached to the wrong referent:**
- It gave **Jaccard 0.246** as `EXP-030`'s. **EXP-030's Jaccard is 0.127.** 0.246 is a
  different quantity on a different population — two ORACLES' label sets over 660 labelled
  rows, versus two deployed STUDENTS' surfaced sets over 15,372 unlabelled production
  articles. `docs/evidence/2026-09-08-v7-v8-same-articles/README.md:126-139` exists to prevent
  exactly that substitution, and the citation was made inside a parenthetical naming it.
- It gave **1.00% of 296,636** and **7.30% of 385,390** under an `EXP-030` citation and
  dropped the *"Peer measurement, attributed not re-derived"* marking the queue entry had
  carried. Those are **not** EXP-030's numbers: EXP-030 measured **1.093%** and **7.702%** on
  the same 15,372 articles. The two large figures come from the NexusMind peer session, over
  two different and unnamed windows, and `385,390` appears nowhere else in this repo. They are
  restored to **attributed, not re-derived**, and are not evidence of the same quantity
  EXP-030 measured — that they land near each other (7.28 vs 7.05) is not corroboration.

**The same-articles 7× cut is `EXP-030`'s own result** (v7 surfaces 1,184, v8 168, of 15,372),
and that is the one to cite for the cutover.

Nothing was deployed to NexusMind and nothing was uploaded to the Hub — verified rather than
asserted: `filters/human_thriving/v8/normalization.json` is absent from the NexusMind checkout,
from `sadalsuud:/home/jeroen/local_dev/NexusMind`, and from `gpu-server:~/NexusMind`, and this
repo does not exist on the production host. Reaching production needs four deliberate steps
(`deploy_to_nexusmind.sh` → NexusMind commit → `git pull` on sadalsuud → `deploy_filters.sh`).
⚠️ **One guard disappears on commit**: `scripts/deploy_to_nexusmind.sh:135` refuses to deploy
a filter directory containing untracked files, and the file is untracked right now. After this
commit the only thing between the fitted CDF and production is the operator.

## 4. NexusMind#319 — accepted, and the number I gave for it was a tautology

⛔⛔ **CORRECTED. The first version of this record said #154's 60.4% was superseded by a
recomputed 60.0% on 2,976 rows. Both are the same identity, and recomputing it at larger n
repaired nothing.** The CDF is fitted on exactly those rows and the normalized scale is
`10 × CDF`, so *"share above normalized 4.0"* is *"share above this sample's own 40th
percentile"* — **≈60% by construction, for any percentile-normalized filter, whatever the
model does**. My recomputation landing on 60.013% is that identity, not a measurement.

⛔ **The repo had already caught this exact error and I walked into it anyway.**
`memory/gotcha-log.md:7209` retracted the 60.4% on 2026-09-08 under the heading *"An in-sample
share measured against a percentile gate is a tautology"*; `docs/RUNBOOK.md` and the v8
package's own `STATUS.md:149` both carry the warning. Three surfaces said so, and the session
that re-derived the number read none of them. ⭐ The tell was named there too — *agreement
that is too good*: two figures matching to 0.01pp, one of them guaranteed.

**What survives, and what does not:**

| quantity | status |
|---|---|
| v8: 1,786 / 2,976 = 60.0% of the **fitted** rows clear the gate | ⛔ **arithmetic**, not a result — do not quote as a measurement |
| v8: effective **raw** bar for enrichment = **4.794** (op-point 4.50) | ✅ the transferable quantity; it was 4.872 on the 202-row fit |
| `uplifting v7`: 40% of surfaced articles un-enriched | ✅ a real **out-of-sample** measurement — 7,224 of 18,041 surfaced over 82 cycles, 2026-08-23 → 2026-09-06, 251,461 rows (`docs/evidence/2026-09-06-v8-deploy-gate/README.md` §3) |
| "v8 is at parity with v7" | ⚠️ **weaker than it was presented**: it sets an identity beside a measurement. What v7's number really shows is that a live filter has run at 40% un-enriched for months without complaint |

⛔ **What is genuinely unknown**: the share of v8's FUTURE rows that will clear the gate.
That depends on whether the future score distribution matches the fit population, and it can
only be measured on cycles the fit did not see — exactly how v7's figure was obtained.

**The ruling is unaffected.** The owner accepted that fitting arms NM#319, on the basis that
v7 already lives with it — and that basis is the out-of-sample row above, which holds.
Enrichment is post-scoring: nothing leaves the reader's view.

## A control fired, and was NOT repaired by deleting it

`test_fit_calibration_config_write.py::test_the_shipped_v8_package_would_be_refused` went
red the moment Phase E wrote `normalization.json` (it is now
`test_a_shipped_calibrated_package_without_normalization_would_be_refused` — renamed, so
grep for the new name) — its precondition assertion firing
exactly as written, with its own message naming the remedy. It is re-pointed to **search**
for a package with `calibration.json` and no `normalization.json` (today: `solutions v5`,
`thriving v1`) rather than naming one, with an assertion that fails loudly if no such
package remains. Mutation-checked: forcing the decision to "write" kills it.

## A door this opens, recorded so the next Phase D does not re-learn it

Writing `normalization.json` flips `fit_calibration.score_scale_factor_decision()` for v8 from
**False to True** (verified by executing it). A future `fit_calibration.py --filter
filters/human_thriving/v8` **without** `--no-config-update` will now write a
`score_scale_factor` into that package's `config.yaml`, where it was previously refused. It is
inert *by precedence* — the loader prefers `normalization.json` — but only while that file is
ACCEPTED, and acceptance sits at **zero margin** (`raw_min > 4.5` is a strict `>` against
`raw_min == 4.5`). A later refit landing one ULP high would make the CDF inert **and** the
stretch factor live, with nothing louder than a `logger.warning`. Noted in `config.yaml`.

## Review

Six lenses (`guarantee-preservation`, `adversarial`, `doc-accuracy` + this repo's
`reachability`, `claim-verification`, `sync-safety`), structural pre-check on 10 markdown
files. The battery before review was green — 926 tests, both budget guards, doc-claims 6/6 —
which is the state in which this project expects review to find the most, and it did: the
"3.75/4.0 unchanged" claim, the silent `[0, 0.5]` band, the Jaccard misattribution, the
dropped peer attribution, the tautology, four un-updated documentary surfaces, and the
scratchpad-only outcome proof. All are fixed above rather than noted.

⚠️ **Unrelated defect found by the review, NOT fixed here and worth an issue:**
`tests/unit/test_experiment_registry.py:16-26` plants its test defects in the **real committed
`experiments/registry.jsonl`** and restores them in a `finally`. A killed or concurrent run
leaves the planted corruption on disk — which happened during this review, from a
`timeout`-killed pytest. Restored with `git checkout -- experiments/registry.jsonl`. The fix
is to copy the registry to `tmp_path` rather than mutate the tracked file.
