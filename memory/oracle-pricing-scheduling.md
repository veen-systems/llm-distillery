---
name: oracle-pricing-scheduling
description: Oracle cost — both rate cards verified 2026-08-24, but Gemini Batch is a price we CANNOT PAY (no .batches call site, 2026-08-25), so among IMPLEMENTED paths DeepSeek off-peak wins by 1.74x; the answer is a RATIO (DeepSeek needs input/output < 8.4, ours are 20-43), not an anchor; the real lever is the per-prompt CACHE CEILING set by where build_prompt inserts the article (1.5%-35.7%), which flips the ranking at 19-27%; Gemini AI Studio forces Prepay by 2026-10-12
metadata:
  type: reference
---

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
> ⛔⛔ **RE-DERIVED 2026-08-24 FROM COUNTED TOKENS — AND THE CONCLUSION INVERTS.
> `Gemini Batch` IS A PRICE WE CANNOT PAY: there is no Batch API call site in this
> repo.** `ground_truth/batch_scorer.py` (line 819) and `scripts/score_ollama_oracle.py`
> (line 266) both call `models.generate_content` — the **real-time** endpoint — and
> `.batches` appears in no `.py` file in the tree. Every comparison in this file since
> 2026-08-16 has been measuring DeepSeek against a **rate card we have never been
> billed at**. Against the Gemini path that actually exists, **DeepSeek off-peak is
> cheaper at every measured shape — $0.001756 vs $0.003052 on `uplifting v7`, a factor
> of 1.74** — and the cd v5 DeepSeek-as-default precedent is **NOT void**. Implementing
> Gemini Batch is a prerequisite for the switch, not a detail; until it exists the
> honest comparison is the `GemRealtm` column.
> ⚠️ This is the [[feedback-verify-call-path]] shape again: the price was verified, the
> *ability to obtain it* never was.
> <!-- verify: R=/home/jeroen/repos/veen-systems/llm-distillery; if [ ! -d "$R" ]; then echo "CANNOT VERIFY: repo not at that path"; elif grep -rlE '\.batches\.|batches\.create' --include=*.py "$R"/ground_truth "$R"/scripts "$R"/filters 2>/dev/null | grep -qv 'scripts/analysis/oracle_cost.py'; then echo "CLAIM REFUTED: a Batch API call site now exists — re-derive the oracle choice"; exit 1; else echo "still absent: no .batches call site in ground_truth/, scripts/ or filters/"; fi -->
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
> <!-- verify: python3 scripts/analysis/oracle_cost.py | grep -m1 'rate-card check' -->
>
> ⭐⭐ **The 0.3%-vs-14% cache puzzle is SOLVED, and it is structural.** `build_prompt`
> substitutes the article **into the middle** of the template
> (`prompt_template.replace(PROMPT_PLACEHOLDER, summary)`), so everything after
> `[Paste the summary of the article here]` is unique per request and a prefix cache can
> only ever hit what precedes it. That fraction is a per-prompt constant — its **cache
> ceiling**:
>
> | prompt | placeholder at | ceiling |
> |---|---|---|
> | `human_thriving/v8` | 617 / 42,406 | **1.5%** |
> | `nature_recovery/v4` | 682 / 31,190 | 2.2% |
> | `uplifting/v7` | 617 / 23,662 | 2.6% |
> | `belonging/v1` | 600 / 19,080 | 3.1% |
> | `investment_risk/v6` | 1,806 / 17,772 | 10.2% |
> | `cultural_discovery/v5` | 6,393 / 37,894 | **16.9%** |
> | `solutions/v6` | 14,968 / 41,871 | **35.7%** |
>
> cd v5's 14% is its own ceiling (16.9%), **not a project constant**; nature_recovery's
> 0.34% sits under the v1/v2 template's 3.2% (no v3 prompt is on disk — nearest proxy).
> ⚠️ The ceiling is a **char-share proxy for a token quantity**: `nr_v4_positives.log`
> came in at 4.9% against that 3.2%, so treat it as an order-of-magnitude bound, not a
> hard cap. ⚠️ Note also how that log **decays 14% → 7% → 5% across progress lines** to a
> 4.9% total — a mid-run cache reading is not a run cache rate.
>
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
>
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
> **Provenance of the challenge (2026-08-23):** an outside GitHub account
> (`xyzs996`, `author_association: NONE`, **not** DeepSeek) posted the
> back-solve-to-a-dead-heat argument on
> [#103](https://github.com/veen-systems/llm-distillery/issues/103#issuecomment-5382743370).
> Its rate table and its input arithmetic check out against the vendor page; its
> conclusion differs from ours *only* because it anchored on our rounded $0.0011
> rather than the cd v5 invoice. ⚠️ **Two of its claims remain UNVERIFIED and are
> not adopted here:** (a) that the weekend rule took effect
> 2026-08-22T16:00Z / 00:00 Beijing 2026-08-23 — the vendor page carries **no
> effective date**; and (b) that the Mon–Fri boundary is read in Beijing
> `+08:00`, making the weekend 16:00 Fri → 16:00 Sun UTC — the page fixes the
> *windows* in UTC and says nothing about the weekday. Its argument that the two
> readings cannot disagree *today* is arithmetically sound (both peak windows lie
> outside 16:00–24:00 UTC, the only band where a UTC and a +08:00 weekday reading
> differ), so this is a latent trap, not a live error: **it bites the day DeepSeek
> moves a window.**
>
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
>
> 🚫 **There is NO lighter DeepSeek tier to retreat to.** Verified 2026-08-14
> against the live API with our key: `GET https://api.deepseek.com/models`
> returns exactly two IDs — `deepseek-v4-flash` and `deepseek-v4-pro` (~3.1×
> flash on input-cache-miss). No lite/mini tier, and the V3-era models are gone
> as distinct IDs. Flash is the floor, and the floor is what is rising.
> ⚠️ **And do NOT "pin" the model name to save ambiguity** — our call sites use
> the alias `deepseek-chat`, which resolves to v4-flash in *non-reasoning* mode;
> the literal `deepseek-v4-flash` enables reasoning mode and returns **empty
> `content`**, breaking the score parser. See `memory/gotcha-log.md` 2026-08-14.
> The real levers are Gemini Batch (~$0.0018/article), local judges on b650 at
> $0 (`scripts/score_ollama_oracle.py`),
> and the off-peak scheduling rule below, which survives the hike unchanged.
> ⛔ **Correction 2026-08-17: this line used to read "#109 Arm B names Qwen3:14b +
> Phi4:14b". It does not.** #109's body names **no** judge model — that omission is
> precisely its blocking gap #1. The two names come from the **cd v5 multi-oracle
> precedent**, where they were actually run. Cite the precedent, not the issue.
> The self-hosted-oracle question now has its own issue: **#124**.
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

**Peak windows (UTC):** 01:00–04:00 and 06:00–10:00, **Monday through Friday** (vendor page, 2026-08-23). In CEST (summer, UTC+2): 03:00–06:00 and **08:00–12:00**. The morning peak is the trap — it overlaps normal working hours, exactly when you'd kick off a job at your desk. ⚠️ **There are TWO windows, and a rule naming only "08:00–12:00 CEST" misses the 03:00–06:00 one** — a batch started at 04:00 CEST pays peak.

**Rule: run big oracle batches at the WEEKEND — time-of-day then stops mattering entirely.** Failing that, Mon–Fri: start after ~noon CEST (or overnight, avoiding 03:00–06:00). Our scoring is async batch work, so this is free — pure scheduling discipline.

⚠️ **The windows are fixed in UTC; the CEST mapping is not.** When CEST → CET on **2026-10-25** every local time above shifts an hour (peak becomes 02:00–05:00 and 07:00–11:00 local). Prefer reasoning in UTC. See also the banner's unverified-timezone note on where the *weekday* boundary falls.

**deepseek-v4-flash pricing — ⛔ HISTORICAL, pre-2026-08-16 only, kept to date the change. For current rates use the banner's table.** ($/1M tokens, regular / peak):
- input cache hit: 0.0028 / 0.0056
- input cache miss: 0.14 / 0.28  ← dominant cost
- output: 0.28 / 0.56

**Cost per article** (v5-class ~8K-token prompts, ~14% cache hit): ~$0.0011 off-peak / ~$0.0022 peak. An 8K-article retrain ≈ $8.90 off-peak vs ~$17.80 peak (cd v5 actual under old pricing was $10.36). Cache-hit input is negligible; our low cache-hit rate barely matters.

**Alternatives for context:** Gemini Flash 2.5 real-time ~$0.003–0.004/article with v5-class 8K-token prompts (the $0.001 figure from the 1.5 Flash era is stale — moved here from CLAUDE.md, 2026-07-31 audit). Gemini Batch API ~$0.0018/article (50% off, 24h async) now sits at roughly DeepSeek *peak* pricing (⛔ **that $0.0018 was never anchored** — measured 2026-08-24 it is $0.001175–$0.002127 depending on the prompt; see the banner) — so DeepSeek off-peak remains cheapest, but the gap closes if forced into peak. DeepSeek cd v5 actual: $10.36 for 8K articles, 14% cache hit (⛔ **that 14% is cd v5's structural ceiling, 16.9% — not a project constant**; nature_recovery measures 0.34% against a 3.2% ceiling).

Effective mid-July 2026 with 24h advance email notice. See [[cd-v5-reference-status]] (DeepSeek-as-default-oracle precedent). Next batch job on deck: solutions v4 (ADR-020 validation case).

## The third option: a self-hosted oracle (#124, 2026-08-17)

Both levers above pick a **commercial** oracle. There is a third axis — host the oracle
ourselves — and it is **not a cost play**. Prompted by the owner asking whether
[lyceum.technology](https://lyceum.technology/) (Berlin, EU-sovereign GPU cloud, H100 SXM
$2.79/hr, A100 SXM $1.59/hr, per-second billing) is useful to us. **Ruling: important
experiments, not now.** Filed as **#124**, P3-low.

**Two code facts, verified by reading source 2026-08-17 — not inferred from config:**

- `scripts/score_ollama_oracle.py` **already works**: byte-for-byte prompt parity with
  `batch_scorer.py` and `validate_deepseek_oracle.py`, scores the frozen 522-article cd v5
  set, and `qwen3:14b` / `phi4:14b` have been through it. Host is one hardcoded constant,
  `OLLAMA_HOST = "http://gpu-server:11434"`.
- ⛔ **The canonical oracle cannot be retargeted.** `ground_truth/batch_scorer.py` accepts
  only `claude/gemini/gemini-pro/gemini-flash/gpt4`, and `_init_client` builds
  `openai.OpenAI(api_key=...)` with **no `base_url` anywhere in `ground_truth/*.py`**. So a
  *real retrain* cannot use an OpenAI-compatible vLLM endpoint today. Small change,
  but it is a precondition, not a detail. **Note also that DeepSeek has no backend in
  `batch_scorer.py` at all** — every DeepSeek call site lives in
  `filters/common/obituary_detector/validation/`, not in the filter oracle path.

**The cost arithmetic does not decide it (ESTIMATED, wide bars).** A v5-class 8K-article
retrain is ~64M input + ~9.6M output tokens and is **prefill-dominated** (~6.7:1), so
break-even vs Gemini Batch's $14.40 is ~5.2 H100-hours. Estimated: 70B fp8 ≈ 4.5–7 hrs
($12–20, a wash), 32B ≈ 2.5–3.5 hrs ($7–10), 14B on b650 **$0**. **Renting saves nothing at
the size that would justify renting, and only wins at sizes we nearly run for free.**
Per [[feedback-nothing-verifies-an-estimate]] treat these as estimates until measured.

**What it does buy, and this is the actual case:** EU residency for full article text
(closing the open carve-out in `docs/decisions/2026-08-05-tdm-opt-out-training-data.md`),
independence from the two dated vendor forcing functions above, and model sizes past
b650's 24 GB ceiling.

⚠️ **Do not import the cross-box parity objection from the student path.** It was raised
and withdrawn in the originating conversation. Bit-level box determinism
([[b650-gpu]], `scripts/verification/box_parity.py`) governs **student scoring**, where a
verdict flip at an op-point is a production defect. Oracle *labelling* has a far larger
intrinsic decoder noise floor (ν = 0.436 / 0.687, see [[filter-status]] and the #109 Arm A
follow-up), so an ephemeral rented box is an acceptable labelling instrument.
