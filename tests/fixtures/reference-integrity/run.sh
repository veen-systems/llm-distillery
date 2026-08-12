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
must_catch+=(verify_filter_package.py                 # 13 stale marker, explicit
             test_normalization_invariant.py          # 14 stale marker, angle-bracket
             never_existed_alongside.py)              # 16 unmarked break on a marked line
must_be_placeheld=("filters/<name>/<version>/config.yaml"   # 17 counted, not dropped
                   nexusmind-scorer.service)                # 18
for p in "${must_catch[@]}"; do
  grep -q -- "$p" <<<"$findings" && echo "  ok    caught  $p" \
    || { echo "  FAIL  missed  $p"; fail=1; }
done
for p in "${must_be_silent[@]}"; do
  grep -q -- "$p" <<<"$findings" && { echo "  FAIL  reported $p"; fail=1; } \
    || echo "  ok    silent  $p"
done
placeheld="$(sed -n '/### SKIPPED AS DECLARED-PLACEHOLDER/,/### SKIPPED AS ASSERTED/p' <<<"$out")"
for p in "${must_be_placeheld[@]}"; do
  grep -q -- "$p" <<<"$placeheld" && echo "  ok    counted $p" \
    || { echo "  FAIL  not in counted skip section: $p"; fail=1; }
done
grep -q "COVERS NO PATH" <<<"$findings" && echo "  ok    caught  marker-covering-no-path" \
  || { echo "  FAIL  missed  marker-covering-no-path"; fail=1; }
total=$(( ${#must_catch[@]} + ${#must_be_silent[@]} + ${#must_be_placeheld[@]} + 1 ))
[ $fail -eq 0 ] && echo "SENSITIVITY: $total/$total PASS" || echo "SENSITIVITY: FAILED"
exit $fail
