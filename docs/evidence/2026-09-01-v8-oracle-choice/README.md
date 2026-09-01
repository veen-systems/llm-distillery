# The oracle choice under the ADOPTED prompt — the disagreement that decided it is gone

**2026-09-01. Spend: DeepSeek $0.0093 off-peak (27 calls) + Gemini 2.5 Flash 321,564 in /
8,585 out over 27 calls.** 54 calls, **0 errors**. No model trained, no threshold moved,
nothing under `filters/common/`. Design fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md)
before any call; five of six predicted ranges hit and **the sixth — the important one — was
wrong.**

## 1. Headline

⛔ **First, the finding that cost nothing: the bake-off the plan demands was largely run on
2026-08-23, and the plan was never updated with its own answer.** Phase B and §9 Q1 still carry
a **2026-08-20, n=3** claim that *"Gemini is the stricter arm on class A"*. Three days later a
**15-row × k=3 × 2-prompt × 2-oracle** run costing **$0.4711** concluded the opposite and said so
explicitly: *"DeepSeek applies it, Gemini does not… **this decides the Phase B oracle choice,
which the plan left open**"* (`docs/evidence/2026-08-23-gate-a-two-oracle-run.md`). The stale
sentence sits in the section a reader consults **while deciding how to spend $10**.

⭐⭐ **And now the finding that did cost something: under the ADOPTED prompt that disagreement
has disappeared.** The row 08-23 named as decisive — *"Five men arrested in Mashonaland Central
for raping a minor"* — was **DeepSeek 3.00 vs Gemini 7.43** under the as-is prompt. Under
`prompt-candidate-tail.md`:

| | DeepSeek | Gemini 2.5 Flash |
|---|---|---|
| k=3 weighted mean | **1.050** | **1.025** |
| runs | 1.05 / 1.05 / 1.05 | 1.05 / 0.97 / 1.05 |
| `scope_verdict` | harm_is_subject ×3 | harm_is_subject ×3 |

