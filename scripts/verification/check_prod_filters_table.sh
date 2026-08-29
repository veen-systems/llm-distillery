#!/usr/bin/env bash
# Reconcile memory/filter-status.md's production table against CLAUDE.md's
# Production Filters table. Every filter listed in CLAUDE.md must have a
# same-version row in filter-status.md.
#
# Prints PASS or FAIL on its own first line (plus the offending rows on FAIL),
# and may add a trailing `NOTE:` block naming rows it could not parse as a filter
# claim. ⚠️ No line may BEGIN with FAIL or CANNOT VERIFY unless it is the verdict:
# run_verify_annotations.py classifies on line-initial verdict words.
#
# WHY THIS IS A SCRIPT AND NOT AN INLINE `<!-- verify: -->` COMMENT.
# It used to be inline, and it broke in the way the framework's curate skill
# warns about: the command greps for the literal string `<!-- prod-filters-
# table:start -->`, which CONTAINS `-->`. An HTML comment ends at its first
# `-->`, so the comment terminated mid-command. The remainder was left rendering
# as visible prose in the middle of a paragraph, and the check silently stopped
# being one command. Found 2026-08-11 by running every verify comment in
# memory/ rather than by reading the file.
#
# Rule this encodes: a verify command that must mention `-->` cannot live in an
# HTML comment. Put it in a file and call the file.
#
# Usage:  bash scripts/verification/check_prod_filters_table.sh
set -uo pipefail

cd "$(dirname "$0")/../.." || exit 1

STATUS=memory/filter-status.md
PROJECT=CLAUDE.md

START='<!-- prod-filters-table:start -->'
END='<!-- prod-filters-table:end -->'

# Anchors must exist, or the awk ranges below silently match nothing and the
# comparison passes by having compared two empty sets.
if ! grep -qxF "$START" "$STATUS" \
  || ! grep -qxF "$END" "$STATUS" \
  || ! grep -q '^## Key Decisions' "$PROJECT"; then
    echo "FAIL: verify anchors missing"
    exit 1
fi

# Filters CLAUDE.md claims are in production. `thriving` is PARKED (ADR-015) and
# `ai_engineering_practice` is a separate product, so neither needs a row here.
claimed=$(awk '/^## Production Filters/,/^## Key Decisions/' "$PROJECT" \
    | grep -E "^\| \*\*" \
    | sed -nE 's/^\| \*\*([a-z_-]+)\*\* \| (v[0-9]+).*/\1 \2/p' \
    | tr '-' '_' \
    | grep -Ev "^(thriving|ai_engineering_practice) " \
    | LC_ALL=C sort -u)

documented=$(awk "/prod-filters-table:start/,/prod-filters-table:end/" "$STATUS" \
    | grep -E "^\| \**[a-z]" \
    | awk -F'|' '{gsub(/\*\*/,"",$2); sub(/^[ \t]+/,"",$2); sub(/[ \t].*$/,"",$2);
                   gsub(/ /,"",$3); print $2, $3}' \
    | tr '-' '_' \
    | LC_ALL=C sort -u)

# Rows in CLAUDE.md's table that the extractor could not parse. Reported, never
# silently dropped: a future filter row in an unexpected shape would otherwise
# leave the checked set with no trace. The REMOVED sustainability_technology /
# foresight row is the one expected member. Its name cell carries TWO bolded filter
# names with inline versions, which is what the extractor cannot parse; the em-dash
# version cell is independently sufficient but is not the operative cause (measured
# both ways -- restoring a `v3` version cell leaves the row unparsed).
unparsed=$(awk '/^## Production Filters/,/^## Key Decisions/' "$PROJECT" \
    | grep -E "^\| \*\*" \
    | grep -vE "^\| \*\*[a-z_-]+\*\* \| v[0-9]+" \
    | sed -E 's/^\| ([^|]*)\|.*/\1/' | sed -E 's/[[:space:]]+$//')

missing=$(LC_ALL=C comm -23 <(printf '%s\n' "$claimed") <(printf '%s\n' "$documented") | grep . || true)

if [ -n "$missing" ]; then
    echo "FAIL: in CLAUDE.md's Production Filters table but missing here:"
    printf '%s\n' "$missing"
    exit 1
else
    echo PASS
fi

if [ -n "$unparsed" ]; then
    echo "NOTE: rows not parsed as a filter claim (not checked):"
    printf '%s\n' "$unparsed" | sed 's/^/  /' 
fi
