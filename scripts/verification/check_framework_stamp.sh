#!/usr/bin/env bash
# Is the framework stamp in CLAUDE.md corroborated by the INSTALLED skills?
#
# Mechanizes the hand-dated sentence that used to sit in `CLAUDE.md`'s footer —
# "the FOUR user-global skills were byte-identical to the vX.Y.Z reference
# install, 0 differing lines, when enumerated <date>". That claim is about files
# OUTSIDE this repo, so no commit here can hold it still: it was written on
# 2026-09-11 and was false by 2026-09-17, upstream having moved six releases and
# the installed copies with it. A sentence that decays silently in an
# always-loaded file is what this script exists to replace.
#
# Adopted from `ducroq/agent-ready-projects` v1.43.0 (THAT repo's #136 — this repo's
# #136 is the commit-msg deploy guard, an unrelated issue), whose `curate`
# Step 0 ships the same probe inline. THREE deliberate differences:
#   1. It checks the FOUR skills installed here; upstream's `want` list has
#      three and omits `review-changes`, which v1.40.0 moved into the global
#      set. Three of four passing is the shape this repo keeps shipping.
#   2. `FRAMEWORK` defaults to the clone this estate actually uses, so the
#      probe runs with no environment set up. An explicit `FRAMEWORK=` wins.
#   3. It compares BYTES (`cmp`), not diff lines, so the success line means
#      what it says.
#
# ⚠️ UPSTREAM'S COPY STILL RUNS AND IS NOT THIS ONE. `/curate` Step 0 executes
# its own inline `stampcheck()` over THREE skills; it will keep doing so, and it
# skips `review-changes`. A green curate does not mean this script passed.
# ⚠️ NOT the same check as `check_doc_claims.py`'s identically-named
# `check_framework_stamp()`, which asks only whether CLAUDE.md's frontmatter and
# footer agree with EACH OTHER — a much weaker question, and the one that is
# already wired into `memory/MEMORY.md`.
#
# ⛔ THE VERSION IS DERIVED FROM THE STAMP, NEVER HARDCODED. A probe pinned to
# a literal tag has the lifetime of that tag, not of the claim — it expires at
# the exact moment it has something to report. Bumping the stamp re-arms this.
#
# ⚠️ UNDECIDED IS NOT A PASS. Three outcomes, carried by EXIT STATUS, never by
# a word in the output: 0 verified, 1 drift, 2 could not decide. The success
# line is gated on a COUNT of what was actually compared, so a skipped skill
# cannot leave the "byte-identical" line standing beside its own failure, and
# the count is DERIVED from `WANT` rather than restated — a hand-maintained
# second copy of it reproduces upstream's original false PASS exactly.
#
# Usage:  bash scripts/verification/check_framework_stamp.sh
#         FRAMEWORK=/path/to/agent-ready-projects bash scripts/.../check_framework_stamp.sh
#         CLAUDE_SKILLS=/path/to/skills   # where the installed SKILL.md files live

set -u

WANT="audit-context curate update-drift review-changes"
# DERIVED, never written down: a hand-kept second copy of this number reproduces
# upstream's original false PASS the moment the two disagree.
# ⚠️ `$(( ))`-wrapped because BSD/macOS `wc` pads its output with spaces, and the
# comparisons below are STRING equality — unpadded it reads `4`, padded `       4`,
# and every run on such a host would report "compared 4 of        4", exit 2.
N_WANT=$(( $(printf '%s\n' $WANT | wc -l) ))

R=$(git rev-parse --show-toplevel 2>/dev/null) ||
  { echo "CANNOT VERIFY: not in a git repo"; exit 2; }

# ⚠️ `$HOME` unset is an ENVIRONMENT problem, not drift. Under `set -u` a bare
# `$HOME` aborts the script, and an abort exits 1 — which this contract reads as
# "the skills have drifted". A cron, container or `env -i` caller would get a
# confident wrong verdict, so the undecidable case is made explicit.
if [ -z "${FRAMEWORK:-}" ] || [ -z "${CLAUDE_SKILLS:-}" ]; then
  [ -n "${HOME:-}" ] ||
    { echo "CANNOT VERIFY: HOME is unset and FRAMEWORK/CLAUDE_SKILLS were not given"; exit 2; }
