---
name: prefilter-length-floor-hypotheses
description: Hypotheses from the NM#284/#285 prefilter measurement and the LD#92 short-content oracle test — what the per-filter prefilters actually do, and what enforcing them would cost
metadata:
  type: project
---

# Per-Filter Prefilters & the Short-Content Floor — Hypotheses

**Date:** 2026-08-02

Context: NexusMind#284 found the per-filter prefilters have never run in
production. Everything below is about the two questions that follow — *what
would they do if they ran*, and *is the student unreliable on the short content
the length floor blocks*.

## Refuted

1. **"The 0.638–0.649 four-filter cluster is a truncation artifact" (NM#285) —
   REFUTED.** Same-row full-vs-truncated replay, 4 cycles, n=8,283: the effect
   is +0.0000 (nature_recovery, solutions), +0.0005 (cultural_discovery),
   +0.0008 (belonging), +0.0028 (uplifting), +0.0097 (investment_risk). The
   *mechanism* claim was right — url/source rules genuinely cannot fire in-path —
   but it is worth tens of articles, not the hundreds needed to move a rate by
   0.05. The cluster survives the full contract unchanged.
   <!-- verify: manual — rerun the same-row A/B; nature_recovery and solutions must still return 0.0000 -->

2. **"uplifting v7 over-scores sub-300-char stubs" (LD#92 at n=15) — REFUTED at
   n=60/group.** DiD **+0.44**, but **not significant**: exact permutation
   p = 0.054, and under Holm across the six filters tested it does not survive
   (only solutions and cultural_discovery do). Read it as **"no detectable
   length effect"**, not as the student under-scoring stubs. MAE ratio 0.88×.
   Clears rate short/long is flat at every bar: 90/88 @2.25, 87/87 @3.0,
   67/65 @4.0, 28/32 @5.0 — that flatness is the robust part.
   ⚠️ **The "P(DiD ≤ −1.24) = 0.0000" claim is WITHDRAWN** (2026-08-02 review):
   it sampled *without* replacement (finite-population correction deflates sd by
   √(1−15/60)), and 20k draws cannot resolve a true 8.0e-5. It also asked the
   wrong question — resampling the 40-cycle window says nothing about an n=15
   draw from a different 8-cycle window. See hypothesis 6 for what does hold.

3. **"Promote `content_too_short` to one global pre-fan-out gate" (08-01) —
   still refuted, but for a different reason than recorded.** The 08-01 argument
   was "it drops ~half genuine content". At n=60 the real reason is stronger and
   simpler: short content that clears an op-point is **as likely to be genuine as
   long content** (uplifting 67% vs 65% oracle-validated). A length gate would
   discard ~78 genuine surfacing uplifting articles per 8 cycles to remove ~39
   bad ones.

## Confirmed

4. **`nature_recovery v4` and `solutions v6` prefilters are pure length floors.**
   Both declare `EXCLUSION_PATTERNS = {}` deliberately (commerce upstream,
   ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides — a no-op with
   nothing to override. Across 8,283 articles the only block reason either emits
   is `content_too_short` (2,950); zero lens blocks. They are byte-identical
   because they are the same filter. Their declared `expected_pass_rate` (0.85 /
   0.20) described gates that do not exist; both deleted 2026-08-02.

5. **`solutions v6` has a real short-content defect — IDENTIFIED 2026-08-05.**
   The discriminating tests the 08-02 review asked for were run (both of them,
   plus a replication in the same oracle run; n=80/arm, 456 articles, 0 errors,
   0 junk skips). Predictions were pre-registered in the sampler before any
   oracle call.

   | design | arm depth ratio | DiD | cluster 95% CI | cluster p | + Holm |
   |---|---|---|---|---|---|
   | D1 both arms `raw >= 2.25` | 0.50 | −0.790 | [−1.29, −0.28] | 0.0032 | 0.0032 |
   | D2 both arms `raw >= 4.00` | 0.19 | −0.861 | [−1.34, −0.38] | 0.0006 | 0.0012 |
   | D3 top 2.3% **within** each arm | 1.00 | **−1.119** | [−1.61, −0.61] | <5e-5 | <1.5e-4 |

   ⚠️ The p-values are the **source-clustered bootstrap** p, Holm-corrected
   across the three designs. An earlier version of this table carried
   article-level *permutation* p (0.0022 / 0.0007 / <1e-5), which ignores
   clustering and is anticonservative. Both sets support the same conclusion,
   but quote the clustered ones. The scripts print the permutation p in a
   parenthesised column for continuity only.

   The artifact predicted D2 markedly more negative and **D3 → 0**. Observed:
   D2 moved −0.071 and **D3 is the largest**. At matched depth the oracle puts
   35.0% of the short arm below op-point vs 5.0% of the long arm, across 55
   distinct sources in 80 rows. Unchanged with the gatekeeper off (corroborates
   #94); survives dropping `smart_compress`-truncated long rows (D3 −1.024,
   p=0.0002). Residual: matched percentiles equalise selection *severity* but
   not *noise* (short-arm MAE ratio 1.91×), so some negative DiD is still
   expected in D3 — D2 is the independent check and it barely moved.
   **Second oracle confirms it.** `gemini-2.5-flash` on the same D3 sample
   (160/160, 0 errors) gives DiD **−1.351** [−1.73, −0.96] vs deepseek's −1.119.
   The two disagree per article (mean |diff| 1.18) and gemini is more generous
   on *both* arms (2.80/4.95 vs 2.40/4.31) — different absolute bias, same gap.
   That is the convergence DiD exists to produce, and it rules out "the judge
   penalises short input" as the explanation.
   ⚠️ **Still do not fit the cap VALUE**: that is a threshold fit and inherits
   #95's |Δ| ≤ 0.16 noise floor (Batch F.1 first). Identification is cleared;
   calibration is not.
   ⏱️ **The next annotation needs `VERIFY_TIMEOUT=120`.** It is a source-clustered
   bootstrap with no iteration flag and takes ~50s, against the curate runner's
   30s default — so a default run reports it ERROR *(timed out)*, which is
   indistinguishable from a broken check. It is not broken: verified 2026-08-12,
   exit 0, `D3_pct2.3  80  80  -1.119 [-1.61, -0.61]`.
   <!-- verify: M=""; for p in scripts/diagnostics/ld92_analyze_did.py tests/fixtures/ld92/design.json tests/fixtures/ld92/deepseek_scored.jsonl; do [ -f "$p" ] || M="$M $p"; done; if [ -z "$M" ]; then echo "PASS harness+fixtures present (the RUN is manual, ~50s — see below)"; else echo "FAIL missing:$M"; exit 1; fi -->
   <!-- verify: manual — the full DiD run, ~50s, exceeds the curate runner's 30s default and so cannot be an inline check: `PYTHONPATH=. python3 scripts/diagnostics/ld92_analyze_did.py --design tests/fixtures/ld92/design.json --scored tests/fixtures/ld92/deepseek_scored.jsonl | grep D3_pct2.3`. Expect exit 0 and `D3_pct2.3  80  80  -1.119 [-1.61, -0.61]` (verified 2026-08-12). The inline check above covers the realistic decay — harness or fixtures deleted. -->

   **Harness AND data committed.** Scripts in `scripts/diagnostics/ld92_*.py`
   (`a10e084`; `ld92_crosscheck.py` came later in `c587b78`), fixtures in
   `tests/fixtures/ld92/` — the 456 deepseek rows, the 160 gemini rows and the
   design file, with article bodies stripped (only the word count is used, for
   the `smart_compress` flag) so no scraped text enters git. Every number in
   this hypothesis reproduces from those three files.

   The n=15 and n=60 originals committed **neither** script nor data, which is
   why this had to be rebuilt from the production pool up — the single most
   expensive part of the re-run, and the reason the fixture is here.

   What is *not* in doubt is the failure mode, which is exactly as LD#92
   described it — development/progress vocabulary in a headline with no subject:
   *"ABD Grants $250m Loan to Shield Cambodia's Vulnerable Households"* student
   4.21 / oracle 0.00. That the solutions lens is *about* concrete interventions
   makes development-finance headlines its maximally confusable case, which is a
   mechanism a selection artifact does not supply. Corrected exposure ~49 false
   positives per 8 cycles (**36–62** at n=60), not ~460.

6. **The oracle-test design is sound; the 08-01 execution mixed up a filter
   parameter.** LD#92 states uplifting's tier threshold as **2.25**, which is
   *solutions'* op-point — uplifting's is **4.0** (verified in production: tier
   `low` tops at raw 3.999, `medium` starts at 4.003). The "924 / 15.0%" scale
   figure reproduces exactly at a 2.25 bar (910 / 14.8%) and collapses to
   **117 / 1.9%** at 4.0. Difference-of-differences itself held up fine at 4×
   the sample.

7. **A matching pass rate says nothing about recall (LD#86).** cultural_discovery
   v5's observed 0.2605 matches its declared 0.25 — the one MATCH on the board —
   and enforcing it anyway costs **15.5% of surfacing articles** (135/871 over
   20 cycles), 0% of high tier. Rate-agreement and safety-to-enforce are
   independent properties.
   ⚠️ **"Skewed non-English" was the wrong framing** (corrected 2026-08-02).
   German 4.9% and French 5.3% are blocked at *less than half* the English rate
   (13.0%); pooling ten languages into "non-English 19.9%" describes no real
   population, and with source clustering z is 2.3 not 2.6. The sharper, true
   finding: **the entire gap is `no_cultural_topic_signal`** (9.9% en vs 19.2%
   non-en) while `celebrity_art`, `political_conflict` and `tourism_fluff` all
   fire *more* on English. It is uneven multilingual keyword coverage in
   `TOPIC_GATE_PATTERNS`, not a demographic bias — and that is fixable and
   falsifiable (extend the keywords, re-run, check the rates converge).

## Open questions

8. **Does a short-content cap actually help solutions? Still open — but it is now
   the only question left, and it is a *value* question, not an existence one.**
   Identification is settled (hypothesis 5). What is not settled is the number,
   and two things constrain it:
   - **#95 first.** The cap is a threshold fit and inherits the measured
     |Δ| ≤ 0.16 batch-composition noise floor. Batch F.1 (pin `batch_size`)
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

9. **Does extending `TOPIC_GATE_PATTERNS` close LD#86's per-language spread?**
   Now a sharp question rather than a demographic one: the gap is entirely
   `no_cultural_topic_signal`, and German (4.9%) and French (5.3%) already sit
   *below* English (13.0%) while Italian (28.6%) and Korean (37.5%) sit well
   above — consistent with keyword coverage, not with language per se.
   Falsification: extend the keyword set for the poorly-covered languages, re-run
   NexusMind's `scripts/measure_prefilter_recall_cost.py`, and check whether the per-language
   rates converge. If they do, the residual 15.5% is genuine editorial blocking
   and enforcement can be re-argued on its merits.

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

Sized it, then found the sizing invalid. Both structural findings hold whatever
the value:

- **A cap ≥ the op-point cannot remove a single false positive.** Visibility
  keys on the raw score (ADR-022/NM#280) and a cap leaves the row above the
  op-point by construction. #92's ~47% oracle-negative short rows sit just
  above solutions' 2.25 — a cap re-ranks them, only a gate suppresses them,
  and #93 exists to avoid the gate. **The cap and the defect are not the same
  shape.**
- **No short article reaches `medium_high` (5.0); max is 4.93** over 8 cycles.
  "Off the top of the feed" is already true with no cap, and any cap ≥ 5.0 is a
  guaranteed no-op (the LD#94 shape).

Mechanically fittable — cap 3.50 binds 71 of 173 short surfacing rows at mean
displacement 0.37, i.e. 2.3× the #95 noise band. **But 87.9% of that population
carries a Google News URL** (152 of 173) — and only the **A** slice below is
retired, which is the trap that produced my 3× error. ADR-007 (FluxusSource,
Accepted 2026-08-08) retires the **59** `gn_*` country proxies.
**Migration is UNDERWAY, not pending** —
`b869881` moved the first 6 African feeds to native RSS, first visible in
`collection_20260808_120948`; ~29 proxies follow. `gn_*` items per collection
went **565 → 528 → 202** across 08-08, so the corpus was already moving *during*
the 8-cycle measurement window and its last cycle sits on the boundary. (I first
wrote "decided, not implemented" from the 506 GN stubs still in the 12:49 cycle
— the count was right, the inference wrong; the FluxusSource session caught it.)
**There are THREE GN populations and ADR-007 retires only the first** (settled
with the FluxusSource session, 2026-08-08; their `memory/gn-proxy-protocol.md`):

| pop | what | enabled | query shape | fate |
|---|---|---|---|---|
| **A** | `gn_*` country proxies | 59 | `q=<Country>` | ADR-007 retires |
| **B** | publisher-named repoints | 230 | `q=…site:<domain>` | slow #90 migration |
| **C** | `google_news_*` topic feeds | 13 | `q="battery storage" OR …` | **editorial keep/drop** |

C proxies **no publisher at all** — there is nothing to migrate to, so the only
move is one line of config.

Measured on `solutions v6`, 8 cycles, sub-300-char rows:

| pop | short | surfacing | **surfacing rate** | /cycle |
|---|---|---|---|---|
| A | 3,736 | 109 | 2.9% | 13.6 |
| B | 1,715 | 21 | 1.2% | 2.6 |
| **C** | **137** | **22** | **16.1%** | 2.8 |
| non-GN | 2,023 | 21 | 1.0% | 2.6 |

```
today                       21.6 surfacing rows/cycle
after ADR-007 (A gone)       8.0
after ADR-007 + dropping C   5.2
```

**C is 13× the non-GN surfacing rate off the smallest population, and supplies
34% of everything surviving ADR-007** — so dropping 13 feeds is worth roughly
what the entire 230-feed repoint migration is. Probably mechanistic rather than
luck: LD#92's defect is the student reading a title dense in solution vocabulary
with no subject to ground it, and a topic-query feed emits exactly that by
construction. Predicts the rate persists after any migration.

**Two errors of mine here, both caught by the FluxusSource session.** First I
posted 2.6/cycle by counting only non-GN, assuming retirement clears GN broadly
— understated 3×. Then I merged C into B, because I split on "not `gn_*`".
Offsetting the first: H4 measured **0 of 14,198** GN-proxy rows ever enriched
(pre-enrichment fetches from `url`; a GN `url` is a redirect), so migration
converts part of the population into >300-char articles rather than deleting it.
Of what remains, cap 3.50 would bind ~2.5/cycle — and
they are named outlets with short RSS (`automotive_electrive` 6, `china_cgtn`,
`nyt_world`, `trt_world`, `observador`), not broken-proxy stubs, so not what
#92 measured.

**The verdict rests on 1–2 above plus the one-feed finding — NOT on "too thin to
fit", which the 3× correction weakened and which I withdraw as the primary
ground.**

**Do not gate the re-measure on "migration complete" — there is no near-term
done.** FluxusSource expects GN-URL volume to step down as country-proxy batches
land, then plateau well above zero; the next ~29 are blocked on a real defect in FluxusSource's
`gn_to_native_upgrade.py` (it ranks candidate publishers by frequency in GN
output, which the bare-country-name collision corrupts — it proposed a football
site for Algeria over `aps.dz`). Gate on **measured GN-URL share per cycle**
instead. #95 stopped being a blocker on 08-06 (noise band shipped).

**Match GN on `news.google.com` in `url`, never on the `gn_` source prefix** —
the prefix identifies only the country-proxy subset and under-counts GN feeds
~5:1 in config (302 GN-URL feeds enabled, 59 of them `gn_*`). This supersedes
the "use the union" note below.

The trap for next time: the issue's own comment already said "a cap fitted
before the GN decision would be tuned against a population that is about to
change size." I sized it first and checked that second. **When a prior comment
names a sequencing precondition, verify it is satisfied before doing the work,
not after.** A decision being *taken* is not the precondition — the corpus
changing is, and here it was changing *while I measured*.

**The `gn_*` prefix is NOT a GN detector.** In `collection_20260808_120948`,
**202** items carry a `gn_*` source but **441** carry a `news.google.com` URL.
The gap is not a migration artifact and never resolves: it is two naming
conventions — 59 country proxies named `gn_*`, and 243 publisher-named feeds
repointed at GN. **`news.google.com` in `url` is the reliable signal**; the
prefix identifies only the retirement target. I used the union and reported it
as "GN", which conflated a population being retired with one that is not — the
direct cause of the 3× residual error above.

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

The 2026-08-08 comment left an encoded criterion rather than a date: *gate on
measured GN-URL share per cycle, matching `news.google.com` in `url`*. Ran it.

**GN-URL share has not moved: 24.1% (67 cycles before the first ADR-007 migration
batch) → 25.1% (18 cycles after)**, pooled over 301k items in NexusMind
`data/raw`. Per-cycle it ranges 15.7–39.0% with no trend.

That is **not** evidence ADR-007 stalled — 6 migrated feeds against 311 remaining
GN URLs predicts a flat population. See [[google-news-corpus-hypotheses]].

**The decisive ground survives a window twice the original size.** "Nothing short
reaches `medium_high`, so any cap ≥ 5.0 is a no-op": over the 16 cycles since
`content_length` reached 100% population, `solutions v6` short rows are n=13,406,
**max raw 4.878, zero at or above 5.0**. Previously 4.93 over 8 cycles.

**Verdict unchanged: do not set `short_content.cap`.** The mechanism stays wired
and off.

Two things that did move:

- Short surfacing rows for `solutions v6` fell 25.4 → 18.2 per cycle, and **the
  only population that changed is B** (6.0 → 2.4/cycle), driven by one feed —
  `energy_utilities_google_news_energy_storage`, 20 → 4. Population A (16.8 → 13.2)
  and C (2.7 → 2.6) are flat. That is the "addressable at source" prediction from
  08-08 coming true without a cap being set.
- **`content_length` is now populated on 100% of rows in all six filters** — 0 nulls
  in 230,070 scored rows since the 2026-08-08 17:10 cycle. NM#300's fix holds, so
  `_apply_short_content_cap`'s silent-no-op hazard is no longer latent. A future
  flip still needs a binding check at the end of a real run.

**Same-instrument warning:** the before/after comparison used `len(content)` on the
persisted row, because `content_length` was 0% populated before 2026-08-08 17:10
and the stamped field would have compared two different quantities.

---

## 2026-08-23 — the floor measured by SCRIPT, both curves, 1,332,648 rows

Evidence: `docs/evidence/2026-08-23-length-floor-by-script.md`. Read-only, no spend.
Population: every `(id, filter)` pair in NexusMind `data/filtered/` (516 files, 8.8 GB).
Script classified **from the article text** (Unicode ranges) — *not* the `language` field,
which under-reports non-Latin because Asian/African/MENA publishers are acquired in their
English editions (FS#166).

### ⭐⭐ H-LF1 CONFIRMED — a flat CHARACTER floor is a different rule for every script

Chars/token, measured with the real Gemma-3-1B tokenizer on 220 production articles per
script: Latin **4.36**, Devanagari 3.27, Arabic 2.91, Cyrillic 2.88, Greek 2.61, Hebrew 2.15,
CJK 1.70, Korean 1.60, Japanese **1.53**. So a flat **300-char** floor demands **69 tokens of
Latin and 197 of Japanese — 2.85×**. ⇒ **Define any floor in TOKENS, naming its tokenizer,
and DERIVE the per-script character equivalents.**

### ⛔ H-LF2 REFUTED — "a character floor hits non-Latin hardest" (my own claim, same day)

At a flat 300 chars, **Latin loses 32.6%** against Japanese 4.0%, Arabic 8.7%, Devanagari
0.7%. Latin is bimodal (p1 62, p25 130, median 1,310). ⚠️ **Most likely the Google News
headline-echo population — NOT VERIFIED, `source` was not captured.**
**Both are true of different quantities:** *information demanded* is harshest on CJK;
*rows lost today* is harshest on Latin.

### ⭐⭐ H-LF3 CONFIRMED — the case for a QUALITY floor is weak; it is a COMPUTE lever

- **The scorer already suppresses short text.** On `stage2` rows, share reaching 4.5 runs
  **2.1% at 0–32 tokens vs 8.8% at 384+** — a 4× gradient nobody configured. And **variance is
  LOWER at short lengths** (sd 1.06 vs 1.55): short text is not scored *unreliably*, it is
  scored *low*, which is mostly correct.
- **31% of the corpus is already excluded.** `stage1_low` = 414,276 rows scoring **0.0% ≥ 4.5
  in every token band**. A large share of any floor's "cost" is rows the probe already removed
  — pure compute saving, zero reader effect.
- **The exchange rate:** a 128-token floor drops **36.64% of the corpus** to remove **16.23%
  of surfacing rows** (9,463 of 58,291) **of unknown quality**.
- **The short-surfacing problem is Latin-only:** 12.0% of Latin surfacing rows are <64 tokens
  vs **0.0%** for Japanese/CJK/Devanagari/Other. ⇒ **the targeted fix is the GN population
  (ADR-007), not a global floor.**

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
