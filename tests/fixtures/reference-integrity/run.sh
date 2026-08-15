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
total=$(( ${#must_catch[@]} + ${#must_be_silent[@]} + ${#must_be_placeheld[@]} + 1 ))
[ $fail -eq 0 ] && echo "SENSITIVITY: $total/$total PASS" || echo "SENSITIVITY: FAILED"
exit $fail
