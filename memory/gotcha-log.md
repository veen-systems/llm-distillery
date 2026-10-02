# Gotcha Log

*Newest-first, dated entries. **One standing section lives at the BOTTOM**: [`## Mechanized`](#mechanized) — the destination for `/review-changes` Step 3.1, where a review finding that became a deterministic check is recorded. It is named here because nobody scrolls to the bottom of this file.*

*⚠️ **Entries dated before 2026-09-17 live in [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md)**, verbatim (the 09-01 → 09-16 ones moved 2026-09-27 by an owner-approved MID-MONTH pass, `--before 2026-09-17`; earlier ones moved 2026-09-24; into `archive/` 2026-09-26 so curate's size measurement stops counting it, #163; the month-dated Feb–May entries followed on 2026-09-26). Next pass: `python3 scripts/maintenance/retire_memory.py gotcha --before <first of this month> --apply` (dry run without `--apply`). It retires top-level entries only; the `###` entries inside the catalogue are kept by rule and counted. The unreachable-mechanism catalogue stayed here. For a recurrence match, grep both: `grep -n <term> memory/gotcha-log*.md`.*

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

### `pkill -f "<pattern>"` killed the shell that carried the pattern (2026-08-21) [x5] (2026-10-02: `pkill -f` on a git-grep pattern killed its own shell, exit 144)
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
**2026-09-29: PR #167 (merged `4ec7850`).** Prose-only `filters/*/v*/` dirs verify as N/A; "nothing deployed", "not deployed" and "deploy N/A" pass. Mention still counts as use.

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
| 2026-09-17 | Dutch NAMES in framework text (ADR-013) — a function-word sweep scores 0 on both real violation sites, so the instrument must carry the names themselves and its allowlist **is** the carve-out table | `scripts/verification/check_framework_language.py` <!-- placeholder --> | proposed | — |
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
