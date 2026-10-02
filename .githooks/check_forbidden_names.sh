#!/bin/bash
# Block names the owner forbids in this PUBLIC repo (owner ruling 2026-10-02: the external curator is never named).
#
# The patterns live in a GITIGNORED local file, config/credentials/forbidden_names.txt (one case-insensitive fixed
# string per line, # comments allowed), so the forbidden name itself never lands in the repo.
#
#   check_forbidden_names.sh            checks the STAGED diff (added lines) and staged file paths  [pre-commit]
#   check_forbidden_names.sh --msg F    checks a commit message file                                [commit-msg]
#
# No denylist file (another clone, CI): prints a note and passes. Escape hatch: git commit --no-verify.
set -uo pipefail
ROOT=$(git rev-parse --show-toplevel)
LIST="$ROOT/config/credentials/forbidden_names.txt"
if [ ! -f "$LIST" ]; then
  echo "note: no $LIST; forbidden-name check skipped" >&2
  exit 0
fi
mapfile -t PATS < <(grep -vE '^\s*(#|$)' "$LIST")
[ "${#PATS[@]}" -gt 0 ] || { echo "note: $LIST is empty; forbidden-name check skipped" >&2; exit 0; }
ARGS=(); for p in "${PATS[@]}"; do ARGS+=(-e "$p"); done
if [ "${1:-}" = "--msg" ]; then
  if grep -n -i -F "${ARGS[@]}" "$2" >&2; then
    echo "BLOCKED: the commit message contains a forbidden name (patterns in $LIST)." >&2
    exit 1
  fi
  exit 0
fi
HITS=$( { git diff --cached -U0 --no-color | grep -E '^\+' | grep -v -E '^\+\+\+ ' ; git diff --cached --name-only; } \
        | grep -n -i -F "${ARGS[@]}" )
if [ -n "$HITS" ]; then
  echo "$HITS" | cut -c1-200 >&2
  echo "BLOCKED: staged changes contain a forbidden name (patterns in $LIST). Redact it, or --no-verify if you must." >&2
  exit 1
fi
exit 0
