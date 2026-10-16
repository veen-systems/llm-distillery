# Oracle pricing & scheduling — archive of closed entries

*Moved VERBATIM from `memory/oracle-pricing-scheduling.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read surface), under
the 2026-09-27 ledger rule: entries whose verdict is closed (CONFIRMED / REFUTED / SETTLED / RESOLVED) move; open
entries, rulings and standing traps stay. Order kept; a block from inside a section repeats that section's heading.
The rule applied here is the owner's DATE rule (2026-10-09), by judgement: blocks priced on the superseded V4 card or
explicitly marked superseded/historical moved; the no-Batch-call-site finding and both executable verify checks, the cache
ceiling lever, the weekday-boundary trap, the Prepay coupling, the don't-pin-the-alias rule and the scheduling rules stay.*

> 🔴 **THE NOTICE LANDED — effective 16:00 UTC, 2026-08-16 (email dated
> 2026-08-14 16:58 +0800, to jveen1@proton.me).** Both the announcement email and
> the docs page confirm: **peak/off-peak billing, off-peak = half of peak, and
> every tier — off-peak included — bills ABOVE the old flat rate.** The peak
> *hours* are **unchanged** (01:00–04:00 and 06:00–10:00 UTC); what changed is
> that off-peak is no longer cheap, and — see below — that those hours now apply
> **Mon–Fri only**, which does change the scheduling rule.
>
> ✅ **THE RATES ARE NOW ESTABLISHED — read off the vendor pricing page
> (`https://api-docs.deepseek.com/quick_start/pricing/`) on 2026-08-23.**
> `deepseek-v4-flash`, $/1M, off-peak / peak:
>
> | | cache-hit in | cache-miss in | out |
> |---|---|---|---|
> | **off-peak** | 0.007 | 0.22 | 0.66 |
> | **peak** | 0.014 | 0.44 | 1.32 |
>
> This **settles the two-disagreeing-sources caveat that stood here until
> 2026-08-23**: the docs summary (0.007 / 0.22 / 0.66) was right and the pricing
> round-up's blended ×7.84 / ×1.96 / ×2.94 ratios are **REFUTED**. Do not
> re-quote the round-up.
>
> ✅ **Weekends bill off-peak.** The same page states the peak windows apply
> **"Monday through Friday"** — 01:00–04:00 and 06:00–10:00 UTC — and that every
> other hour is off-peak. So off-peak is now free to *obtain*: run any big batch
> Sat/Sun and time-of-day stops mattering. The weekday rule below is unchanged
> for Mon–Fri.
>
> **The conclusion is UNCHANGED and now rests on verified rates.** At our stated
> shape (8K-token prompt, ~14% cache hit) the input side is a fixed
> **$0.001521/article** and output adds **$0.00000066/token**. Anchoring output
> on cd v5's *actual* $10.36 / 8K articles ($0.001295/article ⇒ **~1,174 output
> tokens**), new off-peak is **$0.0023/article** — **above Gemini Batch's
> ~$0.0018**, and above the **+64%** flip point on either baseline (+109% vs the
> $0.0011 planning figure, +77% vs the $0.001295 actual).
> **→ Gemini Batch (~$0.0018/article) is the cheapest oracle, and the
> DeepSeek-as-default precedent from cd v5 is VOID.** New DeepSeek peak is
> **$0.0046/article** — dearer than Gemini Flash *real-time*, so peak is
> unambiguously wrong, not merely wasteful. Per 8K-article retrain: DeepSeek
> off-peak **$18.37**, Gemini Batch ~$14.40, DeepSeek peak ~$36.74. Still
> single/double-digit dollars — this picks the default oracle, it does not
> threaten affordability.
>
> ✅ **The rest of the re-derivation stands, and it no longer depends on the cache unknown.**
> Both rate cards re-read first-hand 2026-08-24. DeepSeek off-peak `0.007 / 0.22 / 0.66`,
> peak exactly 2×, *"Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through
> Friday (all other hours are off-peak)"*. **Gemini 2.5 Flash Batch `$0.15/M in,
> $1.25/M out`** (50% off standard `$0.30 / $2.50`) — the first Gemini rate table this
> file has ever carried. ⛔ The `~$0.0018/article` Gemini figure that every comparison
> above was measured against **was itself an unanchored planning number**; only the
> DeepSeek side was ever scrutinised.
>
> **The decisive numbers are counted, not back-solved.** `datasets/scored/nr_v4_batch.log`
> — a `score_deepseek_production.py` run, **n=3,641 articles**, nature_recovery v3 prompt,
> 2026-07-07, the largest DeepSeek batch on disk — reports **5,986 input / 195.9 output
> tokens per article at a 0.34% cache-hit rate**. Its own `$3.24` line reconciles to the
> cent against the old rate card, so those counters are sound.
>
> | prompt (measured) | I/O | DS @0.34% | Gemini Batch *(no call site)* | Gemini realtime *(implemented)* | cheapest **implemented** |
> |---|---|---|---|---|---|
> | nature_recovery v3, n=3,641 | 30.6 | 0.001442 | 0.001175 | 0.002350 | **DeepSeek** |
> | uplifting v7 | 19.9 | 0.001756 | 0.001526 | 0.003052 | **DeepSeek** |
> | human_thriving v8 | 28.3 | 0.002168 | 0.001741 | 0.003482 | **DeepSeek** |
> | human_thriving v8r2 | 43.3 | 0.002585 | 0.002100 | 0.004201 | **DeepSeek** |
> | human_thriving v8r3 | 42.8 | 0.002675 | 0.002127 | 0.004255 | **DeepSeek** |
>
> ⭐⭐ **Stop arguing about the anchor — the answer is SHAPE-INDEPENDENT.** *If* Gemini
> Batch is ever implemented, it beats DeepSeek off-peak unless **input/output < 8.4** at
> the measured cache rate (< 14.7 even at the assumed 14%). Every oracle prompt we run
> sits at **I/O ≈ 20–43**, so no plausible output length reaches the crossover — the
> anchor everyone was arguing about could not have decided it either way. That is why
> both the "+64% flip point" and the outside "dead heat" framings mislead: each compares
> at one assumed shape instead of asking which side of the ratio we are on. Reproduce:
> `scripts/analysis/oracle_cost.py` (rates in the header, measured shapes inline).
> ⛔ **Two corrections to what this file asserted on 2026-08-23:**
> 1. **"cache-hit 0% (measured)" HAD NO INSTRUMENT.** It came from a
>    `score_ollama_oracle.py` run. That script reads `prompt_cache_hit_tokens` into
>    `_cached_tokens` (line 359) and then never sums it, never persists it into the result
>    row, and never prints it — the run logs carry no cache line at all. A **dead-field
>    zero**, the exact trap CLAUDE.md names as *"a wrong path and a dead field both read as
>    zero"*. It lands near the right answer only by luck; what makes 0.34% believable is
>    `nr_v4_batch.log`, whose instrument **can** report non-zero and did (1% mid-run).
> 2. **"n=45 articles, k=3" is wrong — it is n=15 articles, k=3 = 45 calls.** Those 15 are
>    a hand-picked adversarial class-A sample (median content 3,482 chars against the
>    1,349-char production median in [[uplifting-oracle-genre-hypotheses]]), so their
>    absolute $/article are upper bounds. The provider *ratio* stands: both oracles scored
>    the identical 15 articles.
>
> ⚠️ **Superseded reasoning kept below to date the correction — the ~1,174 anchor
> is a back-solve, not a measurement:**
> ~1,174 output tokens is derived from an invoice total under an
> assumed input shape; it has never been counted. It is decisive: the break-even
> against Gemini Batch sits at **~420 output tokens**, so *if* the oracle really
> emits under ~400/article, DeepSeek off-peak still wins and the paragraph above
> is wrong. Our own $0.0011 planning figure back-solves to ~430–480 tokens —
> i.e. **almost exactly on the line** — which is why the anchor choice, not the
> rates, decides this. **Count `completion_tokens` on the next DeepSeek run
> before spending on either oracle**; `scripts/score_deepseek_production.py` now
> prints output-tokens/article at the end for exactly this reason. ⛔ **Do not
> promote either figure to settled without that count.**
>
> ⚠️ **SUPERSEDED IN PART — a price hike IS coming (2026-08-06).** DeepSeek
> emailed all API users: *"We plan to raise the overall pricing for DeepSeek API
> services in the near future, with a significant increase expected."* **No
> numbers and no effective date** — "subject to official notice", and continued
> use after the change counts as acceptance. Everything below is the **old**
> pricing and remains the correct baseline until the official notice lands; the
> sentence "this is a scheduling lever, not a price hike" is now false as a
> forward-looking statement.
>
> **The number that decides it: +64%.** DeepSeek off-peak is $0.0011/article and
> the next-cheapest option, Gemini Batch API, is ~$0.0018 — so a rise of more
> than **~64%** on off-peak makes Gemini Batch the cheapest oracle and voids the
> DeepSeek-as-default precedent from cd v5. DeepSeek **peak** ($0.0022) is
> *already* dearer than Gemini Batch today, so post-hike peak usage is
> unambiguously wrong, not merely wasteful.
>
> **Keep the stakes in proportion:** on an 8K-article retrain this is $8.90
> (DeepSeek off-peak) vs $14.40 (Gemini Batch) — the whole decision is worth
> single-digit dollars per retrain. It changes *which oracle we default to*, not
> whether we can afford to retrain.
>
> **Action: none yet, but do not start a large DeepSeek batch on the old
> pricing without re-checking the Open Platform announcements first.** Not
> affected: uplifting (#102) and investment_risk, whose oracle is Gemini Flash
> via `--llm gemini-flash` (google-genai 2.17.0). Affected if the hike is steep:
> cultural_discovery v6 and any future DeepSeek-oracled filter.
> Re-verify with: the DeepSeek Open Platform pricing page, then re-run the
> per-article arithmetic below against a v5-class 8K-token prompt at ~14% cache
> hit. Update this file with real numbers when the notice arrives.

DeepSeek V4 officialised mid-July 2026, introducing **peak/valley API pricing**. Same batch job costs **2x** at peak vs regular. This was a scheduling lever, not a price hike — off-peak stayed cost-neutral vs what we paid for cd v5. (See the banner above: that framing has an expiry date now.)

**deepseek-v4-flash pricing — ⛔ HISTORICAL, pre-2026-08-16 only, kept to date the change. For current rates use the banner's table.** ($/1M tokens, regular / peak):
- input cache hit: 0.0028 / 0.0056
- input cache miss: 0.14 / 0.28  ← dominant cost
- output: 0.28 / 0.56

**Cost per article** (v5-class ~8K-token prompts, ~14% cache hit): ~$0.0011 off-peak / ~$0.0022 peak. An 8K-article retrain ≈ $8.90 off-peak vs ~$17.80 peak (cd v5 actual under old pricing was $10.36). Cache-hit input is negligible; our low cache-hit rate barely matters.

**Alternatives for context:** Gemini Flash 2.5 real-time ~$0.003–0.004/article with v5-class 8K-token prompts (the $0.001 figure from the 1.5 Flash era is stale — moved here from CLAUDE.md, 2026-07-31 audit). Gemini Batch API ~$0.0018/article (50% off, 24h async) now sits at roughly DeepSeek *peak* pricing (⛔ **that $0.0018 was never anchored** — measured 2026-08-24 it is $0.001175–$0.002127 depending on the prompt; see the banner) — so DeepSeek off-peak remains cheapest, but the gap closes if forced into peak. DeepSeek cd v5 actual: $10.36 for 8K articles, 14% cache hit (⛔ **that 14% is cd v5's structural ceiling, 16.9% — not a project constant**; nature_recovery measures 0.34% against a 3.2% ceiling).

Effective mid-July 2026 with 24h advance email notice. See [[cd-v5-reference-status]] (DeepSeek-as-default-oracle precedent). Next batch job on deck: solutions v4 (ADR-020 validation case).


## Moved 2026-10-16 (#163 round 6)

*Moved VERBATIM from `memory/oracle-pricing-scheduling.md` (#163 the read surface, round 6): closed, moot or done blocks only. Each was a blockquote fragment, so the `>` prefixes are kept.*

### V4 Pro shutdown — cancelled 2026-09-11 (two fragments of the top banner)

> ⛔ **THE V4 PRO SHUTDOWN IS OFF — CANCELLED, NOT POSTPONED AGAIN (vendor mail
> 2026-09-11 20:17 +0800, surfaced by the owner and read 2026-09-17).** *"In response to
> user demand, we have decided to continue providing API services for DeepSeek V4 Pro after
> September 14, 2026, with the billing method remaining unchanged. We will provide further
> notice should there be any changes."* There is now **no published end date and no
> announced routing to Flash**. This passage previously read *"pushed back: 04:00 UTC
> 2026-09-14"* — true when written on 2026-09-10, superseded the next day by a mail nobody
> here had read until six days later.
>
> With the shutdown cancelled, `deepseek-v4-pro` simply stays available at Pro rates, so the
> only thing that changes for us is that a cost comparison against Pro is **live again**
> rather than expiring. DeepSeek claims V4.1 Flash *"comprehensively surpassed V4
> Pro across all key metrics"* — **vendor assertion, unmeasured here.**

### The unpulled lever — V4-card flip points (MOOT under V4.1)

> ⭐⭐ **THE UNPULLED LEVER, worth more than the vendor choice.** Cache hit is the only
> term that can reverse the ranking, and it needs less than people assume: each measured
> shape flips at **19.0%–26.5%** (uplifting v7 19.0%, nature_recovery v3 23.8%,
> human_thriving v8r2 26.5%), and **32.9%** flips it at *any* shape because DeepSeek's
> blended input rate then falls below Gemini Batch's `$0.15/M`. Moving the placeholder to
> the END of the template raises the ceiling toward ~97%: `uplifting v7` would cost
> **$0.000324/article — $2.59 per 8K retrain, 79% below Gemini Batch**, against $14.04
> today. ⚠️ `solutions/v6` is **already past every flip point on paper at 35.7%** — and
> `cultural_discovery/v5`'s 16.9% sits just under, which is the likeliest reason cd v5
> looked cheap enough to set the DeepSeek-as-default precedent in the first place.
> ⛔ **NOT a free change, and not to be taken as decided.** Instructions-then-article is a
> *different prompt* from article-then-instructions, and this project ranks oracle
> consistency above cost (ADR-010). It needs a parity run — same articles, both orders,
> compare label distributions against the ν decoder noise floor — **before** any retrain
> uses it. Untested. Follow-up on #103.

### AI Studio Postpay → Prepay coupling — DONE

> ⛔ **Coupling the owner must not miss: the Gemini fallback has its own
> deadline.** Google AI Studio forces **Postpay → Prepay by 2026-10-12** or the
> Gemini API is interrupted (email 2026-08-12, to jVeen1@gmail.com). Our oracle
> authenticates with an AI Studio **API key** (`ground_truth/secrets_manager.py`
> → `API_GEMINI_API_KEY`), so it is in scope. **Production is NOT in scope** —
> verified 2026-08-14: NexusMind's `get_gemini_key()` has **zero callers**
> outside its own module, the scoring path is the local Gemma student, and
> summarization is ollama. So the risk is a *silent oracle outage at the next
> retrain*, not a pipeline failure.
>
> **Action for the owner:** switch AI Studio to Prepay + enable auto-reload
> before 2026-10-12 — it is now on the critical path for oracle work, not
> housekeeping.
> ✅ **DONE — owner, 2026-10-12: switched to Prepay "last week"** (owner-reported; billing not
> checked from here, auto-reload not confirmed). Gemini oracle calls on 2026-10-07/08 succeeded.

### Correction 2026-08-17 — #109 Arm B names no judge model

> ⛔ **Correction 2026-08-17: this line used to read "#109 Arm B names Qwen3:14b +
> Phi4:14b". It does not.** #109's body names **no** judge model — that omission is
> precisely its blocking gap #1. The two names come from the **cd v5 multi-oracle
> precedent**, where they were actually run. Cite the precedent, not the issue.
