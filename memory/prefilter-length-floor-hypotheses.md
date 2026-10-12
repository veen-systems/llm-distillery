---
name: prefilter-length-floor-hypotheses
description: Hypotheses from the NM#284/#285 prefilter measurement and the LD#92 short-content oracle test — what the per-filter prefilters actually do, and what enforcing them would cost
metadata:
  type: project
---

# Per-Filter Prefilters & the Short-Content Floor — Hypotheses

> ⛔ **2026-10-01: every per-lens prefilter this file measures is DELETED** (decision 0, NexusMind#284;
> ADR-019 *Amendment 2026-10-01*). The short-content floor half is still live (`make_oracle_prefilter`).
> Read the per-filter rows as history; nothing here is enforceable any more.

**Date:** 2026-08-02

Context: NexusMind#284 found the per-filter prefilters have never run in
production. Everything below is about the two questions that follow — *what
would they do if they ran*, and *is the student unreliable on the short content
the length floor blocks*.

## Refuted — 1–3 MOVED to [`archive/prefilter-length-floor-hypotheses-archive.md`](archive/prefilter-length-floor-hypotheses-archive.md) (2026-10-12)

1. the 0.638–0.649 cluster is not truncation (+0.0000–0.0097); 2. uplifting v7 does not over-score stubs at
n=60 (DiD +0.44, p 0.054, not Holm-significant; the P(DiD ≤ −1.24) claim is withdrawn); 3. a global length
gate would discard ~78 genuine uplifting articles per 8 cycles to remove ~39 bad ones.

## Confirmed — 4–7 MOVED to [`archive/prefilter-length-floor-hypotheses-archive.md`](archive/prefilter-length-floor-hypotheses-archive.md) (2026-10-12)

4. nature_recovery v4 / solutions v6 prefilters were pure length floors; **5. solutions v6 has a real
short-content defect** (D3 DiD −1.119 [−1.61, −0.61], second oracle −1.351; identification cleared, the cap VALUE
is not); 6. LD#92 used solutions' 2.25 as uplifting's op-point (it is 4.0); 7. a matching pass rate says nothing
about recall (cd v5: 15.5% of surfacing articles, 135/871). Hypothesis 5's harness check stays live here (its "see below", the ~50s manual run, is in the archive):
   <!-- verify: M=""; for p in scripts/diagnostics/ld92_analyze_did.py tests/fixtures/ld92/design.json tests/fixtures/ld92/deepseek_scored.jsonl; do [ -f "$p" ] || M="$M $p"; done; if [ -z "$M" ]; then echo "PASS harness+fixtures present (the RUN is manual, ~50s — see below)"; else echo "FAIL missing:$M"; exit 1; fi -->

## Open questions

