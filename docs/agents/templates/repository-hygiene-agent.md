# Repository Hygiene Agent Template v1.0

---
name: "Repository Hygiene"
description: "Periodic repository health check and cleanup recommendations"
model: "sonnet"
trigger_keywords:
  - "check repository hygiene"
  - "audit repository"
  - "cleanup check"
when_to_use: "Monthly or after major development sprints to catch drift"
focus: "Preventive maintenance - catch problems early"
output: "Hygiene report with actionable cleanup recommendations"
---

**Purpose:** Proactively identify repository maintenance issues before they accumulate.

**When to use:**
- Monthly scheduled hygiene checks
- After completing major features or milestones
- Before major releases
- When repository feels "messy"

**Expected duration:** 10-15 minutes

---

## Agent Task Description

You are auditing the repository for hygiene issues that violate the AI-Augmented Development Workflow principles (see `docs/agents/AI_AUGMENTED_WORKFLOW.md`).

**Your responsibilities:**
1. Find untracked files outside sandbox/
2. Identify scripts without corresponding documentation
3. Flag hardcoded values that should be in config files
4. Check docs/SESSION_STATE.md currency (is it current?)
5. Identify stale documentation or outdated references
6. Generate hygiene report with actionable recommendations

---

## Hygiene Checks

### CRITICAL (High Priority - Fix Immediately)

#### 1. Sandbox Workflow Violations
**Check:** Files that should be in sandbox/ but aren't

**How to check:**
```bash
# Find untracked files outside sandbox, scripts, docs
git ls-files --others --exclude-standard | grep -v "^sandbox/" | grep -v "\.pyc$" | grep -v "__pycache__"
```

**Red flags:**
- ❌ Untracked .py scripts outside scripts/ or sandbox/
- ❌ Work-in-progress .md files at root level
- ❌ Analysis scripts in scripts/ (should be sandbox/)
- ❌ Calibration/experiment files in filter directories

**Recommendation format:**
```
CRITICAL: Sandbox workflow violation
- Found: scripts/experiment_analysis.py (untracked)
- Action: Move to sandbox/analysis_scripts/
- Reason: Experimental scripts should not pollute scripts/
```

#### 2. Hardcoded Configuration Values
**Check:** Code that duplicates config.yaml values

**How to check:**
```bash
# Search for hardcoded dimension names
grep -r "agency.*progress.*collective_benefit" --include="*.py" scripts/ training/

# Search for hardcoded tier boundaries
grep -r "tier.*>=.*[0-9]" --include="*.py" scripts/ training/
```

**Red flags:**
- ❌ Dimension names hardcoded in scripts (should read from config.yaml)
- ❌ Tier boundaries hardcoded (should read from config.yaml)
- ❌ Filter-specific logic in "generic" scripts

**Recommendation format:**
```
CRITICAL: Hardcoded configuration
- File: scripts/some_script.py:42
- Found: dimensions = ['agency', 'progress', ...]
- Action: Read dimensions from config.yaml instead
- Reason: Single source of truth principle violated
```

#### 3. Stale docs/SESSION_STATE.md
**Check:** docs/SESSION_STATE.md matches actual repository state

**How to check:**
- Compare "Current Status" against actual files
- Check "Files Modified This Session" date
- Verify "Next Steps" are still relevant

**Red flags:**
- ❌ docs/SESSION_STATE.md not updated in >2 weeks
- ❌ "Current Status" doesn't match git status
- ❌ "Next Steps" reference completed work

**Recommendation format:**
```
CRITICAL: docs/SESSION_STATE.md is stale
- Last updated: 2025-11-01 (14 days ago)
- Action: Update current status, accomplishments, next steps
- Reason: docs/SESSION_STATE.md is primary session recovery document
```

### IMPORTANT (Medium Priority - Fix Soon)

#### 4. Undocumented Production Scripts
**Check:** Scripts in scripts/ without documentation

**How to check:**
```bash
# Find scripts without docstrings
for f in scripts/*.py; do
  if ! head -20 "$f" | grep -q '"""'; then
    echo "Missing docstring: $f"
  fi
done
```

**Red flags:**
- ⚠️ Production script without module docstring
- ⚠️ Script not mentioned in any README or doc
- ⚠️ Unclear when/why to use the script

**Recommendation format:**
```
IMPORTANT: Undocumented script
- File: scripts/new_utility.py
- Action: Add module docstring with purpose, usage, examples
- Consider: Adding to training/README.md if part of workflow
```

#### 5. Stale Documentation References
**Check:** Documentation referencing moved/deleted files

**How to check:**
```bash
# Find references to old file paths
grep -r "docs/ARCHITECTURE.md" docs/
grep -r "scripts/old_script.py" docs/
```

**Red flags:**
- ⚠️ Documentation links to deleted files
- ⚠️ References to old directory structure
- ⚠️ Example commands using moved scripts

**Recommendation format:**
```
IMPORTANT: Stale documentation reference
- File: training/README.md:45
- References: scripts/old_script.py (deleted)
- Action: Update to current path or remove reference
```

#### 6. Missing ADRs for Significant Changes
**Check:** Major changes without Architecture Decision Records

**How to check:**
- Review recent git commits for architectural changes
- Check docs/decisions/ for corresponding ADRs
- Look for patterns/conventions without documentation

