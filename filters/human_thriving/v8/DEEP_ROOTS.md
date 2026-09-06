# The Deep Roots of Human Thriving

*The lens rationale for `human_thriving v8`. Written at Phase 9, 2026-09-06, as the
doc-standard item 5 (`memory/filter-doc-standard.md`). Everything here is traceable to the
shipped prompt (`prompt-v8-4.md`), to a recorded owner ruling, or to a measurement in
`docs/evidence/`; where a claim is retrospective rather than something that drove the design,
it says so.*

---

## Why ground this filter?

Because "uplifting" is a feeling, and a filter that scores a feeling scores the writing.

`uplifting v7` is a good filter with one structural problem: none of its six dimensions ask
whether **anyone actually received anything**. So an arrest reads as justice, a pledge reads as
durability, a funding round reads as wellbeing, a helpline reads as cohesion, and a
well-sourced article about a catastrophe reads as high-evidence. Each of those is a hopeful
*shape* wrapped around a harm, and each one reaches a reader who came looking for the opposite.

v8 exists to replace the feeling with a question that has an answer:

> **Does this article contain a process that is going well *for people*, *now*?**

Three words carry the whole lens. **Process** — not an intention, not a promise. **For people**
— not for an institution, a market, a jurisdiction, or an animal. **Now** — not scheduled, not
proposed, not funded.

## The one architectural decision

The question is asked **before** anything is scored, and its answer can veto everything else.

The oracle emits `dominant_subject` and `scope_verdict` as the first two keys of its JSON,
ahead of all six dimensions. Any verdict other than `in_scope` forces every dimension to 0–2 —
including dimensions whose own scoring ladder would otherwise reward the article.

This is not a stylistic preference about prompt structure. It is the answer to a specific
failure: a model that scores six dimensions and then decides is a model that has already talked
itself into the article. Deciding first, in writing, and being told not to revise a dimension
into disagreement with your own verdict, is what makes the scope judgement stick.

⚠️ **`in_scope` is not the default.** If the prompt cannot *name* a process going well for
people in `dominant_subject`, the verdict is not `in_scope`. Absence of a reason to exclude is
not a reason to include.

## The four ways an article fails the question

### 1. The subject, or the occasion, is a harm

Name the dominant subject — the thing the article would still be about if you deleted its best
sentence. Then name the **occasion**: the event that caused it to be published *today*, which
is what the headline and first two paragraphs report.

⛔ **Background does not displace the occasion, and length does not vote.** An article whose
occasion is an arrest is about the arrest, even when twelve of its fifteen paragraphs describe
a community campaign with real successes. That material is context an editor wrapped around the
news. A reader meets the article as its headline.

The rejected alternative is worth recording because it was v7's: *"is harm more than 50% of the
article?"* That invites arithmetic on paragraphs, and it lets a story plainly about a killing
pass because two thirds of it quotes a campaigner. **Ask what the article is about, not how much
of it is grim.**

⭐ **The guard matters as much as the rule.** An occasion can be good news set in a terrible
place. Remains identified at a former torture centre; a truth commission publishing; a
conviction handed down; compensation paid. Those occasions are things **completed and delivered
to people**, and the atrocity is the setting. Ask what the occasion *is*, not what it is
*about*.

### 2. Harm answered is not harm undone

The most common failure the lens exists to stop: an article about a harm contains **the response
to that harm**, and the response is read as a delivered good outcome.

An arrest is a process starting. A helpline existing — or its caseload growing — is a
**measurement of harm**, however well sourced the number. A policy change, review, apology or
pledge made after the fact is a response, however prominent, however funded, however clearly
caused by the events reported. A sentence handed down finishes the process and still leaves
nobody in the article better off.

Two owner rulings live here:

- **Money committed is not a protection established** *(2026-08-23)*. Funding secured,
  mobilised, pledged or allocated improves nobody's circumstances yet. A facility **operating**,
  a law **enacted**, a service **running** is a different thing.
- **A policy change that has not taken effect is an announcement** *(2026-09-03)*, whatever else
  is true of it. ⚠️ And commencement is not a way out: a response to harm that *has* taken
  effect is still a response to harm. What lifts an article out of this section is **repair that
  someone received**, never the bare fact that a measure has started.

