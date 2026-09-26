# Gotcha Log

*Newest-first, dated entries. **One standing section lives at the BOTTOM**: [`## Mechanized`](#mechanized) — the destination for `/review-changes` Step 3.1, where a review finding that became a deterministic check is recorded. It is named here because nobody scrolls to the bottom of this file.*

*⚠️ **Entries dated before 2026-09-01 live in [`gotcha-log-archive.md`](gotcha-log-archive.md)**, verbatim (moved 2026-09-24, #163). The unreachable-mechanism catalogue stayed here. For a recurrence match, grep both: `grep -n <term> memory/gotcha-log*.md`.*

## A NOTIFICATION FOR WORK I DID NOT REMEMBER — AND THREE BATCHES THAT WERE NEVER LAUNCHED (2026-09-25)
**Problem**: Background-task notifications arrived for "NR re-judge" judges while my context held no record of the Nature
recovery audit, ruling NR-1 or the re-judge. I told the owner twice that the audit had not started. Git showed it had
(commits at 18:45–19:00), and 3 of its 8 batches (A06/B01/B02) had never been launched, so the run would have waited forever.
**Root cause**: The session lost its record of an hour of its own work. I answered from context instead of from artifacts.
**Fix**: When a notification names work you do not remember, read `git log`, the evidence dir and the task outputs FIRST,
and say the correction plainly. Reconcile "launched" against "expected" by grepping task outputs for each batch's input
path; a batch with no task was never started.

## A PERCENTILE BOOTSTRAP PRINTED "0 [0, 0]" AND I WROTE "NONE VIA THE PROBE" (2026-09-25)
**Problem**: The NR miss audit's analyse.py reported 0 missed stories via the probe with interval [0, 0] (0/100 judged),
and a commit said "none via the probe". Wilson allows up to ~3.7% of 1,487/week, i.e. ~55/week.
**Root cause**: Resampling a stratum with zero positives always yields zero, so a percentile bootstrap is degenerate there.
**Fix**: For zero (or all) positive strata, report N × Wilson bounds and say "none OBSERVED". Corrected in both READMEs.
The claim-shapes `zero-width-interval` check reads JSON artifacts, not printed tables, which is why it did not fire.

## THE OWNER JUDGED MY SUMMARIES, NOT THE ARTICLES (2026-09-25)
**Problem**: In the band audit's owner check, my one-line gloss of a Nigerian pardon omitted "the use of human parts for
rituals", and in the next check an excerpt I cut stopped before the pension amount the story turned on. Both flipped
the owner's call once the full text was shown.
**Root cause**: A summary is a second instrument between the article and the owner, and it drops the detail that decides.
**Fix**: Owner checks show a faithful translation of the full opening text (or the whole text when short), never a gloss.
When a call rests on a detail the excerpt might have cut, show the rest before recording.

## A CLAIM-SHAPE CHECK WHOSE ONLY CALLER RUNS AT SESSION EDGES LET A FAILING COMMIT LAND, AND A WHOLE SESSION LEFT NO RECORD (2026-09-25)
**Problem**: `f7119a6` (2026-09-24 20:51) added `docs/evidence/2026-09-24-thriving-adjudication-full/merge.py`,
which reads the 25.1×-design-weighted `labels_v84_merged.jsonl`, prints an agreement rate and
move counts, and carries no `# design-weights:` line. `check_claim_shapes.py` goes red on exactly
this, and stayed red for ~13 h through 14 more commits. `/curate` found it. That same 09-24 run
also wrote no session file and no index row, so the index stopped at 2026-09-22 while $0.78 of
oracle spend and 553 relabels happened.
**Root cause**: the check's callers are a `verify:` annotation in `memory/MEMORY.md` and its own
unit tests. Nothing runs it at COMMIT time (`.githooks/` holds only `commit-msg`). It is the
"a command with no caller at the moment it matters" shape (see the 2026-09-17 entry *I replaced
a decaying sentence with a command, and gave the command no caller*). A fast run of small
commits never reaches a session edge, so neither the check nor the session record fired.
**Fix**: declared the line in `merge.py` (the output is a per-row relabel; the printed figures are
sample quantities); 26/26 clean after, red before. The session record was rebuilt from the commits:
`project_session_2026_09_24_adjudication.md`. **Open, owner's call:** add `check_claim_shapes.py`
to a pre-commit hook. It has to run on staged `docs/evidence/**.py`, and it was never measured
for speed.

## A GUARD THAT BORROWS ANOTHER GUARD'S CONSTANT IS MEASURING THE WRONG QUANTITY (2026-09-22)

**Problem**: `fit_normalization.py`'s NexusMind#205 bias check hard-errored on
`sample_min > MAX_NORMALIZATION_RAW_MIN`. That constant is the **loader's** bound, and the
loader applies it to `raw_min`. Reusing it for `sample_min` silently turns a **bias** test
(is the sample's floor far above the op-point?) into a **density** test (did the sample
happen to reach 4.5?), because the distance it allows is `4.5 - op_point` — a number that
shrinks to nothing as a filter's op-point approaches 4.5 and goes NEGATIVE above it.
**Root cause**: the guard measured an ABSOLUTE position where the thing it stands for is a
RELATIVE distance. Its own comment recorded the premise — *"no false-block possible for any
real op-point (3.75/4.0)"* — which was true in July 2026 and expired when #102 moved a filter
to 4.5. ⭐ **The tell nobody looked for: at op-point 4.5 the guard could not be SATISFIED by
any correct fit.** The population is filtered AT the op-point, so its minimum is always above
it. A guard with no passing input is not strict; it is broken, and it reads as strict.
**Fix**: `MAX_SAMPLE_GAP = 0.5`, its own name, tested as `sample_min - anchor`, in the fitter
and the invariant test together (llm-distillery#154, owner-ruled option 1).
⛔ **Two things the fix taught that the issue had not:**
1. **It is NOT "unchanged at the op-points it was written for".** A flat 0.5 is *stricter*
   below 4.0 (nature_recovery 3.75: 0.75 → 0.5; solutions 2.25: 2.25 → 0.5), identical at
   4.0, *looser* above it. All three directions are now pinned by tests. **When you replace
   an absolute bound with a relative one, every op-point moves — enumerate them.**
2. **Deleting the advisory tier left the opened band SILENT.** The old code errored on every
   gap at 4.5; the new one admits everything under 0.5 and said nothing. A sample drawn from
   *enriched* output starts at the enrichment bar (raw 4.794 for v8) — gap 0.294, under the
   limit, missing 13% of the span, which is #205's literal root cause. Replaced with a
   span-relative advisory. ⭐ **A loosening's blast radius is the band it opens, not the case
   it was written for.**
⚠️ **The proof of the deploy-path branch lived only in a scratch directory** until review
said so; it is now `tests/unit/test_fit_normalization_guard.py`, running the real CLI.

## THE SAME TAUTOLOGY, TWICE, PAST THREE WARNINGS WRITTEN FOR IT (2026-09-22)

**Problem**: published *"60.0% (1,786/2,976) of v8's surfaced rows clear the normalized 4.0
enrichment gate"* as a **recomputation that corrected** the retracted 60.4% from 202 rows.
It corrects nothing. Both are the same identity: the CDF is fitted on those very rows and
the normalized scale is `10 × CDF`, so *"above normalized 4.0"* is *"above this sample's own
40th percentile"* — ≈60% by construction for any percentile-normalized filter.
**Root cause**: ⛔ **a bigger sample felt like a better measurement.** The defect was never
the sample size; it was that the quantity is not a function of the model. Re-deriving it on
15× the rows reproduced the tautology at higher confidence.
⭐⭐ **THE KEEPER: this gotcha log already had the entry, dated 2026-09-08, and two more
surfaces carried the warning** — `docs/RUNBOOK.md`'s Phase E section and the v8 package's own
`STATUS.md:149` (*"in-sample and near-tautological … read it as shape, not as a
measurement"*). **Three written warnings, all in files the task routes you to, and the
session read none of them before recomputing.** A gotcha entry is not a guard: it fires only
if someone opens it, and nothing made anyone open it.
**Fix**: quote the **effective raw bar** (4.794 against op-point 4.50) — the transferable
quantity — and, for a share, measure on cycles the fit did not see, which is exactly what
makes `uplifting v7`'s 40%-un-enriched real (82 cycles, 18,041 surfaced, out-of-sample).
⚠️ The parity argument built on it was the casualty: it set an identity beside a measurement,
and the agreement to 0.01pp read as corroboration. *`feedback-predict-the-range-first` names
this tell: "about 60%" was predictable from the gate's definition alone.*

## A TEST THAT PLANTS ITS DEFECTS IN THE REAL TRACKED FILE (2026-09-22)

**Problem**: a `timeout`-killed pytest run left `experiments/registry.jsonl` **corrupted in
the working tree** — `EXP-001`'s `spend_usd` deleted and its `decision` set to
`probably-fine`. Five suite failures followed, in a file nothing in the diff touched, and
they were nearly read as pre-existing breakage.
**Root cause**: `tests/unit/test_experiment_registry.py:16-26`'s `run_against()` writes its
fixtures **into the committed registry** and restores in a `finally`. A `finally` does not run
when the process is killed, so any interrupted or concurrent run leaves planted defects on
disk — in a tracked data file `CLAUDE.md` routes *"did we ever test X?"* to.
**Fix**: restored with `git checkout -- experiments/registry.jsonl` (explicit path — a
parallel session may be live). ⛔ **Not repaired in code**: the test should copy to `tmp_path`.
⭐ **A test harness that mutates a tracked file is a hand-built population with a fuse on it**
— and the corruption is indistinguishable from a real regression at the moment you read it.

## A PREDICTION THAT COULD NOT FAIL, AND A SELECTION STEP THAT AMPLIFIED 4e-05 INTO A VERDICT FLIP (2026-09-17)

**Problem**: Two separate ways a pre-registered number carried less than it looked like it did.
(a) `H-DEV2` predicted *"`solutions v6` flips **at least as often as** the median filter"*. The
median filter flipped **0** and `solutions v6` flipped **0**, so the prediction passed with no
possible failing branch — the idea behind it (a lower op-point sits deeper in the score mass) got
no test at all. (b) In `EXP-039`, arm A reproduced `EXP-037` exactly on **4 of 5 seeds**; the fifth
changed its verdict count 0 → 1 because a median **4.3e-05** probability difference moved the
val-picked threshold **0.795 → 0.905**.

**Root cause**: (a) A comparative prediction against a statistic that can land on the floor has no
failing branch — it is the mirror of `feedback-prove-the-bar-is-reachable`: not an unreachable bar
but an **unmissable** one. (b) `pick_threshold` is a **selection** step, not a measurement: it picks
the lowest threshold meeting a constraint, so an arbitrarily small perturbation can select a
different operating point and move every threshold-mediated number with it.

**Fix**: (a) Predict an **absolute**, or name the value that would refute the prediction, and say so
in the pre-registration. (b) When a probe's output passes through a selection step, report the
selected value beside the metric — and do not read a stable metric as evidence of a stable decision:
in the same run **test recall was identical on all five seeds** across the GPU swap while the
flagged panel SET moved. Both recorded in `memory/hypothesis-ledger.md` (`H-DEV2`, `H-HD12`).

## A TIER RULE WHOSE WARRANT WAS AN ABSOLUTE NOBODY HAD ENUMERATED — TWICE, IN ONE CHANGE (2026-09-17)

**Problem**: `refcheck.py`'s new `docs/` tier assigned LIVE/FROZEN by directory, warranted
with *"every frozen entry is dated BY CONSTRUCTION"*. False.
`docs/decisions/framework-adoption-history.md` is undated, was edited the same day, is
routed into from `CLAUDE.md` twice, and carries the largest finding count of any single
frozen file — and the rule declared it *"never to be edited to satisfy this checker"*,
along with four more pointer targets and every undated index.

**Then the fix did it again.** Rule 3 became *"undated ⇒ live"*, warranted with *"an
undated file in a dated directory is an index or a running history"*. Also an
unenumerated absolute: it admitted **13 files of which 10 are frozen accounts** — six
verbatim copies of other repos' ADRs, two reports for a filter removed 2026-08-03 — worth
**21 findings, 7.7%** of the live total the promotion decision rests on. Depth-restricting
it to files sitting *directly* in the frozen directory leaves three, and the one arguable
member is named in the code.

**Root cause**: the tier is a claim about a POPULATION, and both drafts asserted it
without enumerating that population. Neither the 17 tests written to guard the tier nor a
full green suite could see it — a tier defect narrows the scan set, and a narrower scan
set reports FEWER findings, which reads exactly like a repo that got cleaner.

**Fix**: the rule is three tests, one of them computed from `CLAUDE.md`/`memory/MEMORY.md`
rather than hand-listed; the residue of each is enumerated in the code beside it; the
count of files reaching LIVE by override is printed in the report, because rule 2 makes
the tier a function of mutable text. Guard tests run the checker and read what it did —
the first pair were source-text greps, and three behaviour-changing mutants survived them.

⭐ **The transferable part is the process, not the rule.** Round 1 of `/review-changes`
found the first instance; round 2, scoped to the fixes, found the second. Two instances is
a CLASS, and the round cap's own remedy is a **census, not a third round**. Two ran: every
absolute about behaviour in the change's prose (3 more defects, all fixed), and every count
either tool prints against the population it is over (19 surfaces, both defects already
known). Full record: `docs/decisions/2026-09-17-refcheck-docs-tier.md`.

## I REPLACED A DECAYING SENTENCE WITH A COMMAND, AND GAVE THE COMMAND NO CALLER (2026-09-17)

**Problem**: `CLAUDE.md`'s footer asserted "the FOUR user-global skills were byte-identical to
the v1.40.0 reference install, 0 differing lines, when enumerated 2026-09-11". Six days later
upstream had shipped six releases and the installed copies had moved with them. The sentence
was false and nothing said so. I deleted it and pointed the footer at a new probe,
`scripts/verification/check_framework_stamp.sh`.

**Root cause**: the probe was invoked by **nothing**. Not `.githooks/` (which holds only
`commit-msg`), not CI (there is no `.github/`), not any skill. Its unit test is deliberately
hermetic, so a green suite cannot report drift in `~/.claude/skills`. The claim therefore still
depended on a human remembering to run a command — **the exact dependency the change was made
to remove**. Naming the caller would not have helped either: I had not named one.

**Fix**: a `<!-- verify: -->` block in `memory/MEMORY.md` naming the probe, executed by `scripts/verification/run_verify_annotations.py` (this repo's
implementation of `/curate` Step 0 sub-step 3). Proven in both directions, not read: it reports
`pass … 4 global skills byte-identical to v1.45.1`, and a seeded `FRAMEWORK=/nope` arm made the
runner print `CANNOT VERIFY` and exit 1.

⛔ **The generalisable form: replacing a claim with a mechanism is only half the work — the
mechanism needs a caller, and "it is a command now" is not one.** A command in a document is a
sentence with a shell prompt in front of it.
⚠️ **And `/curate`'s own `stampcheck()` is NOT this probe**: three skills, skipping
`review-changes`, so a green curate says nothing about the fourth. Two probes, similar names,
different populations. `scripts/verification/check_doc_claims.py:191` defines a third function
literally called `check_framework_stamp()`, which only asks whether two lines of `CLAUDE.md`
agree with *each other*.

---

## A TEST THAT PASSED FOR THE WRONG REASON, INSIDE THE TEST WRITTEN TO STOP A HAND-KEPT COUNT (2026-09-17)

**Problem**: round 1 of review found `N_WANT=4` hand-written beside a four-name `WANT` list —
the shape that reproduces upstream's original false PASS once the two disagree. I derived the
count and wrote `test_count_is_derived_not_restated` to pin it. Round 2 killed the test: a
mutant deriving the count from an unrelated literal list (`printf '%s\n' a b c d | wc -l`) left
**all 17 tests green**.

**Root cause**: the test asserted `"N_WANT=$(printf" in src` — a **spelling check** — and its
behavioural half exercised only the 4-of-4 happy path, where a literal and a derivation agree
by construction. The name claimed derivation; the assertions proved orthography.

**Fix**: the test now writes a variant of the script whose `WANT` carries a fifth name and
requires `compared 4 of 5 skills`, exit 2. A literal count prints `byte-identical`, exit 0, and
the test fails. Mutation-proven.

⛔ **The generalisable form: when a test's subject is "this value must FOLLOW that one",
the only test is one where they MUST DISAGREE if it does not.** A happy-path assertion cannot
distinguish a derivation from a coincidence, and `grep`ping the source for the fix's own
spelling is the weakest check that still looks like one — see `feedback-a-name-is-an-assertion`.
⚠️ Round 2 also found the condemned `diff | grep -c` construction reintroduced **six lines
below the comment condemning it**. Two recurrences of one class in one file triggered a
**census** rather than a third round: all 21 substitution/pipe sites enumerated at once, the
last live instance closed with an invariant.

---

## A SHAPE TEST INSIDE AN EXISTENCE-TEST DISJUNCTION — THE CONTROL COULD NEVER STOP FIRING, AND THE FIRST REMEDY DELETED THE EVIDENCE (2026-09-17)

**Problem**: `/audit-context` step 4 reported 3 references as `STALE PLACEHOLDER MARKER (the
path resolves)` — `data/raw/.processed_ids_<name>.json` and twins. They are correct references.

**Root cause**: `refcheck.py`'s STALE test asks "is this marked path actually THERE?" through a
disjunction of rungs. Every rung in it is an existence test except `rung3`, which is
`frag.startswith(STATE_DIRS)` — a **shape** test that no file system can falsify. Any
angle-segment path under a state directory therefore "resolved", always. The angle form is
*mandatory* for a variable segment, so the author had **no legal move**: marked → STALE,
unmarked → the angle branch again.

⭐ **THE PART WORTH KEEPING: THE COUPLING WAS ALREADY MEASURED, AND THE REMEDY CHOSEN WAS TO
DELETE THE EVIDENCE.** A comment in the same file, 2026-08-16: *"rung3 sits INSIDE the
STALE-PLACEHOLDER `resolves` disjunction, so adding a dir here makes any `<!-- placeholder -->`
on that dir fire STALE IMMEDIATELY — measured, findings went 1 → 4. The two mechanisms are
alternatives, never both: the three markers these dirs cover were removed in the same commit."*
The measurement was right and the conclusion was backwards. Removing the markers satisfies a
shape test that **cannot stop matching**, so it buys silence until the next time anyone writes a
state path — which happened four times, 2026-09-07..09-10, and would have recurred at every
future audit forever.

⚠️ **The generalisable form: when a check has no legal move, the defect is in the CHECK, and
"remove the thing it flags" is the remedy that guarantees recurrence.** `/audit-context` step 4
says to distinguish wolf-crying from residue before touching anything. The tell for wolf-crying
is not "it keeps coming back" — it is **"no input could make it stop"**.

⛔ **And the mirror, from the same skill: do not loosen without seeding what the loosening newly
permits.** Excluding rung 3 permits exactly one new case — a path angle-marked, under a state
dir, and really on disk. Rung 1 is tested first in the same expression and catches it. Seeded
both ways (`run.sh` 34/35) and both proven non-vacuous by mutation: 34 FAILS on the pre-change
code, 35 dies when rung 1 is removed. Fixed in `ad32356`; the obsolete comment was rewritten
rather than deleted, because a note that contradicts the code is worse than no note.

---

## I RAN THE WRONG CHECKER, BECAUSE THE SKILL NAMED THE UPSTREAM ONE AND WE HAVE A FORK (2026-09-17)

**Problem**: `/audit-context` step 4 gives a literal command rooted at
`~/repos/agent-ready-projects/tests/fixtures/reference-integrity/refcheck.py`. I ran it. It
reported **216 findings**, 113 of them `COLLISION` on bare basenames (`config.yaml` ×18). The
fork in this repo reports **23** on the same tree.

**Root cause**: `tests/fixtures/reference-integrity/refcheck.py` here is a genuine **fork**,
1,629 lines different, recorded as a deliberate partial adoption of v1.40.0 in
`docs/decisions/framework-adoption-history.md:145` — *"deferred to `/audit-context`, NOT silently
copied"*. It carries a doc-relative rung, a systemd-unit class, a rung-5 auto-memory extension
and a `GENERIC ARTIFACT NAMES` section that absorbs the collisions. The two programs answer
different questions.

⭐ **Two numbers from two instruments is the shape, and the DANGEROUS half is that both were
correct.** Neither run was broken. Had I reported "references regressed from 1 to 216" — which
was one sentence away — the reader's next move would have been to hunt a regression that does not
exist. ⛔ **A skill's literal command is an instruction about the FRAMEWORK's tree, not about
yours. Before running a named tool, check whether this repo re-mapped it** — the decisions file
is where declines and forks live, and `feedback-decline-reason-is-local` already says to grep it
by the feature's own name.

⚠️ Prior-audit numbers are only comparable if they came from the same instrument: the
"24 findings → 1" of 2026-08-27 is a **fork** number.

---

## I CAPPED A FILE AND SHIPPED NOTHING THAT HOLDS THE CAP (2026-09-17)

**Problem**: the always-loaded layer was over its soft budget. Attribution said the growth was
the auto-memory index (~370 B/day) and not `CLAUDE.md` (~19 B/day). I capped its 25 pointer rows
the way `CLAUDE.md`'s are, recovered 5,187 B, and reported the layer fixed.

**Root cause**: `check_index_budget.py --target pointers` reads `CLAUDE.md` **only**. So the cap
I had just applied to the other file was a one-time hand trim with no mechanism behind it —
precisely the state `CLAUDE.md` was in *before* #133, and at 370 B/day it refills in about a
fortnight.

⭐ **I caught it while writing the issue comment, not while doing the work** — the sentence
"remedy applied, not just diagnosed" would not finish honestly, because the diagnosis was
*a byte budget is an alarm and a cap is the mechanism* and I had shipped the alarm's remedy.
⚠️ **Writing the claim out for someone else is a cheap control that ran after the change instead
of before it.** Same shape as `feedback-articulating-is-not-applying`: the check is least likely
to be present right after you have been most articulate about needing it.

**Fix**: `--target pointers` now covers both always-loaded surfaces (its own extractor — the
auto-memory index is a bullet list, not a table, and reusing `_pointer_rows` would have returned
CANNOT VERIFY forever). Four tests pin the arms, including *absent is reported as unchecked and
never as a pass*. Mutation-proven: gutting the cap kills
`test_automem_row_over_the_cap_fails`.

⛔ **The cap is 400 and that number is BORROWED, not derived** — it is `POINTER_CARVEOUT_CAP`,
already in the file. A ratchet at today's max (437) would only say "do not get worse"; 400 has
precedent and bit one row, trimmed in the same change with its caveat verified present in the
target first.

---

## RECORDING A COMMIT HASH IN A FILE THAT IS PART OF THAT COMMIT, THEN `--amend` (2026-09-17)
**Problem**: Committed `EXP-038` with `experiments/registry.jsonl` recording `"commits":
["70555e2","32919c3"]`, where `32919c3` was the hash printed by that very commit. Then ran
`git commit --amend` to stage one more file. The amend rewrote the commit as `81e1498`, so
the registry at `HEAD` pointed at an object **no longer reachable from any branch** —
`check_experiment_registry.py` still passed, because it checks that metrics are traceable to
artifacts, not that a recorded hash resolves.
**Root cause**: a chicken-and-egg that reads as an ordinary two-step. A commit's hash covers
its own tree, so a file inside the commit can never hold that commit's hash in one step. I
worked around it by recording the hash *after* committing and then amending — which is the
one move that invalidates exactly what I had just written. `--amend` is the trap, not the
two-step.
**Fix**: record the hash in a **follow-up commit**, never an amend. The follow-up's own hash
does not need recording. Caught by re-reading `git log --oneline -3` after the amend and
noticing the hash had changed; nothing automated would have. ⭐ **Generalises past git: any
artifact that records an identifier derived from its own content cannot be written in one
pass, and every "just amend it" shortcut re-breaks it.** Same family as the 2026-09-04
`git commit --amend` orphaning the commit that produced a trained model — third time `--amend`
has cost something here.

## AN ORDERING PUBLISHED WITH NO BAND — AND THE GUARD CAUGHT IT, NOT ME (2026-09-17) [x2]
**Problem**: Wrote *"the new GPU agrees with CPU BETTER than the old one did — max |Δ| 0.1572
against 0.1956"* as the one-line answer of an evidence document. `check_claim_shapes.py`
failed it on `ordering-needs-band`, plus two `no-difference-range` failures on *"the `_meta`
stack fingerprint is identical in every dump"* and *"recall is identical on all three"*.
Three failures, all in a document I had just written carefully.
**Root cause**: both figures are a **max over 660 rows** — an extreme-value statistic, the
least stable thing a sample publishes — and the Ampere arm **can never be replicated**,
because the card is out of the machine. So there is no paired band and no way to get one. I
had the repeatability figure for the *new* arm (run-to-run 0.0000) and let it stand in for a
band across two arms, which it is not. ⛔ **This is the same defect as the 2026-09-05 "AUC
would have picked the wrong arm" entry** — a point-estimate ordering promoted to a finding —
so it is occurrence two, written by someone who had read that entry's lesson in the same
session's memory index.
**Fix**: state the ordering as *two single measurements*, say the Ampere arm is
unreplicable, and move the load onto the **flip counts**, which are counts and not
extreme-value statistics. ⭐ **The durable half: the guard is the control, and its failure was
it working.** I fixed the substance rather than the wording — the tempting move was to add the
word "band" until it went green, which would have left the claim exactly as wrong.

## TWO MEMORY SURFACES DISAGREED ABOUT SSH ACCESS; ONE WAS RIGHT ABOUT THE OUTCOME AND BOTH WERE WRONG ABOUT THE CAUSE (2026-09-17)
**Problem**: `memory/b650-gpu.md` said `ssh b650-gpu` *"works from situla and sadalsuud"*.
`CLAUDE.md`'s pointer row said *"works from the workstation, NOT from sadalsuud"*. Flat
contradiction, both always-loaded or near it, and neither referenced the other.
**Root cause**: `CLAUDE.md` was right about the **outcome** and wrong about the **reason**,
which is why nobody fixed it — it read as a known limitation rather than as a bug. The actual
cause was one word: sadalsuud's `~/.ssh/config` said `User jwasys` (the box owner's account)
instead of `jeroen`. The **key was correct the whole time** — sadalsuud's
`~/.ssh/b650_gpu.pub` fingerprint matches the `jeroen@sadalsuud-to-b650` entry in b650's
`authorized_keys` exactly. So a true-sounding limitation concealed a one-line fix for six
weeks, and `memory/b650-gpu.md` even carried the warning *"the account is `jeroen` (NOT
jwasys)"* three lines above the claim it contradicted.
**Fix**: changed to `User jeroen` and **proved the outcome** — `sadalsuud → b650` now returns
the hostname, `jeroen`, and the GPU — rather than declaring the config edit done. Backup at
`sadalsuud:~/.ssh/config.bak-20260917-b650user`. ⭐ **A "doesn't work from X" note with no
cause beside it is a bug report nobody triaged.** Record the mechanism or the note becomes
permanent; and when two surfaces disagree, the one that is right may still be right for the
wrong reason.


## A FAILED `git add` LET THE COMMIT RUN ANYWAY, AND HALF A REVERT WENT TO `main` (2026-09-12)
**Problem**: Ran `git add <8 paths>` where one was `tests/unit/test_refcheck_exit_contract.py` <!-- placeholder -->
— already staged as a deletion by an earlier `git rm`, so the pathspec matched **no file**.
`git add` printed `fatal: pathspec ... did not match any files` and exited non-zero. **It is
ATOMIC over its argument list, so none of the other seven were staged.** The `git commit` on
the next line ran against an index holding only that deletion, and I pushed it. For one commit
`main` carried `refcheck.py` **still holding the exit contract** with its tests deleted, under
a message saying the contract was reverted.
**Root cause**: Two, and the second is the real one. (1) A non-matching pathspec is fatal for
the WHOLE `git add`. (2) **I verified the commit by reading the message I had just written
rather than `git show --stat`.** `git status --porcelain` printed the eight unstaged files in
the same output block, immediately above the commit — the evidence was on screen, unread.
**Fix**: Follow-up commit carrying the other seven (no force-push; the bad commit was public).
⛔ **Put `git diff --cached --stat` between staging and committing, or `&&` them so the commit
cannot run on a failed add.** ⭐ **A deletion already staged by `git rm` must NOT be re-listed
in a later `git add`** — the commonest way to make a pathspec that matches nothing. ⭐ **Same
shape as the thing being reverted: I confirmed an outcome from the artifact that DESCRIBES it
instead of the artifact that RECORDS it.**

## A TRUNCATED HEADER READ IS NOT A HEADER READ — `| head -6` HID THE ANSWER (2026-09-12)
**Problem**: `/audit-context` and `/curate` both say to review the gotcha log by reading its
**headers**. I ran `grep -nE '^#{2,3} ' memory/gotcha-log.md | head -6` and read six. The entry
that would have stopped a day's wasted work — **`## I RE-ADOPTED A RECORDED DECLINE, IN THE
FILE THAT RECORDS IT (2026-08-29)`** — is at **line 307**, entry ~24 of 458. I then wrote an
almost identically-titled entry for the same defect without noticing its twin.
**Root cause**: `head -6` was there to keep output small on a 665 KB file. The step's whole
value is that headers are ~6% of the file and CAN all be read; truncating restores the cost
problem while looking like the cheap solution. **A capped read reports like a complete one.**
**Fix**: Read all 458 headers, or `grep` them for the term you are about to act on
(`grep -nE '^#{2,3} ' <log> | grep -i decline`) — which is one command and would have hit.
⛔ **Never `| head` a check whose purpose is completeness.** ⭐ The log had the answer, in the
right place, correctly titled, at a line number no truncation reached — the memory layer
worked and the read did not.

## I RE-ADOPTED A RECORDED DECLINE — THE THIRD TIME, AND THE ANSWER WAS IN THE FILE I WAS EDITING (2026-09-12)
**Problem**: `/audit-context` found `refcheck.py` had no `sys.exit` — a check structurally
unable to fail — and added a three-outcome exit contract with 6 tests and 4 killed mutations.
It was **recorded as Declined for this fork**, had already been re-adopted and reverted once
on 2026-08-29, and I made it occurrence three. I had appended my own entry to the TOP of
`docs/decisions/framework-adoption-history.md` the same session without reading further down.
**Root cause**: I verified the feature against the CHANGELOG, the installed skill and the
code. **A decline's reason is LOCAL — upstream does not know it — so no amount of reading
upstream can recover it.** Neither the review battery nor the mutations could help: both ask
*does the mechanism work*, and the defect was that it should not exist.
⛔ **Worse, my test asserted the unreachable branch and passed.** `test_coverage_incomplete_exit_2`
used a synthetic `findings=[]`; forcing `SIBS=[]` on the real repo still yields 22 findings →
exit 1, so exit 2 **cannot fire**. Four killed mutations on a branch with no reachable input —
*prove the bar is reachable*, violated inside the test written to guard it.
**Fix**: Reverted the block and deleted the test file. ⭐ **Before adopting anything into a
fork, `grep docs/decisions/framework-adoption-history.md` for the feature's OWN NAME** — the
file that records declines is not the file you are adopting from, and that is the whole point.
⭐ **And "this check cannot fail" is not automatically a defect**: a status nothing reads is a
mechanism with no caller, which is the same class. Fix it in the change that adds the caller.
**How it was actually caught**: `gh issue view 134 --comments`, during an unrelated sweep the
next day. The comment saying *"recorded so it is not re-attempted"* worked — one day late,
and only because someone opened the thread.

## A TEST'S NAME ASSERTED MORE THAN THE TEST CHECKED, AND THE MUTATION PROVED IT (2026-09-11)
**Problem**: Added a three-outcome exit contract to `refcheck.py` with six tests, including
`test_findings_are_deduplicated`. Four mutations run. Three killed. The fourth —
`len(set(findings))` → `len(findings)` — **left all six green**.
**Root cause**: The test asserted the EXIT CODE. Five duplicate findings and one finding
both exit 1, so the branch is identical either way; dedup only changes the printed COUNT,
which nothing read. The test was named for a property it never touched, and the name is what
a future reader would trust — `[[feedback-a-name-is-an-assertion]]`, now on a test function.
**Fix**: Rewrote it to capture stdout and assert `1 unique finding(s)`; M4 now dies.
⭐ **A mutation that survives is not a gap in coverage — it is a NAME that is lying.** Pick
each mutation to attack the property the test NAMES, not the line it executes; three of my
four attacked the code I had just written and could not have found this.
⚠️ **The ARTIFACT is gone — the exit contract and this test file were reverted 2026-09-12 as
the third re-adoption of a recorded decline** (see the 09-12 entry above). The lesson stands
and is why this entry stays; do not go looking for `tests/unit/test_refcheck_exit_contract.py` <!-- placeholder --> — deleted by the revert `222d6a6`, deliberately absent.
⛔ And note what the two entries say together: the test-name defect was found by MY mutation,
and the *branch should not have existed at all* was not — no mutation can ask that.

## TWO REVIEW LENSES, OPPOSITE ERRORS, AND THE TRUTH WAS NEITHER (2026-09-11)
**Problem**: Asked whether a guarantee on `filters/*/v*/model/**` could ever fire. The
adversarial lens reported **0 tracked files** and called the guarantee unreachable. The
doc-accuracy lens reported **32 tracked files** and called the pattern diff-visible. Both
were confident, both cited a command.
**Root cause**: Adversarial ran `git ls-files 'filters/*/v*/model/'` — a trailing slash with
no filename wildcard matches NOTHING whatever is tracked, so its negative came from a broken
instrument. Doc-accuracy counted correctly but stopped one question early. The 32 files all
belong to DEAD filters (`investment_risk/v2_*`, `uplifting/v4*`, `commerce_prefilter/v1`)
that predate `.gitignore:65`; **every current production filter has 0**. So the conclusion
"unreachable" was right on wrong evidence, and the evidence "32 tracked" was right with the
wrong conclusion.
**Fix**: Measured per-filter rather than in aggregate, and repointed the guarantee at
`scripts/deployment/*`. ⭐ **When two lenses disagree, do not pick the more emphatic one —
the disagreement is the finding, and the answer is usually a THIRD thing.** Note the shape:
one was a broken instrument (*prove it could have said yes*) and one was a correct number
under an unasked question (*a count is not coverage*), so the standard rules catch one each
and neither catches both.

## `git ls-files 'dir/'` WITH A TRAILING SLASH SILENTLY MATCHES NOTHING (2026-09-11)
**Problem**: `git ls-files 'filters/*/v*/model/'` printed nothing and exited 0 on a tree
holding 32 tracked files under those paths. Read as "nothing is tracked there".
**Root cause**: A git pathspec with a trailing slash and no filename component matches no
FILES; `git ls-files` lists files, so the empty result is correct and useless. It is the
zero-that-carries-no-information shape in a one-character form.
**Fix**: `git ls-files 'filters/*/*/model/*'`, or `git ls-files | grep '/model/'`.
⛔ **Before believing an empty `git ls-files`, run it once with a pattern you KNOW matches.**

## A HAND-EXTRACTED CONFIG DROPPED RULES WHILE ITS RECORD CLAIMED COMPLETENESS (2026-09-11)
**Problem**: Split a 546-line review skill into a generic half and a 163-line repo profile,
extracting the repo-specific rules by hand. Wrote "extracted from the fork" and "one
invariant was repaired" — implying the tiering moved intact. It had not: two rules were gone,
including `docs/evidence/** is HIGH when it ships a .py`, over a directory holding **58 .py
files**. A pre-commit lens found both.
**Root cause**: `[[feedback-hand-built-population]]` — hand extraction loses exactly what is
not in front of you, and nothing in the result looks wrong, so review cannot find it by
reading the artifact. The completeness claim made it worse: it told the next reader not to
check.
**Fix**: Restored both rules; the record now names the drop instead of asserting fidelity.
⭐ **When you move rules by hand, diff the OLD against the NEW by rule, not by reading the
new one — and never write "extracted" as though it were "copied".**

## A GREEN SUITE IS A STATEMENT ABOUT THE ORDER IT RAN IN (2026-09-11)
**Problem**: A new test file's fixtures were named `content_items_*.jsonl` in `tmp_path`.
`scripts/contract_check.py:276` globs `**/content_items_*.jsonl` from `path.parent.parent`,
which for a pytest `tmp_path` is the **session-shared basetemp** — so the harm fixtures were
read as producer collections, the measured delivery cadence collapsed, and
`freshness.input_stale` asserted error. Measured: the NexusMind suite's `NexusMind/tests/unit/test_contract_check.py` alone 52 passed;
harm tests first then contract_check **6 FAILED**, 58 passed; reverse order 64 passed.
**Root cause**: The full suite passed only because `c` sorts before `h`. Two sessions reported
"1,649 pass" and both were true. The victim was the exact test that exists to prove the check
does not false-red on a conforming producer row — so the thing measuring false-reds was itself
false-redding, invisibly.
**Fix**: Renamed the fixtures (`raw_items_*`); the name was never load-bearing since
`process_files` takes an explicit file list. ⭐ **A suite's pass is conditional on its
collection order. When a test writes files whose names another test GLOBS, the shared
basetemp is the coupling — and pytest's default alphabetical order hides it.**

## A PROPERTY INSERTED MID-METHOD ORPHANED THE REST BEHIND A RETURN, AND 16 TESTS PASSED (2026-09-11)
**Problem**: Adding a `stack_id` property to `HarmDetectorV1` placed it between
`self.version = ...` and the end of `_load()`. Everything after it — `_warn_on_stack_drift()`
and `self._embedder = SentenceTransformer(...)` — became unreachable code after the property's
`return`. `_embedder` stayed `None` and the next `batch_score` died on
`'NoneType' object has no attribute 'encode'`.
**Root cause**: Every one of the 16 unit tests substitutes a `_FakeDetector`, so not one
executes `_load`. The review had warned *"inference.py has zero test coverage"* in the same
session; the warning came true within the hour, inside the fix for a different finding from
the same review. No syntax error, no lint, no failing test.
**Fix**: Moved the property after `_load`; added `test_load_finishes_and_sets_the_embedder`,
which stubs only the heavy import and reproduces the defect exactly when mutated. ⭐ **A fix is
the least-reviewed code in a session, and a class whose tests all use a stand-in has no test
for the object itself. Smoke-run real data after editing a loader — that is what caught it.**

## A CROSS-REPO SYNC DONE FROM MEMORY PUSHED THE BROKEN FILE (2026-09-11)
**Problem**: `filters/common/harm_detector/v1/inference.py` is byte-identical in llm-distillery
and NexusMind. I copied it to llm-distillery, then found and fixed a defect in the NexusMind
worktree copy, and never re-synced. Commit `5681c66` shipped the broken loader to
llm-distillery `main` and I pushed it. Repaired in `bb5a52d`.
**Root cause**: The sync happened at the point in the session where the file was WRONG, and
"I synced it" survived in my head as a completed fact while the file underneath changed. The
existing rule (`feedback-diff-before-cross-repo-sync`) is about the deploy script; this was a
hand `cp`, which felt too small to verify.
**Fix**: `cmp -s` both copies after every sync, and re-sync after ANY later edit to either.
⭐ **A sync is not a copy until you diff it — and a file that is byte-identical across repos by
contract needs the diff run at the END of the session, not at the moment of copying.**

## A NUMBER THAT HAS BEEN COPIED HAS BEEN COPIED MORE THAN ONCE (2026-09-11)
**Problem**: The harm detector asserted the **0.2008** stack noise floor "was taken on exactly
this architecture (mpnet + sklearn MLP)". It is the Gemma-3-1B student's — `uplifting v7`, 660
held-out rows, b650 vs gpu-server's venv, CPU both sides. My first correction pass fixed the
module docstring and moved on. A grep found it in **five** places: two docstrings, a README, a
test docstring, and the `RuntimeWarning` text **emitted into production logs on every off-pin
load**.
**Root cause**: I worked from the review's finding list instead of grepping the files — the
same shape as the DeepSeek surface count (three, then six, then eight) one session earlier,
which is already a promoted pattern. A fabricated provenance is invisible to every control:
the number is real, the mechanism is real, only the population is wrong.
**Fix**: All five corrected to say this architecture's term is UNMEASURED. ⭐ **Enumerate a
claim's occurrences FROM THE FILES before correcting any of them, and when inheriting a
measured constant, carry whose it is.**

## `git checkout -- <path>` DESTROYED UNCOMMITTED WORK MID-MUTATION-TEST (2026-09-11)
**Problem**: Restoring a mutated test file with `git checkout -- tests/unit/test_x.py` reverted
it to HEAD — discarding a test I had written minutes earlier and not yet committed. The
mutation run then reported "restored: 17 passed" where 18 was correct, and only the count
caught it.
**Root cause**: The working rule bans whole-tree git verbs (`git add -A`, bare `git stash`,
`git checkout .`). This passed an explicit path, so it read as compliant — but the hazard is
not the tree, it is that `checkout` restores from HEAD and HEAD did not contain the new work.
**Fix**: Mutation-test with `cp file /tmp/bak` and `cp` back. Never use a git verb to undo an
edit to a file that has uncommitted work in it. ⭐ **The count in the "restored" line is the
control — read it, do not assume the restore worked.**


## [Short description] (YYYY-MM-DD)
**Problem**: What went wrong or was confusing.
**Root cause**: Why it happened.
**Fix**: What solved it.

     Write the lesson, not the narrative of the session that found it.

     ⚠️ The old "keep it to 2-3 lines" rule is WITHDRAWN (agent-ready-projects
     v1.25.0), and this log is the evidence that retired it upstream: 203
     entries, median ~1,200 chars, 35% over 1,500. The rule was unenforceable
     (a markdown source line has no length limit, so it could be met and
     violated at once) and enforcing it in characters would have flagged
     88-92% of entries across three independent logs. Upstream's verbatim
     adopter note: "If you have been ignoring it, you were right to."
     The real signal is ABOVE ~3,000 characters — 2-7% of entries across the
     logs measured (this one is the high end, 5.8%) — and at that size it belongs in a topic file or an ADR.

     STATUS AND RECURRENCE GO IN THE HEADING, NOT THE BODY (v1.24.0). Curation
     reads headings and opens a body only for an entry it is acting on, so a
     status buried in prose is invisible to it. Forms in use here:
         ## [RESOLVED] Title (date)
         ## [RESOLVED <date>] Title (date)
         ## [RESOLVED <date> by <ref>] Title (date)
         ## [<N>x <pattern-name>] Title (date)   <- recurrence
         ## [<N>x] Title (date)
     `[CORRECTED <date>]` is a second accepted status form (one entry uses it).
     Grep `^#{2,3} \[` to catch every status marker, not `[RESOLVED` alone.

     (agent-ready-projects v1.25.0. Note the heading level differs from the
     framework template: entries here are `##`, not `###` — and BOTH levels
     are in use, so any reader must match `^#{2,3} `. A `^### `-only grep
     misses 106 of the 203 entries here (re-derived 2026-08-12: 106 under `##`,
     97 under `###`); that exact bug shipped upstream in a
     v1.24.0 draft and was caught on this file.)

     NEW ENTRIES ONLY. Do not retrofit the existing log — a bulk rewrite of
     history is a separate, engineer-approved decision, and this file is
     1,995 lines precisely because it predates the rule.
-->

---

### A FIX IS THE LEAST-REVIEWED CODE IN A SESSION — I repeated a defect inside its own repair, three times (2026-09-10)

**Problem**: fixing a batch of review findings, three of my repairs carried the same shape as the
defects they were fixing: **a cheap check placed after expensive work**.

- `scaler.pkl` was unpickled **before** `_verify_hashes()` — the integrity check ran after the one
  file it was already loading.
- The `from sentence_transformers import SentenceTransformer` line sat **above** every integrity
  check, so an ensemble mismatch, a bad hash and a missing manifest were all unreachable until a
  ~7-second ML library had loaded — and unreachable *entirely* in a checkout without it, which is
  where CI runs.
- The empty-ensemble guard in `batch_score` ran **after** the embedding pass, so discovering there
  was nothing to score cost a full embed.

**Root cause**: each was written minutes after articulating the principle in a commit message. A
fix feels like a correction rather than a change, so it does not get the scrutiny a change gets —
and the framework's own review skill records that most introduced defects come from a previous
round's fixes.

**Fix**: all three reordered. **Verify before you load; refuse before you spend.**

**Same session, same shape, different axis**: I removed a **denylist** from the DeepSeek guard and
then wrote `load_split` treating any unknown `scope_verdict` as a negative, and a `band()` that
named `list` while falling through on dicts. Both are unbounded-negative enumerations. Both fixed
to allowlists.

**Lesson**: ⭐ **Re-read a fix as a change, at the tier of the file it lands in.** The two questions
that would have caught all five: *does this check run before the thing it guards?* and *does this
enumerate the good or the bad?*

### MY COUNT OF A SURFACE WAS WRONG TWICE IN ONE SESSION — three, six, then eight (2026-09-10)

**Problem**: guarding the DeepSeek call sites, I wrote *"the three entry points"* in a commit
message and an issue comment. An adversarial review lens found **six**. A test I then wrote to
enumerate the surface by grepping the tree found **eight**.

**Root cause**: I counted by recalling the files I had edited, not by asking the code. The two the
test added name the host only inside **commented-out** config with no dispatch function behind it —
latent rather than present, a distinction a hand-written list cannot carry and a grep can.

**Fix**: `test_every_deepseek_call_site_is_guarded` greps for the host, strips comment lines before
deciding a file talks to DeepSeek, asserts on live callers and **prints** the latent ones.

**Lesson**: ⭐ **Enumerate a surface from the code and ship the enumeration as a test.** A list in a
docstring is a snapshot of what you grepped once; the test is the inventory. ⚠️ And when correcting
a check that over-reports, narrowing the predicate to match the claim is legitimate — *loosening it
so the run goes green is not*. The tell is whether the narrowed predicate still fires on the real
case: uncommenting either entry puts that file straight back in.


### A NULL ARM THAT CANNOT FIRE IS NOT A CONTROL — read its FLAG RATE, not only its catch count (2026-09-10)

**Problem**: `EXP-037`'s threshold sweep concluded *"and the null is still 0.0"* — presented as
evidence the detector's catch was real across the whole sweep. It is not evidence anywhere above
0.65.

**Root cause**: the sweep table reported the null's **catch count** and omitted its **flag count**.
At thresholds ≥0.65 the shuffled-label arm flags **0 of 137 rows in all five seeds**, so a catch of
zero is arithmetically forced — the instrument could not have said yes. Worse, the direction
reverses: at 0.30 the null flags **22.4** rows against the real arm's **10.6**, so the defence
*"it fires at TWICE the real arm's rate"* — true at the pre-registered operating point — is
backwards at the low end of the same table.

**Fix**: retracted in the evidence README, with the null's flag column added beside the catch
column. The PRIMARY result is unaffected: at the pre-registered rule the null is genuinely
rate-advantaged and still touches the 9 zero times.

**Lesson**: ⭐ **This is the instrument rule — already in `CLAUDE.md` — applied to a CONTROL rather
than to a measurement, and that is the axis nobody checks.** A control is built to produce a
reassuring negative, so its own ability to fire is the last thing interrogated. **Report a null
arm's firing rate beside its catch count, always; a control with a zero firing rate is not a weak
control, it is not a control.** Found by an adversarial review lens, in a document whose own text
was congratulating itself on having a null arm.

### A DENYLIST OF KNOWN-BAD VALUES IS A HAND-BUILT POPULATION, AND THE VENDOR EXTENDS IT (2026-09-10)

**Problem**: `score_ollama_oracle.py` refused the literal DeepSeek model ids with
`args.model.startswith("deepseek-v4")`. On 2026-09-10 DeepSeek renamed the flash line;
`GET /models` began returning **`deepseek-flash`**, which does not match the prefix — so the one
id the vendor now advertises, the id anyone would reach for, walked straight past the guard. The
other two DeepSeek entry points had no guard at all.

**Root cause**: the guard enumerated the **bad** values, and that set is owned by someone outside
the repo. It was correct code on the right path with a passing rationale; nothing in the codebase
changed and it stopped working anyway.

**Fix**: `ground_truth/deepseek_models.py` — an allowlist of the one known-good alias, endpoint-aware
so a Gemini `--base-url` is passed through, wired into all three scripts before the key, the prompt
and any file I/O; subprocess tests plus two positive controls, both mutations killed.

**Lesson**: ⭐ **Enumerate what is ALLOWED. A denylist is a hand-built population whose maintainer
is the vendor.** ⚠️ And the review found the fix's own scoping was wrong: there are **six** DeepSeek
call sites, not three (`violence_promotion/v1/oracle.py` takes the model as a constructor argument),
and `urlparse().hostname` is fooled by a root-anchored FQDN — `api.deepseek.com.` reaches the real
API and skips the check. **Fixing the shape is not the same as covering the surface.**

### A GUARD WHOSE DOCSTRING NAMES ITS PURPOSE AND WHOSE PREDICATE IS NARROWER IS WORSE THAN NONE (2026-09-10)

**Problem**: `test_no_threshold_anywhere_in_the_inference_module` existed to stop a threshold
appearing in a stamp-only artifact, and its docstring said so: *"the thing that notices if someone
adds a convenient default later."* It walked `ast.arg` and `ast.Name`. The natural way to add a
threshold — `self.threshold = 0.85` — is an `ast.Attribute` whose `Name` is `self`, and it passed
in silence. So did a float knob under another name (`cut=0.85`). Its sibling matched **substrings**
against a hand-written forbidden list, so any newly-invented key name passed.

**Root cause**: the test was written from the shape I had in mind while writing the module, not from
the shapes an editor would reach for later. A green test on a narrow predicate proves the narrow
predicate; the docstring then sells it as the wide one.

**Fix**: widened to Attributes and to float defaults on `__init__`, and the key test now **parses
the returned dict** and requires exactly two keys, so an ADDITION fails rather than only a known-bad
name — the same denylist→allowlist move as the entry above, on the same day, in a file written the
same afternoon. Three mutations killed.

**Lesson**: **A guard is read as covering what its docstring claims.** When the two diverge the
docstring wins in every future reader's head, which makes an over-promising guard strictly worse
than an absent one. Mutate the guard with the shape a *later* author would write, not the shape you
just avoided.


### ⭐ ADDENDUM 2026-09-10 — the vendor renamed the model and the guard silently stopped covering it

**The rule above still holds. The guard enforcing it did not.** `score_ollama_oracle.py:416`
tested `args.model.startswith("deepseek-v4")` — a denylist of the ids that existed the day it
was written. On 2026-09-10 DeepSeek renamed the flash line: `GET /models` now returns exactly
**`deepseek-flash`** and **`deepseek-v4-pro`**. Both `deepseek-v4-flash` and
`deepseek-v4-flash-vision-exp` are **gone from the listing** (the former still resolves if sent).
So **the one flash id the vendor now advertises — the id anyone reading `GET /models` would
reach for — did not match the guard.** The other two DeepSeek entry points
(`score_deepseek_production.py`, `validate_deepseek_oracle.py`) had **no guard at all**.

⚠️ **THE SYMPTOM CHANGED, AND THE NEW ONE DOES NOT RAISE.** Re-measured today, matched prompt
and matched request shape:

| request shape | `--model deepseek-chat` | `--model deepseek-flash` |
|---|---|---|
| `max_tokens=16`, plain | content `'OK'`, 1 tok | content `''`, 16 tok all reasoning — the 2026-08-14 break |
| `max_tokens=4096`, `response_format=json_object` (**production**) | content `{"score": 7}`, **6** tok | content `{"score":7}` — **correct** — but **208** tok |

The empty-`content` parser break was a **truncation artifact of a small token budget**, not the
whole failure. Under the shape production actually uses, the literal id returns **valid JSON**
and merely bills **~34.7×** the output tokens. ⚠️ n=1 on one trivial prompt — direction and rough
magnitude only, **not a calibrated multiplier**; a real scoring prompt was not measured. A run
on the literal id now looks entirely healthy. Nothing downstream would catch it.

**Fix**: `ground_truth/deepseek_models.py` — an **allowlist** (`{"deepseek-chat"}`), endpoint-aware
so `--base-url` at Gemini's OpenAI-compatible endpoint is passed through, wired into all three
scripts and covered by `tests/unit/test_deepseek_model_guard.py` (subprocess tests that run each
script for real and assert it exits before loading a prompt or a key, plus two positive controls).
Both mutations killed: removing the guard from one script fails that script's test; widening the
allowlist fails all three.

**Generalisation**: ⭐ **a denylist of known-bad values is a HAND-BUILT POPULATION, and the vendor
gets to add to it without telling you.** Enumerate the one thing that is allowed instead. The
denylist was correct code, on the right path, with a passing rationale — it stopped working
because a name changed **outside the repo**, which is exactly the class the 2026-08-14 entry above
already named and did not defend against.

⛔ **And the "pin it instead" escape is CLOSED, not merely inadvisable.** There is no versioned
flash id to pin: `GET /models` carries no version, the response `model` field reads
`deepseek-flash` whatever you send (alias, new literal, or the retired `deepseek-v4-flash`), and
no response header carries one. **The served version is not observable through this API** — so
llm-distillery#157's proposed "stamp the served model" buys the **tier**, not the version, and
would not have distinguished V4 from V4.1.

---

## PEFT Adapter Resave Breaks Hub Loading (Feb 2026)

**Problem**: After running `resave_adapter.py`, `PeftModel.from_pretrained()` fails to load the adapter from HuggingFace Hub.

**Root cause**: `resave_adapter.py` converts keys from OLD format (`.lora_A.weight`, `score.weight`) to NEW format (`.lora_A.default.weight`, `score.modules_to_save.default.weight`). Hub loading via `PeftModel.from_pretrained()` expects OLD format and doesn't remap.

**Fix**: Never run `resave_adapter.py` before Hub upload. Keep adapters in OLD format. Local `inference.py` remaps at load time. Documented in ADR-007.

---

## Gemma-3 Auto Mapping Not Supporting gemma3_text (Feb 2026)

**Problem**: `AutoModelForSequenceClassification.from_pretrained("google/gemma-3-1b-pt")` fails because `gemma3_text` model type isn't in the Auto mapping (only `gemma3` for multimodal is mapped).

**Root cause**: `google/gemma-3-1b-pt` uses `Gemma3TextConfig` with `model_type: gemma3_text`, but transformers 4.55.3 doesn't register it in `AutoModelForSequenceClassification`.

**Fix**: Created `load_base_model_for_seq_cls()` in `filters/common/model_loading.py`. Falls back to building a custom `Gemma3TextForSequenceClassification` using `Gemma3TextModel` + `nn.Linear` head when Auto fails.

---

## Windows Safetensors Memory-Mapped Write Conflict (Feb 2026)

**Problem**: Saving a safetensors file on Windows fails if the same file is currently loaded (e.g., modifying adapter weights in place).

**Root cause**: Safetensors uses memory-mapped I/O. Windows locks memory-mapped files, preventing overwrite.

**Fix**: Save to a temp file first, then `os.replace()` to atomically swap.

---

## rsync dup() Errors on gpu-server (Feb 2026)

**Problem**: `rsync` fails with `dup()` errors when transferring files to gpu-server.

**Root cause**: Unknown — likely related to LXC container filesystem or Tailscale network layer.

**Fix**: Use `scp` instead of `rsync` for all file transfers to gpu-server.

---

## Training Data Dir Naming Mismatch (Feb 2026)

**Problem**: Training data directories don't follow a single naming convention, causing confusion when scripting.

**Root cause**: Organic growth. Some dirs use filter version from when data was scored (e.g., `sustainability_technology_v3`) vs the filter version being trained. Hyphenated filter names (investment-risk, cultural-discovery) keep hyphens in dir names.

**Fix**: Convention: `datasets/training/{filter_name}_{version}/` where `{filter_name}` preserves the filter's canonical name (including hyphens). Check actual dir names before scripting.

---

## Hyphenated Filter Names Break Python Imports (Feb 2026)

**Problem**: `import filters.investment-risk.v6.inference` fails — Python interprets hyphen as minus.

**Root cause**: Python identifiers can't contain hyphens.

**Fix**: Use `importlib.import_module("filters.investment-risk.v6.inference")` for hyphenated filter names.

---

## Pipeline is I/O-Bound, Not Compute-Bound (Mar 2026)

**Problem**: Instinct says "optimize model inference" (#24), but production logs show GPU scoring is only 12% of pipeline time.

**Root cause**: The NexusMind pipeline spends most time on pre-enrichment (HTTP-fetching full article text from source URLs) — 55% of wall time on big runs. GPU scoring does ~2K articles × 5 filters in under 4 minutes (~22ms/article). Story dedup (GPU embeddings) adds another 8%.

**Data** (2026-03-08, 1,949 articles × 5 filters):
- Pre-enrichment: ~16 min (55%)
- GPU scoring: ~3.6 min (12%)
- Story dedup: ~2.3 min (8%)
- Aegis export: ~3.3 min (11%)
- Cleanup/sync: ~4 min (14%)

**Implication**: On GPU, scoring is fast and not the bottleneck — pre-enrichment is. But GPU access is borrowed. Without it, scoring becomes the bottleneck: ~900ms/article on CPU × 1,949 articles × 5 filters ≈ 2.4 hours per run (vs 3.6 min on GPU). That's why #24 matters — it's not about optimizing today's pipeline, it's about surviving without the GPU.

---

## score_scale_factor Is Linear, Cross-Filter Normalization Is Not (Mar 2026)

**Problem**: Filters produce structurally different score distributions. Uplifting passes 62.8% of articles as MEDIUM+, nature_recovery passes 0.3%. The HOME tab uses `max(weighted_average)` across filters, so uplifting dominates. Articles open in the wrong tab (uplifting instead of recovery).

**Root cause**: `score_scale_factor` (e.g., 1.53 for nature_recovery) applies a linear stretch to compensate for calibration range compression. But the distributions are non-linear — most nature_recovery articles cluster near 0, and linear stretching doesn't help them. Meanwhile, calibration itself is fitted on enriched val sets (ADR-003/005), not production data, so the calibration ceiling reflects what the oracle saw in enriched data, not what's possible.

**Fix**: Replace `score_scale_factor` with percentile normalization (ADR-014). Non-linear monotonic mapping fitted from production MEDIUM+ data. Same pattern as isotonic calibration (ADR-008) but applied on the weighted average across filters, not per-dimension within a filter. Set `score_scale_factor` to 1.0 for all filters after deploying normalization.

---

## SCP Creates Nested Directories When Target Exists (Mar 2026, recurred Apr 2026)

**Problem**: `scp -r source/dir/ dest/dir/` creates `dir/dir/` nesting. Hit three times: filter directory, model directory, and nature_recovery v2 model copy from gpu-server.

**Root cause**: When the target directory already exists, `scp -r source/ target/` copies `source` INTO `target` rather than merging contents.

**Fix**: Always scp to the PARENT directory: `scp -r source/dir/ dest/` (not `dest/dir/`). RUNBOOK.md updated 2026-04-15 with correct patterns. Promoted to feedback memory.

---

## Git Bash Mangles Unix Paths in Arguments (Mar 2026, recurred Apr 2026)

**Problem**: `--remote-dir /home/jeroen/...` becomes `C:/Program Files/Git/home/jeroen/...` when passed through Python on Windows Git Bash.

**Root cause**: Git Bash's POSIX-to-Windows path conversion applies to command arguments that look like Unix paths.

**Fix**: Set `MSYS_NO_PATHCONV=1` before the command: `MSYS_NO_PATHCONV=1 PYTHONPATH=. python ...`

---

## Systemd Service Context Differs From Interactive SSH (Apr 2026)

**Problem**: Filter works when tested interactively on gpu-server (`ssh gpu-server "python3 ..."`) but fails when the NexusMind scorer systemd service restarts.

**Root cause**: The systemd service runs with a different environment than an interactive SSH session. Key differences: working directory, PYTHONPATH, HF_HUB_OFFLINE, PATH, and available GPU memory (other services may claim VRAM). Interactive testing bypasses these constraints, so "it works when I run it" doesn't guarantee it works in production.

**Fix**: Always test through the actual execution context after deploying changes: `sudo systemctl restart nexusmind-scorer && journalctl -u nexusmind-scorer -f`. Check the service's EnvironmentFile and WorkingDirectory in the unit file, not just interactive shell behavior.

---

## MAE Is Misleading for Needle-in-Haystack Filters (Apr 2026)

**Problem**: nature_recovery v1 had val MAE 0.54 — looks great. But in production, 98.6% of articles scored below 1.0. The model had zero discrimination. v2 has "worse" MAE (0.63) but dramatically better ranking (Recall@20: 0.70 vs 0.55).

**Root cause**: MAE treats all errors equally. When 95% of articles are noise with oracle WA ~0, predicting zero for everything gives low MAE. The model is "accurate" on noise but useless on the articles that matter.

**Fix**: For needle filters, use ranking metrics: Recall@k, NDCG@k, false negative rate on MEDIUM+. Documented in filter development guide (Issue 4). Overall MAE is still fine for balanced filters (uplifting, belonging, etc.).

---

## Memory Claimed "Shipped" But Feature Only Existed in Running Process (Apr 2026)

**Problem**: Agent memory can state a feature is "shipped and working" based on a point-in-time test during a session. If the feature lives only in a running process (not persisted to the deployed codebase), it disappears on restart. Future sessions that trust the memory never re-verify.

**Root cause**: Memory records a session observation as deployed state. There's no mechanism to distinguish "I tested this once" from "this is persistently deployed."

**Fix** (v1.9.0 self-verifying memory): Never write "shipped"/"deployed"/"live" in memory based on a session observation alone. Qualify: *"responded correctly during session — verify persistence after restart."* Include a verification command in an HTML comment so future sessions can check before trusting: `<!-- verify: curl https://endpoint | grep expected -->`. The `/curate` skill now scans for unverified state claims and runs verify commands automatically.

---

## [RESOLVED] train.py --output-dir Creates Nested model/model/ (Apr 2026)

**Problem**: `--output-dir filters/foresight/v1/model` saves adapter to `model/model/`. Then `--resume-from filters/foresight/v1/model/model` looks for `model/model/model/`.

**Root cause**: `train.py` appends `/model` to the output dir for the adapter save path. Both `--output-dir` and `--resume-from` do this, so the nesting doubles each time.

**Fix**: train.py now strips trailing `model` from both `--output-dir` and `--resume-from` before appending. Either path form works now.

---

## Prefilter Title/Description Unbounded in `_get_combined_text` (May 2026)

**Problem**: `BasePreFilter._get_combined_text` (`filters/common/base_prefilter.py:497-512`) slices the article body to `MAX_PREFILTER_CONTENT = 2000` chars, but `title` and `description` are appended in full. Regex evaluation cost (and theoretical ReDoS exposure) scales with the unbounded inputs.

**Root cause**: Content was assumed to be the only long field when the slice was added. RSS titles and descriptions are typically short in practice, so the gap went unnoticed.

**Fix (deferred)**: For the current threat model (RSS-sourced, no attacker-controlled feed), the exposure is theoretical — security-auditor classified as low-severity during the 2026-05-22 belonging ADR-019 review battery. If attacker-controlled feeds ever land in scope (raw user submissions, third-party aggregators with low input hygiene), add explicit slices on title/description in `_get_combined_text` (e.g. `title[:200]`, `description[:500]`). Surfaced by review-battery on belonging v1 ADR-019 migration (commit `ba6b7cb`).

---

## The unreachable-mechanism catalogue

⚠️ **`memory/working-rules.md` is CANONICAL for the occurrence COUNT and numbering** (14 as
of 2026-08-16). The table below is the shape-by-shape evidence and is **not** a second
running total — it was missing occurrences 11, 12 and 14 for two days while the rule's own
`<!-- verify: -->` passed, because that check compares `CLAUDE.md` against `working-rules.md`
and cannot see this file. Add new occurrences to `working-rules.md` first.

Moved out of `CLAUDE.md` on 2026-08-09 (context audit): the **rule** belongs in the
project file, the **evidence** belongs here. The rule is unchanged — name the caller,
then prove the outcome changed at the end of the run.

A mechanism that is present, configured and unreachable is this repo's defining failure:

| occurrence | shape |
|---|---|
| ducroq/NexusMind#284 | per-filter prefilters never ran in production — **six months** |
| llm-distillery#94 | a gatekeeper binding **0 times in 191,616 articles** |
| ducroq/NexusMind#281 | a gate that could never fire |
| ducroq/NexusMind#300 | the #93 `content_length` stamp computed then dropped — **0 of 50,605 rows**, and it was **five allowlists in series**, not the two first diagnosed |
| `filters/cultural_discovery/v6` | a `hybrid_inference` block and probe shipped into a package with **no inference module** — written the same day the other four were documented |
| 2026-08-07, two guards | **correct callers on the right paths**, both inert: one reverted by a later step re-sending the old value through a `COALESCE` merge (123 stored rows already carried the signature), one a complete no-op because a different commit point short-circuited before it — while its own comment asserted it was "the only point every source has in common" |
| 2026-08-09, the stage trap | the arXiv `Announce Type:` prefix is a **91.6%** detector on the collection corpus and **0.000** on NexusMind rows, because enrichment re-fetches the body between the two. Both are "production data" |
| 2026-08-09 evening, self-inflicted | 34 rows labelled `CANDIDATE_UNADJUDICATED` committed **inside** `datasets/adverse/`, the glob a planned #91 gate reads as curated evidence. Not a mechanism that couldn't fire — **a population that would have been read by one that does.** Found by re-reading my own commit, not by a test |
| 2026-08-10, self-inflicted | a guard that "refuses to emit uncalibrated scores" and checks only that the calibration file is truthy — a partial `dimensions` block passes it and the raw logits go through under a success line. Its own error message cited #98, the shape it missed. Found by a review lens, not by 270 green tests |

| 2026-08-12, **10th occurrence** | a `<!-- verify: -->` annotation twelve lines long, backing the NexusMind#300 "100% populated" claim. An HTML comment ends at its first `-->` on its own line, so the extractor never saw it and the claim went unchecked. **The file looked annotated** — which is the config-key smell one layer up: presence of the mechanism read as operation of it. Found by adopting the framework's own runner, not by review |

| 2026-08-15, **13th occurrence** | a framework **stamp bumped ahead of its content**. `CLAUDE.md`'s footer read v1.26.0 from 2026-08-13 while neither v1.25.1 nor v1.26.0 had been triaged — and the stamp is the drift check's only input, so every run reported "current" and examined nothing. **The only value in this repo that can turn its own checker off.** Two releases unreviewed, one carrying an explicit adopter action (a CRLF fix that made the table check examine no tables). Now probed |
| 2026-08-15, the audit's own instrument | `refcheck.py` stripped a **sibling** repo's name from a path and never the **local** one, so every self-prefixed reference went unexamined. Not a wrong answer — a silence. Found by reading a finding instead of dismissing it as residue |
| 2026-08-27, **caught pre-ship** | a **doc-relative rung** back-ported into `refcheck.py` and gated on `isabs(doc)` instead of *outside ROOT* — so it was disabled for every run of `run.sh`, the seeded harness whose only job is to prove the checker detects. The rung under test never fired while its own sensitivity suite reported PASS. **Not counted in the occurrence total: it never shipped.** Listed for the detection method — the assertion was written against the **rung label** (`[rung1b] ->`), not against the absence of a finding, which a never-extracted path also satisfies |
| 2026-09-05, **18th occurrence** | `check_claim_shapes.py` — the guard written *against* guards that examine nothing — carried `experiments` as a JSON scan root behind `endswith(".json")`. `".jsonl".endswith((".json",))` is **False**, so the root matched **0 files**, `experiments/registry.jsonl` was never scanned, and the `.jsonl` guard beneath it was **unreachable dead code**. Twin in the same file and worse: `_reads_field` accepted any non-docstring string constant, so deleting the **only** real weight read from `phase_c_outcome.py` still PASSED — the name survived in an error message and a JSON label, while the docstring claimed *mention is not use* was fixed. Third, aggregate: emptiness was tested across all roots at once, so losing three of four evidence directories took a check from 7 sites to 1 and still printed PASS. **A fix applied to one shape of a problem and named after all of them.** Found by `/review-changes` after 707 tests and every guard went green |
| 2026-09-05, **the fix as the mechanism** | the sibling shape, logged under *establish what it excludes* as its 22nd occurrence but belonging here too: a rewrite made to satisfy a new check moved the ordering verb onto a different physical **line** from its two numbers, so the per-line trigger stopped matching. The site was not qualified — it became **invisible**, the check re-ran green, and a published site count failed to reproduce. **After any edit made to satisfy a checker, confirm the site is still EXAMINED: count sites before and after, not just the verdict** |
| 2026-08-11 evening, **caught pre-ship** | a `solutions v6` re-weighting that moved +19.5pp across an absolute 4.0 — correct at its own layer, erased downstream by a percentile CDF, because the gate reads the *normalized* score. **Not counted in the occurrence total: it never shipped.** Listed because it is the first time reading the caller stopped the recommendation instead of explaining it afterwards |
| 2026-09-08, **caught pre-commit** | `EXP-030`'s stage-2 control was a **`print`, not an `assert`**, sitting inside a section headed *"they run in `compare.py` and assert, they are not claims in prose"* — and its wording was true in its first clause and false in its second, so 3,162 probe-estimate rows entered every section-2 statistic. **Not counted in the occurrence total: it never shipped.** Listed for what found it: an adversarial lens reading the control's sentence one clause at a time, after 762 green tests and six green guards |
| 2026-09-08, the **guard's expired enumeration** | `fit_normalization.py`'s NexusMind#205 hard tier compares `sample_min` against a literal **4.5** that IS `human_thriving v8`'s op-point, so at that op-point it is a sample-**density** test and refuses every honest sparse fit. Its own comment names the premise — *"no false-block possible for any real op-point (3.75/4.0)"* — written before llm-distillery#102 moved a filter to 4.5. **A guard that enumerates the values it was safe for has a premise that expires.** ✅ **RESOLVED 2026-09-22** — ruled option 1, now `sample_min - anchor > MAX_SAMPLE_GAP`; see the 2026-09-22 entry for the two things the fix itself got wrong. llm-distillery#154 |

The cultural_discovery v6 entry is the point of the whole list: **knowing this failure
mode does not prevent it.** Only running the check against your own work does.

The 2026-08-11 evening row is the first counter-example: the same check, run on my own
work *before* proposing it, converted a would-be occurrence into a negative result. One
data point, not a trend — but it is the only known way the list stops growing.

### A backwards index-slice silently duplicated a document — twice in one session (2026-08-21) [x2]
**Problem**: `s[:i] + new + s[j:]` where `i` and `j` come from `s.index(...)` on two anchors.
When the second anchor precedes the first, the slice is backwards: the first form duplicated
§1e–§1g of a plan (923 → 1,007 lines), the second produced an **empty** `old`, and
`s.replace("", new)` inserts `new` between **every character** — 38 KB → **16.5 MB**.
**Root cause**: no assertion that `i < j`, and none that `old` is non-empty. The second
occurrence happened ~20 minutes after fixing the first, on a section whose order I had myself
changed earlier in the session — the anchors were correct when written and stale when used.
**Fix**: before any two-anchor slice, `assert i < j`; before any `.replace(old, new)`,
`assert s.count(old) == 1` and `assert old`. Both corruptions were recoverable exactly
(uniform insertion → `"".join(s.split(new))`; duplication → drop the truncated copy), but only
because the damage was deterministic. **Prefer anchored `.replace()` with a count assertion
over index arithmetic.**

### A hand-keyed dict transposed two article IDs, so two training rows carried each other's rationale (2026-08-21)
**Problem**: six adverse examples were promoted into `datasets/adverse/uplifting.jsonl` with
per-row `why_adverse` text supplied from a hand-written `{id: (why, features)}` dict. Two IDs
from the same publisher were swapped, so the helpline article shipped the Travelodge rationale
and vice versa — including each other's normalized scores. Both rows carry
`training_use: HARD NEGATIVE`, so the text a future adjudicator reads was **confidently wrong,
not absent**. Found by the adversarial review lens, not by me.
**Root cause**: a mapping built by eye between two similar-looking opaque IDs
(`british_irish_independent_uk_5985bde5bb3a` / `..._a4fdcb129620`), with nothing coupling the
prose to the record it described.
**Fix**: assert an invariant that ties the text to its own row — each `why_adverse` now must
contain its record's `observed.normalized_weighted_average`, checked at write time. A
hand-built mapping needs a machine-checkable link back, not proofreading.

### `pkill -f "<pattern>"` killed the shell that carried the pattern (2026-08-21) [x4]
**Problem**: `pkill -f -- "-L 11435:localhost:11434"` closed the SSH tunnel *and* the bash
process running the command, which exited 144 mid-script and skipped the rest.
**Root cause**: the documented `pgrep -f` trap — the pattern appears in the invoking shell's
own argv — applies identically to `pkill`, which then kills it.
**Fix**: kill by PID from `ps -eo pid,args | grep -v grep`, or `ssh` the target and kill there.
The existing working rule says `pgrep -f` cannot answer "is it running?"; **extend it: `pkill -f`
cannot answer "stop it" either.**

### A pipe inside a code span silently deleted a table cell that carried a BLOCKING flag (2026-08-21)
**Problem**: an acceptance criterion written as `` `|student_raw − oracle_k_run_mean|` `` inside
a markdown table row parsed as 7 cells against a 5-cell table. GFM drops the excess, so the
row rendered without its last three cells — including `Blocking? = YES`. The criterion would
have rendered as non-blocking.
**Root cause**: GFM splits a row into cells **before** parsing inline content, so backticks do
not protect a `|`. It reads correctly in the diff and is wrong only when rendered.
**Fix**: escape as `\|` inside tables. Caught by `/review-changes`' structural pre-check, which
exists for exactly this; it is the one check that reads *structure* rather than content.

### A free-tier API key turned k=3 into k=1 and the run still looked successful (2026-08-23)
**Problem**: A Gate A run scored 15 rows × k=3 on Gemini and reported results. It had actually
completed 14 of 45 and 8 of 45 calls; **8 articles carried a single sample while the run was
labelled k=3**, so every per-article mean and spread was computed over a sample size nobody
had chosen.
**Root cause**: `gemini_api_key` in `secrets.ini` is **free-tier** and returns
`429 RESOURCE_EXHAUSTED` partway through any real batch. Errors were counted but the surviving
rows were written and summarised normally — a *partially populated* result set is
indistinguishable from a complete one unless something checks per-article completeness.
**Fix**: Use `gemini_billing_api_key`, now the script's default with the free-tier fallback
labelled aloud. The catch came from the `⚠️ N articles have fewer than k successful runs`
warning added to `score_ollama_oracle.py` hours earlier for an unrelated reason — **without
it the numbers would have been read as a k=3 measurement.** ⭐ *Generalises: an error count is
not a completeness check. Assert the shape of the result, not just the absence of errors.*

### `grep -rl <article_id>` matched three files that do not contain the article (2026-08-23)
**Problem**: Looking for an article's full text in production, `grep -rl` returned three
`filtered_*.jsonl` files. None of them held the article. Parsing and comparing the `id` field
found it in none of the three.
**Root cause**: The id appeared inside a **different row's** `nexus_mind_attributes` — the
Express Tribune "Poison on our plates" row carries it as a **cluster co-member** of "The
silent crisis on our plates". Near-identical titles, co-clustered: the centroid-inheritance
shape behind NM#188/#228/#278.
**Fix**: Parse and compare the `id` field; never accept a substring hit as a row hit. ⭐ *A
grep for a string is not a grep for a row — and in a corpus with cross-references, an id is
exactly the string most likely to appear somewhere that is not its own record.*

### `b650-gpu` resolves for ssh and not for anything else (2026-08-23)
**Problem**: `ssh b650-gpu` works; `http://b650-gpu:11434` fails DNS resolution, so a scoring
run against the box errored on every call.
**Root cause**: `b650-gpu` is an **SSH-config `Host` alias**, not a hostname. Its real address
is the Tailscale name in the `HostName` line.
**Fix**: `B650_HOST` in `scripts/score_ollama_oracle.py` now carries the Tailscale name, with
the reason in a comment. ⚠️ *If a name only ever appears after the word `ssh`, do not assume
anything else can resolve it.*

### A judge that scores everything zero looks perfect on the adverse set (2026-08-23) [x2]
**Problem**: `qwen3:14b` scored two known-bad class-A rows at 0.0 and 1.0 against production's
6.846 and 5.976. Reported as evidence the prompt already handled them.
**Root cause**: **No positive control had been run.** The same judge scores all three
no-regression *true positives* at 3.733 / 0.767 / 1.333 — it puts nearly everything in the
0–2 band, so getting the adverse set "right" costs it nothing and carries no information.
**Fix**: Run the positive control **before** reading the negative arm. `qwen2.5:14b` is the
usable instrument here — run-to-run spread 0.383 mean / 0.650 max against qwen3's 1.700 /
2.950. ⭐ *The standing rule is "prove the instrument could say yes"; this is the same rule
one step over — prove it can still say **no** to something good.* Model-specific, not a
property of local judges.

### A verification that scanned zero files reported CLEAN (2026-08-23)
**Problem**: To prove violence enforcement worked I searched the cycle's output for the 74
flagged article ids and got "0 present — CLEAN". It scanned **0 files**. The zero was guaranteed.
**Root cause**: The flagged files are named in **UTC** (`flagged_20260823_144622`) and the
filtered files in **local time** (`filtered_20260823_164812`). I globbed `filtered_20260823_14*`
against a 16:xx file. Two naming conventions in one directory tree, neither documented.
**Fix**: Re-ran with an explicit `rows scanned > 0` control printed beside the verdict. Every
negative needs a control proving the instrument could have said yes — and a *count of what was
examined*, not just the finding. 2nd occurrence of the 2026-08-09 entry above.

### A precision bar measured on the wrong population blocked a good gate for 26 days (2026-08-23)
**Problem**: `violence_promotion` sat in shadow from 2026-07-28 to 2026-08-23 waiting for
"precision ≥ 0.90". Measured: **71–86%** — a fail. Enforcing anyway was correct.
**Root cause**: The bar was computed over **all 5,882 flagged articles**, of which **99.6% never
reach a lens operating point**. It described articles no reader could ever see. The
decision-relevant population was **21 articles**, where the trade is ~10 junk removed against
~10 good lost — which ADR-023 answers in one line.
**Fix**: Judge a gate on the population where its errors reach someone. ⛔ And the threshold is
not the lever: among the 21 the scores interleave (top scorer 0.9988 is a false positive, a true
positive sits at 0.9546), so raising it shrinks cost and benefit together.

### "Aged out of retention" — but the 730-day archive had every one (2026-08-23)
**Problem**: Reported that 4 of 9 class-A articles had aged out and were unrecoverable.
**Root cause**: I checked `data/filtered/` (14-day window) and stopped. `data/archived/` holds
**19 GB, 17 monthly tarballs back to 2025-10**, and contained all four —
`tar xzOf data/archived/nexusmind_2026-08.tar.gz | grep <id>` returns 6 hits, one per lens.
**Fix**: **Absent from hot storage is not absent.** Search the archive before calling data lost.
Same shape as *establish what your source excludes*, one directory over.

### A stamp that is CONSTANT because its positives are deleted upstream (2026-08-23)
**Problem**: `_is_commerce` and `_is_obituary` are `False` on 100% of 25,122 rows — 1 distinct
value each. Reads like two broken stamps.
**Root cause**: Neither is broken. Each gate's positives are **dropped before persistence**, so
the saved population is the gate's negatives and nothing else. Constant *by construction*.
**Fix**: New status in `NexusMind/docs/ARTICLE_RECORD.md`: `CONSTANT-BY-CONSTRUCTION` — the field
is fine, the place it was measured is not. ⭐ **Corollary that cost us today: turning a gate ON
removes it from the record.** `_is_violence_promotion` had 2 distinct values only while in
shadow; enforcing it makes it constant-`False` too.

### Assumed today's date was one later than it was, and it reached a production config (2026-08-23)
**Problem**: Dated an evidence file, a GitHub issue body, two issue comments and a **production
config comment** `2026-08-24`. It was the 23rd.
**Root cause**: The previous session record was dated 2026-08-23, so I inferred today must be the
24th rather than reading the date I was given.
**Fix**: Corrected all five surfaces; sadalsuud's `date -u` is what caught it. In a project whose
memory is date-indexed, a wrong date makes evidence unfindable. Read the date, never derive it.

### An unsized bucket in a prose clause carried 85% of the volume (2026-08-24)
**Problem**: Predicted the block ledger's first flush at "~22,237 rows, ~42 MB". Actual:
**168,486 rows, 320 MB** — 7.6× low.
**Root cause**: The estimate enumerated and counted the gate-blocked classes, and disposed of
everything else in a prose clause — *"plus freshness and dedup rows"*. `freshness.too_old`
turned out to be **142,899 rows, 85% of the ledger**. The part I counted was nearly exact
(22,494 vs 22,237, **1.2% off**); the part I described in words was never a number at all.
**Fix**: Size every bucket against its own counter, or state explicitly that a bucket is
unsized and therefore unbounded. ⭐ **A prose clause inside a quantitative estimate reads as
though it has been accounted for and has not.** The decomposition only existed because the
prediction was pre-registered in `docs/TODO.md` before the deploy — without it, 320 MB would
have been a number with nothing to compare against, and the real defect invisible.

### Asserted a deployed SHA I had inferred rather than checked (2026-08-24)
**Problem**: Reported "sadalsuud is at `7f57708`". It was at `8eed8d9`, one commit behind, so
the box's copy of a research script cited the wrong issue number.
**Root cause**: I pulled to the box in the same command chain as one commit, then made a
second commit and pushed it — and carried the *intent* forward as if it were the state. The
pull had run before the second commit existed.
**Fix**: `git rev-parse --short HEAD` on the box before naming a SHA. **A push is not a
deploy, and a deploy earlier in the same session is not a deploy now** — this is
`feedback-verify-call-path` applied to my own reporting rather than to a gate.

### A fix for one defect introduced another, caught by asking why a test PASSED on the old code (2026-08-24)
**Problem**: Fixing the census's un-attributable reader count, I marked every shared leaf
name `RDRS-AMBIGUOUS` and suppressed its consumer finding. That silently dropped TRUE
findings: a shared count of **zero** is an upper bound on every field sharing the name, so
it proves absence for all of them.
**Root cause**: I treated "shared" as "unknowable" without asking what the shared number
actually bounds. The tell was there: one of my 15 tests passed against the OLD script too,
and I nearly logged that as "it's a control" instead of chasing it.
**Fix**: Only a NON-ZERO shared count is ambiguous. `test_shared_leaf_with_zero_readers_
still_raises_for_both` kills the over-suppressing mutation. **A test that passes against
the code you are replacing is either a control you can name, or a defect you have not
found yet — decide which, out loud.**

### A number derived from a rounded percentage, published as if measured (2026-08-24)
**Problem**: Wrote "`_post_enriched` sits on **44** of 145,301 rows" into NexusMind's
`ARTICLE_RECORD.md`. An independent `grep -c` over the same 72 files says **46**.
**Root cause**: The census printed `0.03`, I multiplied by the row count, and a *derived*
number entered a document in the same sentence shape as a *measured* one. Nothing in the
text distinguished them.
**Fix**: Counted it with a second instrument and corrected the doc, which now says the 46
was counted rather than read off the percentage. **If a number came out of arithmetic on a
displayed value, either measure it or print the raw count in the tool.**

### The tidied script and the tested script were not the same program (2026-08-24) [x2]
**Problem**: A probe worked in the scratchpad, was cleaned up for commit, and died on its
first real run with `ModuleNotFoundError: No module named 'filters'`.
**Root cause**: The scratchpad version carried `sys.path.insert(0, REPO)`; tidying it into
a well-structured module dropped that line. The committed artifact had never been run.
**Fix**: Ran the committed version on the box before citing anything from it. **Verifying
version A and shipping version B is the same defect as not verifying at all — and the
tidy-up step is exactly where it hides, because the change feels cosmetic.**

### An issue number guessed before the issue was filed (2026-08-24) [x2]
**Problem**: Wrote `llm-distillery#125` into a script docstring and a commit message. The
issue was created as **#130**.
**Root cause**: Filed the artifact before filing the issue, and guessed the next number
from the ones I had seen.
**Fix**: Corrected the docstring; the pushed commit message cannot be edited in place and
carries the wrong number permanently, so the follow-up commit is the correction of record.
**File the issue first, or leave the reference blank until it exists.**

### A one-line class selector picked the empty base class (2026-08-24)
**Problem**: `next(v for v in vars(mod).values() if hasattr(v, "EXCLUSION_PATTERNS"))`
selected `BasePreFilter` — imported into the module and carrying an EMPTY dict — instead
of the subclass that defines the patterns.
**Root cause**: `hasattr` tests for the attribute's existence, not for it containing
anything. The module namespace holds its imports as well as its definitions.
**Fix**: Select on the CONTENT (`"crime_violence" in ...`) and require exactly one match,
exiting otherwise. It happened to raise `KeyError` here; had the category been present but
empty, the probe would have screened on nothing and returned a clean-looking zero.

### A NEGATIVE-EXISTENCE PROBE MATCHED THE DOCUMENT ASSERTING THE NEGATIVE (2026-08-25)
**Problem**: Wrote a probe for "there is still no Gemini Batch call site" —
`grep -rqE '\.batches\b' --include=*.py …` — and it fired **CLAIM REFUTED** on its first run.
**Root cause**: The only match was `scripts/analysis/oracle_cost.py:178`, the banner line I
had written that same hour saying *"`.batches` appears nowhere"*. The probe found the
sentence claiming absence and read it as presence. A negative-existence check searches the
same tree that holds the prose about the absence, and prose is not excluded by `--include=*.py`
when the prose lives inside a `print()`.
**Fix**: Match a call *shape* rather than a name — `\.batches\.` needs the trailing dot a
real invocation has and the prose does not — plus an explicit exclusion of the analysis
script, then **seed-tested it**: planted `client.batches.create(...)` in a throwaway file,
confirmed CLAIM REFUTED, removed it. **A negative-existence probe must be seed-tested in
both directions; the false-positive direction is the one that discredits the probe, because
the next reader will "fix" the claim rather than the check.**

### A PRICE THAT WAS VERIFIED THREE TIMES AND COULD NEVER HAVE BEEN PAID (2026-08-25)
**Problem**: llm-distillery#103 spent three days deciding between oracles by comparing
DeepSeek's per-article cost against "Gemini Batch, ~$0.0018". Both rate cards were read
first-hand at the vendors, an outside contributor independently checked the arithmetic,
and the flip point was computed to four decimals. **There is no Gemini Batch API call site
in the repo** — `ground_truth/batch_scorer.py:819` and `scripts/score_ollama_oracle.py:266`
both call `models.generate_content`, the real-time endpoint, and `.batches` appears in no
`.py` file. Against the path that exists, DeepSeek off-peak is 1.74× *cheaper*, so the
conclusion was backwards for nine days.
**Root cause**: A price is a property of a vendor; **being able to pay it is a property of
your code**, and only the first one looks like a fact to be checked. Nobody grepped for the
call site because the number was not in dispute.
**Fix**: `scripts/analysis/oracle_cost.py` now prints the implemented-path column with a
banner saying the other one is unreachable. **Durable lesson**: `feedback-verify-call-path`
applies to *prices, rates and quotas*, not only to gates and stamps. Before comparing
against an option, name the function that would invoke it. A number can be correct,
independently confirmed, and still not be an option.

### A DEAD FIELD REPORTED AS A MEASUREMENT, AND IT HAPPENED TO BE RIGHT (2026-08-25)
**Problem**: Published "cache-hit 0% (measured)" and built a decision table on it.
**Root cause**: The run it came from used `scripts/score_ollama_oracle.py`, which reads
`prompt_cache_hit_tokens` into `_cached_tokens` at line 359 and then **never sums it, never
persists it into the result row, and never prints it**. The run logs contain no cache line
at all. There was no instrument; the 0 was the absence of one.
**Fix**: Requalified as unmeasured, then measured properly from a different log whose
instrument *can* report non-zero and did (1% mid-run, 0.34% total, n=3,641). **The trap is
that the dead field's answer was nearly right.** A wrong-but-close number produces no
symptom, so the only defence is the standing rule: before believing a zero, prove the
instrument could have said yes. Being lucky is not being right.

### A MID-RUN PROGRESS READING CARRIED FOR MONTHS AS A RUN TOTAL (2026-08-25)
**Problem**: "14% cache hit" was quoted as a project constant in `CLAUDE.md`'s pointer
table and in `memory/oracle-pricing-scheduling.md`, and used in every per-article cost
estimate since.
**Root cause**: `nr_v4_positives.log` shows the shape — its progress lines read
**14% → 7% → 5%** and its final total is **4.9%**. An early reading is computed over a
small denominator and drifts as the run proceeds. Someone quoted the first line.
**Fix**: The real number is structural and per-prompt: `build_prompt` inserts the article
into the MIDDLE of the template, so the prefix cache can only hit what precedes the
placeholder — a ceiling of 1.5% (`human_thriving/v8`) to 35.7% (`solutions/v6`). 14% is cd
v5's own ceiling, not a project property. Filed as #131. **Quote a run's summary line, never
a progress line — and when a "constant" varies 7× across subsystems, it is a per-subsystem
property that nobody has decomposed yet.**

### THE SHIPPED ARTIFACT EXITED 1 ON A CLEAN CLONE (2026-08-25)
**Problem**: Committed `scripts/analysis/oracle_cost.py`, ran it, cited its output in a
memory file, a commit message and a public issue comment. On a fresh clone it exits **1**.
**Root cause**: The DeepSeek batch log the whole analysis rests on lives under `datasets/`,
which is gitignored (`.gitignore:76` — and #97, article text in a public repo, is why it
stays that way). My working tree had the file; the repo never did.
**Fix**: Copied the two logs — **counters only, no article text** — to
`docs/evidence/2026-08-24-deepseek-token-counts/`, made the parser try both locations, and
**proved the clean clone now exits 0**. Third occurrence of this family in two sessions.
**A script is not shipped until it has run somewhere that only has what you committed.**
`git clone --depth 1 file://$PWD /tmp/x && cd /tmp/x && <run it>` is the whole test.

### Keyword mining for hard negatives was 92% wrong (2026-08-23)
**Problem**: Harvested 244 candidate false positives with multilingual regexes for four classes;
judged 100; **8 survived**.
**Root cause**: Most POW/remains/prisoner matches are war roundups that genuinely *are* violence
(*"103 POWs returned home — Russian drone strike kills 2"*). A keyword is a candidate generator,
never a labelled set.
**Fix**: Mine where the error is dense instead: FPs run **~50%** among articles that are flagged
*and* clear a lens op-point, vs ~8% among keyword matches.

### A COVERAGE TEST WRITTEN FOR ONE QUESTION, REUSED FOR ANOTHER — prefix vs exact (2026-08-25) [2nd occurrence of *a check that answers a NARROWER question*]
**Problem**: Building the register's `scope` column, I reused the coverage predicate
I had just written for the ghost check — "is this declared path observed, itself or
through a child?" — to answer "is this observed field declared?". The first run
reported **every one of the 31 `nexus_mind_attributes.*` lens fields as declared in
Contract B**, including the seven undeclared fields that are the reason the register
exists. It looked plausible: Contract B *does* declare `nexus_mind_attributes`.
**Root cause**: prefix matching is correct for the ghost direction (a populated object
never appears as its own census row, so a child proves the parent) and wrong for the
attribution direction (a parent declared as an open object says nothing about its
children). One predicate, two questions, and the wrong answer was **true for the other
question** — the 2026-08-14 shape exactly: a check that is correct forever about
something you did not ask.
**Fix**: `scope_of()` matches EXACT paths only and says so in its docstring;
`_observed()` keeps the prefix rule for ghosts. `test_declared_parent_does_not_declare_its_children`
pins both directions. ⭐ The tell was the same as last time: the wrong answer was the
*comfortable* one — "the contracts declare almost everything" is the answer you want.

### I EXPLAINED 78 TEST FAILURES AS "THE ENVIRONMENT" AND IT WAS THE WRONG INTERPRETER (2026-08-25) [x3]

**Occurrence 3 (2026-09-17)**: `python3 -m pytest` on the #158 change reported **13 failed, 6 errors**, and I relayed them to the owner as *"all ModuleNotFoundError … pre-existing and unrelated"*. `.venv/bin/python -m pytest` returned **0 failed**. ⛔ The diagnosis was RIGHT and that is what made it useless — an explained phantom baseline is a believed one. `.claude/review-profile.md` carries the warning **six lines above** the baseline number and I had not opened the file. Recorded there too, as its occurrence two.
**Problem**: `python3 -m pytest tests/unit` in NexusMind reported **78 failed, 123
errors**. I checked that none of the failures named my files, attributed the rest to
"this workstation's environment (missing deps)", and moved on. It was nearly a session
finding. In `venv/bin/python` the same tree is **1,457 passed**.
**Root cause**: I reached for an explanation that made the signal go away instead of a
test that would have made it fail. The evidence I *did* collect — `ModuleNotFoundError:
trafilatura` — was consistent with both "the environment is broken" and "I am not in
the environment", and I only looked for confirmation of the first.
**Fix**: `ls -d venv` before believing any suite-wide failure, and run the project's own
interpreter. ⭐ The general form: **an explanation that dismisses a signal has to be
tested at least as hard as the signal was.** A dismissal is a claim.

### I CALLED A DECLARATION DEAD IN THREE DOCUMENTS BEFORE READING WHAT IT SAID (2026-08-25)
**Problem**: The census's new top-level check reported `_corroboration` as declared in
Contract B and present on **0 of 164,572 rows**. I wrote it up as a live
declared-but-dead field — "either the declaration goes or the pop moves; the pop is
deliberate, so the declaration is the wrong half" — in a commit message, a TODO block
and a session record. Then I opened the declaration to delete it. Its description reads:
*"Intermediate field — consumed by scripts/main.py and re-emitted under
nexus_mind_attributes.{filter}.source_quality before JSONL write."* It was right, and
had been since it was written.
**Root cause**: two failures stacked. (1) I read the *measurement* (0 rows) and inferred
the *intent*, when the intent was written down one file away. A zero has at least two
explanations — dead, or never meant to appear — and I only priced one. (2) The
instrument genuinely could not tell them apart, because **the fact lived in prose**. A
`description` is documentation; a checker cannot act on it.
**Fix**: Contract B `1.18.0 → 1.18.1` marks the field `x-intermediate: true` (annotation
only — `x-` keywords are ignored by validators, so nothing validates differently), and
check A excludes marked fields from the ghost list while still printing them once;
hiding them would be the other failure. The right disambiguation was already available
and free: an intermediate has an **in-process reader** (`display_ranking._corroboration_boost`)
and zero persisted rows, where a corpse has neither. ⭐ **When a schema's prose states a
fact a checker needs, move the fact into the schema.** ⭐⭐ And: *0 rows* is a
measurement; *dead* is a conclusion — the gap between them is where the declaration's own
words were sitting.

### THE WATCHER MATCHED ITSELF AND WAITED FOREVER (2026-08-25) [5th occurrence of the pgrep rule]
**Problem**: A background wait-loop, `until ! ps -eo args | grep -q "[m]ain.py"; do sleep
10; done`, never exited. It held a deploy for ~20 minutes after the box had already gone
idle, and three separate "is it still running?" polls reported a process that was my own
waiter.
**Root cause**: the `[m]ain.py` bracket trick stops the grep matching *itself* — and does
nothing about the rest of the command line. The loop's own `echo "no main.py process
running"` put the literal pattern on its argv, so the watcher matched itself on every
iteration and could never terminate. The two other pollers matched it too.
**Fix**: `ps -eo pid,etime,comm,args | awk '$3 ~ /python/'` plus `systemctl is-active`,
which showed `nexusmind-cleanup.service` had been `dead` the whole time. ⭐ **The tell was
in the output from the first poll: the matching line began `bash -c until`.** A count of
matches cannot show you that the match is you — **print the line**. ⭐⭐ And note where the
rule was: it is in `CLAUDE.md`, in this log, and in `working-rules.md`, and I wrote a fresh
instance of it anyway. Knowing a rule and applying it at the moment you write the command
are different acts (`feedback-articulating-is-not-applying`).

### A CYCLE IS A WINDOW, AND MY VERIFIER TREATED IT AS AN INSTANT (2026-08-25)
**Problem**: The deploy verifier decided which lenses had written "this cycle" by comparing
each file's timestamp to the newest timestamp with `==`. Run against production it reported
**one** lens as current and five as stale — and had the deploy already landed, that is
precisely the output a successful pause of five filters would produce.
**Root cause**: a cycle writes one file per lens as each finishes, minutes apart —
2026-08-25's ran 17:10:29 → 17:17:46. There is no single cycle timestamp to compare
against. I built the population by an equality the data can never satisfy for more than one
member. This is `feedback-hand-built-population` in its purest form.
**Fix**: membership by window (2h; cycles are 4h apart and run ~1h20m, so they cannot
overlap). ⭐ **The reason I caught it is that I ran the verifier BEFORE the deploy, expecting
failure.** A checker you have only ever seen pass is indistinguishable from one that cannot
fail — and here the wrong answer was the *encouraging* one, which is the shape that ships.

### A VERIFICATION COMMAND THAT ERRORED AND PRINTED THE REASSURING BRANCH (2026-08-27) [2nd occurrence of *prove the instrument could say yes*, same day]
**Problem**: Checking that escaping the pipes in an evidence doc cleared the table
check, I ran `awk ... && echo 'silent (FIXED)'` inside a `$( ... )` with escaped inner
quotes. awk received a filename with literal quotes, failed to open it, printed nothing —
and the `[ -z ]` test read the empty output as success. **The report said `silent
(FIXED)` on a run that never examined the file.**
**Root cause**: An empty result and a failed run are byte-identical to `[ -z ]`. The
check had no way to distinguish "nothing to report" from "nothing happened", which is
the same defect as a grep over 0 files.
**Fix**: Capture the output and the exit status separately (`out=$(...); rc=$?`), print
both, and run a positive control in the same breath. Re-run: file clean, control fires,
repo-wide sweep 1 → 0. ⭐ **The tell was that I wrote the success string myself, in the
same command that was supposed to earn it.** A verdict that a command can print without
having done the work is not a verdict.

### `git archive HEAD` AS A BASELINE TREE — IT EXCLUDES EVERY GITIGNORED PATH (2026-08-27) [11th occurrence of *establish what a source excludes*]
**Problem**: To get a before/after baseline for the reference checker I extracted
`git archive HEAD` into a temp tree and ran the checker against it. It reported **240
findings against the real 1** — and for about a minute that looked like a catastrophic
regression in my own edit.
**Root cause**: `git archive` ships tracked files only. `datasets/`, `data/` and every
other gitignored path are absent, so the references that resolve against them cannot
resolve. **The baseline was not a worse version of the tree; it was a different tree.**
**Fix**: Baseline from the working tree with only the changed files reverted. ⚠️ And the
cheap copy tricks do not work here either: `cp -al` cannot hardlink across filesystems
(/tmp is tmpfs, the repo is on ext4) and my `|| cp -a` fallback then copied the repo
*into* the half-made directory. Swap the two files in place, run, restore, and
`md5sum -c` the restore. ⭐ This is the same shape as the 2026-08-24 keeper — *the
shipped artifact exited 1 on a clean clone* — approached from the other side: there,
gitignored evidence was missing from a clone; here I built the clone myself.

### THE HEADROOM FIGURE IS MEASURED AT EXACTLY THE MOMENT THAT HIDES THE GROWTH (2026-08-27)
**Problem**: I was one sentence from recommending we skip a second `CLAUDE.md` trim, on
the grounds that the file had moved "one byte in a full cycle" — a figure from that
morning's own write-up.
**Root cause**: That figure is **headroom at audit time**, and the file is trimmed to the
wall at each audit and then refills. Two audits both reporting ~45 bytes free describes a
file that grew by whatever the trim removed, not a file that did not grow. Measured over
25 commits: **35,094 → 39,955 bytes in 10 days, ~486/day.**
**Fix**: Measure the series, not the endpoint, before quoting a rate. ⭐ **A quantity
sampled only at the moment it is reset cannot show a trend, and it reads as stability.**
Filed as #133 with the routing-rule options.

### A VERBATIM MOVE RELOCATED A REFERENCE OUT OF ITS EVIDENCE (2026-08-27)
**Problem**: Rotating the oldest session entry from `memory/MEMORY.md` into
`memory/session-log.md` — byte-for-byte, as #123 requires — took the reference checker
from **1 finding to 2**. Nothing about the entry changed; `diff` on the moved text is
empty.
**Root cause**: `refcheck.py`'s cross-repo rung resolves `NexusMind/data/exports/aegis/latest/narrative_risk.json` by looking
for an unbackticked sibling-repo name in a **3-line window** around the reference. In the
index that window held other session entries naming NexusMind in prose. In the log the
same line sits between different neighbours, and the evidence did not travel with the
bytes. **A positional window is part of the reference's meaning, and moving text verbatim
does not move it.**
**Fix**: None applied, deliberately — the finding is real, the entry stays verbatim, and
loosening the rung to silence it would be fixing the control. Recorded in
`memory/session-log.md`'s header so the next rotation is not surprised. ⭐ **Second time
in one session that relocating text changed what a checker could see** — the first was
dropping a qualified path from `CLAUDE.md`, which exposed an unqualified twin underneath
that had been resolving to the wrong repo. **Both directions are the same lesson: a
reference's resolvability is a property of where it sits, not only of what it says.**

### I SUPPLIED A MECHANISM AND IT SHIPPED AS A MEASUREMENT (2026-08-27)
**Problem**: Reporting that a residual exposure had no instance in this estate, I added
that "a CI runner cloning siblings with `--depth 1` reproduces the case immediately."
Plausible, confidently phrased, and **false**. It was accepted by the framework
maintainer and shipped in a release note as *"a shallow or partial sibling checkout"*
before they ran it and refuted it.
**Root cause**: `--depth 1` truncates **history**, not the working tree — a shallow clone
has every file. `--filter=blob:none` fetches blobs at checkout. Only **sparse checkout**
removes tracked files from disk. I reasoned from "incomplete clone" to "missing files"
without cloning anything, in a message whose whole subject was the difference between a
measurement and a window.
**Fix**: Verified all three modes afterwards, on this machine: `--depth 1` → `is-shallow:
true`, **58 files present**; sparse → **58 tracked, 13 on disk**, a tracked file outside
the cone genuinely absent; `--filter=blob:none` **inconclusive here** (the local `file://`
transport ignored the filter — recorded as untested rather than confirmed). Corrected in
`docs/TODO.md`. ⭐ **The estate sweep itself survived, and only by luck of construction**:
I had checked `core.sparseCheckout` alongside the other three flags, so the finding rested
on the one mode that matters. **A superset check saved a conclusion whose stated reason
was wrong.** ⛔⛔ **The reusable half: a mechanism offered to a peer is load-bearing the
moment they act on it.** Inside this repo an unverified mechanism is a hypothesis and gets
a ledger row; sent across a repo boundary it arrives as a finding, with none of the
hedging the ledger would have forced. **Say "I have not run this" in the sentence that
offers it, or run it first.** See [[feedback-nothing-verifies-an-estimate]].

### A VACUOUS ASSERTION IN THE FILE WHOSE DOCSTRING FORBIDS THEM (2026-08-27)
**Problem**: `tests/unit/test_pointer_row_cap.py` shipped with
`assert "1 rows" in out or "38 rows" not in out`. Its own module docstring says *"each one
seeds the failure it claims to catch"*.
**Root cause**: the second disjunct is true whenever the output does not mention 38 — which
is almost always — so the `or` made the assertion unfalsifiable. **Proven, not argued**:
deleting the delimiter-row skip from the guard (the exact defect the test names) left the
test green.
**Fix**: seed three rows and assert `"3 rows"` exactly; the same mutant now turns it red.
⭐ **Caught by a peer's message about a defect in someone else's fixture** — an authored
fixture reporting 26/26 green with three assertions that could not fail. Not by writing the
test, not by re-reading it, not by the 361-test suite. ⛔ **The compounding detail: this is
[[feedback-articulating-is-not-applying]] firing inside the hour, in a file written to
enforce the opposite** — and the guard it tests was itself built to close a rule this repo
had just articulated. **An `or` in an assertion is a smell: it gives the test two ways to
pass and you only ever exercise one.**

⭐ **THE DISCRIMINATOR, from the framework maintainer running the smell against their own
fixtures: a disjunction in a PASS condition is the hole; in a FAIL condition it is the
opposite and is correct.** Their sweep found 3 hits, **all safe** — shell `[ a ] || [ b ]`
guards where the disjunction *widens* failure detection. So the lintable form is a Python
`assert A or B`, where the disjunction unambiguously **is** the pass condition; in shell
the two shapes are indistinguishable and a lint would be all false positives. They declined
to build the rule for that reason, which is the right call and is why this is a rule for
authors, not a check.

⛔ **Swept this estate with the detector SEEDED FIRST (a negative from an unproven detector
is worthless): 5 raw hits, 1 of them my own docstring quoting the old form** — a detector
matching its own documentation — **2 loose but genuinely falsifiable, and 2 UNCONDITIONAL:**

- `tests/unit/test_short_content_split.py:488` — `assert checked or True, "no live
  prefilters on disk"`, directly beneath the comment *"A pass with nothing checked is
  indistinguishable from a disabled test."* ⭐⭐ **The comment states the rule and the next
  line defeats it.** `or True` permitted exactly the case the comment names.
- `tests/unit/test_base_prefilter.py:280` — `assert "&amp;" not in result or "&" in
  result`, in a test named `test_html_entities_removed`. A **tautology**: `&amp;` contains
  `&`, so whenever the first disjunct is false the second is true. Measured: it passed on
  the decoded output, on the raw undecoded input, and on the empty string alike.

Both now pin measured behaviour and both mutants die (`checked` forced empty → red;
`sanitize_text_comprehensive` made a no-op → red). ⚠️ The other two hits were left: a
2- and a 3-way disjunction over message wording, loose but able to fail, and pinning exact
wording would trade a weak test for a brittle one.

### I CALLED A REFERENCE UNFIXABLE FOR WEEKS WITHOUT ONCE TRACING IT (2026-08-27)
**Problem**: ~~`NexusMind/scripts/research/nm188_mojibake_derived.py`~~ was the reference
checker's one standing finding, carried across sessions and repeatedly described — by me,
today, three times — as *"needing someone who remembers the experiment."* It needed no
memory at all. Ten minutes of tracing settled it.
**Root cause**: I treated *the file is absent* as the end of the enquiry instead of the
start. The sibling that DOES exist, `NexusMind/scripts/research/nm188_mojibake_invert.py`,
**names the missing file in
its own docstring** — as being in llm-distillery at commit `5d5467e`. That commit is real
and touches **only** `memory/corroboration-feature-hypotheses.md`. The script is in no
commit, under any path, in either repo: an uncommitted working file from 2026-08-17.
**Fix**: struck in the memory file per the `ABSENT_SPANS` convention, so it is counted as
asserted-absent rather than reported as a break, with the diagnosis and the surviving
method beside it; the misdirecting NexusMind docstring corrected (`946d6f0`).
⛔ **TWO DOCUMENTS DISAGREED ABOUT WHICH REPO HELD IT AND IT WAS IN NEITHER** — mine said
NexusMind, NexusMind's said llm-distillery. Each looked authoritative from the other side.
⭐ **A path plus a commit hash reads as the strongest kind of reference there is, and
neither half was checkable until someone tried.** The hash resolving is what sells it: I
verified `5d5467e` exists and stopped, when the question was what it *contained*.
⛔ **The reusable half is about the STANDING finding, not the file.** A finding that
survives many runs stops being read as a question. I defended keeping it — correctly,
"zero is not the target" — and that defence became the reason nobody asked what it *was*.
**A deliberately-unfixed finding still needs a diagnosis on the record, or the decision to
keep it decays into never having looked.**
⛔⛔ **AND THIS ENTRY ADDED TWO FINDINGS OF ITS OWN, caught only by re-running the checker
after committing it.** Writing up a reference defect, I wrote the dead path unstruck (so it
read as live) and the surviving sibling as a bare filename with no repo prefix (so it did not
resolve). **The document explaining that references need care could not itself pass the
check it was explaining** — 1 finding became 3. Struck and qualified; back to 1.
⭐ **The habit that saved it is small and worth naming: re-run the checker AFTER writing the
prose about the checker, not before.** The write-up is new text and new text is where new
broken references come from — but it arrives feeling like documentation of work already
verified, which is precisely when nobody re-verifies.
⛔⛔ **FOUR OCCURRENCES IN ONE EVENING, and the fourth was inside the warning about the
third.** Writing the paragraph that explains *illustrative example paths get reported as
breaks*, I put the illustrative example path in a code span. Same file, same session,
one sentence after describing the mechanism. The framework maintainer hit the same class
independently at **86 findings** over their `CHANGELOG.md` — every one an invented path
quoted to explain a check — which reopened an issue they had closed that morning as
needing a second adopter's instance. **Two instances arrived the same day and one of them
was written by the person documenting it.**
⭐ **The durable form: an extractor cannot see intent, so in any corpus that documents its
own tooling, a code span IS a reference.** The only reliable move is to write illustrative
paths WITHOUT a code span — which costs the formatting and buys the check back.
⚠️ **Why this estate showed 1 finding and theirs showed 86 is a writing habit, not a
protection**: prose here quotes real files, which resolve at rung 2 or rung 4. The first
genuinely invented example path written into `memory/` is reported as a break, and the
reflex is to "fix" a reference that was never meant to resolve.

### THE NULL ARM WAS THE RESULT — a treatment sitting inside its own control (2026-08-28)
**Problem**: A prompt-reorder probe showed 16/30 rows moving past the #95 band and 3
crossing the op-point. Read alone that is a damning parity failure and the change dies.
**Root cause**: There was nothing to compare it to. Running the *same* prompt twice on the
same 30 articles gives 16/30 and **5** crossings — the treatment is inside its own null.
**Fix**: Never report a delta against a single baseline run when the mechanism is sampled.
The null arm costs one extra run and it decided the question in both directions: it cleared
the change *and* it was the only thing that could have found the instability underneath.
⭐ Say **"no effect detectable above noise"**, never "no effect" — the instrument's
resolution is part of the finding.

### A NUMBER THAT IS REAL, CORRECT, AND ABOUT A DIFFERENT QUESTION — 99.4% cache (2026-08-28)
**Problem**: The null arm reported a 99.4% prompt-cache hit rate. Quoting it would have
claimed a cost saving nothing can reproduce.
**Root cause**: It re-sent the **same 30 articles**, so the whole prompt matched — not the
shared prefix. A corpus run sends distinct articles, where only the template caches. The
number is arithmetically correct and answers a question nobody asked.
**Fix**: Recorded as **unquotable** in three places rather than dropped, because a deleted
number gets re-derived. Same treatment for the arm's 76.0% aggregate: with concurrency N the
first N requests race and all miss, so a short run's aggregate is warm-up, not steady state.
⭐ The generalisation: **a cache rate is a property of a RUN, so ask what varied between the
requests before believing it** — the sibling of *establish what a source excludes*.

### MY TRIAGE COUNTED THE PARENT DIRECTORY AS A SIBLING REPO (2026-08-28)
**Problem**: Classifying 338 reference findings, I reported **137 of 156** cross-repo refs as
matching more than one sibling repo. The real answer is **13**.
**Root cause**: `veen-systems` is this repo's own parent *and* is re-listed as a child of the
grandparent, so its tree contains every other repo. Every match also matched through it.
**Fix**: Exclude the container. ⛔ The tell was not the total — **both versions summed to
exactly 156**. *Closed accounting is not attribution*, third occurrence, and the first where
the miscounted bucket was one I had invented five minutes earlier.

### READING A NESTED SCORER FIELD AT THE ROW ROOT EMPTIES A DRAW SILENTLY (2026-08-28)
**Problem**: A cohort sampler read `raw_weighted_average` and `stage_used` off the archive
row root. Both are `None` on every row — they live under
`nexus_mind_attributes.<lens>`. Every band came back empty.
**Fix**: It **raised** instead of returning a short draw, so it cost two minutes rather than
a corpus. That is the *make the missing case raise, never return `None`* rule paying out —
worth recording as the rule WORKING, not only as the near miss. ⚠️ The first failure printed
`FATAL: band 0.0-2.5 has 0 eligible` with **no denominators**, which is unactionable; the
guard now prints the exclusion stats before it dies.

### A MORE PERMISSIVE RESOLVER LAUNDERED A WRONG PATH FOR 15 DAYS (2026-08-28)
**Problem**: `CLAUDE.md` cited ~~`ovr.news/BRAND.md`~~ (no such file). The real path is
`ovr.news/docs/BRAND.md`. Wrong since 2026-08-13, in an always-loaded file.
**Root cause**: The repo's own `refcheck.py` **resolved** it — rung 4 strips the sibling repo
name and matches by *suffix*, so the basename found the real file one directory down and the
reference reported clean. The generic extractor in `/curate`, which requires the **exact**
path inside the sibling, caught it on the first run.
**Fix**: Path corrected. ⭐ The keeper: **two instruments with different strictness are not
redundant** — the looser one was silently absorbing a class of error the stricter one exists
to find, and neither is wrong. Do not consolidate them without checking which findings die.
⛔ **[2nd occurrence] — the first draft of THIS entry added two more unresolved references**
(the wrong path and its bare basename, both quoted as live paths), exactly as `75f08d4` did on
2026-08-27. **An entry about a broken reference is written in the one register that creates
them: quoting paths as evidence.** Strike the dead one so the absence rung claims it, and
fully qualify the live one.

### THE COMMIT GUARD CANNOT READ NEGATION, AND ITS REMEDY POINTS AT --no-verify (2026-08-28)
**Problem**: A commit was rejected for a "deploy-class word" — the words were
**"Nothing deployed"**, in the preamble this repo puts on every session commit.
**Root cause**: Two gaps. The word test has no negation handling; and the verifier failed a
directory with no `config.yaml` and no `inference_hub.py` on
`hub: cannot check — no repo_id extracted from inference_hub.py`, i.e. it derived a hard
failure from a file it had already logged as legitimately absent.
**Fix**: Reworded (remedy 2), **not** `--no-verify` — that override is what cost three days in
#44. Filed as #136. ⭐ Recorded because of the *direction* of the failure: a guard that fires
on correct messages spends operator trust, and the cheapest-looking exit is the dangerous
one. **A false positive in a safety check is a safety problem, not an annoyance.**

### A BOOTSTRAP QUANTILE IN THE FAR TAIL IS ONE ORDER STATISTIC, AND I PRINTED IT AS A DECISION (2026-08-29)
**Problem**: To "handle multiplicity" I added a Bonferroni interval to an evidence script and
reported that a finding **survived** it. Two independent reviewers re-ran the identical
bootstrap across seeds: the bound's Monte-Carlo sd was ~0.014 against a reported −0.010, and
it sat above zero in **24/30 and 408/500** replications. The published verdict was decided by
`seed=17`.
**Root cause**: at α=0.05/21 on 4,000 draws, each bound is `vals[4]` — the 5th smallest of
4,000. A percentile that far into the tail is a single order statistic; the estimator has no
resolution there. Nothing in the output said so, because a printed interval looks like an
interval whatever its variance.
**Fix**: removed, not recomputed. The **permutation** test (20,000 draws, stable to 4
figures) is the multiplicity-relevant statistic, and it had been *contradicting* the
Bonferroni line in the same file all along — p=0.0049 does not clear 0.05/21.
⭐ **A resampling estimator has a resolution, and the correction that needs the deepest tail
is exactly where it runs out. Before quoting a bootstrap bound, re-run it under a different
seed** — one line, and it is the whole check.

### A HAND-COUNTED CONSTANT GOVERNING A DECISION, WHERE THE QUANTITY IS DATA-DEPENDENT (2026-08-29)
**Problem**: `N_INTERVALS = 21`, commented "every interval this script prints". It printed 15
nominal / 22 total, and 17 on a null fixture. Three reviewers counting independently got
three different answers, none of them 21.
**Root cause**: the count is data-dependent **by construction** — the block emitted a
correction line only in its non-holding branches, so the number of intervals varies with the
result. A hand-count of one run was frozen as a property of the script.
**Fix**: derived — every printed interval increments the family — and the arithmetic replaced
by an explicit statement: **no family was pre-registered**, p clears 0.05 and 0.05/2 but not
0.05/16, and *picking the family that keeps the result is not the way out*.
⭐ **If a constant describes what the code does, the code should compute it.** The tell is a
comment that begins "every".

### I RE-INTRODUCED A TAUTOLOGICAL ASSERTION IN THE COMMIT THAT REMOVED TWO (2026-08-29)
**Problem**: a mutation hardcoding `PROMPT_FILE = "prompt-candidate.md"` survived all 15
tests. The assertion was `prompt_file == "prompt-candidate.md"` — and the harness only ever
passed that one prompt.
**Root cause**: the test was written from the *writer's* side (does the field arrive?) rather
than from the property's side (can the two arms be told apart?). The commit message two
paragraphs above claimed to have deleted two tautologies of exactly this shape.
**Fix**: drive **both** prompts, hold the oracle response identical so only the prompt varies,
and require the persisted rows to differ. Five mutations re-seeded, five caught.
⭐ **A test that supplies only one value cannot test a distinction.** Articulating the rule in
the same commit did not prevent it — [[feedback-articulating-is-not-applying]], again.

### THE RETRACTION SWEEP STOPPED AT THE REPO BOUNDARY (2026-08-29)
**Problem**: a wrong rule was corrected across nine repo surfaces and announced as "finished
properly". It was still live in `~/.claude/projects/.../memory/` — the **auto-memory**, which
loads into every session for this project, i.e. a stronger re-injection than the repo files
that were fixed.
**Root cause**: every sweep, including the one that found four sites "by grep rather than
recall", was rooted at the repo. The auto-memory is not under it and was in no operand list.
**Fix**: corrected there too. ⭐ **The always-loaded layer for this project spans TWO trees.**
A grep whose root is the repo cannot see half of it, and reports clean.

### THE SOURCE DOCUMENT DREW THE WRONG CONCLUSION FROM ITS OWN CORRECT TABLE (2026-08-29)
**Problem**: I wrote into memory that "production scoring is gpu-server on CPU", licensing
exactly the comparison a device term forbids. A peer session caught it; this repo had said
"production serves on GPU" in two files the whole time.
**Root cause**: I read an **experiment's arm label** as a description of production. Run P is
labelled `gpu-server | CPU`: its venv is production's, its device is the study's control. And
I did not invent it — the 2026-08-10 evidence document's own "What it means operationally"
section says the same thing, drawn from a table that does not support it.
**Fix**: corrected in the source document as well as the copies. ⭐ **An arm label says what
was held fixed to isolate a term. It is not a statement about production** — and when a
propagated error is found, the copy you are looking at may not be the origin.


### A 402 IS NOT A PER-ROW ERROR — 6,586 doomed calls in 11 minutes, then exit 0 (2026-09-01/02)

**Problem**: A DeepSeek balance ran out during a 6,590-row k=3 corpus pass. Pass 2 wrote 2,500
error rows and stopped scoring; pass 3 made **6,586 requests in 11 minutes against an empty
account**, wrote 6,586 error rows, printed `Successful: 0  Errors: 6586` — and **exited 0**. A
caller could not distinguish a catastrophe from a clean run. $1.11 of pass 2 was spent for
labels that could not be aggregated.

**Root cause**: Two independent defects.
1. `call_deepseek` routed `402` through the generic `return {"error": ...}` branch. 401/403 had
   a `raise SystemExit` — which does **not** work either: raised inside a `ThreadPoolExecutor`
   worker it surfaces only when the main thread calls `future.result()`, and the executor's
   context manager drains every queued future first. The existing "handling" was decorative.
2. `main()` returned `None` regardless of outcome, so the exit status carried no information.

**Fix**: An explicit `RUN_FATAL` flag that every worker checks **before** issuing a call, so the
first fatal status stops all further requests deterministically. `FATAL_STATUSES = (401, 402,
403)`. Exit **2** on abort with a block naming the status, the body and the resume command;
exit **1** if any row errored; **0** only when clean. 7 tests, 5 mutations killed.

⭐ **The generalisable half: an account-level condition is not a property of a row.** Any status
that will be identical for every subsequent call must abort the run, not decorate each row with
it. Retry logic is for transient failure; 402 is not transient.

⭐ **What caught it downstream was a guard written the night before.** `aggregate_k_runs.py`
refused to write anything — *"FATAL: 6586 id(s) are not in every run"*. The tool it replaced,
`average_oracle_runs.py`, silently intersects the runs and would have produced a label file.

### `training/prepare_data.py` WRITES 0 EXAMPLES, PRINTS "COMPLETE", AND EXITS 0 (2026-09-01)

**Problem**: A filter package's `config.yaml` selects the analysis field via `filter.name`.
Labels written under `uplifting`'s config carry `uplifting_analysis`; pointed at a v8 directory
named `human_thriving`, `prepare_data.py` printed `Analysis field: human_thriving_analysis`,
wrote **0 examples to all three splits**, printed `TRAINING DATA PREPARATION COMPLETE`, and
exited 0.

**Root cause**: `convert_to_training_format`'s own docstring states it: *"Articles without
analysis are silently skipped; missing dimensions default to score 0."* The second clause is
the worse one — a **renamed** dimension does not vanish, it becomes a silent column of zeros on
every row, which is a wrong label rather than a missing one.

**Fix**: Wrote `filters/human_thriving/v8/config.yaml` before labelling and proved the chain end
to end (6 train / 2 test, non-zero labels) against a control that still writes 0. Added
`IN_DEVELOPMENT_FILTERS` coverage to `tests/unit/test_filter_config_schema.py` plus a test that
the config's dimension keys are keys the **prompt actually emits** — the pairing nothing checked.

⚠️ The schema test had been passing **vacuously**: `ACTIVE_FILTERS` is a hand-maintained list, so
the new package could be given `name: 12345` and a weight of 99 with the module still green.
That file already records the same shape biting once (cd v5 invisible for six weeks).

### "THE WINDOW HAS ROLLED, SO IT IS UNRECOVERABLE" IS FALSE — there are monthly archives (2026-09-01) [16th occurrence of *establish what a source excludes*]

**Problem**: All 18 rows of `datasets/adverse/uplifting.jsonl` were 300-char excerpts and the
originals were believed gone — a premise recorded in llm-distillery#127's thread and in the
2026-08-30 rulings as a reason five filters' provenance could never be reconstructed. Gate B-A
is BLOCKING and judged on that file.

**Root cause**: The live `data/filtered/` window rolls at ~14 days. **NexusMind also archives
monthly** — `~/local_dev/NexusMind/data/archived/nexusmind_YYYY-MM.tar.gz`, 9 tarballs back to
2025-10, one scored-rows member per lens, inside the tarball and resolving to no path on disk.

⛔ **And my first search could not have found them.** I globbed `**/*.jsonl*` over the archive
directories, which hold `.tar.gz` files, and got `RECOVERABLE: 0 of 18` — a negative from an
instrument pointed where it could not produce a positive. I nearly reported the rows as
permanently lost on the strength of it.

**Fix**: `scripts/dataset/rehydrate_adverse.py`. **18 of 18 recovered**, 3 from the live window
and 15 from `nexusmind_2026-08.tar.gz`; 5,449 → 100,460 content chars; every length equal to the
row's recorded `content_original_length`.

⛔ **The FluxusSource archive is NOT a substitute and returns a stub rather than nothing.** Its
1,593 `collection_*.tar.gz` hold **producer bytes**: three rows whose enriched originals are
14,546 / 2,917 / 3,652 chars appear there at **447 / 133 / 441**. So "is it archived?" has two
answers depending on which archive, and the wrong one looks like a hit.

⭐ **The join must be verified, not trusted.** Ids are reused when a source rewrites a URL and
the archives span months, so match on the recorded original length **and** a
whitespace-normalised prefix. Normalisation is load-bearing: excerpting collapsed newlines to
spaces on one row and a strict `startswith` rejected the correct article six times.

### `head -N` OF A CELL-GROUPED CORPUS IS NOT A SAMPLE (2026-09-01)

**Problem**: A dry run on the first 8 rows of the staged v8 corpus (gitignored, on b650) measured a 25% scope-gate
flip rate. Quoting that as a corpus figure would have been wrong by construction.

**Root cause**: The file is **grouped by design cell**, and its **first 47 rows are exactly the
class-A supplement** (18 `pos_clear|latin|classA` + 29 `pos_marginal|latin|classA`); row 48 is
`pos_clear|non_latin|-`. So the head is the harshest, most harm-adjacent stratum in the corpus
and looks exactly like a sample.

**Fix**: Reported it as a class-A number, not a corpus one. ⭐ The same shape recurred usefully
later: when an interrupted pass left 4,078 rows scored twice, checking coverage **first** showed
`stage1_low|*` at **0%** and `neg_low|latin` at 16% — so the 12.0% disagreement rate derived
from them is an **upper bound**, which is what made it usable for a spend decision.

### A SHARED TEMP DIRECTORY MADE A 403 TEST REPORT `FATAL: HTTP 401` (2026-09-02)

**Problem**: A subtest asserting that HTTP 403 aborts a run failed, reporting that the script
had said 401. It read as a defect in the code under test.

**Root cause**: Two stale-state bugs at once in the fixture, both from reusing one temp
directory across invocations. Python served a **cached `__pycache__` copy** of the previous
stub `requests` module (same path, same coarse mtime), *and* the scorer **resumed** from the earlier
run's output file.

**Fix**: A fresh subdirectory per invocation. ⭐ A test fixture that reuses a path reuses more
than the path — the interpreter's import cache and any resume-capable artefact under it.

### FOR A LEXICAL GUARD, MENTION *IS* USE — I tripped the commit hook by naming the word that trips it (2026-09-02)

**Problem**: `.githooks/commit-msg` rejected the same commit three times. The third rejection was
caused by a paragraph I had added **to explain the second one**, because explaining it meant
writing the trigger word.

**Root cause**: The hook matches a word list against the message with `grep -iqE '\b(...)\b'` and
fires whenever a `filters/*/v*/` path is also staged. It has no notion of quoting, negation or
metadiscussion, so *"this was rejected for the word X"* is indistinguishable from a claim
containing X. My first rejection was for a legitimate **negation** (*"not deployed"* — describing
the state a filter is **not** in); the second for a past-tense verb about political prisoners
going free, an unavoidable false positive on a news corpus.

**Fix**: Reword. ⛔ **Not `--no-verify`** — the hook's own message records that a prior override
cost three days of production scoring with wrong weights (#44), and it fails **closed**, which is
the right direction for a guard whose failure mode is a false deployment claim.

⭐ **The generalisable half, and it inverts a pattern already promoted here.** This log records
*mention is not use* — records that merely **quote** a dead path should not be counted as
references to it. For a **lexical** guard the opposite holds: it cannot see the difference, so
**mention is use**, and any prose *about* the guard is subject to the guard. Two consequences:
a commit message may not name the vocabulary that gates it, and a false positive rate on a news
corpus is structural rather than fixable — `released`, `shipped` and `live in production` are
ordinary English about the world, not only about software.

⚠️ **This will recur for every `human_thriving v8` commit** until the package passes
`verify_filter_package.py`, because `STATUS.md` necessarily discusses the state the filter is not
yet in, and the package legitimately has no `inference_hub.py` to extract a Hub repo id from.
Expect it; do not "fix" it by weakening the guard.

**Related**: the same hook has a separate hole in the other direction — `git commit --amend`
reads `git diff --cached`, which is empty on an amend, so a filter-touching commit can be amended
with any wording at all (found 2026-09-01, reported, not fixed).

## 2026-09-03 — `| tail` swallowed an exit code while I was testing exit codes **[x6 — recurred 2026-09-25, v9 smoke test `echo exit=$?` after `| tail`; re-run for the real code]**

**Problem.** Checking the four exit codes of a new gate, I ran
`python3 gate.py <bad-glob> 2>&1 | tail -1; echo $?` and read **0** for two refusal paths that
in fact exit 1 and 3. The pipeline's status is the last command's, and `tail` always succeeds.

**Fix.** Redirect to a file and echo `$?` on the next line, or use `${PIPESTATUS[0]}`. **If an
exit code decides anything, do not put a formatter after it.**

⭐ This is the **fifth** recorded occurrence, and the sharpest: it happened *inside the task of
verifying exit codes*, and it masked a real defect — the gate's plumbing errors were exiting 1,
the same code as "a row FAILS", so a gate that never ran was indistinguishable from a gate that
ran and failed. Both were fixed only because the second check had no pipe.

## 2026-09-03 — a truncated id broke a join silently, and its fallback was a claim

**Problem.** A probe printed `d["id"][:40]` for readability. One id is exactly 40 characters, so
it came back truncated, its lookup into the adverse suite missed, and the code fell through to
`class-A: False`. Had that row been class-A-detected, its design-cell inclusion probability is
**0.763**, not the 0.081 I was about to publish — a tenfold error in the alarming direction.

**Fix.** Re-ran with full ids and a `KeyError`-raising join (`adv[rid]`, not `adv.get(rid)`).
The figures held, but for a different reason than my code assumed.

⭐ **A truncated key does not fail, it misses — and the default it falls back to is an
assertion.** Truncate for display only, never in the value you join on.

## 2026-09-03 — prompt clauses are not additive, and a four-arm ablation misled me into shipping their union

**Problem.** Four v8.1 clauses, each measured individually safe at k=6 on the #91 origin row
(0.900–0.917, `in_scope` 0/6). Their union scored that row **5.921 with 12/12 `in_scope`** — far
worse than any single clause. I had run the ablation, drawn the conclusion that safe-alone means
safe-together, and validated the union at k=12 only after shipping it into a candidate prompt.

**Fix.** Leave-one-out isolated a **B×D interaction** (removing either fixes it, neither causes
it alone). D held the only sentence among the four that *licenses* a positive; deleting it
helped 5.921 → 3.375 and was not sufficient. D was dropped.

⭐ **Ablate to attribute, validate the artifact you intend to ship.** An ablation answers "which
clause caused this"; it does not answer "is the combination safe".

## 2026-09-03 — the class-A instrument does not detect a declared class-A row

**Problem.** `filters/uplifting/v7/prefilter.py`'s `crime_violence` patterns — the class-A
instrument the corpus draw uses — match **none** of the title *"Children's helpline says number
of calls about child domestic abuse cases has risen"*, which the adverse suite declares as
**class A**. It therefore lands in a `|-` design cell, not `|classA`.

**Not fixed** — recorded. The class-A *supplement* population (title patterns) and the class-A
*adverse* population (editorial judgement) are defined by different things, and neither the plan
nor the manifest says so. Any figure that treats them as one population is wrong.

## 2026-09-03 — `verify_filter_package.py` reports "All 4 checks passed" on a package that cannot score

**Problem.** Asked to establish whether deploy was applicable, I ran the package verifier
against `filters/human_thriving/v8` — a labelling-scope package with **no** model adapter, no
`calibration.json`, no `normalization.json`, no probe and no scorer. It printed
`All 4 checks passed` and exited **0**.

**Root cause.** Absent files are not failures, by design: the checker returns
`(True, "skip: {name} not present")` for each, so on v8 two of the four "passed" checks are
skips-because-absent. It is a **shape** checker for what is present, not a readiness gate — and
the summary line does not distinguish *4 passed* from *2 passed and 2 absent*.

**Fix.** None applied — nothing is deploying, and editing a deploy guard at session end with no
run to prove it is the 2026-08-25 pattern (green suite, nobody watched a service start). The
real gate is `scripts/deployment/preflight_deploy_guards.py`, which does check the Hub against
the local adapter mtime and requires `--nexusmind-root`, so it cannot run from this repo alone.

⭐ **Never read `verify_filter_package.py`'s summary as deploy readiness.** Count the skips: a
package with nothing in it passes every check it has. ⚠️ The lesson generalises past this script
— *a check that treats absence as success is loudest exactly when there is nothing to check.*

## 2026-09-04 — `--select-metric` was accepted and inert, because the metrics weights were gated on an unrelated flag [RESOLVED]
**Problem**: `training/train.py --select-metric recall_at_20` ran, printed nothing unusual, and
selected every checkpoint on **aggregate MAE** — the metric ADR-023 forbids ranking on, on a
corpus that is 94.9% floor. Four deployed filters (`solutions v6`, `cultural_discovery v5`,
`belonging v1`, `investment_risk v6`) have no needle keys in `training_history.json` at all, so
they were selected this way too.
**Root cause**: `dimension_weights_list` was built only under `if args.sample_weight_scale > 0`
(default 0.0), and the **same list** is what `compute_metrics` needs to emit `recall_at_k` /
`recall_medium` / NDCG. With it `None` the whole needle block was skipped, `val_metrics.get(
args.select_metric)` returned `None`, and selection fell to the MAE branch. Two unrelated flags
coupled through one variable named for the wrong one of them.
**Fix**: `1878e7b` — weights always built; the MEDIUM+ boundary resolved and **raising** rather
than defaulting; `recall_at_k` skipped when `n <= k`; resume seeded from `max(history)`; metadata
split into run-scoped and checkpoint-scoped; 26 tests in `tests/unit/test_train_metrics.py`.
⭐ **The generalisable part: nothing in `tests/` referenced `training.train`, so "573 tests pass"
was true and carried zero information about the module.** A green suite that cannot execute the
changed lines is not evidence about them.

## 2026-09-04 — I offered a tautology as an outcome proof, in the commit fixing an outcome-proof defect
**Problem**: To prove the fix fired I cited: the run logs `Needle metrics at MEDIUM+ threshold:
4.5`, and *"the pre-fix run contains that string 0 times."* Presented as an A/B control.
**Root cause**: The string literal is **introduced by the same commit**. A pre-fix run could not
have contained it under any circumstances, so the negative carried no information — it is a
presence check on a new constant wearing the costume of a before/after comparison.
**Fix**: Dropped from the message; replaced with a real control — the pre-fix expression vs the
resolver over every config on disk, which returns **6 configs wrong or invented**.
⭐ **A control has to be able to come out the other way.** Ask what would have made the "before"
different *before* citing it — this is the *establish what a source excludes* rule pointed at a
control rather than a population.

## 2026-09-04 — I used MAE's shape to reason about recall, one message after naming that exact substitution as the trap
**Problem**: Argued the selection defect "almost certainly cost nothing" because **val MAE fell
monotonically across all six epochs, so there was no sign of a turn**. The owner pushed back. The
re-run moved the kept checkpoint from epoch 6 to epoch 4 — it did change what ships.
**Root cause**: MAE falling monotonically is what a model steadily improving its **floor**
prediction looks like; its ranking of the needle can peak early and decay while MAE keeps
dropping. That is the entire reason the needle metrics exist. I had identified the
MAE-as-proxy-for-recall substitution as the defect *in the previous message*, then built a
recommendation on it.
**Fix**: Re-ran with corrected selection. Also refuted my second argument — I called the metric
"noise-dominated" having measured no variance, and used that to argue against measuring.
⭐ **Being articulate about a trap is not the same as being outside it, and the moment right
after naming one is when the guard is weakest.** ⭐ *"There is no sign of X"* measured with an
instrument that cannot show X is not evidence about X.

## 2026-09-04 — `git commit --amend` orphaned the commit that produced a trained model
**Problem**: The `human_thriving v8` checkpoint on b650 was trained under `0697f5a`. Review found
defects, I amended into `1878e7b`, and the tree that actually produced the weights became
**reachable from no branch** — one `git gc` from gone, while the weights themselves are gitignored
and exist on exactly one host.
**Root cause**: Amending is routine for an unpushed commit and normally costs nothing. It is not
routine when an **external artifact was built from that exact tree** — the artifact's provenance
is the sha, and amending rewrites it after the fact.
**Fix**: `git tag -a exp-015-training-code 0697f5a` keeps it reachable; recorded in
`filters/human_thriving/v8/STATUS.md` and EXP-015 as a decision owed before phase 9 — retrain
under a real commit, or record the exception.
⭐ **Before amending, ask whether anything outside the repo was built from the commit being
replaced.** Seed 42 is not bit-reproducible on CUDA here (val MAE 0.5601 vs 0.5605, same code and
data), so a retrain does not recreate the artifact either — it makes a different one.

## 2026-09-04 — a borrowed resolver was wrong for the one filter it was borrowed to handle
**Problem**: Fixing the hardcoded `MEDIUM = 4.0`, I reused `fit_normalization`'s
`_lowest_nonzero` rule. A test written in the same commit failed immediately: `resilience/v1`
resolved to **2.5**, not its configured medium of **4.5**.
**Root cause**: `resilience/v1` ships `high 6.5 / medium 4.5 / low 2.5`. Almost every other
filter sets `low: 0.0`, which makes *lowest non-zero* and *the medium boundary* the same number —
so the rule looks correct across 17 configs and is wrong on the one with a non-zero bottom tier.
**Fix**: A tier literally named `medium` wins; lowest-non-zero is the fallback for filters that
call it `connection` (uplifting v1/v4) or `monitoring` (todo/v1).
⭐ **A rule validated on the population where two definitions coincide has not been validated.**
⭐ And the test earned itself on its first run — this was found by writing the assertion, not by
reading the code, which had already passed a four-lens review.

## 2026-09-04 — `.gitignore`'s scratch rule ate a committed evidence file, and `git add` said nothing
**Problem**: `docs/evidence/2026-09-04-v8-probe-calibration/probe_recall_report_test.json` — the
sole source for every test-split number published in that directory's README, in
`filters/human_thriving/v8/calibration_report.md` and in EXP-016 — was not staged by
`git add <dir>`. No message, no warning, exit 0. Its `_val` and `_test_seed7` siblings staged fine.
**Root cause**: `.gitignore:163` carries `*_test.*` in a scratch-file block beside `*.bak`,
`*.old` and `*_backup.*`. It is a PATTERN, not a path, so it applies repo-wide and matched an
evidence artifact whose name happened to end `_test.json` <!-- placeholder --> (a suffix, never a file).
**Fix**: `!docs/evidence/**/*_test.*` and `!docs/evidence/**/*_backup.*`, verified in both
directions — the JSON is stageable, and `scripts/foo_test.py` <!-- placeholder --> is still ignored. ⛔ **Scoped to
`docs/evidence/` only**; the pattern still swallows `*_test.*` elsewhere.
⭐ **The question that found it was not "did the add succeed?" but "what is in the staged set?"** —
`git add -n` listed 13 files where the directory held 14. Blast radius measured
(`git status --porcelain --ignored | grep '_test\.'`): exactly two untracked files repo-wide, that
JSON and `filters/common/obituary_detector/validation/panel_obit_test.py`, a junk-gate validation
script that has never been in git while every sibling in its directory is tracked.
→ *establish what a source excludes*, **18th occurrence**.

## 2026-09-04 — the Stage-1 threshold belongs to the PROBE, not to the recipe
**Problem**: A threshold of 1.75 was derived to hold the owner's ruled ~88.6% Stage-2 routing
(design-weighted 0.8876 val / 0.8935 test, FN@MEDIUM+ 0/31 and 0/35). Retraining with the same
data, objective and code but `--seed 7` gave a probe on which that *same* 1.75 routes
**0.7406 / 0.7567** — a ~14 pp collapse in routing, with every recall number still 0 FN and a
*better* val BCE.
**Root cause**: the probe's score SCALE moves with the seed; its ORDERING does not. A threshold
is a statement about one probe's scale, so it does not survive a retrain — and Stage 1 is silent
by design (a screened-out article produces no score, no log line, no output), so a 14-point
tightening has no symptom anywhere.
**Fix**: `config.yaml` records `probe_sha256` **beside** the threshold and
`filters/human_thriving/v8/inference_hybrid.py` refuses to construct the scorer on a mismatch,
with an error naming the re-derivation procedure. Mutation-killed.
⚠️ **Deliberately a different pin from `probe/*.pkl.sha256`**: that companion travels *with the
probe* and a retrain regenerates it, so it can only catch corruption — it cannot notice a
valid-but-unpaired probe. This one travels *with the threshold*.
⭐ Generalises past probes: **any number derived against one artifact must be pinned to it, or a
legitimate rebuild of that artifact silently invalidates the number.**

## 2026-09-04 — hashing is the wrong reproducibility test for a torch pickle
**Problem**: Two `--seed 42` probe runs, same host, same venv, same CPU, produced pickles with
different sha256. Read naively that says the seed does not work.
**Root cause**: the files differ in **134 of 541,144 bytes**, all of them torch storage keys
derived from **memory addresses** (`94090181761856` vs `97139374751504`). The tensors are
identical: all six `np.array_equal`, `max|Δ| 0.000e+00`, scaler identical.
**Fix**: compare `state_dict` tensors, never file hashes, when asking whether a seeded run
reproduced. The shipped `.pkl.sha256` still has a job — it pins *the shipped file* against
corruption — but it is not a reproducibility instrument.
⭐ **`sha256sum` would have reported "not reproducible" about a fully reproducible artifact** —
an instrument that cannot say yes about the thing being asked. Same family as *prove the
instrument could have said yes*, in the direction that produces a false NEGATIVE.

## 2026-09-04 — a documented refusal that could not fire on the path that scores
**Problem**: `filters/human_thriving/v8/base_scorer.py`'s `_load_prefilter` raises
`NotImplementedError`, with a docstring citing NM#284 as the reason — a silent pass-through would
read as "the prefilter ran and let everything through". Measured:
`HumanThrivingHybridScorer(use_prefilter=True)` **constructed fine**, with
`self.use_prefilter = True` and no prefilter.
**Root cause**: `HybridScorer._create_stage2_scorer` hardcodes `use_prefilter=False`, so the
Stage-2 scorer never reaches the raise. The guard was on the wrong object for the hybrid path,
which is the path production uses.
**Fix**: raise in `HumanThrivingHybridScorer.__init__` before anything is loaded; two tests,
mutation-killed.
⭐ **The refusal was written to prevent exactly the shape it then had.** Writing the rationale
into the docstring made it feel discharged. → the *unreachable-mechanism* family; caught
pre-commit by `/review-changes`, not shipped.

## 2026-09-04 — a script promised to omit a column and emitted it unconditionally
**Problem**: `scripts/analysis/probe_recall_report.py`'s `--corpus` help text and the output
JSON's own `design_weight_note` both said the design-weighted columns were "omitted rather than
silently computed with weight 1". `summarize()` emitted `weighted_positive_rate`,
`weighted_fn_rate` and `weighted_stage2_rate` unconditionally. Run without `--corpus`, the JSON
carried `design_weighted: false`, a note saying the columns were omitted, **and those three
fields populated with unweighted values**.
**Root cause**: the promise was written in the help text and never expressed in the code.
**Fix**: `summarize(..., weighted=...)` nulls them; `sum_weights*` added per group so a weighted
rate can be POOLED across splits, which is what had forced the routing-gap test to be unweighted.
⚠️ **It did not bite this run** — all shipped reports have `design_weighted: true` with a complete
join — which is exactly why it would have survived. The field was there, was populated, and was a
different instrument from the one its name claimed (the 2026-09-03 `harm_title` shape).

## 2026-09-04 — a presence control that fired after the files were written
**Problem**: `scripts/analysis/dump_student_scores.py` raised
`SystemExit("refusing to emit two files that are the same file")` when calibration changed no
row — after writing and closing all three output files.
**Root cause**: the check was placed after the write loop because that is where the counter
finished, not where the decision belonged. The files it "refused to emit" were on disk at exit,
and `ground_truth_gate.py --recompute-model-wa` pointed at that directory would have read them.
**Fix**: build the rows in memory, check, then write. The refusal now also says "Nothing was
written", so the message and the state agree.
⭐ **A guard that fires after the damage is not a guard** — and a `SystemExit` reads like one in
review, because the exception is the thing you look at.

## 2026-09-04 — an absolute in a description, asserted on six surfaces, refuted by its own next clause
**Problem**: I wrote "Every other `inference_hybrid.py` hardcodes `DEFAULT_THRESHOLD = 1.00`" in
`config.yaml`, `inference_hybrid.py`, `STATUS.md`, an evidence README, a test docstring, and as a
**constant name** (`DEPLOYED_DEFAULT_THRESHOLD`) whose comment called it the fleet default.
Measured: **2 of 13** are 1.00 (the rest 0.75, 1.225, 1.25, 1.50, 2.25, 2.50).
**Root cause**: the claim was true of v8's ancestor, `uplifting v7`, and I generalised it to the
fleet without measuring — one `grep -h '^DEFAULT_THRESHOLD' filters/*/v*/inference_hybrid.py` away.
Worse, the next clause said "they agree today, so it is harmless", and `nature_recovery v4` ships
config **3.225** against runtime **0.75** — the 3.225-vs-0.75 divergence the same paragraph cites
as the cautionary shape is **live right now**.
**Fix**: all six surfaces carry the measured distribution; the constant renamed
`V7_DEPLOYED_THRESHOLD` with a comment saying why it must not go back.
⭐ **A field or constant NAME is an assertion, and it is read far more often than the note beside
it.** ⭐ And an absolute about *behaviour* ships unmeasured by default — the cheap check was one
grep, and the claim's own counterexample was two lines below it.

## 2026-09-04 — the significance test was unweighted inside a document arguing against unweighted rates
**Problem**: `script_routing_gap.py` computed the Latin/non-Latin routing gap from
`stage2_rate` — the UNWEIGHTED sample rate — while the same JSONs carried
`weighted_stage2_rate` unused, and put a binomial SE on a stratified design whose weights run
1.31–29.32. The evidence README two sections above argues that an unweighted split rate "is a
rate for the sample and for no population the filter will ever meet".
**Root cause**: Σw was not recorded per group, so a weighted rate could not be pooled across
splits — and rather than fix the report, I reached for the field that was there.
**Fix**: `sum_weights*` recorded per group; the test now prints weighted (Hájek ratio) **and**
unweighted side by side, plus the measured Kish deff. Reweighting made the gap **larger** —
0.0762 (z 2.65) against 0.0693 (z 2.53) — so the finding was never at risk and the reporting was.
⚠️ Both SEs are still binomial and therefore optimistic; deff 1.068 moves the unweighted z to 2.45.
⭐ **Writing the caveat is not applying it.** The document that names the trap most clearly is
where I then fell into it.

## 2026-09-04 — the commit-msg hook blocked the commit, and it was right
**Problem**: `git commit` aborted: "deploy-class word detected in message; verifying staged
filters" → `[FAIL] hub: cannot check — no repo_id extracted from inference_hub.py`.
**Root cause**: the message used "shipped"/"ships" in passing (about *other* filters' configs),
which triggered the verifier; `human_thriving v8` ships neither `inference_hub.py` nor a `NO_HUB`
sentinel, so `verify_filter_package.py --check-hub` cannot tell *deliberately not on the Hub* from
*hub check broken*. `uplifting v7` ships the sentinel.
**Fix**: reworded the message (the commit genuinely deploys nothing). ⛔ **NO_HUB was NOT added** —
`docs/HUMAN_THRIVING_V8_PLAN.md` §3c calls a Hub repo for v8 "optional", so writing the sentinel
would assert an undecided deployment choice. Recorded as owed before phase F.
⭐ **A failing check may be the control working.** The hook was blocking on a real package gap that
two independent review lenses had flagged the same session — not on my wording.

## 2026-09-04 — I judged four times on an aggregate that pooled the thing being asked about
**Problem**: Four claims made and refuted in one evening, three of them the same shape.
(1) *"v8's recall is below the fleet's 0.59–0.72"* — v7 and v8 do not share a positive class
(Jaccard 0.246), so those are two recalls of two different quantities. (2) *"non-Latin content
is screened harder"* — the routing gap is **entirely in the negatives**; every positive routes
in both scripts. (3) *"the student is not replaceable"* from ΔAUC — AUC integrates the whole
ranking, and the decision is a top-k cut at k≈17–26, where the difference vanishes.
**Root cause**: each aggregate was correctly computed and answered a question nobody asked. A
rate pools the classes; an AUC pools the ranks; a recall pools whatever the label definition
happens to be. **The pooling is invisible in the number.**
**Fix**: before quoting an aggregate as a finding, name the partition the decision actually
uses and compute it there. Positives vs negatives. Ranks you surface at vs ranks you don't.
One label definition vs another.
⭐ **An aggregate difference is not a finding until it is split by the thing that makes it
interpretable** — and the tell is that every one of these was *reportable*, *reproducible* and
*wrong*, so no verification step could have caught them. Only asking a different question did.
⚠️ The fourth was a different failure and worth separating: *"the probe/student gap is a
kind-of-signal limit, not capacity"* was a mechanism claim, pre-registered with a falsifier,
and refuted by measurement — which is the system working rather than failing.

## 2026-09-04 — a verdict carried from one role to another, and ADR-011 was right all along
**Problem**: I reported ADR-011's floor-collapse prediction — *"regression will likely collapse
to a floor predictor and drop positives"* — as **not holding**, because a regression-objective
probe beat the recall probe on AUC by 3.25 points at a 4.7% positive rate.
**Root cause**: I measured the **scorer** role and stated the verdict for the **screen** role.
ADR-011's claim is about screening, where collapse means unrecoverable Stage-1 false negatives.
Measured properly (threshold selected on val, evaluated on test), regression e5-large screens
hardest at 30.3% routing and **drops 6 of 35 positives — 17% of the needles.** Exactly as
written.
**Fix**: corrected in `IS_THE_PROBE_ENOUGH.md`, the ledger and EXP-020, not merely noted.
⭐ **A probe can be the better SCORER and the worse SCREEN.** They are different objectives
with different failure modes, and an ADR scoped to one of them is not refuted by evidence from
the other. Check which role a claim is about before reporting it refuted.

## 2026-09-04 — the memory index blew its budget because I kept growing one entry
**Problem**: `run_verify_annotations.py` went from exit 0 to exit 1 mid-session:
`memory/MEMORY.md is 31,916 B, over the 30,000 hard limit`.
**Root cause**: five experiments landed in one evening and I appended each to the same index
entry, which reached **9,787 chars** — a session record living in the always-loaded layer.
**Fix**: the guard's own message prescribes it — *"Do NOT drop your session entry to fit — move
detail into `memory/project_session_*.md` and leave a hook here. Check each trimmed entry has
its full session file FIRST."* Did exactly that: diffed every distinctive number in the index
entry against the session file, found **three** (`0.0986`, `0.1009`, `0.8520` — the truncation
causal test) that existed ONLY in the index, homed them, re-checked to zero, then trimmed
9,787 → 2,901 chars. Guard back to exit 0 with 5,120 B spare.
⭐ **A budget guard that tells you the correct remedy is worth more than one that only refuses**
— and the "check the session file FIRST" clause is the load-bearing half: trimming before
homing would have destroyed three measurements silently.

## 2026-09-04 — two windows whose per-call rates agreed (a four-instance pattern, three of them a peer's)
**Problem**: Measured production scoring overhead and reported *"~62 ms/article of overhead
against 18.5 ms of compute, a 4× multiplier"* — one message away from sending it to the
NexusMind peer session as an action item. Matched to one window: **0.30 ms/article of
client+network and a 1.18× multiplier.**
**Root cause**: I paired sadalsuud's `score` total from a **three-cycle** window (1,209.1 s /
15 calls) with gpu-server's totals from a **twenty-hour** window (1,656.8 s / 941 batches).
Both numerators were correct. Both denominators were correct. They were denominators of
different populations.
⛔ **The tell was absent, and that is the finding.** The *per-call* rates agreed across the two
windows — **80.6 s/call against 77.5 s/call** — so every sanity check on the pieces passed. A
defect that lives in how two correct quantities are combined cannot be seen by a check aimed at
either one.
**Fix**: `docs/evidence/2026-09-04-scoring-overhead/measure_scoring_overhead.py` derives the
window from the outer layer, reads both journals with `-o short-iso`, and refuses rather than
reporting zero on an empty read. Rates reproduce on a nested 13.21 h window (1.18×, 18.05
ms/article, 390.9 s/cycle) — ⚠️ **a subset re-run, not an independent replication.** Registry
`EXP-021`.
⛔ **That fix did NOT close the defect, and review proved it.** Filtering the gpu journal to
`[lo, hi]` excludes over-coverage and **not under-coverage**: a gpu journal starting after
`lo` gives sadalsuud's totals the full window and gpu's a subset — the same defect, the same
direction, every per-call rate still agreeing. Demonstrated on a synthetic pair at **4.80×
against a true 2.40×**. Now guarded by asserting both journals *cover* the window, and by
asserting the layers nest (`compute ≤ http ≤ wall`). ⭐ **Three of my guards were refusals on
an EMPTY read; the defect lives in a PARTIAL one, and nothing had a word for that.**
⚠️ **Recomputing "a second way" is not automatically enough — it has to differ in the right
way.** Recomputing ms/article would have *confirmed* the error; only a quantity that cannot be
formed without a shared denominator catches it.
⚠️ **Two hosts, two clocks**: gpu-server runs UTC, sadalsuud UTC+2. systemd's default
`Sep 04 13:27:52` carries no offset, so comparing those bare local times shifts a window two
hours with no error. `-o short-iso` on both sides, compare in UTC.
⭐ **Cross-repo evidence, from the NexusMind peer the same day — this is one shape, not four.**
Theirs: a control requiring `cosine < 0.60` that drew **zero pairs in 200,000 attempts**
because that value does not occur in the space; a sampling design whose arms sat at different
cosines, so a real comparison **came out sign-reversed**. A FluxusSource session: a regression
guard matching a pattern the defect did not take, **green over the thing it was written to
catch**. In all four the components were individually correct and the composition was not, and
in all four the checks were aimed at the components. Filed here under *a window is part of a
source*; NexusMind holds three of the four and is the better home if these are ever merged.

## 2026-09-04 — a config read presented as a runtime proof, caught by a peer's wrong guess
**Problem**: Wrote *"the e5 probes do not run on sadalsuud at all"*, sourced from
`require_gpu: true` + `cpu_fallback.enabled: false` + `host: gpu-server`. True of the **filter**
path, and wrong as stated: **story dedup runs its own `multilingual-e5-large` pass**, worth
**2,477.5 s against scoring's 3,127.1 s** in the same window — 42.4% of the pipeline's blocking
wall time, omitted entirely.
**Root cause**: `require_gpu` and `cpu_fallback` are keys under `scoring:`. Story dedup is a
**preprocessing** stage and never consults them. I read the config of one consumer and stated
the conclusion for the host.
⭐ **The config would have predicted the OPPOSITE, and that is what makes this worth logging.**
sadalsuud has no GPU at all (`nvidia-smi` absent) and `NexusMind/src/preprocessing/story_dedup.py`'s own loader falls back
to `SentenceTransformer(model_name, device="cpu")`, so a config read gives a CPU e5-large pass.
It does not happen — the runs log `Story dedup: using GPU embeddings via gpu-server`. **Only
the log says so, in both directions.** ⚠️ I first wrote *"every run"*: it was **7 of 8**, and
the instrument cannot express "CPU" at all — the CPU branches log a phrase without the word
`using`, so a CPU-fallback run reads as *no information*, not as a negative. `devices` was a
`set`, and a set of size 1 is produced identically by 1 of 8 runs and by 8 of 8.
**Fix**: `measure_scoring_overhead.py` now collects dedup from the same journal and window and
reports it separately; §6 of the writeup and `EXP-021` corrected before commit.
⛔ **And the "real answer" I reached here was the NEXT error — see the entry below.** I wrote
*"embeddings 14.0%, clustering 86.0% and IS sadalsuud CPU"*; the 86% is a subtraction, not a
category. What stands: **≤4.4% of dedup is GPU work, ≥95.6% is sadalsuud-side**, and the split
between clustering and embedding client overhead is **not separable** with current
instrumentation. The owner pointed at e5 and the box; the peer pointed at e5 and the box; the
load is somewhere neither of us named and is still not fully named.
⛔ **A caveat can be right about scope and wrong about mechanism — check both halves; the wrong
half was what led to the finding.**

## 2026-09-04 — I subtracted a timer from a total and named the remainder
**Problem**: Reported *"story dedup: embeddings 14.0%, **clustering 86.0% and IS sadalsuud
CPU**"*, and told a peer session so. The 86% is not clustering.
**Root cause**: `Centroid migration … embed_seconds=` times **only the re-embedding of cluster
centroids being drift-checked** (`NexusMind/src/preprocessing/story_dedup.py`
`_migrate_drifted_seeds_with_stats`). The run's **article** embedding pass is untimed and
unlogged on the sadalsuud side. So `dedup wall − embed_seconds` still contains that pass's
blocking HTTP wait — which is *not* sadalsuud CPU, by the same document's own doctrine two
sections earlier.
⛔ **The remainder of a subtraction is not a category. It is whatever is left**, and it
inherits every consumer nobody enumerated. Naming it *"clustering etc."* made an unenumerated
bucket sound like a measurement.
**Fix**: measure the article pass from the side that sees it — gpu-server's
`POST /embeddings/encode`, **107.8 s against dedup's 2,477.5 s**. Honest claim: **at most
4.4% of dedup is GPU work and ≥95.6% is sadalsuud-side**, clustering *plus* embedding client
overhead, **not separable** with current instrumentation. (Sadalsuud's own centroid timer
reads 299.5 s against gpu's 107.8 s for *all* encode traffic, so the client overhead is
substantial and is not clustering.)
⭐ **This is the third correction of the same shape in one document, and it landed twenty
lines after logging the second one.** *Articulating the rule is not applying it.*
⚠️ Two instrument defects surfaced with it: **7 device lines over 8 dedup runs**, so *"every
run logs `Story dedup: using GPU embeddings via gpu-server`"* — which I had already sent to a
peer — is **false as stated**; and the instrument **cannot express "CPU" at all**, since the
CPU branches log a phrase without the word `using`. A set of size 1 is produced identically by
1 of 8 runs and by 8 of 8; `devices` was a set and was never counted.

## 2026-09-05 — `pgrep -f` matched its own wait-loop TWICE in one session (7th and 8th) [x3, 9th occurrence 2026-09-17]
*(⭐ **9th, 2026-09-17 — FIRED AND WAS CAUGHT, which is what the rule buys.** Launching the
parity run, `pgrep -af "box_parity.py"` returned **three** lines: two were the `bash -c` and
the ssh command carrying the pattern, one was the real process. Unlike the 7th and 8th it cost
nothing, because `CLAUDE.md`'s working rule — **"if a process check decides whether you act,
print the matching line before believing it"** — was followed and the pid was read off the
printed line rather than off a count. Recorded as an occurrence anyway: the trap's **rate** is
the thing worth knowing, and only counting the times it wins understates it.)*

**Problem**: Waited for a remote benchmark with
`ssh b650-gpu 'while pgrep -f "bench_devices.py --arm student-gpu"; do sleep 5; done; ...'`.
It never returned and was killed at the timeout (**exit 143**) — while the benchmark itself
had finished minutes earlier.
**Root cause**: `pgrep -f` matches the **full command line**, and the remote shell carrying
the loop contains the pattern. The loop was waiting for itself. CLAUDE.md documents this at
six prior occurrences; I wrote it anyway, inside an experiment about instruments that cannot
say what they claim.
**Fix**: no data lost — the result was already retrieved by reading the output file directly.
Use `ps -eo pid,etime,args | grep -v grep`, or check for the artifact the job produces rather
than for the job. ⭐ **The general form is the session's own theme: I asked "is it still
running?" of an instrument that had to answer yes.** The wait-loop is a *negative*-detector
whose positive was guaranteed.
⚠️ **The tell was available and I did not use it**: an earlier command in the same session had
already listed the process with `ps -eo pid,etime,args`, which shows the loop and the job as
separate lines. `pgrep` collapses exactly the distinction that matters.
⛔⛔ **AND I DID IT AGAIN ~40 MINUTES AFTER WRITING THIS ENTRY.** Same session, same box, same
shape: `ssh b650-gpu 'while pgrep -f "venv/bin/python benchmark_devices.py"; do sleep 5; done'`
— exit **143** again. **8th occurrence.** I had just written the paragraph above, in this file,
naming the mechanism and the remedy. ⭐ *Articulating the rule is not applying it, and the gap
here was under an hour.* The remedy that would have worked both times is the one already
written down and still not used: **wait on the ARTIFACT the job produces, never on the job.**

## 2026-09-05 — a benchmark reported CUDA twice and called one of them CPU
**Problem**: Measuring v8 throughput by device, the CPU arm read **2.37 ms/article** against
the GPU arm's **2.34** — a 1% difference between two devices. Measured properly, CPU is
**42.41 ms/article**, **18× slower**.
**Root cause**: `filters/common/embedding_stage.py:112` caches loaded models in a class-level
dict keyed on the **model name alone**. On a cache hit (`:214`) the `device` argument is never
consulted, so the second `EmbeddingStage(..., device="cpu")` in the process got the
CUDA-resident model — while `self.device` still read `"cpu"`, and `self.device` *is* honoured
at `:195` and `:284` for the probe head and the input tensors. **Half the object obeys the
flag and half ignores it, so nothing crashes.**
**Fix**: one arm per process, and the script now **reads the device back off the loaded
model** instead of trusting the flag it passed. Filed **llm-distillery#146** — the same dict
is read (`:861`) and written (`:881`) by `NexusMind/src/preprocessing/story_dedup.py`, so the
cache spans two repos and each side believes it chooses the device.
⚠️ **Latent, not live — and my first statement of WHY was false.** I wrote *"no two current
consumers share a model name"*; **fourteen** filter configs name `multilingual-e5-small`. The
latency is on the **device** axis: none of them passes `device`, so all resolve identically at
`embedding_stage.py:141-142`. ⭐ *The claim was true of `(name, device)` pairs and false of
names, and I asserted the wrong one of the two in four files.*
⭐⭐ **THE ONLY TELL WAS THAT THE TWO NUMBERS AGREED.** A 20× error was visible; a 20% one
would have shipped. *When two arms of an experiment are supposed to differ and don't, that is
a result about the instrument before it is a result about the world.*
⭐ **And the second finding is where the repeats belong.** Within one process the arms are
stable to **0.03–0.61%**; between sessions on the same box with the same script shape,
e5-small GPU moved **1.60×** (3.74 → 2.332). **Repeats inside one process measure the
process, not the quantity** — a figure quoted to three significant figures from five such
repeats is precise about one run. What changed between sessions was not identified, and no
cause is claimed.

## 2026-09-05 — I searched for an artifact where it could not be, then published the negative
**Problem**: Wrote *"the e5-large probes from EXP-018/019 were never retained"* in four places
and substituted an **encoder-only** measurement for the missing arm. The probe was at
`b650-gpu:/tmp/probe_e5large.pkl` (1,211,967 B, `input_dim 1024`, `output_dim 6`) the whole
time — and it was not alone: **eleven probes were in that `/tmp`**, including both EXP-019
regression heads and the seed-42/seed-7 pair from the reproducibility work.
**Root cause**: my search was `find /home/jeroen -maxdepth 8 -name "*.pkl"`. `/tmp` is not
under `/home/jeroen`. ⛔ **The instrument could not have said yes**, which is this repo's first
working rule, and I broke it inside a document written about instruments that cannot say what
they claim.
⚠️ **A 36-day uptime meant they were one reboot from gone.** Copied to
`~/llm-distillery/rescued_probes/`; manifest with sha256s committed at
`docs/evidence/2026-09-05-scorer-device-throughput/rescued_probes_manifest.txt`. They are
**not** in git — an owner decision, not something to do silently.
⭐⭐ **The uncomfortable part is that the substitution was numerically harmless**: the full
probe reads **16.417 ms** against the encoder-only **16.514** — the MLP head is free. **A
harmless-looking substitution is exactly what stops anyone re-checking the premise**, and the
premise was false.
⭐ **What found it was going and looking on the machine.** Four of the six defects in this
work were found that way, by a reviewer, not by reading code and not by 667 green tests.

## 2026-09-05 — rewriting an artifact made nine registry metrics untraceable
**Problem**: Corrected `EXP-022`'s write-up in place. `check_experiment_registry.py` then
failed with **9 FAILURES**: metrics recorded in the append-only registry no longer appeared in
any cited artifact.
**Root cause**: the registry's append-only rule protects the **entry**, and I had assumed that
was enough. It is not — an entry is a pointer, and rewriting what it points at destroys the
evidence while leaving the claim. **The record that a number was once believed survived; the
number did not.**
**Fix**: §7 of the write-up now keeps `EXP-022`'s figures verbatim in a superseded table, with
what moved and why. Checker back to `entries 23  metrics checked 298  untraceable 0`.
⭐ **The guard did the thing a guard is for: it refused work I was confident about.** I would
have committed the rewrite without noticing, because every number in the *new* document was
correct. **Correcting a document is a delete of its predecessor unless you carry the old
values forward.**

## 2026-09-05 (third session) — the `*_test.*` gitignore trap, third victim, because the fix was scoped to the instance [x3]

**Problem**: `scripts/gate/v8_smoke_test.py` was gitignored the moment it was written.
`.gitignore:170` carries `*_test.*` in a scratch-file block; it is a PATTERN, not a path.

**Root cause**: the 2026-09-04 rescue negated it **only under `docs/evidence/`** — and its own
note said so in writing: *"the rescue is scoped to `docs/evidence/` only; the pattern still
swallows `*_test.*` anywhere else in the repo."* That made it a fix for the instance, not for
the defect, and the note even named the second victim
(`filters/common/obituary_detector/validation/panel_obit_test.py`) without rescuing it.

**Fix**: negations extended to `scripts/`, `tests/`, `filters/`, `training/` and
`ground_truth/`. Verified in BOTH directions: the smoke test is stageable, and a
`scratch_probe_test.json` <!-- placeholder --> at the repo root is still ignored. ⭐ **The reusable part is how it
surfaced: `git add <explicit path>` WARNS, and `git add <dir>` does not** — the 09-04 loss was
silent for exactly that reason. Do not rely on the warning; the pattern is the hazard.
⚠️ A documented limitation that is left in place is a defect with a note attached, not a
mitigation — this one was re-read three times and rescued nobody.

## 2026-09-05 (third session) — the guard against guards-that-examine-nothing had a root that examined nothing

**Problem**: `check_claim_shapes.py` shipped with `experiments` in its JSON scan roots
behind an `endswith(".json")` filter. `".jsonl".endswith((".json",))` is **False**, so the
root contributed **0 files**, `experiments/registry.jsonl` — where every experiment's
headline numbers live — was never scanned, and the `if rel.endswith(".jsonl"): continue`
guard beneath it was **unreachable dead code**. The run printed PASS with a site count that
silently excluded it. This is inside the file written *because* a guard that examines
nothing reports success.

**Root cause**: `.jsonl` is not a suffix of `.json` — it is the other way round. The scan
root and its file-type filter were written in one line and neither was exercised: no test
asserted the root contributed anything, and the aggregate site count was non-zero from the
other roots, so nothing was visibly wrong.

**Fix**: JSON-lines artifacts are now named explicitly in `JSONL_FILES` and read
line-by-line; a missing one is CANNOT VERIFY. Proven by mutation on the real tree (M6: a
`[0.0, 0.0]` interval added to a registry row is now caught). ⭐ **The reusable part is the
per-root count**: emptiness was tested across all roots at once, so losing three of four
evidence directories took a check from 7 sites to 1 and still printed PASS. Each root is
checked separately now. **A site count is an outcome — print it per source, not in total.**

## 2026-09-05 (third session) — the fix deleted the trigger instead of the defect

**Problem**: a new check flagged an unbanded comparative ordering in
`docs/evidence/2026-09-05-adr023-op-point-table/README.md` §7. I rewrote the sentence to add
the band. The rewrite put the ordering verb on a different physical **line** from its two
numbers, so the per-line trigger stopped matching. The site was not qualified — it became
**invisible**. The check re-ran green, and a site count I had already published
(`quantified_orderings: 3`) failed to reproduce.

**Root cause**: the trigger was a text shape evaluated per line while the qualifier search
ran over the paragraph. Any edit that rewraps a line can move a claim out of scope, and the
green run afterwards is indistinguishable from a fix. Re-joined onto one line the paragraph
**still FAILED** — the hedges I had added matched no band vocabulary — so the claim was never
qualified at all; only its visibility changed.

**Fix**: triggers are sentence-scoped (list items and table rows are their own units), and
qualifier searches run on the flattened paragraph so a line break cannot decide a verdict.
⭐ **The rule, which generalises past this checker: after any edit made to satisfy a checker,
confirm the site is still EXAMINED — count sites before and after, not just the verdict.**
Logged as the 22nd occurrence of *establish what it excludes* in `memory/working-rules.md`.

## 2026-09-05 (third session) — a guard that passed on a MENTION, twice, inside its own fix

**Problem**: `check_design_weights` decides whether an analysis reads the design weights.
Version 1 was a substring test — and the first `# design-weights:` declaration written under
it explained the gap by *naming* `inclusion_probability`, so the check read the confession as
compliance. Version 2 excluded docstrings. Version 2 still passed when a review deleted the
**only** real weight read from `phase_c_outcome.py`: the field's name survived in an error
message and a JSON label. The docstring claimed *mention is not use* was fixed and a unit
test claimed to pin it.

**Root cause**: "does this file contain the string" and "does this file use it as a key" are
different questions, and the first fix answered the first question one shape more narrowly
rather than switching questions. Each version was tested against the instance that prompted
it.

**Fix**: `_reads_field` now requires one of three concrete AST shapes — a `Subscript` with a
constant string key, or a constant string argument to a call (an f-string is a `JoinedStr`,
so an interpolated error message no longer counts). The false-FAIL direction (a field name
held in a variable) is disclosed and safe: it demands a one-line declaration from a correct
script. ⭐ **A fix applied to one shape of a problem and named after all of them is the
shape to watch for** — the giveaway was that the mutation record said KILLED for a mutation
nobody had run against the file that mattered.

## 2026-09-05 (third session) — a scan root, a symlink and a decode, all silently narrowing

**Problem**: three ways the same checker could examine less than it appeared to. (a)
`os.walk`'s default does not follow symlinks, so a symlinked evidence directory contributes
zero files with no signal. (b) `errors="replace"` on a latin-1 markdown file silently drops
`±` — a band token — turning a properly-qualified ordering into a FAIL. (c) `CODE_ROOTS`
was the three directories that happened to hold an offender on the day it was written, so an
unweighted rate published from `training/` or `ground_truth/` was unchecked.

**Root cause**: all three are the hand-built-population failure at the level of the
*instrument's own reach*. Each default was chosen for the tree as it stood that hour.

**Fix**: `followlinks=True` with a realpath cycle guard; `Undecodable` raised and reported
as CANNOT VERIFY rather than a lossy read; `CODE_ROOTS` widened to nine directories, with
`filters/` deliberately excluded and the reason stated. ⭐ **And the widening was the one
that paid**: registering the three v8 splits as design-weighted populations — `test.jsonl`
IS the 660 drawn rows — surfaced **five analyses that were not sites at all**.

## 2026-09-05 (second session) — a comparison that could not have come out any other way

**Problem**: EXP-024 published *"the gate buys nothing — B and C give identical TP at all
eight k"* as a measured result. It was arithmetically forced.

**Root cause**: B and C can only differ once a **screened** row outranks the k-th highest
stage-2 score. Max `probe_reg_large` score among screened rows is **1.4921**; the k-th
highest is **2.7787 even at k=60**. The smallest k at which they could differ is **140**,
and the grid stopped at 60 — 1.29 score points of margin. The equality was guaranteed
before the data were read.

**Fix**: `adr023_op_point_table.py` now computes that k and prints it beside the verdict, so
the comparison always ships with the range over which it could have failed. The conclusion
(drop the gate) survives on two independent legs that need no data: 0 of 35 positives
screened out, and the 85.7% break-even against ~90% routing.

## 2026-09-05 (second session) — an ordering published as a finding, with no band [x2 — recurred 2026-09-17, see the entry at the top]

**Problem**: *"AUC would have picked the wrong arm"* was labelled ⭐⭐ THE REUSABLE FINDING
in four places, on a gap of **+0.0014**.

**Root cause**: the two arms' AUCs were compared as point estimates. With its band the gap
is CI **[−0.0448, +0.0476]**, **P = 0.523** — a coin flip, the band ~30× the gap. CLAUDE.md
already states the rule (*two models whose bands overlap are NOT DISTINGUISHABLE whatever
their point estimates say*); it was applied rigorously to the TP comparison in the same
document and not at all to this one.

**Fix**: retracted. The script now computes bands for every ranking-metric delta it reports.
⚠️ The converse is the part worth keeping: **AUC separates the student from `probe_reg_large`
(P = 0.995) where the op-point test cannot**, so "the op-point is the better criterion" and
"the op-point test is underpowered" are both live, and the artifact now says so.

## 2026-09-05 (second session) — a bootstrap that froze what it was resampling

**Problem**: the paired bootstrap emitted a **zero-width 95% CI** (`[+0,+0]`) for
`student_raw` at k=30 and k=43, published in the committed output.

**Root cause**: the top-k masks were computed once on the full sample and only the row
indices resampled — a McNemar discordant-pair interval on a *fixed* classifier, when top-k
is sample-dependent. Zero discordant rows therefore gave zero width. Measured, **90.6%** of
replicates did not even surface k rows, so the design's own `FP = k − TP` premise held in
fewer than 1 replicate in 10.

**Fix**: re-selection bootstrap — top-k recomputed inside each replicate — plus a **null
control** (an arm against itself) that must return exactly `[0,0]` and does. ⭐ A zero-width
interval is proof an interval is not measuring sampling variability; it is not a strong
result.

## 2026-09-05 (second session) — unweighted figures on a design-weighted sample

**Problem**: every figure in EXP-024 was unweighted. The v8 test split is drawn under a
design with `inclusion_probability` spanning **25.1×** over 16 strata.

**Root cause**: the dumps carry ids and scores, not weights, so nothing in the analysis path
surfaced the design. The *previous day's* artifact on the same rows
(`gating_tradeoff.py:118`) used Horvitz–Thompson weights deliberately.

**Fix**: `--corpus` arm added; it refuses a partially-weighted table. Weighted, the positive
rate is **3.1638%** against the unweighted **5.3030%**, and the student leads
`probe_reg_large` at every share tested (0.529 vs 0.478) where unweighted they tie. **The
headline finding was a property of the sample, not the population.**

## 2026-09-05 (second session) — the arms were on different devices and nothing said so

**Problem**: EXP-024 compared a **CPU**-scored student against **GPU**-scored probes.
Neither the four-lens review nor the mechanical battery noticed; it was found during session
close while following up the open-issue list.

**Root cause**: `scores_raw.jsonl` / `scores_calibrated.jsonl` are the 16-minute CPU pass;
EXP-019's probe dumps say *"same corpus, splits, --seed 42, GPU"*. Confirmed rather than
inferred: `student_raw` reads recall **0.4857**, matching EXP-015's CPU **0.486** against
CUDA **0.514**. CPU→CUDA is max |Δ| **0.1956**, 3 flips at 4.5 (#104).

**Fix**: recorded as README §6.7 and in H-V8-22, with the direction stated — CUDA *gains* the
student a TP, so the CPU pass **understates** it and the "not distinguishable" result is
weaker, not stronger. ⭐ **The confound was conservative by luck, not by design.**

## 2026-09-05 (second session) — I read `tail`'s exit status while reading the rule against it [x3]

**Problem**: ran `run_verify_annotations.py 2>&1 | tail -2; echo "exit=$?"` during `/curate`
and reported `exit=0`. That is `tail`'s status.

**Root cause**: the 3rd occurrence of a rule already in `working-rules.md` at 2 occurrences —
and it happened in the same minute the rule's own text was on screen, having been printed by
a grep I ran.

**Fix**: `out=$(cmd 2>&1); rc=$?` then inspect. True status was 0, so the reported figure
was right — **by luck**. ⭐ *Articulating the rule is not applying it*: the reading and the
violation were seconds apart.

## The tests written to prove a guard could not see its worst failure (2026-09-06)

**Problem**: `ground_truth_gate.py` gained a rule that carries a hand-written `provenance`
block across reruns, plus four tests. All four passed. A review then mutated
`report["provenance"] = prior["provenance"]` into `report.update(prior)` — which reverts
**every freshly computed metric** to the previous report's — and **all four still passed**.
The escaping failure is the worst one that file can have: a retrained model's gate report
keeping the old model's recall.

**Root cause**: none of the four varied the *scores* between the two gate invocations. They
proved "a provenance block survives a rerun" and could not distinguish that from "the whole
prior report survives a rerun", because on identical inputs the two are the same output.
I mutation-tested three ways and every mutation I chose attacked the mechanism I had just
written, not the *blast radius* of getting it wrong.

**Fix**: a fifth test that makes the model worse between runs and asserts recall moved
1.0 → 0.0 while `provenance` persisted. ⭐ **When a guard copies data forward, the test must
vary the data it must NOT copy.** Mutating the line you wrote checks your intent; mutating
what the line *touches* checks the damage.

## A guard against stale provenance that shipped stale provenance (2026-09-06)

**Problem**: the same carry-over was written *because* a gate report could not be attributed
to a device (#104). It then reintroduced that defect one layer up: rerun the gate on a
different dump and the prose still describes the old run — beside a freshly correct `inputs`
block whose sha256s make the report look newly attributed.

**Root cause**: I treated "never delete the block" as the whole requirement. Carrying data
forward and *vouching* for it are different acts, and the fresh metadata beside it did the
vouching.

**Fix**: stamp the block with a fingerprint of the inputs it described, and report three
states — `matches` / `UNVERIFIED` / `⛔ STALE`. ⚠️ **My first version conflated the last two**
and its own test caught it: a hand-written block has no fingerprint, so *unknown* was being
reported as *stale*, which never converged and would have fired on every rerun. ⭐ A warning
that cries wolf is ignored within a day, so *unknown* and *wrong* must stay distinguishable.

## Being careful cost 4.2 GB of a 15 GB tmpfs (2026-09-06)

**Problem**: mid-session a plain `pwd` failed with `write error: Disk quota exceeded`.
`/tmp` was 81% full; 4.2 GB of it was one directory in this session's own scratchpad.

**Root cause**: I told a review lens to copy the repo to `/tmp` before mutating it, so it
could not damage the working tree. The copy included a **2.1 GB `.venv`** and the filter
packages. The instruction was right about safety and blind about cost.

**Fix**: removed it (`/tmp` 3.0 GB → 11 GB free) and added the rule to
`.claude/skills/review-changes/SKILL.md`: **mutate in place and restore from git, or copy
only the file under mutation.** ⚠️ Note where the space actually was — the caches a reader
would reach for first (`~/.cache/huggingface` 7.6 GB, puppeteer 1.9 GB) sit on a disk with
**222 GB free**, so clearing them would have freed nothing where the shortage was.

## A guard against orphaned commits could not detect an orphaned commit (2026-09-06)

**Problem**: `train.py`'s `resolve_git_provenance()` and
`scripts/verification/check_training_provenance.py` were written because
`human_thriving v8`'s adapter was built by a commit `git commit --amend` had orphaned.
Both shipped unable to detect that state.

**Root cause**: `git branch --contains <sha>` prints the pseudo-branch
`* (HEAD detached from abc1234)` when HEAD is detached. `lstrip("* ")` leaves
`(HEAD detached from abc1234)` — a non-empty string — so the list was truthy and the
"reachable from no branch" refusal never ran. A second hole beside it: `git -C` walks
**upward**, so a plain copy of the tree inside any other repository answered
`--is-inside-work-tree true` and stamped the *enclosing* repo's HEAD as clean.

**Fix**: `git for-each-ref --contains <sha> refs/heads refs/remotes`, which enumerates real
refs and cannot emit a pseudo-branch; plus `rev-parse --show-toplevel` compared against the
directory itself. ⭐ **Both were found by mutating the WORLD the guard runs in** — checking out
a detached HEAD, nesting a copy — rather than the guard's own lines. Neither is visible from
the code.

## An exemption that could not tell a saturated instrument from a switched-off one (2026-09-06)

**Problem**: `check_claim_shapes.py` gained a `_saturated_band` exemption letting a zero-width
`#95` band pass when `indeterminate_by_cell` is all zeros. Review showed it exempts a gate run
made with `--noise-floor 0`, where every cell is zero **because the instrument was disabled**.

**Root cause**: the exemption read the cells and not the parameter that produces them.
`noise_floor` is a sibling key in the same JSON object. Two smaller holes in the same
predicate: `any(ind[c] ...)` treated `null`, `""`, `[]` and `false` as "no indeterminate rows"
— and `null` means *unknown*, not zero — and the cell mapping was **wrong against the
producer**: `ground_truth_gate.py` computes precision and F1 bands from all four cells, while
the table declared `precision: (tp, fp)`, so a band was exempted with a printed reason that
was false.

**Fix**: read `noise_floor` and require it positive; require `isinstance(v, int)` and `v == 0`;
correct `BAND_CELLS` against the producer's arithmetic and cite the line numbers in a comment.
⭐ **A printed reason is an assertion** — the NOTE said "no row is within the noise floor" while
four rows were.

## The documented regeneration command reintroduced the defect it documented (2026-09-06)

**Problem**: `.gitignore` gained a comment giving the command to regenerate a model card:
`upload_to_huggingface.py --filter <dir> --repo-name <id> --card-only`. Run verbatim against
`human_thriving v8` it silently rewrote 17 lines to epoch 6's metrics beside epoch 5's weights,
exit 0.

**Root cause**: `--selected-epoch` was added in the same commit *because* the generator reads
`training_history[-1]`, and then omitted from the command written to document it. The flag and
its own instructions were written minutes apart.

**Fix**: the comment now carries `[--selected-epoch N]` with the reason, and says how to
recover N (match `best_val_mae` against `training_history.json`). ⚠️ Three other surfaces said
"epoch 4 of 6" for a filter that now ships epoch 5 — one of them in `--help`, i.e. visible to
someone who would then pass `--selected-epoch 4` deliberately.

## A filter was deployed, verified by execution, and called by nothing (2026-09-07)
**Problem**: `human_thriving v8` shipped to NexusMind (PR #452) with every gate green —
package synced, weights pre-placed on gpu-server, scorer restarted, CODE_REVISION
round-tripped, `verify_filter_package.py --check-hub` 9/9, and a direct
`POST /filter/human_thriving/score` returning wa 5.604 → medium. I published "live in
production". No production cycle would ever have called it: `human_thriving` was missing from
`pipeline.enabled_filters`, the list `scripts/main.py:2569` reads and iterates. Left as
shipped, `data/filtered/human_thriving/` stays empty forever and Phase E normalization — which
fits its CDF from that directory — becomes impossible.
**Root cause**: I proved the CALLEE and inferred the CALLER. "Can it score when asked?" and
"does anything ask it?" are different questions and the first is the easy one, so the
deliberate outcome check I ran to satisfy the working rule answered the wrong one. Compounding
it: the post-deploy smoke suite passed through the whole deploy **having never loaded v8**,
because it had no fixture for that filter — a suite that reports success on a filter it never
exercised. And a NEW filter has an enablement step that a version upgrade does not, so every
guard in the chain was built for the upgrade case.
**Fix**: NexusMind PR #453 — add `human_thriving` to `pipeline.enabled_filters` AND add the
missing smoke fixture, which must land together because `deploy_filters.sh`'s fixture-name
alignment gate requires every fixture's filter to be enabled. Found only because writing the
fixture forced a read of that gate. Recorded as the 21st occurrence of *prove the outcome
changed* in `memory/working-rules.md`.

## A published count came from a grep with two lossy stages (2026-09-07)
**Problem**: I told a peer session that ovr.news names `uplifting` in "8 distinct files" and
then listed 7. The real figure is 12. I used the wrong number to correct a peer who had it
right.
**Root cause**: Two independent truncations in one pipeline. The `--include` list was
`*.ts *.tsx *.svelte`, which silently dropped `.astro` — and the two `.astro` hits are the page
layer, the most consumer-facing files of the twelve. Then the output was piped through
`head -15`, which cut three `.ts` files the include DID cover. Neither stage announced itself,
and the count was published without the enumeration that would have made it re-derivable.
**Fix**: Re-derive with `grep -rl <term> src --exclude-dir=node_modules | sort` and publish the
LIST, not the number. `#151` carries the enumeration rather than the figure. The tell was
visible in my own sentence — "8 distinct files" above a list of 7 — so an internal
count/enumeration disagreement is worth treating as a defect signal in itself.

## A nested score field read as a clean zero, three times (2026-09-07)
**Problem**: Sizing Phase E from production output, I measured "rows ≥ 4.5" in
`data/filtered/uplifting/filtered_*.jsonl` three times and got three wrong answers before the
right one: `>= 4.5: 0 (0.0%)`, then `raw_weighted_average: ABSENT on all rows` with
`tier counts: [(None, 2530)]`, then `scored rows: 0 of 2530`. Every one looked like a finding.
The truth is **147 of 2,530 (5.81%)**.
**Root cause**: The filter scores are not top-level on those rows. They live one level inside
`nexus_mind_attributes.<filter>`, which is how `fit_normalization.load_weighted_averages_*`
reads them. Top level carries only `_commerce_score` / `_obituary_score` /
`_violence_promotion_score`, so a top-level lookup returns a **plausible zero rather than a
KeyError** — and 0% surfacing is exactly the shape a real problem would take on a
newly-deployed filter. The second attempt walked the structure and *printed the right block*,
but the aggregation loop beneath it iterated one level too shallow, so the diagnostic and the
count disagreed inside one script and the count was the half I read.
**Fix**: Read a derived population the way its consumer reads it — for normalization that is
`nexus_mind_attributes.<filter>.raw_weighted_average` falling back to `weighted_average`. Where
a lookup can miss silently, print the denominator and the min/max beside the count: `min 0.868
max 6.961` is what finally showed the field was live. Better still, and what the peer session
did: **run the wrong reading as a CONTROL beside the right one**, so the zero is visibly an
artifact rather than a result. Recorded in `docs/TODO.md` beside the Phase E step.

⭐ **The deeper root cause is not the wrong field — it is that the wrong denominator came out
approximately right.** (Framing from the `nexusmind-0a` session, 2026-09-07, which had the same
error in four places.) Sizing Phase E off rows *written* (~2,500/cycle) gave "1–2 cycles";
the true figure, rows *above the op-point*, gives 2. **A coincidentally plausible conclusion is
the strongest protection a bad measurement can have** — it is what stops anyone re-deriving it.
That generalises past this case and explains why all three of my zeros read as findings rather
than as instrument failures: each was a number a real problem could plausibly have produced.
⚠️ Corollary for this project's own habit: *predict the range first* only helps if the
prediction and the measurement do not share a source. Here they did — both came from the same
misunderstanding of what a filtered row contains.

## An empty directory that reads as a completed cycle (2026-09-07)
**Problem**: `data/filtered/human_thriving/` existed on sadalsuud with 0 rows. A peer session
reported a dual-scoring cycle had run at ~12:09; it was 11:04, and the last cycle had run at
08:04 — before the deploy.
**Root cause**: The directory was created at 10:10 by my own failed
`run_filters.py --filter human_thriving` attempt — `FilterRunner.__init__` sets up its data
directories before `_load_filter` raises, and it raised (`No module named 'torch'`: sadalsuud
orchestrates, gpu-server scores over REST). So a run that scored nothing left the artifact a
successful cycle would leave.
**Fix**: Count ROWS, never test for the directory, and confirm a cycle actually ran with
`systemctl list-timers fluxus-collection.timer` — LAST must be after the deploy. Both are now
in `docs/TODO.md`'s step-1 measurement block.

## Enabling a new filter took the whole pipeline down (2026-09-07)
**Problem**: The first cycle after enabling `human_thriving v8` ran the shared preprocessing
stages 7–10× over normal — og:image backfill 21,245 pages against a 2.6k–3.1k baseline, hero
image extraction 41,435 against 3.3k–4.0k, ML candidates 18,206 against a 3,000 cap. It hit the
og:image stage's own 3,600s budget (dropping 5,203), and was on course to exceed
`TimeoutStartSec=4h` **before scoring started** — a SIGKILL with zero filtered output for all
six filters, not just the new one.
**Root cause**: NexusMind skips articles listed in `data/raw/.processed_ids_<filter>.json`
(`scripts/main.py:1565`). A new filter has no such file, so it loads **every** article inside
`max_article_age_days: 3` — 18 collection cycles of backlog, ~41,400, against the observed
41,435. That would be private to the new filter except story dedup and image analysis run once
on the **union of every enabled filter's pool** (`scripts/main.py:3555-3567`), so one cold start
inflates them for everyone. ⛔ **And it does not self-heal**: `_save_processed_ids` runs at
`scripts/main.py:2141`, after the per-filter scoring loop, so a kill before scoring leaves the
file unwritten and the next cycle rebuilds the identical pool — a kill loop every 4h until
someone intervenes. The thing that would end it is what the kill prevents.
**Fix**: Seed the file from any established filter before enabling a new one — same corpus, same
id space (all five sat at 121,881–121,883). Copy it **wholesale**: the `versions` sidecar is
`{id, content_hash, collected_date}`, the superseded-rows mechanism (#119), and it is
filter-agnostic corpus data, so stripping it costs the new filter change detection for the whole
window. Now `docs/RUNBOOK.md` § *4b*, as a step that exists for a new filter name and not for a
version bump.
⭐⭐ **THE SHARPEST STATEMENT OF IT, from the `nexusmind-0a` session that ran the mitigation:
the cost and the thing that would end it are on OPPOSITE SIDES OF THE SAME TIMEOUT.**
`_save_processed_ids` sits after the scoring loop, so the very first run of a new filter is the
one that both incurs the full backfill *and*, if it does not finish, fails to record that it
happened. That is the general shape to look for — **a one-time cost whose receipt is written
only on success is not one-time; it is a loop.** Worth checking wherever a first run is
expensive and its completion marker is written at the end.
⭐ **The lesson under the mechanism**: I verified that enabling the filter would make it score,
and never asked what its FIRST cycle would cost. Same shape as the same day's earlier miss one
layer out — I checked the thing I changed, not the system around it. A per-entity progress marker
means the entity's absence is not a neutral starting state, it is a full backlog; and where an
expensive stage is SHARED across entities, one cold start is everyone's outage.

## A cross-agent export carried the wrong FIELD, and the false finding was mechanistically perfect (2026-09-08)
**Problem**: A peer session exported v8's 63 live passers for auditing. `len(content)` said 37 of 63
were under 300 characters, median 233, with the short share *rising* by score band (51% → 67% → 80%).
That is a train-to-production distribution shift with a named mechanism — the training corpus passed
an oracle 300-char floor, so the student had never seen stub-length input — and it explained the data.
It was entirely an artifact.
**Root cause**: the export wrote `d.get('original_content') or d.get('content')`, preferring the
**pre-enrichment RSS teaser**. By the `content_length` stamp, exactly **one** row of 63 is under 300
and the median is 4,098. The 79-char "South Africa has emerged from the 2026 winter season without a
single blackout" was the teaser; the scorer read the full article.
**Fix**: read length off the **stamp**, never off the row — the rule `memory/stamp-contract-integrity.md`
already states, arriving through a field substitution rather than a null. Two things contained it:
the claim was published with its own killer attached (*"if `content` is a stored snippet, every number
above dissolves"*), and the check that could settle it lived with the party who held the stamps.
⭐ **A finding can be mechanistically plausible, have a named cause, explain the data, and be false.
That combination is the one where "someone should check" reliably fails to become "someone checked" —
so name the disconfirming test and give it an owner in the same message.**

## A projection corrected by a better projection leaves the frame untested (2026-09-08)
**Problem**: Two sessions independently sized Phase E's remaining wait. One said ~3.2 cycles (63
passers/cycle), the other ~7.7 (26/cycle). Each correctly diagnosed the other's denominator — 63 came
from a 2.45× backlog-draining cycle, 26 was the lowest normal cycle. Both were wrong.
**Root cause**: `MIN_NORMALIZATION_ARTICLES = 200` is **cumulative across cycle files**, not per-cycle
— `scripts/normalization/fit_normalization.py:306` globs `filtered_*.jsonl` and pools them, enforced at
line 723. **168 rows already existed on disk** while both sessions modelled a *rate* against a fresh
start. `ls` and a sum answered it, at any point in the preceding day.
**Fix**: before projecting a rate to a threshold, ask whether the quantity is **cumulative and already
measurable**. ⭐ **The correction round is what made it durable**: a disagreement about the number
looks like the method being tested, and the shared frame comes out *stronger* for having two
independent sources agree on it. A correction that changes the number and not the frame is the most
convincing way to stay wrong.

## A registered acceptance rule that could only ever find fault (2026-09-08)
**Problem**: A pre-registered decision rule compared a 63-article result against a 17/20 comparator by
interval overlap: entirely above → supports (a), entirely below → supports (b), overlap → not
distinguishable. It was written before any verdict was read, which is correct practice, and it was
still broken.
**Root cause**: the comparator's Wilson interval is [0.6396, 0.9476] because it rests on **20**
articles. A **perfect 63/63** has a Wilson lower bound of **0.9425** — below 0.9476. **No outcome of
the run could return "supports (a)".** The stated boundaries (a ≥ 46, b ≤ 38) also matched neither
that rule (a never, b ≤ 32) nor a proper Newcombe difference test (a ≥ 62, b ≤ 38) — the b boundary
was right *under a test that was never registered*, which is worse than a wrong answer because it
validates the method.
**Fix**: **before demanding a bar, prove the bar is reachable** — evaluate the rule at its extreme
outcomes. The mirror of this repo's own `feedback-prove-the-bar-is-reachable`, pointing the other way.
Where superiority is unprovable at the available n, register the question **one-sided** and say so:
"does it fall materially below" is answerable and decision-relevant; "is it better" was not.

## A null between two labellers is a RATE-null, and hides case-level disagreement (2026-09-08)
**Problem**: Holding rubric and truncation fixed, two judge families differed by −0.032 on the
in_scope rate (McNemar p = 0.73) — a clean null that reads as "the families agree".
**Root cause**: they disagreed on **8 of 62 articles**, Cohen's **κ 0.587**, 5-way verdict agreement
50/62. Truncation was *exactly* 0.0000 and still moved **6 of 62** verdicts (b=3, c=3). Only the
prompt effect was large *and* directional (b=12, c=1). Churn that cancels is invisible in a rate.
**Fix**: for any null between two labellers, **print the discordant-pair counts and κ beside the
rate**; a p-value on a difference of proportions says nothing about per-item agreement. Report *"the
rates are indistinguishable"*, never *"it doesn't matter"* — different claims, only the first measured.
⭐ This is `CLAUDE.md`'s prefilter rule (*rate agreement and safety-to-enforce are independent
properties*) arriving in a completely different place, which is the argument for reading it as general.
It also bounds what a per-row citation can carry: at κ 0.587 no single article is *proven* mis-scored,
so a 12-row table is evidence as a **pattern** and not as twelve findings.

## "This repo" in a cross-session message resolves to the SPEAKER's repo (2026-09-08)
**Problem**: A peer wrote *"this repo already has the confound on record at 37.4%"*. I grepped
**llm-distillery**, found `37.4` (CLAUDE.md's byte size, 37.4k), and reported their figure as a
coincidence with a file size. Their number was right: 7,816 / 20,881 = 37.43% of lens-rows, recorded
in **NexusMind**.
**Root cause**: `this repo` is deictic. Across a session boundary it binds to the sender's tree, not
the reader's — and the reader has a same-shaped artifact to find, so the wrong answer is available.
**Fix**: qualify every cross-repo reference in a message the way `feedback-bare-issue-number-resolves-locally`
already requires for issue numbers; the failure mode is identical and the pronoun is worse, because
`#167` at least looks ambiguous. ⭐ **And before contradicting a peer's measurement, check that you
searched the tree they were describing** — a dismissal is a claim (`feedback-a-dismissal-is-a-claim`),
and this one had a plausible coincidence doing the work of the check.

## The frame mixed two instruments, and the control that should have caught it was a print (2026-09-08)
**Problem**: `EXP-030`'s section 2 — Spearman, Pearson, the volume-matched top-K and every
per-dimension delta — was computed over all 15,372 rows. **3,162 of them carry an e5 PROBE estimate
in `raw_weighted_average`, not a Gemma score** (`stage_used == "stage1_low"`). The clean both-stage2
frame gives Spearman **0.7177** where the mixed frame gave 0.5551, and every dimension delta moves
(`human_wellbeing_impact` −0.618 → −0.882).
**Root cause**: two failures stacked. The evidence had a control for exactly this, and it was a
`print`, not an `assert`, inside a section headed *"they run in `compare.py` and assert, they are not
claims in prose"*. And its wording — *"every surfaced row is stage2, so `raw_weighted_average` is a
Gemma output everywhere it is used here"* — was **true in its first clause and false in its second**:
the probe rows never surface, so sections 1/3/4/5 were genuinely safe, and section 2 does not use the
surfaced set.
**Fix**: the control asserts (`assert set(surf_st) <= {"stage2"}`), section 2 leads with the
both-stage2 frame and prints the mixed one beside it, labelled. ⭐ **The general shape: a control
scoped to one population, described as though it covered the file.** When a control's sentence
contains "so", check the second clause separately — CLAUDE.md's own rule already says *condition on
`stage_used` before reading `raw_weighted_average` as a model output*, and this session cited that
rule in the README while breaking it three sections later.

## The chance level was a straw null, and the null that mattered was free (2026-09-08)
**Problem**: `EXP-030` published *"volume-matching v8 recovers only 57.0% of v7's passers, against a
chance level of 7.70%"* to support *"v8 is not a rescaled v7"*. 7.70% is the overlap of a **random**
top-K — nothing would produce it. The live alternative is *v8 = a monotone-noisy, rescaled v7*.
Built it (noise on v7 tuned until its Spearman with v7 matches v8's, quantile-mapped onto v8's exact
marginal): on the published frame it gives overlap **64.4%** and within-union rho **0.3654
[0.3281, 0.4172]** against an actual 0.3463 — **the actual sits inside the null**. The evidence did
not exclude the thing its headline claimed.
**Root cause**: the null was chosen because it was easy to compute, not because anyone would assert
it. It is the `feedback-prove-the-bar-is-reachable` failure with the sign reversed — an unfalsifiable
bar rather than an unreachable one.
**Fix**: `compare.py` runs the noise null on both frames and prints null-vs-actual. On the clean
both-stage2 frame the null gives 76.8% / 0.5630 against 57.5% / 0.3436 and is excluded decisively.
⭐ **Two lessons and the second is the sharper one**: name the null someone would actually argue for,
and note that the *same* contamination that inflated the statistic also **deflated the null toward
it** — a mixed frame moves the measurement and its comparator the same way, so nothing looks wrong.

## Spearman computed from global ranks restricted to a subset is not Spearman (2026-09-08)
**Problem**: published *"Spearman rho = 0.224 within the union of the surfaced sets"*. The script
ranked all 15,372 rows once and then Pearson-correlated those **global** ranks over the 1,200-row
subset. Spearman re-ranks **inside** the sample. The statistic is **0.3463** — the published figure
was 35% low, and it was quoted in an issue comment, a registry entry and the always-read TODO.
**Root cause**: `ranks()` took no key list; the subsetting happened at the correlation step, which
looks like restriction and is a different estimator. Nothing in the pipeline could catch it — the
registry's traceability checker confirms a number appears in an artifact, not that the artifact
computed the right thing.
**Fix**: `ranks(f, ks)` ranks within `ks`; `scipy.stats.spearmanr` on the committed manifest
reproduces 0.3463. ⭐ **For any statistic with a "computed within" definition, verify against a
library implementation on the committed artifact once** — the check is one line and it is the only
thing that distinguishes a named statistic from a plausible arithmetic neighbour.

## Two counts across different denominators are not a comparison (2026-09-08)
**Problem**: 10 of `EXP-029`'s 12 prompt flips fall in the `both` set and 2 in `v8_only`, from which
I concluded *"the owed prompt work is not what separates the two lenses"*. The two sets are **56 and
6 rows**. On rates: v8-only **2/6 = 33.3%** vs both **10/56 = 17.9%** — flips are **1.87× enriched**
among the rows that distinguish the lenses, the opposite of the published direction. Fisher two-sided
**p = 0.328**, so six rows settle nothing either way.
**Root cause**: the counts were *interesting* — 10 vs 2 is a striking split — and the denominators
were in a different part of the analysis. `feedback-rate-needs-population` names exactly this and I
had written the denominators into the same file three sections earlier.
**Fix**: `flip_overlap.py` prints both rates, the ratio and a Fisher p, and its denominators are
**panel membership** rather than manifest membership (57 vs 56 — the panel dropped one row). ⭐ **A
split that is striking as counts is the specific case to convert to rates before believing**, because
the striking-ness usually comes from the set sizes.

## A guard whose absolute bound EQUALS the op-point is a density test (2026-09-08)
**Problem**: `fit_normalization.py` refused to write `human_thriving v8`'s normalization — *"Lowest
observed article (4.51) is above MAX_NORMALIZATION_RAW_MIN (4.5): the reference population never
reaches the visibility threshold"*. The fit was correct: 202 rows drawn at raw ≥ 4.5 from 18,418
scored, `sample_min` 4.5069, gap to the anchor **0.0069** against the advisory tier's 0.5.
**Root cause**: the hard tier compares `sample_min` against the literal **4.5**, and this filter's
op-point **is** 4.5. Every honest fit above a 4.5 bar has a minimum above 4.5, so the guard passes
only if the minimum rounds to 4.5 at four decimals — a **5e-5 window**, i.e. a test of sample
density. The block's own comment names the stale premise: *"no false-block possible for any real
op-point (3.75/4.0)"*, written 2026-07-16, before #102 moved `uplifting v7` to 4.5. v7 passed it in
August with a true `sample_min` of **4.500027** on 15,698 rows; **a refit of v7 on four cycles today
would fail it** (min 4.5018). Same filter, same op-point, opposite verdict.
**Fix**: not changed — it is a deploy-path guard, so llm-distillery#154 carries the diagnosis and
three options for the owner. ⭐ **A guard that enumerates the values it was safe for has a premise
that expires**: list the enumeration in the comment (this one did) and re-run it when a new value
joins the set. ⛔ And the fix is two files — `tests/unit/test_normalization_invariant.py:190`
asserts the same bound on every committed package, so a fitter-only change makes the output
uncommittable.

## An in-sample share measured against a percentile gate is a tautology (2026-09-08)
**Problem**: published *"60.4% (122/202) of v8's surfaced rows would clear NexusMind's normalized 4.0
enrichment gate"* and set it beside `uplifting v7`'s measured 60.0% as though the two were
comparable.
**Root cause**: the CDF was fitted on the **same 202 rows** the share was then measured over, and the
normalized scale is `10 × CDF`, so *"share above normalized 4.0"* is *"share above this sample's own
40th percentile"* — **~60% by construction**, whatever the model does. v7's 60.0% is out-of-sample
(fitted 2026-08-10 on 15,698 rows, measured over 82 later cycles) and is a measurement. The two
numbers agreeing to 0.4pp read as corroboration and were nothing of the kind.
**Fix**: labelled as a projection, and the transferable quantity stated instead — the effective raw
bar for enrichment lands at **4.872** against an op-point of 4.50. ⭐ **When a threshold is defined
as a percentile of a fitted distribution, any share measured on the fitting sample is arithmetic.**
The tell is agreement that is too good: `feedback-predict-the-range-first` says state the believable
range first, and *"about 60%"* was predictable from the gate's definition alone.

## A judge's verdict is a rate; two judges' verdicts are a rate and an instrument check (2026-09-08)
**Problem**: The Thriving harm panel ran two judges — DeepSeek and Gemini — and they disagreed on
**61 of 137** articles, Cohen **κ 0.375**. On the same rows, `harmful` reads **3.3%** (DeepSeek)
or **23.3%** (Gemini) for `v7_only`: a factor of seven. Either number alone would have been
published as *the* harm rate.
**Root cause**: I picked two judges to defeat an authorship confound — v7's oracle is Gemini,
v8's is DeepSeek, so each family flatters its own lens — and got a second, unplanned result: the
**absolute level of a judged rate is not a property of the articles**. The *within-judge*
comparisons agreed on direction in every case; the levels did not agree at all.
**Fix**: report within-judge comparisons and never the absolute level, and say so at the point of
citation rather than in a caveats section. ⭐ **The design generalises past this confound: when a
conclusion depends on two measuring instruments being independent, run both and ASSERT they
measurably differ** — `analyze.py` fails if the two judges agree on every row, because that state
means the cross-family design proved nothing while looking maximally clean. **A control that
fires when the result is too tidy is rarer than one that fires on a bad result, and this is the
shape that needs it.**

## `cmd | tail` turns a guard's exit code into 0 — three instances in one evening, two repos (2026-09-08)
**Problem**: The Gemini judge arm aborted correctly after 5 consecutive HTTP 429s and exited **3**.
My invocation was `python3 judge.py … 2>&1 | tail -4`, so the pipeline reported **exit 0** and the
run read as a clean completion. It was caught only because the output file was missing.
**Root cause**: a shell pipeline's status is the **last** command's. Every guard in the harness
was correct — the checkpointing, the retry, the consecutive-error abort, the refusal to write
ERROR rows — and all of it was silenced one layer up, at the call site.
**Fix**: `PIPESTATUS`, or do not pipe a command whose exit code is the result. ⭐ **The general
form, and it is why this recurs: the defect is at the INVOCATION, not in the checked thing, so no
amount of hardening the guard prevents it and no checker that reads the guard can see it.** Third
instance this evening across two repos — the NexusMind session masked its verify runner's output
entirely by the same route, and this repo already logs the shape at `[x5]`. **When a guard's exit
code decides anything, invoke it bare and read `$?` on the next line.**

## The record held the diagnosis; nobody had drawn the consequence (2026-09-08)
**Problem**: v8 leaks its harm gate because a **binary scope gate is a step function and the
student is a regression head**. Every input to that sentence was already written down — ADR-015
recorded the identical bimodality on `thriving v1` (*"a sparse 2-5 dead zone the student model
couldn't learn"*), the 2026-08-28 session found `scope_verdict` zeroes all six dimensions and
called v8 *"a STEP FUNCTION"*, and #135 was filed off it. **Nobody joined them.**
**Root cause**: the 08-28 finding was framed as **oracle label noise** — *13% of identical re-runs
flip the gate*, i.e. a problem for k and for cost. The consequence for the **student** — that the
distillation target contains a discontinuity the architecture cannot represent — is one step
further and was never taken. The owner recognised the shape immediately when shown the symptom;
the record could not surface it because it was filed under a different question.
**Fix**: when a finding is filed, ask **who else consumes this quantity** — here, the oracle's
gate is also the student's target, so a fact about the gate is automatically a fact about the
training signal. ⭐ **And searching the record for a REMEDY is not the same as searching it for a
DIAGNOSIS**: all three prior bimodality fixes were findable, and all three were inapplicable
(they changed the target; v8's target is the harm rule we require). **A precedent that matches the
symptom can still be unavailable — check what made the earlier fix legal, not just that it worked.**

## A test fixture is a POPULATION, and mine excluded exactly the rows at risk (2026-09-08)
**Problem**: Fixing #155 (`prepare_data.py` dropping the oracle's non-dimensional output) I wrote
six tests that enumerate the *input* rather than an allowlist — deliberately, so a new oracle field
would be covered the day it appeared. The review then applied one mutation,
`'oracle_meta': {k: v for k, v in analysis.items() if not isinstance(v, list)}`, and **all 35 tests
passed** while the real corpus lost `scope_verdicts_per_run` on **6,586/6,586** rows and `runs` on
6,130.
**Root cause**: the fixture's docstring said *"shaped like `labels_v84_merged.jsonl`"* and it was
not. It carried 12 scalar keys against the real 20 and **omitted every value that was a list or a
dict** — so "enumerated, not allowlisted" was true of the wrong population. The real file also has
**two** shapes (6,130 rows: float dimensions, `runs` a list; 456 rows: `{"score": float}`
dimensions, `runs` an **int**), and the fixture modelled neither exactly.
**Fix**: both real shapes are now fixtures, plus a test that reads real rows off disk and skips when
the gitignored corpus is absent. ⭐ **The durable lesson is that this is #155's own failure mode one
level up** — the thing meant to detect a silent drop could not see the fields most likely to be
dropped. A fixture is a hand-built population and inherits every hazard of one; the tell is that it
contains only the *easy* types. **Ask what a fixture EXCLUDES before trusting a green test**, and
prefer one row read from the real artifact over any number of invented ones. Extends the auto-memory
entry `feedback-hand-built-population` to test fixtures.

## I shipped a negative in a commit before running its positive control (2026-09-08)
**Problem**: Measured that regenerating v8's splits at seed 42 reproduces them exactly — *"identical
id order, identical labels, **0 rows moved**"* — wrote it into a decision record, the hypothesis
ledger and a commit message, and **committed**. Only afterwards did I ask whether the comparison
could report anything other than zero.
**Root cause**: the number was the *answer I wanted* (regeneration is safe), so it read as a
finding rather than as a negative needing an instrument check. The working rule — *before believing
a negative, prove the instrument could have said yes* — was one I had quoted in the same session.
**Fix**: ran the control after the fact. Seed 43 moves **1,044/584/599** rows and shifted tier
thresholds move **1,041/593/580** (sizes drift 660→661), so the instrument can say "moved" and the
zero is real. Recorded beside the claim in all three places. ⭐ **The ordering was the defect, not
the result** — a control run after the commit protects the next reader, not the commit. It also
sized the risk it was clearing: seed 43 replaces **599 of 660** test rows, which is what a redraw
would have cost.

## Telling a review agent to "restore from git" would have deleted the fix under review (2026-09-08)
**Problem**: I asked a mutation-testing subagent to mutate `training/prepare_data.py` in place and
restore it with `git checkout -- training/prepare_data.py`. The fix under review was **uncommitted**,
so that command restores HEAD — reverting the mutation *and the entire change*, silently, while the
agent reports success.
**Root cause**: "restore from git" reads as "undo my edit" and actually means "return to the last
commit". The two are identical only when the working tree is clean, which during a pre-commit review
is exactly when it is not.
**Fix**: snapshotted both files to the scratchpad the moment I noticed, and confirmed the md5 was
unchanged when the agent finished. **Hand a mutation agent an explicit byte backup to restore from,
never a git verb** — and note this is the same family as the standing rule that no git verb may take
the whole tree, one scope narrower: here the *path* was explicit and the *revision* was wrong.

## A heading anchor that is a prefix of a deeper heading matched twice (2026-09-08)
**Problem**: An exact-match edit anchored on `## ▶ NEXT SESSION STARTS HERE` asserted one occurrence
and found two — the file also contains `### ▶ NEXT SESSION STARTS HERE — deployment, and the
ordering that surprised phase 8`, which contains the `##` form as a substring.
**Root cause**: a markdown heading string is a prefix of every deeper heading with the same text.
**Fix**: anchor on `"\n## ▶ NEXT SESSION STARTS HERE\n"` — leading newline pins the heading level,
trailing newline pins the end of the line. Cheap, and the assertion caught it, which is the system
working; noted because the shape recurs wherever a doc keeps a current and an archived block under
the same title.

## Persisted the outputs and a frame, not the model INPUT — the panel cannot be replayed (2026-09-09)
**Problem**: `docs/evidence/2026-09-08-thriving-harm-panel/` commits `panel_frame.jsonl`,
`judge.py`, both judges' per-row verdicts, `analyze.py` and its output — and the panel still cannot
be re-run. `judge.py` reads `id` / `title` / `content`, and the frame carries **no `content` field
on any of its 137 rows**. The real judge input was assembled at runtime and never written down.
**Root cause**: the frame was built for `analyze.py`'s joins (stratum, both lenses' scores, source,
language, url), so it *looks* like the population and is complete for the analysis it was written
for. Two artefacts were needed and one file appeared to be both. The directory's own file list
describes it as "137 rows, both lenses' scores, stratum" — accurate, and nobody asked what the model
had actually been shown.
**Fix**: documented in that README and in `docs/evidence/2026-09-09-adverse-pool-consult/README.md`.
The panel is **auditable as reported and not reproducible from source**, so EXP-031's figures stay
usable as an anchor while *"the anchor was wrong"* stops being a testable hypothesis downstream — a
materially different reading of a failed prediction, and it is now written into the NexusMind
pre-registration that depends on it. ⭐ **The rule: persist the exact model input, not the outputs
plus a frame you believe reconstructs it.** A frame sufficient for the analysis is not evidence of
what the instrument was shown. **Caught by a peer session about to model a new judge-input schema on
that frame** — which would have shipped a content-free file that fails on row 1.

## A control whose failure mode is silence, and whose silence reads as a pass (2026-09-09)
**Problem**: proposed a re-judge control to a peer — feed rows back through `judge.py` and read the
flip rate — with the verdict rule *"flips below the floor ⇒ the contrast is sound and earned."*
`judge.py`'s resume cache keys on `(id, pass)` and is loaded from `<out.json>.partial.jsonl`
(`judge.py:60-71`, `:76-78`), so an arm reusing the main run's output path returns **every cached
verdict with no API call**. The flip rate would have been **exactly 0%**, and 0% is below any floor.
**Root cause**: the control's failure mode was *silence*, and the rule read silence as success. ⭐
**The reassuring answer is the one the bug produces** — which is worse than having no control,
because it converts an unchecked assumption into a documented one.
**Fix**: three requirements, all before the run — a distinct `<out.json>` per arm, per-arm id
suffixes so a later merge cannot collide them, and **a positive control on the control**: assert
`n × k` FRESH lines in the arm's `.partial.jsonl` before reading any flip rate. If the arm cost
$0.00 it measured nothing. **A zero has to be earned, not inherited.** Pinned as the Method under
`H-AP1` in `memory/hypothesis-ledger.md`.

## Borrowed a noise floor across the JUDGE and its SAMPLING STRUCTURE (2026-09-09)
**Problem**: set a verify-arm threshold of *"flips above ~46%"* for an arm that was to run on
**Gemini at k=1**. ⛔ **And 45.8% was not even the rate I named it as**: it is the **NON-ENGLISH**
split-vote rate; DeepSeek's own k=3 rate is **43.1%** (59/137), stated in the sibling evidence
README the same commit edited. So the borrowed floor was a *stratum's* rate relabelled as an
instrument's — inside the very entry about borrowing a floor across populations. Caught by review.
**Root cause**: two transfers inside one number — a different judge, and a different sampling
structure. ⛔ **And the sharper half: at k=1 there is no split-vote rate at all**, because one vote
has nothing to disagree with. The floor was not merely moved somewhere it fitted badly; it was moved
somewhere the quantity **does not exist**, and the comparison would have returned a number anyway.
**Fix**: measure the floor **inside the arm** — k=2, read `unanimous`, never `majority` (at even k
`Counter.most_common(1)` resolves a tie to the first-encountered vote: vote order dressed as a
verdict). Caught by the peer session. Standing form: **a floor belongs to an instrument and a
population jointly, neither transfers alone, and check the quantity is even DEFINED on the target.**
Recorded in the assistant auto-memory as `feedback-noise-floor-per-population`; the project-side
list of measured floors is `memory/score-batch-shape-noise.md`.

## A count of matching rows is not coverage of a failure mode (2026-09-09)
**Problem**: asked what v9's training data lacks. `human_thriving v8`'s corpus holds **1,253
`harm_is_subject` rows (19.0% of 6,586)**, and the obvious read — a peer's first read, and nearly
mine — is *"not short of harm data."* It is backwards. **Not one reaches `weighted_mean_all` 4.0**
(max **2.7667**), and **all 316 rows at or above the 4.50 op-point are `in_scope`**.
**Root cause**: the labelling process cannot emit the row that matters. The failure mode is harm
content the STUDENT scores ≥4.5 (#150: oracle gates at 0.80–0.90, student returns 4.66–4.85) — i.e.
student/oracle *disagreement* — and the label comes from the instrument that got those rows right.
**Fix**: cross-tabulate the verdict against the **score band** rather than counting the verdict, and
before concluding a corpus covers a failure, name the process that assigned the labels and ask what
it **cannot** emit. ⭐ **The mirror of *prove the instrument could have said yes*: a positive count
of 1,253 carried as little information as a zero, and a big reassuring number is the harder half
because nobody interrogates it.** `H-AP5`; `feedback-count-is-not-coverage` in the auto-memory.
⛔ **AND THE FIX OVERSHOT — review refuted my own absolute.** I wrote *"zero examples and CANNOT
have any"* and *"a production-scored population is the only route."* Both are false: the corpus's
**per-run** votes carry the shape (**178** rows with ≥1 harm run-vote and a non-harm final verdict,
**1** above the op-point at 5.367, **1,079** `scope_flipped`, **178** harm rows with split run
votes), and a $0 detector arm on the existing 1,011/105/137 positives was never costed before the
pool was called "the only" route. **`analyze.py` never read `scope_verdicts_per_run` or
`scope_flipped` — fields sitting in the same JSON object.** The defensible claim is narrow: the
corpus's FINAL LABELS cannot exhibit student/oracle disagreement. ⭐ **An absolute is a measurement,
and mine went further than the thing I had measured — in the same paragraph that named the rule.**

## The convenience fallback that unioned two labelling generations (2026-09-09)
**Problem**: `analyze.py`'s score helper read `weighted_mean_major` and fell back to
`weighted_mean_all`. Published **351 rows above the op-point = 5.3% of the corpus**, quoted onward
into six surfaces including the auto-loaded memory index.
**Root cause**: the corpus declares its own aggregate. Every row carries
`aggregate_used == "all"` — **6,586/6,586** — written by `scripts/oracle/aggregate_k_runs.py` and
asserted in its unit test. The fallback therefore read the **non-declared** field on the 6,130 rows
that have it. ⛔ **And the 456 rows lacking `weighted_mean_major` are not a shape quirk — they are a
different labelling generation**: `prompt-v8-4.md` (hash `c4705408c477`, k=6) against
`prompt-candidate-tail.md` (`003cd35a5122`, k=3), and they were *selected* for being above-op under
an earlier pass. So `351 = 35 + 316` glued a rate on one population to a census of another under one
variable name. Correct figure: **316 = 4.798%** unweighted, **2.709%** design-weighted.
**Fix**: read the declared aggregate and `assert` it uniform at load; report design-weighted beside
unweighted; print the per-prompt-arm above-op rate, which shows the majority arm has **0** and the
minority arm **69.30%**. ⭐ **The repo's shape rule passed and its semantics rule failed** — the
`isinstance` guard that CLAUDE.md asks for was present and correct, and a field being *present* said
nothing about it being the one the producer used. **`aggregate_used` appeared in no document in the
repo.** ⚠️ Note the conclusion survived: 0 harm rows at ≥4.0 and all-`in_scope` above-op hold under
every aggregate definition. **The published quantity was wrong while the finding was right**, which
is exactly why the quantity gets its own check.

## My headline conclusion was a hardcoded print, and a data mutation proved it (2026-09-09)
**Problem**: `analyze.py`'s Part B ended in four `print()` calls stating *"ALL 351 rows at or above
the op-point are in_scope … has ZERO training examples and cannot have any."* The number was typed
in and the sentence was unconditional.
**Root cause**: Part A gated its conclusion (`if only_d == 0:`); Part B — the load-bearing half —
gated nothing. Two review lenses independently mutated the DATA (flipping rows to
`harm_is_subject`, pushing one above the op-point) and the script **printed the claim verbatim, exit
0**, while the computed line two lines above it disagreed.
**Fix**: `assert set(av) == {"in_scope"}` and `assert n40 == 0`, with the sentence interpolating
`len(above)`. Then mutation-tested six ways — harm row to 9.0, harm row to 4.1, an above-op row
relabelled harm, an above-op row relabelled `out_of_scope`, a mixed `aggregate_used`, a missing
design weight — **all six killed, control passes**, and the `in_scope` assert proven to fire
independently of the ≥4.0 one.
⭐ **This is the fifth mutation rung again — the lens mutated the DATA, not the code — and it landed
on the one sentence the whole directory exists to support.** The repo's own precedent was explicit
and one directory away: EXP-030's review blocker read *"the control was a print, not an assert."*


## I "refuted" a peer's hypothesis by testing their two EXAMPLES, not the CLAIM (2026-09-10)
**Problem**: ovr.news proposed that a good obituary headline over a long biography gets dragged
under the op-point. I scored their two example headlines, found both at 0.98–1.00 on the title
alone and still above 0.85 under 128 tokens of padding, and told them the diagnosis was
**refuted** — adding that dilution was *"real but bounded; it does not reach 1e-4."* Measured over
the population two days later: **22.1% of all the detector's misses are exactly that mechanism**
(title passes alone, full text does not, median 0.9556 → 0.6529).
**Root cause**: Two failures, and the second is the one with reach. (a) A hypothesis is about a
**class**; refuting the instances it was illustrated with refutes nothing — their two rows
genuinely do not reproduce, and that is compatible with the class being real and common. (b)
**"Bounded" was measured against the wrong bar.** Dilution never had to reach 1e-4; it only had to
cross **0.85**, the operating point. The number was correct and the reference point was wrong, and
nothing in a green run fires on that.
**Fix**: Went to the population and reported against myself (`EXP-035`,
`docs/evidence/2026-09-10-obituary-title-body-pooling/`). Two rules, both now in the assistant's
auto-memory under `feedback-a-dismissal-is-a-claim`: **"refuted" is the most expensive word
available and needs a population behind it, not an example**; and **before calling a magnitude too
small, name the threshold the effect would have to cross — for anything near an op-point that bar
is the op-point, never zero.**
⭐ **Third instance of one shape in a single day, across three surfaces** — a real number checked
against the wrong reference. The other two were peer-reported: `2828/2828` read off a file that is
100% passers by construction, and **n=1,529 vs n=1,537** (both "the obituary heldout", different
exclusion criteria) printed as comparable.

## A corpus filename off by one character and four rows would have answered a different question (2026-09-10)
**Problem**: Retraining obituary v3/v4/v5 across seeds needed each version's own training corpus.
Staged on b650 (off-tree; none of these four is in this repo) were `train_split_corpus.jsonl` <!-- placeholder -->, `v4_train_seed.jsonl` <!-- placeholder -->, `v4b_train_seed.jsonl` <!-- placeholder --> and
`v5_train_seed.jsonl` <!-- placeholder -->. The obvious pick for v4 is the one named `v4_train_seed.jsonl` <!-- placeholder -->. **It is not
v4's corpus** — it holds 11,304 rows (2,673/8,631) against v4's published 11,308 (2,673/8,635).
`v4b_train_seed.jsonl` <!-- placeholder --> is the real one.
**Root cause**: A name is an assertion, and an intermediate artefact kept the un-suffixed name
while the shipped one took the suffix. Nothing about the four-row difference is visible without
checking, and a grid built on the wrong file would have looked completely clean.
**Fix**: Identified all three by **label counts against the shipped `training_config.json`**
(`n_samples`/`n_positive`/`n_negative`), never by filename — all three matched exactly. The peer
had asked for exactly this ("if they turn out not to reconstruct the versions as shipped, say so
and stop"), which is why it was checked before training rather than after.
⭐ Same session, same family: **leakage had to be computed, not hand-listed** — 25 heldout rows are
in v5's training corpus, 4 in v4's, 0 in v3's. Excluding the union gives n=1,537 and reconciles the
published n=1,529, which drops all 33 **panel-graded** rows; the 8-row gap is rows a human
adjudicated but no model trained on. Two defensible criteria, different questions, not
interchangeable in one column.

## `early_stopping=True` makes `random_state` pick the validation split — every shipped detector metric is one draw (2026-09-10)
**Problem**: Both detector trainers build the head as `MLPClassifier(..., early_stopping=True,
n_iter_no_change=15, random_state=SEED)` with `SEED = 42` hardcoded. With corpus, embedder, window
and hyperparameters all fixed, **obituary heldout recall at the live 0.85 spans 0.6599–0.8081
across five seeds** — 0.148, and 0.285 at threshold 0.95.
**Root cause**: `early_stopping=True` carves an internal validation split, and `random_state` picks
it. So the seed does not merely perturb initialisation; it changes what the model is selected on.
**Fix**: Filed as **#158**. Any detector comparison must average over a seed set and report the
band. This is not academic: a downstream repo's ADR argument rested on a 0.136 recall delta sitting
inside a 0.148 seed band, and once seeds were varied the ordering produced **three different
orders across five seeds** and the point estimate reversed.
⛔ **The trap is that a seed band is invisible to every check this project runs** — the tests pass,
the gate passes, the number is reproducible on the same seed forever. Nothing distinguishes "this
model is better" from "this seed was luckier" without deliberately varying it.

## A POSITIVE CONTROL OF THE WRONG CLASS — THE INSTRUMENT SAID YES AND STILL COULD NOT SEE THE VIOLATION (2026-09-17)

**Problem**: Amended ADR-013 to require English across all framework-internal text, swept the
repo, and published **"Zero framework-internal prose violations."** A review lens falsified it
in under a minute: `docs/adr/009-add-filters-first-reduce-later.md:25,34,35,37,60` carries
`Welzijn`/`Erfgoed`/`Vooruitgang` as ADR prose, and `scripts/analysis/cross_filter_landscape.py`
carries 39 occurrences as dict keys, identifiers and printed column headers. Both sites are
inside the sweep's own declared scope.

**Root cause**: The wordlist was 36 Dutch **function words** (`niet`, `wordt`, `omdat`, …). The
violation class ADR-013 polices is Dutch **names**, which contain no function words. Measured:
the list scores **0** on both files. ⛔ **And I DID run a positive control — it passed.** The
control was the Dutch fixture *sentences* at `filters/uplifting/v7/prefilter.py:567` and
`filters/common/commerce_prefilter/training/benchmark_models.py:61`, which are full of function
words. A Dutch sentence and a Dutch lens name are different classes; the control only ever
proved the first, so the instrument looked sound the whole way.

**Fix**: Claim retracted the same day, the two sites filed as **#160** for an owner call (an ADR
is a historical record — rewriting one is not obviously right). ⭐ **The rule: a positive control
must be of the CLASS UNDER TEST, not merely the language, domain or file type under test.** This
is `CLAUDE.md`'s own instrument rule — *"prove the instrument could have said yes"* — and "it
said yes" is not enough; it has to have said yes **to the thing you are about to claim is
absent**. ⚠️ ADR-013's own Consequences `:86` already carried an open action pointing at exactly
the leftover class that was missed, and the sweep declared zero without reconciling it: **an open
action in the document you are amending is part of the evidence.**

## `grep` ON THIS WORKSTATION IS ugrep, AND IT REFUSES BOUNDED REPETITION (2026-09-17)

**Problem**: A context-extraction command using `grep -oE ".{0,70}#123.{0,90}"` printed
`ugrep: error at position 620 … exceeds complexity limits` and returned nothing for every line.
Under the `2>/dev/null` that such one-liners usually carry, it would have returned a silent empty
result and read as "no matches".

**Root cause**: `grep` here resolves to **ugrep**, not GNU grep. ugrep rejects bounded-repetition
quantifiers over a UTF-8 character class as too complex. `agent-ready-projects`' `update-drift`
skill documents exactly this for `(^|[^A-Za-z])` and prescribes `\b` instead.

**Fix**: Use Python for context extraction around a match, or `\b`-anchored patterns for
detection. ⭐ **A non-zero exit with no stdout is indistinguishable from a clean run once stderr
is discarded** — never `2>/dev/null` a grep whose empty result you intend to read as evidence.

---

## Mechanized

⚠️ **A STANDING TABLE, NOT A DATED ENTRY.** Everything above is newest-first chronological;
this section sits at the bottom because it is appended to, not prepended. Adopted from
`agent-ready-projects` v1.41.0 — it is the destination for `/review-changes` **Step 3.1**,
which until 2026-09-17 had nowhere to land, so every mechanization triage it ran was written
into a report and lost.

**Separate from the log above because the destinations differ**: a gotcha becomes PROSE an
agent reads; a review finding becomes a CHECK that runs.

⛔ **`live` requires a SEEDED POSITIVE — never the author's read of the code.** A check that
has never caught anything is indistinguishable from one that does not work; that is this
repo's signature defect (a mechanism present, configured, unable to fire) arriving in the
table built to prevent it. Status values: `proposed` (shape named, no check yet),
`live` (check exists AND a seeded case made it go red), `rejected` (Check cell carries the
reason — kept, not deleted, because a shape rejected twice is worth another look),
`retired` (say what removed the class).

⚠️ **OCCURRENCES does NOT mean what it means in a promotion table.** It counts sightings
**after** the row went `live` — before that there is no check to have failed. A `proposed`
row reads `—`. A lens finding a class its own `live` check covers is a finding about the
CHECK: it does not fire on the real shape, is scoped to the wrong population, or was never
wired in. Investigate the check, not the finding.

⚠️ A `proposed` row's Check cell names the path the check WILL live at and marks it
`<!-- placeholder -->` **immediately after the path, in that path's own cell** — the marker
binds to the nearest path *before* it. Without the marker every proposed row is a standing
false finding in the reference audit, which trains readers to dismiss that audit.

| Date | Finding shape | Check | Status | Occurrences |
|------|---------------|-------|--------|-------------|
| 2026-09-22 | A doc states a code guard's rule as a literal (`sample_min > 4.5`) and the code moves without it | `scripts/verification/check_guard_doc_sync.py` <!-- placeholder --> — assert each guard CONSTANT named in `fit_normalization.py` appears in `NORMALIZATION_METHOD.md` §5.3's table, and that retired literals do not appear as live rules | proposed | — |
| 2026-09-22 | An in-sample share quoted against a percentile gate, i.e. a tautology presented as a measurement | `scripts/verification/check_doc_claims.py --check gate-share-sample` + 8 tests in `tests/unit/test_doc_claims.py`. Any live doc block quoting a `%` that CLEARS the normalized-4.0 / enrichment gate must say `in-sample`, `out-of-sample` or `tautolog`. ⚠️ **Narrower markers than proposed**: `by construction` / `arithmetic` passed the real `docs/TODO.md` NM#319 block, which uses "by construction" about the ANCHOR beside a bare 60.0%. Live 2026-09-24: **red on the real tree, 4 blocks** (v7's out-of-sample 60.0% ×3, solutions' 75.6%), all fixed by naming the sample; 9 mutants, 9 killed | live | 0 |
| 2026-09-22 | A number attributed to an `EXP-` id that the experiment's own evidence file contradicts | `scripts/verification/check_experiment_citations.py` <!-- placeholder --> — for each `EXP-NNN` cited beside a numeric literal, assert the literal occurs in that experiment's evidence README or registry row | proposed | — |
| 2026-09-22 | A mutation set that moves a value AWAY from every valid option: proves only that invalid values are caught, silent on swaps/parents/siblings INSIDE the valid set. 3 survivors on a check I called "6 mutations, 6 killed" | `scripts/verification/check_mutation_directions.py` <!-- placeholder --> — ⚠️ shape is hard to detect mechanically; the realistic form is a CHECKLIST rung in the review profile, not a grep | proposed | — |
| 2026-09-22 | A closed-form number in a config comment reads as MEASURED ("at 3000/run the backlog needs ~12 cycles" = a fixed backlog over a cap, no intake term). Quoted onward twice before anyone checked it | needs intent — no grep separates a derived quotient from a measured one. The mechanizable half is narrower: flag a comment carrying an arithmetic claim with no date and no command beside it | rejected | — |
| 2026-09-22 | A doc claim citing a real source against the WRONG REFERENT — ovr.news Chain 7.5/7.6 quoted accurately for a field that file never mentions (0 hits for `harm_is_subject`/`_harm_`) | `grep -c` the cited file for the identifier the claim is about, before citing it; mechanizable as a rung in `check_doc_claims.py` for claims that name a cross-repo document | proposed | ⚠️ **RECURRED SAME DAY, 2026-09-22** — `Jaccard 0.246` attributed to `EXP-030` (whose own evidence reads 0.127 and whose lines 128-139 exist to prevent that exact substitution), in a session that had this row in its own log. A proposed row does not fire. |
| 2026-09-17 | An always-loaded file asserts byte-identity with an installed skill *outside* the repo, hand-dated; no commit here can hold it still and it decays silently | `scripts/verification/check_framework_stamp.sh` | live | 0 |
| 2026-08-27 | A pointer row in the always-loaded layer grows past its cap; a byte budget loses the race, a per-row cap does not (#133) | `scripts/verification/check_index_budget.py --target pointers` | live | 1 |
| 2026-09-17 | A reference-integrity rung that is a SHAPE test inside an existence-test disjunction — it cannot stop matching, so the flagged author has no legal move | `tests/fixtures/reference-integrity/run.sh` (cases 34/35) | live | 0 |
| 2026-09-17 | A number restated into a second file from PROSE rather than re-measured — the copy is plausible, self-consistent and wrong | `scripts/verification/check_doc_claims.py` | live | **1** |
| 2026-09-17 | The test-suite baseline gets a SECOND live copy — the profile's own "only live copy" rule broken by the change that quotes it | `scripts/verification/check_doc_claims.py --check suite-baseline` | live | 0 |
| 2026-09-17 | A reference-checker's SCAN SET narrowed without notice — fewer findings reads exactly like a repo that got cleaner, and the tier decides which files are opened at all | `tests/unit/test_refcheck_docs_tier.py` (37 tests) | live | 0 |
| 2026-09-17 | An argument a CLI does not know scans the default set and prints a small, reassuring count — including a positional, which "starts with `--`" guards miss | `tests/fixtures/reference-integrity/run.sh`, the `guard_fail` block (7 rejected + 4 accepted) | live | 0 |
| 2026-09-17 | A detector metric published as a POINT when `early_stopping=True` makes `random_state` pick the validation split — one draw read as a property of the model, and the artifact says nothing (#158). ⛔ The numbers live at TWO sites and the gitignored one is not the one a reader opens | `scripts/verification/check_detector_metric_bands.py` + `tests/unit/test_detector_metric_bands.py` (18 tests) | live | 0 |
| 2026-09-17 | An ADR-021 gate artifact that does not say which DEVICE produced its numbers — the tree mixed 4 `cpu`, 1 CUDA and 3 silent, so a cross-filter comparison was already crossing hardware paths with nothing saying so (#104) | `scripts/verification/check_gate_device_stamp.py` + `tests/unit/test_gate_device_stamp.py` (10 tests) | live | 0 |
| 2026-09-17 | Dutch NAMES in framework text (ADR-013) — a function-word sweep scores 0 on both real violation sites, so the instrument must carry the names themselves and its allowlist **is** the carve-out table | `scripts/verification/check_framework_language.py` <!-- placeholder --> | proposed | — |

⛔ **THE FIRST OCCURRENCE, AND IT IS A FINDING ABOUT THE CHECK (2026-09-17).** The #134
step-2 battery found a number restated from prose — the decision record wrote its own copy
of the suite count while citing, one sentence away, the rule that
`.claude/review-profile.md` holds the only live copy. That is the row above's class
exactly, and `check_doc_claims.py` **could not have fired**: its checks are four
hand-listed CLAIM PAIRS between `CLAUDE.md` and named memory files, and the class is "any
number restated anywhere". **Scoped to the wrong population**, per this table's own
instruction to investigate the check rather than the finding. Remedy shipped in the same
session: the `suite-baseline` check below, which walks the tree for the profile's CURRENT
value and excepts only dated records. It went red on the real restatement (not a synthetic
one) before `docs/TODO.md` was fixed, and `CANNOT VERIFY` when the protected line is
deleted.

**First positives, in prose** (they are what made the `live` rows live, and predate the
occurrence counter):

- **`check_framework_stamp.sh`** — on the tree it shipped into it printed `DRIFT` for all four
  skills against the `v1.40.0` stamp, exit 1, with per-skill line counts 27/372/26/240 matching
  an independently-run `diff` across tags; after the bump, `4 global skills byte-identical to
  v1.45.1`, exit 0. **Thirteen mutations, thirteen killed**, each listed with the test that killed it
  in `docs/decisions/framework-adoption-history.md`. Its automatic caller is a
  `<!-- verify: -->` block in `memory/MEMORY.md`, run by
  `scripts/verification/run_verify_annotations.py` (= `/curate` Step 0 sub-step 3); a seeded
  `FRAMEWORK=/nope` arm made that runner report `CANNOT VERIFY` and exit 1, so the caller can
  say no.
  ⛔ **Its FIRST draft is the thing worth remembering, and a pre-commit review found all of
  it**: `diff`'s exit status unchecked, so an unreadable file read as *identical*, exit 0;
  `N_WANT=4` hand-written beside a four-name `WANT`, reproducing upstream's original false PASS
  the moment the two disagree; `head -1` on the version, so prose naming an older release
  outranked the stamp; `$HOME` unset exiting **1**, i.e. an environment fault reported as
  DRIFT; and three branches — not-a-git-repo and both `$HOME` defaults — with **no test at
  all**, proven by surviving mutants. Six of the eight were false PASSes in a probe whose
  entire job is to refuse one.
- **`--target pointers`** — live since **2026-08-27** (`5bd0cdb`; 11 tests in
  `tests/unit/test_pointer_row_cap.py` at its first commit, mutation evidence in `768678f`).
  **Extended** to the auto-memory index on 2026-09-17 (`ad6eba5`, 5 further tests in
  `tests/unit/test_index_budget_guard.py`). ⚠️ This bullet first read *"added 2026-09-17 with
  4 tests"* — wrong on date, count and citation, because it was copied from a TODO summary
  instead of measured, and `ad6eba5`'s own message says *four* where the diff adds five.
  **Occurrences 1**: on 2026-09-17 the check was found to read `CLAUDE.md` only while the
  surface actually growing was the auto-memory index — a finding about the CHECK's population,
  which is exactly what this column exists to surface.
- **run.sh 34/35** — seeded both ways and both proven non-vacuous: case 34 FAILS on the
  pre-change code, case 35 dies when rung 1 is removed. See the 2026-09-17 entry at the top
  of this file. ⚠️ `/audit-context` Step 4 runs `refcheck.py`, **not** `run.sh` — so the rung
  runs monthly while the 34/35 cases that prove it non-vacuous fire only by hand.
- **`check_doc_claims.py`** — already owns the frontmatter-vs-footer stamp rung; printed
  `PASS framework stamp: both say v1.45.1` during this review, and it is wired into
  `memory/MEMORY.md`. ⛔ **NOT the same check as `check_framework_stamp.sh`**, though
  `check_doc_claims.py:191` defines a function of that very name: it asks only whether two
  lines of `CLAUDE.md` agree with *each other*, never whether either matches upstream. A
  reader told "the framework-stamp check is green" gets the weaker one.
