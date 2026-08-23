# 2026-08-23 — Gate A measured on two oracles; the length floor measured both ways

**Spend $0.4711.** Nothing trained, nothing sent anywhere, nothing deployed. Nine commits.

Evidence: `docs/evidence/2026-08-23-gate-a-two-oracle-run.md`,
`docs/evidence/2026-08-23-length-floor-by-script.md`,
`docs/evidence/2026-08-23-no-regression-set-and-local-judge.md`.
Hypotheses: `memory/uplifting-oracle-genre-hypotheses.md` (H-UP11..14),
`memory/prefilter-length-floor-hypotheses.md` (H-LF1..4).

---

## 1. The DeepSeek comment on #103 — not DeepSeek, and the anchor was mine to fix

An outside account (`xyzs996`, `author_association: NONE`) posted rates and arithmetic on
#103. **Rate table verified correct** against the vendor page — which settled the
two-disagreeing-sources caveat that had stood since 08-16, and confirmed **weekends bill
off-peak** ("Monday through Friday"). Replied on the issue.

⛔ **Its "dead heat" conclusion was closer to right than mine.** I argued output length was
the single decider and anchored on ~1,174 tokens back-solved from the cd v5 invoice. **Measured
in this session's own DeepSeek run: 349 output tokens/article, and 0% cache hit** against an
assumed 14%. There are **two** unmeasured parameters and they pull opposite ways — at 349
output, DeepSeek *wins* on the assumed cache rate ($0.001752) and *loses* on the measured one
($0.001990). Conclusion (Gemini Batch) survives; my reasoning for it did not.
⛔ **Output length is prompt-specific** — cd v5's invoice is arithmetically inconsistent with
349 — so oracle choice is a per-filter measurement, not a project default.

## 2. Phase A drafted, then measured

Two drafts, spliced into `filters/human_thriving/v8/prompt-candidate.md`:

- **Step 2b** — `evidence_level` becomes two questions in order, Q1 a gate: did an outcome for
  people occur? LIVE / DELIVERED / REACHED SOMEONE. Any failure → 0–2, gatekeeper caps at 3.0.
- **Step 1** — dominant subject over best fragment; *harm answered is not harm undone*;
  benefit must reach **people**.

⭐ **Found while writing step 1: v7's own STEP 1 already covers 8 of the 9 class-A rows** —
*"Individual arrest/sentencing → NOISE"*, *"Doom-framed content"*, *"Professional knowledge
sharing"*. Same shape as the §1h gatekeeper finding: **a rule that exists and is not followed**,
not a missing rule.

### Gate A result — 15 rows × k=3 × 2 prompts × 2 oracles, 0 errors

| | DeepSeek | Gemini |
|---|---|---|
| Class A (blocking) | 4/9 → **7/9** | 4/9 → **6/9** |
| Class B (reported) | 1/3 → **3/3** | 1/3 → **3/3** |
| No-regression (blocking) | 1/3 → 1/3 | 2/3 → 2/3 |

- ✅ **Step 2b is validated on both oracles.** Dawn 5.98 → **3.00** / 7.36 → **1.60**; TSA
  4.63 → **2.53** / 5.53 → **0.00**. The 3.00 is `GATEKEEPER_CAP` firing.
- ⛔ **Step 1 is not ready — the oracles disagree by 4.4 points** on the worst row. *"Five men
  arrested for raping a minor"*: DeepSeek **7.05 → 3.00** (capped), Gemini **7.23 → 7.43**
  (*rises*). ⭐ **This decides Phase B's open oracle question.**
- ⛔ **Criterion 2's bars are broken and v7 proves it** — v7 also fails the no-regression set.
  Unifesp passes its **delta** on both (+0.77, +0.13) ⇒ transitional justice **not** suppressed.
- ⛔ **v8 caps the Rwanda row to 3.00 on both oracles, behaving exactly as written** (mobilised
  funding is *announced, not delivered*). **Owner call**, same boundary as delivered
  accountability: *what counts as delivery.*

## 3. The §5b no-regression set existed only as prose

Three gates reference it — step A5, Gate B-C, and acceptance **criterion 2 (BLOCKING)** — and
none could execute it. Assembled as `datasets/adverse/uplifting_no_regression.jsonl`.
⛔ **Three articles, not four**: the fourth row's only instance is one of the 18 **accepted
adverse rows**, carrying a scope warning. Two of three had aged out of every JSONL on
sadalsuud; they survive in **`ovr.db`'s `articles` table**.

⭐ **It killed a wrong conclusion of mine within the hour**, which is what a blocking control
is for.

## 4. The length-floor question (owner)

Measured over **1,332,648 rows**, script classified from the text.

- ⭐⭐ **A flat char floor is 2.85× stricter on Japanese than Latin** (chars/token 4.36 vs 1.53)
  ⇒ **define any floor in TOKENS**, naming its tokenizer; derive char equivalents.
- ⛔ **But the quality case is weak.** The scorer already suppresses short text 4× (2.1% vs
  8.8% reach 4.5), **variance is *lower* at short lengths**, and **31% of the corpus is already
  probe-screened** (`stage1_low` = 0.0% ≥ 4.5 in every band). A 128-token floor costs **36.64%
  of corpus to remove 16.23% of surfacing rows of unknown quality**.
- ⭐ **The real target is the Google News population, not a global floor** — 12.0% of Latin
  surfacing rows are <64 tokens vs **0.0%** for Japanese/CJK/Devanagari.
- ⛔ **#128 filed: Hebrew median 202 chars, 77% would fall to any floor** — a defect, not a
  threshold question.
- ⛔ **Do not copy the constant into three repos** — the op-point already lives in four and
  drifted off in NM#161 and NM#205.

## 5. ⛔ Three retractions, all mine

1. **"qwen3:14b zeroing class A shows v7's prompt already handles them."** Its positive control
   shows it zeroes all three *true positives* too. A judge that scores everything zero is free
   to be right about the bad rows.
2. **"A character floor hits non-Latin hardest."** On this corpus Latin loses 32.6% at 300
   chars vs Japanese 4.0% — the Latin short tail is the GN artifact.
3. **The pricing anchor** (§1).

Plus one mis-specified assertion of my own, corrected an hour after writing it: the Unifesp
row's bar was absolute where its baseline was never established. **An absolute bar on a row
with no baseline measures the prompt family, not your change.**

## 6. Traps paid for

- **Every adverse row on disk is a 300-char excerpt** (originals 620–28,905). 9th occurrence
  of *establish what a source excludes*. Caught **before** the spend.
- **`gemini_api_key` is free-tier** — 429s, and **k=3 silently became k=1** on 8 articles.
  Caught only by a "fewer than k runs" warning added hours earlier.
- **`grep -rl <article_id>` matched three files not containing the article** — cluster
  co-member ids live in *other* rows' `nexus_mind_attributes`.
- **`b650-gpu` is an SSH alias, not DNS.**

## Next session

`docs/TODO.md` top block. Rewrite step 1 against Gemini's behaviour or adopt DeepSeek as the
labelling oracle (Gate A is $0.47/run — iterate freely). Then **Phase B2 hard negatives**, the
larger half of class A and **$0 of oracle** — §1f measured 2 of 3 class-A rows as the *student*
disagreeing with all three oracles, and nothing this session touched it.

**Two owner calls block progress:** delivered accountability, and development finance.
