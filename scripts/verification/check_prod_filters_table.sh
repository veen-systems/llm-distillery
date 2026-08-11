#!/usr/bin/env bash
# Reconcile memory/filter-status.md's production table against CLAUDE.md's
# Production Filters table. Every filter listed in CLAUDE.md must have a
# same-version row in filter-status.md.
#
# Prints exactly one word: PASS or FAIL (plus the offending rows on FAIL).
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
    exit 0
fi

# Filters CLAUDE.md claims are in production. `thriving` is PARKED (ADR-015) and
# `ai_engineering_practice` is a separate product, so neither needs a row here.
claimed=$(awk '/^## Production Filters/,/^## Key Decisions/' "$PROJECT" \
    | grep -E "^\| \*\*" \
    | sed -E 's/^\| \*\*([a-z_-]+)\*\* \| (v[0-9]+).*/\1 \2/' \
    | tr '-' '_' \
    | grep -Ev "^(thriving|ai_engineering_practice) " \
    | sort -u)

documented=$(awk "/prod-filters-table:start/,/prod-filters-table:end/" "$STATUS" \
    | grep -E "^\| [a-z]" \
    | awk -F'|' '{gsub(/ /,"",$2); gsub(/ /,"",$3); print $2, $3}' \
    | tr '-' '_' \
    | sort -u)

missing=$(comm -23 <(printf '%s\n' "$claimed") <(printf '%s\n' "$documented") | grep . || true)

if [ -n "$missing" ]; then
    echo "FAIL: in CLAUDE.md's Production Filters table but missing here:"
    printf '%s\n' "$missing"
else
    echo PASS
fi
