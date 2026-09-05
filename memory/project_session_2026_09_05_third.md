# Session record — 2026-09-05 (third session)

**$0 spend. No oracle calls, no GPU, no training.** Arithmetic on dumps that already
existed, plus one new verification script. **Deploy N/A, not skipped** — v8's weights are
gitignored (#97) and live only on `b650-gpu`; sadalsuud's `NexusMind/filters/` has no
`human_thriving` (verified 2026-09-04, unchanged).

Commits: `347a239`, `e6ddb09`. Experiment: **EXP-025**. Not pushed.

---

## What was owed, and what it produced

`docs/TODO.md` carried four mechanical checks owed from `EXP-024`'s review — four of that
round's five defects have a mechanical shape. They are now
`scripts/verification/check_claim_shapes.py`, 43 tests, wired into `memory/MEMORY.md`'s
verify annotations:

| check | what it demands |
|---|---|
| `no-difference-range` | a "no difference at all X" claim must publish the range over which it COULD have differed |
| `zero-width-interval` | a published [x, x] interval is a defect signal; one printed exemption for a declared null control |
| `ordering-needs-band` | a quantified comparative ordering needs a band or p-value in its paragraph |
| `design-weights-read` | an analysis reading a design-weighted population must read the weights or declare in writing why not |

**19 real sites over three rounds**, on a tree that had just passed the whole battery.

## ⛔⛔ THE KEEPER — the review of the checks found more than the checks did

A four-lens `/review-changes` on a **green** mechanical battery (707 tests, registry, both
budget guards, doc-claims, 22/22 annotations) returned **3 blockers and 10 warnings**.

1. **The guard against guards-that-examine-nothing had a root that examined nothing.**
   `experiments` sat in the JSON scan roots behind `endswith(".json")`, and
   `".jsonl".endswith((".json",))` is **False** — 0 files, `registry.jsonl` unscanned, the
   `.jsonl` guard beneath it unreachable dead code.
2. **The flagship file survived its own mutation.** `_reads_field` accepted any
   non-docstring string constant, so deleting the **only** real weight read from
   `phase_c_outcome.py` still PASSED: the field's name survived in an error message and a
   JSON label. *Mention is not use*, 4th and 5th occurrences, the first of them committed by
   the declaration written to explain the rule.
3. ⭐ **My own fix deleted the trigger instead of the defect.** Rewriting an unbanded
   ordering to add a band moved the verb off the line carrying its two numbers, so the
   per-line trigger stopped matching. The site was not qualified — it became **invisible**,
   the check re-ran green, and a site count I had already published failed to reproduce.
   Re-joined onto one line it **still FAILED**: the hedges matched no band vocabulary.
   ⭐ **After any edit made to satisfy a checker, confirm the site is still EXAMINED —
   count sites before and after, not just the verdict.**

Two of my claims were retracted before the first commit: *"good-kept moves at most +0.5 pp"*
(measured **+0.198**) and *`quantified_orderings: 3`* (it was **2**).

## ✅ What stands, and what it means for phase 8

**The op-point decision is unchanged by design weighting.** `phase_c_outcome.py` produced
the phase-8 trade table unweighted on a split drawn under a **25.1×** design; it now prints a
Horvitz–Thompson arm beside every sweep, and every previously published number reproduces
byte-identically (61 keys added, 0 changed, 0 removed).

Raw arm, junk removed / good kept: **3.00 → 62.7% / 90.0% · 4.00 → 84.9% / 73.4% ·
4.50 → 92.4% / 56.8% · 5.00 → 97.4% / 23.5%**. Over all 7 bars and both arms, junk-removed
moves at most **+2.44 pp**, good-kept **+0.20 pp**.

⛔ **But those are the two quantities that move LEAST.** Specificity — ADR-023's own
criterion — moves up to **+2.65 pp**, recall **−8.51 pp**, and the base rate goes
**5.3030% → 3.1638%**. The trade columns are conditional on the v7-surfaced partition, which
is why they are the stabler instrument here and why quoting only them understates the
weighting elsewhere.

**A third unbanded ordering, now measured.** `GATING_DECISION.md` published *"regression
e5-small ranks far better than the shipped probe (AUC 0.9035 vs 0.8710)"*. Paired bootstrap,
both published AUCs reproduced as a control: **ΔAUC +0.0325, 95% CI [−0.0054, +0.0725],
P = 0.094 — NOT DISTINGUISHABLE** (`scripts/auc_ordering_band.py`). The section's conclusion
— *a better ranker does not buy a safer screen* — is strengthened, not weakened.

## ⚙️ #139 — the look the owner asked for, taken

`import filters.cultural_discovery.v5.inference` **succeeds** from the repo root. The
shipped filter is fine; the **test harness** is broken — `spec_from_file_location` gives the
module no package, so `from .base_scorer import ...` cannot resolve. Test-side fix, touches
no filter package. Left for the owner: cd v5 is LIVE and the issue is theirs.

## Structural

- **`CLAUDE.md` moved +0 B** while two occurrence entries were added (18th *prove the
  outcome changed*, 22nd *establish what it excludes*, plus the 5th *mention is not use*).
  All **+3,182 B** went to `memory/working-rules.md`. The monotonic floor `H-CX3` named is
  gone, and the cause is the 2026-09-04 inversion of `check_doc_claims.py`'s `rule-ordinals`:
  a copy that does not exist cannot grow.
- **`H-CX4` registered**: mechanising a defect shape reduces what an adversarial lens then
  finds. Stated as the thing `EXP-025` does **not** claim, with the first evidence pointing
  the other way.

## ✅ All three owed decisions RULED, same session

1. **Phase-8 op-point: 4.50 on the CALIBRATED scale.** No code changed — the runtime already
   carried it; its status changed from *inherited* to *re-derived and ratified*.
   `docs/decisions/2026-09-05-v8-op-point.md`. ⭐ The argument is the **shape** of the trade:
   from 3.75 up every step costs ~1 agreed-good article per junk article, and ADR-023 breaks
   a 1:1 trade toward specificity. The frontier bends at **3.50** (−3 good buys −11 junk),
   so that — not 4.0 or 4.25 — is where to go if volume is ever wanted. ⛔ 5.00 was never
   available: `MAX_NORMALIZATION_RAW_MIN = 4.5`, strict `>`. Verified by **executing**
   `_assign_tier` at the boundary and by reading the path that proves the comparison is
   against the **calibrated** score (`filter_base_scorer.py:315-317` → `:340`).
2. **The rescued probes: a PRIVATE Hub repo, not git** —
   `https://huggingface.co/jeergrvgreg/llm-distillery-probes`, verified `private=True` and
   all 11 present by **listing the repo**, not by the upload not erroring. ⭐ Two findings
   from sha256 rather than filenames changed the shape of it: **two of the eleven were
   already in git** byte-identically (`probe_v2.pkl` IS v8's shipped probe), and **four are
   named after production filters and are not those filters' probes**. The identity gap
   EXP-024 §6 logged is half-closed — every pickle carries its own
   `objective`/`seed`/`device` under `metrics`, not at top level.
3. **#139 fixed, and the shipped filter was never the problem.** Dotted-path import instead
   of `spec_from_file_location`. ⭐ Seeded with a true positive before being believed:
   breaking one filter's `inference.py` makes the repaired test FAIL. **The suite is now
   711 passed / 0 failed** — the first fully green run in months.

## Owed, still

Nothing is waiting on an owner decision. Phase 8's remaining work is the **deploy-gate run**
itself (ADR-021, held-out oracle ground truth), which needs the weights on `b650-gpu`.
