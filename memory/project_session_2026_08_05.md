---
name: project_session_2026_08_05
description: LD#92 identified (two discriminating tests + second oracle), review-changes skill adopted and immediately caught four of my own errors, GN measured as the stub source, ovr#299 filed
metadata:
  type: project
---

# Session 2026-08-05

## Headline

**LD#92 is identified.** `solutions v6` really does over-score sub-300-char
content; it is not the selection artifact the 2026-08-02 review showed could
reproduce it. The cap value is still blocked — on **#95**, not on #92.

## What was verified, measured and shipped

### 1. The 2026-08-02 12:0x CEST cycle — all checks PASS

The one Batch A.6 had left open. Not today's cycle: the baselines in the ask
(7713 / 7800 / 7898) are 08-02's 00:12 / 04:13 / 08:14 runs. Cycles are 4-hourly,
starting :07–:11.

- 132/132 shadow lines carry `contract=title+content` **and** `pre_source_filter=true`
- `INCOMPLETE(inert:…)` on exactly 4 filters — belonging/cultural_discovery/uplifting `(url)`, investment_risk `(source)`
- no `declared=` on nature_recovery or solutions (investment_risk has none either; it never declared one)
- **zero HTTP 422s** in the cycle and none since 2026-08-02 06:58 UTC
- 7 `NM#244: clamping title` WARNINGs — one article, 1999→1000 chars

Two corrections worth keeping:

- **The clamp WARNINGs are on sadalsuud, not gpu-server.** `_clamp_article` lives
  in `src/scoring/gpu_client.py`, the client side. Grepping the gpu-server
  journal returns zero, which reads as "the fix never fired".
- **The commerce check passes, but not as framed.** `N commerce` is
  `stats['commerce_blocked']`, which the enforce key does gate — so it is the
  right signal — but it is a *cumulative* count over a rolling window. The
  meaningful test is "does it keep incrementing", not "does the delta match".
  The cited baseline deltas (+87/+98) are ranks 4 and 5 of 29 across
  07-30→08-03, the quietest stretch in five days. Target cycle's +162 is the
  exact median; pre-deploy median +158.5, post +162.0. **No level shift.**

### 2. LD#92 — identified (the session's main result)

The n=15 and n=60 harnesses were **never committed**, so the sampling half had to
be rebuilt from the production corpus. That rebuild was the most expensive part
of the day and is the reason the fixture is now committed.

Three designs, n=80/arm, 456 articles, `deepseek-chat`, 0 errors, 0 scrape-junk
skips. Predictions written into the sampler **before** any oracle call.

| design | arm depth ratio | DiD | cluster 95% CI | cluster p | +Holm |
|---|---|---|---|---|---|
| D1 both arms `raw >= 2.25` | 0.50 | −0.790 | [−1.29, −0.28] | 0.0032 | 0.0032 |
| D2 both arms `raw >= 4.00` | 0.19 | −0.861 | [−1.34, −0.38] | 0.0006 | 0.0012 |
| D3 top 2.3% **within** each arm | 1.00 | **−1.119** | [−1.61, −0.61] | <5e-5 | <1.5e-4 |

The artifact predicted **D2 markedly more negative** (severity worsens 0.50→0.19)
and **D3 → 0** (severity equalised). Observed: D2 moved −0.071, and D3 is the
*largest*. Unchanged with the gatekeeper off — which independently corroborates
**#94**, it never binds. Survives dropping the `smart_compress`-truncated long
rows (D3 −1.024).

**Second oracle confirms.** `gemini-2.5-flash` on the same D3 sample (160/160, 0
errors): **−1.351** [−1.73, −0.96]. The two disagree per article (mean |diff|
1.18) and gemini is more generous on *both* arms (2.80/4.95 vs 2.40/4.31) —
different absolute bias, same gap. That is what DiD exists to produce, and it
kills "the judge penalises short input".

At matched depth the oracle puts **35.0% of the short arm below op-point vs 5.0%
of the long arm**, across 55 distinct sources in 80 rows.

**Residual, still an assertion not a measurement:** matched percentiles equalise
selection *severity* but not *noise* (short-arm MAE ratio 1.91×). D2 is the
independent check and it barely moved. Sizing it properly means re-running the
08-02 simulation under matched-percentile selection.

Committed: `scripts/diagnostics/ld92_{build_pool,sample_designs,analyze_did,crosscheck}.py`
and `tests/fixtures/ld92/` (456 + 160 rows + design; article bodies stripped, 1.0 MB).

### 3. `review-changes` skill adopted — and it earned its keep immediately

llm-distillery was pinned at framework **v1.10.6**, four releases behind, and was
the only active repo without a pre-commit review skill. Now at **v1.14.0**.

