# Phase A step 2b — the live-process rule (gatekeeper rewrite)

**Status: DRAFT for Gate A. Not wired to anything.** This is a drop-in replacement for
**section 4** of `filters/uplifting/v7/prompt-compressed.md` (lines 124–149, up to the `### 5.`
heading at line 150 — re-locate by heading, not by line number) plus the
`evidence_level` note on **Contrastive Example 5**. Phase A steps 1, 3, 4 are not written yet;
this file is step 2b alone.

⚠️ **This directory contains no `config.yaml` and no `model/`.** It is not a filter yet.
Deploying it as one makes a seventh filter and, weightless, stops the gpu-server scorer from
starting at all — plan §3a / §F3. Guard D of `scripts/deployment/preflight_deploy_guards.py`
aborts on exactly this; do not bypass it.

## Why this is the change, not a new dimension

Both owner-flagged rows of 2026-08-22 (Dawn 7.359 → normalized 9.988; TSA 6.901 → 9.856)
are literal instances of `evidence_level`'s **own** 0–2 band — *"No uplifting outcome to
verify, OR pure speculation"*. It scored them **6.21** and **6.44**, so `GATEKEEPER_MIN = 3.0`
never tripped. Had it fired, both land at **3.0** — under the 4.5 op-point *and* under the
3.85 adverse bar.

⚠️ **The cap is the lever, not the dimension value.** Scoring Dawn's `evidence_level` down to
2 *without* the gatekeeper firing moves raw only **7.359 → 6.938**. A 0.10-weight dimension
cannot move a 7.36 average. The job below is to make the gatekeeper **fire**, not to
re-weight (closed, §2) and not to add a dimension.

---

## Replacement text

### 4. **Outcome Verification** (JSON key: `evidence_level`) [Weight: 10%] **[GATEKEEPER: if < 3, max overall = 3.0]**

*Measures whether an outcome for people ACTUALLY OCCURRED, and only then how well it is
verified — NOT how well-documented the article is as journalism, and NOT how worthwhile the
subject sounds.*

**Answer two questions IN ORDER. Question 1 is a gate. You may not skip to Question 2.**

---

#### QUESTION 1 — Did an outcome for people actually occur?

An outcome for people has occurred **only when all three of these hold**:

- **(a) LIVE** — a named actor is doing something in the **present**. Not only in the past,
  not only somewhere else, not only in the recommended future.
- **(b) DELIVERED** — something has been **received or experienced**. Not only announced,
  appointed, funded, pledged, planned, launched or opened.
- **(c) REACHED SOMEONE** — there are identifiable **people whose circumstances differ**
  because of it.

**If ANY of (a), (b), (c) fails → `evidence_level` = 0.0–2.0. This is mandatory, and it is
not a judgement about article quality.** The gatekeeper will then cap the overall score at
3.0. **That is the intended result, not a malfunction.**

Only if **all three** hold, continue to Question 2.

---

#### The three shapes that fail Question 1

**Shape 1 — NO LIVE PROCESS.** An essay, op-ed, explainer, history or manifesto whose
concrete instances are past or elsewhere, and whose present-tense content is *prescriptive*.

> **0–2:** An op-ed on liberation psychology. The concrete programmes are 1970s–80s El
> Salvador, with examples from Colombia, Chile and Brazil — all decades old and elsewhere.
> Every sentence about the author's own country is a recommendation: *"should become part of
> schools"*, *"urgently needs"*. **Not one current, named, operating programme.** → `0.0`
>
> **CONTRAST, scores normally:** A university forensic team excavating a dictatorship-era
> torture site **this year**, returning identifications to families. The crime is from the
> 1970s; **the work is happening now**, by a named institution, and families are receiving
> answers. Passes (a), (b), (c). → score on how well those identifications are documented.

⛔ **The discriminator is the age of the ACTION, never the age of the SUBJECT MATTER.**
Write this as *"is the process live?"* — **never** as *"is the subject recent?"* A recency
rule keyed on when events happened suppresses **transitional justice**, which is the purest
correction for presentism and is explicitly protected (§5b).

**Shape 2 — NO OUTCOME YET.** An appointment, a launch, a funding round, a pledge, a plan, a
ribbon-cutting, a strategy, a target. Something has been *announced* or *staffed*, not
*delivered*.

> **0–2:** A doctor is named general manager of a new clinic. The article carries their
> degrees, an 18-year CV, two teaching awards, and a stated wish *"to build an accessible
> clinic"*. **No patient has been seen.** → `0.0`
>
> **CONTRAST, scores normally:** A heat-storage facility that **is heating 25,000 homes now**.
> The benefit is being received. Passes (a), (b), (c).

⚠️ The boundary here is **announcement vs outcome**. It is *not* "policy is adverse" —
policy items that report delivery score normally.

**Shape 3 — NO BENEFICIARY.** An award, an honour, a career profile, an obituary-adjacent
biography, or a ranking, where the subject is **a person's standing** rather than anyone's
changed circumstances.

> **0–2:** A distinguished scientist receives a lifetime achievement award. The article
> describes their career and their reputation. Nobody's circumstances changed. → `1.0`
>
> **CONTRAST, scores normally:** *"One nurse's clinic now serves 4,000 people."* A named
> individual, but the individual is the **vehicle** for a collective outcome, and 4,000
> people are receiving care.

⛔ **Count BENEFICIARIES, not protagonists.** A named individual is never by itself a reason
to score low. Do **not** read this as "large groups, not individuals" — beneficiary breadth
is `benefit_distribution`'s job, not this dimension's.

---

#### QUESTION 2 — How well verified is that outcome?

