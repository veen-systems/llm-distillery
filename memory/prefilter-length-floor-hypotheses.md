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

5. **`solutions v6` has a real short-content defect — IDENTIFIED 2026-08-05.**
   The discriminating tests the 08-02 review asked for were run (both of them,
   plus a replication in the same oracle run; n=80/arm, 456 articles, 0 errors,
   0 junk skips). Predictions were pre-registered in the sampler before any
   oracle call.

   | design | arm depth ratio | DiD | cluster 95% CI | cluster p | + Holm |
   |---|---|---|---|---|---|
   | D1 both arms `raw >= 2.25` | 0.50 | −0.790 | [−1.29, −0.28] | 0.0032 | 0.0032 |
   | D2 both arms `raw >= 4.00` | 0.19 | −0.861 | [−1.34, −0.38] | 0.0006 | 0.0012 |
   | D3 top 2.3% **within** each arm | 1.00 | **−1.119** | [−1.61, −0.61] | <5e-5 | <1.5e-4 |

   ⚠️ The p-values are the **source-clustered bootstrap** p, Holm-corrected
   across the three designs. An earlier version of this table carried
   article-level *permutation* p (0.0022 / 0.0007 / <1e-5), which ignores
   clustering and is anticonservative. Both sets support the same conclusion,
   but quote the clustered ones. The scripts print the permutation p in a
   parenthesised column for continuity only.

   The artifact predicted D2 markedly more negative and **D3 → 0**. Observed:
   D2 moved −0.071 and **D3 is the largest**. At matched depth the oracle puts
   35.0% of the short arm below op-point vs 5.0% of the long arm, across 55
   distinct sources in 80 rows. Unchanged with the gatekeeper off (corroborates
   #94); survives dropping `smart_compress`-truncated long rows (D3 −1.024,
   p=0.0002). Residual: matched percentiles equalise selection *severity* but
   not *noise* (short-arm MAE ratio 1.91×), so some negative DiD is still
   expected in D3 — D2 is the independent check and it barely moved.
   **Second oracle confirms it.** `gemini-2.5-flash` on the same D3 sample
   (160/160, 0 errors) gives DiD **−1.351** [−1.73, −0.96] vs deepseek's −1.119.
   The two disagree per article (mean |diff| 1.18) and gemini is more generous
   on *both* arms (2.80/4.95 vs 2.40/4.31) — different absolute bias, same gap.
   That is the convergence DiD exists to produce, and it rules out "the judge
   penalises short input" as the explanation.
   ⚠️ **Still do not fit the cap VALUE**: that is a threshold fit and inherits
   #95's |Δ| ≤ 0.16 noise floor (Batch F.1 first). Identification is cleared;
   calibration is not.
   <!-- verify: PYTHONPATH=. python3 scripts/diagnostics/ld92_analyze_did.py --design tests/fixtures/ld92/design.json --scored tests/fixtures/ld92/deepseek_scored.jsonl | grep D3_pct2.3 -->

   **Harness AND data committed.** Scripts in `scripts/diagnostics/ld92_*.py`
   (`a10e084`; `ld92_crosscheck.py` came later in `c587b78`), fixtures in
   `tests/fixtures/ld92/` — the 456 deepseek rows, the 160 gemini rows and the
   design file, with article bodies stripped (only the word count is used, for
   the `smart_compress` flag) so no scraped text enters git. Every number in
   this hypothesis reproduces from those three files.

   The n=15 and n=60 originals committed **neither** script nor data, which is
   why this had to be rebuilt from the production pool up — the single most
   expensive part of the re-run, and the reason the fixture is here.

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

8. **Does a short-content cap actually help solutions? Still open — but it is now
   the only question left, and it is a *value* question, not an existence one.**
   Identification is settled (hypothesis 5). What is not settled is the number,
   and two things constrain it:
   - **#95 first.** The cap is a threshold fit and inherits the measured
     |Δ| ≤ 0.16 batch-composition noise floor. Batch F.1 (pin `batch_size`)
     precedes any value.
   - **Recall cost against NM#231/#292.** The same populations lead solutions'
     short-and-clearing list (`gn_africa_gn_sudan`, `gn_asia_gn_afghanistan`,
     `gn_africa_gn_zimbabwe`) as NM#231's under-served set, and two of the
     worst-gap D3 examples are real interventions the lens arguably *should*
     surface. Weigh against recall, never fit to the FP count alone.

   **A cheaper alternative appeared 2026-08-05 and should be priced first.**
   Google News is 14–17% of scored articles but **48–56% of all sub-300-char
   stubs** (~3× over-represented; measured within-period). Pre-enrichment already
   rescues ~62% of short content and fires below 500 chars, so the net is not too
   small — GN survives because its `url` is a `news.google.com/rss/articles/…`
   redirect, so the fetcher gets Google's redirect page, not the publisher's.
   **Retiring the GN proxies (FS#120, decision due ~2026-08-14) removes roughly
   half the population the cap exists to handle, at no recall cost to genuine
   articles.** Fix upstream before trading precision for recall downstream.
   <!-- verify: manual — FS#120 readout; check GN share of sub-300 rows after any retirement -->

12. **Does the same defect exist in the summariser, and is it the same
    mechanism?** Filed as ovr#299 on 2026-08-05. For English sources the share of
    summary content words absent from the article *and* its title runs 31.6% at
    1000+ chars → 73.9% at 120–299 → **83.4% under 120**, monotone. Mechanism is
    *not* the same as the scorer's: median summary length is 1159/968/875/1065
    against a 40× input range, i.e. a fixed output budget the model fills — with
    a full article it compresses, with a headline it generates. Open question for
    this file: **whether the scorer has an analogous fixed-budget behaviour**, or
    whether its short-content error is purely a vocabulary-without-subject
    effect. Worth testing because the fixes differ — one is a budget, the other a
    cap.

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
<!-- verify: test -f scripts/diagnostics/prefilter_gate_ab.py && echo PASS || echo FAIL -->

**The one intended exception: cultural_discovery v5.** Its custom `apply_filter`
never called `check_content_length` — a v3→v4 regression recorded in its own
module docstring and in TODO "Prefilter Quality". So cd was the only filter
whose *labelling* path had no floor, and hoisting the floor restores one there:
**190/474 = ~40% of what cd would have sent to the oracle** on the stress
corpus. Production-realistic share is lower (enriched corpora run ~35% sub-300,
not 66%) and **unmeasured**. Pinned by a test so it stays a decision, not an
accident. **Re-measure before the next cd oracle run (#87).**

**Synced to NexusMind 2026-08-03** (`c932065` content + `c1df13c` record; 950
NM tests pass). Syncing surfaced a second drift: `investment_risk v6` blocked
`arxiv` / `mastodon_` / `bluesky` in NexusMind since 2026-05-18 and never
upstream, so the oracle was labelling a population production never scores. A
blind LD→NM copy would have deleted all three; they were ported *back* to
llm-distillery instead (`e51309d`). **Diff the two copies before every sync —
`.nexusmind-owns` is empty, so nothing else compares them.**

**Still not done:** the NM#284 shadow re-run. Its pass rates will jump, and for
the first time describe lens behaviour rather than a length floor (LD#90 item
2). Nothing live changed — the per-filter prefilter does not execute in the
production scoring path (NM#284).

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
