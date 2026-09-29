# Filter Harmonizer Agent - Documentation

**Created:** 2025-11-17
**Location:** `C:\local_dev\llm-distillery\docs\agents\`

---

## What Was Created

### 1. Main Agent Specification
**File:** `filter-harmonizer.md` <!-- placeholder -->
**Size:** ~21 KB
**Purpose:** Complete agent specification for maintaining structural consistency across LLM filter prompts

**Contents:**
- YAML frontmatter (name, description, model, trigger keywords)
- Core harmonization principles (5 key principles)
- Filter inventory (4 active filters)
- Agent workflow (4 phases: analysis, consistency checks, reporting, auto-fixes)
- Decision criteria (Harmonized/Minor Issues/Major Issues)
- Common harmonization patterns
- Validation procedures
- Version history

---

### 2. Quick Reference Guide
**File:** `FILTER_HARMONIZATION_GUIDE.md`
**Size:** ~6 KB
**Purpose:** Fast reference for using the harmonizer agent

**Contents:**
- When to use the agent
- Quick invocation examples
- Key harmonization principles (condensed)
- Common issues and fixes
- Harmonization checklist
- Report interpretation guide
- Example workflow (new filter creation, quarterly audit)
- Q&A section

---

### 3. Sample Report
**File:** `examples/sample_harmonization_report.md`
**Size:** ~10 KB
**Purpose:** Demonstration of what harmonization reports look like

**Contents:**
- Executive summary
- Structural comparison table
- Detailed issue analysis (critical/minor/informational)
- Filter-by-filter breakdown
- Comparison matrices (output schemas, ARTICLE placement, inline filters)
- Summary statistics
- Harmonization checklist status
- Actionable recommendations

---

## Key Features

### Comprehensive Consistency Checks
The agent validates 7 critical aspects:

1. **Oracle Output Statement** - Explicit statement that oracle outputs dimensional scores only
2. **ARTICLE Placement** - ARTICLE appears after scope/rules, before dimensions
3. **Inline Filter Format** - Each dimension has inline CRITICAL FILTERS
4. **Classification Field Removal** - No tier/stage in oracle output (computed post-hoc)
5. **Post-processing Section** - Tier/stage calculation explained separately
6. **CHANGELOG** - Version history documented
7. **Philosophy Statement** - Guiding principle stated (optional)

### Multi-Phase Workflow

**Phase 1: Structural Analysis**
- Load all filter prompts
- Extract structural elements
- Generate comparison tables

**Phase 2: Consistency Checks**
- Run 7 automated checks per filter
- Flag issues with severity (critical/minor/informational)
- Generate detailed findings with line numbers

**Phase 3: Generate Report**
- Executive summary
- Issue-by-issue breakdown
- Comparison matrices
- Prioritized recommendations

**Phase 4: Automated Harmonization** (optional)
- Auto-fix minor issues (CHANGELOG format, add statements)
- Manual review required for classification fields
- Show diffs before applying

### Decision Criteria

**✅ HARMONIZED:** All filters consistent, no action needed

**⚠️ MINOR ISSUES:** Fixes recommended for next update cycle
- Missing Philosophy statements
- CHANGELOG format inconsistencies
- Classification fields documented as metadata

**❌ MAJOR ISSUES:** Must fix before release
- Oracle outputs tier/stage (violates oracle discipline)
- Missing inline filters
- Incorrect ARTICLE placement
- No CHANGELOG

---

## Usage Examples

### Example 1: Full Harmonization Check
```
Task: "Run filter harmonization check on all filters. Generate detailed report comparing:
- Oracle output statements
- ARTICLE placement
- Inline filter format
- Classification fields in output
- Post-processing sections
- CHANGELOGs

