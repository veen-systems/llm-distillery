# Phase C review — did any of this work?

**2026-09-04, after phases 6b and 7 closed. `EXP-017`. $0 spend** — every number here comes
from the 660-row forward pass already on disk (`b650-gpu:~/llm-distillery/ht_v8_test_dump/`).
Reproduce: `phase_c_outcome.py` → `phase_c_outcome.json` / `.txt`.

---

## ⛔ First, a claim reported all through Phase C that is void

Every recall figure in this phase was set beside the deployed fleet's 0.59–0.72, with the
caveat *"those are post-calibration"*. **That caveat is real and it is not the problem.**

On the same 660 test rows:

| | count |
|---|---|
| rows `uplifting v7` calls positive | **117** |
| rows `human_thriving v8` calls positive | **35** |
| rows both call positive | **30** |
| **Jaccard overlap of the two positive classes** | **0.246** |

**v8 keeps 25.6% of what v7 called positive.** The two filters do not have the same positive
class, so "v8's recall is below the fleet's" compares **recall of two different quantities
that share a name**.

Recall is conditional on the true class — which is precisely why it survives a change of base
*rate*, and precisely why it does **not** survive a change of *definition*. `memory/` already
records the weaker form of this correction (recall survives a change of rate, not of mix); a
changed definition is stronger than either.

⚠️ **This was propagated to six surfaces** — `STATUS.md`, this directory's README,
`calibration_report.md`, `docs/TODO.md`, the session record and `H-V8-15` — and it is the
reason Phase C read as a disappointment. All six are corrected. The number itself
(recall 0.486 raw / 0.343 calibrated at 4.5) is right; **only the comparison was wrong.**

---

## What is actually measurable

v8 exists to stop v7 surfacing harm-answered-only and institution-beneficiary content (#107,
the class-A rulings). So partition the rows **v7 surfaced** by what the v8 oracle says:

- **junk** — v7 ≥ 4.5, v8 oracle < 4.5 → v8 says v7 was wrong to surface it. **87 rows.**
- **good** — v7 ≥ 4.5, v8 oracle ≥ 4.5 → both definitions agree it belongs. **30 rows.**

Then ask the trained student two questions, and one control.

### The purpose: how much of the junk does it remove?

At the inherited 4.5 op-point, on held-out data:

| arm | junk removed | good kept |
|---|---|---|
| raw | **79 / 87 = 90.8%** | 17 / 30 = 56.7% |
| calibrated | **82 / 87 = 94.3%** | 12 / 30 = 40.0% |

**Nine in ten of the content v7 was wrongly surfacing does not survive v8.** That is the
defect the whole version exists for, measured on a split the model never saw.

### The control that matters: is it discriminating, or just scoring lower?

A student that had merely learned "score everything lower" would remove junk and lose good
content in step, and would show no gain over v7's own ordering. AUC on those 117 disputed
rows:

| | AUC |
|---|---|
| **v7's own score** (baseline) | **0.7218** |
| v8 student, raw | **0.8454** |
| v8 student, calibrated | **0.8521** |

**+0.12 AUC over the baseline, on exactly the population under dispute.** v8 learned a
distinction v7 did not have. And at bar 3.0 the raw student keeps **90%** of the good while
still removing **62%** of the junk — the two move apart, which is what discrimination looks
like.

