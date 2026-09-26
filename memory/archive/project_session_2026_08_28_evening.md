# 2026-08-28 (evening) — three reserved numbers decided, and a probe whose control outranked it

**Spend: $0.12** (DeepSeek off-peak, 90 calls, 0 errors) — the session's only spend, and the
first oracle spend in this repo since 2026-08-23. **No model trained, no threshold moved, no
filter package changed, nothing reaching a path NexusMind runs.** Deploy is **N/A, not
skipped**: every changed file is `docs/`, `memory/`, `scripts/`, `tests/fixtures/` or a
non-deployable prompt.

Commits: `9c4cef0`, `6d72848`, `f026dc4`, plus the curate commit.

## 1. The three Gate 0 numbers the plan reserved are decided

Owner rulings. Record: `docs/decisions/2026-08-28-v8-gate0-corpus-spec.md`.

| | ruled |
|---|---|
| positive base rate | **19.5%**, enrichment **2.0×** over drawable production's 9.76% — *recorded*, not inherited |
| stage-1 aggressiveness | **hold near pass-through** (~88.6% routed); no cost constraint claimed, so the FN risk is not bought |
| class-A supplement | **3:1 TP:FP** at ≥0.70% of corpus, sampled above the op-point |

Marked in the record as **derived, not ruled**: at 19.5% with the mix held at 63.5/36.5 the
5.5+ band lands ≈7.1%, i.e. ≈2.0× production instead of today's 4.21×. Check against a
prepared split.

## 2. ⛔⛔ THE KEEPER — the null arm outranked the experiment it was controlling

Went looking for a price. The v8 prompt puts the article at char **617 of 42,406**, so its
cache ceiling is **1.5%, the lowest of 17 prompts here**, on the most input-heavy shape we
run. Moving the `INPUT DATA` line to just before §7 is content-preserving to one `---` and
lifts the ceiling to **95.8%**; measured on the real call site, **0.0% → 90.2%**.

Then the control. The reorder moves 16/30 rows past the #95 band and crosses the op-point 3
times — a damning parity failure, read alone. **Running the same prompt twice gives 16/30 and
5 crossings.** The treatment sits inside its own null.

⭐ **Without the null arm the change dies on a number that measures the oracle, not the
change.** And the null is what exposed the real finding:

| identical prompt, identical articles, two runs | |
|---|---|
| rows crossing the op-point | **5 / 30 (17%)** |
| rows where the scope gate (all six dims ≤ 2) flips | **4 / 30 (13%)** |
| median \|Δ\| — gate-**stable** rows | **0.100** (inside #95's 0.16) |
| median \|Δ\| — gate-**flipped** rows | **3.750** |
| of 5 rows moving >1.0 / of 25 moving ≤1.0 — gate flips | **4** / **0** |

`scope_verdict` is a binary that zeroes all six dimensions, so this is a **step function, not
jitter** — and `1/√k` does not touch a Bernoulli. **Gate A never saw it: it ran k=3 and
averaged over exactly this.** A k=1 re-score labels ~860 of 6,590 rows by a toss, at the
boundary. → **#135**, and `memory/score-batch-shape-noise.md` now carries it as a **fourth**
noise population that is explicitly *not a floor*.

**The two findings are one decision: k=3 reordered $10.16 vs k=1 as-is $18.00.** Three labels
for 56% of the price of one. The plan's "≈$12" was a single run at the old shape.

⛔ **Parity remains UNPROVEN** — "no effect detectable above noise" is not "no effect". The
reordered prompt is written, **not adopted**; it goes into the Phase A k=3 calibration, where
parity gets settled.

## 3. #134 step 1 — 338 findings, and not 338 defects

`refcheck.py --docs`: scan set **34 → 202 files**, findings **1 → 339**. Above my
pre-registered 60–250, so triaged before reporting: **155 unmarked cross-repo**, 170
not-found, 13 collisions/stale. LIVE tier 211 / FROZEN 127.

Confirmed real decay: **`docs/README.md`, the repo's own docs index, points at three
`docs/agents/*.md` that do not exist.** The FROZEN tier behaved exactly as #134 predicted —
its 71 not-found are dominated by 2025-11 Qwen-era records that are *correct as history*, so
`docs/` stays flag-gated. Controls: sensitivity 33/33 before and after; default run identical
bar the new attribution section.

## ⛔ Four of my own

1. **My triage counted `veen-systems` — this repo's own parent — as a sibling repo**, so its
   tree held every other repo: **137 of 156** cross-repo refs read as ambiguous against a real
   **13**. Both versions summed to exactly 156. *Closed accounting is not attribution.*
2. **The 99.4% cache artifact** — **13th occurrence of *establish what a source excludes*, and
   a new axis**: the instrument could not produce a *negative*, so the *positive* carried no
   information. Caught before it was quoted.
3. **A cohort sampler read `raw_weighted_average` at the row root**; it lives under
   `nexus_mind_attributes.<lens>`. Every band came back empty — and it **raised** rather than
   returning a short draw, which is the *make the missing case raise* rule paying out.
4. **`CLAUDE.md` cited `ovr.news/BRAND.md`; the file is `ovr.news/docs/BRAND.md`** — wrong for
   15 days in an always-loaded file. ⭐ The repo's own `refcheck.py` **resolved** it (rung 4
   matches by suffix); `/curate`'s stricter extractor, which needs the exact path, caught it.
   **Two instruments of different strictness are not redundant.**

## Also

- **#136** filed: the commit-msg deploy-guard rejected *"Nothing deployed"* — it cannot read
  negation, and it failed a directory with no `config.yaml` and no `inference_hub.py`. Handled
  by rewording, not `--no-verify` (that override cost three days in #44).
- `scripts/score_deepseek_production.py` now persists **per-row `usage`**. ⚠️ No run before
  today can be decomposed into warm-up vs steady state.
- The archive rolled **83 → 84 files within three hours**. Re-enumerate at draw time.
- Free control: the cohort draw's GN exclusion came out **22.0%** against the 22.1% on record,
  from a different instrument.

## Next session

1. **Persist `scope_verdict` + `dominant_subject`** (#135 prerequisite — the gate was inferred).
2. **Phase A calibration at k=3**, reordered prompt, production-mix cohort — settles #135's
   flip rate, ADR-010 parity (H-V8-3) and the real $/article in one run.
3. **Corpus size**, then stage on b650 + `corpus_manifest.json` (#127).
4. #134 step 2 (tiering) and #136 — hygiene.
