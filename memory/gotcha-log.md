# Gotcha Log

*Newest-first, dated entries. **One standing section lives at the BOTTOM**: [`## Mechanized`](#mechanized) — the destination for `/review-changes` Step 3.1, where a review finding that became a deterministic check is recorded. It is named here because nobody scrolls to the bottom of this file.*

*⚠️ **Entries dated before 2026-09-17 live in [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md)**, verbatim (the 09-01 → 09-16 ones moved 2026-09-27 by an owner-approved MID-MONTH pass, `--before 2026-09-17`; earlier ones moved 2026-09-24; into `archive/` 2026-09-26 so curate's size measurement stops counting it, #163; the month-dated Feb–May entries followed on 2026-09-26). Next pass: `python3 scripts/maintenance/retire_memory.py gotcha --before <first of this month> --apply` (dry run without `--apply`). It retires top-level entries only; the `###` entries inside the catalogue are kept by rule and counted (⚠️ superseded 2026-10-09: 43 of them moved by date; see the note under the catalogue heading). The unreachable-mechanism catalogue stayed here. For a recurrence match, grep both: `grep -n <term> memory/gotcha-log.md memory/archive/gotcha-log-archive.md` (a `memory/gotcha-log*.md` glob does NOT reach the archive). Was: `grep -n <term> memory/gotcha-log*.md`.*

## AN ALARM TRIGGER I WROTE COMPARED TWO POPULATIONS — and fired falsely at 02:47 (2026-10-09) [*rate needs population*, again]
**Problem**: belonging v3's early-refit trigger was "if ovr's normalized ≥ 4.5 pass count drops below 100%". ovr measured
12/19 = 63% on v3's raw ≥ 4.0 rows and escalated to the owner. v1 on the SAME measure was 469/872 = 54% (47–66% per file).
**Root cause**: the "100%" baseline came from ovr.db's published top-50 (winners of a cap); the trigger was read on every
raw ≥ 4.0 row in a file. Different populations; nothing in the rule named its population, so ovr could not see it.
**Fix**: trigger reworded to the same measure on both sides (`docs/TODO.md` item 0, ledger `H-BB5`). **Action:** a
trigger handed to another session names its population AND quotes the baseline measured on that population before it
ships. A threshold with no baseline number beside it is the tell.

## "TELL ME ONLY IF IT FAILS" WOULD HAVE HIDDEN A CHECK THAT NEVER RAN (2026-10-09)
**Problem**: ovr offered to message only if Belonging's pass check failed. I asked for a line either way. The 02:47
check then could not run at all (ovr's summarizer OOM-died before ingesting v3), which the silence-means-pass deal
would have reported as a pass.
**Fix / action**: a delegated check reports `N/M` or "could not run, because …", always. Silence is not a verdict
(*before believing a negative, prove the instrument could have said yes*).

## ROLLBACK STATED FROM THE OLD DEPLOY MECHANISM (2026-10-08)
**Problem**: I wrote "rollback = remove `filters/belonging/v3`, v1 loads" into STATUS, #170 and peer messages. NexusMind's
review: since NM#395 the scorer image bakes only the served version, so removing v3 stops the scorer (all six filters).
**Root cause**: "NexusMind loads the highest vN on disk" was true of the gpu-server path, which is stale; I imported the
mechanism with the precedent (*a precedent is a mechanism claim*). It also survived into NM commit 4901fb5's message.
**Fix**: corrected in STATUS (`d71f972`), #170, ovr and pipeline-atlas. **Action:** state a rollback only after the
deploying session confirms the mechanism on the CURRENT path; `docs/TODO.md` item 2b rewrites the stale RUNBOOK path.

## A BACKGROUND ORACLE RUN LOOPED ALL NIGHT ON TWO FAILING ROWS — ~74k failed calls (2026-10-07/08)
**Problem**: `ground_truth.batch_scorer` (sequential mode) scored 796/798 easy negatives, then re-fetched the 2
permanently failing rows (`llm_api_error`) as "unscored" for ~6,100 batches until killed 12 hours later. Billing
impact unknown (the error text was never logged).
**Root cause**: a failed article was never recorded, so `load_unscored_articles` returned it forever. The 2026-09-01
"402 is not a per-row error" entry is the same family: the scorer has no per-run failure budget.
**Fix**: failures are now skipped for the rest of the run (`_failed_this_run`, test in `test_batch_scorer.py`).
**And**: a background oracle run gets a completion check, not just a start: I launched it and never looked at its
log again until the next morning. Read the log tail (or the row count vs expected) before reporting "running".

## "THE SOURCE FILES EXPIRED" — WRITTEN INTO TWO DOCS, REFUTED BY THE MONTHLY ARCHIVE (2026-10-07) [17th occurrence of *establish what a source excludes*]
**Problem**: Recovering full text for cut belonging rows, I found 23+25 source files gone from sadalsuud's live
`filtered/` window and committed "67 rows lost", "16 judged rows' files expired", "the only copies left" to GATE.md
and the TODO. All 393 rows were in `data/archived/nexusmind_2026-09.tar.gz`.
**Root cause**: I treated the live window as the source. `memory/nexusmind-data-sources.md` § *THE LIVE WINDOW
ROLLS. THE DATA DOES NOT* says exactly this, and the same mistake is the 09-01 entry in the archive. I read that
memory file only at `/curate`, after writing the claim.
**Fix**: Before writing "lost", "expired" or "unrecoverable" about NexusMind rows, list
`~/local_dev/NexusMind/data/archived/` and stream the month's `nexusmind_YYYY-MM/<lens>/scored.jsonl` member.
A prose lesson did not fire a 17th time: this wants a check (`feedback-prose-promotion-does-not-fire`).

## A DRAW THAT CUT TEXT AT 4,000 CHARS BROKE A HEAD+TAIL MODEL'S INPUT (2026-10-07)
**Problem**: v1 scored on the belonging held-out set disagreed with production on 20/295 verdicts (max |Δ| 3.73),
all on the 133 rows the draw had cut at 4,000 chars. The uncut rows reproduced production exactly.
**Root cause**: belonging reads the first 256 AND LAST 256 tokens. Cutting the text replaces the real ending with
text from around char 4,000. The draw (and harvest r1, and its oracle labels) inherited a "harmless" cap from a pilot.
**Fix**: Before capping article text for any measurement, read the filter's `preprocessing.head_tail`. Keep the full
text, or prove the cap sits inside what the model reads. Proven by re-scoring 117 recovered full texts: 0 flips.
Evidence: `docs/evidence/2026-10-03-belonging-heldout/GATE.md` § *v1 reference run*.

## A GATE COUNTED AN UNSCORED ROW AS A CORRECT REJECTION — a forged PASS (2026-10-07)
**Problem**: My belonging gate runner treated any row not `stage2` as "out". A reviewer set `stage_used: null` (what
an invalid article returns) on every deciding negative and got PASS. A forward score file copied as `_reversed`
also passed "both orders". 15 tests and 9 mutations had all been green.
**Root cause**: The tests and mutations covered the RULE (`decide`), not the inputs it trusts. The refusals that
guard the inputs had no test at all.
**Fix**: In a gate, any input state the rule does not define RAISES (exit 2, distinct from FAIL). Mutation-test
the refusals as well as the rule. The second review round still found gaps in the fixes (a syndicated twin, Latin-only
titles): `feedback-articulating-is-not-applying` recurred.

## STRIPPING A URL'S QUERY STRING MERGED SIX DIFFERENT ARTICLES (2026-10-07)
**Problem**: A url-normaliser for an overlap check dropped `?…`. aib.media's WordPress urls are `/?p=167850`, so six
different stories became one url and a clean build would have been refused.
**Fix**: Drop only tracking parameters (`utm_*`, `fbclid`, `gclid`, `mc_*`, `ref`); keep the rest. Measure a
dedup key on real data before trusting it. A near-duplicate key also needs a boilerplate filter: 13 different
20minutos stories shared site text with the same held-out row.

## A CHECKER COMMITTED IN THE SAME CHANGE AS ITS TEST FILE WAS RED AT THAT COMMIT (2026-10-07)
**Problem**: `8c464cd` added `check_framework_language.py` and its test. The checker scans TRACKED files, and the
test's own fixtures (and the checker's name list) were violations once committed. Green before `git add`, red after.
**Fix**: Run a repo-scanning check AFTER staging (or over `git ls-files` plus the new files), then the full suite,
before committing.

## A RULE BORROWED FROM ITS ORIGIN BECAME THE DEFINITION — the "doing" test (2026-10-02)
**Problem**: I adopted ovr.news `BRAND.md:84`'s "doing, not feeling" test as the core of the belonging rubric.
The first adjudication pilot passed every instrument check (controls 4/4, A vs B 1.000) and failed the owner
check at 3/10.
**Root cause**: The test was written for ONE case, belonging whose occasion is a harm, and was marked "Undecided"
there. Generalised, it excluded what 0.50 of v1's weight rewards (intergenerational, rootedness, slow presence).
Chasing an external curator's picks, which mostly come from solutions-style stories, had pulled me toward it.
**Fix**: Before importing a rule, read the paragraph it came from and name the case it was built for
(`feedback-precedent-is-a-mechanism-claim`). Ground a lens definition in its own dimensions and in research,
not in a benchmark from a different lens.

## A PRE-REGISTERED κ BAR THAT RARITY MADE UNREACHABLE (2026-10-02)
**Problem**: Pilot v2's bar was κ ≥ 0.75. The passes agreed on 99/100 rows and κ was 0.66: FAIL.
**Root cause**: With ~2 in-scope rows in 100, one disagreement caps κ near 0.66. I never checked the bar could be
met at the expected prevalence (`feedback-prove-the-bar-is-reachable`).
**Fix**: Before setting an agreement bar, simulate it at the predicted prevalence (pilot v3 did: one disagreement
in 100 at p=0.25 gives κ 0.973). Below a minimum count of positives, report κ and do not judge it.

## MY PREDICTIONS FROM TITLES OVERSHOT THREE TIMES IN ONE DAY (2026-10-02)
**Problem**: I predicted in-scope rates of 15–35%, 25–50% and 25–50%. The judges measured 1/39, 0/30 and 2/48.
**Root cause**: Titles of belonging-shaped stories oversell. The predictor (me, from titles) and the judges
(Claude, from full text) share a model but not an input; only the full text decides.
**Fix**: Do not size a harvest, a stratum or a budget from a title read. Predict, but measure on full text before
any decision rests on the rate.

## PARALLEL SUBAGENTS SHARED ONE SCRATCH FILE (2026-10-02)
**Problem**: In the first pilot one judge overwrote another judge's temporary script in the shared scratchpad, and
fixed its output by hand.
**Fix**: Give every parallel subagent its own input/output directory AND its own `scratch/`, and say so in the
instructions (pilots v2/v3 and the calibration did; no recurrence).

## A RUBRIC EXAMPLE THAT DESCRIBES A CALIBRATION ROW TELLS THE ORACLE THE ANSWER (2026-10-02)
**Problem**: Rubric v2.1's new examples (a hospital clean-up, inmates making theatre, a DIY workshop) were taken
from calibration rows the owner had just ruled on. Re-running an oracle on v2.1 would score those rows trivially.
**Fix**: Flag such rows (`NAMED_IN_RUBRIC_V2_1`) and report them apart from the headline. The same leak as the
v2 prompt's "synthetic" examples, from the opposite direction: rulings flowing INTO the instrument.

## "READER-FACING" WAS DEFINED BY THE QUERY I WROTE, NOT THE GATE THAT BINDS (2026-10-02)
**Problem**: I described 2,368 belonging articles as "normalized ≥ 4.5, what readers could see". Then I concluded
that the curator's community stories (raw 4.1–6.7) "pass, mid-pack". Every sampled row had raw ≥ 5.77, and 6 of the
17 picks could never have reached readers.
**Root cause**: `ovr.db` holds only the winners of ovr's top-50-per-lens cap, a competition per run. My WHERE clause
was looser than the gate that had already filtered the table, so it constrained nothing. Nobody compared the
sample's minimum with the stated predicate.
**Fix**: Before naming a population, print the min/max of the predicate column in the sample. A minimum far above
your threshold means an upstream gate binds, so name it. This is the working rule "establish what a source
EXCLUDES", again.

## WRITING DOWN THE LEAK RULE LEAKED THE LOCATION (2026-10-02)
**Problem**: The owner said never to name an external curator in this public repo. I recorded that rule in
`docs/TODO.md`, and in the same item listed WHERE the name already leaks (the source-id prefix and the dirs).
`git grep` then finds it in one step. It reached an unpushed commit, and was squashed out before the push.
**Root cause**: The same mechanism as "for a lexical guard, mention IS use" (2026-09-02, archive), a second
occurrence. Describing what must not appear means writing a pointer to it.
**Fix**: Keep the inventory of a sensitive thing in a LOCAL file (here, the plan file), and keep only the rule in
the repo. Before pushing, grep the staged diff AND the unpushed commits (`git log -p origin/main..HEAD`).


## "SYNTHETIC" EXAMPLES I WROTE AFTER READING THE TEST SET WERE THE TEST SET (2026-10-02)
**Problem**: The belonging v2 prompt's contrast examples were called "synthetic, so no contamination". Six of
them paraphrase test rows (the parish reopening, the rent march, the chef, the burial ground, the souvenir
weaving, the minister's centre). The headline 41 → 11–14/65 became a DEV score, and the methodology review
caught it, not me. In the same session I had removed two probe-derived exclusions from probe A for exactly
this reason.
**Root cause**: An author who has read the evaluation rows cannot write examples independent of them.
Paraphrase does not launder it: the SHAPE is what the prompt teaches and the test probes.
**Fix**: Write prompt examples BEFORE reading the evaluation set, or from rows outside it, and record their
source beside each example. Treat any set the prompt author has read as a dev set. Clean evidence comes only
from a sample drawn AFTER the prompt is frozen.

## A ROW SELECTED BY THE INSTRUMENT CANNOT TEST THE INSTRUMENT — 19/19 recall, 33/33 baseline (2026-10-02)
**Problem**: Two circular numbers from the same session:
- 11 P rows were added because the v1 oracle scored them ≥ 6.15, and then v1 recall was reported as 19/19.
- The 49-row probe was selected because v2-Flash passed it, and its 33/33 "baseline" held by construction;
  a Flash re-run alone flips about 3 of 14.
**Root cause**: The selection criterion was the measured quantity. The same shape as "the checker and the
checked must be different objects" ([[feedback-hand-built-population]]).
**Fix**: Before reporting a rate on a hand-added stratum, write down what selected it. If the selector is the
instrument under test, report that stratum separately and add a re-run control.

## `S=x && (job1) & (job2) &` — THE ASSIGNMENT LIVES ONLY IN THE FIRST BACKGROUND JOB (2026-10-01)
**Problem**: The second oracle run wrote to `/v2_draft1.log` (Permission denied) and never started. The first
run succeeded, so the pair looked half-done, not broken.
**Root cause**: `A && B & C &` parses as `(A && B) &` then `C &`, so `S` was set only inside the first
background list.
**Fix**: Assign variables on their own line before backgrounding, or use absolute paths. Check BOTH logs'
`Articles scored` lines before reading results.

## TURNING A NO-OP INTO A RAISE IN SHARED CODE BREAKS EVERY CONSUMER STILL ON THE OLD DEFAULT — and the rule I broke at the end of the same session (2026-10-01)
**Problem**: Decision 0 made `use_prefilter=True` raise in `FilterBaseScorer` (the right call: a silent no-op is the NM#284 shape). Green suite, outcome proven. Review then found three callers still passing `True` (one inside `except: pytest.skip`, which would have hidden the raise as a skip forever), ~12 docs still describing prefilters in the present tense, and a cross-repo trap: NexusMind's package copies default `use_prefilter=True`, so syncing `filters/common` ALONE makes every un-redeployed package raise off the GPU path. At session close I ran `git add -A memory/`, which the working rules forbid even when scoped.
**Root cause**: I grepped for callers of the deleted MODULE, not for callers of the changed VALUE. A deletion changes two surfaces: who imports it, and who passes the argument whose meaning changed. The `add -A` was speed at the end of a long session; checked after the fact (25 files, all mine) rather than prevented.
**Fix**: `test_no_caller_asks_for_use_prefilter_true` (AST, `live` in § Mechanized; it went red on the real missed caller). Sync sequence recorded in `docs/TODO.md` item 1 and sent to NexusMind. **Lesson: when a value changes meaning, enumerate callers of the VALUE across BOTH repos, and when shared code tightens a default, list who still runs the old default before shipping.**

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

### `pkill -f "<pattern>"` killed the shell that carried the pattern (2026-08-21) [x5] (2026-10-02: `pkill -f` on a git-grep pattern killed its own shell, exit 144)
**Problem**: `pkill -f -- "-L 11435:localhost:11434"` closed the SSH tunnel *and* the bash
process running the command, which exited 144 mid-script and skipped the rest.
**Root cause**: the documented `pgrep -f` trap — the pattern appears in the invoking shell's
own argv — applies identically to `pkill`, which then kills it.
**Fix**: kill by PID from `ps -eo pid,args | grep -v grep`, or `ssh` the target and kill there.
The existing working rule says `pgrep -f` cannot answer "is it running?"; **extend it: `pkill -f`
cannot answer "stop it" either.**

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
| 2026-09-17 | Dutch NAMES in framework text (ADR-013) — a function-word sweep scores 0 on both real violation sites, so the instrument must carry the names themselves and its allowlist **is** the carve-out table | `scripts/verification/check_framework_language.py` + `tests/unit/test_framework_language.py` (built 2026-10-07, shown red: 64 hits; carve-outs by ROLE via the AST; commit messages still unread) | live | 1 (2026-10-07: found an unlisted site, nature_recovery `config.yaml` `'Herstel' tab`) |
| 2026-09-26 | A "lossless" check that compares two quantities built from the same blocks — equal by construction, so it can never fail (`retire_memory.py`, round 1 of review) | `tests/unit/test_retire_memory.py::test_reconstruction_check_can_fail` — the split is mutated to drop a line and the run must refuse and write nothing | live | 0 |
| 2026-09-26 | A file move that computes path edits BEFORE the move and writes them AFTER, recreating a moved file at its old path (introduced by a round-1 fix) | `tests/unit/test_retire_memory.py::test_a_moved_file_that_references_another_is_not_resurrected` | live | 0 |
| 2026-09-26 | A trim of `CLAUDE.md` that keeps every token (paths, numbers, issue ids) but drops an operative CLAUSE — five were lost and only a review lens noticed; the token survival check passed | **REJECTED 2026-09-27** — lexical clause survival cannot separate compression from loss: best setting caught 2/3 seeds (never the polarity flip) at 52/125 false flags on the reviewed 09-26 trim; 1/3 at 25/125. Script and grid: `docs/evidence/2026-09-27-claude-md-trim-check/`. The working check is a clause-loss REVIEW LENS (caught 5 clauses on 09-26 and 2 on 09-27); mechanize its invocation, not its judgement | rejected | — |
| 2026-09-29 | A test writes a path inside the repo (tracked or not) and cleans it up in `finally`, which SIGKILL skips — llm-distillery#162's class; `tests/unit/test_verify_annotation_runner.py:100-105` (`MEMORY_FIXTURE.md` <!-- placeholder --> at repo root, created and deleted by the test) is a surviving instance, found reviewing PR #166 | `tests/lint/test_no_repo_writes_in_tests.py` <!-- placeholder --> — AST-scan `tests/**/*.py` for `write_text`/`open(...,'w')`/`unlink` on a path rooted at `REPO`/`PROJECT_ROOT`; allowlist `tmp_path`/`tempfile` | proposed | 2 |
| 2026-09-29 | A negation/allowlist rule in a lexical guard that is not anchored at clause start admits the success-report idiom (`No regressions deployed v7`, `Errors during deploy: none`) — PR #167 rounds 1 and 2, same class twice | `tests/unit/test_commit_msg_hook.py` CLAIMS list (40 must-block messages from both review rounds) + 26 mutations incl. dropping each clause-start anchor; seeded positives re-run by a second session: rule-2 anchor removed → 6 fail, rule-3 anchor removed → 1 fail | live | 2 |
| 2026-10-02 | A name the owner forbids in this public repo reaches a commit, and its location is written beside the rule | `.githooks/check_forbidden_names.sh` (called by `pre-commit` and `commit-msg`), reading a denylist from the GITIGNORED `config/credentials/forbidden_names.txt` and rejecting a staged diff, a staged path or a commit message that matches (mutation-tested 2026-10-02: name staged → 1, name in msg → 1, clean → 0, the animal → 0) | live | 1 |
| 2026-10-02 | An exclusion rule ("never draw these ids") lives only in prose, so a later builder silently draws an exemplar/pilot/test row | `docs/evidence/2026-10-02-belonging-adjudication/belonging_exclusions.py` `assert_disjoint()` (771 ids, 10 sources; raises on overlap AND on a missing source; mutation-tested 2026-10-02) | live (belonging only) | 1 |
| 2026-10-02 | An oracle output file silently mixes verdicts from two rubric versions after the rubric file is edited in place | `calibrate_scope_oracles.py run` stamps `prompt_sha` and refuses a mixed file (mutation-tested: exit 1, file unchanged) | live (belonging only) | 1 |
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
