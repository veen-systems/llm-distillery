# ADR-013: English Lens Names

**Date:** 2026-03-28
**Status:** Accepted
**Amended:** 2026-09-17 — scope widened from names to the framework's own language; see *Amendment* below.

## Amendment (2026-09-17): the rule is the framework's own language, not just names

All framework-internal text is English. That is **the original decision's surfaces —
lens names, filter names, ovr.news tab labels, NexusMind field names — plus** docs,
ADRs, code comments, memory files, plan documents and commit messages. Nothing the
original decision covered is narrowed here; ⛔ **tab labels in particular stay in
scope**, and they are the surface the 2026-03-28 Context exists to protect
(`Verwondering`, `Herstel`, `Leren` at `:44` below).

⛔ **This does NOT reach match patterns, boilerplate strippers or test fixtures.** A
non-English string that the code *matches against article text* is **data, not
language**:

| Surface | Example (`filters/*/v*/prefilter.py` unless noted) | Container |
|---------|---------|-----------|
| Prefilter match patterns | `nature_recovery/v4:84` `herstel\|wordt hersteld` | `POSITIVE_PATTERNS` |
| | `uplifting/v7:289` `conflictoplossing\|verzoening` | `EXCEPTION_PATTERNS_PER_CATEGORY` |
| | `cultural_discovery/v5:105` `niet jouw cultuur om te` | `EXCLUSION_PATTERNS` |
| Boilerplate strippers | `ground_truth/text_cleaning.py:293, :330` — 36 `# nl/de/fr/es/it/pt`-tagged lines | module-level regex lists |
| Test and benchmark fixtures | `commerce_prefilter/training/benchmark_models.py:61` (also de `:55,:57`, fr `:63`, zh `:65`); `uplifting/v7/prefilter.py:567` | fixture string literals |

⚠️ **The table is a SNAPSHOT, not an inventory** — a 2026-09-17 sweep of
`filters/ ground_truth/ training/ scripts/ tests/` (`*.py`/`*.yaml`/`*.sh` only) hit
**9** files / 12 lines against the 5 named. The row's *class* governs; do not treat the examples
as the population.

⚠️ **The fixture row is scoped by ROLE, not by path** — `uplifting/v7/prefilter.py:567`
sits inside a production module, in `def test_prefilter()`. It covers **string literals
standing in for article text**. Comments, docstrings and `'description'` fields in
fixture files stay English.

⛔ **The test is "does deleting it change what the filter matches", NOT "does it cost
recall" — the sign runs both ways.** `cultural_discovery/v5:105` is an **exclusion**:
deleting it makes the filter block *less*, costing **specificity**, which ADR-023 and
`CLAUDE.md` name as the priority over recall. A rule phrased as a recall test licenses
exactly that deletion.

⚠️ **And name the path before quoting a cost.** The per-lens rule prefilter has **never
executed in the production scoring path** (NM#284, dead since 2026-02-10; `CLAUDE.md`
Hard Constraints). Deleting these patterns changes **zero production scoring
decisions** today — the cost lands on the llm-distillery oracle/labelling path, and is
**unmeasured**. ⛔ **Do not cite `cultural_discovery`'s enforcement cost here**: an
earlier draft of this amendment cited *"19.9% non-English vs 13.0% English"*, which is
a pooled framing this repo **retracted on 2026-08-02** (`memory/prefilter-length-floor-hypotheses.md`
— German 4.9% and French 5.3% sit *below* English's 13.0%, so the pool "describes no
real population"), attached to the wrong study (it is LD#86, 135/871 surfacing articles
over 20 cycles — not NM#285's 8,283) and to the wrong question (enforcement, which has
not happened).

### ⛔ Compliance is NOT established, and the first sweep's negative carried no information

**Retracted 2026-09-17, same day it was written.** A first version of this amendment
claimed zero violations. The sweep used a 36-token list of Dutch **function words**
(`niet`, `wordt`, `omdat`, …) and returned zero — but the class this ADR polices is
Dutch **names**, which contain no function words. Measured: that list scores **0** on
both sites a name-aware sweep found immediately.

