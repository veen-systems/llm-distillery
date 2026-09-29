# Filter Package Validation & Release Report Agent v1.0

---
name: "Filter Package Validation"
description: "Validate filter package completeness and generate production readiness report"
model: "sonnet"
trigger_keywords:
  - "validate filter package"
  - "filter release report"
  - "check filter completeness"
when_to_use: "Before declaring a filter production-ready, after calibration/validation complete"
focus: "Quality gate - ensure filter package is complete, validated, and documented"
output: "Validation report + Human-readable release report for stakeholders"
---

**Purpose:** Comprehensive validation that a filter package is complete, calibrated, and ready for production use. Generates both technical validation report and stakeholder-friendly release report.

**When to use:**
- After calibration and validation are complete
- Before batch scoring full dataset
- Before deploying filter to production
- Quarterly filter quality audits

**Expected duration:** 15-30 minutes

---

## Agent Task Description

You are validating a filter package for production readiness. This is a quality gate that ensures the filter is complete, properly calibrated, and ready to use.

**Your responsibilities:**
1. Check all required files exist and are valid
2. Validate configuration integrity (dimensions, weights, tiers)
3. Verify calibration and validation were completed
4. Check postfilter logic matches config
5. Generate technical validation report
6. Generate human-readable release report for stakeholders

**Input:**
- Filter directory path (e.g., `filters/uplifting/v4`)
- Calibration report path (optional - will search)
- Validation report path (optional - will search)

**Output:**
- `filters/{name}/v{version}/validation_report.md` - Technical checklist
- `filters/{name}/v{version}/release_report.md` - Stakeholder-facing report

---

## Validation Checklist

### CRITICAL (Must Pass)

#### 1. Required Files Exist

**Check:**
```bash
# All required files present?
filters/{name}/v{version}/
├── config.yaml              ✓
├── prompt.md                ✓ (or prompt-compressed.md)
├── postfilter.py            ✓
└── README.md                ✓
```

**Pass criteria:**
- ✅ All 4 files exist
- ✅ No empty files

**Failure:**
- ❌ Missing any required file
- ❌ File exists but is empty

#### 2. Config Validation

**Check:**
```python
# Load and validate config.yaml
import yaml
config = yaml.safe_load(open('config.yaml'))

# Required sections
assert 'filter' in config
assert 'scoring' in config
assert 'dimensions' in config['scoring']
assert 'tiers' in config['scoring']

# Dimensions
dimensions = config['scoring']['dimensions']
assert len(dimensions) == 8  # Standard for dimensional regression

# Weights sum to 1.0
weights = [d['weight'] for d in dimensions.values()]
assert 0.99 <= sum(weights) <= 1.01

# Tiers have thresholds
tiers = config['scoring']['tiers']
for tier_name, tier_config in tiers.items():
    assert 'threshold' in tier_config
    assert 'description' in tier_config
```

**Pass criteria:**
- ✅ Valid YAML
- ✅ All required sections present
- ✅ 8 dimensions defined
- ✅ Weights sum to 1.0 (±0.01)
- ✅ All tiers have threshold + description

**Warnings:**
- ⚠️ Dimension weights heavily skewed (one >40%)
- ⚠️ Tier thresholds not sorted (0.0 → 10.0)

#### 3. Prompt-Config Consistency

**Check:**
```bash
# Extract dimension names from config
config_dims = ['agency', 'progress', 'collective_benefit', ...]

# Extract dimension names from prompt
grep "dimension:" prompt.md | extract dimension names
prompt_dims = [...]

# Compare
assert set(config_dims) == set(prompt_dims)
```

**Pass criteria:**
- ✅ All config dimensions appear in prompt
- ✅ No extra dimensions in prompt
- ✅ Dimension names match exactly (case-sensitive)

**Failure:**
- ❌ Dimension mismatch (prompt has different dimensions than config)

#### 4. Postfilter Exists and Works

**Check:**
```python
# Import and test postfilter
from filters.{name}.v{version}.postfilter import PostFilter

pf = PostFilter("filters/{name}/v{version}")

# Test with dummy scores
test_scores = {dim: 5.0 for dim in config['scoring']['dimensions'].keys()}
result = pf.classify(test_scores)

# Validate output
assert 'tier' in result
assert 'overall_score' in result
assert 'dimensional_scores' in result
```

**Pass criteria:**
- ✅ Postfilter imports successfully
- ✅ `classify()` method exists
- ✅ Returns expected output format
- ✅ Handles all dimensions from config

**Failure:**
- ❌ Import error
- ❌ Missing `classify()` method
- ❌ Crashes on test input

#### 5. Calibration Completed

**Check:**
```bash
# Search for calibration report
find filters/{name}/v{version}/ -name "*calibration*report*.md"

# Validate report content
grep -q "Status.*READY\|Status.*PASS" calibration_report.md
```

**Pass criteria:**
- ✅ Calibration report exists
- ✅ Report shows PASS or READY status
- ✅ Report dated within last 90 days

**Failure:**
- ❌ No calibration report found
- ❌ Calibration FAILED or BLOCKED
- ❌ Calibration report >90 days old (stale)

