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

*(Recurrences 2026-08-15 and 2026-08-16, two each: moved verbatim to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *HAND-BUILT POPULATION*.)*

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

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — and then prove the outcome changed at the END of the run.** *(**Count: 21st occurrence, 2026-09-07.** The 17th–21st stories, 2026-09-04 → 2026-09-07: moved verbatim 2026-10-12 to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *name the caller — September stories*.)* *(Occurrences 9–16, 2026-08-11 → 2026-08-25: moved verbatim to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *name the caller*.)* **An annotation, a test and a check are mechanisms too** — "the file has a verify comment" is a config key, not an outcome. **Naming the caller is not sufficient.** Guards have shipped with *correct callers on the right paths* and still done nothing — one reverted downstream by a `COALESCE` merge, one short-circuited by an earlier commit point. Both passed unit tests on the predicate; a green test on the predicate proves only the predicate. If a guard's whole value is that it changes an outcome, **run it and print the resulting state**, and ask "is this the only writer of this field?" — not just "is my code reached?". **Never infer runtime behaviour from the presence of a config key.** Three smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end; a field initialised to `None` and populated somewhere you have not read; and **a feature validated on "production data" without naming WHICH STAGE** (the arXiv announce prefix is a 91.6% detector at collection and **0.000** after enrichment — both are production data). Two related traps: **a comment explaining why code is safe is a claim like any other**, and **if a criterion depends on "now", encode the criterion, never its answer**. → The catalogue of occurrences (NM#284, #94, NM#281, NM#300, cd v6) is in `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first (2026-08-12).** A `stage1_low` row's persisted score is an **e5 probe estimate** (ADR-006 hybrid inference), not a Gemma score. Measured: re-scoring 300 production rows on a production-parity box reproduced `stage2` rows **231/231 within 0.16 at median \|Δ\| 0.0000**, and **every** disagreement above 0.16 was a `stage1_low` row — 23% of rows. Mixing the two silently blends a probe distribution into a model-score distribution. This is the same shape as the length-field trap: the field exists, is populated, and means different things per row.
- **A CONTRACT TERM IS NOT EVIDENCE THAT IT BINDS AT EVERY CONSUMER — establish the precondition per consumer.** *(2026-08-16, llm-distillery#119.)* I put an ordering clause into a cross-repo contract on the strength of a four-cycle simulation at **one** consumer, and relayed it to the others as settled. It is necessary at NexusMind, which **re-reads the whole of `data/raw` every run** and therefore manufactures the stale-after-fresh sequence the clause exists to stop. It may be **cargo at ovr**, which reads filtered output written once per cycle and has run a bare hash-differs test at *four production sites* with no recorded thrashing. ⛔ **A term derived from one consumer's mechanics, stated in the contract, reads to every other consumer as a requirement with evidence behind it.** Name which consumer's mechanics produced a term, and let the others measure their own precondition rather than adopt it. *(Cost of the same session's related error: I described a cache from its **write** sites without reading where it is **consulted**, and reported a defect in a cache that already behaved correctly.)*
- **An issue that holds a FUTURE observation must never be referenced with `Closes`/`Fixes` by the PR that implements it.** *(2026-08-16, NexusMind NM#388.)* The two intentions contradict each other and **the merge resolves it toward closure, silently**: a dated watch was written correctly, cross-referenced in three places, and then closed by the `Closes #388` in the body of the PR whose evidence it was designed to receive. ⛔ **And the second carrier was equally dead** — the `docs/hypothesis-log.md` entry carried the date only inside its *Method* prose, with no `Review by:` field, which is the field `/curate` Step 0 sub-step 5 actually sweeps. **Correct, fully written, cross-referenced, and reachable by nothing.** Both fixed and *verified* rather than asserted (`gh issue view --json state` → OPEN; `grep -c "Review by: 2026-08-23"` → 1). **A dated check needs a home that is OPEN on the date and a field that something sweeps** — being written down in three places is not the same as being surfaced in one.
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

- **Before using any source as evidence, establish what it excludes.** *(**Count: 25th occurrence, 2026-09-26.** The 16th and 18th–25th stories, 2026-09-01 → 2026-09-26: moved verbatim 2026-10-12 to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *establish what it excludes — September stories*.)* *(Occurrences 4–15, 2026-08-09 → 2026-08-30: moved verbatim to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *establish what it excludes*.)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer. ⭐ **ONE ROOT, and it covers the INSTRUMENT as well as the source: THE INSTRUMENT WAS POINTED SOMEWHERE THAT CANNOT PRODUCE A POSITIVE, SO THE NEGATIVE CARRIED NO INFORMATION.** Found in three repos in three media on 2026-08-16 — a corpus shorter than the mechanism's period (the #119 case above), a validator run over 0 rows, and a grep over 0 files. A fourth, 2026-08-16, is the cleanest specimen because the number was never in doubt: measuring llm-distillery#121 (opinion/editorial surfacing), `nature_recovery` came back null with **68 of 92 within-source strata tied at 0 vs 0** — that lens surfaces 365 of 229,588 rows (0.16%), so at n≈10-30 per stratum most strata cannot produce a positive in *either* arm. The null was arithmetically correct and evidentially empty. **Before believing a negative, prove the instrument could have said yes.** ⚠️ **Second clause, because all of the above is only the broken-instrument half:** an instrument can be sound, its number *correct*, and still not be a function of the thing under test — a before/after whose baseline rests on an invariant the change does not touch. Nothing a reader checks comes back wrong. **Also ask what would have made the "before" different.**
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.

- **A PIPELINE WHOSE LAST STAGE IS A FORMATTER LAUNDERS THE EXIT STATUS OF THE THING
  YOU ARE TESTING.** *(**3rd occurrence 2026-09-05**, during `/curate`, in the same
  minute this rule's own text was on screen — a grep had just printed it. Ran
  `run_verify_annotations.py 2>&1 | tail -2; echo "exit=$?"` and reported `exit=0`,
  which is `tail`'s. True status was also 0, so the figure was right **by luck**;
  ⭐ *articulating the rule is not applying it*, and the gap was seconds. Previously
  **2nd occurrence 2026-08-29**, and that second was by the session
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
  *(⛔ **5th occurrence 2026-09-05 (third session) — TWICE IN ONE FILE, AND THE FIRST
  VIOLATION WAS THE DECLARATION EXPLAINING THE RULE.** `check_design_weights` asks whether
  an analysis reads `inclusion_probability`. **4th:** a substring test, and the first
  `# design-weights:` declaration written under it explained the gap by *naming* the field —
  so the check read the confession as compliance, and passed. **5th:** excluding docstrings
  fixed that instance and not the question; a review then deleted the **only** real weight
  read from `phase_c_outcome.py` and the check still PASSED, because the field's name
  survived in an error message and a JSON label — while this file's docstring claimed
  *mention is not use* was fixed and a unit test claimed to pin it. ⭐ **The generalisable
  part is the SHAPE OF THE FIX, not the matcher: each version answered "does this file
  contain the string" one shape more narrowly, rather than switching to "does it USE it".**
  A fix applied to one shape of a problem and named after all of them reads as complete.
  Now three AST shapes — a `Subscript` constant key, or a constant-string call argument
  (an f-string is a `JoinedStr`, so an interpolated error message does not count) — with the
  false-FAIL direction disclosed and safe. ⛔ **This rule was in `CLAUDE.md`'s always-loaded
  layer and in this file throughout, and was violated twice anyway; the promotion has not
  taken.** Records: `EXP-025`, commit `347a239`, `scripts/verification/check_claim_shapes.py`,
  `tests/unit/test_claim_shapes.py`.)* *(**3rd occurrence 2026-08-29**, all three inside ONE
  session, on three different matchers — and the third was inside the guard written after the
  second.)*
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

- **`pgrep -f "<pattern>"` cannot answer "is it running?" — and `pkill -f` cannot stop it.** *(**Count: 8th occurrence, 2026-09-05.** The 7th and 8th stories: moved verbatim 2026-10-12 to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *pgrep / pkill — September stories*.)* *(Occurrences 4–6, 2026-08-21 → 2026-08-26: moved verbatim to [`archive/working-rules-archive.md`](archive/working-rules-archive.md) § *pgrep / pkill*. ⭐ Enforced since 2026-10-09 by `scripts/hooks/block_pattern_kill.py`, a PreToolUse hook.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

