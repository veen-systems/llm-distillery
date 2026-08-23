---
status: Accepted
date: 2026-04-28
deciders: [team]
superseded_by:
---

# ADR-018: Declarative prefilter shape (BasePreFilter extension)

## Context

The 7 production-filter `prefilter.py` files diverged structurally as the project grew. Same conceptual problem (block off-topic noise before LLM scoring), seven different implementations:

- **Pattern containers**: 4/7 use flat lists per category, 1 uses a dict, 2 inline lists.
- **Override mechanisms**: 5 distinct shapes across 7 filters (pattern-pair, keyword substring, source allowlist, count threshold, none).
- **Compile sites**: 5/7 compile in `__init__`, 2 inline at apply time.
- **Class/version drift**: 3/7 have class names that don't match their directory version.

Symptoms this divergence has produced:
- #45 (belonging obit) and #46 (sustech clickbait) shipped per-filter regex patches that would have been one shared change in a harmonized world.
- The #45 RIP/IGNORECASE trap was filter-specific because each filter compiles patterns its own way (gotcha-log 2026-04-28).
- #51 (universal obituary detector) wants a per-filter consumption hook — much cleaner if every filter exposes the same shape.

`BasePreFilter` already carries shared bones (validation, text cleaning, pattern utilities) but doesn't dictate the *shape* of how subclasses register exclusion patterns or override keywords.

## Options Considered

### Option A: Status quo, fix per-filter as bugs surface

