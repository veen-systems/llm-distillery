# Filter Development Checklist

**Use this checklist when creating or modifying LLM filter prompts**

---

## Pre-Development

- [ ] Reviewed existing filters for patterns
- [ ] Identified filter purpose and scope
- [ ] Defined dimensional scores (typically 8 dimensions)
- [ ] Decided on tier/stage classification scheme (if needed)
- [ ] Reviewed harmonization principles

---

## Header Section

- [ ] **Purpose** statement (one sentence describing filter's goal)
- [ ] **Version** number (e.g., v1.0, v2.1-academic-filter)
- [ ] **Target** model specified (e.g., Gemini Flash 1.5 / Claude Haiku)
- [ ] **Focus** statement (core principle or main focus area)
- [ ] **Philosophy** statement (optional but recommended)
- [ ] **Oracle Output** statement: "Dimensional scores only (0-10 per dimension). Tier classification is applied post-processing, not by the oracle."

**Example:**
```markdown
# Filter Name

**Purpose**: Rate content for [specific goal]

**Version**: v1.0
**Target**: Gemini Flash 1.5 / Claude Haiku / Fast models

**Focus**: [Core principle]

**Philosophy**: "[Guiding principle]"

**Oracle Output**: Dimensional scores only (0-10 per dimension). Tier classification is applied post-processing, not by the oracle.
```

---

## Scope Definition

- [ ] **IN SCOPE** section clearly defines what to include
- [ ] **OUT OF SCOPE** section clearly defines what to exclude
- [ ] Examples provided for both in-scope and out-of-scope
- [ ] Edge cases addressed ("When in doubt" rule)

---

## Structure

- [ ] ARTICLE placement is AFTER scope/rules, BEFORE dimensions
- [ ] Pre-classification or gatekeeper rules (if applicable)
- [ ] Dimensional scoring section with all dimensions
- [ ] Examples section (validation examples)
- [ ] Output format (JSON schema)
- [ ] Post-processing reference section
- [ ] CHANGELOG section

**Correct order:**
```
1. Header
2. Scope (IN SCOPE / OUT OF SCOPE)
3. Rules/gatekeepers
4. ARTICLE ← HERE
5. Dimensions
6. Examples
7. Output format
8. Post-processing
9. CHANGELOG
```

---

## Dimensional Scoring

For each dimension:

- [ ] Dimension name and description
- [ ] **❌ CRITICAL FILTERS** section with inline filters
- [ ] "If NONE of above filters match, score normally:" guidance
- [ ] Scoring rubric (0-2, 3-4, 5-6, 7-8, 9-10 with descriptions)
- [ ] Evidence indicators (what to look for)

**Template:**
```markdown
1. **Dimension Name**: Description

   **❌ CRITICAL FILTERS - If article is ANY of these, score 0-2:**
   - Filter criterion 1
   - Filter criterion 2
   - Filter criterion 3

   **If NONE of above filters match, score normally:**
   - 0-2: Description
   - 3-4: Description
   - 5-6: Description
   - 7-8: Description
   - 9-10: Description

   **Evidence**: What to look for in article
```

- [ ] All dimensions (typically 8) have inline filters
- [ ] Filters are specific and testable
- [ ] Scoring rubric is clear and actionable

---

## Output Format

- [ ] JSON schema provided
- [ ] Dimensional scores included (0-10 per dimension)
- [ ] Reasoning field included
- [ ] Metadata fields defined (content_type, primary_technology, etc.)
- [ ] **NO tier/stage classification fields** (or documented as metadata)
- [ ] Reminder: "DO NOT include any text outside the JSON object"

**Check for forbidden fields:**
- [ ] ❌ No `tier` field (computed post-hoc)
- [ ] ❌ No `signal_tier` field (computed post-hoc OR documented as metadata)
- [ ] ❌ No `deployment_stage` field (computed post-hoc)
- [ ] ❌ No `overall_score` field (computed post-hoc)

**Acceptable metadata:**
- [ ] ✅ `content_type` (descriptive, not classification)
- [ ] ✅ `primary_technology` (descriptive)
- [ ] ✅ `confidence` (oracle's confidence)

---

## Post-Processing Section

- [ ] Section title: "POST-PROCESSING REFERENCE (NOT part of oracle output)"
- [ ] Emphasizes oracle outputs dimensional scores only
- [ ] Shows tier/stage calculation logic (Python code or formula)
- [ ] Explains weighting scheme (if applicable)
- [ ] Gatekeeper rules documented (if applicable)

**Example:**
```markdown
## POST-PROCESSING REFERENCE (NOT part of oracle output)

The oracle produces dimensional scores only. Tier classification is computed:

```python
weights = {'dim1': 0.20, 'dim2': 0.15, ...}
overall_score = sum(dimensions[k] * weights[k] for k in dimensions)

if overall_score >= 7.0:
    tier = "high"
elif overall_score >= 4.0:
    tier = "medium"
else:
    tier = "low"
```
```

---

## Examples Section

- [ ] High score example with reasoning
- [ ] Low score example with reasoning
- [ ] Out-of-scope example with reasoning
- [ ] Edge case examples (if applicable)
- [ ] Examples show dimensional scores, not just overall scores
- [ ] Examples include content_type or stage (if applicable)

**Minimum 3 examples:**
1. High-scoring article (7-10)
2. Low-scoring article (0-3)
3. Out-of-scope article (should score 0-2 on all dimensions)

---

## CHANGELOG

- [ ] CHANGELOG section exists
- [ ] Current version documented
- [ ] Breaking changes noted
- [ ] Expected impact statements included
- [ ] Dates included (YYYY-MM-DD format)
- [ ] Previous versions documented (if applicable)

**Format:**
```markdown
## CHANGELOG

**vX.Y (YYYY-MM-DD):**
- Change description
- **BREAKING CHANGE:** If applicable
- Expected impact: Reduce false positives from X% to Y%

**vX.Y-1 (YYYY-MM-DD):**
- Previous version
- Known issues documented
```

---

## Quality Checks

- [ ] Token estimate included (optional but helpful)
- [ ] Critical reminders at end of prompt
- [ ] All dimensions use consistent format
- [ ] No typos or formatting errors
- [ ] Inline filters are comprehensive (cover common out-of-scope cases)
- [ ] Scoring rubrics don't overlap (clear boundaries)

---

## Testing and Validation

- [ ] Run oracle calibration on 200 sample articles
- [ ] Check success rate (>95%)
- [ ] Verify dimensional score distributions (healthy variance)
- [ ] Review reasoning quality (specific to articles)
- [ ] Test on edge cases
- [ ] Verify JSON output parses correctly

**Use oracle-calibration-agent:**
```
Task: "Calibrate oracle for [filter] before batch scoring.
Sample 200 articles, use Gemini Pro for accuracy validation."
```

---

## Harmonization Check

- [ ] Run filter-harmonizer to check consistency
- [ ] Address critical issues before release
- [ ] Review minor issues and prioritize
- [ ] Update documentation based on findings

**Use filter-harmonizer agent:**
```
Task: "Check filter at [path] for harmonization.
Compare against uplifting v4 as reference."
```

---

## Documentation

- [ ] Filter README.md updated (if exists)
- [ ] config.yaml updated with dimension definitions
- [ ] Training documentation updated (if needed)
- [ ] Examples added to examples/ directory (if applicable)

---

## Pre-Release Checklist

- [ ] All checklist items above completed
- [ ] Oracle calibration passed (✅ READY status)
- [ ] Harmonization check passed (✅ HARMONIZED or ⚠️ MINOR ISSUES)
- [ ] Filter version incremented
- [ ] CHANGELOG updated with release notes
- [ ] Documentation reviewed
- [ ] Backup of previous version created (if updating)

---

## Post-Release

- [ ] Monitor first 1,000 labeled articles
- [ ] Check for unexpected patterns
- [ ] Collect feedback from users
- [ ] Schedule quarterly harmonization audit
- [ ] Plan next version improvements (if needed)

---

## Common Mistakes to Avoid

### ❌ Oracle outputs tier classification
**Problem:** Violates "dimensional scores only" principle
**Fix:** Remove tier from output, add to post-processing

### ❌ ARTICLE before scope
**Problem:** Oracle doesn't see scope before article
**Fix:** Move ARTICLE to after scope/rules

### ❌ Top-level filters only, no inline filters
**Problem:** Fast models skip top-level SCOPE section
**Fix:** Add inline CRITICAL FILTERS to each dimension

### ❌ Vague scoring rubrics
**Problem:** Oracle can't distinguish between score levels
**Fix:** Add specific, testable criteria for each score level

### ❌ No evidence indicators
**Problem:** Oracle doesn't know what to look for
**Fix:** Add "Evidence" line showing what to check in article

### ❌ Missing CHANGELOG
**Problem:** No version history or change tracking
**Fix:** Add CHANGELOG section documenting all versions

### ❌ No post-processing section
**Problem:** Tier calculation logic not documented
**Fix:** Add POST-PROCESSING REFERENCE section

---

## Reference Filters

**Best practice examples:**
- `filters/uplifting/v4/prompt-compressed.md` - Excellent structure, comprehensive inline filters
- `filters/investment_risk/v2/prompt-compressed.md` - Good inline filters, clear philosophy
- `filters/sustainability_tech_deployment/v3/prompt-compressed.md` <!-- placeholder --> - Clear gatekeepers, good structure

---

## Tools and Agents

**During development:**
- **filter-harmonizer**: Check structural consistency
- **oracle-calibration-agent**: Test on sample articles
- **prompt-calibration-agent**: Fine-tune prompt based on results

**After labeling:**
- **dimensional-regression-qa-agent**: Validate labeled dataset
- **model-evaluation-agent**: Evaluate trained model

---

## Quick Links

- [Filter Harmonization Guide](FILTER_HARMONIZATION_GUIDE.md)
- [Oracle Calibration Template](templates/oracle-calibration-agent.md)
- [Agent Operations Guide](agent-operations.md)
- Filter Harmonizer (`filter-harmonizer.md` <!-- placeholder -->)

---

**Version:** 1.0
**Last Updated:** 2025-11-17
**Maintainer:** LLM Distillery Project

---

## Checklist Summary

**Pre-Development:** 5 items
**Header:** 6 items
**Scope:** 4 items
**Structure:** 9 items
**Dimensions:** 8 items per dimension
**Output Format:** 8 items
**Post-Processing:** 5 items
**Examples:** 6 items
**CHANGELOG:** 6 items
**Quality:** 6 items
**Testing:** 6 items
**Harmonization:** 4 items
**Documentation:** 4 items
**Pre-Release:** 8 items
**Post-Release:** 5 items

**Total:** ~80 checklist items for comprehensive filter development

Print this checklist and check off items as you create your filter!
