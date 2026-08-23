# A minimum-length floor: measured by script, over 1,332,648 production rows

**2026-08-23. Read-only, no spend.** Population: every `(id, filter)` pair in NexusMind
`data/filtered/*/filtered_*.jsonl` — 516 files, 8.8 GB. Script classified **from the article
text** (Unicode ranges), not from the `language` field, because Japanese mixes kana and Latin,
Serbian appears in both alphabets, and FS#166 established that Asian/African/MENA publishers
are largely acquired in their **English editions** — so `language` systematically
under-reports non-Latin.

⚠️ **What this population EXCLUDES:** source-type-excluded rows, and anything the per-lens
prefilter blocked in the oracle/training path. It is the post-prefilter scoring population —
the right denominator for *"what would a floor cost us"*, and the wrong one for *"what does
the collector see"*.

---

## 1. ⭐⭐ A flat character floor is 2.85× stricter on Japanese than on English

Chars-per-token measured with the **actual Gemma-3-1B tokenizer** (`GemmaTokenizerFast`,
vocab 262,144) on 220 real production articles per script:

| script | chars/token | what a flat **300-char** floor really demands | vs Latin |
|---|---|---|---|
| Latin | 4.36 | 69 tokens | 1.00× |
| Devanagari | 3.27 | 92 tokens | 1.33× |
| Arabic | 2.91 | 103 tokens | 1.50× |
| Cyrillic | 2.88 | 104 tokens | 1.51× |
| Greek | 2.61 | 115 tokens | 1.67× |
| Hebrew | 2.15 | 139 tokens | 2.03× |
| CJK | 1.70 | 177 tokens | 2.57× |
| Korean | 1.60 | 187 tokens | 2.72× |
| **Japanese** | **1.53** | **197 tokens** | **2.85×** |

**A single character number is a different rule for every script.** This is the argument for
defining the threshold in **tokens** and deriving characters, not the reverse.

## 2. ⛔ But the raw drop rates run the *opposite* way, and that corrects me

I warned this morning that a character floor would fall hardest on non-Latin content. **On
this corpus it does not** — at a flat 300 chars:

| Latin | Japanese | Arabic | Korean | Devanagari |
|---|---|---|---|---|
| **32.6%** dropped | 4.0% | 8.7% | 9.0% | 0.7% |

Latin's percentiles are bimodal — p1 **62**, p10 **83**, p25 **130**, median **1,310** — a
huge short tail under a long body. ⚠️ **Most likely the Google News headline-echo population**
(recorded as 100% sub-300-char), i.e. an artifact of one source, not a property of the
language. **NOT VERIFIED HERE — the scan did not capture `source`.** Check before relying on it.

**Both statements are true and they are about different things:** *information demanded* is
harshest on CJK (§1); *rows lost on today's corpus* is harshest on Latin (§2, artifact).
A token floor fixes the first. Only removing the GN population fixes the second.

## 3. ⛔ Hebrew is not a threshold question — it is a defect

| | median length | dropped at 128 tokens (275c) |
|---|---|---|
| Hebrew | **202 chars** | **77.0%** |
| every other script | 554–2,829 chars | 0.8%–38.4% |

9,282 rows whose median is 202 characters. That is a stub-publishing source or an extraction
failure, and **any floor at all silently deletes almost all Hebrew content**. Investigate
before setting a number — do not let a threshold quietly resolve it.

## 4. The decision table

% of each script dropped, applying the per-script character equivalent of one token floor:

| script | 64 tok | 96 tok | **128 tok** | 160 tok | 192 tok |
|---|---|---|---|---|---|
| Latin | 32.3% | 35.4% | **38.4%** | 40.8% | 42.9% |
| Greek | 7.8% | 8.0% | **8.2%** | 8.7% | 9.7% |
| Arabic | 6.0% | 8.5% | **8.9%** | 9.5% | 10.4% |
| Cyrillic | 2.9% | 3.2% | **8.1%** | 15.7% | 24.8% |
| Korean | 0.4% | 1.2% | **2.3%** | 5.3% | 9.3% |
| Hebrew | 14.1% | 52.9% | **77.0%** | 80.9% | 81.2% |
| Japanese | 0.0% | 0.7% | **0.8%** | 0.8% | 3.8% |
| CJK | 1.7% | 9.6% | **12.8%** | 15.2% | 19.6% |
| Devanagari | 0.0% | 0.7% | **2.1%** | 6.5% | 10.3% |
| **corpus-wide** | 30.3% | 33.6% | **36.6%** | 39.0% | 41.1% |

## 5. ⛔ What this measurement does NOT establish

**This is the COST curve. It is not the BENEFIT curve.** It says what each floor throws away;
it says nothing about *below what length a score stops being meaningful*. **Picking the number
needs the other half** — score reliability vs length — and that has not been measured.

⚠️ Do not read "36.6% dropped at 128 tokens" as a recommendation. It is a price tag with no
product attached yet.

## 6. Recommended shape

- **One authoritative constant, in tokens, naming its tokenizer** — Gemma-3-1B's, because the
  gate exists to protect the scorer and Gemma is what consumes the text.
- **Per-script character equivalents are DERIVED**, for cheap upstream checks where loading a
  tokenizer is impractical. Set them *conservatively loose*: a loose upstream approximation
  costs a little compute, a tight one silently loses articles.
