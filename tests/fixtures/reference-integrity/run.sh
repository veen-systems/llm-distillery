#!/usr/bin/env bash
# Sensitivity test for refcheck.py. Run BEFORE and AFTER any edit to it.
#
# A run that finds nothing cannot distinguish a fixed check from a disabled one
# (/audit-context step 4). So this seeds the failures each loosening newly
# PERMITS, not the ones it was designed to preserve.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
out="$(SEED="$here/SEED.md" python3 "$here/refcheck.py" 2>&1)"
findings="$(sed -n '/### FINDINGS/,/### RESOLVED/p' <<<"$out")"
fail=0
must_catch=(totally_made_up_thing.py no_such_module.py no_such_file_xyz.md
            feedback-does-not-exist-at-all.md absent_thing.py
            no_such_template.md)          # 11: frontmatter scope must still check
must_be_silent=(config.yaml NexusMind/scripts/main.py
                feedback-claim-requires-verify.md gate/ground_truth_gate.py
                filters/foresight/v1/config.yaml
                templates/release.md)     # 12: the absorption the change permits
# v1.23.0 #45 — the failures the placeholder skip NEWLY permits.
must_catch+=(absorbed_by_distance.py                  # 19 non-adjacent marker
             deploy_filters.sh                        # 20 stale marker, cross-repo (rung 4)
             verify_filter_package.py                 # 13 stale marker, explicit
             test_normalization_invariant.py          # 14 stale marker, angle-bracket
             never_existed_alongside.py)              # 16 unmarked break on a marked line
must_be_placeheld=("filters/<name>/<version>/config.yaml"   # 17 counted, not dropped
                   nexusmind-scorer.service)                # 18
# 2026-08-15 — the failures the SELF-PREFIX STRIP newly permits. The strip can only
# ever turn a report into a resolution, so both new catches are the laundering cases.
must_catch+=(no_such_self_thing.sh                           # 22 fabricated behind self-prefix
             "llm-distillery/model/adapter_model.safetensors") # 23 collision must survive the strip
must_be_silent+=(llm-distillery/scripts/remote_deploy.sh)    # 21 must now resolve
# 2026-08-15 — the failure the SYSTEMD UNIT class newly permits: a unit that exists
# nowhere in the estate must not be absorbed by the class.
must_catch+=(totally-made-up-unit.service)                   # 24
# 2026-08-27 — the v1.28.0/v1.26.1 back-port. Three of the four are LOOSENINGS, so
# these seed the FALSE RESOLUTION each newly permits, not the case it was built for.
must_catch+=(no_such_doc_relative_file.md   # 26 rung1b must not launder a real break
             no_such_link_target.md)        # 27 a broken link URL is now CHECKED
must_be_placeheld+=("fixtures/reference-integrity/run.sh")  # 31 #56: rung2 no longer
                                            #    adjudicates intent, so this is COUNTED
must_be_silent+=(no_such_struck_target.md)  # 30 struck LINK is an absence assertion
must_catch+=(project_session_1999_01_01.md) # 33 rung5 extension must not launder
# 2026-09-17 — rung 3 excluded from the STALE `resolves` test. 34 is what the
# loosening newly permits (a state-dir angle path may now be counted rather than
# reported); 35 is the laundering case it must NOT permit, caught by rung 1, which
# is tested first in the same expression.
must_be_placeheld+=("data/raw/.processed_ids_<seedname>.json")           # 34
must_catch+=("datasets/scored/<solutions_v6_rescored.jsonl>")            # 35
for p in "${must_catch[@]}"; do
  grep -q -- "$p" <<<"$findings" && echo "  ok    caught  $p" \
    || { echo "  FAIL  missed  $p"; fail=1; }
done
# Assert POSITIVELY. Absence from FINDINGS cannot distinguish "resolved correctly"
# from "silently dropped" -- with the skip made unconditional, 4 of 6 still printed
# "ok silent" (2026-08-12 review). Each must appear in a resolution section.
# Everything after FINDINGS: RESOLVED, GENERIC, DECLARED-PLACEHOLDER and
# ASSERTED-ABSENT are all legitimate non-finding dispositions. What must never
# happen is a path appearing in NONE of them.
resolved_secs="$(sed -n '/### RESOLVED/,$p' <<<"$out")"
for p in "${must_be_silent[@]}"; do
  if grep -q -- "$p" <<<"$findings"; then echo "  FAIL  reported $p"; fail=1
  elif grep -q -- "$p" <<<"$resolved_secs"; then echo "  ok    resolved $p"
  else echo "  FAIL  neither reported NOR resolved (silently dropped?): $p"; fail=1; fi
done
placeheld="$(sed -n '/### SKIPPED AS DECLARED-PLACEHOLDER/,/### SKIPPED AS ASSERTED/p' <<<"$out")"
for p in "${must_be_placeheld[@]}"; do
  grep -q -- "$p" <<<"$placeheld" && echo "  ok    counted $p" \
    || { echo "  FAIL  not in counted skip section: $p"; fail=1; }
