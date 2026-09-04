# Working rules — the full text, with evidence

**These are non-negotiable constraints, not tips.** Each was promoted out of the
gotcha log only after repeating. `CLAUDE.md` carries the imperative form of each
rule in its Hard Constraints section, because they are needed every session; this
file carries the **evidence, the occurrence catalogue and the war stories**, which
are reference material and are not.

Moved here 2026-08-12 by `/audit-context`: the block was 6,136 chars of an
auto-loaded 38.7k file (38,743 bytes), against a 40k tool warning. Nothing was cut — the rules
stay in `CLAUDE.md`, their justification lives here.

⚠️ **If you are about to weaken or delete one of these rules, read its evidence
here first.** Every one of them exists because something shipped broken.

## The rules, in full

### A FAILING CHECK MAY BE THE CONTROL WORKING — never "fix" it before asking what it proves

**Added 2026-08-15, from my own error, caught by NexusMind declining it.**

I found that validating 788 live producer rows against Contract A gave **788/788
violations, all one field (`source_group`) unexpected at a closed root** — verified, and
the facts were right. I inferred that declaring the field was therefore a **prerequisite**
for the canary, and recorded the resequencing. **The inference was the error.**

`source_group` is the production contract check's **only non-circular acceptance control**:
an independent field, on 100% of rows, **that the check was never shown** — and therefore
the only evidence the check *can fail at all*. It was already a recorded decision (NM#304,
NexusMind `contracts/CHANGELOG.md` 1.18.0) guarded by a test whose name says so, which failed by
design the moment someone tried it.

⭐ **The trap, in its general form: I proposed spending an acceptance control PRECISELY IN
ORDER TO DRIVE A VIOLATION COUNT TO ZERO — the very number whose trustworthiness the
control exists to establish.** And a synthetic replacement cannot restore it: injecting a
key you chose proves the check catches **what you already knew to look for**; the organic
control proves it catches **something nobody designed it to catch.** Not replaceable once
spent.

**So a 100%-failure reading is an argument for building the observer SOONER, not for
removing the thing that is failing.** Ask, in order: *what does this failure prove that
nothing else proves?* — then *does my fix delete that proof?*

⚠️ **Sibling, same shape, opposite sign** (2026-08-12): *the archive survived only because
the purge was broken* — verify that a mechanism **not** running is not what is protecting
you. Together: **before changing a thing that is failing or dead, establish what its
failure or deadness is currently buying you.**

*(Also from the same exchange, and the reason this was caught at all: NexusMind hit three
pre-existing tests, reverted twice, and modified none of them. **A failing test is a
finding, not an obstacle.**)*

⚠️ **Corollary found the same day — REFUTING IN PLACE IS NECESSARY AND NOT SUFFICIENT.**
A wrong figure was refuted in place rather than deleted, on the argument that *a refuted
figure carries its refutation wherever it travels*. **It does not: the same wrong reading
was still asserted in three live places in the producer's tree** (verified: the literal
survives at `FluxusSource/src/utils/date_parser.py:242`). First reading: the argument holds
**within** a repo and fails at the boundary. ⛔ **Sharpened when a peer found a FOURTH stale
site — the docstring of the test whose job was pinning that very behaviour. It did not
travel within one repo either.** So: refute in place *and* **grep the number, and its
complement.** The value alone is not enough; the claim it supports gets restated in words
that do not contain it.

⭐ **SIBLING RULE, and it is cheaper than any of the above: BEFORE BUILDING WHAT A NOTE
SAYS IS MISSING, `ls` FOR IT.** 2026-08-15: a relay's compressed *"the canary does not
exist"* was believed and an ad-hoc validator written, while the canary had existed since
2026-08-14 — **and the correct statement was in NexusMind's own always-loaded index the
whole time** (*"`validate_production_contract.py` has no automatic caller"*). **So this was
never a cross-repo information gap; a compressed relay outranked a precise local
statement that loads every session.** ⭐ **"X does not exist" and "X is not yet invoked"
have completely different costs, and only the second was true — the first licenses
rebuilding.** When a note reports an absence, check the absence before acting on it,
especially when the note is a *summary* of someone else's summary.

⚠️ **And the sampling half, from the producer's own review the same day: A SAMPLE WITH NO
NEGATIVES CANNOT LICENSE AN ABSOLUTE.** *"Expect ~100%"* was generalised from 662/662 and
737/737; an independent sample read **97.2%**. ⭐ **The check that catches a broken
instrument is NOT the check that bounds the rate** — a differently-derived cross-check
validates *agreement on the rows you have*, never *the representativeness of the rows you
chose*. Same family as the hand-built-population rule below, arriving through the back
door of a **verification** rather than a measurement.

### Every measurement error this project has made was a HAND-BUILT POPULATION