**Re-mapped, not copied.** The template's tiers key on the framework's own paths
(`templates/*`, `docs/GUIDE.md`, `tests/lint/*`); installed verbatim every change
here would fall through to LOW and the skill would quietly do nothing — this
repo's own signature defect. Three lenses are ours: **reachability** (trace the
call path, confirm the gate's input exists), **claim-verification** (measured vs
inferred, denominator exclusions, the #95 noise floor, and the
permutation/multiplicity/clustering/selection set), **sync-safety**.

Its first run found five real defects, **four of them mine from earlier the same
day** — including p-values I had publicly flagged as wrong and then pasted into
memory anyway. None changed a conclusion; all were errors in how evidence was
stated. Checked v1.11–v1.14 for other adopter gaps: none apply (v1.13.0's
`curate` Step 0.2 fix needs a gitignored `memory/`; verified with
`git check-ignore` that ours is tracked).

### 4. Google News is the stub source — evidence into FS#120

Measured over 149,075 scored `solutions v6` articles (80 cycles):

- **GN is 14–17% of articles but 48–56% of all sub-300-char stubs** — ~3×
  over-represented, measured within-period so it needs no before/after claim.
- Pre-enrichment *is* working: 3,130 candidates → 1,929 replaced, 702
  quality-rejected, 499 failed (~62% rescued). It fires below **500** chars, not
  300 — the net is not too small. GN residue persists because a GN item's `url`
  is a `news.google.com/rss/articles/CBMi…` redirect, so the fetcher retrieves
  Google's redirect page.
- 72.7% of stubs are under 120 chars; median 95. Stubs are 19.7% non-English
  (long articles are 46.2%) — so stubs skew *English*, and the
  "non-English readers need this" argument is weaker for stubs than for the
  corpus.

Posted to **FS#120** with a suggested checklist addition: **enrichable rate** per
candidate per country. Retiring GN drains three separately-measured problems at
once — the LD#92 stub population, the ovr#299 summary population, and part of
Chain 14. FS#120 is the only calendar-bound item on the board (~2026-08-14).

### 5. ovr#299 — summaries of headline-only articles are mostly invented

`src/lib/summarization.ts` validates the **output** thoroughly and never checks
the **input** had enough to summarise. Measured over all 18,756 summaries,
English sources (novel-word rate = share of summary content words absent from
content *and* title):

| source length | n | med source | med summary | summ÷src | novel-word rate |
|---|---|---|---|---|---|
| <120 (headline) | 13 | 108 | 1,159 | 10.7× | **83.4%** |
| 120–299 | 76 | 181 | 968 | 5.4× | 73.9% |
| 300–999 | 399 | 600 | 875 | 1.5× | 54.2% |
| 1000+ | 10,994 | 4,229 | 1,065 | 0.25× | 31.6% |

**The mechanism, and the owner called it before the measurement did:** median
summary length is 1159/968/875/1065 while input spans 108→4,229 chars. A 40×
range in, 1.2× out. The model has a fixed length target and fills to it —
compressing an article, *generating* the difference from a headline. So the lever
is the **output budget as a function of input length**, not prompt wording.

Scale is small: 163 of 18,756 (0.9%), because stubs rarely clear the scoring bar.
It matters because `/accountability` tells publishers the summaries are "original
words".

**My recommendation to skip the summary for stubs was wrong and the owner
overruled it correctly** — for a non-English article the summary is the reader's
only way in, and refusing would land hardest on exactly the population Chain 14
says is already disadvantaged. Non-EN rows also cannot be read with this metric
(87.8% even for full articles — a translation baseline).

Filed **ovr#299**; audit script `scripts/summary-invention-audit.ts` on branch
`measure/summary-invention` (`aea369c`, pushed).

## Gotchas added

`pgrep -f` over ssh **recurred twice** (3rd occurrence — treat as unusable, go
straight to `ps -eo pid,etime,args | grep -v grep`); a NUL byte written into a
`.ts` made git call it binary *and* concealed a real bug; `git commit --amend`
under husky/lint-staged created a child commit and swept another session's file;
harness committed but data not; a function call inside a list-comprehension
condition re-ran per element.

## State at close

- llm-distillery `main` pushed through `c55212d` (6 mine + 1 from a parallel session)
- ovr.news branch `measure/summary-invention` pushed; `docs/BRAND.md` left as
  another session's uncommitted work
- Issues touched: **LD#92** (2 comments + 1 amendment), **FS#120**, **ovr#299** (new)

## Next

1. **FS#120** — deadline ~2026-08-14, and today's evidence strengthens retiring GN.
2. **Batch F.1 / #95** — pin the production batch size; the only remaining blocker on the solutions cap value.
3. **LD#86** (`TOPIC_GATE_PATTERNS` multilingual coverage) and **NM#286 item 3 → LD#82** — untouched, independent, both gate the violence enforce flip.

## Related

- [[prefilter-length-floor-hypotheses]] — hypothesis 5 now says identified
- [[score-batch-shape-noise]] — #95, the remaining blocker
- [[cross-repo-prioritization]] — Chain 4, Chain 13, Chain 14
- [[gotcha-log]] — five new entries, one recurrence
