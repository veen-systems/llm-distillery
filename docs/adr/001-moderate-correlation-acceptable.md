# ADR 001: Moderate Dimension Correlations Are Acceptable

**Date**: 2025-11-23  
**Status**: Accepted  
**Context**: sustainability_technology v1 calibration analysis

## Decision

Moderate correlations (0.70-0.85) between filter dimensions are **acceptable** when they reflect real domain relationships rather than oracle failure, provided:

1. PC1 variance < 70% (multi-dimensional problem)
2. Zero high correlations (r > 0.85)
3. Individual articles show variation from the trend
4. Dimensions provide distinct filtering value

## Context

During calibration of sustainability_technology v1 filter, we observed:
- PC1 variance: 66.5%
- Moderate correlations (0.70-0.85): 3 pairs
  - TRL ↔ Economics: r=0.763
  - Social ↔ Governance: r=0.768  
  - Environment ↔ Governance: r=0.708
- High correlations (>0.85): 0
- Redundancy score: 60%

Initial assessment flagged this as problematic, but deeper analysis revealed these correlations reflect **realistic causal relationships**:
- More mature technology (high TRL) *tends* to be more economically competitive
- Better governance *tends* to improve social equity
- Governance influences environmental outcomes

## Rationale

### Why Moderate Correlations Are Acceptable

1. **Real-world patterns**: Technologies don't exist in isolation - maturity, economics, and governance are genuinely related

2. **Individual variation**: Despite r=0.76 correlation, individual articles show:
   - High TRL + Low Economics (nuclear power, early solar)
   - Low TRL + High Economics (early-stage prototypes)
   - All combinations exist in practice

3. **Distinct filtering value**: By scoring separately, we capture:
   - Tech-maturity-focused articles (high TRL weight)
   - Economics-focused articles (high Econ weight)  
   - Both aspects (weighted combination)

4. **Significantly better than old filters**:
   - Old: PC1 = 89.1%, essentially one-dimensional
   - New: PC1 = 66.5%, clearly multi-dimensional

### What Makes Correlation Problematic

Correlations are problematic when:
- r > 0.85 (very high correlation)
- PC1 > 85% (single dominant factor)
- Dimensions *always* move together regardless of content
- Oracle rating on single "overall quality" factor

## Consequences

### Positive
- Accept natural domain relationships
- Avoid over-engineering dimension independence
- Focus on what matters: PC1 < 70%, zero high correlations
- Clearer guidelines for future filters

### Negative
- None - this correctly distinguishes real relationships from oracle failure

## Decision Rule

**Proceed to training if**:
- PC1 variance < 70% **AND**
- Zero high correlations (r > 0.85) **AND**  
- Moderate correlations have plausible domain explanations

**Do not proceed if**:
- PC1 variance > 85% **OR**
- Multiple high correlations (r > 0.85) **OR**
- Dimensions always move together in lockstep

## References

- Analysis: ~~`sandbox/sustainability_technology_v1_calibration/analysis_summary.json`~~
- Visualizations: `sandbox/sustainability_technology_v1_calibration/*.png`
- Updated guide: `docs/agents/filter-development-guide.md` (lines 449-485)
