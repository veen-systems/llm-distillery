> **Note (Mar 2026):** For general operations guidance (principles, runbooks, deployment), see `docs/WAY-OF-WORKING.md`. This guide covers agent-specific patterns for dataset validation and QA.

# Agent Workflow Guide

## Overview

This guide documents the agent-assisted workflow for dataset validation and quality assurance in the LLM Distillery project. Agents are Claude Code subprocesses that autonomously handle complex, multi-step tasks.

## When to Use Agents

Use agents for:
- **Complex multi-step validation** - Dataset QA across multiple files
- **Systematic exploration** - Codebase analysis, file discovery
- **Repetitive analysis** - Checking multiple datasets against criteria
- **Research tasks** - Gathering information from documentation

Don't use agents for:
- **Simple single-file operations** - Use Read tool directly
- **Direct edits** - Use Edit tool directly
- **Known file paths** - Read/Edit directly instead of searching

## Agent Types

### General-Purpose Agent
**Use for:** Complex tasks, research, multi-step validation

**How to invoke:**
```
Use the Task tool with subagent_type: "general-purpose"
Provide detailed prompt describing task and expected output
```

### Explore Agent
**Use for:** Codebase exploration, finding files by patterns

**Thoroughness levels:**
- `quick` - Basic searches
- `medium` - Moderate exploration
- `very thorough` - Comprehensive analysis

## Dimensional Regression QA Agent Workflow

### Purpose
Validate ground truth datasets for multi-dimensional regression training, ensuring dimensional score quality (not tier classification accuracy).

### Template Location
`docs/agents/templates/dimensional-regression-qa-agent.md`

### When to Use
- After consolidating labeled data
- Before training model
- After any major dataset changes
- Quarterly validation of production datasets

### How to Invoke

**Step 1: Prepare the prompt**

Include:
- Dataset path
- Filter name
- Number of expected dimensions
- Dimension names
- Reference to QA template

**Step 2: Launch agent via Task tool**

Example for uplifting filter:
```
Task: "Audit the uplifting dataset at datasets/scored/uplifting/labeled_articles.jsonl
for dimensional regression training. Expected dimensions: 8 (agency, progress,
collective_benefit, connection, innovation, justice, resilience, wonder).
Use the dimensional regression QA criteria from
docs/guides/dimensional-regression-qa-agent.md"
```

Example for tech deployment filter:
```
Task: "Audit the tech deployment dataset at
datasets/scored/sustainability_tech_deployment/labeled_articles.jsonl
for dimensional regression training. Expected dimensions: 8
(deployment_maturity, technology_performance, cost_trajectory,
scale_of_deployment, market_penetration, technology_readiness,
supply_chain_maturity, proof_of_impact).
Use dimensional regression QA criteria from
docs/guides/dimensional-regression-qa-agent.md"
```

**Step 3: Review agent output**

Agent generates a report in `reports/{filter}_dimensional_regression_qa.md`

### What the Agent Validates

**CRITICAL CHECKS (Must Pass - Block Training):**

1. **Dimension Completeness**
   - All 8 dimensions present in every article
   - No missing dimension scores
   - Dimension names match filter specification

2. **Score Validity**
   - All dimension scores are numeric
   - All scores in valid 0-10 range
   - No null or invalid values

3. **Range Coverage**
   - Each dimension has examples across 0-10 spectrum
   - No "dead zones" (e.g., no examples in 7-10 range)
   - Sufficient variance for learning gradients

4. **Data Integrity**
   - All lines parse as valid JSON
   - No duplicate article IDs
   - No all-zero dimension scores (failed labeling)
   - All required fields present

