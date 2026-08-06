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

   **ASSESSED 2026-08-06 — see the appendix at the end of this record (#97).** The
   models came back clean, as expected. The repository did not: 812 committed JSONL
   rows carry more than 500 characters of article body each in a public repo, and
   grounds 2–3 do not cover republication.
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

## Appendix: the already-trained filters, assessed (#97, 2026-08-06)

Carve-out 2 above said the deployed models had not been assessed and that "probably
nothing" is not an assessment. This is the assessment. It answers #97's three
questions, and **the second one did not come back clean.**

Scan used throughout: `FluxusSource/data/tdm_opt_outs.json`, the 2026-08-04 snapshot
(1,357 domains, 333 opted out, 117 failed open). Domain matching is hostname with a
leading `www.` stripped — a subdomain not listed in the scan counts as unknown, not
as clean.

### Q1 — reservations addressed to *us*: none found

**Zero of the 333 opted-out domains carry a `User-agent: *` reservation.** Every
signal in the file names a specific third-party crawler; the deduplicated
domain-level counts reproduce ground 1 exactly (gptbot 286, ccbot 270, bytespider
235, claudebot 231, google-extended 230, applebot-extended 192, anthropic-ai 167,
chatgpt-user 153, perplexitybot 144, diffbot 127, facebookbot 110). We operate none
of them. Ground 1 therefore transfers to the already-trained filters with nothing
left over, and carve-out 3 (the specific-reservation case) has no instances today.

Overlap is nonetheless large, so the question was worth asking. Training splits
present in this checkout, matched against the scan:

| split | articles | on the opted-out list | domain not in the scan |
|---|---|---|---|
| `solutions_v6` | 10,297 | 3,033 (29.5%) | 2,309 (22.4%) |
| `solutions_v4` | 11,797 | 3,415 (28.9%) | 2,783 (23.6%) |
| `nature_recovery_v4` | 3,892 | 568 (14.6%) | 655 (16.8%) |

Heaviest contributors are exactly the non-Anglophone outlets the Consequences
section named: xataka.com, lalibre.be, mediapart.fr, dhnet.be, 20minutos.es,
lavanguardia.com, plus theregister.com and bbc.co.uk.

**Limits of this answer, stated rather than glossed:** (a) only three splits exist
in this checkout — `uplifting v7`, `investment_risk v6`, `cultural_discovery v5` and
`belonging v1` live only on gpu-server (`~/llm-distillery/datasets/training/`), so
their overlap is *unmeasured*, though there is no reason to expect a different
shape; (b) the scan is a 2026-08-04 snapshot and **cannot** establish what a domain's
`robots.txt` said at training time — #97 anticipated this, and the honest answer is
that it is not recoverable; (c) the 117 fail-open domains aggregate into "clean", so
"we checked" is only as strong as those.

### Q2 — published artefacts: the Hub is clean, **this repository is not**

**Hub artefacts do not redistribute source text.** `upload_to_huggingface.py` sends
the model directory (`adapter_config.json`, `adapter_model.safetensors`,
`tokenizer.json`, `tokenizer_config.json`), a generated model card, and two JSON
files whose keys are hyperparameters and metrics only (`batch_size`, `best_val_mae`,
`dimension_names`, `epochs`, `learning_rate`, `max_length`, `model_name`,
`num_parameters`, …). No article field is uploaded on any path.

**Training splits are not published** — `.gitignore:76` ignores `datasets/*`, and
`git ls-files datasets/` returns 9 files, none of them a split. That part of #97's
expectation holds.

**But `git ls-files '*.jsonl'` turns up 812 committed rows carrying more than 500
characters of article body each — 2,364,068 characters in total (median row 1,713,
p90 6,171, max 42,002) — and this repository is PUBLIC.** 160 of those rows (19.7%,
21 distinct domains) come from domains on the opted-out list, led by biorxiv.org
(40), nos.nl (40), xataka.com (30) and fastcompany.com (20). The largest files are
`filters/common/commerce_prefilter/training/splits/test.jsonl` (115),
`filters/ai-engineering-practice/v1/calibration/prefiltered_sample_100.jsonl` (90),
`filters/belonging/v1/calibrations/candidates/belonging_candidates.jsonl` (62), the
`filters/todo/seece/v1/calibrations/` batches, and `datasets/adverse/*.jsonl` (11
rows, deliberately committed and documented in that directory's README, several
complete articles ending on a full sentence).

The training-data question and this one are not the same question, and the grounds
above do not stretch to cover it:

- Art. 4(3) is about **mining**. A JSONL file on GitHub is **republication** — an
  ordinary reproduction-and-making-available question under copyright, which the
  quotation exception may or may not reach at 1,700–42,000 characters per row.
- **Ground 2 does not apply.** It says the *artefact cannot reproduce the input*.
  These files **are** the input. Ground 2 is the strongest ground in this record and
  it is silent here.
- **Ground 3 does not apply either.** A committed corpus file is not a path that
  ends in a link to the publisher.

### Q3 — remedy

**For Q1: nothing to do, and that is now recorded rather than assumed.** Grounds 1–3
cover the already-trained filters. No retrain, no data removal, no re-derivation of
any op-point.

**For Q2: yes, there is something to do, and it is *not* "stop and retrain."** The
models are unaffected — this is a publication defect in the repository, not a defect
in the training. It is also not urgent in the #93/#95 sense: 812 rows is small, and
nothing about it is getting worse on its own. Sizing and choosing the remedy is an
owner decision, but the shape of the options is:

1. **Truncate in place** — cap `content` at a quotation-length excerpt (a few hundred
   characters) across the tracked JSONL, keeping `id`/`url`/`title` and all
   scores/labels. Every one of these files exists as *evidence about a score*, not as
   a corpus, so the scores are the load-bearing part. Cheapest, and preserves what the
   files are for.
2. **Rewrite history as well** — required only if a public repo's git history is
   itself considered a publication surface. Expensive, and the working rule here is
   that history another session may hold does not get rebased.
3. **Accept and record**, as with the oracle-to-third-party transfer in §3 of
   `ovr.news/docs/compliance-register.md`. A defensible option; it just has to be a
   decision rather than an oversight, which until today it was.

**Not chosen here.** #97 asked for an assessment, and an assessment that quietly
performed a 60-file redaction would be doing something else. Filed for the owner.

### Reproduce

```bash
# Q1 — overlap between local training splits and the opt-out scan
python - <<'PY'
import json, collections
from urllib.parse import urlparse
scan = json.load(open("../FluxusSource/data/tdm_opt_outs.json"))
opted = {k for k, v in scan["domains"].items() if v.get("has_tdm_opt_out")}
norm = lambda u: (lambda h: h[4:] if h.startswith("www.") else h)((urlparse(u).hostname or "").lower())
for d in ("solutions_v6", "solutions_v4", "nature_recovery_v4"):
    c = collections.Counter()
    for part in ("train", "val", "test"):
        for line in open(f"datasets/training/{d}/{part}.jsonl", encoding="utf-8"):
            c[norm(json.loads(line)["url"])] += 1
    n = sum(c.values())
    print(d, n, sum(v for k, v in c.items() if k in opted))
PY

# Q2 — committed article text, repo-wide
for f in $(git ls-files '*.jsonl'); do
  python -c "import json,sys;print(sum(1 for l in open(sys.argv[1],encoding='utf-8',errors='replace') if l.strip() and len(str(json.loads(l).get('content','')))>500))" "$f"
done | paste -sd+ | bc
```

---

**Not legal advice.** An engineering reading by the operator, written so it can be
audited rather than merely asserted. Grounds 1–3 are arguments; none has been tested.
Consult a qualified Dutch/EU lawyer before relying on this against a claim.
