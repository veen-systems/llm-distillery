# Phase A step 1 — the dominant-subject rule (class A, #91)

**Status: DRAFT for Gate A. Not wired to anything.** Replaces **STEP 1: SCOPE CHECK**
(`filters/uplifting/v7/prompt-compressed.md` lines 13–58, up to `## STEP 2:` — re-locate by
heading, not line number). Companion to `PHASE_A_2b_evidence_level.md`.

---

## ⛔ Read this first: the rule is largely already written, and ignored

The plan calls step 1 *"the hard one to write without over-reaching"*. Reading v7's actual
STEP 1 against the 9 class-A records changes that framing. **v7's scope check already
contains categorical exclusions that cover 8 of the 9**, each of which orders *"score ALL
dimensions 0-2. Stop."*

⚠️ **This is my adjudication of 9 records against prompt text — not a measurement of what the
oracle did.** It is checkable by anyone re-reading the two documents, and it is falsifiable at
step A5. Mapping:

| raw | article | the v7 rule that already covers it |
|---|---|---|
| 6.846 | Five men arrested for raping a minor | *"Individual arrest/sentencing → NOISE (all dimensions 0-2)"* — **literal** |
| 6.766 | Celebrated at birth, pushed into sex work | *"Doom-framed content — >50% describes harm/crisis, even with silver lining"* |
| 6.087 | Rethink Business Centre Management | *"Professional knowledge sharing — … business advice, industry trends"* — **literal** |
| 5.976 | Woman 'tortured' over grabbed land | doom-framed |
| 5.748 | Children's helpline calls up 80% | doom-framed |
| 5.458 | Baby girl killed at nursery | doom-framed |
| 5.374 | Travelodge gave abuser room key | doom-framed |
| 5.260 | Assault/harassment/stalking top victim-line calls | doom-framed |
| 5.860 | Greyhounds to Australia as NZ racing ban begins | **none — a real gap**, see §3 |

**So class A has the same shape as §1h's gatekeeper finding: a rule that exists and is not
followed.** Writing a *better-worded* exclusion is therefore not obviously the fix, and step 1
should not be scoped as "add the missing rule". Two changes that follow:

1. **The `>50%` proportion test is the weak link and must go** (§1 below). It invites a
   proportion judgement — an article can be 40% harm and still be *about* harm — where a
   subject test admits no such arithmetic.
2. ⭐ **Step 2b's Question 1 appears to cap all nine on its own.** Every class-A row fails
   LIVE / DELIVERED / REACHED SOMEONE, and **2 of the 9** `why_adverse` fields already argue
   in exactly those words — *"not an outcome"* (victim line), *"no completed positive outcome
   for anyone"* (Sahiwal torture). *(Measured, not eyeballed: an earlier draft of this line
   said four.)* ⚠️ **The other seven are my adjudication, and I wrote the rule I am grading, so
   treat it as a prediction to test at A5, not a result.** If it holds, classes A and B are
   less independent than the plan's two-defect structure assumes. ⛔ **This does not touch
   §1f** — a prompt reaches only the labels, and 2 of 3 class-A rows are the *student*
   disagreeing with all three oracles. Phase B2 stays load-bearing either way.

**Every class-A row also has `evidence_level` 5.41–7.06 with the gatekeeper never firing**
(`gatekeeper_applied` false or absent on all nine) — the same instrument failure as §1h,
across the whole class.

---

## Replacement text

### STEP 1: SCOPE CHECK (Do This FIRST)

**Before scoring any dimension, answer one question: *does this article contain a process
that is going well for people, now?***

Everything in this step serves that question.

---

#### 1. What is the article ABOUT?

Name the article's **dominant subject** in one phrase — the thing the article would still be
about if you deleted its best sentence.

⛔ **The score follows the dominant subject, never the best fragment.** A story whose subject
is a crime, an abuse, a bereavement, a worsening statistic or an institutional failure **does
not become uplifting** because it contains an arrest, a vow, a proposal, a ban, a helpline, a
policy change or a hopeful closing line.

**If the dominant subject is a harm → score ALL dimensions 0-2. Stop.** Apply this before any
other test, and apply it even when the article is well-written, well-sourced, and important.
Important is not the same as uplifting.

⚠️ **Do NOT estimate what proportion of the text describes harm.** The old rule asked whether
harm was *"more than 50%"* of the article; that invites arithmetic on paragraphs and lets a
story that is plainly *about* a killing pass because two thirds of it quotes a campaigner.
**Ask what the article is about, not how much of it is grim.**

#### 2. Harm answered is not harm undone

The most common failure this rule exists to stop: an article about a harm contains **the
response to that harm**, and the response is read as a delivered good outcome.

**A response to harm is NOT an outcome for people.** Score 0-2:

- An **arrest**, charge, suspect named, investigation opened, raid, joint police operation.
- A **helpline, hotline, victim service or charity existing**, or its caseload growing. ⛔ A
  rising number of reports is a **measurement of harm**, not evidence of uplift — however
  well-sourced the number is.
- A **policy change, review, apology or pledge made after the fact**, especially as a
  trailing sentence.
- A **warning** that a practice is widespread, or a call for it to stop.

> **0-2:** *"Five men arrested for the repeated sexual exploitation of a 14-year-old girl.
> Police describe a joint operation."* The subject is the rape of a child. The arrest is the
> beginning of a process, not an outcome anyone has received. → all dimensions 0-2.
>
> **CONTRAST, scores normally:** *"A survivor met the man who attacked her, through a
> restorative-justice programme that has now run 200 such meetings."* Repair has been
> **delivered** to identifiable people. The harm is the setting; the process going well is
> the subject.

