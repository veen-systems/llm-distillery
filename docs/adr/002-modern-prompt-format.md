# ADR 002: Modern Prompt Format Support

**Date**: 2025-11-23  
**Status**: Accepted  
**Context**: sustainability_technology v1 development

## Decision

Support **modern prompt format** in batch_scorer.py that uses entire file as-is without requiring `## PROMPT TEMPLATE` wrapper sections. This becomes the **recommended format** for new filters.

## Context

The legacy prompt format required:
1. `## PROMPT TEMPLATE` section wrapper
2. Placeholders: `{title}`, `{source}`, `{published_date}`, `{text}`
3. Python `.format()` method to inject article data

This caused issues when:
- Prompts contained JSON examples with curly braces (broke `.format()`)
- Custom frameworks (LCSA) needed different structure
- Prompt files became cluttered with wrapper sections

## Solution

batch_scorer.py now auto-detects two formats:

### Modern Format (Recommended)
```markdown
# LCSA Framework: Sustainability Technology...

**INPUT DATA:** [Paste the summary of the article here]

## 1. Score Dimensions (0.0-10.0 Scale)
...

```json
{
  "technology_readiness_level": {...}
}
```
```

- Uses entire file as-is
- Placeholder: `**INPUT DATA:** [Paste the summary of the article here]`
- batch_scorer replaces placeholder with article summary
- Supports JSON examples, tables, any custom structure

### Legacy Format (Backward Compatible)
```markdown
## PROMPT TEMPLATE

```
Title: {title}
Source: {source}
Published: {published_date}

{text}
```
...
```

- Requires `## PROMPT TEMPLATE` section
- Uses `.format()` placeholders
- Maintained for existing filters

## Implementation

**batch_scorer.py:344-351** - Detect format and set flag:
```python
if prompt_section_marker in content:
    self.is_modern_format = False  # Legacy
else:
    self.is_modern_format = True   # Modern
```

**batch_scorer.py:528-547** - Build prompt based on format:
```python
if self.is_modern_format:
    # Replace placeholder with article summary
    return self.prompt_template.replace(
        '[Paste the summary of the article here]',
        article_summary
    )
else:
    # Use .format() with placeholders
    return self.prompt_template.format(...)
```

## Benefits

1. **Cleaner prompts** - No wrapper sections needed
2. **JSON examples supported** - Curly braces don't break formatting
3. **Flexible structure** - LCSA, tables, any custom format
4. **Backward compatible** - Legacy format still works
5. **Auto-detection** - No configuration needed

## Consequences

### Positive
- Enables rich prompt formats (LCSA framework, tables, examples)
- Reduces boilerplate in prompt files
- Fixes JSON example bug
- Default for new filters going forward

### Negative
- Two formats to maintain (minimized by auto-detection)
- Need to update documentation

## Migration

**New filters**: Use modern format by default  
**Existing filters**: Keep legacy format (no need to migrate)

## References

- Implementation: `ground_truth/batch_scorer.py:344-547`
- Example modern format: `filters/sustainability_technology/v1/prompt-compressed.md` <!-- placeholder -->
- Example legacy format: `filters/uplifting/v4/prompt-compressed.md`
- Updated guide: `docs/agents/filter-development-guide.md:173-215`