### 3. The benefit must reach a person

An outcome delivered to animals, to an institution, to a market, or to a jurisdiction's
reputation is out of scope — however positive it is.

The canonical case, ruled 2026-09-03: *"US removes Syria from state sponsor of terrorism list."*
The article's own claim for the action is that it *"will help foster additional investment in
Syria to promote political and economic stability"* — the recipient is a jurisdiction and an
investment climate. The same applies to grey-list exits, delistings, sanctions moves and trade
normalisations.

⚠️ **This is a scope statement, not a claim that animal welfare or macroeconomic stability do
not matter.** They belong to other lenses. ADR-015: lenses are perspectives, not partitions,
and overlap between them is correct.

### 4. Nothing has taken effect yet

A proposal, a draft law, a bill not yet enacted, a plan, a scheduled discussion, a proposed
settlement, preparations for an event.

⭐ **Where this rule is written turned out to matter more than what it says.** Stated as a
**category in the exclusion list** it is safe. Stated as a **test inside the occasion check** it
destabilises a class-A row that the occasion check otherwise pins deterministically — measured
2026-09-03, seven-arm ablation, and a +996-character placebo of restatement left the row
unmoved, which rules out length and location. *A rule stated as a test becomes a question the
model asks of every article; the same rule as a category does not.*

## What the filter must NOT suppress

⚠️ **This list is load-bearing and it is not theoretical.** A v8 that suppressed these would
have traded a reader-facing defect for a worse one: defining a whole category of constructive
journalism out of the lens.

- **Transitional justice** — truth commissions, mass-grave identification, war-crimes forensics,
  dictatorship-era accountability. Historical crime, **living** process.
- **Recovery narratives** — a harm-heavy opening does not make the recovery absent. ⭐ **Rank is
  not membership**: an article sitting too high in a feed is not a reason to score it 0–2.
- **Repair that someone received** — compensation and settlements paid to survivors, restitution
  and amnesty delivered, restorative-justice meetings held, remains returned to families, a
  protection established that will improve people's lives.
- **Measured improvement in a harm** — murder rates falling, rescues completed, a disease
  receding. The subject is the improvement, not the harm.
- **Legitimate lens overlap** — a genuine solutions story may also be a thriving story.

The empirical backing: the 2026-08-20 harm screen found that **most harm-lexicon hits are true
positives** — rescues, survivor recovery, falling murder rates, convictions delivered. The false
positives are rarer and more specific than "harm-adjacent" implies. **Any rule that suppresses
harm vocabulary fails this filter.**

⭐ The unifying test across all of it: **who is better off?** Not the subject matter, and not how
far the process got. An arrest is the process starting; a sentence with no named beneficiary is
the harm answered; a settlement paid is something a person received.

## Where this sits in existing traditions

⚠️ **Retrospective placement, not derivation.** One tradition is named in the prompt itself and
therefore genuinely shaped the design. The rest is offered so a reader can locate the lens, and
it did not drive any ruling.

**Solutions journalism — in the design.** The prompt casts the oracle as a *Solutions Journalism
Analyst* and states the philosophy outright: *stories about responses to problems that show
evidence of results*. The insistence on documented outcomes over intent, and the explicit
exclusion of corporate success and speculation, come straight from that tradition — as does the
protection of constructive journalism in the do-not-suppress list.

**Constructive journalism** is the adjacent European strand and is the term the plan itself
uses. The relevant borrowing is negative: constructive journalism is not "positive news", and
neither is this lens. Tone is not evidence.

**The capabilities tradition** (Sen, Nussbaum) is where the phrase *going well for people* would
sit if it had a theory behind it: thriving as what people are actually able to do and be, rather
than as sentiment or as aggregate output. The lens's insistence that a benefit reach a **person**
rather than an institution, a market or a jurisdiction is the same instinct. It was not consulted
and no ruling rests on it.

**Deliberately not used: subjective wellbeing frameworks.** Anything measuring how an article
makes a reader *feel* — positive-affect scoring, PERMA-style flourishing inventories — is the
exact failure mode v8 was built to remove. `uplifting v7`'s residual defect is that it partly
scored register. Emotional tone is not in scope, at any weight.

