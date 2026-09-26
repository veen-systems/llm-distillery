---
name: project_session_2026_08_22
description: Three owner-flagged Thriving false positives promoted, two prompt rules drafted, and H-CV1 refuted at the premise — the keyword prefilter NEVER RAN on the v7 corpus. The corpus argument survives, differently: four measured composition gaps. No spend, no model, nothing deployed.
metadata:
  type: project
---

# 2026-08-22/23 — the corpus was never filtered, and the owner was right anyway

**Zero oracle spend. No model trained. Nothing deployed** (nothing to deploy — no filter
package changed). Output: 2 adverse rows, 1 prompt rule, 1 evidence file, 4 reusable
scripts, llm-distillery#127, and one hypothesis refuted at its premise.

## The arc

The owner opened with three live false positives from the Thriving lens and two questions
about the prompt. Each answer narrowed differently from how the question was asked.

1. *"Shouldn't thriving be about today, not the past?"* — **yes for the process, no for the
   subject.** The Dawn op-ed fails a stronger test than recency: it describes **no process at
   all**. A rule keyed on *when events happened* would suppress transitional justice, which
   §5b protects and calls *"the purest correction for presentism"*.
2. *"Shouldn't it be about large groups, not individuals?"* — **no, as written.**
   `benefit_distribution` already carries breadth at weight 0.10, and **zeroing it entirely
   moves the TSA row only 6.901 → 6.280**, still tier high. The defect is that **no one has
   benefited yet**, not that the protagonist is one person. Beneficiary count, not
   protagonist count.
3. *"This is more a solution"* (Helsinki heat caverns) — **not a false positive.** Ruled by
   the owner as placement, not prompt: *"there are more misattributions, and that is not our
   biggest concern right now."*

Then: *"I am not convinced about #1"* — and that push was correct. See below.

## ⭐⭐ H-CV1 REFUTED at the premise: the prefilter never ran

Three arms, positive control on each, `diagnose()` fingerprint `938302d84050047a` identical
across A and B.

| arm | population | instrument | blocked |
|---|---|---|---|
| A | 235,905 production rows | today's prefilter | 6.917% |
| B | 6,590 corpus rows | today's prefilter | 9.074% |
| **C** | the same 6,590 | **March-2026 prefilter** (`991ffec`) | **15.493% — 1,021 rows** |

⭐ **Arm B alone was worthless and I nearly stopped there.** The corpus is dated 2026-03-11;
`prefilter.py` was created 2026-03-09 and changed **four times since**. Today's rules cannot
testify about March. Arm C is the one that settles it.

1,021 blocked rows are **in the training splits**, so the filter cannot have run.
Corroborated twice: `batch_scorer.py:1615`'s legacy `--prompt` mode marked *"NO PREFILTER
SUPPORT"*, and the March prefilter's 300-char floor against corpus rows of **35 characters**.

⛔ **The plan's Phase 0 premise was FALSE** and is rewritten.

## ⭐⭐ The owner's push was right, and my recommendation was wrong

I recommended *"don't rebuild the corpus to fix class A"*. The owner did not accept it:
*"I do not want a keyword prefilter anymore, and I want a proper data corpus to train on.
It is my belief that the corpus partly determines the quality of the result."*

**My error was conflating two quantities.** I measured crime-violence keywords **anywhere in
the body** (2.72% corpus vs 2.38% production, "not depleted"). Class A needs harm to be the
**dominant subject**. Matching on the **title** instead:

| | corpus (6,590) | production (205,939 stage2) | gap |
|---|---|---|---|
| harm as dominant subject | **0.46%** (30) | 0.87% (1,798) | 1.9× under |
| …teaching the FIX (< 3.85) | **25 rows** | 1,663 | — |
| **positive base rate (≥ 4.5)** | **28.22%** | **7.74%** | **3.6× enriched** |
| non-Latin script | 4.57% | 7.26% | 1.6× under |
| median length | 2,658 ch | 1,349 ch | 2× longer |

**25 rows are the entire training signal for class A.** Nothing removed them — they were
never assembled in. Refuting H-CV1 closed **removal**; it said nothing about **composition**,
and I presented the first as if it settled the second.

⚠️ **The 4 harm-title rows labelled ≥4.5 are NOT defect-teaching** — restorative justice
(Brussels survivor meets perpetrator 6.55, $30M abuse settlement 5.85, Myanmar amnesty 5.38).
**An FP-only supplement would destroy §5b.**

⭐ **Class B is NOT a corpus problem** — the corpus *under*-represents primary literature
(arxiv 4.23% vs production 7.92%). #125 is a prompt defect. The two classes have different
causes, which is why one prompt rewrite cannot be all of v8.

## ⭐ The cheapest large win, found while adjudicating

`evidence_level`'s own 0–2 band reads *"No uplifting outcome to verify, OR pure speculation"*
— a literal description of both new adverse rows. It scored them **6.21** and **6.44**, so
the single gatekeeper never fired. Had it fired, both land at **3.0** — under the op-point
*and* under the 3.85 bar. ⚠️ **The cap is the lever, not the value:** scoring Dawn's
`evidence_level` to 2 *without* the gatekeeper firing moves raw only 7.359 → 6.938.

## What I got wrong

1. ⛔ **"Don't rebuild the corpus."** Wrong, and the owner caught it. Body-match ≠
   dominant-subject; I generalised a narrow measurement into a planning recommendation.
2. ⛔ **"The worst class-A row normalizes to 8.284."** It is **9.862**. 8.284 was the max of
   §1g's *newly promoted subset*, read as the whole slice.
3. ⛔ **A badly chosen positive control** (an airstrike headline against a procurement-vocabulary
   pattern list) failed and briefly looked like a prefilter bug. The control was wrong, not
   the code.
4. ⚠️ **`timeout` on an ssh call kills the local ssh, not the remote process** — the first
   production run kept going and briefly double-loaded sadalsuud. Killed by explicit PID,
   never `pkill -f`.

## State

- `datasets/adverse/uplifting.jsonl`: **16 → 18** rows (9 class A, 9 class B).
- **Class B's score band is falsified**: two non-outcome rows at raw **7.359 / 6.901** sit
  above every class-A row. The A-over-B priority ruling stands on reader harm; its band
  argument does not.
- **`lens_fit` (ADR-037 Phase 3) has never run** — absent from ovr's deployed
  `data/chief_editor_config.json`, so it falls to `{enabled: false, audit_only: true}`.
  Nothing ever compared Thriving's 9.617 against Solutions' 8.074. That is #96, an ovr fix.
- Only **22 editorial rows** (18 adverse + 4 no-regression) are independent of the oracle.
  Everything else grades the student against its own teacher.

## Next session

Read `docs/HUMAN_THRIVING_V8_PLAN.md`, then the TODO top block. Start at **Phase A step 2b**
(the live-process rule) — free, and it fixes both new adverse rows via the existing
gatekeeper. Then Phase 0 against the four Gate 0 targets, with **#127**'s corpus manifest.

⚠️ **Still open and unexplained:** why the student fails on class A. Composition gaps are not
a mechanism. Every explanation offered so far has died under measurement, three of them mine.
