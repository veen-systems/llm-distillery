# Decision: AI-crawler opt-out directives do not bar distillation training

**Date:** 2026-08-05
**Decider:** Jeroen (project owner)
**Status:** Accepted
**Issue:** #28 (filed 2026-03-14, no comments until now)
**Sibling:** ovr.news ADR-043 — the same directives, the *fetching* layer

---

## The question

FluxusSource's scanner found, on 2026-08-04, that **333 of 1,357 source domains
(24.5%)** publish a machine-readable directive blocking at least one AI crawler.
Under DSM Directive 2019/790 Art. 4(3), a rightsholder may reserve text-and-data-
mining rights by machine-readable means.

#28 argued that this repo carries **more** exposure than any other layer, because
training a model on article text is "textbook TDM" — more so than reading a feed
(FluxusSource) or summarising for a reader (NexusMind/ovr.news).

## Decision

**Training continues on the full corpus. These directives do not bar it.**

The owner's framing: *"that is not 'mining', that is modelling."* Recorded below in
the form that survives scrutiny, along with the form that does not.

### Grounds

**1. The directives are addressed to other parties.** Every one names a specific
third-party crawler — of the 333 flagged domains, GPTBot is named on **286**,
CCBot **270**, Bytespider **235**, ClaudeBot **231**, Google-Extended **230**,
and seven others below that. (A domain usually names several, so these do not sum
to 333.) We operate none of them. The
publishers overwhelmingly leave `User-agent: *` permissive, which is the line that
would address us. This is ovr.news ADR-043's ground 1, and it transfers here intact
because it is a claim about *who was addressed*, not about *what was done*.

**2. The artefact cannot reproduce the input.** A student model is Gemma-3-1B plus a
LoRA adapter with a **regression head that emits a number between 0 and 10** (ADR-001).
It has no language-modelling head at inference. It cannot emit a sentence, let alone
a source article — there is no prompt, no decoder, no sampling path. Whatever the
legal characterisation of the training act, the *output* is incapable of substituting
for any publisher's work, and no memorisation-extraction attack has a surface to
target. This is the strongest ground and it is specific to this repo: it would not be
available if we were distilling a generative model.

**3. Non-substitutional purpose.** The models exist to decide which articles a reader
is shown, and every path ends in a link to the publisher. The reservation right
protects a rightsholder's market; this use feeds it.

## The counter-argument, recorded because it is real

**"Modelling is not mining" is not a distinction the Directive draws, and it should
not be the sentence this decision rests on.**

DSM Art. 2(2) defines TDM as *"any automated analytical technique aimed at analysing
text and data in digital form in order to generate information which includes but is
not limited to patterns, trends and correlations."* Fitting a model to article text in
order to learn the pattern that predicts an oracle score is close to a central example
of that definition, not an exception to it.

**So the position is not "we are outside TDM."** It is: *a reservation under Art. 4(3)
was not made against us (ground 1), and even on the broadest reading of Art. 4, the
resulting artefact is non-reproductive and non-substitutional (grounds 2–3).* Those are
arguments about the **reservation** and about **harm**, not about the definition.

Anyone re-reading this record should not carry forward the shorter phrasing. It is the
kind of confident-and-untested claim the `feedback-claim-requires-verify` memory exists
to catch, and it would be the weakest sentence in the file if a publisher ever asked.
(That memory lives in the Claude Code auto-memory directory, **not** in this repo's
`memory/`. This record originally wrote it as a repo path — the identical broken
reference its own commit was fixing in `CLAUDE.md`. Corrected 2026-08-06.)

## What this decision does *not* cover

Three things, each genuinely separate and none of them settled here:

1. **The oracle sends article text to a third party.** Scoring runs through Gemini
   Flash (Google) and DeepSeek. Full article content leaves this machine and is
   processed by a foreign commercial LLM provider under that provider's terms. That is
   a *disclosure to a third party*, which is a different act from local training and is
   not addressed by any of the three grounds above — ground 2 in particular does not
   apply to it, because the recipient is a generative model.

   **Decided the same day: risk identified and knowingly accepted by the owner** —
   *"this is the only way I can do this, so if someone objects in future, let's see
   then."* Recorded in full, with the supporting considerations and the revisit
   triggers, at `ovr.news/docs/compliance-register.md` §3. It lives there rather than
   here because the same transfer happens on the summarisation path too; this repo is
   one of two callers, not the owner of the question.
2. **Models already trained.** Every deployed filter — uplifting v7, investment-risk v6,
   cultural-discovery v5, belonging v1, nature_recovery v4, solutions v6 — was trained
   before this question was asked. #28 is written entirely forward-looking. Nothing here
   says anything about the existing adapters, and on grounds 2–3 there is probably
   nothing to say; but it has not been assessed, and "probably nothing" is not an
   assessment.
3. **The specific-reservation case.** If a publisher addresses a reservation to *us* —
   by name, by a site-wide `User-agent: *` disallow, or in writing — that source comes
   out of training data. This decision is about ambiguous named-agent directives only.

## Corrections to #28 as filed

- **Numbers are stale.** #28 cites *238 of 971 domains (25%)* from the March scan. The
  2026-08-04 scan says **333 of 1,357 (24.5%)** — proportion nearly identical, absolute
  numbers up by half.
- **And this record's own first numbers were wrong (corrected 2026-08-06).** Ground 1
  originally read "GPTBot (401 domains), CCBot (359)…". Those were case-sensitive counts
  of matching *lines* in the scan output, not domains — over-counting domains that name
  an agent twice and dropping case variants. **401 exceeded the 333 total, which is
  impossible on its face.** Ground 1 is unaffected in substance; the figures were not.
- **117 domains failed open.** The scan could not check them and they aggregate into the
  "clean" 907. A publisher behind a WAF that 403s non-browser agents scores clean, and
  that is exactly the publisher most likely to be reserving. Any future claim that "we
  checked" is only as strong as those 117.
- The implementation sketch in #28 (filter training articles against
  `tdm_opt_outs.json`) is **not adopted**. It is retained in the issue as the thing to
  build if this decision is ever reversed.

## Consequences

- No change to the training pipeline. `prepare_data.py` gains no filter step.
- The 5–10K articles per filter (ADR-010) stay drawn from the full corpus, so no
  distribution shift and no re-derivation of any op-point. Had the alternative been
  taken, dropping 24.5% of domains would have shifted the corpus in ways that interact
  with the non-English work — several of the flagged domains are exactly the
  non-Anglophone outlets Chain 14 is about (zeit.de, volkskrant.nl, trouw.nl, yle.fi,
  yna.co.kr). **That is a consequence of the alternative, not an argument for this
  decision** — it would have been a reason to measure, not a reason to decide.
- #28 moves from open-and-untouched to decided, with the two carve-outs above filed as
  what remains.

## Review triggers

Re-open this record if any of the following happens:

- A court or the Commission rules on whether named-agent directives constitute Art. 4(3)
  reservations against unnamed parties. **This is the fact that would flip it.**
- This repo ever trains a model with a generative head. Ground 2 dies immediately, and
  grounds 1 and 3 are much weaker on their own.
- A publisher addresses a reservation to us directly.
- ovr.news ADR-043 is reversed — the fetching and training positions share ground 1.

---

**Not legal advice.** An engineering reading by the operator, written so it can be
audited rather than merely asserted. Grounds 1–3 are arguments; none has been tested.
Consult a qualified Dutch/EU lawyer before relying on this against a claim.
