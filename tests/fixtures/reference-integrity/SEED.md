---
framework: agent-ready-projects v1.23.0
framework_reconciliation: |
  Cases 11 and 12 test the FRONTMATTER MARKER SCOPE added 2026-08-11. The
  `framework:` stamp above is several lines away from both, so under the old
  1-line window neither could see it.
  11. fabricated path inside frontmatter, exists nowhere: `templates/no_such_template.md`
  12. real sibling path, marked ONLY by the stamp above: `templates/release.md`
---

# Sensitivity fixture — every line below is a deliberate test case

## MUST BE CAUGHT (genuine breaks)
1. fabricated bare basename, 0 matches: `totally_made_up_thing.py`
2. fabricated under a real sibling repo: `NexusMind/src/scoring/no_such_module.py`
3. a GENERIC first component must not mark a sibling: `docs/no_such_file_xyz.md`
4. fabricated auto-memory file: `feedback-does-not-exist-at-all.md`
5. fabricated path fragment with a slash: `scripts/nope/absent_thing.py`
11. **fabricated path INSIDE frontmatter** — see frontmatter case 11. The
    frontmatter marker scope must not stop the check running there; a path that
    exists in no repo is still a break.

## MUST STAY SILENT (correct resolutions)
6. real generic basename, a CLASS of artifact: `config.yaml`
7. real cross-repo qualified path: `NexusMind/scripts/main.py`
8. real assistant auto-memory file: `feedback-claim-requires-verify.md`
9. real local move — fragment that resolves at rung 2: `gate/ground_truth_gate.py`
10. asserted absent, must be skipped: ~~`filters/foresight/v1/config.yaml`~~
12. **real sibling path inside frontmatter, marked only by the stamp** — see
    frontmatter case 12. This is the absorption the 2026-08-11 change
    deliberately PERMITS: inside frontmatter, one `framework:` stamp marks every
    reference in that frontmatter, not just its immediate neighbours. Bounded
    because frontmatter is short and hand-maintained; it can never absorb a
    reference in the document body.