| Pros | Cons |
|------|------|
| No refactor risk | Each future bug is a new bespoke patch |
| | Universal detectors (#51) fight 7 different consumption shapes |
| | Class/version drift compounds |

### Option B: Declarative pattern registry on `BasePreFilter` (additive, backwards-compatible)

| Pros | Cons |
|------|------|
| Subclasses become ~50-line declarations | Migration is per-filter work (~12-16h total) |
| Universal detectors (#51) get one consumption hook | Backwards-compatible only — old shape lingers until each filter is migrated |
| Class-name drift fixed during per-filter migration | |
| Compile-site discipline (one place) prevents IGNORECASE-trap-class bugs | |

### Option C: Top-down rewrite of all 7 prefilters in one PR

| Pros | Cons |
|------|------|
| Clean cutover | High blast radius — 7 filters, 7 deployments to verify in one shot |
| | Hard to roll back per-filter |
| | Violates "deploy independently with smoke test" pattern |

## Decision

**We chose Option B.**

Extend `BasePreFilter` with a declarative registry of class attributes (`EXCLUSION_PATTERNS`, `OVERRIDE_KEYWORDS`, `POSITIVE_PATTERNS`, `POSITIVE_THRESHOLD`) plus a default `apply_filter()` that drives the standard pipeline (validate → length check → exclusions-with-override → filter-specific final check → passed). Existing filters that override `apply_filter()` directly continue to work unchanged; new and migrated filters use the declarative form.

> **Amendment 2026-08-03 (llm-distillery#93):** the length check is no longer a
> stage of this pipeline. It reduces to *validate → exclusions-with-override →
> filter-specific final check → passed*. Measurement (NexusMind#284/#285, #92)
> showed the 300-char floor was 87–100% of everything four of six production
> prefilters blocked, and that short content clearing an op-point is as likely
> to be genuine as long content. Its actual rationale — LLM framework leakage —
> is labelling-time, so it moved to the oracle path
> (`ground_truth.batch_scorer.make_oracle_prefilter`). The scoring path stamps
> `content_length` on every result and applies at most one config-gated cap
> (`short_content.cap`, off everywhere until #92's confound is resolved), per
> ADR-022. `validate_article` still rejects empty content — empty is not short.

Each filter migrates as its own PR with a smoke test, in priority order:
sustainability_technology/v3 → belonging/v1 → cultural-discovery/v4 → uplifting/v7 → investment-risk/v6 → nature_recovery/v2 → foresight/v1.

Class-name version drift (3 of 7) is fixed in a separate batch pass once all migrations are done, to avoid cross-repo coordination noise on every PR.

## Consequences

### Positive
- One canonical place to fix prefilter-class bugs (e.g., the next IGNORECASE trap).
- #51 (universal obituary/clickbait detectors) gets a uniform per-filter consumption hook — `OVERRIDE_KEYWORDS` and `POSITIVE_PATTERNS` already cover the common consumption patterns.
- New filters: ~50 LOC of declarations instead of ~150 of bespoke logic.
- Compile-once discipline: patterns compiled in `__init__`, no inline `re.search(pattern, ..., flags=...)` at apply time.

### Negative
- Backwards compat means the old shape sticks around in unmigrated filters. Two shapes coexist for ~1-2 weeks of background work.
- A subtle filter-specific behavior (e.g. sustech's two-stage `_is_excluded` then `_is_sustainability_related`) needs the `_filter_specific_final_check()` hook — not all filters fit cleanly.

### Risks
- Migration of any one filter could regress its prefilter behavior. **Mitigated by**: each filter ships with a `test_prefilter()` self-test exercising its known FN/FP cases; smoke-test runs as part of each migration PR.
- Old filters keep their custom `apply_filter()` until migrated — temporary inconsistency during the rollout.

## Revisit If

- A migration reveals a filter that fundamentally can't fit the declarative shape (e.g., needs more than three sequential check stages, or a non-pattern-based exclusion source). Re-evaluate whether to extend the base shape or accept that filter as a permanent exception.
- A universal noise detector (#51) wants a consumption mechanism not covered by `OVERRIDE_KEYWORDS` / `POSITIVE_PATTERNS`. Add a third class attribute rather than creating a parallel system.

## Implementation

1. Extend `filters/common/base_prefilter.py` with the new class attributes, an `__init__` that compiles patterns, and a default `apply_filter()` that calls the standard pipeline. (This ADR's first companion change.)
2. Migrate sustainability_technology/v3 first (already dict-based; lightest lift; proves the shape on a real filter).
3. Migrate the remaining six filters in priority order, each as its own PR with smoke test + deploy.
4. Once all migrations complete, fix class-name version drift in a single batch (3 filters: sustech V2→V3, nature_recovery V1→V2, investment-risk give v6 its own class).

## Related Decisions

- [ADR-004](004-universal-noise-prefilter.md) — Commerce is the only universal prefilter. ADR-018 is structural (how filters register patterns); ADR-004 governs scope (which detectors are filter-level vs universal).
- [ADR-016](016-drop-tier-assignments.md) — Filters output pass/block + score. ADR-018 standardizes the pass/block structure.

## References

- llm-distillery#52 — the harmonization issue (filed 2026-04-28).
- llm-distillery#45, #46 — per-filter prefilter patches that motivated the refactor.
- llm-distillery#51 — universal obituary detector (downstream consumer of the harmonized shape).
- `memory/feedback-regex-ignorecase-trap.md` — the case-insensitive override trap, an example of a class of bug that one canonical compile-site prevents.

## Amendment 2026-08-21 — new filters ship no per-lens prefilter (owner ruling)

**This ADR still governs the SHAPE of a prefilter where one exists. It no longer implies
that a filter should have one.**

Owner ruling 2026-08-21: `human_thriving` v8 ships **no `prefilter.py`**, and the Stage-1 e5
probe is retrained to carry the screening. Reason, measured on `uplifting v7`s prefilter:
662 lines, 74 patterns in three categories, and exactly two families of non-ASCII characters
<!-- CORRECTION 2026-08-22: the pattern count is **77** (crime_violence 37, corporate_finance 21,
     military_security 19), measured by loading the class rather than counting by eye. And
     "Latin script only" understates it: measured over 235,905 production rows it is a
     FOUR-LANGUAGE instrument (EN/NL/DE/FR = 74.9% of production; Spanish 0.89% removal vs
     English 8.89%). Evidence: docs/evidence/2026-08-22-uplifting-v7-corpus-provenance.md.
     The DECISION this ADR records is unaffected. -->
— **Latin (78) and em-dashes (30)**. No Cyrillic, Arabic, CJK, Devanagari, Greek or Hebrew.
Keyword screening is **Latin-script only**, which ADR-011 already said embedding screening
should replace.

Consistent with what was already measured: the per-lens prefilter has **never run in the
production scoring path** (NM#284), and `nature_recovery v4` + `solutions v6` emit **zero
lens blocks across 8,283 production articles**.

**Consequences**
- `memory/filter-doc-standard.md` core is now **6 files**; a per-lens prefilter is optional,
  with omission the default for new filters.
- `scripts/analysis/filter_completeness.py` no longer lists `prefilter.py` in `core`.
- ⛔ **`_load_prefilter` remains an `@abstractmethod` on `FilterBaseScorer`.** Dropping the
  *file* is safe; omitting the *method* raises `TypeError` at scorer startup and **no filter
  scores at all**. A prefilter-less package must define
  `def _load_prefilter(self): self.prefilter = None`.
- Existing filters keep their prefilters; this is not a retro-removal.

Detail: `docs/HUMAN_THRIVING_V8_PLAN.md` §F2, llm-distillery#98.