Save report to reports/filter_harmonization_report_2025-11-17.md"
```

**Expected output:** Comprehensive report like `examples/sample_harmonization_report.md`

---

### Example 2: Audit New Filter
```
Task: "Check the new filter at filters/my-new-filter/v1/prompt-compressed.md
for harmonization with existing filters. Focus on:
1. Does it follow the standard structure?
2. Oracle output statement present?
3. Inline filters used correctly?
4. No classification fields in oracle output?"
```

**Expected output:** Focused report on single filter with specific issues

---

### Example 3: Compare Against Reference
```
Task: "Audit filters/investment-risk/v2/prompt-compressed.md for harmonization.
Compare against filters/uplifting/v4/prompt-compressed.md as reference.
List specific issues with line numbers and recommended fixes."
```

**Expected output:** Detailed comparison showing where investment-risk differs from reference

---

## Filters in Scope

### Active Filters (Check These)
1. **filters/uplifting/v4/prompt-compressed.md**
   - Reference implementation (best practices)
   - 8 dimensions: agency, progress, collective_benefit, connection, innovation, justice, resilience, wonder
   - No tier classification in oracle output ✅

2. **filters/investment-risk/v2/prompt-compressed.md**
   - 8 dimensions: macro_risk_severity, credit_market_stress, market_sentiment_extremes, valuation_risk, policy_regulatory_risk, systemic_risk, evidence_quality, actionability
   - Signal tiers: RED, YELLOW, GREEN, BLUE, NOISE

3. **filters/sustainability_tech_deployment/v3/prompt-compressed.md**
   - 8 dimensions: deployment_maturity, technology_performance, cost_trajectory, scale_of_deployment, market_penetration, technology_readiness, supply_chain_maturity, proof_of_impact
   - Deployment stages: mass_deployment, commercial_proven, early_commercial, pilot, lab

4. **filters/sustainability_tech_innovation/v1/prompt-compressed.md**
   - Same 8 dimensions as tech_deployment
   - Broader scope: includes pilots and validated research

---

## Core Harmonization Principles

### 1. Oracle Output Discipline ⭐
**Rule:** Oracle outputs dimensional scores (0-10) only, NOT tier/stage classifications

**Rationale:** Separation of concerns. Oracle focuses on accurate dimensional scoring. Tier/stage logic is post-processing and can be changed without re-labeling thousands of articles.

**Example violations:**
```json
// ❌ BAD - Oracle outputs tier
{
  "tier": "impact",
  "overall_score": 8.7,
  "agency": 9,
  "progress": 8
}

// ✅ GOOD - Oracle outputs dimensions only
{
  "agency": 9,
  "progress": 8,
  "collective_benefit": 10
  // tier computed post-hoc from weighted sum
}
```

---

### 2. Standard Structure ⭐
**Order matters for fast models:**

1. Header (Purpose, Version, Focus, Philosophy, Oracle Output)
2. Scope (IN SCOPE / OUT OF SCOPE)
3. Rules/gatekeepers
4. **ARTICLE** ← After scope/rules, before dimensions
5. Dimensions (with inline filters)
6. Examples
7. Output format
8. Post-processing reference
9. CHANGELOG

**Why ARTICLE placement matters:** Oracle sees scope/rules before article, sets context for scoring.

---

### 3. Inline Filters ⭐
**Problem:** Fast models (Gemini Flash) skip top-level SCOPE sections

**Solution:** Inline CRITICAL FILTERS per dimension
```markdown
1. **Dimension Name**: Description

   **❌ CRITICAL FILTERS - If article is ANY of these, score 0-2:**
   - Filter criterion 1
   - Filter criterion 2

   **If NONE of above filters match, score normally:**
   - 0-2: None
   - 3-4: Limited
   - ...
```

**Evidence:** Uplifting v3→v4 and investment-risk v1→v2 transitions reduced false positives from 50-75% to <10% by adding inline filters.

---

### 4. CHANGELOG Required ⭐
**Every filter must document:**
- Version numbers (e.g., v2.1, v3.0-revalidation-fixes)
- Breaking changes
- Expected impact statements
- Dates

**Example:**
```markdown
## CHANGELOG

**v2.0 (2025-11-14):**
- **BREAKING CHANGE:** Restructured with inline filters
- Moved critical filters INLINE within each dimension
- Expected impact: Reduce false positives from 50% to <10%

**v1.0 (2024):**
- Initial compressed prompt
- Known issue: 50% false positive rate
```

---

## Common Harmonization Fixes

### Fix 1: Add Oracle Output Statement
**Before:**
```markdown
**Purpose**: Rate content for uplifting value
**Version**: v4
**Focus**: MEANING not TONE
```

**After:**
```markdown
**Purpose**: Rate content for uplifting value
**Version**: v4
**Focus**: MEANING not TONE
**Oracle Output**: Dimensional scores only (0-10 per dimension). Tier classification is applied post-processing, not by the oracle.
```

---

### Fix 2: Remove Classification from Oracle Output
**Before:**
```json
{
  "signal_tier": "RED|YELLOW|GREEN|BLUE|NOISE",
  "deployment_stage": "mass_deployment|commercial|pilot|lab",
  "macro_risk_severity": <0-10>,
  ...
}
```

**After:**
```json
{
  "macro_risk_severity": <0-10>,
  "credit_market_stress": <0-10>,
  ...
  // Note: signal_tier computed post-hoc from dimensional scores
}
```

Add to post-processing section:
```markdown
## POST-PROCESSING REFERENCE (NOT part of oracle output)

