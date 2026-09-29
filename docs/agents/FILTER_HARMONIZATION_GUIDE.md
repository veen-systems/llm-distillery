# Filter Harmonization Quick Reference

**Agent:** filter-harmonizer
**Location:** `C:\local_dev\llm-distillery\docs\agents\filter-harmonizer.md`

---

## When to Use

- After creating a new filter
- Before releasing a filter version
- Quarterly structural audits
- After major prompt restructuring
- When onboarding new filter contributors

---

## Architecture Context

The LLM Distillery uses a **3-stage filter architecture**:

1. **Prefilter** (`prefilter.py`) - Fast rule-based blocking (~5ms)
   - Blocks obvious out-of-scope content
   - Target: <10% false negative rate

2. **Oracle/Student Model** (`prompt-compressed.md`) - Dimensional scoring (20-50ms)
   - **Outputs**: 8 dimensional scores (0-10) + metadata
   - **Does NOT output**: Tier classifications
   - Models: Oracle (Gemini Flash/Claude) → Student (Qwen2.5-7B)

3. **Postfilter** (`postfilter.py`) - Tier classification (<10ms)
   - Maps dimensional scores → tier classification
   - Applies gatekeeper rules, uses config.yaml thresholds

**This guide focuses on Stage 2 (Oracle/Model) harmonization** - ensuring all filter prompts follow consistent structure and oracle output discipline.

For the complete architecture, see [ARCHITECTURE.md](../ARCHITECTURE.md).

---

## Quick Invocation Examples

### Full Harmonization Check
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

### Single Filter Audit
```
Task: "Audit filters/investment-risk/v2/prompt-compressed.md for harmonization.
Compare against filters/uplifting/v4/prompt-compressed.md as reference.
List specific issues with line numbers and recommended fixes."
```

### Check New Filter
```
Task: "Check the new filter at filters/my-new-filter/v1/prompt-compressed.md
for harmonization with existing filters. Focus on:
1. Does it follow the standard structure?
2. Oracle output statement present?
3. Inline filters used correctly?
4. No classification fields in oracle output?"
```

---

## Key Harmonization Principles

### 1. Oracle Output Discipline ⭐
**Rule:** Oracle outputs dimensional scores (0-10) ONLY, NOT tier/stage classifications

**Check:**
- Header has explicit "Oracle Output" statement
- JSON output does NOT include tier/stage/overall_score fields
- Post-processing section explains tier calculation

### 2. Standard Structure ⭐
**Order:**
1. Header (Purpose, Version, Focus, Philosophy, Oracle Output)
2. Scope (IN SCOPE / OUT OF SCOPE)
3. Rules/gatekeepers
4. **ARTICLE** (after scope/rules)
5. Dimensions (with inline filters)
6. Examples
7. Output format
8. Post-processing reference
9. CHANGELOG

### 3. Inline Filters ⭐
**Every dimension must have:**
```markdown
**❌ CRITICAL FILTERS - If article is ANY of these, score 0-2:**
- Filter 1
- Filter 2

**If NONE of above filters match, score normally:**
- 0-2: Description
- 3-4: Description
```

**Why:** Fast models skip top-level SCOPE sections

### 4. CHANGELOG Required ⭐
**Every filter must document:**
- Version numbers
- Breaking changes
- Expected impact
- Dates

---

## Common Issues and Fixes

### Issue: Oracle outputs tier classification
**Problem:** JSON includes `tier`, `signal_tier`, or `deployment_stage`

**Fix:**
1. Remove from JSON output schema
2. Add to post-processing section with calculation logic
3. Document as "computed post-hoc, not by oracle"

### Issue: ARTICLE before scope
**Problem:** ARTICLE appears before scope/rules sections

**Fix:** Move ARTICLE to after scope/rules, before dimensions

### Issue: Missing inline filters
**Problem:** Top-level SCOPE only, no per-dimension filters

**Fix:** Add inline CRITICAL FILTERS to each dimension

### Issue: No Oracle Output statement
**Problem:** Header missing explicit statement about oracle role

**Fix:** Add after Version line:
```markdown
**Oracle Output**: Dimensional scores only (0-10 per dimension). Tier classification is applied post-processing, not by the oracle.
```

---

## Harmonization Checklist

Use this when creating new filters:

