---
name: project_session_2026_08_27
description: /audit-context and acting on it — the reference checker got its upstream fixes, 24 findings went to 1, and a held stamp turned out to be a count without a checklist.
metadata:
  type: project
---

# 2026-08-27 — the context layer repaired; a hold with no release condition

*No spend, no model, no filter, no scoring-path change, **nothing deployed**.* All twelve
changed files are `CLAUDE.md`, `docs/`, `memory/` and `tests/fixtures/`. Nothing this
session touches a path that reaches NexusMind — **deploy is N/A, not skipped.**

## What was asked

`/audit-context`, then act on findings 1–3, then 5–6, then wrap up: clean up, update docs,
hypotheses, TODOs and GitHub issues, curate, commit, push, merge and deploy if applicable.

## ⛔⛔ THE KEEPER — a hold is indistinguishable from neglect without a release condition

The audit found the framework stamp pinned at `v1.26.0` against upstream `v1.28.0` and no
entry past `v1.25.1 + v1.26.0` in the file the frontmatter names as provenance. I reported
that as "the triage was never recorded" and proposed bumping the stamp.

**Both halves were wrong, and the correction is the finding.** The 08-26 session had
triaged all three releases and **deliberately held** the stamp, recording why verbatim:

> *"`CLAUDE.md` stamp stays v1.26.0 until adopt items land. A stamp ahead of its content
> silences the check that would catch the gap."*

That is correct practice — it is the v1.25.1 lesson applied, where a footer stamp ran two
days ahead of its content and silenced the drift check for two releases. I had not opened
the previous session's file before calling something unrecorded.