done
# 36/37 (#122, ported 2026-09-17) — the shape section must NAME what it skipped.
# Asserted on the section and the LABEL, not on absence from FINDINGS: absence is
# exactly what the defect looked like for the whole life of the fork.
shapes="$(sed -n '/### PATH SHAPES NOT EXTRACTED/,/### EXTENSIONS/p' <<<"$out")"
grep -q "filters/{seedname}/v{N}/never_extracted.py .*brace group" <<<"$shapes" \
  && echo "  ok    named   brace-group shape (labelled, not dropped)" \
  || { echo "  FAIL  brace-group shape not named in its section"; fail=1; }
grep -q 'C:\\dev\\seed_notes.md .*Windows path' <<<"$shapes" \
  && echo "  ok    named   Windows-path shape (labelled, not dropped)" \
  || { echo "  FAIL  Windows-path shape not named in its section"; fail=1; }
grep -q "seed_notes.md" <<<"$findings" \
  && { echo "  FAIL  a NOT-EXTRACTED shape leaked into FINDINGS"; fail=1; } \
  || echo "  ok    shapes are not findings (deliberate)"
grep -q "COVERS NO PATH" <<<"$findings" && echo "  ok    caught  marker-covering-no-path" \
  || { echo "  FAIL  missed  marker-covering-no-path"; fail=1; }
# --- back-port assertions that need an exact SECTION, not mere absence ---
# 25: rung 1b must actually FIRE. Asserted on the rung label rather than through
# must_be_silent: the seed path shares its name with the seed DOCUMENT, so a bare
# grep would match every output line and pass vacuously.
grep -q '\[rung1b\] ->' <<<"$resolved_secs" && echo "  ok    fired   rung1b (doc-relative)" \
  || { echo "  FAIL  rung1b never fired"; fail=1; }
# 29: a declined URL must be NAMED with its reason. Masking a label is a silent loss
# unless this holds -- absence from FINDINGS would be satisfied by never extracting it.
grep -q 'example.invalid.*external URL' <<<"$out" && echo "  ok    declined external URL (named, not dropped)" \
  || { echo "  FAIL  declined URL not reported with a reason"; fail=1; }
# 32: identifier-shaped token counted, never silently dropped.
grep -q 'DROPPED AS IDENTIFIER-SHAPED (1 unique)' <<<"$out" && echo "  ok    counted process.env as identifier" \
  || { echo "  FAIL  process.env not counted in the identifier section"; fail=1; }
# 28: THE ACCEPTED LOSS, asserted so it stays deliberate. A broken path appearing only
# as a link LABEL is no longer reported -- the label is presentation. If this ever
# starts failing, the masking has been widened past the label span.
grep -q 'no_such_label_path.md' <<<"$findings" \
  && { echo "  FAIL  label extracted as a reference (masking broken)"; fail=1; } \
  || echo "  ok    label not extracted (accepted loss, deliberate)"
# 2026-09-17 (#134 step 2) — THE ARGUMENT GUARD, seeded here because it is the one part
# of that change this harness CAN reach: it runs at module level on argv, above the DOCS
# ternary that SEED short-circuits. Asserted on the exit status AND on the absence of a
# findings section: the defect being guarded is an unrecognised argument producing a
# small, reassuring count, so "no findings section" is the observable, not "no match".
# ⚠️ `.` and `CLAUDE.md` are in the list on purpose. The first version of the guard
# rejected only `--`-prefixed tokens while its message claimed there were no positional
# arguments, and the /audit-context command with its flag dropped ran clean to exit 0.
guard_fail=0
for bad in --doc --docs-frozn --sibling-root -docs -h . CLAUDE.md; do
  gout="$(SEED="$here/SEED.md" python3 "$here/refcheck.py" "$bad" 2>&1)"; grc=$?
  if [ $grc -eq 0 ] || grep -q '### FINDINGS' <<<"$gout"; then
    echo "  FAIL  unrecognised argument accepted: $bad (rc=$grc)"; fail=1; guard_fail=1
  fi
done
[ $guard_fail -eq 0 ] && echo "  ok    rejected 7 unrecognised arguments (flags AND positionals)"
# ...and the complement, or the guard could simply reject everything: a KNOWN flag must
# still run. Under SEED the docs flags change nothing, which is the point — they must not
# be an error either.
for good in --sessions --docs --docs-live --docs-frozen; do
  SEED="$here/SEED.md" python3 "$here/refcheck.py" "$good" >/dev/null 2>&1 \
    || { echo "  FAIL  known flag rejected: $good"; fail=1; }
done
echo "  ok    accepted 4 known flags (the guard is not simply refusing everything)"
total=$(( ${#must_catch[@]} + ${#must_be_silent[@]} + ${#must_be_placeheld[@]} + 10 ))
[ $fail -eq 0 ] && echo "SENSITIVITY: $total/$total PASS" || echo "SENSITIVITY: FAILED"
exit $fail
