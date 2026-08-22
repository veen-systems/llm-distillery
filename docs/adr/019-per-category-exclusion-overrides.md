---
status: Accepted
date: 2026-05-05
deciders: [team]
superseded_by:
---

# ADR-019: Per-category exclusion overrides on `_is_excluded`

## Context

ADR-018 standardized prefilter shape with declarative `EXCLUSION_PATTERNS`,
`OVERRIDE_KEYWORDS`, `POSITIVE_PATTERNS`, `POSITIVE_THRESHOLD` class
attributes plus a default `apply_filter()` that drives a standard pipeline.

`BasePreFilter._is_excluded()` walks `EXCLUSION_PATTERNS` in declared order;
on the first matching pattern it consults `_has_override()`. Override is
**global and binary**: any `OVERRIDE_KEYWORDS` substring or any
`POSITIVE_THRESHOLD`-meeting count of `POSITIVE_PATTERNS` bypasses the
*current* exclusion category (and the loop continues to the next category).

This works for filters where one override rule applies uniformly to every
exclusion category. But four of seven production filters need
**per-category override behavior** and have therefore retained custom
`apply_filter()` implementations:

| Filter | Per-category override behavior |
|--------|-------------------------------|
| **belonging/v1** | Each non-obit category has its own positive-count threshold (`POSITIVE_COUNT_THRESHOLDS`: wellness=3, self_help=2, …). The obit category uses a unique compound rule: `positive_count >= 2` OR `(has_exception AND positive_count >= 1)`. |
| **foresight/v1** | Override is distinct-categories-fired count (`POSITIVE_CATEGORIES_THRESHOLD = 3`), not total match count. A single repeated keyword in one positive group counts as 1, not N. |
| **sustainability_technology/v3** | Custom keyword-substring override gated to specific categories. |
| **cultural-discovery/v4** | Pattern-pair override per category. |

The cost of staying on global override:

1. **#51's universal obituary detector wants per-filter consumption.**
   Cultural-discovery should consume "high P(obit)" as a soft signal that
   *only* tags obit-specific exclusions, not its general-noise excluded
   categories. Today there's no way to express that without a custom hook.
2. **Bug surface multiplies.** The 2026-04-29 belonging RIP-token repair
   touched the legacy `apply_filter()` only — base infrastructure couldn't
   help, because per-category logic lives outside it.
3. **Migrations from #52 stall on the override mismatch.** Filters that
   could otherwise drop their custom `apply_filter()` keep it solely
   because they need per-category override.

Why now: #51 implementation begins as soon as the obit detector ships, and
its per-filter consumption hook is the trigger that makes per-category
override a blocker. We want this in place before the first lens consumes
the obit signal.

## Options Considered

### Option A: Status quo, accept custom `apply_filter()` for per-category needs

| Pros | Cons |
|------|------|
| No base change | 4 of 7 filters keep ~80 LOC of bespoke override logic |
| | #51 per-filter consumption requires per-filter integration code |
| | Future fixes (next IGNORECASE-trap-class bug) hit 4 separate codepaths |

### Option B: Per-category config dict on the base

```python
class _CategoryOverride(TypedDict, total=False):
    keywords: list[str]      # bypass keywords (substring match)
    threshold: int           # positive-pattern count needed
    positive_groups: list[str]  # which positive pattern groups count

# Subclass declares:
CATEGORY_OVERRIDES: Dict[str, _CategoryOverride] = {
    "obituary_funeral": {"threshold": 2, "positive_groups": ["belonging"]},
    "wellness_industry": {"threshold": 3, "positive_groups": ["belonging"]},
    # categories without entries fall back to global OVERRIDE_KEYWORDS / POSITIVE_THRESHOLD
}
```

`_is_excluded()` consults `CATEGORY_OVERRIDES.get(category)` first, falls
back to the global rule. Empty dict = current behavior.

| Pros | Cons |
|------|------|
| Fully declarative — covers belonging's and foresight's threshold cases | Doesn't cover compound rules (belonging's "thr OR (exception AND >=1)") without escape valve |
| Backwards compatible (empty dict = current behavior) | Adds a class attribute + TypedDict to a base that's already four attributes deep |
| `_has_override()` can stay as the global fallback path | Risk of subclasses declaring overlapping rules in both global and per-category — needs precedence rule |

### Option C: Override hook method `_category_override_applies(category, …)`

```python
def _category_override_applies(
    self,
    category: str,
    title: str,
    text: str,
) -> bool:
    """Return True to bypass exclusion in `category`. Default: global rule."""
    return self._has_override(f"{title} {text[:1000]}".lower())
```

`_is_excluded()` calls this in place of `_has_override()` directly.
Subclasses override and branch on `category`.

| Pros | Cons |
|------|------|
| Maximum flexibility — covers belonging's compound rule cleanly | Less declarative — subclass logic isn't visible in class attrs |
| One-line base change | Signature commits to passing `(category, title, text)` — future signal additions (e.g. `url`, raw title for case-sensitive checks) become breaking changes |
| Filters with no per-category needs are unaffected | |

### Option D: Combine — declarative dict (B) with hook (C) as escape valve

`CATEGORY_OVERRIDES` covers thresholds + keyword variants declaratively.
`_category_override_applies()` exists as an overridable hook for compound
rules. Default hook implementation reads from `CATEGORY_OVERRIDES`, then
falls back to global `_has_override()`.