**Red flags:**
- ⚠️ New training approach without ADR
- ⚠️ Changed filter structure without ADR
- ⚠️ Modified evaluation criteria without ADR

**Recommendation format:**
```
IMPORTANT: Missing ADR
- Change: New stratified sampling approach (commit abc123)
- Action: Create ADR documenting decision, alternatives, trade-offs
- File: docs/decisions/YYYY-MM-DD-stratified-sampling.md
```

### NICE-TO-HAVE (Low Priority - Consider)

#### 7. Code Duplication
**Check:** Similar code across multiple files

**How to check:**
- Look for repeated functions across scripts
- Check for similar data loading patterns
- Identify opportunities for shared utilities

**Informational:**
```
NICE-TO-HAVE: Code duplication opportunity
- Found: Similar JSONL loading in 3 scripts
- Consider: Creating shared utility function
- Benefit: DRY principle, easier maintenance
```

#### 8. Experiment Archaeology
**Check:** Old experiments in sandbox/ that could be archived

**How to check:**
```bash
# Find sandbox experiments older than 60 days
find sandbox/ -type f -name "*.py" -mtime +60
```

**Informational:**
```
NICE-TO-HAVE: Old experiments
- Found: 5 scripts in sandbox/ older than 60 days
- Consider: Move to sandbox/archive/2025-Q3/ or delete
- Benefit: Cleaner sandbox for active experiments
```

---

## Report Format

Generate a markdown report: `reports/repository_hygiene_YYYY-MM-DD.md` <!-- placeholder -->

### Executive Summary

```markdown
# Repository Hygiene Report

**Date:** 2025-11-15
**Status:** ⚠️ REVIEW NEEDED | ✅ HEALTHY | ❌ ACTION REQUIRED

## Summary
- Critical issues: 2
- Important issues: 3
- Nice-to-have improvements: 1

**Overall assessment:** [1-2 sentence summary]

**Recommended action:** [Fix critical issues this session | Schedule cleanup | All good]
```

### Findings by Category

For each finding:
```markdown
## Critical Issues

### 1. Sandbox Workflow Violation: Experimental Scripts in scripts/

**Severity:** CRITICAL
**Impact:** Pollutes production scripts directory, violates workflow principles

**Files affected:**
- scripts/analyze_something.py (untracked, 145 lines)
- scripts/temp_experiment.py (untracked, 67 lines)

**Recommended action:**
1. Move to sandbox/analysis_scripts/
2. Update any documentation references
3. Add sandbox/README.md if missing

**Effort:** 10 minutes
```

### Priority Matrix

```markdown
## Recommended Actions (Priority Order)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 | Move experimental scripts to sandbox | 10 min | High |
| 2 | Update docs/SESSION_STATE.md | 15 min | High |
| 3 | Document new production script | 20 min | Medium |
| 4 | Fix stale doc references | 5 min | Medium |
| 5 | Create missing ADR | 30 min | Medium |
```

---

## Decision Criteria

**✅ HEALTHY**
- No critical issues
- 0-1 important issues
- docs/SESSION_STATE.md current (<7 days)
- All production scripts documented
- No sandbox violations

**⚠️ REVIEW NEEDED**
- 1-2 critical issues
- 2-4 important issues
- Fixable in one session (<2 hours)

**❌ ACTION REQUIRED**
- 3+ critical issues
- 5+ important issues
- Major refactoring needed
- Requires dedicated cleanup session

---

## Usage Example

```
Task: "Run repository hygiene check using the Repository Hygiene Agent template
from docs/agents/templates/repository-hygiene-agent.md. Generate hygiene report
in reports/repository_hygiene_2025-11-15.md with prioritized recommendations."
```

**Agent will:**
1. Run all hygiene checks
2. Categorize findings by severity
3. Generate hygiene report with recommendations
4. Prioritize actions by impact/effort ratio

---

## Best Practices

### 1. Schedule Regular Checks

**Frequency:** Monthly or after major milestones

**Add to calendar:**
- First Monday of each month
- After completing major features
- Before releases

### 2. Fix Critical Issues Immediately

Don't let critical issues accumulate. Schedule 30-60 minutes to fix them the same day they're identified.

### 3. Batch Important Issues

Create a "Repository Maintenance" task that you tackle periodically (e.g., last Friday of month).

### 4. Don't Ignore Nice-to-Haves

They compound. Once per quarter, spend a session on nice-to-have improvements.

### 5. Update Hygiene Checks

As the project evolves, update this template with new checks relevant to your workflow.

---

## Integration with Workflow

This agent enforces the principles from `docs/agents/AI_AUGMENTED_WORKFLOW.md`:

1. **Sandbox for experiments** - Catches workflow violations
2. **Single source of truth** - Flags hardcoded config values
3. **Effortless documentation** - Ensures docs/SESSION_STATE.md stays current
4. **Architecture Decision Records** - Reminds to document decisions

**Prevention > Cure:** Regular hygiene checks prevent the repository from becoming unmaintainable.

---

## Version History

### v1.0 (2025-11-15)
- Initial repository hygiene agent template
- Critical/Important/Nice-to-have categorization
- Automated checks for sandbox violations, hardcoded config, stale docs
- Integration with AI-Augmented Development Workflow