⚠️ **TWICE MORE on 2026-08-16, both mine, both inside instruments built that same hour.**
(1) `origin`'s shelf data was voted on by parsing `config/sources/*.yaml` myself instead
of asking `UnifiedConfigManager`, which resolves sources my parse missed — so
`legal_policy` scored 3/3 = 100% for me and **3/4 = 75% for the peer who used the
loader**, and a 4-source vote was stamping `country: NL` onto a 22-source subject shelf.
(2) The Contract A smoke test **hand-listed the field names it checked**, so it reported
16/17 on a delivery carrying 17/18 — it could not see a field that shipped after the list
was written. ⭐ **Both are the rule's own subject matter occurring inside the tool that
measures compliance with it.** Now derived from the loader and from the schema.

⚠️ **Recurred TWICE on 2026-08-15, and one of them was inside `/curate` itself.**
(a) The `+1.98h` NewsAPI clock offset was an artifact of comparing each source to the
**run median** when that source *runs first in the cycle* — the true offset is exactly
2h, and the fabricated 72-second "gap to the fabrication signature" was my denominator,
not the data. (b) A per-file annotation table built by `paste`-ing two independently
generated lists silently misattributed 8 annotations to the wrong file, during the
curation step whose job is to catch exactly this. ⭐ **The promoted rule did not
prevent either; it only made them recognisable afterwards.** Both were fixed by
switching to a population the tool already emits — the pipeline's own per-source
`collected_date`, and a `for f in …; do grep -c` that carries its own filename.

*(Added to CLAUDE.md 2026-08-12; its evidence was in `gotcha-log.md` only, which made
this file's own "full text of each rule" contract false for one rule — caught by
`/review-changes` the same day.)*

Across a four-session cross-repo investigation, **every quantitative claim any session
made failed under checking, and not one failed where its author was looking.** The
shared structure: someone chose a file, a window, a join key or a directory, and the
*choice* carried the defect while attention went to the arithmetic.

Instances, all independent: a rate whose numerator and denominator had different
exclusion lists; a six-filter union masking a 33-point single-filter exclusion; a
counterfactual replay over stored rows reported as observed attrition; `ls docs/adr/`
run in the wrong repo; a per-filter field (`stage_used`, 82% disagreement) read as
article-level; a sliding `[-N:]` glob evaluated twice, measuring two different file
sets; a `sorted(glob(...))[-40:]` that sorted by path and so sampled one filter only;
and a character class hand-written for latin-1 that was blind to cp1252 — 83% of its
population.

**Prefer a population the pipeline already computes to one you construct**, and
**Derive classes rather than writing them** (`bytes(range(0x80,0xC0)).decode(codec)`
*is* the continuation set, by construction) — ⚠️ **but derivation is a COVERAGE fix,
not a discriminator, and it does not transfer between codecs.** Measured 2026-08-12:
for **cp1252** the derived classes exclude the `’`+accented-vowel pair entirely, so
deriving genuinely fixes that arm (the large one — 1,210 rows vs 256). For
**mac_roman** the derived leads CONTAIN `’` (0xD5) and the derived continuations
CONTAIN `é` (0x8E), so a derived-class candidate stage **flags `l’éclipse`, the
round-trip confirms it, and you get `lՎclipse`** — FS#167 reproduced in full.
Deriving is how the 2,030 false-positive pairs were *enumerated*; it builds that set
rather than excluding it. **Two arms, two different answers.** Safety still needs the
conjunction: an unambiguous signature AND a clean inversion, then hand-review. Hand-built populations and hand-built
character classes are the same failure with different nouns. Make the missing case
raise, never return `None`.