fi
FRAMEWORK=${FRAMEWORK:-$HOME/repos/agent-ready-projects}
SKILLS=${CLAUDE_SKILLS:-$HOME/.claude/skills}

# ⚠️ NOT `[ -d "$FRAMEWORK/.git" ]`. In a worktree or a submodule checkout `.git` is a
# FILE, so the directory test rejects a perfectly usable clone — and the message it
# prints is in this suite's skip list, so such a machine reports green-with-a-skip
# while the probe is permanently undecidable.
git -C "$FRAMEWORK" rev-parse --git-dir >/dev/null 2>&1 ||
  { echo "CANNOT VERIFY: FRAMEWORK ($FRAMEWORK) is not a git clone"; exit 2; }
[ -f "$R/CLAUDE.md" ] ||
  { echo "CANNOT VERIFY: no CLAUDE.md at $R"; exit 2; }
# Separate "unreadable" from "no stamp in it" — `grep`'s own failure is swallowed
# by the `2>/dev/null` below, so without this the diagnosis is confidently wrong.
[ -r "$R/CLAUDE.md" ] ||
  { echo "CANNOT VERIFY: $R/CLAUDE.md is not readable"; exit 2; }

# ⛔ THE FRONTMATTER KEY IS AUTHORITY; the scan only CORROBORATES it.
# `head -1` took whatever appeared earliest in the file, so a provenance line
# ("adopted from agent-ready-projects v1.40.0") above the stamp won and the probe
# verified a tag nobody pinned — measured, with a confident PASS naming it.
# ⚠️ Unanimity over the scan is NOT sufficient on its own, and a round-2 review
# proved it: the scan's `[^0-9]{0,40}` bound SILENTLY DROPS a stamp worded more
# loosely than 40 characters, and the stale provenance line then wins uncontested
# and unanimously. A missed stamp does not stay undecidable, it becomes invisible.
# So: take the anchored key, and treat any OTHER version the scan finds as a
# disagreement. If there is no anchored key, fall back to unanimity over the scan
# — weaker, and the comment above says exactly how.
# ⚠️ A 4-component version (`v1.45.1.2`) truncates to its first three and is
# verified as that; no upstream tag has ever had a fourth component.
KEY=$(grep -oE "^framework:[[:space:]]+agent-ready-projects[[:space:]]+v?[0-9]+\.[0-9]+\.[0-9]+" \
        "$R/CLAUDE.md" 2>/dev/null | head -1 |
      grep -oE "v?[0-9]+\.[0-9]+\.[0-9]+$" | sed "s/^v*/v/")
ALL=$(grep -oE "agent-ready-projects[^0-9]{0,40}v?[0-9]+\.[0-9]+\.[0-9]+" \
        "$R/CLAUDE.md" 2>/dev/null |
      grep -oE "v?[0-9]+\.[0-9]+\.[0-9]+$" | sed "s/^v*/v/" | sort -u)
if [ -n "$KEY" ]; then
  P=$KEY
  # ⛔ CENSUS RESULT (round 2 trigger: the same class twice → enumerate, don't re-review).
  # The class is "a command's FAILURE read as a VALUE". Both `grep` extractions above are
  # the last live instance: `2>/dev/null` makes a grep that FAILED indistinguishable from
  # one that matched nothing, and an empty `ALL` in this branch would mean the
  # corroboration silently never ran — a check that reports nothing wrong having checked
  # nothing. The KEY pattern is a strict subset of the ALL pattern (the frontmatter line
  # puts 2 non-digit chars between the repo name and the version, well inside the 40-char
  # bound), so KEY non-empty and ALL empty is IMPOSSIBLE unless the scan itself failed.
  [ -n "$ALL" ] ||
    { echo "CANNOT VERIFY: the stamp scan returned nothing while the key matched $KEY"; exit 2; }
  for v in $ALL; do
    [ "$v" = "$P" ] && continue
    echo "CANNOT VERIFY: CLAUDE.md's stamp is $P but it also names $v"
    exit 2
  done
