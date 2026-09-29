# Agent Documentation

**Purpose:** This directory contains documentation for AI assistants working on this project.

**Portability:** This entire `docs/agents/` directory is designed to be portable - you can copy it to any project and AI assistants will understand how to work effectively.

---

## Core Documents

### AI_AUGMENTED_WORKFLOW.md
**For:** AI assistants (Claude Code, etc.)
**Purpose:** Defines philosophy, principles, and operational protocols
**When to read:** At the start of every session

**Contains:**
- Core philosophy (effortless docs, single source of truth, progressive disclosure)
- Session start protocol (what to read, how to orient the user)
- Proactive behaviors (when to create ADRs, update docs)
- Session end protocol (final updates, commit messages)
- Rules of engagement (always/never/when uncertain)

### agent-operations.md
**For:** AI assistants
**Purpose:** Detailed operational guide for agent workflows
**When to read:** When creating agents, ADRs, or doing complex tasks

**Contains:**
- Agent workflow (when to use agents, types, invocation)
- Dimensional regression QA agent (project-specific example)
- Creating new agent templates (YAML frontmatter, structure)
- Architecture Decision Records (ADR creation protocol)
- Automated documentation updates (what/when to update)
- Progressive context loading (how to efficiently load context)

---

## Filter Development Agents

### filter-development-guide.md
**For:** Filter developers
**Purpose:** End-to-end filter lifecycle guidance (9 phases: planning → deployment)
**When to use:** Starting new filters, reviewing production readiness, debugging validation issues

**9 Phases Covered:**
1. Planning - Define purpose, dimensions (design for independence!), tiers, gatekeepers
2. Architecture - Create harmonized prompt structure
3. Validation - Oracle calibration (50-100 articles) + **CRITICAL: Dimension redundancy analysis**
4. Prefilter - Test & optimize (avoid false negatives!)
5. Training Data - Score 5K+ articles, validate quality
6. Training - Knowledge distillation
7. Testing - Benchmark vs oracle
8. Documentation - Complete reports & README
9. Deployment - Production rollout

**Output:** Phase-specific guidance, checklists, validation criteria, common pitfalls

**Usage:**
```
Use the filter-development-guide agent to start a new filter from scratch
Use the filter-development-guide agent to review existing filter for production readiness
```

---

## templates/

Reusable templates for agent tasks:

### ADR-TEMPLATE.md
Template for Architecture Decision Records. Copy this when documenting significant technical decisions.

### dimensional-regression-qa-agent.md (if exists)
**Purpose:** Dataset quality assurance for dimensional regression training
**When:** After consolidating labeled data, before training
**Output:** QA report with Pass/Review/Fail status

### oracle-calibration-agent.md (if exists)
**Purpose:** Validate oracle performance before large-scale batch scoring
**When:** Before labeling thousands of articles, after prompt changes, periodic quality checks
**Output:** Calibration report with Ready/Review/Block recommendation

**Note:** Some templates may be in planning - check directory for current availability.

---

## How to Use This Directory

### For AI Assistants

**At session start:**
1. Read `AI_AUGMENTED_WORKFLOW.md` - Get the operating system
2. Read project's `docs/SESSION_STATE.md` <!-- placeholder --> - Understand current status
3. Orient the user

**During work:**
- Follow proactive behaviors (offer ADRs, update docs)
- Use progressive context loading
- Reference `agent-operations.md` for detailed workflows

**At session end:**
- Update project's `docs/SESSION_STATE.md` <!-- placeholder -->
- Suggest commit message
- Summarize progress

### For Humans (Copying to New Project)

**To use in a new project:**
1. Copy entire `docs/agents/` directory to new project
2. Update `AI_AUGMENTED_WORKFLOW.md` "Project-Specific Context" section:
   - Key concepts
   - Directory structure
   - Important files
   - Common tasks
3. Create project's `docs/SESSION_STATE.md` <!-- placeholder -->
4. AI assistants now know how to work!

**What to customize:**
- Project-specific context in `AI_AUGMENTED_WORKFLOW.md`
- Agent templates in `templates/` (add project-specific agents)
- Keep core philosophy and protocols unchanged

---

## Version History

### v1.3 (2025-11-22)
- **CRITICAL UPDATE:** Added dimension redundancy analysis to Phase 3 (Validation)
- **Impact:** Can save 50-75% of training time by detecting redundant dimensions early
- **Added:** Step 9 in Phase 3 - Dimension redundancy analysis with PCA/correlation
- **Updated:** Validation criteria to include redundancy thresholds (must be < 50%, PC1 < 85%)
- **Updated:** Phase 1 planning guidance to emphasize dimension independence
- **Analysis tool:** `scripts/analysis/analyze_oracle_dimension_redundancy.py`
- **Reason:** Post-hoc analysis revealed 62-87% dimension redundancy in all three v4 models - would have been detectable before training!

### v1.2 (2025-11-17)
- **Removed:** filter-harmonizer.md (redundant - filter-development-guide covers all harmonization checks in Phase 2)
- **Reason:** Development guide is more comprehensive and caught critical issues harmonizer missed

### v1.1 (2025-11-17)
- **Added:** Filter Development Agents section
- **Added:** filter-development-guide.md (9-phase lifecycle guidance)
- **Added:** filter-harmonizer.md (automated consistency checking - later removed in v1.2)
- **Added:** Supporting documents (FILTER_HARMONIZATION_GUIDE.md, FILTER_CHECKLIST.md)
- **Updated:** Templates section to reflect current availability

### v1.0 (2025-11-12)
- Initial agent documentation structure
- Portable design for reuse across projects
- Core philosophy: effortless docs, single source of truth, progressive disclosure
- Session protocols for AI assistants
- Agent templates with YAML frontmatter