#### 3. Who receives the benefit?

The benefit must reach **people**. An outcome delivered to animals, to an institution, to a
market or to a jurisdiction's reputation is out of scope for this lens, however positive.

> **0-2:** *"Dozens of greyhounds will be flown to Australia as New Zealand's racing ban
> takes effect."* The ban sounds like the good news; the event is animals being exported to
> continue the banned activity, and no person's circumstances improve. → all dimensions 0-2.

⚠️ This is a **scope** statement, not a claim that animal welfare does not matter. It belongs
to another lens (ADR-015: lenses are perspectives, not partitions).

#### 4. ⛔ Do NOT suppress these

Each was flagged and adjudicated **not adverse**. A v8 that suppresses them has traded a
reader-facing defect for a worse one — defining a category of constructive journalism out of
the lens. **These score normally.**

- **Transitional justice** — truth commissions, mass-grave identification, war-crimes
  forensics, dictatorship-era accountability. Historical crime, **living** process.
- **Recovery narratives** — a harm-heavy opening does not make the recovery absent. If the
  article closes on a recovery that has occurred, it is in scope. **Rank is not membership**;
  an article being too high in a feed is not a reason to score it 0-2.
- **Delivered repair after harm** — convictions and sentences handed down, compensation and
  settlements paid, restitution and amnesty delivered, restorative-justice meetings held.
  ⭐ **The line is delivery, not subject matter**: an arrest is the process starting, a
  settlement paid is an outcome received.
- **Measured improvement in a harm** — murder rates falling, rescues completed, a disease
  receding. The subject here is the improvement, not the harm.
- **Legitimate lens overlap** — a genuine solutions story may also be a thriving story.

⚠️ **This list is load-bearing and is not theoretical.** The 2026-08-20 harm screen found that
**most harm-lexicon hits are true positives** — rescues, survivor recovery, falling murder
rates, convictions delivered. The false positives are rarer and more specific than "harm-
adjacent" implies. **A rule that suppresses harm vocabulary fails this filter.**

#### 5. Out of scope (score 0-2 on ALL dimensions)

*(v7's list, retained, with the two changes above folded in.)*

- **Speculation without outcomes** — "could lead to", "promises to", "aims to" with no results
- **Corporate optimization** — efficiency, productivity, market share without societal benefit
- **Technical achievement alone** — faster APIs, better code, new products without wellbeing impact
- **Professional knowledge sharing** — dev tutorials, business advice, industry trends
- **Business success** — funding, profits, growth, IPO without documented broad benefit
- **Individual wealth** — billionaire philanthropy announcements, luxury products
- **Military buildup** — weapons, defenses, security theater (exception: peace processes)
- **Harm as the dominant subject** — §1, replacing the old ">50% doom-framed" proportion test
- **The response to a harm, without delivered repair** — §2
- **Benefit that reaches no person** — §3

**DO NOT hallucinate uplift that isn't there.**

**ANTI-HALLUCINATION RULE:** Every evidence field MUST contain an EXACT QUOTE from the
article, or "No evidence in article." Do not paraphrase, infer, or fabricate evidence.

---

## Open question for the owner — the one boundary I could not settle

⚠️ **Where does delivered accountability sit?** Two sources in the plan pull opposite ways and
I am not going to resolve it by picking one:

- **§1e / ovr `BRAND.md` (`a70609b`)** narrows the lens to *a process going well for people*,
  **excluding harm-answered-only** items. Read strictly, a conviction is harm answered.
- **§1g** adjudicated *"convictions delivered"* as **true positives** in the 2026-08-20 harm
  screen, and the 2026-08-22 adjudication kept three restorative-justice rows (Brussels
  survivor/perpetrator meeting 6.55, $30M abuse settlement 5.85, Myanmar amnesty 5.38) as
  **not defect-teaching**, warning that an FP-only supplement *"would destroy §5b"*.

§4 above draws the line at **delivery** — arrest out, settlement/conviction/restitution in —
because it is the only reading consistent with both, and because it matches the LIVE /
DELIVERED / REACHED SOMEONE test in step 2b. ⚠️ **That is my reconciliation, not a ruling.**
If the owner intends *harm-answered-only* strictly, §2 and §4 both change and three §5b-class
rows become adverse.

## Verification, before this is believed

- **Step A5, k-run mean** (oracle run-to-run noise is 0.82 mean / 2.25 max — a single run is
  not a measurement). Score all 18 adverse records, the §5b no-regression set, and the
  research abstracts.
- **The prediction to test:** all 9 class-A rows land below 3.85, and — per §2 of the header —
  check how many are capped by step 2b's Question 1 **alone**, with step 1 disabled. If Q1
  carries them, step 1's categorical list is redundant belt-and-braces and should be trimmed
  rather than expanded.
- **The control that matters more:** all four §5b rows stay above the op-point, and the
  three restorative-justice rows above stay where they are. ⛔ A step-1 rule that passes the
  adverse set and fails this control is a **worse** filter, not a better one (ADR-023 cuts
  both ways here: the FP is the expensive error, but §5b's rows are the true positives whose
  loss is invisible).
- ⛔ **A prompt reaches only the labels.** Whatever this scores, §1f's student defect is
  untouched and Phase B2 hard negatives remain load-bearing.
