---
name: oracle-pricing-scheduling
description: DeepSeek V4 peak/valley pricing — schedule oracle batch jobs off-peak (avoid 08:00–12:00 CEST)
metadata:
  type: reference
---

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
