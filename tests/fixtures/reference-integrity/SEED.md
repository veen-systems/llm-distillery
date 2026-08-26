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

## PLACEHOLDER SKIP — the failures this loosening NEWLY PERMITS (v1.23.0 / #45)

⚠️ **This file's semantics depend on physical line layout.** Cases 13, 16, 19 and 20
place a marker relative to a path ON THE SAME LINE. A markdown reflow or prettier pass
silently changes what they test, with no assertion guarding it. Do not rewrap.

A marker is an assertion of *intent*, and a wrong one is not detectable. So these
seed the ways it can go wrong, not the ways it works.

13. **stale marker, explicit form** — marker on a path that DOES resolve. Must be a
    FINDING, not a skip: mislabelling is how a real break gets hidden.
    `scripts/deployment/verify_filter_package.py` <!-- placeholder -->
14. **stale marker, angle-bracket form** — an angle segment on a path that resolves
    is caught the same way: `tests/unit/<test_normalization_invariant.py>`
15. **marker covering no path** — a marker that silently does nothing is the exact
    failure this step is built against. Must be a FINDING. <!-- placeholder -->
16. **unmarked break sharing a marked line** — span-scoping must cover only the
    nearest preceding path. ⚠️ THE NEXT LINE MUST STAY ONE PHYSICAL LINE: refcheck
    is line-based, so wrapping it makes this case vacuous — verified 2026-08-12 by
    breaking span-scoping and still getting 18/18.
    `never_existed_alongside.py` and `docs/<slug>.md` <!-- placeholder --> — first must be caught.
19. **marker NOT adjacent to its path** — a trailing marker must not absorb a path
    it does not touch. `absorbed_by_distance.py` is broken, then prose, then a marker:
    `absorbed_by_distance.py` and some intervening prose here <!-- placeholder -->
20. **stale marker on a CROSS-REPO path** — the guard must run the full ladder, not
    rungs 1-2. NexusMind's `deploy_filters.sh` <!-- placeholder --> resolves at rung 4
    and must be reported STALE, not skipped.

## PLACEHOLDER SKIP — must land in the COUNTED skip section, not vanish
17. genuine instructional placeholder: `filters/<name>/<version>/config.yaml`
18. genuine host-side unit, marked: `nexusmind-scorer.service` <!-- placeholder -->

## SELF-PREFIX STRIP — the failures THAT loosening newly permits (2026-08-15)

Docs in this repo sometimes write a local path with the repo's own name in front
(`llm-distillery/scripts/remote_deploy.sh`) — usually in a cross-repo sentence where
every other path is qualified. Rung 4 strips a leading component repeating a
*sibling's* name but never the *local* repo's, so these were reported UNRESOLVED
while the file sat in the tree. "Not reported" would then have meant "never checked".

The strip is a loosening, so what it newly permits is a *false* resolution. These
three seed exactly that:

21. **real path behind the self-prefix** — must now RESOLVE, not be reported:
    `llm-distillery/scripts/remote_deploy.sh`
22. **fabricated path behind the self-prefix** — the strip must not launder a genuine
    break into a resolution: `llm-distillery/scripts/no_such_self_thing.sh`
23. **ambiguous path behind the self-prefix** — the collision rule must survive the
    strip, exactly as rung 2 and rung 4 already carry it:
    `llm-distillery/model/adapter_model.safetensors`

## SYSTEMD UNIT CLASS — the failure THAT rule newly permits (2026-08-15)

A bare `foo.service` is a unit NAME. The rule resolves one only if its definition
exists somewhere in the estate, so the laundering case is a unit that exists nowhere:

24. **fabricated systemd unit** — must stay a FINDING, not be absorbed by the class:
    `totally-made-up-unit.service`

## v1.28.0 / v1.26.1 BACK-PORT — the failures these four changes newly permit (2026-08-27)

Ported from upstream `#54` (doc-relative rung), `#55` (link labels are presentation),
`#56` (locally, "does resolve" means rung 1) and v1.26.1's identifier-shaped whitelist
guard. Three of the four are LOOSENINGS, so what is seeded below is the *false
resolution* each one newly permits — not the case it was built for. This doc sits in
`tests/fixtures/reference-integrity/`, so doc-relative here means that directory.

### #54 — rung 1b, doc-relative

25. **real path beside this document** — must now RESOLVE (rung1b), not collide:
    `SEED.md`
26. **fabricated path beside this document** — the new rung must not launder a genuine
    break: `no_such_doc_relative_file.md`

### #55 — a link's LABEL is presentation, its URL is the reference

27. **broken URL** — newly checked, must be a FINDING:
    [the label is fine](no_such_link_target.md)
28. **broken path in the LABEL, good URL** — the label is deliberately NOT checked, and
    this is the loss the masking accepts: [`no_such_label_path.md`](SEED.md)
29. **declined URL must be NAMED, never dropped** — masking a label is a silent loss
    unless the URL we decline to check is reported with its reason:
    [external](https://example.invalid/nope.md)
30. **struck markdown link** — an absence assertion in link form:
    ~~[gone](no_such_struck_target.md)~~

### #56 — the suffix rung must not ADJUDICATE INTENT

31. **marker on a path that resolves only at rung 2** — must now be COUNTED as a
    declared placeholder, not reported STALE: `fixtures/reference-integrity/run.sh` <!-- placeholder -->

### v1.26.1 — filename-shaped whitelist entry

32. **identifier-shaped token** — must never be extracted as a path, and must be
    counted rather than silently dropped: `process.env`

### rung 5 extension — auto-memory session files (2026-08-27)

The rung resolves files in the Claude Code auto-memory directory, outside ROOT. Its
pattern was written for the kebab-case `feedback-*` family and missed the underscore
`project_session_*` one. Extending it is a LOOSENING, so the seed is the laundering
case, not the fix:

33. **fabricated auto-memory session file** — must stay a FINDING, not be absorbed by
    the new pattern: `project_session_1999_01_01.md`
