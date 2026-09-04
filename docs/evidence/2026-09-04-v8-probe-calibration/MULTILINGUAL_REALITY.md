# Is the e5 probe actually multilingual and multi-script? — three layers, three answers

**2026-09-04. $0.** Asked because the probe is now the *only* layer carrying multilingual
selection: the Latin-script keyword prefilter was dropped (ADR-018/019 *Amendment
2026-08-21*) and the multilingual e5 probe replaces it (ADR-011).

**The question has three layers and they do not have the same answer.**

| layer | verdict |
|---|---|
| the **encoder** — can it read these scripts at all? | ✅ **yes, verified** |
| the **routing** — does it screen non-Latin harder? | ⛔ **yes, measurably** |
| the **ranking** — is it worse at non-Latin *judgement*? | ⚠️ **not measurable**, 2 positives |

And a fourth thing fell out that nobody was looking for, in §4: **the student is hit harder
than the probe.**

---

## 1. The encoder is genuinely multi-script — verified, not assumed

The corpus contains **10 scripts**. Census over all 6,590 rows by dominant script:

| script | rows | share | languages |
|---|---|---|---|
| Latin | 5,981 | 90.76% | en 3459, es 605, de 473, fr 333 |
| Greek | 180 | 2.73% | el |
| Arabic | 155 | 2.35% | ar |
| Cyrillic | 111 | 1.68% | ru 65, mk 43, kk 3 |
| Hangul | 77 | 1.17% | ko |
| CJK | 44 | 0.67% | ja 29, zh-cn 13 |
| Devanagari | 20 | 0.30% | ne 18, hi 2 |
| Hebrew | 12 | 0.18% | he |
| Armenian | 7 | 0.11% | hy |
| Hiragana | 3 | 0.05% | ja |

`intfloat/multilingual-e5-small` uses an XLM-R sentencepiece vocabulary of **250,002**
tokens. Tokenising an equivalent sentence in each of the nine scripts present:

**Zero UNK tokens in any script, and every sample round-trips losslessly** (6–14 tokens per
sentence — no script is being shredded into bytes). ✅ **The encoder can read all of it.**

## 2. But the routing is measurably harsher for non-Latin

Pooled over both held-out splits at the adopted 1.75 threshold, design-weighted:

| | routing to Stage 2 |
|---|---|
| Latin (n=1,187) | **0.8979** |
| non-Latin (n=131) | **0.8218** |

**Gap 0.0762, z = 2.65** (unweighted 0.0693, z 2.53; both SEs binomial and so optimistic —
measured Kish deff 1.068 → z 2.45). This one **has power**, because it is computed over all
131 non-Latin rows rather than over its positives.

## 3. ⚠️ Whether it *judges* non-Latin worse is NOT measurable here

Probe AUC by script on the test split reads **0.8901 Latin vs 0.5608 non-Latin** — which
looks damning and is very nearly meaningless: **the non-Latin group holds 2 positives.** An
AUC over 2 positives is the average rank of two items; its confidence interval spans most of
the range. The student's 0.9730 on the same 2 rows is equally uninformative.

⛔ **Do not quote either number as evidence.** llm-distillery#141 is the blocker — only 27
non-Latin positives with native text ≥1,000 chars exist in the window — and it blocks
**H-V8-10** for the same reason.

## 4. ⭐⭐ The mechanism nobody was looking for: truncation is script-dependent

Non-Latin articles are **shorter in characters** and yet produce **more tokens**, so more of
each one is cut at the 512-token limit. Measured over the whole 6,590-row corpus:

| tokenizer | group | median tokens | % truncated at 512 | **median share of the article the model sees** |
|---|---|---|---|---|
| e5-small (the probe) | Latin | 586 | 56.7% | **87.4%** |
| e5-small | non-Latin | 694 | 64.6% | **73.8%** |
| **Gemma-3-1B (the student)** | Latin | 574 | 55.0% | **89.2%** |
| **Gemma-3-1B** | non-Latin | **843** | **74.1%** | **60.7%** |

Median characters: Latin 2,434, non-Latin 2,222 — the non-Latin articles are *shorter*.
Efficiency: e5 gets **4.25 chars/token** on Latin and **3.48** on non-Latin, a 22% penalty.

⭐ **And Gemma is worse at this than e5**: 843 tokens against e5's 694 for the median
non-Latin article. **So the student sees ~61% of a median non-Latin article against ~89% of a
Latin one — a 28-point gap, twice the probe's 14.**

### Why this matters

- It is a **third mechanism**, distinct from the two `H-V8-10` weighs. That hypothesis asks
  whether the non-Latin gap is a *scoring* property or a *collection* property. This is
  neither: it is **truncation**, it is mechanical, and it applies to every non-Latin article
  regardless of how it was collected or scored.
- It is a **third thinning** of non-Latin content, after the 300-char labelling floor and the
  low scores recorded in #128.
- ⚠️ **It reframes `H-V8-15` arm (b) (`--use-head-tail`).** Head+tail keeps 256 from each end
  — it does **not** show the model more tokens (still 512), but it stops the entire tail of
  the most-truncated articles being invisible, and those are disproportionately non-Latin. It
  is a candidate multilingual fix, not only a general one. ⛔ Not a volume fix, and this is
  not a claim that it works — it is a reason to measure the arm *split by script*.

⚠️ **What this does not establish.** That truncation *causes* the routing gap. Both are
measured; the causal link is not. A test exists and is cheap: compare routing between
non-Latin rows that fit under 512 tokens and those that do not. It needs no new labels.

---

## Summary

**The probe is multilingual in the sense that matters least and is under-evidenced in the
sense that matters most.** The encoder reads all ten scripts cleanly. The routing is
measurably harsher for non-Latin. Whether the *judgement* degrades is unmeasurable at 2
positives — and the newly-measured truncation asymmetry says the **student**, not the probe,
is the component losing the most non-Latin content.

## Reproduce

Corpus script census: `phase_c_outcome.py`'s sibling analysis in this directory's README.
Tokenizer coverage and truncation: the two scripts are short enough to inline, and both need
`venv-prodparity` on `b650-gpu` (the corpus is gitignored, #97, and `sentence-transformers`
is not installed in the repo's `.venv`). Routing gap: `script_routing_gap.py` →
`routing_gap.txt`.
