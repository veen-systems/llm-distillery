---
name: oracle-pricing-scheduling
description: Oracle cost — DeepSeek hiked 2026-08-16 (off-peak no longer cheapest; Gemini Batch wins); Gemini AI Studio forces Prepay by 2026-10-12; still avoid 08:00–12:00 CEST; #124 self-hosted oracle is a residency play, not a cost play
metadata:
  type: reference
---

> 🔴 **THE NOTICE LANDED — effective 16:00 UTC, 2026-08-16 (email dated
> 2026-08-14 16:58 +0800, to jveen1@proton.me).** Both the announcement email and
> the docs page confirm: **peak/off-peak billing, off-peak = half of peak, and
> every tier — off-peak included — bills ABOVE today's flat rate.** The peak
> windows are **unchanged** (01:00–04:00 and 06:00–10:00 UTC), so the scheduling
> rule below still holds; what changed is that off-peak is no longer cheap.
>
> ⚠️ **The exact new per-1M rates are NOT established.** The email carries no
> numbers, and two web sources disagree on magnitude — one docs summary gives
> flash off-peak 0.007 / 0.22 / 0.66 (hit/miss/output, ×2.5 / ×1.57 / ×2.36 vs
> today), a pricing round-up gives blended off-peak ratios of ×7.84 / ×1.96 /
> ×2.94. **Neither is owner-verified; read the rates off the Open Platform
> console before committing spend.**
>
> **The conclusion is robust to which is right.** Anchoring on cd v5's *actual*
> $10.36 / 8K articles ($0.001295/article, implying ~8K input at 14% cache hit
> and ~1.2K output), the new off-peak per-article cost is **$0.0023–0.0029
> (×1.8–2.2)**, i.e. above the **+64%** threshold recorded below under either
> source. **→ Gemini Batch (~$0.0018/article) is now the cheapest oracle, and
> the DeepSeek-as-default precedent from cd v5 is VOID.** New DeepSeek peak is
> ~$0.0046–0.0058/article — dearer than Gemini Flash *real-time*, so it is now
> unambiguously wrong. Per 8K-article retrain: DeepSeek off-peak $18–23, Gemini
> Batch ~$14.40, DeepSeek peak $37–46. Still single/double-digit dollars — this
> picks the default oracle, it does not threaten affordability.
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

**Peak windows (UTC):** 01:00–04:00 and 06:00–10:00. In CEST (summer, UTC+2): 03:00–06:00 and **08:00–12:00**. The morning peak is the trap — it overlaps normal working hours, exactly when you'd kick off a job at your desk.

**Rule: start big oracle batch runs after ~noon CEST (or overnight, not 03:00–06:00).** Our scoring is async batch work, so this is free — pure scheduling discipline.

**deepseek-v4-flash pricing** ($/1M tokens, regular / peak):
- input cache hit: 0.0028 / 0.0056
- input cache miss: 0.14 / 0.28  ← dominant cost
- output: 0.28 / 0.56

**Cost per article** (v5-class ~8K-token prompts, ~14% cache hit): ~$0.0011 off-peak / ~$0.0022 peak. An 8K-article retrain ≈ $8.90 off-peak vs ~$17.80 peak (cd v5 actual under old pricing was $10.36). Cache-hit input is negligible; our low cache-hit rate barely matters.

**Alternatives for context:** Gemini Flash 2.5 real-time ~$0.003–0.004/article with v5-class 8K-token prompts (the $0.001 figure from the 1.5 Flash era is stale — moved here from CLAUDE.md, 2026-07-31 audit). Gemini Batch API ~$0.0018/article (50% off, 24h async) now sits at roughly DeepSeek *peak* pricing — so DeepSeek off-peak remains cheapest, but the gap closes if forced into peak. DeepSeek cd v5 actual: $10.36 for 8K articles, 14% cache hit.

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
