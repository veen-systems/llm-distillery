# Framework adoption history — agent-ready-projects

Per-release reconciliation record. Moved out of `CLAUDE.md`'s
`framework_reconciliation` frontmatter on 2026-08-11, where it had grown to
4,931 chars (12.5% of a file 358 chars under Claude Code's 40k warn threshold).

**The frontmatter keeps only what is still operative** — the current stamp, the
standing skill-scope rules, and open decisions. Everything below is the
historical record: correct when written, and kept for provenance rather than for
reading every session.

Current stamp lives in `CLAUDE.md` frontmatter (`framework: agent-ready-projects vX.Y.Z`).
Upstream changelog: https://github.com/ducroq/agent-ready-projects/blob/master/CHANGELOG.md

---

## v1.26.1 + v1.27.0 + v1.28.0 — triaged 2026-08-26 evening via `/update-drift`

**3 adopted, 0 declined, 4 not applicable, 5 already in force.** Pinned `v1.26.0`,
upstream `v1.28.0`.

⛔ **THE STAMP IS DELIBERATELY HELD AT v1.26.0, and that is the operative fact.**
Recorded verbatim in `memory/project_session_2026_08_26_evening.md`: *"stamp stays
v1.26.0 until adopt items land. A stamp ahead of its content silences the check that
would catch the gap."* This is the v1.25.1 lesson applied (see the section below —
a footer stamp ran ahead of its content for two days and silenced exactly this check).
**A reader who sees `v1.26.0` and no note here concludes the drift is unreviewed.**
It is reviewed and held. Bump the stamp when — and only when — the two unlanded
adopt items below are in the tree.

**Step 0 reconciliation**: 9 mentioned `(file, framework)` pairs, 4 stamped, 5 in the
difference, all dispositioned. One is a **second framework** — `agent-ready-papers`,
cloned locally, already declined at `docs/TODO.md:4052` (*"not adopted here by
design"*). One is a matcher false positive (`agent-ready-fixture`, inside a test
fixture). All three user-global skills (`audit-context`, `update-drift`, `curate`)
are **byte-identical** to the framework's shipped `.claude/skills/` copies; the
23-line diff is the installer converting the SAVE-AS comment into real frontmatter.

### ⛔ The triage produced a COUNT WITHOUT AN ITEMISATION — recorded 2026-08-27

The 08-26 session logged *"3 adopt"* and enumerated **one** of them. Neither the
session file, `docs/TODO.md`, nor this file named the other two, so **nothing could
answer "have the adopt items landed?" — which is the exact question the held stamp
defers to.** A count is not a checklist. Future `/update-drift` runs name each
adopted item and where it lands, or the hold has no release condition.

| Adopt item | State | Evidence |
|---|---|---|
| **v1.27.0 #77** — skill arguments are substituted into the skill body, so a bare `$0` in an embedded awk program arrives as an argument word. Fix is `$(0)` | ✅ **LANDED** | `.claude/skills/review-changes/SKILL.md` in `4b5b28a`. Verified by execution both directions: old form with args examined **nothing**, new form finds the lossy row in both. 6 lines / **10** occurrences — the locating grep (`isdelim(`, 1 line) was not the enumerating grep |
| *(unnamed)* | ❓ **UNKNOWN** | Not recorded |
| *(unnamed)* | ❓ **UNKNOWN** | Not recorded |

**Candidates re-derived from the changelog on 2026-08-27** — these are what the two
unnamed items most plausibly were, **not** a record of what that session chose:

- **v1.28.0 (#54, #55, #56)** — `audit-context` Step 4 reported three classes of
  correct reference as defects: no doc-relative rung (**42 of 102 findings on one
  adopter**), the markdown-link *label* extracted as a reference, and the suffix rung
  adjudicating placeholder intent.
- **v1.26.1** — a whitelist entry that is filename-shaped rather than extension-shaped
  (`env` captures `process.env`).

### ✅ Both candidates LANDED 2026-08-27 — back-ported, not re-copied

`tests/fixtures/reference-integrity/refcheck.py` is a genuine FORK, not a stale copy
(it carries rungs upstream lacks: auto-memory, systemd-unit class, self-prefix strip,
generic-artifact class), so this was a surgical back-port. Four changes:

| Change | Direction | Effect on the real corpus |
|---|---|---|
| rung 1b, doc-relative (#54) | loosening | fires; markdown link semantics ARE doc-relative |
| link labels masked, URLs extracted + declined URLs named (#55) | both | **+108 unique / +110 occurrences newly CHECKED**, measured by ABLATION (disable only this arm: 396 → 288 unique). All resolve; the arm contributes 0 findings |
| locally "does resolve" = rung 1, not the suffix rung (#56) | tightening | rung 4 KEPT: the 2026-08-12 evidence for the full ladder was cross-repo |
| identifier-shaped whitelist guard (v1.26.1) | tightening | latent — 0 occurrences measured here |

Plus one local rung extension: rung 5 now covers `project_session_*.md` in the
auto-memory directory. The gotcha log cited two such files as broken while both sat in
that directory at exactly the byte sizes it quotes (14,194 / 9,502).

**Sensitivity: 24/24 → 33/33.** Nine seeds added for the failures these changes newly
PERMIT (not the ones they were built for): rung-1b laundering, a broken link URL, the
accepted label loss, a declined URL that must be NAMED, a struck link, a rung-2-only
marker that must now be counted rather than reported stale, an identifier-shaped token,
and a fabricated auto-memory session file.

⭐ **A seeded assertion caught a defect in the back-port itself.** `docdir` was gated on
`isabs(doc)` rather than on *outside ROOT* — and `run.sh` names its seed document
absolutely, so **rung 1b silently never fired under its own harness** while working in
the real run. Only an assertion written against the RUNG LABEL, rather than against the
absence of a finding, could see it.

**Outcome on the real corpus: 24 findings → 1.** Dispositions, counted individually
rather than inferred from the total: **17** unmarked cross-repo references (real files in
NexusMind / ovr.news; the prose simply did not name the repo), now qualified in prose —
rung 4 strips backticked paths before looking for a repo name, so a reference may not
mark itself; **4** marked as genuinely unresolvable; **2** resolved by the rung-5
extension; **1** left standing. The one remaining is a genuine break —
`NexusMind/scripts/research/nm188_mojibake_derived.py`, never committed there and absent
from disk, while its `nm188_*` siblings exist. **Zero is not the target**; a change that
drove this to zero would have disabled the check rather than fixed it. Proven alive
after the change by a live mutation on the real corpus: two fabricated references
(one backticked, one a link URL) both caught, then reverted.

**The accepted loss was MEASURED, not just accepted.** #55 makes a broken path that
appears *only* as a link label unreportable. Cost on this corpus: **0** — 87 links, 2
labels that are paths, both resolve. ⚠️ That is a WINDOW, not a property: a future
document can introduce one, which is why `run.sh` asserts the masking stays scoped to
the label span rather than trusting it.

⚠️ **THE STAMP DECISION IS STILL OPEN, and it is the owner's.** The two items above are
what the 08-26 triage *most plausibly* meant; that session never named them. If they
were, the hold is discharged and the stamp goes to **v1.28.0**. If they were something
else, the hold stands and that something else is still unlanded. **Nothing in the record
can settle this** — which is the whole cost of logging a count instead of a checklist.

⚠️ **`review-changes` here is RE-MAPPED, not copied** (453 lines local vs 358
upstream, 577 diff lines): the template's risk tiers key on paths this repo does not
have, so a verbatim install tiers every change LOW and quietly does nothing.
**Patch it surgically; never re-copy.** Filed upstream as **agent-ready-projects#94**:
a fix to a project-local skill cannot reach a re-mapped adopter, and the prescribed
remedy ("re-copy by hand") destroys the re-map. `install-global-skills.sh --check`
solves this for user-global skills; there is no project-local equivalent.

**Adopter-side issue filed**: **agent-ready-projects#48** — the project-file budget
guard reported headroom in *characters* where the ceiling counts *bytes*.

---

## v1.25.1 + v1.26.0 — triaged 2026-08-15 via `/update-drift`

**3 adopted, 1 declined, 4 not applicable, 2 already in force.**

Clone checked at `713a307` (tag `v1.26.0`), in sync with `origin/master`. Note the
default branch is **`master`, not `main`** — a `git log main` fails outright, which
is a fast way to conclude "no releases" from a tooling error.

**The gap existed because a stamp ran ahead of its content.** `CLAUDE.md`'s footer
had read `v1.26.0` since 2026-08-13 while this file's last entry was v1.25.0, and
nothing from either release had been triaged. The frontmatter stamp (`v1.25.0`) was
the honest one. That is the exact failure mode `/update-drift` Step 6 warns about:
a premature stamp silences the check that would have caught the gap. A stamp-
agreement probe now lives in `CLAUDE.md`, seeded against this real disagreement
before it was believed.

| From | What | Outcome |
|---|---|---|
| v1.25.1 | Step 1.5 CRLF strip `{ sub(/\r$/, "") }` | **Adopted** → `.claude/skills/review-changes/SKILL.md`. Reproduced against *our* re-mapped awk first, not adopted on the changelog's word: a seeded lossy row in a CRLF file printed **nothing**, byte-identical to a clean run; the one-line rule restored the hit; the LF result was unchanged on both sides. Live exposure today is nil (`core.autocrlf` unset, 0 of the tracked `.md` files carry CR) — but `docs/RUNBOOK.md` and CLAUDE.md's `MSYS_NO_PATHCONV=1` document driving this repo from Git Bash, where `core.autocrlf=true` is the installer default |
| v1.25.1 | Withdraw the "every reported hit is a real loss" absolute | **Adopted** → same file. It lived here in our own wording — *"A hit is data loss, not a style nit"* — so a phrase-grep for upstream's text would have missed it. Refuted locally in 3 of the 4 classes upstream names: empty excess cells (`\| 1 \| 2 \| \|` reports, loses nothing), YAML frontmatter closing after a piped `description:`, and a spaced `- - -` break. The setext-heading class **did not reproduce** — our guard needs a pipe the fixture lacked, and that is recorded as not-reproduced rather than repeated |
| v1.25.1 | Tighten `isdelim()`'s guard to require a pipe in the delimiter row | **Declined** — upstream deliberately left it loose and says so: the cost to pipe-less delimiter rows is unestablished on both sides, GFM ships no example of one, and framework #52 stays open for the decision. Taking it here would fork our copy from upstream on an undecided question |
| v1.25.1 | framework #58 — the same CRLF defect in `curate`'s copied runner | **Not applicable** — still unfixed **upstream** at v1.26.0, and `curate` is user-global here. Nothing to adopt until upstream ships it; re-check on the next drift run |
| v1.26.0 | `curate` Step 0 sub-step 5 takes the project file | **Already in force** — global `curate` verified byte-identical to the v1.26.0 tag by `diff`, and its runner invocation names `CLAUDE.md` explicitly |
| v1.26.0 | `audit-context` repo-specific count attributed, not probed | **Already in force** — global `audit-context` byte-identical to the tag |
| v1.26.0 | Probe a project-file count against its source of truth | **Adopted** → `CLAUDE.md`. **It caught a live drift on contact**, which is why it earns its place: the file read *"10th occurrence"* while `memory/working-rules.md` read **12th** — in a rule whose own subject is mechanisms that never ran. Corrected to 12th and probed. (Upstream's "third time that line has lagged" is about the **framework's** own project file; this is the first such lag measured here, and no earlier one was looked for) |
| v1.26.0 | `templates/test-verify-memory.md` claim fix | **Not applicable** — the over-broad phrase is absent, and our copy already states the correct thing (the disposition comes from the `CANNOT VERIFY:` prefix, not the exit status) |
| v1.26.0 | `templates/gotcha-log.md` claim fix | **Not applicable** — the claim is about a Promoted table, and we have none. Already declined for the same reason at v1.20.0 |
| v1.26.0 | `docs/claim-audit-sample-2026-08-13.md` | **Not applicable** — framework-internal evidence, no counterpart surface |

### Two stamp defects found independently of the gap

Neither came from the changelog; both came from reading every stamp before
comparing anything, which is Step 0's whole point.

1. **The two `CLAUDE.md` stamps disagreed** — frontmatter `v1.25.0`, footer
   `v1.26.0`. Now probed, so the next disagreement reports both numbers.
2. **`.claude/skills/review-changes/SKILL.md` cited "v1.26.1", which upstream has
   never released.** The fix it describes is real but sits on the unmerged branch
   `fix/review-changes-scope` at `e824212`. A citation to a version that does not
   exist cannot be checked against anything, and would have become permanently
   wrong the moment upstream released that fix under a different number. Restated
   as a commit reference.

A third stamp was found and deliberately **not** touched:
`tests/fixtures/reference-integrity/SEED.md:2` reads `v1.23.0` as **fixture data**,
frozen on purpose to test frontmatter marker scope. Bumping it would break the test
it exists for.

---

## v1.24.0 + v1.25.0 (both released 2026-08-12) — triaged and adopted 2026-08-12 via `/update-drift`

**3 adopted, 0 declined, 1 not applicable, 3 already in force.**

Clone checked at `889b038`, in sync with its origin. Two releases behind, both
shipped the same day we adopted v1.23.0 — upstream velocity, not neglect.

| From | What | Outcome |
|---|---|---|
| v1.24.0 | `curate` Step 0 reads metadata, not documents | **Already in force** — global `curate` verified byte-identical to the framework's tracked copy by `diff`, not by reading its description |
| v1.24.0 | `[RESOLVED]` + recurrence count belong in an entry's **heading** | **Adopted** → `memory/gotcha-log.md`. Measured before acting: 5 resolution markers were already in headings but in **3 incompatible formats**, and recurrence was **7 in bodies, 0 in headings**. Normalised all five to a `[RESOLVED…` prefix findable by one grep, tagged 5 headings (`[5x verify-the-call-path]`, `[4x verify-the-call-path]`, `[3x restated-set drift]`, two `[2x]`), and documented the forms in the file's template comment |
| v1.24.0 | lint rule 8 — ratchet adopter-facing template sizes | **Not applicable** — no `templates/` dir; we ship no templates upstream |
| v1.25.0 | adversarial lens: one rule — a claim needing a measurement gets one, gets hedged, or is not ready | **Adopted** → `.claude/skills/review-changes/SKILL.md`. We already had the negatives half (v1.22.0); the **absolutes-in-descriptions** half is new. Grounded in the same day's own failure rather than upstream's example — see below |
| v1.25.0 | `hypothesis-log` gains a trigger in the working path | **Adopted, adapted** — we have no `templates/hypothesis-log.md`; we have per-topic `memory/*-hypotheses.md`. Landed as a lens clause: report an unmeasurable claim as a finding **at the moment it is made**, register during `/curate`, home is the topic file. This was the exact gap hit hours earlier — a hypothesis noticed while writing results up, not when the claim was made |
| v1.25.0 | shape rule: never end a bolded phrase with a `**`-suffixed glob | **Already in force — nothing to fix.** 0 hits across 451 markdown files. **Verified by execution with a seeded control**: my first two sweep patterns were wrong (one covered only the single-glob shape; the second had the backticks in the wrong order and matched **0 of 2** known positives). Only the third — 2/2 positives, 0/2 safe lines — makes "0 hits" mean anything |
| v1.25.0 | gotcha-log "2–3 lines" rule **withdrawn** | **No action, and it vindicates this log.** llm-distillery IS the cited evidence upstream: 203 entries, median ~1,200 chars, 35% >1,500. Recorded the withdrawal and the real signal (>3,000 chars) in the file's template comment |

### Why the absolutes rule was adopted on our own evidence, not upstream's

Upstream's gate for shipping it was that it catch something in a repo other than
its own. It did — and independently, on the same day, this repo produced a
textbook instance without knowing the rule existed. A measured claim
("NexusMind's `pre_enrich` attempted 35,229 Google News rows and replaced zero")
was written up with an unmeasured absolute attached: *"a property of the URL
scheme, so no fetcher change moves it."* The measurement was scoped to one
fetcher; the absolute was stated of the scheme. It propagated into
`ovr.news#312` as a premise about a **different** resolver — one that
demonstrably works, 74 of 103 — and licensed a "do not fix the GN resolver"
recommendation that would have retired a capability carrying 22 of 38 published
articles. Refuted by a peer re-measuring against their own source.

That is the rule's whole thesis: the number was right, the absolute rode along
unmeasured, and nothing in the previous lens asked for it. Hence the extra clause
we added beyond upstream's text — **name the population, not just the number.**

### Finding sent upstream

v1.24.0's Step 0.3 reconciles its heading count against
`grep -c '^\*\*Problem\*\*'` as ground truth. On this log that reads **203**
against **206** both-level headings. Three orphans: one real section
(`## The unreachable-mechanism catalogue`) and **two real entries that do not use
the `**Problem**` shape**. So the reconcile under-counts this log by 2 and will
report a mismatch every run — the same class as the level-blind grep v1.24.0
itself shipped to fix.

## v1.22.0 + v1.23.0 (both released 2026-08-11) — triaged 2026-08-12 via `/update-drift`

**2 adopted, 0 declined, 1 not applicable, 2 already in force, 1 deferred.**

| From | What | Outcome |
|------|------|---------|
| v1.22.0 | `curate` Step-0 verify runner | **Already in force** — global skill byte-identical to the v1.23.0 tag. But its *adopter action* was real work here, below |
| v1.22.0 | `review-changes` adversarial lens: state the check before the claim, on any negative | **Adopted** → `.claude/skills/review-changes/SKILL.md`, adapted to this repo's terser lens style and grounded in its own three catalogued instances |
| v1.22.0 | `templates/project-file.md` "Active work" section | **Not applicable** — by the template's own instruction: delete it where the tool has auto-memory (Claude Code) |
| v1.23.0 | `audit-context` Step 4 placeholder skip | **Already in force** — global skill current |
| v1.23.0 | Adopter action: mark placeholders with `<!-- placeholder -->` | **Deferred** to the next `audit-context` run. 0 paths marked here today, and a marker is only meaningful against a live findings list — marking speculatively is how a real break gets labelled intentional |

### The v1.22.0 adopter action was the substance, and it was not a no-op

The framework's own changelog measured **this repo** as
`26 ran: 12 pass, 9 fail, 5 error, 3 malformed`. Re-measured 2026-08-12 after
commit `6a96271`'s repairs plus today's:

```
ran 25 of 38 annotations — 25 pass, 0 fail, 0 error, 0 cannot-verify; 6 manual, 0 malformed
exit 0
```

**All 38 accounted for**, as the runner's reconciliation rule demands: 25 ran,
6 manual, 7 prose mentions inside code spans (6 in `memory/gotcha-log.md`, 1 in
`memory/project_session_2026_07_26.md`) — those are documentation of the syntax
and are correctly not extracted.

Three defects were real and are fixed:

- **Two multi-line annotations in `memory/stamp-contract-integrity.md`** — one of
  them twelve lines of embedded Python. An HTML comment whose `-->` sits eleven
  lines below its opener is MALFORMED and **had never run**. Replaced by
  `scripts/verification/check_content_length_populated.sh`, which follows the
  v1.22.0 writing rules (evidence not a verdict word, non-zero exit, explicit
  `CANNOT VERIFY` when the box is unreachable). First run: all six filters
  2,802/2,802 — NexusMind#300 still fixed.
- **One multi-line annotation** in `memory/corroboration-feature-hypotheses.md`,
  collapsed to one line.
- **One ERROR that was not a defect**: the LD#92 DiD check is a source-clustered
  bootstrap taking ~50s against the runner's 30s default. Verified correct
  (exit 0, `D3_pct2.3 80 80 -1.119 [-1.61, -0.61]`) and annotated in place with
  its `VERIFY_TIMEOUT=120` requirement, so a future default run does not read a
  timeout as a broken claim.

### Also folded in: v1.21.0

Triaged 2026-08-11, nothing adopter-facing — the `install-global-skills.sh`
release guard (maintainer tool), `templates/release.md` Step 1 (we publish no
package), `templates/coordination.md` (we have none), one `docs/GUIDE.md`
sentence, and two stamp bumps. Recorded here so the frontmatter can carry only
the current reconciliation.

---

## v1.19.0 + v1.20.0 (both released 2026-08-10) — triaged 2026-08-11 via `/update-drift`

**4 adopted, 1 declined, 3 not applicable, 6 already in force.**

**ADOPTED.** `review-changes` gained v1.19.0's Step 1.5 structural pre-check, the
`Unclassified` naming rule + never-omit report slot, and the guarantee-lens
invariant — every file the guarantee lens names must tier HIGH.
`tests/unit/test_normalization_invariant.py` was MEDIUM under `tests/**`, so a
change weakening the very pin that caught NM#161/#205 would have skipped the lens
that exists to catch it; it is now listed in HIGH.

`test-verify-memory` gained the `CANNOT VERIFY` disposition, its ordering rule,
and an 11th fixture. Load-bearing here because **7 of ~39 verify commands in
`memory/*.md` are host-dependent** and b650-gpu is routinely powered off, so they
read FAIL on every run.

Step 1.5 was **verified by execution** over 382 tracked `.md` files: 2 violations,
0 false positives, both genuine data loss — a `|r|` header in
`filters/cultural_discovery/v5/calibration_report.md`, and a 4-cell row in
`memory/cross-repo-prioritization.md` whose dropped cell was a staleness caveat
that rendered nowhere. Both fixed in the same pass.

**DECLINED** — v1.20.0's gotcha-log Promoted table + `Occurrences` column. This
repo has no Promoted table: promotion targets `CLAUDE.md` § *Working rules*, and
the rate is already carried in prose ("8th occurrence 2026-08-11, four
self-inflicted") plus the per-shape catalogue table in `memory/gotcha-log.md`. A
fourth-column table would be a second counter over the same events — exactly what
the framework itself declined for its own #38 Step 1 tally.

**NOT APPLICABLE** — `physics-tests/` disclosure (no such surface); `.gitignore`
`/memory/` anchoring (`memory/` is tracked here, no ignore pattern);
`tests/lint/skill-sync.sh` (maintainer infra).

**ALREADY IN FORCE** — the v1.20.0 session-start row; the memory-index "not
auto-loaded" correction (this index never claimed it); `audit-context` Step 1,
`curate` Step 2, and both `install-global-skills.sh` fixes — all verified
byte-identical to the **v1.20.0 tag**, not merely to the clone's HEAD, which sat
4 commits ahead on an unreleased #33 installer guard that was deliberately not
triaged.

## v1.18.0 (2026-08-09) — already in force

Stamp bumped to match reality. Its only change is the `update-drift` skill, which
is user-global and was already installed. Nothing in the repo needed to change —
the stamp was understating what was installed. v1.16.x and v1.17.0 reviewed in the
same pass, no adopter action outstanding.

## v1.16.1 / v1.16.2 / v1.17.0 — adopted 2026-08-08, verified by content

Both global skills byte-identical to the upstream tracked copies (`diff`, plus
`install-global-skills.sh --check` clean).

- **v1.16.1** — the `review-changes` adversarial-lens contradiction does **not**
  affect this repo's copy, which is re-mapped and already carries only the
  consistent half plus a concrete-failure requirement; nothing to port. Its
  `curate` Step 0.6 dual-path fix is a **no-op here** — this repo keeps no
  `hypothesis-log.md` at either path; hypotheses live in per-topic memory files.
- **v1.16.2** — example rename only, no action.
- **v1.17.0** — the gotcha-entry length rule. The entry template it added is now
  in `memory/gotcha-log.md`, adapted to that file's `##` heading level and marked
  NEW-ENTRIES-ONLY (the log is ~2,000 lines and predates the rule).

Declined: nothing.

## v1.15.1 (2026-08-06) — adopted 2026-08-07

A patch to the `audit-context` skill only; no template or memory-layout change.
The global skill already carried the new Step 4 rules (three-section output,
extension whitelist, rung ordering), so only the stamp was behind.

## v1.15.0 (2026-08-06) — adopted

Established the skill-scope split that still governs (see `CLAUDE.md`
frontmatter). Declined: nothing.

---

## Standing caveat on the stamp

**The stamp records which surfaces were reconciled — not that any behaviour
changed, and not that a skill has since been run.**