#### 6. Validation Completed

**Check:**
```bash
# Search for validation report
find filters/{name}/v{version}/ -name "*validation*report*.md"

# Validate generalization
grep "validation.*≈.*calibration\|validation.*generalized" validation_report.md
```

**Pass criteria:**
- ✅ Validation report exists
- ✅ Validation metrics ≈ calibration metrics (generalized)
- ✅ No overfitting detected

**Warnings:**
- ⚠️ Validation report missing (not required for all filters)
- ⚠️ Validation worse than calibration (possible overfitting)

### IMPORTANT (Should Pass)

#### 7. README Completeness

**Check README sections:**
- ✅ Filter description and purpose
- ✅ Usage examples
- ✅ Example outputs
- ✅ Version information
- ✅ Calibration results summary

**Warnings:**
- ⚠️ README missing usage examples
- ⚠️ No example outputs shown
- ⚠️ Version not documented

#### 8. Inline Filters Present (if applicable)

**Check:**
```bash
# For filters that should have inline filters
grep -q "OUT OF SCOPE" prompt.md
grep -q "NEVER score above" prompt.md
```

**Pass criteria:**
- ✅ Inline filters defined in prompt
- ✅ Clear scope boundaries

**Not applicable if:** Filter doesn't need inline filters

#### 9. Example Outputs Exist

**Check:**
```bash
# Look for examples
find filters/{name}/v{version}/ -name "examples.md" -o -name "example_outputs.md"
```

**Pass criteria:**
- ✅ Example outputs file exists
- ✅ Shows at least 3 examples (high/medium/low scoring)

**Warnings:**
- ⚠️ No examples file (should create for stakeholders)

### NICE-TO-HAVE

#### 10. Test Coverage

**Check:**
```bash
# Look for tests
find filters/{name}/v{version}/ -name "test_*.py" -o -name "*_test.py"
```

**Nice-to-have:**
- Unit tests for postfilter logic
- Integration tests for full pipeline

---

## Release Report Generation

After validation passes, generate a **human-readable release report** for stakeholders.

### Template: Release Report

```markdown
# {Filter Name} v{version} - Production Release Report

**Date:** {today}
**Status:** ✅ PRODUCTION READY
**Maintainer:** {team/person}

---

## Executive Summary

The **{Filter Name}** filter has been developed, calibrated, and validated. It is ready for production use to {primary use case}.

**Key Results:**
- ✅ Calibration: {success rate}% on {sample size} articles
- ✅ Validation: Generalized successfully (no overfitting)
- ✅ False positive rate: {X}% (target: <{Y}%)
- ✅ Technical validation: All 10 checks passed

**Recommendation:** Deploy to production for {use case}.

---

## What This Filter Does

**Purpose:** {description from config}

**Example Use Cases:**
- {use case 1 from config}
- {use case 2 from config}

**How It Works:**
1. Scores articles on {N} dimensions (0-10 scale)
2. Applies weighted average + gatekeeper rules
3. Assigns tier: {tier names}
4. Flags top articles for {purpose}

---

## Performance Metrics

### Calibration Results

**Dataset:** {calibration sample size} articles (stratified sample)
**Oracle:** {Gemini Flash / Gemini Pro}
**Date:** {calibration date}

**Results:**
- **Success rate:** {X}% ({Y}/{Z} articles)
- **Dimensional variance:** Healthy (std dev {range})
- **Range coverage:** Full 0-10 spectrum
- **False positive rate:** {X}% (off-topic articles scoring >5.0)
- **False negative rate:** {X}% (on-topic articles scoring <5.0)

**Verdict:** ✅ PASS - Oracle is well-calibrated

### Validation Results

**Dataset:** {validation sample size} articles (fresh sample, different seed)
**Oracle:** {Gemini Flash}
**Date:** {validation date}

**Results:**
- **Generalization:** ✅ Validation ≈ Calibration (no overfitting)
- **False positive rate:** {X}% (calibration: {Y}%)
- **False negative rate:** {X}% (calibration: {Y}%)

**Verdict:** ✅ PASS - Improvements generalized successfully

---

## Example Outputs

### Example 1: High Scoring Article (Tier: {tier_name})

**Title:** "{article title}"
**Source:** {source}
**Date:** {date}

**Dimensional Scores:**
```
{dimension_1}: {score}/10
{dimension_2}: {score}/10
...
```

**Overall Score:** {overall_score}/10
**Tier:** {tier_name}
**Why This Scored High:** {brief explanation}

### Example 2: Medium Scoring Article (Tier: {tier_name})

{same format}

### Example 3: Low Scoring Article (Tier: {tier_name})

{same format}

### Example 4: Correctly Rejected (Off-Topic)

**Title:** "{article title}"
**Why Rejected:** {reason - e.g., "Generic IT infrastructure, not climate tech"}
**Dimensional Scores:** All 0-2 (correctly identified as out of scope)

---

## Known Edge Cases

**What the filter handles well:**
- {strength 1}
- {strength 2}

**What to watch for:**
- {edge case 1} - May have {X}% false positive rate
- {edge case 2} - Acceptable trade-off for {reason}

**Mitigation:**
- {how to handle edge cases}

---

## Production Deployment

### Batch Scoring Command

```bash
python -m ground_truth.batch_scorer \
    --filter filters/{name}/v{version} \
    --source datasets/raw/articles.jsonl \
    --output-dir datasets/scored/{name}_v{version} \
    --llm gemini-flash \
    --batch-size 50 \
    --target-scored 10000