| Pros | Cons |
|------|------|
| Declarative form for the common case (B's strength) | Two override mechanisms — subclasses must understand both |
| Hook escape valve for compound rules (C's strength) | More base-class surface area to maintain |
| Belonging migrates: thresholds → dict, obit compound rule → hook | |
| Foresight migrates: distinct-categories rule → hook (one method, ~6 LOC) | |

## Decision

**We chose Option D.** The declarative `CATEGORY_OVERRIDES` dict handles
the bulk of needs visibly; the hook `_category_override_applies()` covers
compound and rare custom rules without forcing filters back into custom
`apply_filter()`. Migration work per filter drops from ~50–80 LOC of
bespoke `apply_filter()` to ~10–20 LOC of declarations plus an optional
5-line hook override. Precedence: dict first, hook second, global
`OVERRIDE_KEYWORDS` / `POSITIVE_THRESHOLD` last.

## Consequences

### Positive
- Belonging, foresight, sustech v3, cultural-discovery v4 can drop their
  custom `apply_filter()` after migrating override semantics into the
  declarative form + hook.
- #51's per-filter consumption becomes a single-line integration: the
  obit detector populates a synthetic exclusion category; a filter
  declares `CATEGORY_OVERRIDES["_is_obituary"]` to control how it consumes
  the signal.
- One canonical override compile-site — closes the same class of bug
  ADR-018 closed for pattern compilation.

### Negative
- Two override mechanisms (dict + hook). Subclass authors need to
  understand the precedence: `CATEGORY_OVERRIDES` first, hook second,
  global `OVERRIDE_KEYWORDS` / `POSITIVE_THRESHOLD` last.
- The dict's `positive_groups` field requires filters to also declare
  named positive pattern groups (a refactor of `POSITIVE_PATTERNS` from
  flat list to dict). Not all filters need this — only those with per-
  category positive thresholds. We make `positive_groups` optional and
  default to all positives.

### Risks
- Migrating belonging's compound obit rule into the hook risks a behavior
  change. **Mitigated by**: belonging has 20 self-tests covering exactly
  these obit cases (RIP variants, heritage-funeral exception, cultural-
  figure-obit exception bypass). Migration must keep all 20 green.
- Filters not yet migrated stay on legacy `apply_filter()` — three
  override systems coexist (legacy, declarative dict, hook) until #52
  closes.

## Revisit If

- A filter needs override semantics that can't be expressed via
  `CATEGORY_OVERRIDES` *or* the hook (e.g. needs cross-category state, or
  needs to inspect non-text article metadata in a way the hook signature
  doesn't expose). Re-evaluate widening the hook signature vs accepting
  custom `apply_filter()` as a permanent escape hatch.
- The hook receives only `(category, combined_lower)` — pre-lowercased
  combined text. Compound rules that need raw fields (case-sensitive
  title checks like belonging's `\bRIP\b`, url, source metadata) cannot
  use the hook today and must stay in custom `apply_filter()`. If a
  third filter shows up wanting raw access, widen the signature to
  `(category, article, combined_lower)` and migrate.
- #51 obituary detector ships and the per-filter consumption pattern that
  emerges differs materially from what `CATEGORY_OVERRIDES` expresses. In
  that case fold the lessons back into a v2 of this ADR.

## Implementation

1. Extend `BasePreFilter` with `CATEGORY_OVERRIDES: Dict[str, dict]` class
   attribute (default `{}`) and `_category_override_applies()` method
   (default reads `CATEGORY_OVERRIDES` then falls back to `_has_override`).
2. Update `_is_excluded()` to call `_category_override_applies(category, …)`
   instead of `_has_override(combined)` directly. Behavior unchanged when
   `CATEGORY_OVERRIDES` is empty (existing default).
3. Migrate **belonging/v1** first (most-tested, biggest LOC reduction).
   Verify all 20 self-tests pass.
4. Migrate **foresight/v1** (parked but useful as a compound-rule example).
5. Migrate **sustech/v3**, **cultural-discovery/v4** as opportunity allows.
6. Once #51 obit detector lands, document the `_is_obituary` consumption
   recipe in this ADR (or a separate consumer-facing doc).

## Related Decisions

- [ADR-018](018-prefilter-shape-harmonization.md) — declarative prefilter
  shape. ADR-019 extends 018's `_is_excluded` mechanism without changing
  the standard pipeline.
- [ADR-004](004-universal-noise-prefilter.md) — universal noise scope.
  Independent of how filters consume universal signals; ADR-019 governs
  how a filter expresses *consumption* of any signal (universal or
  filter-specific) per-category.

## References

- llm-distillery#51 — universal obituary detector. The trigger for
  per-filter consumption.
- llm-distillery#52 — prefilter harmonization tracking issue.
- `filters/belonging/v1/prefilter.py` — current state of per-category
  override logic; the migration target.
- `filters/foresight/v1/prefilter.py` — distinct-positive-categories
  override variant.

## Amendment 2026-08-21 — new filters ship no per-lens prefilter (owner ruling)

**This ADR still governs the SHAPE of a prefilter where one exists. It no longer implies
that a filter should have one.**

Owner ruling 2026-08-21: `human_thriving` v8 ships **no `prefilter.py`**, and the Stage-1 e5
probe is retrained to carry the screening. Reason, measured on `uplifting v7`s prefilter:
662 lines, 74 patterns in three categories, and exactly two families of non-ASCII characters
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
