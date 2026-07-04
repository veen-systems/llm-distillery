---
name: oracle-pricing-scheduling
description: DeepSeek V4 peak/valley pricing — schedule oracle batch jobs off-peak (avoid 08:00–12:00 CEST)
metadata:
  type: reference
---

DeepSeek V4 officialised mid-July 2026, introducing **peak/valley API pricing**. Same batch job costs **2x** at peak vs regular. This is a scheduling lever, not a price hike — off-peak stays cost-neutral vs what we paid for cd v5.

**Peak windows (UTC):** 01:00–04:00 and 06:00–10:00. In CEST (summer, UTC+2): 03:00–06:00 and **08:00–12:00**. The morning peak is the trap — it overlaps normal working hours, exactly when you'd kick off a job at your desk.

**Rule: start big oracle batch runs after ~noon CEST (or overnight, not 03:00–06:00).** Our scoring is async batch work, so this is free — pure scheduling discipline.

**deepseek-v4-flash pricing** ($/1M tokens, regular / peak):
- input cache hit: 0.0028 / 0.0056
- input cache miss: 0.14 / 0.28  ← dominant cost
- output: 0.28 / 0.56

**Cost per article** (v5-class ~8K-token prompts, ~14% cache hit): ~$0.0011 off-peak / ~$0.0022 peak. An 8K-article retrain ≈ $8.90 off-peak vs ~$17.80 peak (cd v5 actual under old pricing was $10.36). Cache-hit input is negligible; our low cache-hit rate barely matters.

**Alternatives for context:** Gemini Batch API ~$0.0018/article (50% off, 24h async) now sits at roughly DeepSeek *peak* pricing — so DeepSeek off-peak remains cheapest, but the gap closes if forced into peak.

Effective mid-July 2026 with 24h advance email notice. See [[cd-v5-reference-status]] (DeepSeek-as-default-oracle precedent). Next batch job on deck: solutions v4 (ADR-020 validation case).
