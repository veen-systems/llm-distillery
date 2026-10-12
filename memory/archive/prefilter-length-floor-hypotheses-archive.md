# Prefilter & length-floor hypotheses — archive of closed entries

*Moved VERBATIM from `memory/prefilter-length-floor-hypotheses.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the
read surface), under the 2026-09-27 ledger rule: an entry whose verdict opens REFUTED / CONFIRMED / MOOT moves; open
entries and live decisions stay. Order kept; a block from inside a section repeats that section's heading. Hypothesis
5's executable verify annotation is ALSO kept in the live file, because the default verify run does not read this
folder.*

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
   #95's |Δ| ≤ 0.16 noise floor (Batch F.1 first — `archive/cross-repo-prioritization-archive.md`). Identification is cleared;
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

## Open questions  *(context heading, repeated)*

9. **Does extending `TOPIC_GATE_PATTERNS` close LD#86's per-language spread?**
   Now a sharp question rather than a demographic one: the gap is entirely
   `no_cultural_topic_signal`, and German (4.9%) and French (5.3%) already sit
   *below* English (13.0%) while Italian (28.6%) and Korean (37.5%) sit well
   above — consistent with keyword coverage, not with language per se.
   Falsification: extend the keyword set for the poorly-covered languages, re-run
   NexusMind's prefilter recall-cost script, and check whether the per-language
   rates converge. If they do, the residual 15.5% is genuine editorial blocking
   and enforcement can be re-argued on its merits.
   ⛔ **MOOT since 2026-10-01:** decision 0 deleted every per-lens prefilter, so there is no enforcement left to
   re-argue, and the recall-cost script is gone from both repos (flagged by the default refcheck 2026-10-02).

## 2026-08-23 — the floor measured by SCRIPT, both curves, 1,332,648 rows  *(context heading, repeated)*

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

