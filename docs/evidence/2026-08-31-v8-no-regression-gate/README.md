# The no-regression gate, re-run over the CURRENT 4-row set — **all four PASS under the adopted prompt**

**2026-08-31. Spend $0.0205** off-peak (36 calls, **0 errors**, 0 junk-skipped). No model trained,
no threshold moved, nothing under `filters/` changed, nothing deployed. Design fixed in
[`PREREGISTRATION.md`](PREREGISTRATION.md) **before any call**; all four predicted ranges were hit
(§4 — and the one row the prediction singled out as most likely to fail is the most stable in the
set, which is a miss of a different kind).

## 1. Headline

✅ **Acceptance criterion 2 passes on today's set, and it did not pass yesterday.** The two rows
added on 2026-08-30 had **never been scored under an oracle prompt** — they were selected from
`uplifting v7` *student* scores — so the criterion covered 2 of its 4 rows. It now covers 4 of 4,
under the **adopted** reordered prompt, k=3, one judge.

```
$ PYTHONPATH=. python3 docs/evidence/2026-08-29-v8-h-v8-9-adjudication/no_regression_analyse.py \
      docs/evidence/2026-08-31-v8-no-regression-gate/runs
op-point 4.5 (imported)   judge deepseek-chat, one judge across all three arms
no-regression set: 4 rows   scored by this run: 4          # exit 0
```

Full output: [`results.txt`](results.txt). ⚠️ The op-point, the six weights and the gatekeeper are
**imported** from `filters/uplifting/v7/base_scorer.py` by the analyser, never copied here.

| row | guard | **A** v8 reordered | B v8 as-is | V v7 prompt | assertion | verdict |
|---|---|---|---|---|---|---|
| Rappler, *"The silent crisis on our plates"* (en, 13,107 ch) | recovery narratives | **5.100** | 5.283 | 5.467 | `raw > 4.5` | ✅ PASS |
| Unifesp, DOI-Codi forensic work (pt, 4,761 ch) | transitional justice | **4.750** | 3.750 | 2.900 | delta ≥ v7, same judge | ✅ PASS, **+1.850** |
| Fast Company, London ULEZ (en, 5,780 ch) | lens overlap (ADR-015) | **6.417** | 6.517 | 6.483 | `raw > 4.5` | ✅ PASS |
| Welingelichte Kringen, Greek lignite (nl, 2,601 ch) | lens overlap, multilingual | **5.550** | 5.667 | 5.750 | `raw > 4.5` | ✅ PASS |

`scope_verdict` is `in_scope` on **24/24** v8 runs (12 per arm). On the v7 arm it is `__absent__` on all 12 —
the scorer's sentinel, not a missing field: **the v7 prompt has no scope binary at all**, which is
why k≥3 is a v8 requirement and was not one for v7.

## 2. ⚠️ The margins, and why one of them is not comfortable

⛔ **A PASS is not the same as a margin.** The oracle decoder's own run-to-run floor on this
population is **0.436 mean / 0.687 max** (§1f of the plan), and two of the four margins are inside
it:

| row | arm A margin over 4.5 | individual runs | inside the decoder floor? |
|---|---|---|---|
| Rappler | **+0.600** | 5.25 / **4.65** / 5.40 | ⚠️ yes, below the 0.687 max — and its lowest single run clears the op-point by **0.15** |
| Unifesp | +0.250 (incidental — its assertion is the delta, which is +1.850) | 4.80 / 4.35 / 5.10 | ⚠️ n/a to the assertion, but one run sits **below** 4.5 |
| Fast Company | +1.917 | 6.45 / 6.45 / 6.35 | ✅ no |
| Welingelichte Kringen | +1.050 | 5.55 / 5.55 / 5.55 | ✅ no |

**This is the argument for k=3 stated as data, not as policy.** A single run of the Rappler row
lands 0.15 above the line; a single run of the Unifesp row lands *below* it. Criterion 2 must
never be read off one pass.

## 3. The free control this design bought — the two carried-over rows, re-scored

The 08-29 run is **not** reused for the two rows it covered: a k=3 mean stitched from two dates
across a decoder with a 0.436/0.687 floor is not a k=3 mean. Re-scoring them makes the day-to-day
movement of a k=3 **mean** visible. ⚠️ **Not "never measured here"** — Phase A measured a
*within-arm* pair null on single runs (mean |Δ| **0.312**, stratum R, same day). What is new is the
unit and the gap: **k=3 means, two days apart** (`grep -rn "within (null)" docs/evidence/` finds
the Phase A table; nothing there varies the day or averages first):