```python
if macro_risk >= 7 or credit_stress >= 7:
    signal_tier = "RED"
# ... etc
```
```

---

### Fix 3: Move ARTICLE Placement
**Before:**
```markdown
## PROMPT TEMPLATE

ARTICLE:
Title: {title}
Text: {text}

**SCOPE: ...**
```

**After:**
```markdown
## PROMPT TEMPLATE

**SCOPE: ...**

[Rules and gatekeepers]

ARTICLE:
Title: {title}
Text: {text}

[Dimensional scoring]
```

---

### Fix 4: Add Inline Filters
**Before:**
```markdown
**OUT OF SCOPE:**
- Generic IT infrastructure
- Gaming and entertainment

1. **Dimension Name**: Description
   - 0-2: None
   - 3-4: Limited
```

**After:**
```markdown
1. **Dimension Name**: Description

   **❌ CRITICAL FILTERS - If article is ANY of these, score 0-2:**
   - Generic IT infrastructure
   - Gaming and entertainment

   **If NONE of above filters match, score normally:**
   - 0-2: None
   - 3-4: Limited
```

---

## Integration with Other Agents

**Related agents:**
- **oracle-calibration-agent**: Test filter after harmonization changes
- **filter-package-validation-agent**: Validate filter package structure
- **prompt-calibration-agent**: Test prompt changes on sample data
- **dimensional-regression-qa-agent**: Validate labeled datasets

**Workflow:**
1. Create/modify filter
2. **Run filter-harmonizer** → Check structural consistency
3. Fix issues identified
4. **Run oracle-calibration** → Test on 200 sample articles
5. Review calibration report
6. Proceed to batch scoring if passed

---

## Version History

### v1.0 (2025-11-17)
- Initial filter harmonizer agent creation
- Support for 4 active filters
- 7 automated consistency checks
- Sample report demonstrating output
- Quick reference guide
- Complete documentation

---

## Files Created

```
docs/agents/
├── filter-harmonizer.md                      # Main agent specification (21 KB)
├── FILTER_HARMONIZATION_GUIDE.md             # Quick reference (6 KB)
├── README_FILTER_HARMONIZER.md               # This file (summary)
└── examples/
    └── sample_harmonization_report.md        # Example output (10 KB)
```

**Total:** 4 files, ~37 KB of documentation

---

## Next Steps

### For Users
1. Review the quick reference guide: `FILTER_HARMONIZATION_GUIDE.md`
2. Try running harmonization check on existing filters
3. Review sample report to understand output format
4. Integrate into filter development workflow

### For Maintainers
1. Add filter-harmonizer to agent index (if exists)
2. Update agent-operations.md with filter-harmonizer workflow
3. Consider adding to pre-release checklist
4. Schedule quarterly harmonization audits

### For CI/CD
1. Create automated harmonization check script
2. Add to pre-release validation pipeline
3. Set up alerts for critical issues
4. Archive harmonization reports for tracking

---

## Questions or Issues?

**Common questions:**

**Q: How do I run the filter harmonizer?**
A: See FILTER_HARMONIZATION_GUIDE.md for invocation examples. Use the Task tool with detailed prompt referencing filter-harmonizer.md.

**Q: What if my filter needs classification in oracle output?**
A: Document explicitly that it's metadata (like content_type), not computed tier. Or move to post-processing if it's derived from dimensional scores.

**Q: Can the agent auto-fix issues?**
A: Yes for minor issues (adding statements, formatting CHANGELOGs). Manual review required for classification field removal.

**Q: How often should I run harmonization checks?**
A: After creating new filters, before releases, and quarterly for active filters.

---

**Maintainer:** LLM Distillery Project
**Agent Version:** v1.0
**Documentation Version:** v1.0
**Last Updated:** 2025-11-17
