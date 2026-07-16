# Filter Status

> **CLAUDE.md is authoritative.** This file keeps the extended per-filter MAE / data
> counts that don't fit in CLAUDE.md; if you just want current production state, read
> CLAUDE.md's Production Filters table. The tables below must be reconciled against it.
>
> <!-- verify: diff <(grep -E "^\| \*\*[a-z_]+" CLAUDE.md | head -20) <(grep -E "^\| [a-z]" memory/filter-status.md | head -20) > /dev/null && echo PASS || echo MANUAL CHECK NEEDED -->

## Production Filters

| Filter | Ver | MAE | Cal. MAE | Data | Hub Repo | Deployed |
|--------|-----|-----|----------|------|----------|----------|
| uplifting | v7 | — | — | 5.3K | (none — file-copy to NexusMind only) | 2026-04 (hybrid inference added) |
| sustainability_technology | v3 | 0.72 | — | 10.6K | `jeergrvgreg/sustainability-technology-v3` | 2026-02-21 |
| investment-risk | v6 | 0.497 | 0.465 | 10.4K | `jeergrvgreg/investment-risk-v6` | 2026-02-21 |
| cultural_discovery | v5 | — | 0.697 (val) | 8.5K | `jeergrvgreg/cultural-discovery-filter-v5` | 2026-05-31 (resolves #62 leakage via F/G/H/I/K soft-penalty flags; DeepSeek oracle) |
| cultural-discovery | v4 | 0.74 | — | 8K | `jeergrvgreg/cultural-discovery-v4` | 2026-02-20 (superseded by v5) |
| belonging | v1 | 0.534 | 0.489 | 7.4K | `jeergrvgreg/belonging-filter-v1` | 2026-03-04 |
| nature_recovery | v4 | recall 0.65 / prec 0.85 @3.75 | 0.48 | 3.9K | `jeergrvgreg/nature-recovery-filter-v4` | 2026-07-10 (DeepSeek oracle; #70 protection scope; op-point 3.75 wired into TIER_THRESHOLDS + validated in prod output, F1) |
| nature_recovery | v2 | 0.63 | 0.53 | 3.5K | `jeergrvgreg/nature-recovery-filter-v2` | 2026-04-19 — kept as fallback (rollback = delete v4 dir; discovery falls back) |
| foresight | v1 | 0.744 | 0.75 | 3.5K | `jeergrvgreg/foresight-filter-v1` | PARKED 2026-04-16 (#43) |

**Runtime content-type caps: NONE (2026-07-14).** NexusMind's `cap_triggers.py` `_TRIGGER_REGISTRY` is empty, so `cap_applied` is permanently `null` on every filter. `nature_recovery/climate_doom` was the only one ever deployed (2026-05-08, #161) and was retired: 3 production bites, 3 false positives, 0 saves — all three the trigger word inside a non-doom construction (`evitar su extinción`, `en peligro crítico de extinción`, `deforestation-free`), which a polarity-blind regex cannot see. #161's actual cause was `normalization.json` fitted at raw ≥ 1.5 instead of the 4.0 tier threshold, inflating correctly-scored doom (raw 2.2–3.3) to normalized 5.2–8.3. Filters' `config.yaml` `content_type_caps` still declare the **oracle** contract and are inert at runtime; the scorer log reports them as INERT. Enforced by `tests/unit/test_normalization_invariant.py` (since 2026-07-16: raw_min must equal the op-point ±0.01 — the fitter anchors the CDF's lower edge there by construction; the old `[op_point, 4.5]` band is gone).

**Normalization (ADR-014, refit 2026-07-10):** `cultural_discovery v5` + `investment_risk v6` now ship `percentile` normalization.json (were silently on linear `scale_factor` — the `version`/`filter_version` fitter bug). `nature_recovery v4` ships NO normalization (fresh version, `score_scale_factor 1.0`); refit due at ≥200 v4 prod articles (#72).

Note: Hub repo naming is inconsistent — some use `{filter}-v{N}`, others use `{filter}-filter-v{N}`. Deploy scripts rely on the name embedded in `inference_hub.py`, so this doesn't break anything, but it's worth normalizing at the next bump.

All use Gemma-3-1B base + LoRA. All have local, Hub, and hybrid inference paths.

## In Development

| Filter | Ver | Status |
|--------|-----|--------|
| thriving | v1 | PARKED indefinitely (ADR-015) — orthogonal lens design caused bimodal distribution |
| sustainability_technology | v4 | Design phase (#43) — broadened scope (governance/community solutions + clean-tech) |
| foresight | v1 | PARKED (#43) — merging into sustainability_technology v4 |

<!-- NOTE: consumer-side concerns (which ovr.news lens/tab uses which filter, frontend rollout)
     live in the NexusMind and ovr.news repos. This repo produces filters; mapping filters to
     product surfaces is a downstream concern. -->

## Repo-wide audit (2026-04-19)

Ran `scripts/deployment/verify_filter_package.py --check-hub` across every `filters/*/v*/`. Current-production filters all pass except uplifting v7 (no Hub repo — production uses file-copy via `deploy_to_nexusmind.sh`, not Hub download; CLAUDE.md's "HF Hub, private" claim for v7 is inaccurate).

**Historical / superseded versions that fail verification** (not in production, low urgency):

- `sustainability_technology/v2` — cross-version imports from v1 (#44 failure mode, pre-v3)
- `ai-engineering-practice/v2` — `config.yaml filter.version` says 1.0 in a v2 dir
- `cultural-discovery/v3` — no default `repo_id` in inference_hub.py signature
- `investment-risk/v5` — references placeholder `your-username/investment-risk-filter-v5` (deploy abandoned mid-flow)
- `uplifting/v5` — Hub `last_modified` is before local `training_history.json` (weights never uploaded after training re-ran)
- `signs_of_wisdom/v1` — package structure incomplete (0 checks pass)

These are all superseded by newer versions in production. Clean up or delete at next audit.

<!-- verify: PYTHONPATH=. python scripts/deployment/verify_filter_package.py --filter filters/nature_recovery/v2 --check-hub > /dev/null && echo PASS || echo FAIL -->

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