**But the real defect was upstream of my error.** That triage logged
**"3 adopt, 0 decline, 4 n/a, 5 in force"** — a *count*, not a *checklist*. One adopt item
was named (v1.27.0 #77, `$0` → `$(0)`, landed in `4b5b28a`). The other two were never
written down anywhere: not the session file, not `docs/TODO.md`, not the history record.

⭐ **So nothing in the record could answer "is the hold dischargeable?"** A stamp that is
HELD and a stamp that is STALE are byte-identical; the difference lives only in prose, and
prose in a session file is invisible to an audit that reads the always-loaded layers.
**A hold needs a release condition, or it reads as neglect on the next audit** — which is
exactly what I did with it.

**Fix**: the hold, its reason and a per-item adopt table now live in
`docs/decisions/framework-adoption-history.md`, and the held-not-stale statement is also in
the footer (which loads). Rule for `/update-drift`: **name each adopted item and where it
lands.**

## Reference integrity: 24 findings → 1

`tests/fixtures/reference-integrity/refcheck.py` is a genuine **fork**, not a stale copy —
it carries rungs upstream lacks (auto-memory, systemd-unit class, self-prefix strip,
generic-artifact class). 347 lines against upstream's 796. So: surgical back-port.

| Change | Direction | Measured effect |
|---|---|---|
| rung 1b, doc-relative (#54) | loosening | fires — markdown link semantics *are* doc-relative |
| link labels masked, URLs extracted, declined URLs named (#55) | both | **+108 unique / +110 occurrences newly checked**, by ablation |
| locally "resolves" = rung 1, not the suffix rung (#56) | tightening | rung 4 **kept** — the 2026-08-12 evidence was cross-repo |
| identifier-shaped whitelist guard (v1.26.1) | tightening | latent: 0 occurrences here, proven live by seed 32 |

Plus a local rung-5 extension for `project_session_*.md` in the auto-memory directory: the
gotcha log cited two such files as broken while both sat there at **exactly the byte sizes
it quotes** (14,194 / 9,502).

**Sensitivity 24/24 → 33/33.** Nine seeds, all for what the changes newly *permit*.

⭐ **A seeded assertion caught a defect in the back-port itself** — `docdir` gated on
`isabs(doc)` instead of *outside ROOT*, and `run.sh` names its seed document absolutely, so
**rung 1b silently never fired under its own harness.** An assertion written against the
*absence of a finding* would have passed vacuously; only one written against the **rung
label** could see it. Logged in the unreachable-mechanism catalogue as **caught pre-ship,
not counted in the occurrence total**.

**Dispositions of the 24**, counted individually rather than inferred: **17** unmarked
cross-repo (qualified in prose — rung 4 strips backticked paths, so a reference may not
mark itself), **4** marked genuinely unresolvable, **2** resolved by the rung-5 extension,
**1** left standing. Qualifying `main.py` surfaced a real **collision** — NexusMind has two
— disambiguated to `scripts/main.py` at all four sites.

⚠️ **The one left standing is deliberate**: `NexusMind/scripts/research/nm188_mojibake_derived.py`,
never committed there, absent from disk, while its `nm188_*` siblings exist. **Zero is not
the target** — a change driving this to zero would have disabled the check. Proven alive
after the change by a live mutation on the real corpus (two fabricated refs, one backticked
and one a link URL, both caught, then reverted).

**The accepted loss was measured, not just accepted**: #55 makes a broken path appearing
*only* as a link label unreportable. Cost here: **0** — 87 links, 2 labels that are paths,
both resolve. That is a window, not a property.

## Size: 46 bytes → 117, and the real fix is still not done

`CLAUDE.md` was **46 bytes** under the 40,000 hard cap (45 at the previous audit — one byte
of movement in a full cycle). Two stale footer claims were corrected — `v1.26.0` called
"the latest TAG", and `v1.26.1` called "(candidate, unreleased)" eleven days after it
shipped — and the trim paid for both additions. Net **−71 bytes**.

⛔ **The real fix is two steps and neither is done**: 8 of 39 pointer rows carry **47%** of
the table (median 222 chars, largest 1,189). Trimming them *deletes* caveats with no other
home — `260 at 12 cycles` exists nowhere else in either repo. **Write the caveats into
their targets first, then trim.** Est. ~3,370 chars.

## #122 — third confirmation, and a one-command probe

The `CLAUDE.md` delivered into context began at line 34 again; the 32-line frontmatter did
not arrive. **Probe: compare `wc -l CLAUDE.md` against what is visible in context** — 295
on disk, and lines 5 and 31 absent from context. It mattered today because the stamp-hold
note's natural home is `framework_reconciliation`, *inside* that block; it was duplicated
into the footer as a deliberate lesser evil while #122 is open. Commented on the issue.

## My own errors this session

1. **Reported a gap before reading the record that explained it** — the "never recorded"
   stamp finding above.
2. **Two numbers carried instead of derived**, in one write-up: "+107" (a delta across a
   *four-part* change, attributed to one part; ablation says the arm is worth 108) and
   "nineteen cross-repo" (never recounted; it is 17). Both caught by the
   claim-verification lens, not by reading.
3. **A malformed `str.replace` anchor** that omitted a closing backtick, inserting a stray
   backtick and a zero-width space into `cross-repo-prioritization.md`. The `count==1`
   assert passed — it asserts the anchor is *unique*, never that it is *complete*. Caught
   in the diff, repaired, and `memory/` swept for U+200B.
4. **A naive fence-toggle awk** used to check whether the gotcha log's annotations were
   documentation. It mis-tracks nested fences; the runner's own 0-extracted/0-malformed
   result was the actual proof.

## Verification battery

| check | result |
|---|---|
| `refcheck.py` sensitivity | **33/33 PASS** |
| live mutation, real corpus | 2 fabricated refs caught, reverted clean |
| reference integrity | **1 finding**, 396 resolved, 30 placeheld, 12 declined URLs named |
| `tests/unit` | 350 passed, 4 skipped |
| curate verify runner | **49 of 74 — 49 pass, 0 fail, 0 error, 0 cannot-verify, 11 manual, 0 malformed**, exit 0 (14 unextracted are fenced documentation) |
| budget guards | `CLAUDE.md` 39,883 (117 left) · index 18,035 |
| structural pre-check | 13 markdown files in scope, 0 violations |
| index self-consistency | 4 identifier clusters, **0 contradicting pairs** |

## Next session

1. **Owner decision: bump the stamp to v1.28.0, or not.** Only the owner knows what the
   08-26 triage's two unnamed adopt items were.
2. The `CLAUDE.md` size fix — caveats into targets, *then* trim the 8 fat rows.
3. `nm188_mojibake_derived.py` — someone who remembers that experiment should say what the
   script was really called.
