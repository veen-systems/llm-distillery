# ADR-012: Lens-Aligned Filter Naming

**Date:** 2026-03-18
**Status:** Accepted (amended by ADR-013: English Lens Names; **amended 2026-08-06 — see "Amendment: the Hub is a public surface" below, which cancels two of the five scheduled renames**)
**Decision:** Rename filters to match ovr.news editorial lens names at each filter's next version bump. Use underscores only in filter names.

## Context

ovr.news presents news through editorial lenses: Thriving, Belonging, Recovery, Solutions, Discovery, with Wisdom and Education planned. The current filter names evolved organically and don't match these lenses:

- `uplifting` → Thriving lens
- `belonging` → Belonging lens (already matches)
- `nature_recovery` → Recovery lens
- `sustainability_technology` → Solutions lens
- `cultural-discovery` → Discovery lens (also uses hyphens, inconsistent)
- `signs_of_wisdom` → Wisdom lens (not yet shipped)
- `future-of-education` → Education lens (not yet shipped)

The mismatch creates confusion in three places:
1. NexusMind attribute field names (`uplifting_analysis` vs frontend "Thriving" tab)
2. Documentation (constantly mapping between internal and external names)
3. New contributor onboarding (which filter powers which tab?)

## Decision

Rename each filter to its lens name at the next version bump. This is a natural breakpoint — the old version stays for reference, and the new version starts clean.

### Rename Schedule

| ovr.news Lens | Old filter name | New filter name | Trigger |
|---------------|----------------|-----------------|---------|
| Thriving | uplifting | `thriving` | **v1 (now)** |
| Belonging | belonging | `belonging` | Already matches |
| Recovery | nature_recovery | `recovery` | At v2 |
| Solutions | sustainability_technology | `solutions` | At v4 |
| Discovery | cultural-discovery | `discovery` | At v5 |
| Wisdom | signs_of_wisdom | `wisdom` | At v1 (not yet shipped) |
| Education | future-of-education | `education` | At v1 (not yet shipped) |

`investment-risk` is not an ovr.news lens and keeps its current name.

### Naming Conventions

- **Underscores only** in filter directory names (no hyphens). Python can't import hyphens.
- **analysis_field_name()** uses the filter name: `thriving_analysis`, `recovery_analysis`, etc.
- Old filter directories remain in the repo for historical reference and backward compatibility.
- NexusMind attribute field names change at each rename — requires frontend coordination.

## Rationale

- **Gradual migration**: Renames happen one at a time at natural version bumps, not a big-bang refactor.
- **No data loss**: Old versions stay in the repo. Old scored data retains its original field names.
- **Frontend alignment**: Each rename is coordinated with ovr.news frontend changes (parallel running period).
- **Simplicity**: One name per concept, used consistently from oracle prompt to production tab.

## Consequences

**Positive:**
- Frontend developers can find the right filter by lens name
- Documentation uses one consistent name per concept
- New filters (wisdom, education) start with the right name from day one

**Negative:**
- Transition period: two field names coexist in NexusMind during parallel running
- Historical oracle data uses old field names (e.g., `uplifting_analysis`)
- grep/search across the codebase must check both old and new names during transition

## Amendment: the Hub is a public surface (2026-08-06)

**Owner decision. `cultural_discovery` and `nature_recovery` keep their names.
The renames to `discovery` and `recovery` are cancelled, not deferred.**

### The audience this ADR did not account for

Every rationale above is about an **internal** reader: NexusMind attribute field
names, our documentation, our contributor onboarding. All three see the filter
name *in context* — beside a lens, in a table, in a repo that explains itself.

Model repositories on HuggingFace have none of that context. A repo page is a
standalone artefact with a global namespace, read by people who have never heard
of ovr.news and have no lens list to map it against. There,
`cultural-discovery-filter-v6` says what the model does and `discovery-filter-v6`
does not. Same for `nature-recovery-filter-v4` versus `recovery-filter-v4` —
recovery of *what*?

This ADR was written on 2026-03-18, before the Hub was a routine part of the
pipeline. The omission is not that the trade-off was judged wrongly; it is that
this surface was never one of the three.

### The rule, stated so it can be applied to the next filter

> Rename to the lens name only when the lens name is **at least as descriptive
> as the internal name to a reader who has no other context**. Where the internal
> name carries a qualifier the lens name drops — the domain, the subject, the
> *of what* — keep the internal name and accept that the filter name and the lens
> name differ.

Losing an adjective is not a cosmetic difference when the noun that remains is
generic. `solutions` survives alone; `discovery` and `recovery` do not.

### Applying it to the schedule above

| Lens | Filter | Hub repo | Verdict |
|---|---|---|---|
| Discovery | `cultural_discovery` | `cultural-discovery-filter-v{N}` (public) | **Keep `cultural_discovery`.** Rename cancelled. |
| Recovery | `nature_recovery` | `nature-recovery-filter-v{N}` (public) | **Keep `nature_recovery`.** Rename cancelled. |
| Solutions | `solutions` | — | Already executed at v4. `solutions` stands alone fine. Filter since removed (2026-08-03). |
| Belonging | `belonging` | `belonging-filter-v1` (public) | Already matches. No change. |
| Thriving | `uplifting` | **NO_HUB** — file-copy deploy only | **Not resolved by this amendment.** The Hub argument does not apply: there is no public repo. Independently complicated — `thriving` already exists as a *separate* filter at v1, parked under ADR-015, so "rename uplifting to thriving" would collide with a real directory. Left open for the owner. |
| Wisdom / Education | not shipped | — | Apply the rule at creation: pick the more descriptive of the two names from day one, rather than renaming later. |

