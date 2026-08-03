---
name: prefilter-length-floor-hypotheses
description: Hypotheses from the NM#284/#285 prefilter measurement and the LD#92 short-content oracle test — what the per-filter prefilters actually do, and what enforcing them would cost
metadata:
  type: project
---

# Per-Filter Prefilters & the Short-Content Floor — Hypotheses

**Date:** 2026-08-02

Context: NexusMind#284 found the per-filter prefilters have never run in
production. Everything below is about the two questions that follow — *what
would they do if they ran*, and *is the student unreliable on the short content
the length floor blocks*.

## Refuted

1. **"The 0.638–0.649 four-filter cluster is a truncation artifact" (NM#285) —
   REFUTED.** Same-row full-vs-truncated replay, 4 cycles, n=8,283: the effect
   is +0.0000 (nature_recovery, solutions), +0.0005 (cultural_discovery),
   +0.0008 (belonging), +0.0028 (uplifting), +0.0097 (investment_risk). The
   *mechanism* claim was right — url/source rules genuinely cannot fire in-path —
   but it is worth tens of articles, not the hundreds needed to move a rate by
   0.05. The cluster survives the full contract unchanged.
   <!-- verify: rerun the same-row A/B; nature_recovery and solutions must still return 0.0000 -->

2. **"uplifting v7 over-scores sub-300-char stubs" (LD#92 at n=15) — REFUTED at
   n=60/group.** DiD **+0.44**, but **not significant**: exact permutation
   p = 0.054, and under Holm across the six filters tested it does not survive
   (only solutions and cultural_discovery do). Read it as **"no detectable
   length effect"**, not as the student under-scoring stubs. MAE ratio 0.88×.
   Clears rate short/long is flat at every bar: 90/88 @2.25, 87/87 @3.0,
   67/65 @4.0, 28/32 @5.0 — that flatness is the robust part.
   ⚠️ **The "P(DiD ≤ −1.24) = 0.0000" claim is WITHDRAWN** (2026-08-02 review):
   it sampled *without* replacement (finite-population correction deflates sd by
   √(1−15/60)), and 20k draws cannot resolve a true 8.0e-5. It also asked the
   wrong question — resampling the 40-cycle window says nothing about an n=15
   draw from a different 8-cycle window. See hypothesis 6 for what does hold.

3. **"Promote `content_too_short` to one global pre-fan-out gate" (08-01) —
   still refuted, but for a different reason than recorded.** The 08-01 argument
   was "it drops ~half genuine content". At n=60 the real reason is stronger and
   simpler: short content that clears an op-point is **as likely to be genuine as
   long content** (uplifting 67% vs 65% oracle-validated). A length gate would
   discard ~78 genuine surfacing uplifting articles per 8 cycles to remove ~39
   bad ones.

## Confirmed

4. **`nature_recovery v4` and `solutions v6` prefilters are pure length floors.**
   Both declare `EXCLUSION_PATTERNS = {}` deliberately (commerce upstream,
   ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides — a no-op with
   nothing to override. Across 8,283 articles the only block reason either emits
   is `content_too_short` (2,950); zero lens blocks. They are byte-identical
   because they are the same filter. Their declared `expected_pass_rate` (0.85 /
   0.20) described gates that do not exist; both deleted 2026-08-02.

5. **`solutions v6` shows the short-content defect LD#92 attributed to
   uplifting — but it is NOT IDENTIFIED.** DiD **−1.13** [−1.74, −0.52], MAE
   ratio 1.51×, oracle clears 53% (short) vs 85% (long).
   ⚠️ **Do not fit a cap on this.** The design selects on the student's own
   score at each filter's op-point, and the two arms sit at very different
   depths of their own distributions (solutions: 2.3% of short vs 4.6% of long
   clear it). Simulation shows that artifact is negative in every filter, and
   under *differential* noise — which the 1.51× MAE ratio itself suggests — it
   reaches −0.82 to −1.61, i.e. it can fully reproduce this headline.
   Controlling for `student_raw` within the sample does nothing (−1.13 →
   −1.13): selection already flattened it inside the band. Discriminating test:
   re-draw from matched *percentile* bands, or re-run at a second op-point — an
   artifact moves with the threshold, a real effect does not.

   What is *not* in doubt is the failure mode, which is exactly as LD#92
   described it — development/progress vocabulary in a headline with no subject:
   *"ABD Grants $250m Loan to Shield Cambodia's Vulnerable Households"* student
   4.21 / oracle 0.00. That the solutions lens is *about* concrete interventions
   makes development-finance headlines its maximally confusable case, which is a
   mechanism a selection artifact does not supply. Corrected exposure ~49 false
   positives per 8 cycles (**36–62** at n=60), not ~460.

6. **The oracle-test design is sound; the 08-01 execution mixed up a filter
   parameter.** LD#92 states uplifting's tier threshold as **2.25**, which is
   *solutions'* op-point — uplifting's is **4.0** (verified in production: tier
   `low` tops at raw 3.999, `medium` starts at 4.003). The "924 / 15.0%" scale
   figure reproduces exactly at a 2.25 bar (910 / 14.8%) and collapses to
   **117 / 1.9%** at 4.0. Difference-of-differences itself held up fine at 4×
   the sample.

7. **A matching pass rate says nothing about recall (LD#86).** cultural_discovery
   v5's observed 0.2605 matches its declared 0.25 — the one MATCH on the board —
   and enforcing it anyway costs **15.5% of surfacing articles** (135/871 over
   20 cycles), 0% of high tier. Rate-agreement and safety-to-enforce are
   independent properties.
   ⚠️ **"Skewed non-English" was the wrong framing** (corrected 2026-08-02).
   German 4.9% and French 5.3% are blocked at *less than half* the English rate
   (13.0%); pooling ten languages into "non-English 19.9%" describes no real
   population, and with source clustering z is 2.3 not 2.6. The sharper, true
   finding: **the entire gap is `no_cultural_topic_signal`** (9.9% en vs 19.2%
   non-en) while `celebrity_art`, `political_conflict` and `tourism_fluff` all
   fire *more* on English. It is uneven multilingual keyword coverage in
   `TOPIC_GATE_PATTERNS`, not a demographic bias — and that is fixable and
   falsifiable (extend the keywords, re-run, check the rates converge).

## Open questions

8. **Does a short-content cap actually help solutions?** ~49 FPs per 8 cycles is
   modest, and the same populations appear in solutions' short-and-clearing list
   (`gn_africa_gn_sudan`, `gn_asia_gn_afghanistan`, `gn_africa_gn_zimbabwe`) as in
   NM#231's under-served set. The cap must be weighed against that recall cost,
   not fitted to the FP count alone.

9. **Does extending `TOPIC_GATE_PATTERNS` close LD#86's per-language spread?**
   Now a sharp question rather than a demographic one: the gap is entirely
   `no_cultural_topic_signal`, and German (4.9%) and French (5.3%) already sit
   *below* English (13.0%) while Italian (28.6%) and Korean (37.5%) sit well
   above — consistent with keyword coverage, not with language per se.
   Falsification: extend the keyword set for the poorly-covered languages, re-run
   `scripts/measure_prefilter_recall_cost.py`, and check whether the per-language
   rates converge. If they do, the residual 15.5% is genuine editorial blocking
   and enforcement can be re-argued on its merits.

10. **Is exposure predictive of defect? Evidence so far says no.**
    investment_risk has by far the largest short-content exposure (635 clearing
    op-point per 8 cycles, 20.3% of its sub-300 rows) and **no length effect at
    all** (DiD +0.26, CI spans zero). Worth keeping in mind before sizing work
    from volume.

11. **cultural_discovery shows a significant *positive* DiD (+0.79).** The
    student *under*-scores short content there. That is NM#231's direction, not
    LD#92's — possibly the same underlying mechanism seen from the other side.

## What shipped (2026-08-03, #93 — llm-distillery side)

The floor is split three ways, per ADR-022 "stamp always, decide once":

- **Labelling:** `ground_truth.batch_scorer.make_oracle_prefilter()` composes
  `check_content_length` + `apply_filter`. The framework-leakage rationale is a
  property of the oracle prompt, so the floor lives on the path that has one.
- **Scoring:** no `apply_filter` checks length (base + the three filters that
  did it inline: uplifting v7, belonging v1, investment_risk v6). Every scoring
  result carries `content_length`; `HybridScorer`'s Stage-1 branch stamps too.
- **Enforcement:** one `short_content.cap` per filter in `config.yaml`, read by
  `FilterBaseScorer._apply_short_content_cap`. **Off on every filter** — the
  only candidate defect (solutions, hypothesis 5) is still confounded.

**A/B verification, n=2,917** (`data/raw` — pre-enrichment, so a short-skewed
*stress* corpus at 65.8% sub-300; not a rate estimate). Oracle-gate verdicts at
HEAD vs after the split: **byte-identical for five of six filters**. The
composition is order-preserving because every rule ANDs into the verdict, so
only the *reason* string can move, not the boolean.
<!-- verify: rerun scratch ab_gate.py against a fresh content_items file; diffs must stay 0 for all but cd -->

**The one intended exception: cultural_discovery v5.** Its custom `apply_filter`
never called `check_content_length` — a v3→v4 regression recorded in its own
module docstring and in TODO "Prefilter Quality". So cd was the only filter
whose *labelling* path had no floor, and hoisting the floor restores one there:
**190/474 = ~40% of what cd would have sent to the oracle** on the stress
corpus. Production-realistic share is lower (enriched corpora run ~35% sub-300,
not 66%) and **unmeasured**. Pinned by a test so it stays a decision, not an
accident. **Re-measure before the next cd oracle run (#87).**

**Not done:** the NexusMind sync (its `filters/` copy still has the old base),
and therefore the NM#284 shadow re-run that would finally read as lens
behaviour. Nothing live changed — the per-filter prefilter does not execute in
production (NM#284).

## Method notes worth reusing

- **Difference-of-differences cancels oracle bias**, which is what makes DeepSeek
  usable as a judge for filters whose teacher was gemini. Read the short-vs-long
  *gap*, never the absolute agreement (FILTER_PLAYBOOK §0).
- **Bootstrap the original n before calling a replication failure "noise" — but
  get the resampling right.** The instinct was correct and the conclusion held;
  the execution did not. Sample **with** replacement (without-replacement
  subsampling silently applies a finite-population correction), check the draw
  count can resolve the probability you are claiming, and remember that
  resampling window B cannot answer a question about window A. The filter
  mix-up conclusion survived on three independent lines of evidence, none of
  which was the bootstrap.
- **Selection on the dependent variable is the standing hazard in this whole
  design.** Matching two groups on the *student's own score* is not matching
  when the two arms sit at different depths of their own distributions. Prefer
  matched percentile bands, and always re-run at a second threshold: an
  artifact moves with the threshold, a real effect does not.
- **Reconcile denominators before diffing two sources.** See
  [[reference-nexusmind-data-sources]] — the log and the file count different
  sets, and `data/raw/` is pre-enrichment.

## Related

- [[project_session_2026_08_02]] — the session
- [[reference-nexusmind-data-sources]] — the two denominator traps
- [[cross-repo-prioritization]] — Chain 4, re-rooted on the length-floor split
