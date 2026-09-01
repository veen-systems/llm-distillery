# B5, the reading half — **all 18 adverse rows read in full. No label reversed.**

**2026-09-01. $0** — reading, no calls. Started while Phase B pass 1 ran.

**All nine class-A rows read at full length.** ⛔ Nothing here changes a label — these are
editorial judgements belonging to the owner; this reports what the full text shows.

## ✅ Headline: 9 of 9 labels hold. Zero reversals.

⚠️ **That is not the outcome the rule predicts, and the difference is worth naming.** The
standing rule is *"three of five drafts reversed on a full read"*
(`datasets/adverse/2026-08-09-reader-flags.md`) — but those were **drafts**, adjudicated before
the owner confirmed them. These are **confirmed** labels, and confirmation is what the rule's
sample lacked. ⛔ So this run is **not** evidence the excerpt risk was overstated; it is evidence
that adjudication catches what excerpting misses. Five of these nine were nonetheless confirmed
on 300-character excerpts, and one row's own `why_adverse` records the owner going back to the
full text and finding the case *"stronger than my first draft, not weaker"*.

The rest of this note is the two rows that decide something — the row **both oracles fail**
(criterion 1's blocker) and the row **Gemini alone fails** (the #91 origin article) — plus what
the other seven show.

---

## 1. The nursery row — ⛔ **I was wrong that this is not a prompt defect**

`british_irish_guardian_world_94f1e7bd4be4`, *"Parents of baby girl killed at nursery fear unsafe
sleeping 'rife' in sector across England"*, 5,457 chars.

I reported this as *"#135's step function, not a prompt defect… no amount of prompt-writing
reaches it"*. **Reading the article shows the prompt names its exact shape twice.** §2 of
`prompt-candidate-tail.md`, *"Harm answered is not harm undone"*, scores 0–2 for:

> - A **policy change, review, apology or pledge made after the fact**, especially as a trailing sentence.
> - A **warning** that a practice is widespread, or a call for it to stop.

The article is **both**: a September ban on infants sleeping anywhere but a cot, Ofsted tripling
unannounced inspections on £8m of new funding — *"as a result of Genevieve's parents'
campaign"* — and a mother saying unsafe practice may be *"rife"* across England. So
`response_to_harm` is the verdict §2 prescribes, and DeepSeek returned exactly that on **1 of 3**
runs (0.90); the other two returned `in_scope` at 6.10 and 6.20.

⭐ **The leak is the qualifier.** *"…especially as a trailing sentence"* was written for a
throwaway mention. Here the policy change is roughly a third of the body, funded, causally
attributed and with a commencement date — so a reader applying §2 in good faith can conclude
this is not what the clause means. **The gate is not flipping at random; it is flipping on a
qualifier that invites an exception this article satisfies.**

⛔ **Do NOT change the prompt now.** Phase B is mid-flight against `prompt_hash 003cd35a5122`;
editing it would invalidate the corpus. This is a **v8.1 finding**, and it is cheap to test after
the run: strike or bound the qualifier — *"however much of the article it occupies, however well
funded, and whether or not it has commenced"* — and re-score this one row k=3 under both
wordings. ~6 calls.

⚠️ **And the fix is not obviously right either.** #107 narrows Thriving to *"a process going well
**for people**"* and excludes harm-answered-only — which is why the editorial label is `adverse`.
But a bereaved family securing a funded national regulation **is** a process going well for
people by most readings. The clause boundary and the #107 boundary are being asked to do the
same work in two places. That is an owner question, not a wording bug.

## 2. The origin row — ⛔ **and "one oracle is stably right, the other stably wrong" overstated it**

`south_asian_the_hindu_20067a4398fa`, *"Celebrated at birth, pushed into sex work"*, 14,546 chars
— the article that led the ovr.news homepage and caused v8 to exist (#91). DeepSeek **0.900**
(`harm_is_subject` 3/3), Gemini **7.158** (`in_scope` 3/3).

Read in full it is genuinely two-sided, and Gemini's reading is **defensible on the text**:

- It **opens** on Savitri, a former sex worker who left the profession so her daughters would
  not enter it. One daughter now works with an NGO and is preparing for the police exam; the
  other is preparing for medical entrance tests. Named, delivered outcomes for identifiable
  people.
- It **closes** on a youth committee in Sagargram that *"were able to stop sex work and liquor
  inside their village"* within a year, and on Saniya persuading a friend's parents to let her
  keep studying.
- The **mass** of the article is the practice itself: ~10,000 women, families acting as pimps,
  girls raised into it from puberty.

So STEP 1's own test — *what the article is about if you delete its best sentence* — resolves to
the practice, which is the editorial call. But the best *paragraphs*, not merely a sentence, are
the escapes, and an oracle that weights them is not malfunctioning.

⭐ **The honest statement is narrower than the one I made:** DeepSeek **reproduces the owner's
adjudication** on this row; Gemini reproduces a defensible reading of the text that the owner
ruled against. That is still the right basis for choosing an oracle — the job is to reproduce
the editorial standard, not to be independently reasonable — but *"stably right"* vs *"stably
wrong"* claimed more than the article supports.

⚠️ It also means the 8/9-vs-7/9 margin is **softer than a bare score line looks**. One of the two
rows separating the oracles is a two-sided article. Nothing here changes the ruling; it changes
how confidently the margin should be quoted.

---

## 3. The other seven — and two of them bracket the §2 boundary exactly

| row | full-text reading | verdict |
|---|---|---|
| *"Five men arrested in Mashonaland Central for raping a minor"* | the **close** carries real delivered outcomes — child marriages, teenage pregnancies and new HIV infections *"significantly going down"* under a community campaign. The dominant subject is still the rape and the arrests, which §2 names outright | ✅ holds; the trailing positive is the fragment-over-subject trap |
| *"Woman 'tortured' for taking possession of grabbed land"* | she **did** recover land illegally occupied for 30 years — a delivered outcome — and was tortured for it. Her own `why_adverse` puts it best: *"even the one good fragment is undone inside the article"* | ✅ holds |
| *"Children's helpline… calls about child domestic abuse risen 80%"* | §2 names this shape verbatim: *"a helpline… its caseload growing. ⛔ A rising number of reports is a measurement of harm"* | ✅ holds |
| *"Domestic violence victim… Travelodge staff gave abuser room key"* | ⭐ **the case §2's qualifier was written for** — the policy change genuinely *is* one trailing sentence | ✅ holds; both oracles ~0.77 |
| *"Assault, harassment and stalking top calls to victim line"* | crime volume; the service existing is context, not delivered benefit | ✅ holds |
| *"Dozens of greyhounds to land in Australia as NZ racing ban begins"* | the event is 150 dogs exported to **continue** racing after the ban, ten euthanised in the final season, and a *"deliberate attempt to avoid"* the transition agency. No person benefits at all | ✅ holds; `no_person_benefits` is exactly right |
| *"Rethink Business Centre Management"* | a signed consultant's opinion column: benefits stated in the **conditional**, subject is failure plus a proposal, nothing delivered. Already re-read in full by the owner | ✅ holds |

⭐⭐ **The Travelodge and nursery rows bracket §2's qualifier, and that is the whole argument for
the v8.1 fix.** Both are *"a policy change made after the fact"*. In Travelodge it is literally
one trailing sentence and both oracles score it **~0.77**, correctly. In the nursery row it is
about a third of the body, funded, commenced and causally attributed — and the gate flips. The
clause is not ambiguous in general; it is ambiguous **exactly where the qualifier stops
applying**, and the two rows show both sides of that line.

⭐ Also worth keeping: the Namibia row's `why_adverse` says its shape is *"same family as
nature_recovery's pledge / policy-announcement caps, **which uplifting has no equivalent of**"*.
v8's §2 **is** that equivalent, and both oracles now score the row ~1.0 — so a gap recorded
against v7 is measurably closed by v8. ⚠️ The two oracles reach it by different routes
(DeepSeek `out_of_scope` 3/3, Gemini `harm_is_subject` 3/3): **the verdict taxonomy is not
uniquely determined even when the score is right.** Do not treat a verdict label as ground truth.

## 4. Class B — 9 of 9 also hold, and the class is about REGISTER, not subject

| row | what the full text is | verdict |
|---|---|---|
| *"Boys must not be left behind, says child welfare minister"* | an aspiration stated at an engagement session — no programme, no budget, no beneficiary count | ✅ holds |
| *"Pioneering marine scientist Sylvia Earle reflects…"* | a **620-character** radio-segment blurb; career firsts, all individual, none delivered to anyone | ✅ holds |
| *"Engineered nanovesicles targeting METTL3…"* | preclinical cells and animals. No patient, no trial | ✅ holds |
| *"…Life Cycle Assessment… Laboratory rodent enrichment"* | the beneficiary is a **research rodent**; the framing is waste-hotspot analysis | ✅ holds |
| *"EBA ESG risk dashboard…"* | a regulator's data pipeline reporting on its own data quality | ✅ holds |
| *"Fehlende Zeichensetzung: Ich war ein Rechtschreibschnösel"* | a first-person essay about becoming less strict about other people's commas | ✅ holds |
| *"Systematic solvent screening… papaya seeds oil"* | a methods paper. No human subject at all | ✅ holds |
| *"Curing the cause"* | an opinion column arguing mental health should engage social determinants; describes no process | ✅ holds |
| *"Sihem Djoudi… nommée à la tête d'une nouvelle clinique"* | a **personnel announcement** — degrees, an 18-year CV, two teaching awards | ✅ holds |

⭐ **Class A and class B fail for opposite reasons, and reading them together makes it obvious.**
Class A is about **subject**: a real delivered outcome exists somewhere in the article and the
dominant subject is a harm. Class B is about **register**: nothing is delivered at all, and the
prose merely *sounds* like an outcome — an abstract, an opinion column, a personnel notice, a
dashboard. ⛔ A single rule cannot catch both, which is why STEP 1 and the gatekeeper are
separate mechanisms and why §1f's finding that they are different defects still stands.

⚠️ Two things to carry into the labels rather than assume:
- The Sylvia Earle row is **620 characters** — the shortest surviving row, barely above the
  300-char floor. A register judgement on 620 characters is thin, and it is thin in the same
  direction for the oracle as for a human.
- The EBA row's own note records an **oracle-prompt gap** against v7: the `corporate_finance`
  flag *"enumerates"* shapes that miss a supervisory dashboard. v8 removed content-type caps
  entirely (§4: *"no code reads it"*) and routes this through STEP 1 §5 instead. **Whether that
  actually catches the dashboard is a question for the Phase B labels, not something to assert
  here.**

## What is still owed

⛔ **Nothing in the reading.** All 18 rows are read at full length and every label holds. What
remains is that **five class-A labels were originally confirmed on 300-character excerpts** — this
re-read did not overturn them, but it also cannot retroactively make the original adjudication
a full-text one. If a future dispute turns on one of those five, the adjudication to cite is
this one.
