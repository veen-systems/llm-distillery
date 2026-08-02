# Filter Status

> **CLAUDE.md is authoritative.** This file keeps the extended per-filter MAE / data
> counts that don't fit in CLAUDE.md; if you just want current production state, read
> CLAUDE.md's Production Filters table. The tables below must be reconciled against it.
>
> <!-- verify: grep -qxF '<!-- prod-filters-table:start -->' memory/filter-status.md && grep -qxF '<!-- prod-filters-table:end -->' memory/filter-status.md && grep -q '^## Key Decisions' CLAUDE.md || { echo "FAIL: verify anchors missing"; exit 0; }; comm -23 <(awk '/^## Production Filters/,/^## Key Decisions/' CLAUDE.md | grep -E "^\| \*\*" | sed -E 's/^\| \*\*([a-z_-]+)\*\* \| (v[0-9]+).*/\1 \2/' | tr '-' '_' | grep -Ev "^(thriving|ai_engineering_practice) " | sort -u) <(awk '/prod-filters-table:start/,/prod-filters-table:end/' memory/filter-status.md | grep -E "^\| [a-z]" | awk -F'|' '{gsub(/ /,"",$2);gsub(/ /,"",$3); print $2, $3}' | tr '-' '_' | sort -u) | grep . && echo FAIL || echo PASS -->
>
> The check asserts every filter in CLAUDE.md's Production Filters table has a
> same-version row here (name separators normalized; `thriving` and
> `ai-engineering-practice` excluded — neither is a production filter here).
> This file may carry *extra* historical rows (cd v4, nr v2) — that's its job.
>
> **Anchoring history — two failures, both of the same kind.** (1) The original
> `diff | head -20` form compared two differently-formatted tables and could
> only ever emit MANUAL CHECK NEEDED. (2) Its 2026-08-01 replacement anchored
> its awk range on the literal `**Per-filter`, and the very next commit renamed
> that heading to `**Per-lens RULE prefilters:` — the range then ran unbounded
> to EOF and swept in unrelated sections. It still printed PASS, because
> `comm -23` tolerates junk in the second stream, so it looked healthy while
> checking something else entirely. Caught by adversarial review the same day.
>
> Hence: the range is now bounded by dedicated `prod-filters-table:{start,end}`
> HTML sentinels that carry no other meaning and so have no reason to be
> renamed, and the check **fails loudly if any anchor is missing** rather than
> silently widening. A verify that cannot fail is worse than no verify.

## Production Filters

<!-- prod-filters-table:start -->