`investment_risk` was already out of scope (not an ovr.news lens) and keeps its
name; its Hub repo `investment-risk-filter-v6` is unaffected.

### Why this is cheaper than it looks

Nothing has to be undone. **Neither rename had happened** — the schedule above
set them for "at v2" (nature_recovery, now at v4) and "at v5"
(cultural-discovery, now at v6), and both bumps passed without it. Cancelling
them changes no directory, no field name, no Hub repo, no NexusMind attribute.

Worth recording plainly: **of the five scheduled renames, one was carried out**
(sustainability_technology → solutions), and that filter has since been deleted.
An ADR that has been followed once in five opportunities across five months is
not a policy being applied; it is an aspiration generating recurring cleanup
tickets. This amendment resolves two of the four outstanding cases by deciding
them, rather than re-scheduling them to the next bump for a fourth time.

### Interaction with #48 (Hub repo naming convention)

#48 proposes standardising on `{name-hyphenated}-filter-v{N}` and adding a check
to `verify_filter_package.py` that **fails when `repo_id` does not match the
filter's own name**. That check and a rename-internally-but-keep-the-Hub-name
compromise are mutually exclusive by construction — it would have needed a
permanent exception list, which is precisely what #48 exists to remove.

Keeping both names aligned makes #48's rule enforceable with no exceptions for
these two filters. That is an argument *for* this amendment, discovered while
writing it — not a reason it was made.

## Appendix: Cross-Lens Boundary Map

Each lens must be distinct. This map documents where dimensions overlap and how boundaries are enforced.

### Lens Dimensions Summary

| Lens | Core Dimensions | What It Measures |
|------|----------------|------------------|
| **Thriving** | human_wellbeing_impact (0.40), justice_rights_impact (0.25), evidence_level (0.10), benefit_distribution (0.10), change_durability (0.15) | Documented outcomes for human wellbeing, rights, verified progress |
| **Belonging** | intergenerational_bonds (0.25), community_fabric (0.25), rootedness (0.15), purpose_beyond_self (0.15), reciprocal_care (0.10), slow_presence (0.10) | Organic social bonds, rootedness, intergenerational ties |
| **Recovery** | recovery_evidence (0.25), measurable_outcomes (0.20), ecological_significance (0.20), restoration_scale (0.15), human_agency (0.10), protection_durability (0.10) | Documented ecosystem recovery when human pressure is reduced |
| **Solutions** | life_cycle_environmental_impact (0.30), economic_competitiveness (0.20), technology_readiness_level (0.15), technical_performance (0.15), social_equity_impact (0.10), governance_systemic_impact (0.10) | Sustainable technology viability via LCSA framework |
| **Discovery** | discovery_novelty (0.25), cross_cultural_connection (0.25), heritage_significance (0.20), human_resonance (0.15), evidence_quality (0.15) | Cultural discovery, cross-cultural bridging, heritage |

### Known Boundary Tensions

| Pair | Overlap Risk | Boundary Rule |
|------|-------------|---------------|
| **Thriving ↔ Belonging** | Community events with wellbeing outcomes | Thriving requires *measurable* wellbeing/rights outcomes. Community bonds alone = Belonging. (social_cohesion_impact removed from Thriving in v1) |
| **Thriving ↔ Recovery** | Environmental projects that improve human lives | Recovery requires *ecological* outcomes. Human health benefits from nature = Thriving |
| **Thriving ↔ Solutions** | Technology that improves human wellbeing | Solutions measures *technology viability* (TRL, LCC). Wellbeing impact of the outcome = Thriving |
| **Recovery ↔ Solutions** | Clean tech with ecological benefits | Recovery = nature bouncing back. Solutions = technology assessment. Solar panel LCSA = Solutions; rewilded riverbank = Recovery |
| **Belonging ↔ Discovery** | Cultural heritage preservation | Belonging = rootedness, intergenerational continuity in *one's own* culture. Discovery = *cross-cultural* bridging and novelty |
| **Discovery ↔ Belonging** | Local traditions and rituals | Local tradition maintaining community bonds = Belonging. Novel cultural insight or cross-cultural connection = Discovery |
| **Solutions ↔ Recovery** | Restoration technology (rewilding drones, coral nurseries) | If the article focuses on the *technology* and its readiness = Solutions. If it focuses on *ecological outcomes* = Recovery |

### Audit Tool

Run `scripts/analysis/cross_lens_audit.py` to compute pairwise correlations and MEDIUM+ overlap on current data. Target: no lens pair with Pearson r > 0.50 or MEDIUM+ overlap > 50%.

## References

- ADR-009: Add Filters First, Reduce Later (lens overlap strategy)
- ADR-010: Oracle Consistency Over Data Volume (prompt precision)
- `ground_truth/__init__.py`: `analysis_field_name()` convention
- `scripts/analysis/cross_lens_audit.py`: Cross-lens overlap analysis tool