**The reorder fixed Gemini's Step-1 adherence on the row the whole verdict rested on.** ⛔ I
predicted it would not (pre-registration §"Predicted ranges": *"3.00–7.5, and I expect it above
3.85"*), and that was the one call in the design that mattered.

## 2. Head to head, 9 class-A rows, FULL TEXT for the first time

Every prior class-A number in this project came from **300-character excerpts**. These rows were
restored to full text (2,107–14,546 chars) earlier today from the monthly archives.

| | Gate B-A (k=3 mean < each row's own `max_acceptable_wa`) | STEP 1 applied (majority verdict ≠ `in_scope`) |
|---|---|---|
| **DeepSeek** | **8/9** | **8/9** |
| **Gemini 2.5 Flash** | **7/9** | **7/9** |

Against 08-23's 7/9 and 6/9 on excerpt-derived text under the weaker prompt — **both oracles
improved, and the gap narrowed to one row.** Full output: [`results.txt`](results.txt).

⚠️ **Judged against editorial upper bounds, not oracle ground truth.** The `max_acceptable_wa`
on each row is an editorial judgement recorded with it (§1a); **ADR-021 coverage is not claimed
and must not be implied.** The bar is read off each row, never typed into the analyser.

### The two failures, and they are different in kind

**Both oracles fail *"Parents of baby girl killed at nursery"* — and on both it is a coin toss.**

| | k=3 | runs | verdicts |
|---|---|---|---|
| DeepSeek | 4.400 | 6.10 / **0.90** / 6.20 | in_scope / response_to_harm / in_scope |
| Gemini | 5.133 | 7.20 / 7.15 / **1.05** | in_scope / in_scope / harm_is_subject |

⭐ **This is #135's step function in the wild, on the row that matters.** Each oracle gets it
right on one run of three. It is not a prompt defect that more prompt-writing reaches; it is the
scope gate flipping.

⛔ **And `--aggregate majority` makes it WORSE, not better.** Re-derived with the tool rather
than by hand (`scripts/oracle/aggregate_k_runs.py`), not from the rounded table above:

```
ds  SCOPE GATE FLIP RATE: 1/9    all=4.400  major=6.150   ['in_scope','response_to_harm','in_scope']
gm  SCOPE GATE FLIP RATE: 1/9    all=5.133  major=7.175   ['in_scope','in_scope','harm_is_subject']
```

The majority verdict is `in_scope` on both, so restricting the mean to the agreeing runs
**removes the one run that got it right**. Evidence that the aggregation rule has to be chosen
on data rather than on which option sounds more principled — and a second, independent class-A
flip observation at **1/9 on each oracle**, alongside the 2/8 measured on the class-A supplement
the same day.

**Gemini alone fails *"Celebrated at birth, pushed into sex work"* — and it is not a coin toss.**
**7.158**, `in_scope` on **3/3**, runs 7.05 / 6.93 / 7.50. DeepSeek: **0.900**,
`harm_is_subject` on 3/3. ⛔ This is the #91 origin row — the one that led the ovr.news homepage
and started v8. **On the single article that motivated this whole filter version, one oracle is
stably right and the other is stably wrong.**

## 3. What this does and does not settle

- ✅ **The 08-23 argument does not carry to the adopted prompt.** Its decisive row is now a tie.
  Anyone citing *"Gemini ignores Step 1"* against `prompt-candidate-tail.md` is citing a
  measurement of a different prompt.
- ✅ **DeepSeek is still ahead**, 8/9 vs 7/9 on both metrics, and its one loss is a shared coin
  toss while Gemini's extra loss is stable and on the origin row. ⚠️ **8 vs 7 on n=9 is one
  row.** Do not read the margin as robust; read the *identity* of the row.
- ⛔ **Gate B-A does not pass on either oracle.** Acceptance criterion 1 requires **every**
  class-A record below its bar. The blocker is now a gate flip on one row, not a prompt defect —
  a different problem with a different fix (k, or an aggregation rule, or a §5 clause naming
  bereaved-parent-safety-campaign stories).
- ⛔ **The cost argument is oracle-specific and does not transfer.** The 5.2× reorder saving is
  DeepSeek **prefix caching**. Gemini's OpenAI-compatible endpoint returns no
  `prompt_cache_hit_tokens` field at all, so the script's *"Cache hit rate: 0.0%"* for Gemini is
  **a construction artifact, not a measurement** — the instrument could not have said anything
  else. A Gemini relabel would be priced on its own card at 11,910 input / 318 output tokens per
  article, and ⛔ **the ≈$10.32 figure would not apply.**
- ⛔ **Nothing here touches the student.** §1f measured 2 of 3 class-A rows as the *student*
  disagreeing with every oracle. These are oracle labels; Phase B2 hard negatives remains the
  larger half of the class-A fix.

## 4. Predictions, scored

| | predicted | measured | |
|---|---|---|---|
| DeepSeek, STEP 1 applied | 8–9 of 9 | **8** | ✅ |
| Gemini, STEP 1 applied | 3–7 of 9 | **7** | ✅ top of the band |
| DeepSeek, Gate B-A | 7–9 of 9 | **8** | ✅ |
| Gemini, Gate B-A | 5–8 of 9 | **7** | ✅ |
| Mashonaland, DeepSeek | ≤ 3.00 | **1.050** | ✅ |
| Mashonaland, Gemini | 3.00–7.5, **expect above 3.85** | **1.025** | ⛔ **MISS** |

Four of the five hits sat in bands wide enough to survive a wrong mechanism, which is why the
scorecard is reported rather than celebrated. The miss is the informative row: I reasoned that a
reorder cannot fix a rule an oracle *ignores*, and that reasoning was wrong — moving STEP 1
away from the article did not weaken it, it strengthened it.

## 5. Instrument notes

- ⛔ **`gemini_billing_api_key`, never `gemini_api_key`.** On 08-23 the free-tier key returned
  429s and *"the first Gemini run was garbage and looked like a run"* — 14/45 and 8/45 succeeded
  and **k=3 silently became k=1**. The analyser here asserts `len(runs) == 3` per row per arm and
  raises otherwise, so that failure cannot be silent again.
- **Both oracles run through the same call site**, `scripts/score_deepseek_production.py`, via
  `--base-url` / `--key-name` / `--model`. A price or behaviour with no call site is not an
  option this project can pick (#103).
- `--max-tokens 8192` for Gemini: 2.5 Flash spends thinking tokens from that budget and the
  4096 default risks a truncated JSON body. 0 parse errors at 8192.
- Weights, the gatekeeper and the cap are **imported** from `filters/uplifting/v7/base_scorer.py`.

## 6. Reproduce

```bash
python3 - <<'PY' > classA.jsonl
import json
for l in open("datasets/adverse/uplifting.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if str(r.get("class", "")).startswith("A"):
        print(json.dumps({k: r.get(k, "") for k in ("id","title","url","content","source",
                                                    "published_date","language")}, ensure_ascii=False))
PY

# DeepSeek arm
PYTHONPATH=. python3 scripts/score_deepseek_production.py --input classA.jsonl \
  --output runs/ds_1.jsonl --config filters/human_thriving/v8/config.yaml \
  --prompt filters/human_thriving/v8/prompt-candidate-tail.md --concurrency 5

# Gemini arm — same script, same prompt, different endpoint and key
PYTHONPATH=. python3 scripts/score_deepseek_production.py --input classA.jsonl \
  --output runs/gm_1.jsonl --config filters/human_thriving/v8/config.yaml \
  --prompt filters/human_thriving/v8/prompt-candidate-tail.md \
  --base-url https://generativelanguage.googleapis.com/v1beta/openai/chat/completions \
  --key-name gemini_billing_api_key --model gemini-2.5-flash \
  --oracle-label gemini-2.5-flash --max-tokens 8192 --concurrency 5

PYTHONPATH=. python3 docs/evidence/2026-09-01-v8-oracle-choice/analyse.py
```

The run files carry full article text for 9 rows already tracked in
`datasets/adverse/uplifting.jsonl`, so committing them adds no new article text to the repo.