## What the filter seeks

An article where you can point at a sentence and say: **this person, or these people, are
measurably better off, and here is what happened.**

The six dimensions then ask *how much* — how large the improvement (`human_wellbeing_impact`,
30%), whether it built bonds between people (`social_cohesion_impact`, 20%), whether rights were
expanded or accountability delivered (`justice_rights_impact`, 15%), how lasting it is
(`change_durability`, 15%), how well the **outcome** is verified (`evidence_level`, 10%, and
note: the outcome, not the journalism), and who actually receives the benefit
(`benefit_distribution`, 10%, and note: receives it, not hears about it).

Those last two are v7's hard-won correction, kept verbatim. In v6 they measured properties of
the *article* — how well-sourced it was, how many people it reached — and together they were 40%
of the weight, so any competent news story scored 6–8 on both. Reframed onto the **outcome**, a
well-sourced ECB rate story with Goldman Sachs quotes scores `evidence_level` 0, because there
is no thriving outcome to verify.

## What this is not

- **Not a positivity filter.** Tone is not evidence, and a hopeful closing line is not an
  outcome.
- **Not a harm-avoidance filter.** It surfaces convictions, rescues, truth commissions and
  falling murder rates. It excludes harm as a *subject*, not harm as *vocabulary*.
- **Not a good-intentions filter.** Announcements, pledges, funding, proposals and plans are
  excluded no matter how large or how welcome.
- **Not an importance filter.** *Important is not the same as uplifting* — the prompt says so
  in as many words, and applies it even to well-written, well-sourced, consequential articles.
- **Not a partition.** ADR-015: an article can belong here and to Solutions, or here and to
  Belonging, at the same time. Nothing is excluded for being adjacent to another lens.
- **Not high-recall, and this is deliberate.** ADR-023: a false positive reaches a reader, a
  false negative is invisible and the slot refills. At the operating point v8 surfaces about a
  third of what the oracle calls on-lens and is right about 70% of what it surfaces. **Read the
  specificity first.**

## Open questions of principle

1. **Is `social_cohesion_impact` at 20% right for a Thriving lens?** It is v7's weight, carried
   verbatim, and the null option is not an answer (Plan §9 Q4). A weight change needs no
   re-labelling (ADR-001).
2. **The Syria cluster under §3.** Nine above-op rows corpus-wide are one event: a delisting
   whose beneficiary is a jurisdiction. The rule handles it. Whether the *lens* should ever
   admit a jurisdiction-level good is an owner question, not a prompt question.
3. **Judicial relief granted to convicted offenders.** Ruled out of scope in principle
   (decision 2, 2026-09-03) and **not implemented** — clause D was dropped from the prompt
   because in combination with the commencement clause it broke the #91 origin row. Three corpus
   rows keep their labels and the decision stands unexecuted until a wording is found that does
   not license a positive.

## References

Prompt and lineage: `prompt-v8-4.md`, `PROMPTS.md`.
Rulings: `docs/decisions/2026-09-01-v8-oracle-ruling.md`,
`docs/decisions/2026-09-03-v8-scope-rulings.md`,
`docs/decisions/2026-09-03-v8-1-commencement-clause.md`,
`docs/decisions/2026-09-05-v8-op-point.md`.
Measurements: `docs/evidence/2026-09-03-v8-1-gate/` (ablation),
`docs/evidence/2026-09-03-classA-supplement-adjudication/`,
`docs/evidence/2026-09-04-v8-probe-calibration/`,
`docs/evidence/2026-09-06-v8-deploy-gate/`.
Plan and journal: `docs/HUMAN_THRIVING_V8_PLAN.md`, `docs/HUMAN_THRIVING_V8_JOURNAL.md`.
ADRs: 001 (dimensional regression), 008 (isotonic calibration), 011 (embedding screening),
012 as amended (the `uplifting` → `human_thriving` rename), 015 (lenses as perspectives),
018/019 as amended 2026-08-21 (no per-lens prefilter), 021 (ground-truth deploy gate),
023 (asymmetric loss).
