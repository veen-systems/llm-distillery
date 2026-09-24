#!/bin/bash
# Arms per PREREGISTRATION.md. Runs are sequential so each pass hits the prompt cache.
set -u
cd "$(dirname "$0")/../../.."
E=docs/evidence/2026-09-24-v8-5-gate; C=filters/human_thriving/v8/config.yaml; P=filters/human_thriving/v8
g=docs/evidence/2026-09-03-v8-1-gate/gate_input.jsonl
run(){ PYTHONPATH=. python3 scripts/score_deepseek_production.py --config $C --prompt $P/$1 --input $2 --output $E/runs/$3.jsonl --concurrency 13 > $E/runs/$3.log 2>&1; echo "$3 exit=$?"; }
for i in $(seq 1 6); do run prompt-v8-4.md $E/flip_input.jsonl F4_$i; run prompt-v8-5.md $E/flip_input.jsonl F5_$i; done
for i in $(seq 1 12); do run prompt-v8-4.md $g G4_$i; run prompt-v8-5.md $g G5_$i; done
echo ALL_DONE
