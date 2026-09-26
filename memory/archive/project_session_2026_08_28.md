---
name: project_session_2026_08_28
description: v8 Phase 0 opened — the Gate 0 targets were measured on a population no draw can sample from, the census script had never been runnable, and the corpus shape hides a stage-1 false-negative trap.
metadata:
  type: project
---

# 2026-08-28 — Phase 0 measured, and the yardstick was wrong

*No spend, no model, no filter, **nothing deployed**, no threshold or probe touched.*
Changed files are `scripts/analysis/`, `docs/`, `memory/`, `CLAUDE.md`. Nothing reaches a
path NexusMind runs — **deploy is N/A, not skipped.**

## What was asked

*"where were we? time to do some real work?"* → chose `human_thriving` v8 Phase 0 from four
options → measure → explain it end to end → push and file the refcheck issue → a design
question about the two-stage corpus → **"i do not want FN again, we need to be careful."**

## ⛔⛔ THE KEEPER — an exclusion stated in prose never reached the numbers

All five Gate 0 corpus targets were measured over a production census that **includes
`news.google.com`, 22.1% of rows** — while the same plan says in bold that GN is excluded
from every draw. The yardstick described a population no draw can sample from.

| target | plan | drawable | |
|---|---|---|---|
| positive base rate | 7.74% | **9.76%** | enrichment 3.6× → **2.9×** |
| non-Latin | 7.26% | **9.76%** | |
| median length | 1,349 | **1,900** | corpus 2× → **1.37×** |
| p10 length / sub-300ch | 84 / 30.8% | **235 / 11.9%** | |
| class-A (harm in title) | 0.87% | **0.70%** | |
| pool | 206,221 rows | **179,111 articles** | |

⭐ **"Production p10 = 84 ch, the short-form regime is under-trained" is largely a statement
about Google News headline echoes** — excluded by rule. Real, and about a third the size
anyone thought (21,374 articles). **12th occurrence of *establish what a source excludes*,
with the opposite sign: the source INCLUDED what the analysis forbids.**

## The instrument had never run

`corpus_census.py` and `production_census.py` both `from hcv1_probe import script_of` — a
module absent from disk and from **all** of git history. The published numbers were right;
the path to re-derive them had never worked. `script_of` is committed one file over.
⭐ **Proving the repair *runs* is not enough — proving it is the SAME instrument is**: re-run
against the frozen 6,590-row corpus it is **byte-identical** to the 08-22 log. A frozen
input is what makes that a control. ⚠️ `gpu-server:~/llm-distillery` is not a git repo and
its prefilter is dated **2026-03-09** with no `_compiled_exclusions`, so the census cannot
ever have run there.

## ⛔ Two of my own, both refuted by measurement

1. **I predicted row-level duplication and there is none** — 232,845 rows → 232,842
   distinct ids. An article is scored once, not per cycle. That was my *reason* for writing
   the drawable-population script.
2. **I prescribed a change to a distribution without measuring it.** My three-region spec
   said over-sample the decision band *and* the visible band. The corpus is already
   **4.21×** over-weighted in 5.5–10 (15.8× at 7.0–7.5, **134×** at 7.5–8.0). It already
   had what I proposed to buy. **A tail is only thin relative to something** — v7's p99 is
   7.15 against production's 6.10.

## ⭐⭐ The FN trap the owner caught

I said enrichment is safe for the probe because "the FN-rate target transfers across
prevalence". **True for prevalence, false for MIX.** `P(pred < t | y=1)` is invariant to how
*common* positives are only if the distribution *within* the positive class is unchanged:

| | positives | marginal 4.5–5.5 | high 5.5+ |
|---|---|---|---|
| corpus | 28.22% | **46.8%** | 53.2% |
| production | 9.76% | **63.5%** | 36.5% |

Skewed **1.36× toward easy positives**, and marginal positives are the ones a screen misses.
**So v7's probe recall was estimated on an easier population than it serves — today, not
hypothetically.** ⚠️ What makes it survivable is that the probe **routes 88.6% to stage 2**
(threshold 1.00, calibrated when MEDIUM was 4.0, never re-derived after #102). **A harder
screen converts that slack into unrecoverable FNs.**

Spec, in Phase 0: add no mass above 5.5; hold the positive mix at 63.5/36.5; spend the
freed budget on 1.5–3.5 (where stage-2 FPs are born, thinnest at **0.43×**); validate
FN@MEDIUM+ on a production-mix cohort via `--recall-check-file`; **stage-1 aggressiveness is
its own owner decision.**

## Also

- **#134 filed** — `refcheck.py`'s `DOCS` is `CLAUDE.md` + `memory/*.md`; **167 files under
  `docs/` are unscanned**, including the plan, the playbook and every ADR. Magnitude
  deliberately NOT guessed. Tiering (frozen vs live) must be settled first.
- **The archive window ROLLED**: `08-14 → 08-28`, not the plan's `08-07 → 08-21`. Targets are
  window-stable (<0.6pp), but harm rows above the op-point went **91 → 78**, so "~6.5/day" is
  **~5.6–6.5/day**.
- Archive excludes **every gate-blocked article** (100% `disposition: kept`).
- Prediction ranges recorded before the run: **4 of 5 inside, visible band missed low**
  (predicted 4–8%, actual 3.562%).

## Next session

1. **Owner: the base rate** (Phase 0 reserves it) and **stage-1 aggressiveness**.
2. Class-A supplement TP/FP balance as a number.
3. Stage the corpus on b650 + `corpus_manifest.json` (#127).
4. #134 step 1: run refcheck over `docs/` behind a flag, then tier.
