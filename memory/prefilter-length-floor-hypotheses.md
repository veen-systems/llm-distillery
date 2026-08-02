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
   n=60/group.** DiD **+0.44** [+0.01, +0.87], MAE ratio 0.88× (short is
   *better*). Clears rate short/long is flat at every bar: 90/88 @2.25,
   87/87 @3.0, 67/65 @4.0, 28/32 @5.0.
   **And it was not small-sample noise** — 20,000 n=15 bootstrap draws from the
   n=60 population give **P(DiD ≤ −1.24) = 0.0000**. Something systematically
   differed between the runs; see hypothesis 6.

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

5. **`solutions v6` carries the short-content defect LD#92 attributed to
   uplifting.** DiD **−1.13** [−1.74, −0.52], MAE ratio 1.51×, oracle clears
   53% (short) vs 85% (long). Failure mode is exactly as LD#92 described it —
   development/progress vocabulary in a headline with no subject: *"ABD Grants
   $250m Loan to Shield Cambodia's Vulnerable Households"* student 4.21 / oracle
   0.00. Makes sense: the solutions lens is *about* concrete interventions, so
   development-finance headlines are its maximally confusable case.
   Corrected exposure ~49 false positives per 8 cycles, not ~460.

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
   20 cycles), **19.9% for non-English vs 13.0% English** (z≈2.6, p≈0.01), 0% of
   high tier. `no_cultural_topic_signal` is 86% of the loss. Rate-agreement and
   safety-to-enforce are independent properties.

## Open questions

8. **Does a short-content cap actually help solutions?** ~49 FPs per 8 cycles is
   modest, and the same populations appear in solutions' short-and-clearing list
   (`gn_africa_gn_sudan`, `gn_asia_gn_afghanistan`, `gn_africa_gn_zimbabwe`) as in
   NM#231's under-served set. The cap must be weighed against that recall cost,
   not fitted to the FP count alone.

9. **Is `no_cultural_topic_signal`'s non-English coverage the cause of LD#86's
   language skew, or is it the corpus?** 1.5× is real but modest. Falsification:
   improve the multilingual keyword set, re-run the identical recall check, and
   see whether the non-English block rate converges on the English one.

10. **Is exposure predictive of defect? Evidence so far says no.**
    investment_risk has by far the largest short-content exposure (635 clearing
    op-point per 8 cycles, 20.3% of its sub-300 rows) and **no length effect at
    all** (DiD +0.26, CI spans zero). Worth keeping in mind before sizing work
    from volume.

11. **cultural_discovery shows a significant *positive* DiD (+0.79).** The
    student *under*-scores short content there. That is NM#231's direction, not
    LD#92's — possibly the same underlying mechanism seen from the other side.

## Method notes worth reusing

- **Difference-of-differences cancels oracle bias**, which is what makes DeepSeek
  usable as a judge for filters whose teacher was gemini. Read the short-vs-long
  *gap*, never the absolute agreement (FILTER_PLAYBOOK §0).
- **Bootstrap the original n before calling a replication failure "noise".** The
  P=0.0000 result is what turned "the first sample was unlucky" into "the two
  runs measured different things", which is a completely different bug.
- **Reconcile denominators before diffing two sources.** See
  [[reference-nexusmind-data-sources]] — the log and the file count different
  sets, and `data/raw/` is pre-enrichment.

## Related

- [[project_session_2026_08_02]] — the session
- [[reference-nexusmind-data-sources]] — the two denominator traps
- [[cross-repo-prioritization]] — Chain 4, re-rooted on the length-floor split