- [ ] Header includes Purpose, Version, Focus
- [ ] Header includes "Oracle Output" statement
- [ ] Philosophy statement present (optional but recommended)
- [ ] Scope section defines IN SCOPE / OUT OF SCOPE
- [ ] ARTICLE appears AFTER scope/rules, BEFORE dimensions
- [ ] Each dimension has inline CRITICAL FILTERS
- [ ] JSON output does NOT include tier/stage classification
- [ ] Post-processing section explains tier calculation
- [ ] Examples section includes validation examples
- [ ] CHANGELOG documents version history
- [ ] Token estimate included (optional)

---

## Report Interpretation

### ✅ HARMONIZED
All filters structurally consistent. No action needed.

### ⚠️ MINOR ISSUES
Filters work but could be more consistent. Fix in next update cycle.

**Common minor issues:**
- Missing Philosophy statements
- CHANGELOG format variations
- Classification fields documented as metadata (OK if explicit)

### ❌ MAJOR ISSUES
Filters violate core principles. Fix before release.

**Common major issues:**
- Oracle outputs tier classifications (violates oracle discipline)
- Missing inline filters (fast models will fail)
- ARTICLE placement wrong
- No version tracking

---

## Example Workflow

### Creating a New Filter

1. **Create initial prompt** based on template

2. **Run harmonization check:**
   ```
   Task: "Check new filter at filters/my-filter/v1/prompt-compressed.md
   for harmonization. Compare against uplifting v4 as reference."
   ```

3. **Review report** and fix issues

4. **Run oracle calibration** to test:
   ```
   Task: "Calibrate oracle for my-filter before batch scoring.
   Sample 200 articles, use Gemini Pro."
   ```

5. **Re-run harmonization** after fixes

6. **Document in CHANGELOG**

### Quarterly Audit

1. **Run full harmonization check** on all filters

2. **Review report** for any drift

3. **Prioritize fixes:**
   - Critical: Fix immediately
   - Minor: Schedule for next update
   - Informational: Note for future

4. **Update documentation** if patterns changed

---

## Filters in Scope

### Active Filters (Check These)
- `filters/uplifting/v4/prompt-compressed.md` (reference implementation)
- `filters/investment_risk/v2/prompt-compressed.md`
- `filters/sustainability_tech_deployment/v3/prompt-compressed.md` <!-- placeholder -->
- `filters/sustainability_tech_innovation/v1/prompt-compressed.md` <!-- placeholder -->

### Legacy Filters (Archive)
- `filters/uplifting/v3/` (superseded by v4)
- `filters/investment-risk/v1/` (superseded by v2)
- `filters/sustainability_tech_deployment/v2/` (superseded by v3)

---

## Integration with CI/CD

**Future:** Add harmonization checks to pre-release validation

**Script idea:**
```bash
# Before filter release
python scripts/check_filter_harmonization.py \
    --filter filters/uplifting/v5 \
    --reference filters/uplifting/v4 \
    --fail-on-critical

# Exit code 0 = harmonized
# Exit code 1 = minor issues (warn)
# Exit code 2 = critical issues (block release)
```

---

## Related Documentation

- **Agent template:** `docs/agents/filter-harmonizer.md` <!-- placeholder -->
- **Agent workflow guide:** `docs/agents/agent-operations.md`
- **Filter development guide:** `docs/FILTER_DEVELOPMENT.md` <!-- placeholder --> (if exists)
- **Oracle calibration:** `docs/agents/templates/oracle-calibration-agent.md`

---

## Questions?

**Common questions:**

**Q: Why can't oracle output tier classifications?**
A: Separation of concerns. Oracle focuses on accurate dimensional scoring. Tier logic is post-processing, can be changed without re-labeling.

**Q: What if my filter naturally outputs tiers?**
A: Fine to include as metadata (like `content_type`), but document explicitly that it's descriptive, not computed by weighted formula.

**Q: Do I need inline filters if I have a SCOPE section?**
A: Yes. Fast models (Gemini Flash) skip top-level SCOPE. Inline filters ensure oracle checks before scoring each dimension.

**Q: How often should I run harmonization checks?**
A: After creating new filters, before releases, and quarterly for active filters.

**Q: What if harmonization requires breaking changes?**
A: Document in CHANGELOG, increment version (v2 → v3), and consider re-calibrating oracle.

---

**Version:** 1.0
**Last Updated:** 2025-11-17
**Maintainer:** LLM Distillery Project