8. **Does a short-content cap actually help solutions? Still open — but it is now
   the only question left, and it is a *value* question, not an existence one.**
   Identification is settled (hypothesis 5). What is not settled is the number,
   and two things constrain it:
   - **#95 first.** The cap is a threshold fit and inherits the measured
     |Δ| ≤ 0.16 batch-composition noise floor. Batch F.1 (archived; pin `batch_size`)
     precedes any value.
   - **Recall cost against NM#231/#292.** The same populations lead solutions'
     short-and-clearing list (`gn_africa_gn_sudan`, `gn_asia_gn_afghanistan`,
     `gn_africa_gn_zimbabwe`) as NM#231's under-served set, and two of the
     worst-gap D3 examples are real interventions the lens arguably *should*
     surface. Weigh against recall, never fit to the FP count alone.

   **A cheaper alternative appeared 2026-08-05 and should be priced first.**
   Google News is 14–17% of scored articles but **48–56% of all sub-300-char
   stubs** (~3× over-represented; measured within-period). Pre-enrichment already
   rescues ~62% of short content and fires below 500 chars, so the net is not too
   small — GN survives because its `url` is a `news.google.com/rss/articles/…`
   redirect, so the fetcher gets Google's redirect page, not the publisher's.
   **Retiring the GN proxies (FS#120, decision due ~2026-08-14) removes roughly
   half the population the cap exists to handle, at no recall cost to genuine
   articles.** Fix upstream before trading precision for recall downstream.
   <!-- verify: manual — FS#120 readout; check GN share of sub-300 rows after any retirement -->

12. **Does the same defect exist in the summariser, and is it the same
    mechanism?** Filed as ovr#299 on 2026-08-05. For English sources the share of
    summary content words absent from the article *and* its title runs 31.6% at
    1000+ chars → 73.9% at 120–299 → **83.4% under 120**, monotone. Mechanism is
    *not* the same as the scorer's: median summary length is 1159/968/875/1065
    against a 40× input range, i.e. a fixed output budget the model fills — with
    a full article it compresses, with a headline it generates. Open question for
    this file: **whether the scorer has an analogous fixed-budget behaviour**, or
    whether its short-content error is purely a vocabulary-without-subject
    effect. Worth testing because the fixes differ — one is a budget, the other a
    cap.

9. MOOT since 2026-10-01 (per-lens prefilters deleted) — moved to the archive.

10. **Is exposure predictive of defect? Evidence so far says no.**
    investment_risk has by far the largest short-content exposure (635 clearing
    op-point per 8 cycles, 20.3% of its sub-300 rows) and **no length effect at
    all** (DiD +0.26, CI spans zero). Worth keeping in mind before sizing work
    from volume.

11. **cultural_discovery shows a significant *positive* DiD (+0.79).** The
    student *under*-scores short content there. That is NM#231's direction, not
    LD#92's — possibly the same underlying mechanism seen from the other side.

## Short vs long surfacing rate, all six lenses (2026-08-08)

The baseline table that was missing from every prior discussion. 8 cycles,
`filtered_*.jsonl` (survivors), split at 300 chars of persisted `content`,
each lens against **its own** op-point:

| filter | short n | short surf% | long n | long surf% | ratio |
|---|---|---|---|---|---|
| solutions | 7,611 | 2.3% | 15,805 | 4.6% | 0.49× |
| uplifting | 7,615 | 2.3% | 15,805 | 13.4% | 0.17× |
| investment_risk | 3,798 | 20.2% | 13,567 | 27.6% | 0.73× |
| cultural_discovery | 7,615 | 0.2% | 15,805 | 2.3% | 0.09× |
| belonging | 7,615 | 0.4% | 15,805 | 3.2% | 0.11× |
| nature_recovery | 7,615 | 0.0% | 15,805 | 0.2% | 0.25× |

**Every lens surfaces short content LESS often than long (0.09–0.73×).** So
"the student over-scores stubs" is not true as a platform-wide *rate* claim.
LD#92's defect is a **within-band** bias — short articles that clear the bar are
likelier to be wrong — not an inflated rate of clearing it. Those are different
claims and earlier framing (mine included) blurred them.

`investment_risk` looked anomalous when only the short column was shown (20.2%
vs ≤3% elsewhere). It is not: its ratio is 0.73×, same direction as the rest,
and its absolute rates are high because that lens surfaces a lot of everything.
**Never compare one length-group's rate across lenses with different base
rates** — the within-lens ratio is the only comparable quantity. Its smaller
short n (3,798) is the NM#189 source-type allowlist dropping rows from
`filtered_*.jsonl` entirely, which also explains why it has zero GN rows.

## Step 4 measured 2026-08-08 — VERDICT: do not set the cap

**Step 4 (2026-08-08): VERDICT do not set the cap** — a cap ≥ the op-point cannot remove a false positive (visibility keys on raw, ADR-022); the sizing and its invalidation are in `archive/prefilter-length-floor-hypotheses-archive.md`, moved verbatim 2026-10-12 (#163).

## ⏳ H-L1 — OPEN: the framework-leakage rationale is ASSERTED EVERYWHERE AND MEASURED NOWHERE

**Opened 2026-08-14 (late).** The 300-char floor's stated reason is that short articles
make the oracle analyse the *evaluation framework* instead of the article. That
sentence is in `batch_scorer.py:146`, in #93, and in this file — and **no measurement
of it exists anywhere in the repo.** It has been load-bearing for a year.

⚠️ **This gates retiring the floor on `content_meta.kind`.** The Round 3 argument is
that the floor discards 77.2% of RSS rows and *"what it discards is overwhelmingly
complete feed summaries, not truncated articles — length was never the quality
signal."* **That does not follow if the rationale is real**: framework leakage is a
function of **how much text the oracle sees**, not of whether the text is *complete*.
A complete 143-char feed summary still gives the oracle 143 chars. **`kind` tells you
the text is finished, not that it is sufficient.** Those are different claims and the
plan currently treats them as one.

⭐ **Confirmed by the producer 2026-08-14, and it makes the gap explicit rather than
closing it.** The entire derivation is one line and **never looks at length**:

```python
kind = 'headline_only' if not body or body == title else 'feed_summary'
```

Vocabulary is **two values** (`feed_summary`, `headline_only`) — no `summary`, and
`full_text` is deliberately absent. Measured over 97,526 RSS rows: **5.3%
`headline_only`, 6.9% of native RSS, 0.0% of 25,607 GN rows.**

⚠️ **My "does `kind` separate complete-short from truncated?" question DISSOLVED, but
not in `kind`'s favour** — there is no `truncated` sibling being emitted, and
FluxusSource **does not truncate RSS bodies at all** (no content slicing on the emit
path), so a short RSS body is the publisher's own `<description>`. Truncation is not
the risk. **Insufficiency is**, and `kind` does not measure it.

**Their position, stated fairly:** `kind` retires the floor *for the purpose the floor
was actually serving* — separating "published nothing but a headline" from "published a
complete short summary."

⚠️ **CONCEDED IN BOTH DIRECTIONS 2026-08-14, and the honest state is a draw.**
FluxusSource conceded the substance — if the rationale is leakage-by-insufficiency then
**length is precisely the property** and `kind` does not retire the floor, and they
agreed my truncation answer cut *against* `kind` rather than for it. **But they were
right that I overstated my side.** I wrote *"this repo's own code says otherwise"*;
`batch_scorer.py:146` **asserts** the rationale, it does not establish it. By my own
account it is asserted in three places and measured in none.

⭐ **So: TWO CANDIDATE RATIONALES, NEITHER ESTABLISHED** — not "mine is proven and
theirs is wrong." A third party had a view all along and nobody noticed: Contract A's
`kind` description reads *"NexusMind currently infers this from length, **which is a
guess the producer does not have to make**"* — the consumer's schema takes a position
on our rationale too, and it is not the one in our code.

⚠️ **And it already shipped as a flat assertion.** `7bc20a0`'s schema `description`
carries the sentence **"Length was never the property being measured"** to every
consumer of FluxusSource's `output_schema.json` — an unproven claim about *this repo's*
rationale, stated at higher confidence than its evidence. FluxusSource identified it as
their defect regardless of who is right. **That is the day's failure mode in its purest
form, and it is now in a machine-readable contract rather than a document.**

### The free natural experiment — run, and it is INCONCLUSIVE

`solutions v4` was labelled with sub-300 rows present (**911/10,297 trainval, 413/1,500
holdout**), so articles below today's floor already carry oracle labels.

| split | n | mean score | within-row spread | flat (<0.25) |
|---|---|---|---|---|
| trainval **sub-300** | 911 | 0.70 | 0.485 | 74.0% |
| trainval **300+** | 9,386 | 0.94 | 0.573 | 67.9% |
| holdout **sub-300** | 413 | 0.21 | 0.144 | 92.7% |
| holdout **300+** | 1,087 | 0.40 | 0.248 | 86.9% |

Short rows score **lower and flatter** in both splits. ⚠️ **This is NOT evidence of
leakage, and must not be cited as such.** It is exactly what *correct* scoring of
thin, off-topic content looks like. Leakage would predict scores drifting toward the
**middle** or becoming uninformative — not collapsing toward zero. **The effect is
fully confounded with topicality**, and nothing here separates them.

### ⚠️ My groundedness instrument was INVALID — recorded so nobody rebuilds it

I tried to probe leakage directly by asking whether each dimension's `evidence` string
appears in the article text. **It read 76.0% / 75.3% "ungrounded" on trainval and
93.3% / 89.6% on holdout — i.e. essentially identical in both arms.** That is not a
finding about short articles; it means the test measured **paraphrase**. The oracle
summarises rather than quoting verbatim, so a substring check fails on nearly every
row at every length. **A number that is the same in the treatment and control arm is
measuring the instrument.**

### What would actually settle it (needs owner approval — oracle spend)

A **paired** design, which is the only shape that breaks the topicality confound: take
articles that exist at **both** stub and full length, score **the same article twice**,
and compare. `docs/evidence/2026-08-12-pre-post-enrichment-pilot-scores.jsonl` is that
shape already but carries **student** scores, not oracle ones. ⚠️ **Do not re-score
Google News rows for this** (median 89 chars — below the floor that exists for exactly
this reason).

⭐ **Until this is measured, do not retire the floor on `kind` alone.** `kind` is still
worth having — it distinguishes *complete-but-short* from *truncated*, which the floor
cannot — but "length was never the quality signal" is currently an unmeasured claim
resting on an unmeasured rationale.

## What shipped (2026-08-03, #93 — llm-distillery side)

The floor is split three ways, per ADR-022 "stamp always, decide once":

- **Labelling:** `ground_truth.batch_scorer.make_oracle_prefilter()` composes
  `check_content_length` + `apply_filter`. The framework-leakage rationale is a
  property of the oracle prompt, so the floor lives on the path that has one.
- **Scoring:** no `apply_filter` checks length (base + the three filters that
  did it inline: uplifting v7, belonging v1, investment_risk v6). Every scoring
  result carries `content_length`; `HybridScorer`'s Stage-1 branch stamps too.
- **Enforcement:** one `short_content.cap` per filter in `config.yaml`, read by
  `FilterBaseScorer._apply_short_content_cap`. **Off on every filter** — the
  only candidate defect (solutions, hypothesis 5) is still confounded.

**A/B verification, n=2,917** (`data/raw` — pre-enrichment, so a short-skewed
*stress* corpus at 65.8% sub-300; not a rate estimate). Oracle-gate verdicts at
HEAD vs after the split: **byte-identical for five of six filters**. The
composition is order-preserving because every rule ANDs into the verdict, so
only the *reason* string can move, not the boolean.
<!-- verify: test -f scripts/diagnostics/prefilter_gate_ab.py && echo PASS || echo FAIL -->

> **SUPERSEDED FOR cd AT v6 (2026-08-06).** Everything below about
> cultural_discovery's prefilter describes **v5**, which is still the version
> NexusMind runs — so it stays accurate for production today. But **cd v6's
> prefilter has no lens rules at all**: the topic gate (453 stems), the four
> exclusion categories and the three domain blocklists were deleted after the e5
> probe beat the gate on held-out oracle labels (FN 0/75 vs 10/75, ADR-021).
> Screening moved to the probe. So the enforcement question this file exists to
> answer — *is it safe to enforce cd's declared 0.25 pass rate?* — **does not
> carry forward to v6**: there is nothing left to enforce but `validate_article`.
> The recall measurement that mattered (15.5% of surfacing articles, below) is
> what justified deleting the gate rather than turning it on. See
> [[cd-v6-probe-hypotheses]].

**The one intended exception: cultural_discovery v5.** Its custom `apply_filter`
never called `check_content_length` — a v3→v4 regression recorded in its own
module docstring and in TODO "Prefilter Quality". So cd was the only filter
whose *labelling* path had no floor, and hoisting the floor restores one there:
**190/474 = ~40% of what cd would have sent to the oracle** on the stress
corpus. Production-realistic share is lower (enriched corpora run ~35% sub-300,
not 66%) and **unmeasured**. Pinned by a test so it stays a decision, not an
accident. **Re-measure before the next cd oracle run (#87).**

**Synced to NexusMind 2026-08-03** (`c932065` content + `c1df13c` record; 950
NM tests pass). Syncing surfaced a second drift: `investment_risk v6` blocked
`arxiv` / `mastodon_` / `bluesky` in NexusMind since 2026-05-18 and never
upstream, so the oracle was labelling a population production never scores. A
blind LD→NM copy would have deleted all three; they were ported *back* to
llm-distillery instead (`e51309d`). **Diff the two copies before every sync —
`.nexusmind-owns` is empty, so nothing else compares them.**

**Still not done:** the NM#284 shadow re-run. Its pass rates will jump, and for
the first time describe lens behaviour rather than a length floor (LD#90 item
2). Nothing live changed — the per-filter prefilter does not execute in the
production scoring path (NM#284).

## Method notes worth reusing

- **Difference-of-differences cancels oracle bias**, which is what makes DeepSeek
  usable as a judge for filters whose teacher was gemini. Read the short-vs-long
  *gap*, never the absolute agreement (FILTER_PLAYBOOK §0).
- **Bootstrap the original n before calling a replication failure "noise" — but
  get the resampling right.** The instinct was correct and the conclusion held;
  the execution did not. Sample **with** replacement (without-replacement
  subsampling silently applies a finite-population correction), check the draw
  count can resolve the probability you are claiming, and remember that
  resampling window B cannot answer a question about window A. The filter
  mix-up conclusion survived on three independent lines of evidence, none of
  which was the bootstrap.
- **Selection on the dependent variable is the standing hazard in this whole
  design.** Matching two groups on the *student's own score* is not matching
  when the two arms sit at different depths of their own distributions. Prefer
  matched percentile bands, and always re-run at a second threshold: an
  artifact moves with the threshold, a real effect does not.
- **Reconcile denominators before diffing two sources.** See
  [[reference-nexusmind-data-sources]] — the log and the file count different
  sets, and `data/raw/` is pre-enrichment.

## Related

- [[project_session_2026_08_02]] — the session
- [[reference-nexusmind-data-sources]] — the two denominator traps
- [[cross-repo-prioritization]] — Chain 4, re-rooted on the length-floor split

---

## 2026-08-11 — the #93 step-4 re-measure gate was run. It is still CLOSED.

**2026-08-11: the #93 step-4 re-measure gate was run and is still CLOSED** (GN-URL share 24.1% → 25.1%, no trend); the run is in `archive/prefilter-length-floor-hypotheses-archive.md`, moved verbatim 2026-10-12 (#163).

## 2026-08-23 — the floor measured by SCRIPT, both curves, 1,332,648 rows

Evidence: `docs/evidence/2026-08-23-length-floor-by-script.md`. Read-only, no spend.
Population: every `(id, filter)` pair in NexusMind `data/filtered/` (516 files, 8.8 GB).
Script classified **from the article text** (Unicode ranges) — *not* the `language` field,
which under-reports non-Latin because Asian/African/MENA publishers are acquired in their
English editions (FS#166).

### H-LF1 CONFIRMED · H-LF2 REFUTED · H-LF3 CONFIRMED — MOVED to [`archive/prefilter-length-floor-hypotheses-archive.md`](archive/prefilter-length-floor-hypotheses-archive.md) (2026-10-12)

H-LF1: define any floor in TOKENS naming its tokenizer (300 chars = 69 Latin tokens vs 197 Japanese, 2.85×).
H-LF2: at 300 chars Latin loses MOST rows today (32.6%), CJK is asked for most information. H-LF3: the floor is a
COMPUTE lever, not a quality one — the scorer already suppresses short text; a 128-token floor drops 36.64% of the
corpus to remove 16.23% of surfacing rows; the short-surfacing problem is Latin-only (GN, ADR-007).

### ⛔ H-LF4 OPEN — Hebrew is a DEFECT, not a threshold question

9,282 rows, **median 202 chars**, **77.0% dropped at a 128-token floor** against 0.8–38.4%
for every other script. A stub-publishing source or an extraction failure. **Any floor
silently deletes almost all Hebrew content.** Investigate before setting a number.

### ⚠️ Limitations

A **single 4.5 op-point** was used across six filters whose op-points differ (`solutions`
2.25, `investment_risk` 4.25) ⇒ the surfacing population is **understated**; re-run per
filter before acting. `source` not captured. Thai (12 samples) and other Indic (2) excluded.

**Bearing on #93/#114:** this measures the *cost and benefit* of a scoring-path floor. It does
**not** measure #114's question — whether the *oracle-prompt* framework-leakage rationale is
real. Those remain separate thresholds on separate tokenizers.