- ⛔ **Do not copy the constant into three repos.** The op-point already lives in four places
  and drifted off in both NM#161 and NM#205. Propagate it as **data** on the row/contract so
  NexusMind and ovr.news *read* it; if it must be duplicated, add a test that fails when the
  copies disagree, as `test_normalization_invariant.py` does for `raw_min`.
- **Shadow first (ADR-022):** stamp the token count always, one config-gated drop point,
  enforcement is a config flip. **Measure recall before the flip (ADR-021).**
- ⚠️ **This reopens #93**, which removed exactly this check from the scoring path on the
  grounds that the floor guards *oracle-prompt* framework leakage and the student sees no
  prompt. **#114 records that this rationale was never measured.** Reopening is legitimate —
  do it knowingly, and settle #114 in the process.

## 7. The three thresholds this must not merge

1. **Scoreability** — protects the scorer. The subject of this document.
2. **Labelling validity** — the #93 300-char oracle floor. A property of the *prompt*, on a
   *different tokenizer*. Keep separate.
3. **Display usefulness** — ovr.news needs enough text to summarise. A *consumer* requirement;
   enforcing it in NexusMind couples the producer to one consumer, and the standalone
   oracle-only outlets would not share it.

---

# Part 2 — the benefit curve. **The case for a quality floor is weak.**

Same population, adding `stage_used` and `raw_weighted_average`. This is the half §5 said
was missing.

## 8. The scorer already suppresses short content, on its own

`stage_used = stage2` rows only — real Gemma scores, not probe estimates:

| tokens | n | mean | sd | **% ≥ 4.5** |
|---|---|---|---|---|
| 0–32 | 207,493 | 1.13 | 1.06 | **2.1%** |
| 32–64 | 52,188 | 1.35 | 1.24 | 4.1% |
| 96–128 | 26,939 | 1.47 | 1.38 | 6.3% |
| 256–384 | 71,887 | 1.50 | 1.38 | 5.9% |
| 384+ | 460,340 | 1.73 | 1.55 | **8.8%** |

**A short article is already ~4× less likely to reach the op-point than a long one**, and the
model produces that without being told. ⚠️ Note what this is *not*: it is not evidence that
short scores are **unreliable**. Variance is *lower* at short lengths (sd 1.06 vs 1.55), not
higher. The scorer is not confused by short text — it scores it low, which is mostly correct.

## 9. ⭐⭐ A third of the corpus is already excluded, and it can never reach a reader

`stage_used = stage1_low` — **414,276 rows, 31% of the corpus** — scores **0.0% ≥ 4.5 in
every single token band**, capped around 1.4 by construction. The e5 probe already screened
them out.

So a large share of any floor's "cost" is rows that were **already removed**. Dropping them
saves compute and changes nothing a reader sees.

## 10. The exchange rate, which is the actual decision

Reader-visible population = `stage2` **and** ≥ 4.5: **58,291 rows, 4.37% of the corpus.**

| token floor | surfacing rows removed | % of surfacing | corpus rows dropped | % corpus |
|---|---|---|---|---|
| 32 | 4,355 | 7.47% | 321,933 | 24.16% |
| 64 | 6,479 | 11.11% | 404,003 | 30.32% |
| **128** | **9,463** | **16.23%** | **488,295** | **36.64%** |
| 256 | 13,419 | 23.02% | 602,402 | 45.20% |

⛔ **And the short-surfacing problem is essentially Latin-only:**

| script | % of its surfacing rows under 64 tokens |
|---|---|
| **Latin** | **12.0%** (6,303 rows) |
| Greek | 5.0% | 
| Arabic | 4.3% |
| Hebrew | 2.7% |
| Cyrillic | 0.9% |
| Korean | 0.1% |
| **Japanese / CJK / Devanagari / Other** | **0.0%** |

## 11. Conclusion — this argues *against* a global quality floor

1. **A length floor is mostly a COMPUTE optimisation, not a quality gate.** 31% of what it
   would drop is already screened by the probe and could never surface.
2. **Its reader-facing effect is to remove 16.23% of surfacing rows at 128 tokens — of
   UNKNOWN quality.** Nothing here says those 9,463 rows are junk. Some short articles are
   good. **ADR-023 cuts against a blunt cut**: the false negative is invisible and the slot
   refills, but 16% is not a rounding error.
3. **The targeted intervention is the Google News population, not a global floor.** The
   short-surfacing rows are 12.0% of Latin and ~0% of every dense script — the signature of
   one source's headline echoes, already retired in principle by ADR-007.
4. **If a floor is wanted for cost/compute reasons, that is a legitimate and different
   argument** — and then it should be justified on inference spend, not on quality, and set
   low (32–64 tokens) where the surfacing cost is 7–11%.

## 12. ⚠️ Limitations

- **A single 4.5 op-point was used for all six filters.** They differ (`solutions` is 2.25,
  `investment_risk` 4.25). So 58,291 **understates** the true reader-visible population, and
  the per-filter short-row share may differ. Re-run per filter before acting.
- **`source` was not captured**, so the Google News attribution in §2 and §11.3 is inference
  from the length signature, not measurement.
- Chars-per-token rests on 220 sampled articles per script; Thai (12) and other Indic (2)
  had too few and are excluded entirely.
