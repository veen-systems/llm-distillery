# Sensitivity fixture — every line below is a deliberate test case

## MUST BE CAUGHT (genuine breaks)
1. fabricated bare basename, 0 matches: `totally_made_up_thing.py`
2. fabricated under a real sibling repo: `NexusMind/src/scoring/no_such_module.py`
3. a GENERIC first component must not mark a sibling: `docs/no_such_file_xyz.md`
4. fabricated auto-memory file: `feedback-does-not-exist-at-all.md`
5. fabricated path fragment with a slash: `scripts/nope/absent_thing.py`

## MUST STAY SILENT (correct resolutions)
6. real generic basename, a CLASS of artifact: `config.yaml`
7. real cross-repo qualified path: `NexusMind/scripts/main.py`
8. real assistant auto-memory file: `feedback-claim-requires-verify.md`
9. real local move — fragment that resolves at rung 2: `gate/ground_truth_gate.py`
10. asserted absent, must be skipped: ~~`filters/foresight/v1/config.yaml`~~