else
  [ -n "$ALL" ] || { echo "CANNOT VERIFY: no framework stamp in CLAUDE.md"; exit 2; }
  if [ "$(printf '%s\n' "$ALL" | wc -l)" -ne 1 ]; then
    echo "CANNOT VERIFY: CLAUDE.md names more than one framework version: $(printf '%s ' $ALL)"
    exit 2
  fi
  P=$ALL
fi

echo "stamp: $P   framework: $FRAMEWORK   skills: $SKILLS"

# ⛔ Separate "tag absent" from "file absent at that tag". `git show TAG:path`
# fails for both, and the message naming only the first sends the reader to
# `git fetch`, which cannot fix a skill upstream renamed or had not yet moved
# into the global set.
git -C "$FRAMEWORK" rev-parse -q --verify "$P^{commit}" >/dev/null ||
  { echo "CANNOT VERIFY: $P is not in the framework clone — fetch tags"; exit 2; }

TMP=$(mktemp) || { echo "CANNOT VERIFY: cannot create a temp file"; exit 2; }
trap 'rm -f "$TMP"' EXIT

n=0
d=0
for s in $WANT; do
  i="$SKILLS/$s/SKILL.md"
  [ -f "$i" ] || { echo "CANNOT VERIFY: $s is not installed at $i"; continue; }
  # ⚠️ SPLIT the pipeline, and REDIRECT rather than capture. Piped, a `git show`
  # that fails — the normal state right after an upstream release, stamp bumped
  # and clone not fetched — is swallowed and the comparison supplies the verdict.
  # `$(...)` additionally strips ALL trailing newlines, so a file differing only
  # at EOF compared equal (or, restored with `printf`, unequal): either way the
  # word "byte-identical" was not what was measured.
  git -C "$FRAMEWORK" show "$P:.claude/skills/$s/SKILL.md" > "$TMP" 2>/dev/null ||
    { echo "CANNOT VERIFY: $P has no .claude/skills/$s/SKILL.md — not a fetch problem"; exit 2; }
  # ⛔ `cmp`'s STATUS, not a line count. `diff | grep -c '^[<>]'` reads ANY diff
  # failure — an unreadable file, an I/O error — as zero differing lines and
  # therefore as identical: a false PASS with the failure on stderr beside it.
  # 0 same · 1 differ · >1 trouble, and trouble is undecidable.
  cmp -s "$TMP" "$i"
  rc=$?
  if [ "$rc" -eq 1 ]; then
    # ⚠️ The line COUNT is decoration; `cmp` above has already decided. It is
    # computed defensively anyway, because a round-2 review found the condemned
    # `diff | grep -c` form reintroduced right here, six lines under the comment
    # condemning it: a NUL byte in the installed file makes `diff` say "Binary
    # files differ" and the count print a self-contradicting `by 0 lines`.
    nl=$(diff "$TMP" "$i" 2>/dev/null | grep -c '^[<>]') || nl=0
    if [ "$nl" -gt 0 ]; then
      echo "DRIFT: $s differs from $P by $nl lines"
    else
      echo "DRIFT: $s differs from $P (binary, or diff unavailable)"
    fi
    d=1
  elif [ "$rc" -ne 0 ]; then
    echo "CANNOT VERIFY: cannot compare $i (cmp exit $rc)"
    exit 2
  fi
  n=$((n + 1))
done

# Printed BEFORE the drift gate: a run that skipped a skill has a hole in it
# whatever else it found, and exiting 1 without saying so told the reader the
# comparison was complete.
[ "$n" = "$N_WANT" ] || echo "CANNOT VERIFY: compared $n of $N_WANT skills"
# Drift is DECIDABLE even with a hole — one differing skill refutes the claim.
[ "$d" = 0 ] || exit 1
[ "$n" = "$N_WANT" ] || exit 2
echo "$n global skills byte-identical to $P"
