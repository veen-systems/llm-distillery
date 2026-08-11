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
for p in "${must_catch[@]}"; do
  grep -q -- "$p" <<<"$findings" && echo "  ok    caught  $p" \
    || { echo "  FAIL  missed  $p"; fail=1; }
done
for p in "${must_be_silent[@]}"; do
  grep -q -- "$p" <<<"$findings" && { echo "  FAIL  reported $p"; fail=1; } \
    || echo "  ok    silent  $p"
done
total=$(( ${#must_catch[@]} + ${#must_be_silent[@]} ))
[ $fail -eq 0 ] && echo "SENSITIVITY: $total/$total PASS" || echo "SENSITIVITY: FAILED"
exit $fail