| Filter | Ver | MAE | Cal. MAE | Data | Hub Repo | Deployed |
|--------|-----|-----|----------|------|----------|----------|
| uplifting | v7 | — | — | 5.3K | (none — file-copy to NexusMind only) | 2026-07-31 normalization REFIT (Apr-06 fit was unit-mismatched ×1.1976, LD#76/NM#279; raw 5.0 → norm 5.17, was ~3.0) |
| sustainability_technology | v3 | 0.72 | — | 10.6K | `jeergrvgreg/sustainability-technology-v3` | 2026-02-21 (retired from ovr.news — superseded by solutions v6) |
| solutions | v6 | 0.476 | — | 8.2K | `jeergrvgreg/solutions-filter-v6` | 2026-07-27 gate passed; normalization fitted 2026-07-28; LIVE. v6 weights on Hub 2026-07-30 (was: v4 repo shared — that mismatch + FILTER_VERSION 5.0 fixed in 403429d). |
| investment-risk | v6 | 0.497 | 0.465 | 10.4K | `jeergrvgreg/investment-risk-v6` | 2026-02-21 |
| cultural_discovery | v5 | — | 0.697 (val) | 8.5K | `jeergrvgreg/cultural-discovery-filter-v5` | 2026-07-31 multilingual topic gate added to prefilter (LD#86); **gate VALIDATED in production 2026-08-01 via NM#284 shadow: observed pass 0.255 vs declared 0.25 (n=2099, full cycle)** — but still NOT ENFORCED (NM#284); 2026-05-31 v5 (#62 flags; DeepSeek oracle) |
| cultural-discovery | v4 | 0.74 | — | 8K | `jeergrvgreg/cultural-discovery-v4` | 2026-02-20 (superseded by v5) |
| belonging | v1 | 0.534 | 0.489 | 7.4K | `jeergrvgreg/belonging-filter-v1` | 2026-07-31 normalization REFIT (Mar-30 fit drifted, survivors under-ranked +1.0–2.1; NM#279) |
| nature_recovery | v4 | recall 0.65 / prec 0.85 @3.75 | 0.48 | 3.9K | `jeergrvgreg/nature-recovery-filter-v4` | 2026-07-10 (DeepSeek oracle; #70 protection scope; op-point 3.75 wired into TIER_THRESHOLDS + validated in prod output, F1) |
| nature_recovery | v2 | 0.63 | 0.53 | 3.5K | `jeergrvgreg/nature-recovery-filter-v2` | 2026-04-19 — kept as fallback (rollback = delete v4 dir; discovery falls back) |
| foresight | v1 | 0.744 | 0.75 | 3.5K | `jeergrvgreg/foresight-filter-v1` | PARKED 2026-04-16 (#43) |

<!-- prod-filters-table:end -->

**Per-lens RULE prefilters: DECLARED but NOT ENFORCED in production (NM#284, found 2026-08-01).** Scope precisely: this is the per-lens rule prefilter only — `filters/{name}/v{N}/prefilter.py`, the ADR-018/019 `BasePreFilter` subclasses (regex/keyword on title+content). Every filter's `config.yaml` says `prefilter: enabled: true`, but the GPU scorer builds each with `use_prefilter=False` (NexusMind `deploy/gpu-server/main.py` L915) and calls `score_batch(skip_prefilter=True)` (L1318), which makes the guard `if self.use_prefilter and not skip_prefilter` false in **both** `filter_base_scorer.score_batch` and `hybrid_scorer.score_batch`. Dead since `66582e7` (2026-02-10).

**Verified NOT affected** (each checked, not assumed): the **e5 probe** (Phase 2 of `hybrid_scorer.score_batch`, ungated by `skip_prefilter` — live log shows `stage1_low=7..19, stage2=77..85` per 100 articles); **commerce / obituary / violence** (separate `src/preprocessing/` stages with their own stamps); the **NM#189 source-type allowlist** (`shadow_mode: false`, enforced in `src/scoring/source_filter.py`); and the same rule prefilters in the llm-distillery oracle/training path.

⚠️ **Do NOT verify prefilter state from `data/filtered/{name}/filtered_*.jsonl`.** That file only receives rows where `passed_prefilter` is true NexusMind `scripts/main.py`’s `if result["passed_prefilter"]:` write guard, so it is 100% passers by construction and can never show a block. An earlier version of this note cited "0 blocks per cycle" from exactly that file — invalid evidence, corrected 2026-08-01. Use instead the pipeline line `Filter X complete (N scored, M prefiltered)` and the NM#284 shadow log, both of which see pre-drop counts. The ~350–360 `prefiltered` per lens per cycle is the source-type allowlist plus validation failures, **not** lens rules (five lenses with different rules landing within 10 of each other is the tell; investment_risk differs at 821 because it also excludes `academic` + `social`).

The finding rests on: (1) the code above; (2) the in-path shadow measurement — cd reports `observed_pass` 0.255 pooled over 2,099 articles *at the scorer*, which would read ≈1.000 if the gate were already enforcing upstream; (3) magnitude — cd's gate blocks 71% on replay vs 15.6% actually dropped.

NM#284 stage 1 (shadow measurement, deployed 2026-08-01 `5d53774`) logs observed
vs declared pass rate per batch. **Superseded by the 2026-08-02 measurement
(NM#285) — the first-cycle n≈2,099 table is no longer the reference.**

Full-contract replay, 4 cycles, n=8,283 per filter (same-row FULL vs
`{title, content}` A/B, so the truncation effect is isolated):

| filter | observed (full) | declared | length blocks | lens blocks | truncation effect |
|---|---|---|---|---|---|
| cultural_discovery v5 | 0.2605 | 0.25 | 0 | 6,103 | +0.0005 |
| uplifting v7 | 0.5873 | 0.20 | 2,949 | 469 | +0.0028 |
| investment_risk v6 | 0.7605 | *(none)* | 1,454 | 117 | +0.0097 |
| belonging v1 | 0.6321 | 0.15 | 2,950 | 99 | +0.0008 |
| nature_recovery v4 | 0.6438 | ~~0.85~~ **deleted** | 2,950 | **0** | +0.0000 |
| solutions v6 | 0.6438 | ~~0.20~~ **deleted** | 2,950 | **0** | +0.0000 |

Three things this replaced:

1. **The "mismatch" verdicts were not drift.** `nature_recovery v4` and
   `solutions v6` declare `EXCLUSION_PATTERNS = {}` by design (commerce upstream,
   ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides — a no-op with
   nothing to override. Both reduce to `validate_article()` +
   `MIN_CONTENT_LENGTH` and are byte-identical because they are the same filter.
   `expected_pass_rate` **deleted** from both (`3ed47e1`), not corrected: 0.644 is
   "fraction of articles ≥300 chars", a corpus statistic.
2. **"Stage 2 is a global short-content gate" is REFUTED** (#93). Length is
   87–100% of blocking for four of six filters, and a length gate is the wrong
   shape — short content clearing an op-point is as likely to be genuine as long
   content (uplifting 67% vs 65% oracle-validated). Fix is a cap/penalty.
3. **investment_risk's logged rate is biased by the shadow denominator**, which
   counts articles `source_filter` discards *after* scoring (2,193 of 8,765).
   ⚠️ Treat **0.129 as an upper bound on the discrepancy, not a measured bias**
   (corrected 2026-08-02): the excluded rows' true pass rate is UNMEASURED. The
   0.008 figure I first quoted came from `data/raw/`, which is pre-enrichment
   and therefore invalid for anything length-dependent; the only other estimate
   is circular. Measuring it properly needs the pipeline instrumented, not a
   file replayed. See `memory/nexusmind-data-sources.md`.

**cultural_discovery's rate matches and is still not safe to enforce** — 15.5%
of surfacing articles blocked, 0% of high tier (#86). Rate agreement and
safety-to-enforce are independent properties. The loss is **entirely
`no_cultural_topic_signal`** (9.9% en vs 19.2% non-en; the other three rules fire
*more* on English) — uneven `TOPIC_GATE_PATTERNS` keyword coverage, not a
language effect: German 4.9% and French 5.3% sit *below* English.

**Runtime content-type caps: NONE (2026-07-14).** NexusMind's `cap_triggers.py` `_TRIGGER_REGISTRY` is empty, so `cap_applied` is permanently `null` on every filter. `nature_recovery/climate_doom` was the only one ever deployed (2026-05-08, #161) and was retired: 3 production bites, 3 false positives, 0 saves — all three the trigger word inside a non-doom construction (`evitar su extinción`, `en peligro crítico de extinción`, `deforestation-free`), which a polarity-blind regex cannot see. #161's actual cause was `normalization.json` fitted at raw ≥ 1.5 instead of the 4.0 tier threshold, inflating correctly-scored doom (raw 2.2–3.3) to normalized 5.2–8.3. Filters' `config.yaml` `content_type_caps` still declare the **oracle** contract and are inert at runtime; the scorer log reports them as INERT. Enforced by `tests/unit/test_normalization_invariant.py` (since 2026-07-16: raw_min must equal the op-point ±0.01 — the fitter anchors the CDF's lower edge there by construction; the old `[op_point, 4.5]` band is gone).

**Normalization (ADR-014, refit 2026-07-10):** `cultural_discovery v5` + `investment_risk v6` now ship `percentile` normalization.json (were silently on linear `scale_factor` — the `version`/`filter_version` fitter bug). `nature_recovery v4` ships NO normalization (fresh version, `score_scale_factor 1.0`); refit due at ≥200 v4 prod articles (#72).

Note: Hub repo naming is inconsistent — some use `{filter}-v{N}`, others use `{filter}-filter-v{N}`. Deploy scripts rely on the name embedded in `inference_hub.py`, so this doesn't break anything, but it's worth normalizing at the next bump.

All use Gemma-3-1B base + LoRA. All have local, Hub, and hybrid inference paths.

## In Development

| Filter | Ver | Status |
|--------|-----|--------|
| thriving | v1 | PARKED indefinitely (ADR-015) — orthogonal lens design caused bimodal distribution |
| solutions | v6 | **LIVE** — gate passed 2026-07-27 (F1 0.739), normalization fitted 2026-07-28, own Hub repo since 2026-07-30. |
| foresight | v1 | PARKED (#43) — merged into solutions. Dir kept for rollback, delete ~2026-08-01 |

<!-- NOTE: consumer-side concerns (which ovr.news lens/tab uses which filter, frontend rollout)
     live in the NexusMind and ovr.news repos. This repo produces filters; mapping filters to
     product surfaces is a downstream concern. -->

## Repo-wide audit (2026-07-27)

Ran `scripts/deployment/verify_filter_package.py --check-hub` across every `filters/*/v*/`.

- `ai-engineering-practice/v2` — `config.yaml filter.version` says 1.0 in a v2 dir → **REMOVED** (LD#49)
- `sustainability_technology/v2` — cross-version imports from v1 (#44 failure mode, pre-v3) → **REMOVED** (LD#49)
- `cultural-discovery/v3` — no default `repo_id` in inference_hub.py signature → **REMOVED** (LD#49)
- `investment-risk/v5` — references placeholder `your-username/investment-risk-filter-v5` → **REMOVED** (LD#49)
- `uplifting/v5` — Hub `last_modified` before local `training_history.json` → **REMOVED** (LD#49)
- `signs_of_wisdom/v1` — package structure incomplete (0 checks pass) → **REMOVED** (LD#49)

All 6 superseded by newer versions in production. Cleaned up 2026-07-27.

<!-- verify: python -c "import huggingface_hub" 2>/dev/null || { echo ERROR: huggingface_hub not installed locally; exit 0; }; PYTHONPATH=. python scripts/deployment/verify_filter_package.py --filter filters/nature_recovery/v2 --check-hub > /dev/null && echo PASS || echo FAIL -->

## Other Filters (not ovr.news)

| Filter | Ver | Status |
|--------|-----|--------|
| ai-engineering-practice (→ augmented-engineering) | v2 | Ready for oracle scoring |
| seece | v1 | Concept only |

## Standalone filter products (separate platforms)

- **augmented-engineering** (renamed from ai-engineering-practice)
- **health-tech** (planned)
- **education** (planned)
- **investment-risk** (deployed, also used standalone)

## Backlog

- Commerce prefilter v2 — v1 needs rework for multilingual embeddings and context size
- train.py nested model/model/ fix (#29)
