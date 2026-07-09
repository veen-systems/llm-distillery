---
status: Accepted
date: 2026-07-09
deciders: [Jeroen Veen, distillery agent]
superseded_by:
---

# ADR-021: Deploy Gate Judges Against Held-Out Oracle Ground Truth, Not the Prior Model

## Context

A distilled filter needs a deploy gate: an automated check that decides whether a
newly trained student is safe to replace the incumbent. nature_recovery v4's first gate
(`scripts/gate/agreement_gate.py`, NM#229) framed this as **agreement with the previous
student (v2)**: its headline metric, `over_demotion`, counted "articles v2 surfaced but
v4 did not," and its reference cohort was drawn from `nr_v4_sourceA_reference.jsonl`.

That gate reported FAIL and nearly triggered two wasted responses (retraining, an
oracle switch). Reproduction showed the FAIL was an artifact:

- The Source-A cohort carried a `_v2_split` field — it was **v2-era Gemini labels**,
  systematically **+1.775 higher** than the DeepSeek labels v4 was trained on (mean WA
  6.40 vs 4.63; only 13/144 matched within 0.3).
- v4 was deliberately trained on a *more conservative* oracle (DeepSeek, chosen for
  editorial bias — see ADR-010, feedback-oracle-bias-vs-noise). Judging it against a
  *generous* Gemini baseline meant v4's **correct** demotions of Gemini-inflated content
  (promo profiles, how-to listicles) counted as failures. 9 of 12 flagged
  "over-demotions" were v4 agreeing with its own oracle.

The forces: a gate must (a) reflect the *intended editorial line*, not a superseded one,
and (b) survive an intentional change of oracle or scope between versions, which is
exactly when "agree with the previous model" breaks.

## Options Considered

### Option A: Agreement with the previous deployed model (agreement_gate.py)

| Pros | Cons |
|------|------|
| No fresh labels needed | Treats the prior model as ground truth |
| Cheap (reuse prior scores) | Structurally penalizes an intentional oracle/scope change |
| | Broke silently when the reference cohort's oracle differed from the candidate's |

### Option B: Judge each candidate against held-out ORACLE ground truth

| Pros | Cons |
|------|------|
| Measures "does it match the intended editorial line" | Needs held-out oracle-labeled data (we already have the test split) |
| Survives oracle/scope changes between versions | "Home advantage" if candidate and reference share an oracle — mitigated by comparing candidate vs incumbent on the *same* ground truth |
| Compares candidate and incumbent on equal footing | |

## Decision

**We chose Option B.** A deploy gate evaluates each model (candidate and incumbent)
against **held-out labels from the oracle the filter is meant to emulate** — the chosen
editorial line — at the surfacing threshold: recall, precision, specificity, F1, and
rank agreement (Spearman). A candidate deploys if it does not regress the incumbent on
these metrics. Implemented in `scripts/gate/ground_truth_gate.py` (pure functions
unit-tested); `agreement_gate.py` is Deprecated.

nature_recovery v4 result (vs held-out DeepSeek labels, operating point 3.75): v4
precision 0.85 / recall 0.67 / Spearman 0.82 vs v2 0.61 / 0.60 / 0.80 — v4 dominates,
where the old gate reported FAIL.

## Consequences

### Positive
- The gate reflects the editorial target, not a legacy model; an intentional oracle
  change (ADR-010, per-filter oracle selection) no longer reads as a regression.
- Candidate-vs-incumbent on identical ground truth is a fair, interpretable verdict.

### Negative
- Requires held-out oracle-labeled data (we hold out the test split for exactly this).

### Risks
- **Home advantage**: a candidate trained on oracle X, judged against X-labels, has an
  edge over an incumbent trained on oracle Y. Mitigate by reading it as "which model
  better matches the *chosen* line" (X is chosen deliberately) and by watching precision
  — a generous incumbent shows low precision against the stricter line regardless.
- The held-out cohort must be labeled by the *candidate's* oracle. Never reuse a prior
  version's cohort without checking its oracle (the exact trap this ADR closes).

## Revisit If

- The editorial target oracle changes such that neither the incumbent nor a fresh
  held-out set reflects it (re-label the gate cohort first).
- A production-representative negative set becomes available — fold real-firehose
  precision into the gate (the enriched test split understates firehose FP cost; see #71).

## Related Decisions

- [ADR-010](010-oracle-consistency-over-data-volume.md) — oracle choice sets the target the gate measures against
- [ADR-017](017-inter-oracle-mae-as-distillation-floor.md) — inter-oracle disagreement; this ADR is why "agree with a differently-oracled model" fails
- [ADR-008](008-isotonic-score-calibration.md) / [ADR-014](014-cross-filter-percentile-normalization.md) — scores fed to the gate are calibrated; surfacing compared at the tuned operating point

## References

- `scripts/gate/ground_truth_gate.py`, `tests/unit/test_ground_truth_gate.py`
- `scripts/gate/agreement_gate.py` (Deprecated banner)
- `memory/feedback-oracle-bias-vs-noise.md`, augmented-engineering#25