Only reachable when Question 1 passed. **Ask: "What outcome for people is documented, and how
strong is the evidence FOR THAT OUTCOME?"**

| Scale | Criteria | Evidence Focus |
| :--- | :--- | :--- |
| **0.0-2.0** | Question 1 failed — no outcome for people occurred — OR pure speculation ("could", "might", "aims to"). | No outcome exists, or future tense only. |
| **3.0-4.0** | Outcome occurred but evidence is limited. Early reports, self-reported claims. | Press releases, single-source reporting. |
| **5.0-6.0** | Outcome documented with some data. Numbers cited, sources mentioned. | Statistics provided, named sources, specific measurements. |
| **7.0-8.0** | Outcome well-documented with verifiable data. Studies cited, official records. | Peer-reviewed data, government statistics, multiple independent sources. |
| **9.0-10.0** | Outcome independently verified/replicated. Third-party audits, multiple studies. | Meta-analyses, independent verification, replicated results. |

**GATEKEEPER RULE:** If Outcome Verification < 3.0, cap overall score at 3.0. **An outcome
that has not happened is not uplift, however well the article is written.**

---

#### ⛔ Do NOT force these to 0–2

These look like the shapes above and are not. Suppressing them trades a reader-facing defect
for a worse one — defining a category of constructive journalism out of the lens.

1. **Transitional justice** — truth commissions, mass-grave identification, war-crimes
   forensics. Historical crime, **living** process. Judge the action's date, not the crime's.
2. **Recovery narratives** — a harm-heavy opening does not make the outcome absent. If the
   article closes on a recovery that **has occurred**, Question 1 passes. Rank is a separate
   concern from membership and is not this dimension's problem.
3. **Rigorous research that DOES report an outcome for people** — a trial that reduced
   mortality passes Question 1 and scores **high**. Only research reporting **no outcome for
   people** — a method, a model, a call for further study — goes to 0–2. ⭐ **This dimension
   must be able to score LOW on a rigorous paper**; that is the point, and v7 could not.
4. **Legitimate lens overlap** — a genuine solutions story may also be a thriving story
   (ADR-015). Overlap is designed behaviour, not a reason to zero this dimension.

---

### Amendment to Contrastive Example 5

Extend the existing note, which currently ends *"That is the bug v7 fixes."*:

> *v8 extends this in the other direction. Under v7 an op-ed recommending a therapeutic
> practice scored `evidence_level` **6.21**, and an article announcing a clinician's
> appointment scored **6.44** — both on vocabulary alone, with no outcome for anyone. Both
> are Question-1 failures and score 0–2 under v8, capping the article at 3.0. **v7 asked "is
> this well-sourced?"; v8 asks "did an outcome for people happen, and is it verified?"***

---

## Consistency requirements before this ships

- ⚠️ **The scale string lives in TWO places.** `scoring.dimensions.evidence_level.scale` in
  `config.yaml` carries its own copy of the band text. v8's config must carry the Question-1
  wording too, or the prompt and the config will disagree — the same two-copies-of-one-number
  failure as the op-point (`CLAUDE.md` Hard Constraints).
- ⚠️ **The gatekeeper NUMBER lives in THREE places, and `config.yaml` is NOT the runtime one**
  — verified by reading source 2026-08-23, same shape as the op-point Hard Constraint:
  1. `filters/uplifting/v7/base_scorer.py:52-54` — `GATEKEEPER_DIMENSION` / `GATEKEEPER_MIN`
     / `GATEKEEPER_CAP` class constants. **This is what scores**, consumed at
     `filters/common/filter_base_scorer.py:331-335`.
  2. `config.yaml` `scoring.gatekeepers.evidence_gatekeeper` (`dimension`/`threshold`/
     `max_score`/`reason`) — documentation.
  3. `config.yaml` `scoring.dimensions.evidence_level.{gatekeeper,gatekeeper_threshold,
     gatekeeper_max_score}` — a **second** documentation copy of the same number.

  v8 must carry all three forward unchanged and in agreement. This step changes **when the
  gatekeeper fires**, not its wiring — but a v8 package that copies only the config half
  ships a gatekeeper that does nothing.
- ⭐ **There is already an instrument for "did it fire": `result["gatekeeper_applied"]`**, set
  at `filter_base_scorer.py:334`. Step A5's acceptance test should assert on that flag, not on
  the final score alone — a row can land under the op-point for unrelated reasons and look
  like a pass. ⚠️ **Confirm the flag survives to the persisted row before relying on it** — a
  stamp can be computed on every row and lost before persistence
  (`memory/stamp-contract-integrity.md`); check a delivered row, do not infer it from this
  line of code.
- **Verify by execution, not by reading.** Per plan step A5, run the ~30-article calibration
  sample — all 18 adverse records, the §5b no-regression set, and hand-picked research
  abstracts — and confirm: Dawn and TSA reach 3.0 **with `gatekeeper_applied: true`**, and all
  four §5b rows stay above the op-point **with it false**. ⛔ A prompt that reads correctly is
  not evidence the oracle follows it.
- ⚠️ **Oracle run-to-run noise is 0.82 mean / 2.25 max** (n=7), 5× the #95 band. A single-run
  oracle score on the calibration sample **is not a measurement** — take a k-run mean.

## What this step does NOT fix

⚠️ **Class A is untouched by this rule.** Neither flagged row contains a harm subject, and
the dominant-subject rule (step 1) is a separate piece of writing. Step 2b is a class-B-shape
fix that happens to be the cheapest large win — it is **not** the priority-1 work.

⚠️ **A prompt reaches only the labels.** §1f measured 2 of 3 class-A rows as the **student**
disagreeing with all three oracles. No prompt reaches those; Phase B2 hard negatives stays
load-bearing.