Moved here from `memory/MEMORY.md` on 2026-08-06: they are always-needed
constraints, and the memory index is navigational. Each was promoted only after
repeating.

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — and then prove the outcome changed at the END of the run.** *(⚠️ **17th occurrence 2026-09-04 — A FLAG ACCEPTED BY ARGPARSE, DOING NOTHING, FOR EVERY FILTER EVER TRAINED.** `training/train.py --select-metric recall_at_20` parsed, ran, and selected on **aggregate MAE** — the metric ADR-023 forbids ranking on — because `dimension_weights_list` was built only under `if args.sample_weight_scale > 0` (default 0.0) and that same list is what `compute_metrics` needs to emit the needle metrics. Two unrelated flags coupled through one variable named for the wrong one. ⛔ **The blast radius was already on disk and nobody had looked**: of 18 `training_metadata.json`, 16 carry `sample_weight_scale` 0/None, and four DEPLOYED filters (`solutions v6`, `cultural_discovery v5`, `belonging v1`, `investment_risk v6`) have no needle keys in `training_history.json` at all. ⭐ **The reusable part is the test suite's silence: nothing in `tests/` referenced `training.train`, so "573 tests pass" was TRUE and carried ZERO information about the changed module.** A green suite that cannot execute the changed lines is not evidence about them — check that a test *can reach* the code before citing its pass. ⛔ And I then shipped the fix citing an outcome proof that was a **tautology**: *"the pre-fix run contains that string 0 times"* — for a string literal the same commit introduced, so no pre-fix run could ever have contained it. A presence check on a new constant, dressed as a before/after. Replaced with a real control (pre-fix expression vs resolver over every config: **6 wrong or invented**). Records: `1878e7b`, llm-distillery#144/#145, `docs/evidence/2026-09-04-v8-checkpoint-selection/`.)* *(⚠️ **16th occurrence 2026-08-25 — a CONFIG CHANGE WHOSE FIRST EXERCISE WAS PRODUCTION.** `investment_risk` was paused (two config lines, owner ruling), deployed at 17:26 with a green suite and a written decision record, and nobody watched a service start. At 20:09:54 `nexusmind.service` failed on a fail-closed deploy gate — `deploy/smoke_test_articles.jsonl` still named the paused filter — and the entire 20:03 cycle was lost. The outcome check that existed (block-ledger `placements` 6 → 5) was correctly identified in advance and **deferred to the very cycle that then never ran**, so the plan contained its own gap. ⭐ **A scheduled service turns "deploy and wait" into "let production be the test." If a config key is cross-checked by something that only runs on the box, the pair has no local test by definition — ask what ELSE reads this key before calling a change two lines.** It was three files. The fixture pair is now a unit test, verified by running it against the breaking commit. 15th occurrence 2026-08-25 — the rule extends past mechanisms to OPTIONS, PRICES and QUOTAS: llm-distillery#103 chose an oracle for nine days by comparing against "Gemini Batch ~$0.0018", a rate card with NO CALL SITE — both paths call `models.generate_content`, and `.batches` appears in no `.py` file, so the cheaper option was never an option and the conclusion was backwards. Both vendors' rates were read first-hand and an outside contributor checked the arithmetic; nobody grepped for the caller, because a price does not look like a mechanism. **Being able to pay a price is a property of your code, not of the vendor. Before comparing against an option, name the function that would invoke it.** 14th occurrence 2026-08-16 — I CLAIMED A MECHANISM I NEVER STARTED**: reported "watcher armed for the 08:02 delivery" in a session summary having launched nothing. The sentence had been true for the three previous deliveries and was written a fourth time from habit rather than from a launch. Caught only because the owner mentioned the time; `ps` settled it in three seconds. **How it fails is the reusable part: silently** — no notification, no error, just no fourth measurement, and the likely outcome was reporting "three clean and a fourth pending" indefinitely. ⭐ Committed on the same day as, and in the report about, a night spent cataloguing declared-but-uninvoked mechanisms. 13th occurrence 2026-08-15 — a STAMP THAT TURNS OFF ITS OWN CHECKER**: `CLAUDE.md`'s framework stamp was bumped to v1.26.0 on 2026-08-13 before either release was triaged, and the stamp is `/update-drift`'s only input — so every later run reported "current" and examined nothing. Two releases sat unreviewed, one carrying an explicit adopter action. **A stale stamp is safe; a premature one is the only value that can silence its own check.** Now probed, seeded against the real disagreement (frontmatter v1.25.0 vs footer v1.26.0) before being believed. 12th occurrence 2026-08-15 — a GATE THAT TRACKS AN EVENT INSTEAD OF A PROPERTY**: FluxusSource's `7bc20a0` was gated "not for deploy until NexusMind's envelope declaration merges." It merged, so the gate reads green — while three `content_meta` shape mismatches stand, one of which fails validation closed. **A gate written as "wait for X to merge" tracks whether X happened, never whether the two shapes agree.** 11th occurrence 2026-08-15 — the MEASUREMENT form: I reported "0 non-canonical across all three timestamp fields" as outcome proof when **two of the three had 0 rows present**; the check counted violations and never presence, so absent and clean produced identical output. **A check that examines nothing reports success.** 10th occurrence 2026-08-12 — a twelve-line `<!-- verify: -->` annotation that could never be extracted, so a claim that had already regressed once went unchecked; 9th 2026-08-11 afternoon — six self-inflicted.)* **An annotation, a test and a check are mechanisms too** — "the file has a verify comment" is a config key, not an outcome. **Naming the caller is not sufficient.** Guards have shipped with *correct callers on the right paths* and still done nothing — one reverted downstream by a `COALESCE` merge, one short-circuited by an earlier commit point. Both passed unit tests on the predicate; a green test on the predicate proves only the predicate. If a guard's whole value is that it changes an outcome, **run it and print the resulting state**, and ask "is this the only writer of this field?" — not just "is my code reached?". **Never infer runtime behaviour from the presence of a config key.** Three smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end; a field initialised to `None` and populated somewhere you have not read; and **a feature validated on "production data" without naming WHICH STAGE** (the arXiv announce prefix is a 91.6% detector at collection and **0.000** after enrichment — both are production data). Two related traps: **a comment explaining why code is safe is a claim like any other**, and **if a criterion depends on "now", encode the criterion, never its answer**. → The catalogue of occurrences (NM#284, #94, NM#281, NM#300, cd v6) is in `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first (2026-08-12).** A `stage1_low` row's persisted score is an **e5 probe estimate** (ADR-006 hybrid inference), not a Gemma score. Measured: re-scoring 300 production rows on a production-parity box reproduced `stage2` rows **231/231 within 0.16 at median \|Δ\| 0.0000**, and **every** disagreement above 0.16 was a `stage1_low` row — 23% of rows. Mixing the two silently blends a probe distribution into a model-score distribution. This is the same shape as the length-field trap: the field exists, is populated, and means different things per row.
- **A CONTRACT TERM IS NOT EVIDENCE THAT IT BINDS AT EVERY CONSUMER — establish the precondition per consumer.** *(2026-08-16, llm-distillery#119.)* I put an ordering clause into a cross-repo contract on the strength of a four-cycle simulation at **one** consumer, and relayed it to the others as settled. It is necessary at NexusMind, which **re-reads the whole of `data/raw` every run** and therefore manufactures the stale-after-fresh sequence the clause exists to stop. It may be **cargo at ovr**, which reads filtered output written once per cycle and has run a bare hash-differs test at *four production sites* with no recorded thrashing. ⛔ **A term derived from one consumer's mechanics, stated in the contract, reads to every other consumer as a requirement with evidence behind it.** Name which consumer's mechanics produced a term, and let the others measure their own precondition rather than adopt it. *(Cost of the same session's related error: I described a cache from its **write** sites without reading where it is **consulted**, and reported a defect in a cache that already behaved correctly.)*
- **An issue that holds a FUTURE observation must never be referenced with `Closes`/`Fixes` by the PR that implements it.** *(2026-08-16, NexusMind NM#388.)* The two intentions contradict each other and **the merge resolves it toward closure, silently**: a dated watch was written correctly, cross-referenced in three places, and then closed by the `Closes #388` in the body of the PR whose evidence it was designed to receive. ⛔ **And the second carrier was equally dead** — the `docs/hypothesis-log.md` entry carried the date only inside its *Method* prose, with no `Review by:` field, which is the field `/curate` Step 0.6 actually sweeps. **Correct, fully written, cross-referenced, and reachable by nothing.** Both fixed and *verified* rather than asserted (`gh issue view --json state` → OPEN; `grep -c "Review by: 2026-08-23"` → 1). **A dated check needs a home that is OPEN on the date and a field that something sweeps** — being written down in three places is not the same as being surfaced in one.
- **A wrong-object read that returns a PLAUSIBLE number goes straight through — surprise is not a defence you can rely on.** *(2026-08-16.)* An ad-hoc reader reported `content_length 0/2265` against the canonical checker's `2265/2265`, because the field lives at `nexus_mind_attributes.<lens>.content_length` and not at top level. It was caught **only because zero was surprising enough to distrust**, not by any process — had the wrong path returned a believable figure it would have been filed as a measurement. ⭐ Sibling framing from the same day: **self-review found nothing at all.** Eleven-odd defects across four sessions were caught by another session re-deriving; the two apparent exceptions were authors *going to look at state they had just changed*, which is re-derivation with a shorter loop, not review. **Re-derive, or have someone else re-derive. Reading your own work again is not a control.**
- **A pointer row is capped at 250 chars, and a new lesson goes in the file the row
  points at.** *(#133, owner decision 2026-08-27.)* `CLAUDE.md` refilled at **~486
  bytes/day** — 35,094 → 39,955 between 2026-08-16 and 08-26, measured over 25 commits —
  while every `/audit-context` trimmed it back to the wall. ⛔ **The audit-time headroom
  figure is what hid this**: two audits both reporting ~45 bytes free describe a file that
  grew by whatever the trim removed, not one that did not grow. **A quantity sampled only
  when it is reset cannot show a trend, and it reads as stability.** A byte budget loses
  that race by construction; a per-row cap makes the table unable to grow at all.
  ⭐ **The stronger argument is not size — it is rot.** All three stale claims found on
  2026-08-27 were in the always-loaded layer and each restated a number living elsewhere
  ("109 owned fields" when the generated register said 125; "the filters were never
  assessed" three weeks after they were; a spec headed "NOT yet deployed" three days after
  going live). The table is the surface that goes stale *because* it restates.
  ⚠️ **The carve-out is the honest part of the rule, not a loophole:** a pointer does not
  fire without opening its target, so a prohibition that prevents SPENDING MONEY or
  PUBLISHING A WRONG NUMBER loses its whole value as a pointer. Four rows may reach 400.
  The exemption is bounded and checked three ways — count (≤5), ceiling (400), and
  **staleness**: a carve-out matching no row fails, because a dead exemption hides growth.
  ⛔ A missing table header is **CANNOT VERIFY, never a pass** — renaming it would
  otherwise retire the check while reporting success.
  → `python3 scripts/verification/check_index_budget.py --target pointers`;
  `tests/unit/test_pointer_row_cap.py` (11 cases, each seeding the failure it claims).

  ⛔ **AND NO GUARD MAY LIVE INSIDE `CLAUDE.md`.** *(2026-08-29, llm-distillery#138.)*
  Four `<!-- verify: -->` shell one-liners sat in the file, checking claims it
  restates from `memory/working-rules.md` and `memory/filter-status.md`. They
  measured **2,047 bytes — 5.5% of a file that was 2,555 bytes from its 40,000-byte
  wall**: the guards were spending the budget they policed, and each one made the
  next trim harder. The same argument had already moved `check_index_budget.py` out
  of `memory/MEMORY.md` on 2026-08-17, when adding a stage inline would have
  tripped the guard on landing — **it just took two weeks to notice the argument
  applied one file over.** A new claim check on `CLAUDE.md` is now a function in
  `scripts/verification/check_doc_claims.py` plus a row in its `CHECKS`,
  annotated from `memory/MEMORY.md`. ⚠️ Note what these checks are worth: they
  prove two layers AGREE, never that either is true — a consolation prize for a
  restatement nobody has removed yet.
  → `python3 scripts/verification/check_doc_claims.py`;
  `tests/unit/test_doc_claims.py` (17 cases; `test_no_verify_block_has_crept_back_into_claude_md`
  is the one that stops the reversal).

- **Before using any source as evidence, establish what it excludes.** *(⚠️ **18th occurrence 2026-09-04 — THE SOURCE WAS `git add`, AND ITS SILENCE WAS THE WHOLE DEFECT.** `.gitignore` carries `*_test.*` in a scratch-file block beside `*.bak` and `*_backup.*`. It is a PATTERN, not a path, so it matched `docs/evidence/2026-09-04-v8-probe-calibration/probe_recall_report_test.json` — the SOLE source for every test-split number published in that directory's README, in `filters/human_thriving/v8/calibration_report.md` and in EXP-016. `git add <dir>` omitted it with **no message, no warning, exit 0**, while its `_val` and `_test_seed7` siblings staged normally, so the loss was invisible from every angle a committer looks at. ⭐ **What made it findable was asking a DIFFERENT question**: not "did the add succeed?" but "what is in the staged set?" — `git add -n` listed 13 files where the directory held 14. Blast radius then measured (`git status --porcelain --ignored | grep '_test\.'`): exactly two untracked files repo-wide, that JSON and `filters/common/obituary_detector/validation/panel_obit_test.py`, a junk-gate validation script that has never been in git and whose every sibling is tracked. Fixed with a `docs/evidence/**` negation, verified in both directions (the JSON stageable; `scripts/foo_test.py` still ignored). ⛔ **The rescue is scoped to `docs/evidence/` only** — the pattern still swallows `*_test.*` anywhere else in the repo. ⚠️ Found by `/review-changes`, not by me, and not by 623 green tests or any guard. 17th 2026-09-03 — TWICE IN ONE HOUR, AND THE FIRST WAS A FIELD THAT LIES BY NAME.** (a) `b650-gpu:~/v8_corpus/pool_v2.jsonl` carries a `harm_title` field. It is **not** the class-A instrument: the reduce pass runs on a host that cannot import the filters package, so it stores a fallback hand lexicon, and `draw_v8_corpus.py` **recomputes** the flag with `filters/uplifting/v7/prefilter.py`'s `crime_violence` patterns before sampling — in memory, never written back. Reading the stored field gave **660** above-op class-A rows where the census instrument gives **59**; I was one step from reporting that Phase B2 had ~600 rows of headroom when it has **12**. ⛔ **Neither flag is a superset** — agree 32, stored-only 628, census-only 27 — so it is not even a conservative over-count. The function that recomputes it carries a docstring saying all of this, and the manifest records which instrument ran. ⭐ *A field name is an assertion*, and a pipeline that corrects a field in memory leaves the wrong value on disk for the next reader. (b) The same hour, counting the Syria-removal cluster by an **English title regex** returned 14 rows / 8 above-op; matching the oracle's own `dominant_subject` — which is written in English whatever the article's language — returns **15 / 9**. ⭐ In a multilingual corpus the ORACLE'S OWN SUMMARY is a language-independent matching surface that the title is not. Records: `docs/evidence/2026-09-03-phase-b2-headroom/`, `docs/evidence/2026-09-03-classA-supplement-adjudication/`.)* *(⚠️ **16th occurrence 2026-09-01 — I GLOBBED FOR THE WRONG FILE TYPE AND NEARLY WROTE OFF A BLOCKING GATE'S INPUTS.** Searching for the full text behind 18 adverse rows held only as 300-char excerpts, I globbed `**/*.jsonl*` across the archive directories — which hold `.tar.gz` — and got `RECOVERABLE: 0 of 18`. A negative from an instrument pointed where it could not produce a positive, and it agreed with a premise already written into llm-distillery#127's thread and the 2026-08-30 rulings: *"their windows have rolled — unrecoverable"*. **18 of 18 were in fact recoverable**, 15 of them from `nexusmind_2026-08.tar.gz`. ⛔ **And the near-miss twin: the FluxusSource archive DOES hold those ids and returns a STUB** — producer bytes, 447/133/441 chars where the enriched originals are 14,546/2,917/3,652. So one wrong archive answers *nothing found* and the other answers *found, and it is short*, and only the second looks like success. ⭐ **"Is it archived?" has a different answer per archive; name which one before believing either.** Records: `docs/evidence/2026-09-01-phase-b-labels/`, `scripts/dataset/rehydrate_adverse.py`.)* *(⚠️ **15th occurrence 2026-08-30 — OPPOSITE SIGN AGAIN, AND THE SMALLEST INSTANCE YET: the source contained a row that is not a member of the population, and the population was never enumerated.** `b650-gpu:~/v8_corpus/pool_v2.jsonl`'s first line is a `__provenance__` record; a probe script counted every line and its output was then described as "rows". **177,593 published against a true 177,592**, in seven documents, a commit message and a report to the owner. ⛔ The correct figure was already committed one file away — `experiments/registry.jsonl` records `drawable: 177592` — and nothing compares a fresh number against the stored one. ⭐ The generalisable form: **a metadata file whose first line is not a datum is off by exactly one, and one is the error size nobody notices** — it survives every plausibility check because it IS plausible. Found by `/review-changes`, not by any of the 493 tests, 3 mutations or 5 guards that had passed. Records: `docs/evidence/2026-08-30-v8-no-regression-replacement/`, commit `45890c1`.)* *(⚠️ **14th occurrence 2026-08-29 — THE OPERAND LIST IS PART OF THE SOURCE: a wrong rule was corrected on nine repo surfaces and announced as finished; it was still live in `~/.claude/projects/.../memory/`, which loads into every session for this project. Every grep, including the one that found four sites "by grep rather than recall", was rooted at the repo. The always-loaded layer spans TWO trees.** ⚠️ **13th occurrence 2026-08-28 (evening) — THE MIRROR: AN INSTRUMENT THAT COULD NOT PRODUCE A NEGATIVE, SO THE POSITIVE CARRIED NO INFORMATION.** Measuring whether moving the article to the end of the `human_thriving v8` prompt recovers prefix caching, the control run reported a **99.4% cache hit** — on the *unmoved* prompt, which has a 1.5% ceiling. It re-sent the **same 30 articles**, so the whole prompt matched rather than the shared prefix: that population cannot return a low cache rate whatever the truth is. Every previous occurrence here is a *negative* that carried no information; this is the same root with the sign flipped, and it is the more seductive half — a number that confirms what you hoped, arithmetically correct, about a question nobody asked. ⭐ **A cache rate is a property of a RUN. Before believing it, ask what varied BETWEEN the requests** — the sibling of asking what a source excludes. Caught before it was quoted, and recorded as unquotable in three places rather than deleted, because a deleted number gets re-derived. ⚠️ **12th occurrence 2026-08-28 — THE SOURCE INCLUDED WHAT THE ANALYSIS FORBIDS, which is the same failure wearing the opposite sign.** All five v8 Gate 0 corpus targets were measured over a production census that includes `news.google.com` — 22.1% of rows — while the same plan says in bold that GN is excluded from every draw. The yardstick described a population no draw can sample from; every target moved once it was corrected (base rate 7.74%→9.76%, p10 length 84→235 chars, sub-300-char share 30.8%→11.9%). **The rule and the figures sat three paragraphs apart in one document, each individually correct.** A stated exclusion does not reach a number unless someone carries it there. ⚠️ 11th occurrence 2026-08-27 — **I BUILT THE EXCLUDING SOURCE MYSELF.** `git archive HEAD` into a temp tree, as a before/after baseline for the reference checker: it ships TRACKED files only, so every gitignored path was absent and the run reported **240 findings against the real 1**. For a minute that read as a catastrophic regression in my own edit. **The baseline was not a worse version of the tree, it was a different tree.** Same shape as the 2026-08-24 keeper (*the shipped artifact exited 1 on a clean clone*) approached from the other side — there the gitignored evidence was missing from someone else's clone; here I manufactured the clone. ⚠️ The cheap copy tricks fail too: `cp -al` cannot hardlink across filesystems, and a `|| cp -a` fallback copies the repo INTO the half-made directory. 10th occurrence 2026-08-26 — A SOURCE THAT EXCLUDED ITS OWN TAIL, AND THE EXCLUDED PART WAS WHAT THE LOADED PART PROMISED.** The Claude Code auto-memory `MEMORY.md` declared at offset 164 that two ⛔ NO REPO FILE entries *"must not be trimmed: they are the only surviving record"*. The file was 26,645 bytes against a 24.4KB load limit, and both entries sat at offsets **24,905 and 25,445** — past the cut. **The guarantee loaded; the thing it guaranteed did not.** No instrument could have reported it: the notice and its subject were on opposite sides of the truncation, so reading the file as loaded shows a well-guarded index. ⭐ **A protection marker is a claim about the rest of the world — that no other copy exists — and it ages like any other state claim while reading as an instruction.** All seven of its claims had in fact been written into topic files, and its one unique atom had landed as a commit. **Before honouring OR removing such a marker, verify what it protects still needs protecting.** ⛔ Worse than stale: **full session files for both dates sat in the marker's OWN DIRECTORY** (14,194 and 9,502 bytes, sixty lines below it). The marker's literal words — NO REPO FILE — were true and irrelevant, and **a `ls` of its own directory refuted it.** Nobody ran one, because it read as an instruction. 9th occurrence 2026-08-23 — `datasets/adverse/*.jsonl` stores a 300-char EXCERPT, not the article. Every one of the 18 rows. Originals run 620–28,905 chars, and a two-oracle paid run against ledes-not-articles was one command away; the class-A test turns on the DOMINANT SUBJECT, which a lede cannot carry. Hydrate from `ovr.db`'s `articles` table. Caught before the spend, not after.**; **8th occurrence 2026-08-16 — a WINDOW is part of a source, and mine was the same length as the mechanism's period.** I bounded llm-distillery#119's reader exposure at "0 observed" over 50 retained collections spanning ~8 days. The mechanism that produces the class is eviction from a seen-URL store whose effective window is **~7.7 days** — so a repeat that requires straddling eviction had essentially no room to appear, and **that population must return 0 whatever the truth is.** Published in a public issue before it was checked; caught by the producer session, not by me. ⭐ The tell I missed: the zero was *satisfying*, and it arrived from a corpus I had not asked what it spans. Sibling error the same day: quoting a count off `ovr.db live_articles`, a legacy view off the build path — **two exclusions, one temporal and one structural, in one afternoon.** 7th occurrence 2026-08-12 afternoon — concluding an ABSENCE from a structure whose shape I had not established: I read `analysis.pre_enriched` over 1,070,665 rows, got 0, and nearly reported a dead stamp. The flags are at `nexus_mind_attributes/<lens>/pre_enriched`. **A wrong path and a dead field both read as zero, and the wrong one is the more exciting finding** — dump the keys that ARE there before reporting an absence. 6th occurrence 2026-08-11 afternoon — a PEER asserted a population claim from a doc whose caveat section they had read that same session and not re-read; verifying against their source rather than their report surfaced two further exclusions. 5th 2026-08-11 midday — see below; 4th 2026-08-09 — and this one was a **machine**, not a file.* I inventoried b650-gpu, found no judge verdicts, and reported the precision panel as UNADJUDICATED, blocking a whole track. The verdicts existed and had for three days: they live in the NexusMind checkout under `data/research/precision_panel*/`, which `.gitignore:230` excludes, so they were never copied to the GPU box. **A host is a source with an exclusion list too** — "I looked on the machine where the work was done" is the same error as "I read the file that only holds passers".*)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer. ⭐ **ONE ROOT, and it covers the INSTRUMENT as well as the source: THE INSTRUMENT WAS POINTED SOMEWHERE THAT CANNOT PRODUCE A POSITIVE, SO THE NEGATIVE CARRIED NO INFORMATION.** Found in three repos in three media on 2026-08-16 — a corpus shorter than the mechanism's period (the #119 case above), a validator run over 0 rows, and a grep over 0 files. A fourth, 2026-08-16, is the cleanest specimen because the number was never in doubt: measuring llm-distillery#121 (opinion/editorial surfacing), `nature_recovery` came back null with **68 of 92 within-source strata tied at 0 vs 0** — that lens surfaces 365 of 229,588 rows (0.16%), so at n≈10-30 per stratum most strata cannot produce a positive in *either* arm. The null was arithmetically correct and evidentially empty. **Before believing a negative, prove the instrument could have said yes.** ⚠️ **Second clause, because all of the above is only the broken-instrument half:** an instrument can be sound, its number *correct*, and still not be a function of the thing under test — a before/after whose baseline rests on an invariant the change does not touch. Nothing a reader checks comes back wrong. **Also ask what would have made the "before" different.**
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.

- **A PIPELINE WHOSE LAST STAGE IS A FORMATTER LAUNDERS THE EXIT STATUS OF THE THING
  YOU ARE TESTING.** *(**2nd occurrence 2026-08-29**, and the second was by the session
  that wrote the first, one screen below it.)* `cmd | tail -4; echo $?` reports `tail`'s
  status, and `tail` succeeds whatever it is fed: four verification guards were recorded
  `exit=0` while one of them was printing `FAIL:` — which `tail -4` had also cut off, so
  the truncation and the status error hid the same defect from two directions. Later the
  same day, `run_verify_annotations.py | tail -2; echo $?` read 0 from a run whose true
  status was **1**. The sibling shape is a `| grep` in an annotation, which discarded a
  script's `return 1` and made the assertion permanently unreachable. `tail`, `head`,
  `cut`, `sort`, `grep` are all formatters. **Capture then inspect — `out=$(cmd 2>&1);
  rc=$?` — or read `${PIPESTATUS[0]}`.** ⭐ **The tell is that the pipe looks like
  FORMATTING, not like TESTING**, which is exactly when the laundering is invisible; the
  pgrep rule below is the same imperative for a different instrument.

- **MENTION IS NOT USE, AND EVERY TEXT-MATCHING INSTRUMENT HERE CONFUSES THEM.**
  *(**3rd occurrence 2026-08-29**, all three inside ONE session, on three different
  matchers — and the third was inside the guard written after the second.)*
  A document that *quotes* a token in order to explain it is indistinguishable, to a
  matcher, from one that *uses* it. `run_verify_annotations.py` counted **10** prose
  mentions of `<!-- verify: -->` as annotations — eight in `memory/gotcha-log.md`, which
  discusses them — inflating the reported denominator of checked claims by **18%**, in the
  one report whose job is to say how much is checked. `/curate`'s path extractor reported
  **2** dead references, both being records that quoted a wrong path (`ovr.news/BRAND.md`)
  or asserted a file's deliberate absence. ⛔ **The two failure directions are different and
  both matter**: an inflated denominator makes coverage look better than it is, and a
  permanent false positive trains the reader to skim the section where a real finding would
  appear. **Fix at the instrument where you can** — an empty match body is not an
  annotation, and it is counted and named rather than dropped, because an *unfilled*
  annotation is a real defect. **Fix at the document where you cannot** — italics rather
  than backticks, and say where the real file is. ⛔ **The third is the one to remember**:
  a new check for the always-loaded oracle command matched the bare dotted path
  `ground_truth.batch_scorer` anywhere in `CLAUDE.md` and stopped at the first hit — a
  Hard Constraint reading *"the floor lives in `ground_truth.batch_scorer.make_oracle_prefilter`"*,
  200 lines above the command — **and reported the file it had just fixed as broken.**
  Match the INVOCATION (`python -m …`), never the identifier. ⭐ **Writing the rule down
  did not stop me writing the bug forty minutes later**, which is the whole content of
  *articulating is not applying*: the guard against a defect is where you are least
  suspicious, because you have just proved you understand it.

- **`pgrep -f "<pattern>"` cannot answer "is it running?" — and `pkill -f` cannot stop it.** *(**6th occurrence 2026-08-26, and it is this rule's own recommended remedy failing**: `systemctl is-active nexusmind.service` read `inactive` and the box was NOT idle — cleanup is a **separate unit** (`nexusmind-cleanup.service`, chained by `OnSuccess=`, running `scripts/main.py --cleanup-only` in its own cgroup) and it stayed `activating` another 8 minutes, executing the exact code path the deploy was about to replace. ⭐ **The service manager answers for the unit you NAME, and a chained unit is a different name.** Enumerate first — `systemctl list-units 'nexusmind*' --all` — then ask all of them; `OnSuccess=`/`Requires=`/`PartOf=` are part of what "is it running?" means. The chain was already recorded in `reference-sadalsuud-pipeline-chain` and I still queried one unit: **a documented mechanism you do not query is not a mechanism you have.** **5th occurrence 2026-08-25**: a wait-loop `until ! ps -eo args | grep -q "[m]ain.py"` never exited — the bracket trick protected the grep from itself, but the loop's own `echo "no main.py process running"` put the literal pattern on its command line, so **the watcher matched itself and waited forever**. Cost: a deploy held ~20 minutes after the box had gone idle, and three polls that reported a process which was my own waiter. The tell was there in the output the whole time — the matching line said `bash -c until`. ⭐ **PRINT THE MATCHING LINE. A count cannot show you that the match is you.** 4th occurrence 2026-08-21: `pkill -f -- "-L 11435:…"` matched and killed the invoking bash, which exited 144 and skipped the rest of the script. Kill by PID from `ps`, or kill on the far side of the ssh.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