**Two open violations, both inside the retracted sweep's own declared scope:**

| Site | What |
|------|------|
| `docs/adr/009-add-filters-first-reduce-later.md:25,34,35,37,60` | `Welzijn` / `Erfgoed` / `Vooruitgang` as framework prose in an ADR |
| `scripts/analysis/cross_filter_landscape.py` | 39 occurrences — dict keys, identifiers (`s1_welzijn`, `bel_not_welzijn`), printed column headers |

⭐ **The transferable lesson, and it is this repo's own rule turned on its author: the
positive control must be of the CLASS UNDER TEST.** The instrument *did* have a control
— it found the Dutch fixture sentences — so it looked sound. A Dutch sentence and a
Dutch lens name are different classes, and the control only proved the first.

⚠️ **This ADR's own Consequences (`:86`) already carried an open action** — *"check
TODO.md, ROADMAP.md, ADR-012 appendix"*. ADR-009 is dated **2026-03-04, earlier than
this ADR**, and is exactly the leftover that action pointed at. The retracted sweep
declared zero without reconciling it.

**Status: the rule is ADVISORY — no mechanism enforces it.** `scripts/verification/`
holds no language check; `.githooks/commit-msg` fires only on deploy-words with staged
`filters/*/v*/` paths, so the commit-message clause has **no reader at all**.
`run_verify_annotations.py` does not scan `docs/`, so a `<!-- verify: -->` block added
here would never execute. Advisory is defensible for prose in a repo whose *data* is
legitimately six languages; it is not defensible for a compliance *claim*, which is why
the claim is withdrawn rather than repaired.

## Decision (2026-03-28 — scope widened by the Amendment above)

All ovr.news lens names and filter names use English. No Dutch naming.

## Context

ADR-012 established lens-aligned filter naming but left the frontend tab language implicit. Some tabs were planned with Dutch names (e.g., "Herstel" for Recovery, "Leren" for Education, "Verwondering" for a potential wonder lens). This created ambiguity about whether filter names should follow Dutch tab names or English internal names.

Maintaining two languages adds friction:
1. Filter developers must know the Dutch translation to find the right tab
2. Documentation mixes languages ("nature_recovery" filter → "Herstel" tab)
3. New lens brainstorming gets tangled in translation questions
4. International contributors or collaborators face an unnecessary barrier

## Decision, as originally recorded (2026-03-28 — scope widened by the Amendment above)

All lens names are English. Filter directory names, ovr.news tab labels, NexusMind field names, and documentation all use the same English name.

### Updated Lens Names (amends ADR-012 table)

| Lens / Tab | Filter name | Status |
|------------|-------------|--------|
| Thriving | `thriving` | In development |
| Belonging | `belonging` | Deployed |
| Recovery | `recovery` | Deployed (as nature_recovery, renames at v2) |
| Solutions | `solutions` | Deployed (as sustainability_technology, renames at v4) |
| Discovery | `discovery` | Deployed (as cultural-discovery, renames at v5) |
| Wisdom | `wisdom` | Pre-development (as signs_of_wisdom, renames at v1) |
| Education | `education` | Concept (as future-of-education, renames at v1) |


`investment-risk` and `ai-engineering-practice` are not ovr.news lenses and keep their current names (per ADR-012).

## Rationale

- One language, one name, everywhere — no mental translation layer
- English is already the codebase language, model language, and oracle prompt language
- Simplifies onboarding and cross-repo references (NexusMind, agentic-engineering)
- Lens names like "Thriving", "Belonging", "Recovery" work well as English tab labels

## Consequences

**Positive:**
- Zero ambiguity between filter name, tab name, and documentation
- Easier to brainstorm new lenses without translation detours

**Negative:**
- ovr.news audience is partly Dutch-speaking — English tab names may feel less native
- Existing references to Dutch tab names in docs need updating (CLAUDE.md done; check TODO.md, ROADMAP.md, ADR-012 appendix)

## References

- ADR-012: Lens-Aligned Filter Naming (amended by this ADR)