| row · arm | 2026-08-29 | 2026-08-31 | Δ | vs decoder floor (0.436 mean / 0.687 max) |
|---|---|---|---|---|
| Rappler · A | 4.900 | 5.100 | +0.200 | inside |
| Rappler · B | 5.350 | 5.283 | −0.067 | inside |
| Rappler · V | 4.983 | 5.467 | **+0.484** | ⚠️ **above the mean floor**, below the max |
| Unifesp · A | 4.367 | 4.750 | +0.383 | inside |
| Unifesp · B | 3.983 | 3.750 | −0.233 | inside |
| Unifesp · V | 2.950 | 2.900 | −0.050 | inside |

⭐ **A k=3 mean moved by up to 0.484 between two days with everything else held fixed** — same
judge, same prompt file (hash stamped, `ed45217e6b80`), same article text, same weights.

⚠️ **The right-hand column compares a MAX to a MEAN, and that is a weaker statement than it
looks.** 0.484 is the largest of **6** movements; 0.436 is a **mean |Δ|** over 40 single-draw
pairs. A max is expected to sit above a mean even with the spread unchanged, so this is **not**
evidence that `1/√k` fails, and `ν/√3 ≈ 0.25` is quoted for scale rather than as a refuted
prediction. ⚠️ The two figures are also drawn from different sets and different quantities, so
the comparison is indicative, not a test. The claim that survives is
the narrow one, and it is enough: **a k=3 oracle mean on this population can move about half a
point between days.** ⛔ Do not read a ≤0.5 movement of one as an effect. Both verdicts are
unchanged, which is what the gate asserts; the *numbers* are not stable to three digits and were
never claimed to be.

⚠️ Three further things are **not separable from six pairs**: small n, a population difference
(these are `uplifting`-prompt rows, not the `cultural_discovery v5` ones the 0.436 was measured
on), and a server-side model change between the two days — **`deepseek-chat` is a moving pointer,
not a pinned version**, and nothing in this run holds it fixed.

## 4. Predictions, scored

| row | predicted (arm A) | measured | |
|---|---|---|---|
| Rappler | 4.5–5.5 | **5.100** | ✅ inside |
| Unifesp | delta +0.8 to +2.0 | **+1.850** | ✅ inside |
| Fast Company | 4.5–6.5 | **6.417** | ✅ inside |
| Welingelichte Kringen | 4.0–6.0, **"the most likely to fail"** | **5.550** | ✅ inside — ⛔ **and the risk call was wrong** |

⛔ **The row flagged as most at risk is the most stable object in the run**: 5.55 / 5.55 / 5.55
under arm A and 5.75 / 5.75 / 5.75 under v7 — **zero** decoder spread on six runs, against a
13,107-char English row that spreads 0.75. The prediction reasoned from *short + non-Latin-adjacent
+ a step-function scope gate*, and length and language predicted nothing here. A hit inside a
predicted range is not confirmation that the *reasoning* was right — three of these four ranges
were wide enough to survive being wrong about the mechanism.

## 5. Provenance and reproduction

Arm identity does **not** rest on the filenames, unlike the 08-29 run: every row carries
`prompt_file` and `prompt_hash` (`003cd35a5122` reordered / `9d31e5ce1378` as-is /
`ed45217e6b80` v7). Verified one file at a time — 9 files × 4 rows, one distinct hash each.

```bash
python3 - <<'PY' > /tmp/nr_input.jsonl        # the live set, article fields only
import json
for l in open('datasets/adverse/uplifting_no_regression.jsonl'):
    r = json.loads(l)
    print(json.dumps({k: r[k] for k in ('id','title','url','content','source',
                                        'published_date','language')}, ensure_ascii=False))
PY

# 9 passes, interleaved A1 B1 V1 A2 B2 V2 A3 B3 V3, through the real call site.
PYTHONPATH=. python3 scripts/score_deepseek_production.py \
  --input /tmp/nr_input.jsonl --output runs/nr_A1.jsonl \
  --config filters/uplifting/v7/config.yaml \
  --prompt filters/human_thriving/v8/prompt-candidate-tail.md --concurrency 4

PYTHONPATH=. python3 docs/evidence/2026-08-29-v8-h-v8-9-adjudication/no_regression_analyse.py runs
```

⚠️ The runs carry full article text (26,249 chars over 4 rows). That text is **already tracked**
in `datasets/adverse/uplifting_no_regression.jsonl`, so committing them adds no new article text
to the repo — this is not the #97 corpus-scale hazard, and the 08-29 run set the precedent.

**Cost, recomputed from the stamped per-row `usage` rather than from the script's rounded
line:** cache-hit input 331,776 · cache-miss input 41,847 · output 13,639 over 36 calls ⇒
**$0.0205 off-peak** / $0.0411 peak, at the 2026-08-16 rates (0.007 / 0.22 / 0.66 per 1M). Run at
18:57 UTC on a Monday — outside both peak windows (01:00–04:00, 06:00–10:00 UTC Mon–Fri).
