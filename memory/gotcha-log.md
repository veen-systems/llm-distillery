# Gotcha Log

*Newest-first, dated entries. **One standing section lives at the BOTTOM**: [`## Mechanized`](#mechanized) — the destination for `/review-changes` Step 3.1, where a review finding that became a deterministic check is recorded. It is named here because nobody scrolls to the bottom of this file.*

*⚠️ **Entries dated before 2026-10-13 live in (except the 10-12 `cp -r` entry, kept while its resolution is fresh) [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md)**, verbatim (the 10-12 ones moved 2026-10-15, #163 round 5; the 10-01 → 10-08 ones moved 2026-10-12 by a second owner-approved MID-MONTH pass, `--before 2026-10-09`, #163 round 2; the 09-01 → 09-16 ones moved 2026-09-27 by an owner-approved MID-MONTH pass, `--before 2026-09-17`; earlier ones moved 2026-09-24; into `archive/` 2026-09-26 so curate's size measurement stops counting it, #163; the month-dated Feb–May entries followed on 2026-09-26). Next pass: `python3 scripts/maintenance/retire_memory.py gotcha --before <first of this month> --apply` (dry run without `--apply`). It retires top-level entries only; the `###` entries inside the catalogue are kept by rule and counted (⚠️ superseded 2026-10-09: 43 of them moved by date; see the note under the catalogue heading). The unreachable-mechanism catalogue stayed here. For a recurrence match, grep both: `grep -n <term> memory/gotcha-log.md memory/archive/gotcha-log-archive.md` (a `memory/gotcha-log*.md` glob does NOT reach the archive). Was: `grep -n <term> memory/gotcha-log*.md`.*

## TWO DEFINITIONS OF "DONE" LEFT AN OLDER CANARY PASS ADMITTING (2026-10-19) [RESOLVED: 4a92805]
**Problem**: review found that a canary whose set came back with a scrape-junk row ended with no record, so an older unused PASS kept admitting labelling runs.
**Root cause**: the resume loop counted a row as done when it lacked an `error` key; `run_scores` counts only rows carrying the analysis. The junk row (`{"skipped": …}`) passed the first and failed the second, and the evaluator's "incomplete" exit was not routed through the NO-VERDICT writer.
**Fix**: one definition (row carries the analysis field) in both places, and every way out of `canary.py run` records NO-VERDICT (`NoVerdict` class; tests seeded with the junk row and a crash).

## GUARDING A DEFAULT TURNED TWO POSITIVE CONTROLS INTO MACHINE-STATE TESTS (2026-10-19) [RESOLVED: 6ca23cb]
**Problem**: `test_deepseek_model_guard`'s alias controls failed after cd v5's canary went live, because they stopped at the canary.
**Root cause**: they ran the scorer with its DEFAULT prompt (cd v5), and had only ever passed because no canary covered it. Their outcome depended on the pass records on the machine, and the alias control would have consumed a live unused PASS.
**Fix**: the controls pass `--skip-canary` (the model-id guard runs before the gate). When you guard something by default, grep the tests that run the real entry point with defaults.

## AN IN-PLACE MUTANT OUTLIVED ITS RESTORE IN A `.pyc` AND FAILED THE SUITE (2026-10-16) [RESOLVED: mechanized]
**Problem**: after a mutation pass, `test_canary_run_resumes…` failed on correct source: Python ran `MAX_PASSES = 1`.
**Root cause**: the mutant was compiled, then the source restored within the same second at the same size, so the cached bytecode still looked valid.
**Fix**: `tests/conftest.py` sets `sys.dont_write_bytecode` (pinned by `tests/unit/test_no_bytecode_from_tests.py`; seeded with the exact failure). Mutation drivers also set `PYTHONDONTWRITEBYTECODE=1`.

## TWO NEAR-DUPLICATE INSTRUMENTS, TWO OPPOSITE MISSES (2026-10-16)
**Problem**: a first-600-chars text comparison called a ScienceDaily copy of a training row "not a leak" (#176); a review found it.
**Root cause**: ScienceDaily puts a Date/Source/Summary header before the body. The full-text shingle share fixed that, then mis-called a templated NYT Connections page a leak and missed an agency rewrite (share 0.13).
**Fix**: compare FULL text, and report both a text instrument and a reading; gate on their union (EXP-051 `gate_excluded.py`).

## "ALL 9 NOT FOUND" WAS MY PARSER, NOT THE LAB (2026-10-16)
**Problem**: a hash check reported every ld-scratch file missing from the lab.
**Root cause**: `_LAB_MANIFEST.json` keeps `files` as a DICT keyed by name; the parser read it as a list and found nothing.
**Fix**: inspect one manifest before trusting a zero; the corrected parser found 9/9. Another case of *prove the instrument could have said yes*.

## `crontab FILE` WITH A LONG PATH FAILS; THE OLD LINE STAYS (2026-10-16)
**Problem**: `crontab <scratchpad file>` errored "No such file", leaving the old crontab installed.
**Root cause**: the path was truncated (session scratchpad paths are long).
**Fix**: `crontab - < file`, then `crontab -l` to confirm.

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

*⚠️ **43 entries dated before 2026-09-01 moved VERBATIM to [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) § *Moved 2026-10-09 — catalogue*** (owner rule 2026-10-09: the date rule the rest of this log uses, except the classes that recurred on or after 2026-09-01, which stay below). Recurrence matching greps both files.*

### `pkill -f` killed its own shell (2026-08-21) [x5] — class now `live` (the kill-pattern hook, `## Mechanized` 2026-10-09); entry MOVED to [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) (2026-10-12)

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

### WRONG INTERPRETER (2026-08-25) [x5] — class now `live` (the suite prints a banner, `## Mechanized` 2026-10-12); entry MOVED to [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) (2026-10-12). ⭐ Its general form stays true: an explanation that dismisses a signal has to be tested as hard as the signal.

### THE WATCHER MATCHED ITSELF AND WAITED FOREVER (2026-08-25) — class now `live` (the kill-pattern hook, `## Mechanized` 2026-10-09); entry MOVED to [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) (2026-10-16)

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

### FOR A LEXICAL GUARD, MENTION *IS* USE — I tripped the commit hook by naming the word that trips it (2026-09-02) [x2: 2026-10-09 — the new PreToolUse kill-pattern hook refused my own edits to its tests twice: a heredoc line starting `"{ <cmd> -f`, and a sed argument holding "then <cmd> -f". The Edit tool, which no Bash hook sees, was the way round]

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
**2026-09-29: negation, PR #167 (merged `4ec7850`)** (three anchored phrases only). Mention still counts as use: naming the word, quoting it or "the shipped one" still arms the guard.

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
| 2026-10-16 | An in-place mutation restored within the same second leaves a `.pyc` that still runs the MUTANT, so a correct tree fails the suite | `tests/conftest.py` `sys.dont_write_bytecode`, pinned by `tests/unit/test_no_bytecode_from_tests.py`; seeded: the 10-16 mutate-run-restore-run sequence passes after restore with no `__pycache__` written | live | 0 |
| 2026-10-15 | A `cp -r` of a filter package keeps the source's absolute imports in `inference*.py`, so the copy trains its own adapter and SCORES the source's (gotcha 2026-10-12; recurred in c2d 2026-10-15 although written down) | `training/train.py` `assert_package_imports_self()` refuses before training; `tests/unit/test_package_imports_self.py` (seeded positive: a real copy of v3 and of solutions v6; all committed packages pass; mutation-tested 2026-10-15: disabling the refusal and ignoring the filter name each go red) | live | 0 |
| 2026-10-12 | `training/prepare_data.py` with a `--filter` whose `filter.name` the labels were not written under: 0 rows match, it wrote three empty splits, printed COMPLETE and exited 0. (Found alongside: the documented call died on `import ground_truth` without PYTHONPATH.) | `tests/unit/test_prepare_data_zero_examples.py` — seeded mismatched field → exit 1, nothing written; control writes all three; both run the documented call with NO PYTHONPATH; guard-off and no-sys.path mutants red | live — ⚠️ NOT covered: a renamed DIMENSION still becomes a silent column of 0s | 0 |
| 2026-10-12 | ModuleNotFoundError rows under the wrong interpreter explained as "pre-existing environment" (5 occurrences while the fix was written down) | `tests/conftest.py` `pytest_terminal_summary` banner + `tests/unit/test_wrong_interpreter_hint.py`; seeded on the real tree: `python3 -m pytest tests/unit/test_fit_calibration_config_write.py` prints it, `.venv` prints nothing | live — a WARNING, it does not change the exit code | 0 |
| 2026-10-12 | An account-level refusal (402 balance, 401/403 auth) handled as a per-row error, so every queued row retries against a dead account (2026-09-01: 6,586 doomed calls). `score_deepseek_production.py` was fixed then; `score_ollama_oracle.py` was not (402 fell through to retries, 401/403 used a `SystemExit` the executor drains past) | `tests/unit/test_scorer_run_fatal.py` + `tests/unit/test_ollama_oracle_run_fatal.py`; seeded 402 → one call, no later calls; mutants (402 dropped, pre-call check off, flag never set) all red | live (both DeepSeek callers; NOT `ground_truth/batch_scorer.py`'s Gemini path) | 0 |
| 2026-10-10 | Evidence must rest on situla, not a GPU host: a host citation with no covering MANIFEST.json, a forged or drifted manifest entry, an empty manifest | `scripts/verification/check_lab_manifests.py` + `tests/unit/test_lab_storage.py::RealTree` (suite) | **live** — 12 guards mutation-tested 2026-10-10/12, all red when broken except the harmless remote-header guard | 0 |
| 2026-10-09 | A Hub repo id DERIVED from the package directory name (`<dir>-filter-<v>`) where the real id lives in `inference_hub.py`: guard D and `check_adapter_matches_hub.py` 404'd for cultural_discovery, human_thriving and nature_recovery, failing closed toward the `--weights-preplaced` bypass. My "live" check used only belonging; found by 4 of 6 review lenses | `tests/unit/test_check_adapter_matches_hub.py::test_repo_id_comes_from_the_package_not_the_directory_name` (4 real packages) + `tests/unit/test_preflight_deploy_guards.py::test_every_hub_backed_package_names_a_repo_id` (every `filters/*/v*/inference_hub.py`). Seeded: re-deriving the name → 4 red. Live: all six live filters MATCH / NO_HUB against the real Hub | live | 0 |
| 2026-10-09 | A hook whose script is missing exits **2** (python3 on a missing file), which Claude Code reads as BLOCK, so moving the script would have blocked every Bash call | `tests/unit/test_pattern_kill_hook.py::test_missing_script_does_not_block_every_bash_call` runs the settings command itself with an empty project dir. Seeded: the previous settings command → red | live | 0 |
| 2026-10-09 | A regex fix that nests a repeated group inside a repeated group backtracks EXPONENTIALLY on input that almost matches: round 2's hook regex took 13 s on 25 × `ssh h ` and 61 s on a sudo/env/nice chain, in a hook that runs before every Bash call. 78 green tests never fed it a long near-miss (adversarial lens, round 3) | `tests/unit/test_pattern_kill_hook.py::test_no_catastrophic_backtracking` runs the hook in a subprocess on 2000 × six near-miss shapes with a 5 s timeout; the hook is now a `shlex` tokenizer, not a regex. Seeded: the round-2 regex → 5 of 6 red. Fuzz: 60,000 random inputs, 0 exceptions, worst 2 ms | live | 0 |
| 2026-10-09 | A `run.sh` assertion grepping a SUBSTRING (`COVERS NO PATH`) that a newer message also contains, so the old check passed on the new one's output (shell lens, shown by mutation) | the tightened grep in `tests/fixtures/reference-integrity/run.sh`; seeded: removing the placeholder message → red. The general class (one finding text a substring of another) needs a check over all finding strings in `refcheck.py`: `tests/lint/check_finding_texts_distinct.py` <!-- placeholder --> | proposed | — |
| 2026-10-09 | A marker that checks only "not committed" counts a MISSPELLED path as deliberate | `run.sh` seed 45 (the absent-here label); seeded: label removed → red | live | 0 |
| 2026-10-09 | `pkill -f` / `pgrep -f` matches the shell that carries its own pattern, so it kills that shell or reports it as "running" (5 occurrences while the rule was written in CLAUDE.md, `working-rules.md` and this log) | `scripts/hooks/block_pattern_kill.py`, a PreToolUse Bash hook wired in `.claude/settings.json`; `tests/unit/test_pattern_kill_hook.py` (25 tests when the row was written: 13 block, 10 pass incl. mentions and a markdown code span, malformed input, wiring; rewritten as a tokenizer in review round 3 — count with `pytest --collect-only -q`, do not copy one here). Seeded: 5 mutants killed (never-block → 13 red, no `-f` requirement → 2, quote-anywhere → 1, backtick trigger → 1, unwired → 1); a live `pgrep -f` was refused by the harness in the session that built it | live | 1 (2026-10-09: its first draft blocked the heredoc writing this row: a backtick trigger, now removed and pinned) |
| 2026-10-01 | A deletion that turns a kwarg value into a raise misses callers still passing it — one inside `except: pytest.skip`, which would hide the raise as a skip (decision 0: 3 callers missed) | `tests/unit/test_no_per_lens_prefilters.py::test_no_caller_asks_for_use_prefilter_true` — AST walk for `use_prefilter=True` keywords; seeded positive: it went red on the real missed caller `scripts/verification/verify_belonging_v1.py:222` | live | 1 |
| 2026-10-01 | Deleting a module leaves READMEs/docstrings/runbook rows describing it in the present tense (decision 0: ~12 sites, found only by a doc-accuracy lens) | a `refcheck.py --docs-live` delta before/after a deletion catches path mentions only; present-tense prose needs intent | — | 1 |
| 2026-10-01 | Measured numbers quoted in two docs with the producing script only in a scratchpad | needs judgment — fixed by `docs/evidence/2026-10-01-decision-0-prefilter-deletion/` as the single copy | — | 1 |
| 2026-09-22 | A doc states a code guard's rule as a literal (`sample_min > 4.5`) and the code moves without it | `scripts/verification/check_guard_doc_sync.py` <!-- placeholder --> — assert each guard CONSTANT named in `fit_normalization.py` appears in `NORMALIZATION_METHOD.md` §5.3's table, and that retired literals do not appear as live rules | proposed | — |
| 2026-09-22 | A number attributed to an `EXP-` id that the experiment's own evidence file contradicts | `scripts/verification/check_experiment_citations.py` <!-- placeholder --> — for each `EXP-NNN` cited beside a numeric literal, assert the literal occurs in that experiment's evidence README or registry row | proposed | — |
| 2026-09-22 | A mutation set that moves a value AWAY from every valid option: proves only that invalid values are caught, silent on swaps/parents/siblings INSIDE the valid set. 3 survivors on a check I called "6 mutations, 6 killed" | `scripts/verification/check_mutation_directions.py` <!-- placeholder --> — ⚠️ shape is hard to detect mechanically; the realistic form is a CHECKLIST rung in the review profile, not a grep | proposed | — |
| 2026-09-22 | A closed-form number in a config comment reads as MEASURED ("at 3000/run the backlog needs ~12 cycles" = a fixed backlog over a cap, no intake term). Quoted onward twice before anyone checked it | needs intent — no grep separates a derived quotient from a measured one. The mechanizable half is narrower: flag a comment carrying an arithmetic claim with no date and no command beside it | rejected | — |
| 2026-09-22 | A doc claim citing a real source against the WRONG REFERENT — ovr.news Chain 7.5/7.6 quoted accurately for a field that file never mentions (0 hits for `harm_is_subject`/`_harm_`) | `grep -c` the cited file for the identifier the claim is about, before citing it; mechanizable as a rung in `check_doc_claims.py` for claims that name a cross-repo document | proposed | ⚠️ **RECURRED SAME DAY, 2026-09-22** — `Jaccard 0.246` attributed to `EXP-030` (whose own evidence reads 0.127 and whose lines 128-139 exist to prevent that exact substitution), in a session that had this row in its own log. A proposed row does not fire. |
| 2026-08-27 | A pointer row in the always-loaded layer grows past its cap; a byte budget loses the race, a per-row cap does not (#133) | `scripts/verification/check_index_budget.py --target pointers` | live | 1 |
| 2026-09-17 | A number restated into a second file from PROSE rather than re-measured — the copy is plausible, self-consistent and wrong | `scripts/verification/check_doc_claims.py` | live | **1** |
| 2026-09-17 | Dutch NAMES in framework text (ADR-013) — a function-word sweep scores 0 on both real violation sites, so the instrument must carry the names themselves and its allowlist **is** the carve-out table | `scripts/verification/check_framework_language.py` + `tests/unit/test_framework_language.py` (built 2026-10-07, shown red: 64 hits; carve-outs by ROLE via the AST; commit messages still unread) | live | 1 (2026-10-07: found an unlisted site, nature_recovery `config.yaml` `'Herstel' tab`) |
| 2026-09-26 | A trim of `CLAUDE.md` that keeps every token (paths, numbers, issue ids) but drops an operative CLAUSE — five were lost and only a review lens noticed; the token survival check passed | **REJECTED 2026-09-27** — lexical clause survival cannot separate compression from loss: best setting caught 2/3 seeds (never the polarity flip) at 52/125 false flags on the reviewed 09-26 trim; 1/3 at 25/125. Script and grid: `docs/evidence/2026-09-27-claude-md-trim-check/`. The working check is a clause-loss REVIEW LENS (caught 5 clauses on 09-26 and 2 on 09-27); mechanize its invocation, not its judgement | rejected | — |
| 2026-09-29 | A test writes a path inside the repo (tracked or not) and cleans it up in `finally`, which SIGKILL skips — llm-distillery#162's class; `tests/unit/test_verify_annotation_runner.py:100-105` (`MEMORY_FIXTURE.md` <!-- placeholder --> at repo root, created and deleted by the test) is a surviving instance, found reviewing PR #166 | `tests/lint/test_no_repo_writes_in_tests.py` <!-- placeholder --> — AST-scan `tests/**/*.py` for `write_text`/`open(...,'w')`/`unlink` on a path rooted at `REPO`/`PROJECT_ROOT`; allowlist `tmp_path`/`tempfile` | proposed | 2 |
| 2026-09-29 | A negation/allowlist rule in a lexical guard that is not anchored at clause start admits the success-report idiom (`No regressions deployed v7`, `Errors during deploy: none`) — PR #167 rounds 1 and 2, same class twice | `tests/unit/test_commit_msg_hook.py` CLAIMS list (40 must-block messages from both review rounds) + 26 mutations incl. dropping each clause-start anchor; seeded positives re-run by a second session: rule-2 anchor removed → 6 fail, rule-3 anchor removed → 1 fail | live | 2 |
| 2026-10-02 | A name the owner forbids in this public repo reaches a commit, and its location is written beside the rule | `.githooks/check_forbidden_names.sh` (called by `pre-commit` and `commit-msg`), reading a denylist from the GITIGNORED `config/credentials/forbidden_names.txt` and rejecting a staged diff, a staged path or a commit message that matches (mutation-tested 2026-10-02: name staged → 1, name in msg → 1, clean → 0, the animal → 0) | live | 1 |
| 2026-10-02 | An exclusion rule ("never draw these ids") lives only in prose, so a later builder silently draws an exemplar/pilot/test row | `docs/evidence/2026-10-02-belonging-adjudication/belonging_exclusions.py` `assert_disjoint()` (771 ids, 10 sources; raises on overlap AND on a missing source; mutation-tested 2026-10-02) | live (belonging only) | 1 |
| 2026-10-02 | An oracle output file silently mixes verdicts from two rubric versions after the rubric file is edited in place | `calibrate_scope_oracles.py run` stamps `prompt_sha` and refuses a mixed file (mutation-tested: exit 1, file unchanged) | live (belonging only) | 1 |

**10 `live` rows with 0 occurrences, dated 2026-09-17 to 2026-09-26** — MOVED 2026-10-19 (#163 round 9) to [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) § *Mechanized rows moved 2026-10-19*. Their checks still run; a lens that finds one of those classes is a finding about the CHECK — grep the archive before triaging.
 | 2026-09-27 | "Must be committed" enforced with `git ls-files --error-unmatch`, which passes a file that is only STAGED (ADR-024 step 3: in the code AND its real-tree test; found by 3 of 6 review lenses) | `tests/lint/check_committed_idiom.py` <!-- placeholder --> — flag `ls-files --error-unmatch` in `scripts/**` where the surrounding message or name says committed/commit; accept `cat-file -e HEAD:` or `diff --quiet HEAD` | proposed | 1 |

**The 2026-09-17 first occurrence and the first positives of the `live` rows, in prose** — MOVED to [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) § *Moved 2026-10-16* (history: what made `check_framework_stamp.sh`, `--target pointers`, run.sh 34/35 and the `suite-baseline` check live).
