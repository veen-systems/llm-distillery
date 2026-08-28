# v8 Phase 0 — the Gate 0 targets were stated against the wrong population

**Measured 2026-08-28.** Raw logs: `docs/evidence/2026-08-28-v8-phase0-runs/`.
Scripts: `scripts/analysis/production_census.py`, `corpus_census.py`,
`v8_draw_population.py` (new).

Phase 0 of `docs/HUMAN_THRIVING_V8_PLAN.md` requires the corpus targets to be
**stated as chosen numbers before drawing**. The plan states five, sourced from the
2026-08-22 production census. This checks them, and three things moved.

---

## 0. The instrument did not run

Both census scripts imported `script_of` from `hcv1_probe`, a module that is absent
from disk and from **all** of git history (`git log --all` returns nothing). Both
failed at import with `ModuleNotFoundError`, so the reproduction path named in
`docs/evidence/2026-08-22-uplifting-v7-corpus-provenance.md` had never worked from a
clean checkout. `script_of` is committed, in `prefilter_removal_probe.py:55`;
`hcv1_probe` was a scratch copy. Repointing the import is the whole fix (`818721f`).

**The fix is instrument-identical, not merely runnable.** Re-run against the frozen
6,590-row v7 corpus, the repaired census is **byte-identical** to the 2026-08-22 log
(`diff` clean): 30 harm-title (0.46%), 4/1/25 bands, 1,860 positives (28.22%), 301
non-Latin (4.57%), 697 domains. A frozen corpus makes that a real control — any drift
in `script_of` would show as a differing count.

⚠️ **gpu-server cannot run it and never did.** `gpu-server:~/llm-distillery` is not a
git repo; its `filters/uplifting/v7/prefilter.py` is dated **2026-03-09** and has no
`_compiled_exclusions` at all, so `corpus_census.py` line 19 would raise there. The
census ran from a scratch tree that has since been cleaned — which is also why
`hcv1_probe.py` was never committed. Both runs here use a minimal tree staged under
`/tmp`; **the production scorer's own tree was not touched.**

Local `filters/uplifting/v7/prefilter.py` is unchanged since 2026-08-03 and its pattern
counts are the documented 21/19/37, so **local is the 08-22 instrument.**

---

## 1. The targets are window-stable — but the damage rate is not

The plan's production column is a 14-day archive window, `2026-08-07 → 08-21`. That
window **no longer exists on disk**: retention has rolled it to `08-14 → 08-28`. Same
instrument, new window, half-overlapping:

| quantity | 08-07 → 08-21 | 08-14 → 08-28 | Δ |
|---|---|---|---|
| stage2 rows | 205,939 | 206,221 | +0.14% |
| harm as dominant subject (title) | 1,798 (0.87%) | 1,828 (0.89%) | +0.02pp |
| positive base rate (raw ≥ 4.5) | 15,935 (7.74%) | 16,102 (7.81%) | +0.07pp |
| non-Latin script | 14,954 (7.26%) | 16,100 (**7.81%**) | **+0.55pp (+7.6% rel.)** |
| median content length | 1,349 | 1,360 | +11 ch |
| p10 content length | 84 | 84 | 0 |
| distinct domains | 1,389 | 1,382 | −7 |
| `news.google.com` share | 22.44% | 22.10% | −0.34pp |

⭐ **Every representativeness target is window-stable**, moving far less than its gap to
the corpus. The 3.6× base-rate enrichment is not a window artifact. Non-Latin is
drifting up (Arabic 1.5% → 2.0%, `aawsat.com` 2,036 → 2,641), so a target quoted as a
fixed 7.26% is already stale.

⛔ **The one number that moved materially is the one the plan uses rhetorically.**
Harm-title rows above the op-point: **91 → 78 (−14%)**. The evidence doc reads
"91 rows above the op-point in 14 days (~6.5/day)". The honest statement is
**~5.6–6.5/day**, a range across two windows — not a constant. The ADR-023 argument is
unaffected; the figure is.

---

## 2. What the archive excludes (measured, not assumed)

On a single cycle file, n=2,991: `passed_prefilter` **True on 100%**,
`prefilter_reason` **null on 100%**, `nexusmind.disposition.status` **`kept` on 100%**.

So the archive excludes **every gate-blocked article** — those now live in the block
ledger (2026-08-24) and are recoverable, which they were not before. It also splits
`stage_used` 2,592 stage2 / 399 `stage1_low` (13.3%).

---

## 3. The drawable population — where the targets actually change

`production_census.py` counts **rows over 83 cycle files**. That is the right
instrument for comparing the corpus against what the scorer serves, and the wrong one
for sizing a draw, for two reasons the plan names but never quantified.

⚠️ **The first reason turned out to be false, and it was mine.** I expected an article
rescored across N cycles to contribute N rows. Measured: **206,221 scored rows →
206,220 distinct ids, 1 repeat (1.0000×)**. An article is scored once, not per cycle,
so dedup is a no-op here. Stage B ≡ Stage A.

The second reason holds and is large. `news.google.com` is 22.1% of rows and must be
excluded from any draw (sub-300-char headline echoes; never oracle-re-score them). The
plan says so and then quotes the un-excluded percentages as targets anyway:

| target | ALL rows (what the plan quotes) | DRAWABLE (GN excluded) | change |
|---|---|---|---|
| n | 206,221 | **160,641** | −22.1% |
| positive base rate (raw ≥ 4.5) | 7.81% | **9.76%** | **+25% rel.** |
| non-Latin script | 7.81% | **9.74%** | **+25% rel.** |
| median content length | 1,360 | **1,936** | **+42%** |
| p10 content length | 84 | **254** | **3×** |
| under the 300-char oracle floor | 30.84% | **11.21%** | **−64%** |
| class-A shape (harm in title) | 0.89% | **0.73%** | −18% |
| top-10 domain share | 36.8% | 19.7% | far less concentrated |
| English share | 60.8% | 51.5% | −9.3pp |

⭐⭐ **Four of the five Gate 0 targets are stated against a population a draw cannot
sample from, and each moves in a direction that changes the draw.**

- **Base rate.** The corpus is enriched **2.9×** over the drawable population
  (28.22% vs 9.76%), not 3.6×. The gap is real and smaller than recorded.
- **Non-Latin.** Target is **≥ 9.74%**, not ≥ 7.26% — a third higher.
- **Length.** The corpus is **1.37×** longer than drawable production (2,658 vs 1,936),
  not 2×.
- **The short-form regime is mostly Google News.** p10 goes 84 → **254 ch** and the
  share under the 300-char oracle floor collapses **30.84% → 11.21%**. "Production
  p10 = 84 ch, the short-form regime is under-trained" is largely a statement about
  headline echoes that are excluded by rule. What remains under the floor is 18,010
  articles — a real but much smaller regime.
- **Class-A.** Target is **0.73%**, not 0.87%.

---

## 4. The probe is an exclusion too — and it is nearly composition-neutral

Conditioning on `stage_used == 'stage2'` is correct for *reading the student's score*
and wrong for *sizing a draw*: it lets the v7 e5 probe decide which articles a v8
corpus may contain. That is the same shape as the keyword prefilter ruling 3 dropped —
a screen the corpus would silently inherit. The oracle relabels from scratch, so
`stage1_low` articles are perfectly drawable; only the score is unusable.

| | C. drawable (stage2 only) | D. full pool (+ `stage1_low`) | Δ |
|---|---|---|---|
| n | 160,641 | **179,111** | **+18,470 (+11.5%)** |
| distinct domains | 1,381 | **1,476** | **+95** |
| non-Latin script | 9.74% | 9.76% | +0.02pp |
| median content length | 1,936 | 1,900 | −36 ch |
| p10 content length | 254 | 235 | −19 ch |
| under the 300-char floor | 11.21% | 11.93% | +0.72pp |
| class-A (harm in title) | 0.73% | 0.70% | −0.03pp |
| English share | 51.5% | 51.5% | 0 |

⭐ **The probe's screening is composition-neutral on every axis Gate 0 measures**, but
it costs **11.5% of the pool and 95 domains**. So the draw should come from the full
pool, and the reason is *coverage*, not bias correction — worth stating, because the
opposite (a probe that shaped the corpus) was the live worry and it is refuted.

Total scored rows in the window: 232,845 → 232,842 distinct ids (3 repeats).

---

## 5. Gate 0 targets, restated against the drawable population

Corrections to `docs/HUMAN_THRIVING_V8_PLAN.md` § Phase 0. **Population: distinct
articles, `news.google.com` excluded, all stages — n = 179,111 over 2026-08-14 → 08-28.**

⚠️ **Three different quantities in this table round to ~9.7% — do not conflate them.**
The **base rate 9.76%** is measured on population **C** (drawable, stage2 only, n=160,641),
because only stage2 rows carry a Gemma score at all. The **non-Latin 9.76%** is population
**D** (full pool, n=179,111); C's non-Latin is 9.74%. Quote the population with the number.

| target | plan says | measured here | status |
|---|---|---|---|
| positive base rate | production 7.74%; corpus 3.6× enriched | **9.76%** (stage2-scored subset); enrichment **2.9×** | ⛔ **owner decision — "decide it, don't inherit it" still stands.** The 2.9× is the factor to record and correct for |
| non-Latin script | ≥ 7.26% | **≥ 9.76%** | corrected, and drifting up |
| class-A shape (harm in title) | ≥ 0.87%, TPs **and** FPs | **≥ 0.70%** | corrected; the TP/FP balance requirement is untouched |
| median content length | production 1,349, corpus 2× | **1,900**, corpus **1.37×** | corrected |
| short-form regime | "p10 = 84 ch, under-trained" | **p10 = 235 ch**; under-floor **11.93%** (21,374 articles) | ⚠️ **largely a Google News artifact** — smaller than recorded, still real |
| exclude `news.google.com` | required | 22.1% of rows, **−22.1% of the pool** | confirmed, and it is what moves every other target |

**What Gate 0 still needs, and none of it is measurement:**

1. The **base-rate decision** — the one number the plan explicitly reserves for the
   owner. Everything needed to make it is now on the table.
2. The **class-A supplement's TP/FP balance**, stated as a number. §1g's screen found
   most harm-lexicon hits above the op-point were *true* positives, and an FP-only
   supplement destroys the §5b no-regression set.
3. The corpus **staged on b650** with a `corpus_manifest.json` (#127) whose counts
   reconcile against a freshly prepared split — not a `json.dump` in the code.

⚠️ **The archive is a 14-day window and it rolls.** Anything older than `08-14` must
come from FluxusSource raw. A draw taken next week is a different population from this
one; the manifest must record the window, not just the counts.
