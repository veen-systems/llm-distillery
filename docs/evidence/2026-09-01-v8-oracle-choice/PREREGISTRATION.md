# Pre-registration — does the REORDERED prompt change the oracle verdict?

**Written 2026-09-01, before any call.**

## ⛔ The bake-off the plan asks for was largely run on 2026-08-23, and the plan was never updated

`docs/HUMAN_THRIVING_V8_PLAN.md` Phase B and §9 Q1 both still say *"Measured on n=3, **Gemini is
the stricter arm** on class A (caps 3/10 vs DeepSeek 1/10)"* — dated **2026-08-20**. Three days
later, a **15-row × k=3 × 2-prompt × 2-oracle** run costing **$0.4711** measured the opposite
where it matters and said so in terms:

> ⛔ **The oracles disagree by 4.4 points on the single most reader-offensive row.** *"Five men
> arrested for raping a minor"*: DeepSeek **7.05 → 3.00** (capped), Gemini **7.23 → 7.43**
> (*rises*). The step-1 text names "individual arrest/sentencing" explicitly; **DeepSeek applies
> it, Gemini does not.** A prompt rule that one frontier oracle ignores is not a shipped rule —
> **this decides the Phase B oracle choice, which the plan left open.**
> — `docs/evidence/2026-08-23-gate-a-two-oracle-run.md`

Class-A totals there: **DeepSeek 7/9, Gemini 6/9**. So the standing recommendation to "run the
ADR-020 bake-off first" is **mostly already discharged**, and its answer points at **DeepSeek** —
the opposite of the sentence still sitting in the plan. ⚠️ This is doc drift of the expensive
kind: the stale claim is in the section a reader consults *when deciding how to spend $10*.

## The genuine residual, and it is the only thing that could overturn that

The 08-23 run scored `filters/human_thriving/v8/prompt-candidate.md` — the **as-is** prompt. The
prompt **adopted** on 2026-08-30 is `prompt-candidate-tail.md`, the **reordered** one, which
moves the article to the end and therefore moves STEP 1 much further from the text it judges.

**Adherence to Step 1 is exactly what separated the two oracles.** Nobody has measured whether
the reorder changes it, in either direction. It is plausible both ways: a longer gap could
weaken adherence (the rule is further from the article), or strengthen it (the rule is read
before the article rather than after).

## Design — fixed here, before the calls

| | |
|---|---|
| rows | the **9 class-A rows** of `datasets/adverse/uplifting.jsonl`, at **FULL TEXT** (2,107–14,546 chars) for the first time — recovered from the monthly archives earlier today |
| prompt | `prompt-candidate-tail.md` **only** (the adopted one). The as-is arm is not re-run; 08-23 covers it |
| oracles | **DeepSeek** `deepseek-chat` · **Gemini** `gemini-2.5-flash` via the OpenAI-compatible endpoint, **through the same call site** (`scripts/score_deepseek_production.py --base-url --key-name`) so this is a price and a behaviour we can actually obtain |
| key | ⛔ **`gemini_billing_api_key`, never `gemini_api_key`** — the free-tier key returned 429s on 08-23 and *"the first Gemini run was garbage and looked like a run"*: 14/45 and 8/45 succeeded and k=3 silently became k=1 |
| k | **3 per oracle**, 9 × 3 × 2 = **54 calls** |
| weights | imported from `filters/uplifting/v7/base_scorer.py`, never copied |

## What is being measured

1. **Step-1 adherence, per oracle** — the share of the 9 rows where `scope_verdict != in_scope`.
   These rows are class A by construction: their dominant subject **is** a harm. An oracle that
   applies Step 1 should return a non-`in_scope` verdict on essentially all of them.
2. **Gate B-A** — every class-A row's k=3 weighted mean must be **< 3.85**. ⚠️ This is the first
   time it is judged on full text; every prior number came from 300-char excerpts, and the
   repo's own rule is that *three of five drafts reversed on a full read*.
3. **The Mashonaland row specifically** (`south_african_herald_zw_…`, *"Five men arrested … for
   raping"*), where the two oracles were 4.4 points apart on 08-23.

## Predicted ranges — stated before looking

| | prediction | why |
|---|---|---|
| DeepSeek, rows non-`in_scope` | **8–9 of 9** | it applied Step 1 under the as-is prompt, and the reorder was adopted partly for sharper labels |
| Gemini, rows non-`in_scope` | **3–7 of 9** — the wide band is the point | 08-23 says it ignores the rule; if the reorder fixes that, this is where it shows |
| DeepSeek, Gate B-A pass | **7–9 of 9** | 7/9 on excerpt-derived text under the weaker prompt |
| Gemini, Gate B-A pass | **5–8 of 9** | 6/9 previously |
| Mashonaland row, DeepSeek | **≤ 3.00** | the gatekeeper cap |
| Mashonaland row, Gemini | **3.00–7.5**, and I expect it **above 3.85** | the reorder is not obviously a fix for a rule being ignored |

⛔ **A hit inside these ranges is not confirmation the reasoning was right** — four of six are
wide. The decisive read is the *contrast* between the two oracles' Step-1 adherence, not either
number alone.

**If Gemini's adherence is now equal to DeepSeek's, the 08-23 verdict does not carry to the
adopted prompt and the oracle question reopens.** That would be a finding, not a failure.

## Cost

54 calls. The 08-23 run was 180 calls for $0.4711, so ≈$0.15 expected, plus Gemini's own rate.
⚠️ DeepSeek's half bills at **peak** (before 10:00 UTC); the premium on ~27 calls is cents, and
waiting hours to save them on a decision-blocking measurement is not a trade worth making.
Gemini has no peak/off-peak.
