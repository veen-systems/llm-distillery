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
total=$(( ${#must_catch[@]} + ${#must_be_silent[@]} + ${#must_be_placeheld[@]} + 5 ))
[ $fail -eq 0 ] && echo "SENSITIVITY: $total/$total PASS" || echo "SENSITIVITY: FAILED"
exit $fail