⚠️ **Scope, stated.** This shows v8 implements the definition the owner chose. It does **not**
show v8 is "better than v7" in any absolute sense: v7 is being judged against a target it was
never trained on, so 0.7218 is a baseline, not a verdict on v7. Whether the new definition is
the right one is an editorial judgement (#107), not a measurement.

### Class-A rows specifically — the named defect, one row at a time

Only **8** class-A rows reached the test split, 6 of which v7 surfaced. ⚠️ n=6; read the
direction, never a rate.

| v7 | v8 oracle | student raw | student calibrated | still surfaces? |
|---|---|---|---|---|
| 1.30 | 1.00 | 0.97 | 1.02 | no |
| 1.89 | 1.00 | 0.98 | 1.05 | no |
| 4.52 | 0.90 | 2.88 | 3.17 | no |
| 4.83 | 0.80 | 1.59 | 1.70 | no |
| 5.36 | 4.08 | 4.33 | 4.09 | no |
| 5.58 | 0.90 | 1.30 | 1.31 | no |
| **6.28** | **1.05** | **5.10** | **4.87** | **yes, both arms** |
| **6.57** | **1.00** | **4.85** | **4.28** | **yes, raw only** |

⛔ **Two rows the oracle scores ~1.0 the student scores ~5.** The prompt fix works; the
student only partly inherits it, and it fails on the highest-scoring v7 rows — the ones a
reader is most likely to see. Calibration rescues one of the two.

---

## ⭐ The finding that changes what to do next: calibration is not neutral here

Phase 7 was written up as *"the same ranker as raw, no distinguishable effect, ships because
ADR-008 requires it."* Measured against v8's actual purpose rather than against aggregate
recall, calibration is **the better arm on every axis that matters**:

- junk removed at 4.5: **90.8% → 94.3%**
- AUC on the disputed rows: **0.8454 → 0.8521**
- and it demotes one of the two class-A rows the raw student still surfaces

⚠️ These are small margins on small n (87 junk rows, 8 class-A) and the #95 bands on aggregate
recall/specificity still overlap. **This does not overturn "not distinguishable"** — it says
the aggregate metric was the wrong place to look for the difference. Ship it, and now for a
reason better than "the ADR says so".

---

## The Phase 8 decision, in two tables — the sample, and the population

The op-point is the only untried lever and it costs nothing to move. Raw arm:

| bar | junk removed | good kept | specificity |
|---|---|---|---|
| 3.00 | 62.1% | 90.0% | 0.9168 |
| 3.75 | 78.2% | 80.0% | 0.9552 |
| 4.00 | 82.8% | 73.3% | 0.9664 |
| **4.50 (inherited)** | **90.8%** | **56.7%** | **0.9856** |
| 5.00 | 96.6% | 23.3% | 0.9952 |

⭐ **ADDED 2026-09-05 — THE DESIGN-WEIGHTED ARM, and it does not change the decision.** The
660-row split is drawn under a stratified design spanning **25.1×** in `inclusion_probability`
(`docs/evidence/2026-08-29-v8-corpus-draw/`), so every share above describes the rows drawn,
not the corpus. ⚠️ **"arm" means raw vs calibrated everywhere else in this file**; here and
in `phase_c_outcome.py`'s output it also names unweighted vs design-weighted, so the script
prints four sweeps — two model arms × two weightings. Horvitz–Thompson weighted, raw arm:

| bar | junk removed | good kept | specificity | (unweighted, for comparison) |
|---|---|---|---|---|
| 3.00 | 62.7% | 90.0% | 0.9432 | 62.1% / 90.0% |
| 3.75 | 80.0% | 80.1% | 0.9715 | 78.2% / 80.0% |
| 4.00 | 84.9% | 73.4% | 0.9797 | 82.8% / 73.3% |
| **4.50 (inherited)** | **92.4%** | **56.8%** | **0.9932** | **90.8% / 56.7%** |
| 5.00 | 97.4% | 23.5% | 0.9983 | 96.6% / 23.3% |

⛔ **What the weighting moves most is the base rate, and the trade least.** v8's positive rate
goes **5.3030% → 3.1638%**. ⚠️ *That ratio is 1.6762; EXP-024 prints the same two rates off the
same 660 rows and the same field, so the agreement is guaranteed by construction and is not a
cross-check — and the ratio itself appears in no EXP-024 artifact.*

Maxima of |weighted − unweighted|, **over all 7 bars and BOTH arms** (`phase_c_outcome.json`):

| quantity | max shift | where |
|---|---|---|
| junk removed | **+2.44 pp** | calibrated, bar 4.00 (raw's own max is +2.27 at 4.25) |
| good kept | **+0.20 pp** | calibrated, bar 4.50 |
| **specificity** | **+2.65 pp** | raw, bar 3.00 |
| recall | **−8.51 pp** | raw, bar 3.50 |

⭐ **So the trade the owner is choosing between has the same shape on either arm, and 4.5 does
not become a different decision when weighted.** ⚠️ **But note which two quantities move
least.** Specificity — ADR-023's own criterion — moves up to 2.65 pp, always upward, and recall
up to 8.51 pp downward; both are rates over the whole split, where the design over-samples
positives. Junk-removed and good-kept are conditional on the v7-surfaced partition, which is
why they are the stabler instrument for this decision and also why quoting only them
understates how much the weighting matters elsewhere.

⚠️ **Neither arm carries a band**; the junk/good columns rest on 87 + 30 rows. ⚠️ **The
specificity column has a different denominator from its neighbours** — 625 negatives over the
whole 660-row split, not the 117 v7 surfaced (`phase_c_outcome.py`, `neg = [...]`); three
columns, two populations, one table.

⭐ **Under ADR-023 the inherited 4.5 is defensible and possibly right.** *"A false positive
costs a reader; a false negative costs nothing visible."* Moving 4.5 → 4.0 buys 5 good
articles and lets 7 junk ones back through — the wrong direction under the project's own
stated loss function. **The low recall is the cheap error, deliberately chosen, not a defect
to fix.**

⚠️ So Phase 8's job is **not** to raise recall. It is to decide, with the owner, how much
agreed-good content is worth losing for the last few points of junk removal — and to make
that choice on the **calibrated** scale, since 4.5 means something different there.

---

## Is this going anywhere? — yes, and here is the honest ledger

**What v8 has bought, measured:** 90.8% (raw) / 94.3% (calibrated) of the content v7 wrongly
surfaced is gone, on held-out data, with +0.12 AUC over v7 on the disputed rows. The prompt
work that took most of the spend (v8.4, the class-A adjudication) reached the student.
⚠️ **Unweighted sample shares**, like every figure in this ledger — design-weighted they are
92.4% / 95.0%, per the table above. The rule stated there applies to the shares *below* it too.

**What it costs:** 43–60% of the content both definitions agree is good, at the inherited
op-point (**design-weighted 43.2–59.8%** — the weighting moves this by at most 0.2 pp). Real, and the reason to hold Phase 8 open rather than deploy on these numbers.

**What is still unproven:** the student under-learns class-A on the highest-scoring rows
(2 of 6, both scored ~5 against an oracle ~1); the multilingual recall question is
unmeasurable at 8 non-Latin positives (#141); and the op-point is inherited, not derived.

**Total spend to date: $7.62.**

---

## Files

| file | what it is |
|---|---|
| `phase_c_outcome.py` | the analysis, committed so every number above is reproducible |
| `phase_c_outcome.json` | its full output: 2 arms × unweighted and design-weighted = 4 sweeps |
| `phase_c_outcome.txt` | the console run, verbatim |

⚠️ The per-row score dumps it reads are **not committed** — they carry ids for corpus rows
whose text is gitignored (#97). They live at `b650-gpu:~/llm-distillery/ht_v8_test_dump/`.
