# Gotcha Log

*Newest-first, dated entries. **One standing section lives at the BOTTOM**: [`## Mechanized`](#mechanized) — the destination for `/review-changes` Step 3.1, where a review finding that became a deterministic check is recorded. It is named here because nobody scrolls to the bottom of this file.*

*⚠️ **Entries dated before 2026-09-17 live in [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md)**, verbatim (the 09-01 → 09-16 ones moved 2026-09-27 by an owner-approved MID-MONTH pass, `--before 2026-09-17`; earlier ones moved 2026-09-24; into `archive/` 2026-09-26 so curate's size measurement stops counting it, #163; the month-dated Feb–May entries followed on 2026-09-26). Next pass: `python3 scripts/maintenance/retire_memory.py gotcha --before <first of this month> --apply` (dry run without `--apply`). It retires top-level entries only; the `###` entries inside the catalogue are kept by rule and counted. The unreachable-mechanism catalogue stayed here. For a recurrence match, grep both: `grep -n <term> memory/gotcha-log*.md`.*

## THE EVIDENCE FILE WAS A DIFFERENT SAMPLE FROM THE ONE I DESCRIBED — one seed shared across lenses (2026-09-28)
**Problem**: For EXP-044 I read 12 flagged titles per lens, wrote "belonging: mixed (Gaza strike, funeral mix-up … Stolperstein)" into the evidence README, then re-ran `harm_titles.py` to SAVE the sample with the lenses in a different order. `random.seed(0)` is set once, so every lens drew different rows: the committed file had none of the titles the README cited, and the Stolperstein row sat under uplifting. The adversarial review lens caught it; the claims-vs-evidence lens (and I) had not.
**Root cause**: A sample whose draw depends on argument order is not reproducible by "the same command", and I wrote the prose from the first run while committing the second — the verified artifact was not the shipped one.
**Fix**: Prose rewritten from the committed file (belonging now reads *mostly harm-dominated*), with a dated correction. Rule: **save the output you read, in the same run; never re-run to save.** Seed per stratum (`random.Random(lens)`), never one global seed across strata. Recurs *the verified artifact is the shipped one*.

## I RECOMMENDED A CAP FROM THE PLAN'S WRITTEN METHOD WITHOUT CHECKING ITS PREMISE — the lens had switched two days earlier (2026-09-28)
**Problem**: TODO item 1 ended "Then, and only then, a cap on `uplifting v7`", and I recommended exactly that to the owner. Thriving had read `human_thriving v9` since 2026-09-26 (ovr.news#373), so a scoring-time cap on v7 changes nothing a reader sees. The owner's "why a cap?" surfaced it. `CLAUDE.md`'s filter table still said "Thriving still reads `uplifting v7`; cutover #151 undecided" — stale by two days, and on the always-loaded path.
**Root cause**: A written method is a claim about the world as of when it was written (*a marker is a claim*); its last step inherits every premise the preceding days may have changed. The stale always-loaded row agreed with the stale plan, so nothing disagreed.
**Fix**: Before recommending the action a plan ends in, name the premise it rests on (here: "v7 is what readers see") and check it against the newest record (the session file, the merged PR). `CLAUDE.md` and `memory/ovr-lens-set-current.md` corrected. Recurs *a marker is a claim* / *a precedent is a mechanism claim*.

## DATED ENTRIES NESTED UNDER THE TEMPLATE HEADING ESCAPE RETIREMENT (2026-09-28)
**Problem**: Five `### ` entries dated 2026-09-10 (~12 KB) sit under `## [Short description] (YYYY-MM-DD)`, the template heading that `retire_memory.py`'s `KEEP_HEADINGS` always keeps — while the file header says entries before 2026-09-17 live in the archive. The 2026-10-01 retire would leave them behind silently.
**Root cause**: Entries were appended under the template instead of as top-level `## ` entries; the keep-list matches the heading, not the content's date.
**Fix**: NOT yet applied (session close). Next session, before the 10-01 retire: move those entries out from under the template (as top-level entries, verbatim bodies), and make `retire_memory.py` report dated entries found under a KEEP heading instead of keeping them silently.

## A NEGATIVE FROM AN INSTRUMENT THAT SILENTLY DROPPED PART OF ITS POPULATION — twice in one change (2026-09-27, evening)
**Problem**: Retiring obituary v3/v4 + commerce v2, I grepped for text still saying they ship, naming `scripts/deployment/deploy_to_nexusmind.sh` — a path that does not exist (the script is `scripts/deploy_to_nexusmind.sh`). `ugrep` printed a stderr warning and the other files' (zero) hits; I read the silence as clean. Review found three stale "v3/v4 still ship" comments, two in that very script (`5590f88`). Minutes later a dry run said "THE FILES WERE STILL COPIED" and `git status` was clean — but the retired pickles are gitignored in NexusMind, so `git status` could not have shown a re-added one.
**Root cause**: both instruments exclude part of the population without failing: grep over a missing operand exits on the other operands; git's view excludes ignored files. Same class as the `ls-files`-as-"committed" entry below.
**Fix**: for grep, list operands with `ls` first or grep the directory, and run a control pattern that must hit in the SAME file; for "did a copy re-create X", check the disk (`ls -d`), then run the control (the check removed → the dirs reappeared). Both done in-session for the second case; the first was caught by review, not by me.

## THREE REVIEW ROUNDS EACH FOUND ANOTHER SITE OF ONE SYMLINK-ESCAPE CLASS (2026-09-27)
**Problem**: ADR-024 step 3's `place()` got a symlink containment fix in round 1 (a dir symlink under the package); round 2 found the `.deploy-tmp` temp file bypassing it; round 3 found the package dir ITSELF being a symlink (`tpkg.resolve()` was already outside, so every check passed). Each fix was tested and mutation-killed, and each was still the wrong SCOPE.
**Root cause**: I fixed the site the reviewer named, not the class. The class's sites are every path operation (open, copy, replace, unlink, mkdir) times every component from the trusted root down; I never listed them.
**Fix**: containment measured against `target_common.resolve() / package`, never the resolved target; every write removes a symlink at its temp and dest names first; a symlinked package/detector dir places nothing (`44b703d`). ⭐ **When a review finds one site of a class, enumerate the class's sites BY OPERATION and BY PATH COMPONENT before fixing the first one** — the round cap (3) was spent learning the list one site at a time.

## "MUST BE COMMITTED" CHECKED WITH `git ls-files`, WHICH PASSES A STAGED-ONLY FILE — IN THE CODE AND IN ITS TEST (2026-09-27)
**Problem**: `deploy_detectors.stage` refused an "untracked" git-origin file via `git ls-files --error-unmatch`; the ten new sidecars were staged, not committed, and passed. The real-tree test used the same idiom, so it was green in the same state. Found by 3 of 6 review lenses.
**Root cause**: `ls-files` answers "is it in the INDEX", not "is it in HEAD". The helper also computed a HEAD-clean flag and the caller discarded it. Test and code shared the instrument, so the checker and the checked were one object.
**Fix**: `_committed()` = `git cat-file -e HEAD:<rel>` + `git diff --quiet HEAD`; the real-tree test reads `git show HEAD:<rel>` and went red until the commit (`6c16056`). Mechanized row `check_committed_idiom.py` proposed.

## A PR BODY'S "BEFORE" CLAIM WAS MEASURED ON A CLONE OF THE WRONG BRANCH (2026-09-27)
**Problem**: NexusMind PR #550's body said `main` "passes the other two" detectors. That was measured on clones of a local checkout that sat on a feature branch, not on `main`; on a clean `main` commerce reports MISSING (its model file is gitignored there). Caught by re-measuring on a `git worktree` of `origin/main` before messaging the peer, and corrected with `gh pr edit`.
**Root cause**: a local clone inherits the source checkout's HEAD, not the remote default branch — the same trap as the sibling-checkout entry below, arriving through `git clone ../NexusMind`.
**Fix**: a PR's "before" is measured on the PR's own BASE commit (`git worktree add <dir> origin/main`), named by sha in the body. Clone from the remote URL, never from a sibling path.

## I NAMED FOUR HUB REPOS BY DERIVING FROM FOLDER NAMES THAT SHARE NO PATTERN (2026-09-27)
**Problem**: `harm-detector`, `obituary-detector`, `violence-promotion`, `commerce-prefilter`. The owner asked why they
were not harmonized. Two repos had to be renamed after upload.
**Root cause**: `name.replace('_', '-')` copies whatever inconsistency the source names carry. A name that outsiders
will see (a Hub repo, a URL, a package) is a DECISION, and I made it with a string transform.
**Fix**: an explicit `REPO_NAMES` table (`scripts/deployment/upload_detector_to_hub.py`); an unnamed detector raises
`KeyError` rather than getting an invented name. ⭐ **Before creating anything public-facing and named, propose the
convention to the owner in one line.** A Hub rename keeps revisions, so it was cheap this time.

## A LOCAL SIBLING CHECKOUT IS NOT "WHAT PRODUCTION SERVES" — IT WAS ON ANOTHER SESSION'S FEATURE BRANCH (2026-09-27) [x2: 2026-09-27 afternoon — `../NexusMind` was on `chore/resolve-0904-unmerge`, then `research/gt2-harness-freeze`, both with WIP; applied this time: every deploy proof ran on a fresh clone, the real deploy went in as NexusMind PR #550]
**Problem**: the ADR-024 backfill needed the bytes production serves. `../NexusMind` was checked out on
`fix/integration-inference-tests`, another session's branch.
**Root cause**: a sibling repo on the workstation belongs to whichever session last switched it.
**Fix**: hash on the serving host (`sadalsuud:~/local_dev/NexusMind`, `git status -sb` = `main`), and cross-check the
other copies (gpu-server, workstation) with `verify --strict`. Record `served_commit` in the artifact. The bytes
happened to match, and that was luck, not the method. Related: `shlex.quote("~/x")` produces a literal `~` directory
over ssh (`remote_path()` fixes it).

## THE GUARD'S TESTS PROVED THE PREDICATE, NOT THE WIRING — AND A PLANNED TRIM LOST CLAUSES ANYWAY (2026-09-27)
**Problem**: Four slips in one session, each caught by a review lens or by the owner, none by my own checks.
1. **`054a0a3`'s sidecar guard** was committed with "5 mutants of the fixes all caught". Round 2 then found **4 surviving mutants that disable it**: CLI exit forced to 0, arguments swapped in Python or in the `.sh`, `exit 1` dropped. Every test called the predicate. The only `.sh` test was a text search for `--check-sidecars`.
2. **`memory/MEMORY.md` thinning**, the day after the 09-26 trim entry below and with a clause-loss lens planned in advance, still lost 2 operative clauses (H-DET6 non-Latin refutation, "do not infer the session from its name"), narrowed a trigger ("threshold or op-point" → "op-point"), and wrote a wrong NM#310 expansion.
3. **The adj4p write-up** stated "positives alone buy volume" as a finding and "would LOSE under the owner-ruled bar", although that bar was adj4's and adj4p had none. Both were glosses the pre-registered rule did not license.
4. **To the owner I said "stop the v10 line"**, a label I coined (they had to ask what it meant). I also said the Venezuela story "appears 5 times": that count came from a date-filtered subset, and the full count was 7.
**Root cause**: (1) The mutants I chose were mutants of the predicate, the part I had just written, not of the path the operator runs. (2) Knowing the failure mode does not stop a rewrite from paraphrasing a clause away; the lens caught it, my eyes did not. (3) and (4): a sentence that feels like a summary gets written as a result.
**Fix**: (1) A CLI exit-code test plus an end-to-end test that runs the real `deploy_to_nexusmind.sh` against throwaway git repos with a presence control (`675c101`); 7 of 7 wiring mutants caught. ⭐ **For any guard, one mutant must break the CALL SITE, not the function.** (2) Restored from the lens report. Keep running a clause-loss lens on every index rewrite: it is the check, not a courtesy. (3) Relabelled as *gloss* in the README, EXP-043 and the ledger; EXP-043 `decision` changed from `rejected` to `parked`. (4) Say the thing, not a label; count from the unfiltered population.

## I COPIED THE PRECEDENT SCRIPT THAT HAD ALREADY FAILED, AND v10 CALIBRATION FAILED THE SAME WAY (2026-09-26/27) [*a precedent is a mechanism claim*, recurred]
**Problem**: For v10 I copied b650's `logs/adj_post_20260925.sh`. It staged the model under `staging/`, and `fit_calibration.py` refused it ("Expected 'filters' in path"), after 51 minutes of training. The 09-25 run had hit exactly this and fixed it in `adj_post2_20260925.sh`, which sat in the same directory.
**Root cause**: I picked the precedent by NAME (the first `adj_post*` I found), not by which one had produced the results I was reproducing. A directory holding `x.sh` and `x2.sh` means the first one failed.
**Fix**: Re-ran only the post-training step, staged under `filters/human_thriving/v8_adj4`. ⛔ **When reusing a run script, take the one whose output the evidence cites (read the log it wrote), and when there are `name` and `name2`, read both first.**

## I STOPPED AT A CREDENTIAL ERROR INSTEAD OF ASKING THE PEER SESSION THAT HAD ACCESS (2026-09-26)
**Problem**: `ovr.news/scripts/flag-evidence.ts` failed with Cloudflare "Authentication error" here, and I told the owner to run `wrangler login`. Owner: *"what? you always were able to do that. ask the ovr.news peer session"*. The peer ran it at once.
**Root cause**: I treated my own failed call as the system's limit. A peer session on the same machine, working in that repo daily, was listed by `ListAgents` and had already done cross-repo work with me that day.
**Fix**: ⛔ **Before handing the owner an interactive step, ask the session that owns the repo whether it can do it.**

## I RELAYED THE OWNER'S QUESTION AS A CLAIM, AND ASSERTED A FACT I HAD NOT CHECKED (2026-09-26) [*relay marks its gloss*, recurred]
**Problem**: Two in one handoff to ovr.news. (1) The owner asked "i think that is working?" and I wrote to the peer "The owner thinks it's working"; the peer rightly refused to treat it as merge approval. (2) I told the peer that v7 and v9 dimension names DIFFER, and they are identical; the peer measured it.
**Root cause**: (1) a question paraphrased into a ruling; (2) an inference from "different filter, different prompt" written as fact.
**Fix**: Quote the owner verbatim in a relay. Label every fact in a handoff measured or guessed, the same rule chat replies follow.

## AN UNANCHORED `archive/` IN THE SCRATCH BLOCK HAD BEEN SWALLOWING `memory/archive/` — AND MY FIRST FIX NEGATED THE INSTANCE AGAIN (2026-09-26) [4th of the `*_test.*` class]
**Problem**: Six session files recovered into `memory/archive/` by `/audit-context` did not appear in `git status` at all. `.gitignore`'s "Temporary files" block (`a1a0768`, 2025-11-15) carried a bare `archive/`, which matches that name at ANY depth. The 79 tracked files there survived only because `retire_memory.py` moves them with `git mv`, and a tracked file stays tracked inside an ignored directory. So the defect was invisible to every tracked-file count, and Step 7's `git ls-files` pass had nothing to see.
**Root cause**: a scratch PATTERN written as if it were a PATH. That is the `*_test.*` mechanism for the fourth time, and my first fix, `!memory/archive/`, was the 2026-09-05 entry's own named mistake: it rescued one instance while the framework prescribes `docs/work-items/archive/`, which the pattern would eat too.
**Fix**: root-anchored `/archive/`, `/tmp/` and `/temp/`, with the negation removed. Verified both ways with `git check-ignore`: nested `memory/archive/`, `docs/work-items/archive/` and `filters/a/tmp/` are trackable; root `archive/`, `tmp/` and `temp/` are still ignored. Zero files changed ignore state (`git status --porcelain --ignored` showed none under those names). ⭐ **Anchoring makes the failure LOUD** (a nested scratch dir shows as untracked) where negation leaves every other instance SILENT. ⛔ The unanchored scratch patterns still in that block (`*_test.*`, `*_backup.*`, …) are the same hazard; an audit of that block is not done.

## MUTATION-TESTED A FILE WITH `git checkout --` TO UNDO THE MUTANT, AND THREW AWAY MY REAL EDIT (2026-09-26)
**Problem**: To prove `retire_memory.py` fails loudly on the old archive path, I sed-reverted its `ARCHIVE` constant, ran it, and then restored with `git checkout -- <file>`. That restored HEAD, not my working version, so both intended edits vanished. `git diff --stat` printing nothing was the only sign.
**Root cause**: the mutant's parent was an UNCOMMITTED edit, and `git checkout` knows only commits. An hour earlier in the same session I had done it right for `refcheck.py`: `cp` to the scratchpad, mutate, `cp` back.
**Fix**: re-applied with count-asserted replacements, and confirmed with `git diff --stat` (2+/2−), a dry run and 18/18 tests. ⛔ **Mutate a working-tree file only from a copy: `cp f $S/f.fixed`, mutate, `cp $S/f.fixed f`.** Never restore with git while the change under test is uncommitted.

## A TRIM THAT KEPT EVERY TOKEN AND LOST FIVE RULES, AND A FIX THAT INTRODUCED THE ROUND'S ONLY BLOCKER (2026-09-26) [x2: 2026-09-27, `memory/MEMORY.md` thinning — see the 09-27 entry]
**Problem**: Four defects in one `/update-drift` adoption, each passing my own checks and each caught only by a review lens.
1. **`CLAUDE.md` trim.** My survival check confirmed every dropped backticked span, number and issue id was still in the repo. Five operative CLAUSES were still lost, among them the ADR-015 ban on excluding adjacent-lens content from oracle prompts and "compare filters ONLY on recall + specificity".
2. **`retire_memory.py`'s "lossless" check** compared two line multisets built from the same blocks, so it was equal by construction and could never fail.
3. **"This log has 0 `[RESOLVED`."** I grepped `^### ` on a log whose entries are `## `. That is working-rules' 24th occurrence of an instrument that could not say yes.
4. **The fix for the resurrection-prone ordering** (git mv first, then write the edits) wrote a moved file's edit back to its OLD path. It was round 2's only blocker, and it was introduced by a round-1 fix.

**Root cause**: Each check measured something adjacent to the claim: tokens rather than clauses, blocks against themselves, one heading level rather than the log. A fix is the least-reviewed code in a session (`feedback-articulating-is-not-applying`).

**Fix**:
- The five clauses were restored.
- The lossless check now rebuilds both files independently, from the original text by string deletion, and re-reads them after writing.
- Every defect has a seeded test in `tests/unit/test_retire_memory.py`, with 12 mutants killed across two rounds.
- The clause-survival check is `proposed` in § Mechanized.

**Rule**: Before calling a trim or move lossless, name the unit the loss would be in (clause, entry, line), and check THAT unit with an instrument built independently of the thing it checks.

**Also**: upstream tagged v1.49.0 mid-triage, and the global skills were reinstalled under me at 11:27. Re-read the remote's tags before bumping a stamp, never the number the triage started with.

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

### I EXPLAINED 78 TEST FAILURES AS "THE ENVIRONMENT" AND IT WAS THE WRONG INTERPRETER (2026-08-25) [x4: 2026-09-28 — `python3 -m pytest tests/unit -x` stopped on `ModuleNotFoundError: transformers`; caught before any claim, `.venv/bin/python3 -m pytest tests/` matched the baseline in `.claude/review-profile.md`]

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

## 2026-09-05 (third session) — the `*_test.*` gitignore trap, third victim, because the fix was scoped to the instance [x4 — recurred 2026-09-26: an unanchored `archive/` swallowed `memory/archive/`; see that day's entry]

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
| 2026-09-26 | A "lossless" check that compares two quantities built from the same blocks — equal by construction, so it can never fail (`retire_memory.py`, round 1 of review) | `tests/unit/test_retire_memory.py::test_reconstruction_check_can_fail` — the split is mutated to drop a line and the run must refuse and write nothing | live | 0 |
| 2026-09-26 | A file move that computes path edits BEFORE the move and writes them AFTER, recreating a moved file at its old path (introduced by a round-1 fix) | `tests/unit/test_retire_memory.py::test_a_moved_file_that_references_another_is_not_resurrected` | live | 0 |
| 2026-09-26 | A trim of `CLAUDE.md` that keeps every token (paths, numbers, issue ids) but drops an operative CLAUSE — five were lost and only a review lens noticed; the token survival check passed | **REJECTED 2026-09-27** — lexical clause survival cannot separate compression from loss: best setting caught 2/3 seeds (never the polarity flip) at 52/125 false flags on the reviewed 09-26 trim; 1/3 at 25/125. Script and grid: `docs/evidence/2026-09-27-claude-md-trim-check/`. The working check is a clause-loss REVIEW LENS (caught 5 clauses on 09-26 and 2 on 09-27); mechanize its invocation, not its judgement | rejected | — |
 | 2026-09-27 | "Must be committed" enforced with `git ls-files --error-unmatch`, which passes a file that is only STAGED (ADR-024 step 3: in the code AND its real-tree test; found by 3 of 6 review lenses) | `tests/lint/check_committed_idiom.py` <!-- placeholder --> — flag `ls-files --error-unmatch` in `scripts/**` where the surrounding message or name says committed/commit; accept `cat-file -e HEAD:` or `diff --quiet HEAD` | proposed | 1 |

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
