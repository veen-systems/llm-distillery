---
name: project_session_2026_08_11_evening
description: 2026-08-11 evening — #109 costed and gated, solutions v6's "dead dimension" refuted three ways, #94 confirmed on a second population, #106 re-scoped after ovr#311 superseded the withholding gate.
type: project
---

# Session 2026-08-11 (evening)

Opened as a decision session with nothing blocked on a machine. Ended the same
way — **four owner rulings open, none waiting on hardware.** No deploy, no
merge, no oracle spend. GPU time ≈ 4 minutes.

## What the owner asked for, and what came back

### 1. The #109 cost estimate (the thing I owed)

Posted to the issue. **Under $7 for both arms; arm A ~$1; arm B's oracle spend
can be $0.** Cost was never the constraint, which was the useful finding — the
real cost is build time, and the estimate named what exists (`gate_refused_label_
audit.py` for populations, `--llm gemini-flash`, the cross-oracle pattern in
`validate_deepseek_oracle.py`) against what does not (**no verification prompt
exists in this repo — every prompt is a scoring prompt — and there is no
automated panel harness**).

**Four gaps found, and one is serious.** #109 argues carefully that arm A must
use a different oracle than the one that made the labels, then **never names arm
B's judge**. The default anyone would reach for — Gemini Flash — is the model
that labelled `investment_risk v6`, so it would silently be a self-consistency
check. Fix: non-Gemini judges on b650 via Ollama, which is also why arm B can be
free. The other three: panel size unspecified; the planted-error gate has no pass
mark (drafted ≥56/80 with "cannot tell" counted as incorrect, p=0.00023, plus a
≥26/40 per-class anti-degeneracy floor); and a donor constraint (≥3.0 points
apart) so the control does not plant undetectable errors and fail for the wrong
reason.

**Data logistics worth remembering: the cd v5 and ir v6 splits are on b650, not
the workstation.** Local `datasets/training/` has only nature_recovery_v4,
solutions_v4, solutions_v6, uplifting_v7.

### 2. `solutions v6`'s "dead" `community_practice_strength`

Owner's framing was a binary: easy to find 20 misses = data gap; hard = the
dimension isn't real. **Neither.** Full record in
`memory/solutions-v6-dimension-hypotheses.md` and
`docs/evidence/2026-08-11-solutions-v6-community-practice-dimension.md`
(commit `3ea78a5`).

Short version: the labels are sound (n=397, mean 5.09, coherent exemplars); the
misses are hard to find (2, not 20, after screening all 1,953 on-topic zeros
twice); and **the student learns this dimension better than the other six** —
r=0.622 on positives, highest of the seven, and 4.0% false-fire, lowest. The 83%
is base rate. The one real defect is calibration compression (student 2.69 vs
oracle 4.63, 16 distinct output values, 13 of 41 pinned to 1.90), worth 0.194 on
4.0% of rows — barely above the #95 floor. **Fold into the next refit.**

Root cause of all of it: 41 positives in the test split. A **sourcing** question,
not a modelling one.

### 3. #94 — the concreteness gatekeeper, independently confirmed

Found incidentally. 8,451 of 10,297 training rows have concreteness < 3.0; **0**
exceed the 3.0 cap; max weighted average 2.600, **margin 0.400**. Second
population agreeing with the issue's 191,616 production articles. **The
inertness is empirical, not structural** — 2.99 concreteness could reach 8.60;
it does not, because low concreteness correlates with low everything. #84's
router rework could decouple that, which is the argument for keeping the guard
and *counting* clamped rows rather than deleting it.

## Cross-repo: the withholding gate was superseded before it was built

The ovr.news session shipped **ovr#311** (reject any summary longer than its
source) and measured the overlap with the `body/title < 2.0` rule we had
converged on: **39 of 39, and 25 of 25 Google News.** Structural, not lucky —
`getArticlesForBuild` inner-joins `summaries`, so an article that fails
summarization never enters the build. ovr#310 closed as superseded; the rule was
never built.

**Consequences here:**
- The withholding gate is **no longer a reader-safety item**. Any residual
  NexusMind ask is data hygiene, and weaker.
- **#106 re-scoped, not closed.** Blocking the output does not correct the input:
  `belonging` still gives normalized 7.26 / tier `high` to a 131-char GN headline,
  and that feeds cross-lens ranking and the normalization CDF. **"Close as no
  longer load-bearing" is explicitly on the table** under ADR-023, since the
  reader cost is gone. Owner ruling, two options, both stated on the issue.
- **#107's urgency driver is gone, the ruling is not.** It is a definition
  question that outlives its example, and it is the cheapest open item.

I gave them back the mechanism for their reopen trigger: NM#310 means a GN
redirect never resolves, so the body cannot grow and the ratio cannot invert —
**structurally unreachable for GN, not merely currently empty.** They restated
the trigger as non-GN only.

## The enrichment ruling is deliberately deferred

My caution on their argument — that the scoring/enrichment incoherence is bounded
to *under 500 chars AND NM did not enrich AND ovr did* — **re-scoped ovr#312**.
They are now instrumenting **outcomes, not attempts** (per article: attempted /
body-actually-changed / already-upstream-enriched) and wiring up
`enrichment_history` (0 rows ever, a writer with no callers).

**If that set comes back empty, the strongest argument for moving enrichment
upstream evaporates.** My bound is a **hypothesis and unverified**; #312 tests it.
**Wait for the number — do not re-litigate this from scratch.**

## What I got wrong

Three, all self-caught, all logged in the gotcha log:

1. **A +19.5pp effect erased by a downstream percentile CDF** — the near-miss of
   the session. Clean, reproducible, pointed at a real open issue (NM#319), and
   wrong, because the enrichment gate reads the *normalized* score. Caught by
   reading the caller instead of trusting the measurement. Added to the
   unreachable-mechanism catalogue as the **first entry caught pre-ship** and
   explicitly **not counted** in the occurrence total.
2. **A decomposition true by definition** — "40.0% tech + 43.1% governance =
   83.1%" where both categories were defined using `comm == 0`. The exactness was
   the tell.
3. **Reading a substantive signal off a 5-row smoke test.**

## Next session

`docs/TODO.md` top block is current. Four owner rulings, nothing blocked on a
machine: **#106** (two options), **#107** (cheapest), **#109** (needs a yes plus
judge model and panel size), and **should ovr.news enrich** (wait for ovr#312).

**Framework is current at v1.21.0.** v1.22.0 is an unreleased candidate branch in
another session's checkout — do not pin it.

⚠️ **CLAUDE.md is ~36.6k chars, over the 35k soft target and under the 40k
warning.** Table padding is not the cause (229 chars, no formatter) and the
footer is already trimmed to a pointer. Getting under target needs a structural
decision — an owner call, flagged not taken.