**QUALITY CHECKS (Report But Don't Block):**

1. **Variance Analysis**
   - Standard deviation per dimension (target: > 1.0)
   - Score distribution shape (normal, skewed, bimodal)
   - Mean score per dimension

2. **Score Distribution**
   - Per-dimension histograms
   - Identify extreme clustering (>60% in one bucket)

3. **Cross-Dimension Correlation**
   - Informational only, not a problem
   - Real-world dimensions may be correlated

**INFORMATIONAL ONLY (Don't Flag as Issues):**

1. **Tier Labels**
   - Metadata only, not used in training
   - Tier-score misalignment is expected and OK

2. **Overall Score**
   - Metadata only, not training target
   - Calculation method doesn't matter

3. **Reasoning Fields**
   - For human interpretability only
   - Presence is optional

### Decision Criteria

**✅ PASS (Ready for Training):**
- All dimension scores present and valid (0-10)
- Full range coverage for each dimension
- Reasonable variance (std dev > 0.5)
- Clean data (no parse errors, duplicates)

**⚠️ REVIEW (Training Possible with Caveats):**
- Low variance in some dimensions (< 0.5 std dev)
- Missing coverage in some ranges (e.g., no 8-10 scores)
- Extreme clustering (>70% in one range)

**❌ FAIL (Block Training):**
- Missing dimensions in >1% of articles
- Scores outside 0-10 range
- >5% parse errors or duplicate IDs
- Complete missing coverage (no examples 0-5 or 5-10)

### Example Output

```markdown
## Executive Summary

✅ PASSED - Dataset ready for dimensional regression training

Dataset: datasets/scored/uplifting/labeled_articles.jsonl
Total articles: 7,715
Dimensions: 8
Critical checks: 4/4 PASSED

## Critical Checks Results

| Check | Status | Details |
|-------|--------|---------|
| Dimension completeness | ✅ | All 8 dimensions present |
| Score validity | ✅ | All scores 0-10 |
| Range coverage | ✅ | Full spectrum for each dimension |
| Data integrity | ✅ | 0 parse errors, 0 duplicates |

## Dimension Quality Statistics

| Dimension | Mean | Std Dev | Min | Max | Range Coverage |
|-----------|------|---------|-----|-----|----------------|
| agency    | 5.3  | 1.8     | 0   | 10  | 8/10 ranges    |
| progress  | 5.5  | 1.9     | 0   | 10  | 8/10 ranges    |
| ...       | ...  | ...     | ... | ... | ...            |

## Recommendations

✅ Ready for training - All critical checks passed
```

## Oracle Calibration Agent Workflow

### Purpose
Validate that your oracle (LLM labeler) is working correctly before running expensive batch scoring on thousands of articles.

### When to Use
- Before batch scoring with a new filter
- After changing the oracle prompt
- After modifying scoring dimensions or tier boundaries
- Periodic quality checks (quarterly)
- If you suspect oracle drift or quality issues

### How It Works
1. **Sample**: Extract ~200 random unlabeled articles
2. **Label**: Run oracle (Gemini Pro) on sample
3. **Analyze**: Check distributions, variance, reasoning quality, API reliability
4. **Decide**: Ready (proceed), Review (fix issues), or Block (don't label yet)

### How to Invoke

**Example for new filter:**
```
Task: "Calibrate the oracle for the uplifting filter before batch scoring.
Sample 200 articles from datasets/raw/unlabeled_articles.jsonl.
Use Gemini Pro for calibration (accurate validation before using Flash for production).
Filter directory: filters/uplifting/v1
Expected: 8 dimensions (agency, progress, collective_benefit, connection, innovation, justice, resilience, wonder)
Use the oracle calibration criteria from docs/agents/templates/oracle-calibration-agent.md"
```

**Example after prompt changes:**
```
Task: "Re-calibrate oracle for sustainability_tech_deployment after prompt revision.
Sample 200 new articles (different from previous calibration).
Compare results to previous calibration baseline.
Focus on: Has reasoning quality improved? Are tier distributions more accurate?"
```

### What the Agent Validates

**MUST PASS (Block if Failed):**
1. **API reliability** - 95%+ success rate
2. **Completeness** - All dimensions present with valid scores
3. **Variance** - Healthy std dev (>1.0) across dimensions
4. **Range coverage** - Full 0-10 spectrum represented

**QUALITY CHECKS (Review if Issues):**
5. **Reasoning quality** - Specific to articles, justifies scores
6. **Cost projection** - Affordable for full dataset

**INFORMATIONAL:**
7. **Cost estimate** - Projected cost for full batch with Flash
8. **Time estimate** - Projected time for full batch

### Example Output

**File:** `reports/uplifting_oracle_calibration.md` <!-- placeholder -->

```markdown
# Oracle Calibration Report: Uplifting

**Date:** 2025-11-13
**Oracle:** gemini-pro
**Sample Size:** 200 articles
**Status:** ✅ READY

## Executive Summary
Oracle is well-calibrated. Score distributions show healthy variance (std dev 1.5-2.1),
full range coverage across all dimensions, and reasoning quality is high.
Ready for batch scoring with Gemini Flash.

## Key Findings
- Success rate: 199/200 (99.5%)
- Dimensional variance: Healthy across all 8 dimensions (std dev 1.5-2.1)
- Range coverage: Full 0-10 spectrum represented
- Reasoning: Specific and justified (sampled 10/10 ✅)
- Projected cost (Flash): $0.85 for 10,000 articles
- Projected time: ~8 hours

## Recommendation
✅ Switch to Gemini Flash and proceed with full batch scoring.
```

### Decision Criteria

**✅ READY - Proceed with Batch Scoring**
- 95%+ success rate
- All dimensions valid (0-10)
- Healthy variance (std dev > 1.0)
- Range coverage (5+ out of 10 ranges per dimension)
- Reasoning quality good

→ **Action**: Switch to Gemini Flash, run batch scoring

**⚠️ REVIEW - Fixable Issues**
- Success rate 90-95%
- Low variance in 1-2 dimensions
- Reasoning generic but not wrong

→ **Action**: Review prompt, run 2nd calibration, proceed with caution

**❌ BLOCK - Do Not Proceed**
- Success rate < 90%
- Missing dimensions or invalid scores
- No variance (clustered scores)
- Reasoning contradicts scores

→ **Action**: Fix prompt/config, run new calibration

### Cost Comparison: Pro vs Flash

**Calibration (200 articles):**
- Gemini Pro: ~$0.20 (for accuracy validation)

**Production (10,000 articles):**
- Gemini Flash: ~$1.00 (10x cheaper than Pro)
- Gemini Pro: ~$10.00 (more accurate but expensive)

**Strategy:** Use Pro for calibration, Flash for production.

## Best Practices

### 1. Clear Task Descriptions

**Good:**
```
Task: "Audit the uplifting dataset at datasets/scored/uplifting/labeled_articles.jsonl
for dimensional regression training. Expected dimensions: 8 (agency, progress,
collective_benefit, connection, innovation, justice, resilience, wonder).
Use the dimensional regression QA criteria from
docs/guides/dimensional-regression-qa-agent.md"
```

**Bad:**
```
Task: "Check the uplifting data"  # Too vague
```

### 2. Reference Templates

Always reference specific templates or criteria:
- `Use dimensional regression QA criteria from docs/guides/dimensional-regression-qa-agent.md`
- `Follow the methodology in docs/methodology.md`

### 3. Specify Expected Output

Tell the agent what to produce:
- "Generate a report in reports/{filter}_qa.md"
- "Report: Pass/Fail status, statistics table, recommendations"

### 4. Provide Context

Give the agent necessary context:
- Filter name
- Number of dimensions
- Dimension names
- Dataset purpose (training, validation, test)

### 5. Review Agent Reports

- Read the full report generated by the agent
- Verify statistics make sense
- Check recommendations against project goals
- Don't blindly trust - validate critical findings

## Agent Workflow Examples

### Example 1: Dataset QA After Labeling

```
# User completes batch scoring
# User consolidates labels into labeled_articles.jsonl

# User invokes agent:
Task: "Audit the tech deployment dataset at
datasets/scored/sustainability_tech_deployment/labeled_articles.jsonl
for dimensional regression training. Expected dimensions: 8.
Use dimensional regression QA criteria."

# Agent validates dataset
# Agent generates report in reports/
# User reviews report
# User proceeds to training if PASSED
```

### Example 2: Quarterly Dataset Validation

```
# Scheduled quarterly validation

# User invokes agents for both filters:
Task 1: "Audit uplifting dataset using dimensional regression QA criteria"
Task 2: "Audit tech deployment dataset using dimensional regression QA criteria"

# Agents validate datasets in parallel
# User reviews both reports
# User identifies any data quality degradation
# User takes corrective action if needed
```

### Example 3: Pre-Training Validation

```
# User prepares training data
python scripts/prepare_training_data.py --filter filters/uplifting/v1 ...

# User validates training data before expensive training run:
Task: "Validate the training data in datasets/training/uplifting/
Verify: (1) train/val/test files exist, (2) no overlap between splits,
(3) stratification maintained tier proportions, (4) all examples have
8 dimension scores in 0-10 range"

# Agent validates training splits
# User proceeds to training if validated
```

## Creating New Agent Templates

When creating new agent templates:

### 1. Add YAML Frontmatter

Start the template with YAML frontmatter containing metadata:

```yaml
---
name: "Agent Name"
description: "What this agent does"
model: "sonnet"  # or "haiku" for quick tasks, "opus" for complex
trigger_keywords:
  - "keyword 1"
  - "keyword 2"
when_to_use: "When to invoke this agent"
focus: "What the agent focuses on"
output: "What the agent produces"
---
```

**Example:**
```yaml
---
name: "Dimensional Regression QA"
description: "Quality assurance for ground truth datasets"
model: "sonnet"
trigger_keywords:
  - "audit dataset"
  - "validate dataset"
  - "qa dataset"
when_to_use: "After consolidating labeled data, before training"
focus: "Dimensional score quality, not tier classification"
output: "Markdown report in reports/ with Pass/Review/Fail status"
---
```

### 2. Define Purpose Clearly

- What problem does this agent solve?
- When should users invoke this agent?
- What makes this agent different from others?

### 3. Specify Critical Checks

- What MUST pass for success?
- Separate critical vs quality vs informational
- Define clear pass/fail criteria

### 4. Provide Decision Criteria

- Pass/Review/Fail thresholds
- Clear recommendations for each outcome
- What to do if checks fail

### 5. Include Examples

- Show example usage
- Provide sample output format
- Include both good and bad scenarios

### 6. Document in This Guide

- Add section describing the new agent workflow
- Update "When to Use Agents" section
- Reference the new template in relevant workflows

## Architecture Decision Records (ADRs)

### When to Create ADRs

Create an ADR when making significant decisions that:
- Affect system architecture or design
- Choose between multiple viable approaches
- Make trade-offs with long-term implications
- Establish patterns or conventions
- Change or supersede previous decisions

**Examples of ADR-worthy decisions:**
- Choosing between classification vs regression for training
- Selecting a class imbalance mitigation strategy
- Deciding on content truncation for oracle-student consistency
- Establishing filter package structure
- Choosing tier boundaries and dimension weights

### ADR Creation Protocol

**Trigger:** During conversation, when a significant decision is made

**Agent action:**
1. Recognize the decision (architectural choice, trade-off, pattern establishment)
2. Offer to create ADR: "This seems like a significant decision. Should I create an ADR documenting it?"
3. If approved, create ADR in `docs/decisions/YYYY-MM-DD-title.md` <!-- placeholder -->
4. Update `docs/SESSION_STATE.md` <!-- placeholder --> to reference the new ADR

**ADR Template:**
```markdown
# [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Accepted | Superseded | Deprecated

## Context

[What was the situation? What problem were we solving?]
[What constraints or requirements influenced this decision?]

## Decision

[What did we decide to do? Be specific and actionable.]

## Consequences

### Positive
- [Good outcome or benefit]
- [Advantage gained]

### Negative
- [Trade-off or limitation]
- [Cost or disadvantage]

### Neutral
- [Other effects or implications]

## Alternatives Considered

- **[Alternative 1]:** [Description] - Rejected because [reason]
- **[Alternative 2]:** [Description] - Rejected because [reason]

## Implementation Notes

[How to apply this decision in practice]
[Links to relevant code, configs, or documentation]

## References

- [Link to related ADRs]
- [Link to relevant documentation]
- [Link to discussions or research]
```

### Example ADR

**File:** `docs/decisions/2025-11-09-dimensional-regression-training.md` <!-- placeholder -->

```markdown
# Use Dimensional Regression (Not Tier Classification) for Training

**Date:** 2025-11-09
**Status:** Accepted

## Context

Initial QA agents focused on tier classification accuracy, but this misaligned with the actual training objective. Training uses dimensional scores (8 scores per article, 0-10 range) as targets, not tier labels.

Tier labels are derived metadata based on weighted sums of dimensions, but:
- Oracle may use holistic assessment for tier assignment
- Tier boundaries in config.yaml are guidelines, not strict rules
- Training goal is to predict dimensional scores accurately, not tiers

## Decision

Train models on multi-dimensional regression (8 scores per article, 0-10 range) rather than tier classification.

**Training targets:**
- Input: [title + content]
- Output: [dim1_score, dim2_score, ..., dim8_score]
- Loss: MSE(predicted_scores, ground_truth_scores)

**Tier labels:** Metadata only, not used in training or evaluation.

## Consequences

### Positive
- Model learns fine-grained distinctions (not just 3-tier buckets)
- More flexible: Can derive any tier scheme from dimensional scores
- Better alignment with oracle labeling (dimensions are primary, tiers secondary)
- QA focuses on dimensional score quality, not tier accuracy

### Negative
- Cannot directly evaluate "tier classification accuracy"
- Requires explaining why tier mismatches are acceptable

### Neutral
- Evaluation metrics: MAE and RMSE per dimension (not accuracy/F1)
- Tier labels remain useful for stratified splitting and human interpretation

## Alternatives Considered

- **Multi-class classification (tier prediction):** Rejected because loses fine-grained information and doesn't match how oracle labels are structured
- **Ordinal regression:** Rejected because ties training to specific tier boundaries, reducing flexibility

## Implementation Notes

- Dataset QA uses dimensional regression criteria (see `docs/agents/templates/dimensional-regression-qa-agent.md`)
- Training format: `labels: [7, 8, 6, 5, 7, 4, 6, 5]` as array
- Tier labels present in labeled data but marked as "metadata only" in README files

## References

- `docs/agents/templates/dimensional-regression-qa-agent.md`
- `datasets/scored/uplifting/README.md` - Training Data Format section
- `datasets/scored/sustainability_tech_deployment/README.md` - Training Data Format section
```

### Maintaining ADRs

**When decisions change:**
1. Create new ADR with updated decision
2. Update old ADR status to "Superseded by [new ADR link]"
3. Update relevant documentation to reference new ADR

**When decisions are deprecated:**
1. Update ADR status to "Deprecated"
2. Add note explaining why (e.g., "No longer applicable after architecture change")

## Automated Documentation Updates

### Assistant Responsibilities

After making significant code changes or completing tasks, proactively offer to update documentation:

**Trigger points:**
- Completed a task or feature
- Made interface changes to major components
- Created or modified scripts
- Resolved a significant issue
- Session is wrapping up

**What to offer:**
```
"I've completed [task]. Should I update the documentation?
- docs/SESSION_STATE.md (current status, resolved issues)
- training/README.md (if training workflow changed)
- [Component docs] (if interfaces changed)"
```

### What Gets Updated Automatically

**1. docs/SESSION_STATE.md**
- Update "Current Status" section with latest progress
- Add to "Key Accomplishments This Session"
- Move completed issues to "Resolved Issues"
- Update "Files Modified This Session"
- Refresh "Next Steps"

**2. Component Documentation**
When creating/modifying major components:
- Create `docs/components/[component-name].md` if doesn't exist
- Update interface documentation when signatures change
- Note breaking changes or deprecations
- Update dependency lists

**3. README Files**
When affecting user workflows:
- Update usage examples if commands changed
- Refresh quickstart if setup changed
- Update file paths if structure changed

**4. Training/README.md**
When training pipeline changes:
- Update command examples
- Refresh architecture diagrams if applicable
- Update expected outputs

### Documentation Update Checklist

After completing work, verify:

- [ ] **docs/SESSION_STATE.md** - Current status reflects reality
- [ ] **Component docs** - Interfaces documented
- [ ] **ADRs** - Significant decisions recorded
- [ ] **README files** - User-facing docs updated
- [ ] **Agent templates** - New workflows documented

### Example Interaction

```
Assistant: "I've created the generic prepare_training_data.py script and removed
the old filter-specific scripts. Should I update the documentation?
- training/README.md (update command examples)
- docs/SESSION_STATE.md (add to accomplishments)
- Create ADR for generic script approach?"

User: "Yes, update all of those."
```

Assistant proceeds to update all three documents.

## Progressive Context Loading

### Principle

**Never dump entire files unless specifically asked.** Load context progressively from broad to specific, aiming for 10-20k tokens of relevant context.

### How to Load Context

**1. Start Broad (Always)**
- Read `docs/SESSION_STATE.md` <!-- placeholder --> - Current project status
- Read `docs/PROJECT_OVERVIEW.md` <!-- placeholder --> (if exists) - High-level understanding
- Scan `docs/ARCHITECTURE.md` (if exists) - System structure

**2. Navigate to Relevant Area**
- Use file structure to find relevant components
- Read directory README files first
- Use Grep to find specific patterns or keywords
- Check `docs/components/[component].md` for interface docs

**3. Load Specific Context Only**
- Read only the files/functions directly relevant to the query
- Use line offsets to read specific sections of large files
- Prefer component documentation over reading entire source files

**4. Synthesize Answer**
- Answer using multi-level understanding
- Reference specific file:line locations when helpful
- Suggest where to find more information if needed

### Example: "How does training data preparation work?"

**Bad approach (context overload):**
```
Read all scripts in scripts/
Read all documentation files
Read all training code
```

**Good approach (progressive disclosure):**
```
1. Read docs/SESSION_STATE.md → See training data section
2. Read training/README.md → Get overview
3. Read scripts/prepare_training_data.py:1-100 → Understand main logic
4. Synthesize answer with references
```

### Example: "Where is the uplifting filter defined?"

**Bad approach:**
```
Grep entire codebase for "uplifting"
Read all filter files
```

**Good approach:**
```
1. Check directory structure: filters/uplifting/v1/
2. Read filters/uplifting/v1/README.md → Get overview
3. Read filters/uplifting/v1/config.yaml → See configuration
4. Answer with specific file references
```

### When to Load More Context

Load additional context when:
- Initial answer is insufficient
- User asks follow-up questions
- Working on implementation (need full code)
- Debugging (need surrounding code)

### Benefits

- **Faster responses** - Less time reading files
- **Focused answers** - Only relevant information
- **Better UX** - Concise, targeted responses
- **Token efficiency** - Stay within context limits

## Troubleshooting

### Agent produces wrong results
- Review the prompt - was it clear enough?
- Check if agent had access to necessary files
- Verify agent used correct template/criteria
- Consider breaking task into smaller steps

### Agent takes too long
- Task may be too complex for single agent
- Break into smaller sequential tasks
- Use more specific file paths instead of broad searches

### Agent report unclear
- Update template with clearer output format
- Specify exact report structure in prompt
- Provide example output in template

### Documentation gets stale
- Set reminders to review docs/SESSION_STATE.md weekly
- After completing major milestones, update all relevant docs
- When creating new components, immediately document them
- Use ADRs to capture decision context while fresh

### Over-documentation
- Keep docs lean - focus on what's useful
- Archive old decisions to `docs/decisions/archive/`
- Delete truly temporary notes (sandbox is for that)
- Prefer concise summaries over exhaustive details

## Version History

### v1.1 (2025-11-12)
- Added ADR creation protocol and template
- Added automated documentation update guidelines
- Added progressive context loading strategy
- Added troubleshooting for documentation issues

### v1.0 (2025-11-12)
- Initial agent workflow guide
- Dimensional regression QA agent documented
- Best practices and examples added
- Decision criteria clarified