```

**Expected Cost:** ~${cost} for 10,000 articles (Gemini Flash)
**Expected Time:** ~{hours} hours

### Training Model (Optional)

After batch scoring, train student model for fast inference:

```bash
python training/prepare_data.py \
    --filter filters/{name}/v{version} \
    --input datasets/scored/{name}/scored_articles.jsonl \
    --output-dir datasets/training/{name}

python training/train.py \
    --config filters/{name}/v{version}/config.yaml \
    --data-dir datasets/training/{name}
```

---

## Technical Specifications

**Filter Package:** `filters/{name}/v{version}/`
**Configuration:** 8-dimensional regression
**Dimensions:** {list dimension names}
**Tiers:** {list tier names with thresholds}
**Postfilter:** Filter-specific logic in `postfilter.py`

**Dependencies:**
- Python 3.10+
- PyYAML
- google-generativeai (for batch scoring)

**Documentation:**
- README: `filters/{name}/v{version}/README.md`
- Calibration: `filters/{name}/v{version}/calibration_report.md`
- Validation: `filters/{name}/v{version}/validation_report.md`

---

## Validation Checklist

**Technical validation completed {date}:**
- ✅ All required files present
- ✅ Config valid (dimensions, weights, tiers)
- ✅ Prompt-config consistency verified
- ✅ Postfilter tested and working
- ✅ Calibration PASSED
- ✅ Validation PASSED (no overfitting)
- ✅ README complete
- ✅ Example outputs documented

**Approval:** {team/person} - {date}

---

## Next Steps

**Immediate:**
1. Deploy for batch scoring on production dataset
2. Monitor first 500 articles for quality
3. Generate training data for student model

**Future:**
- Train Qwen 2.5 student model for fast inference
- Quarterly recalibration (check for drift)
- Expand to additional use cases

---

## Contacts

**Maintainer:** {team/person}
**Questions:** {email/slack channel}
**Documentation:** `docs/agents/templates/filter-package-validation-agent.md`

---

**Report generated by:** Filter Package Validation Agent v1.0
**Date:** {timestamp}
```

---

## Usage Example

```
Task: "Validate the uplifting v4 filter package for production readiness.

Filter path: filters/uplifting/v4
Generate both technical validation report and stakeholder release report.

Use the Filter Package Validation Agent from
docs/agents/templates/filter-package-validation-agent.md"
```

**Agent will:**
1. Check all 10 validation criteria
2. Generate `filters/uplifting/v4/validation_report.md` (technical)
3. Generate `filters/uplifting/v4/release_report.md` <!-- placeholder --> (stakeholder-facing)
4. Provide production readiness decision

---

## Decision Criteria

**✅ PRODUCTION READY**
- All CRITICAL checks passed (6/6)
- All IMPORTANT checks passed (3/3)
- Calibration + Validation completed and passed
- Release report generated

→ **Action:** Approve for batch scoring or production deployment

**⚠️ REVIEW NEEDED**
- 1-2 CRITICAL checks failed (fixable)
- IMPORTANT checks have warnings
- Calibration passed but validation missing

→ **Action:** Fix issues, re-validate

**❌ NOT READY**
- 3+ CRITICAL checks failed
- Calibration or validation FAILED
- Major configuration errors

→ **Action:** Significant rework needed

---

## Best Practices

### 1. Run Before Every Major Milestone

**When to validate:**
- Before batch scoring full dataset
- Before training student model
- Before production deployment
- Quarterly quality audits

### 2. Share Release Report with Stakeholders

**Audience:**
- Product team (what the filter does)
- Data science team (performance metrics)
- Engineering team (deployment instructions)
- Leadership (production readiness decision)

### 3. Keep Reports Updated

**Update triggers:**
- After recalibration
- After prompt changes
- When performance metrics change
- Quarterly reviews

### 4. Use as Quality Gate

**Make validation mandatory:**
- No batch scoring without passing validation
- No production deployment without release report
- Document exceptions (why validation was skipped)

---

## Integration with Workflow

This agent is the **final quality gate** in the filter development workflow:

```
1. Write prompt → 2. Calibrate → 3. Validate → 4. Filter Package Validation ← YOU ARE HERE → 5. Production
```

**Prevents:**
- Incomplete filter packages in production
- Missing calibration/validation
- Undocumented filters
- Configuration errors

**Ensures:**
- Professional, complete filter packages
- Stakeholder-ready documentation
- Production readiness verified

---

## Version History

### v1.0 (2025-11-15)
- Initial filter package validation agent template
- 10-point validation checklist (Critical/Important/Nice-to-have)
- Release report generation for stakeholders
- Technical validation report for engineers
- Production readiness decision criteria
