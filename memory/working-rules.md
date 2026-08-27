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

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — and then prove the outcome changed at the END of the run.** *(⚠️ **16th occurrence 2026-08-25 — a CONFIG CHANGE WHOSE FIRST EXERCISE WAS PRODUCTION.** `investment_risk` was paused (two config lines, owner ruling), deployed at 17:26 with a green suite and a written decision record, and nobody watched a service start. At 20:09:54 `nexusmind.service` failed on a fail-closed deploy gate — `deploy/smoke_test_articles.jsonl` still named the paused filter — and the entire 20:03 cycle was lost. The outcome check that existed (block-ledger `placements` 6 → 5) was correctly identified in advance and **deferred to the very cycle that then never ran**, so the plan contained its own gap. ⭐ **A scheduled service turns "deploy and wait" into "let production be the test." If a config key is cross-checked by something that only runs on the box, the pair has no local test by definition — ask what ELSE reads this key before calling a change two lines.** It was three files. The fixture pair is now a unit test, verified by running it against the breaking commit. 15th occurrence 2026-08-25 — the rule extends past mechanisms to OPTIONS, PRICES and QUOTAS: llm-distillery#103 chose an oracle for nine days by comparing against "Gemini Batch ~$0.0018", a rate card with NO CALL SITE — both paths call `models.generate_content`, and `.batches` appears in no `.py` file, so the cheaper option was never an option and the conclusion was backwards. Both vendors' rates were read first-hand and an outside contributor checked the arithmetic; nobody grepped for the caller, because a price does not look like a mechanism. **Being able to pay a price is a property of your code, not of the vendor. Before comparing against an option, name the function that would invoke it.** 14th occurrence 2026-08-16 — I CLAIMED A MECHANISM I NEVER STARTED**: reported "watcher armed for the 08:02 delivery" in a session summary having launched nothing. The sentence had been true for the three previous deliveries and was written a fourth time from habit rather than from a launch. Caught only because the owner mentioned the time; `ps` settled it in three seconds. **How it fails is the reusable part: silently** — no notification, no error, just no fourth measurement, and the likely outcome was reporting "three clean and a fourth pending" indefinitely. ⭐ Committed on the same day as, and in the report about, a night spent cataloguing declared-but-uninvoked mechanisms. 13th occurrence 2026-08-15 — a STAMP THAT TURNS OFF ITS OWN CHECKER**: `CLAUDE.md`'s framework stamp was bumped to v1.26.0 on 2026-08-13 before either release was triaged, and the stamp is `/update-drift`'s only input — so every later run reported "current" and examined nothing. Two releases sat unreviewed, one carrying an explicit adopter action. **A stale stamp is safe; a premature one is the only value that can silence its own check.** Now probed, seeded against the real disagreement (frontmatter v1.25.0 vs footer v1.26.0) before being believed. 12th occurrence 2026-08-15 — a GATE THAT TRACKS AN EVENT INSTEAD OF A PROPERTY**: FluxusSource's `7bc20a0` was gated "not for deploy until NexusMind's envelope declaration merges." It merged, so the gate reads green — while three `content_meta` shape mismatches stand, one of which fails validation closed. **A gate written as "wait for X to merge" tracks whether X happened, never whether the two shapes agree.** 11th occurrence 2026-08-15 — the MEASUREMENT form: I reported "0 non-canonical across all three timestamp fields" as outcome proof when **two of the three had 0 rows present**; the check counted violations and never presence, so absent and clean produced identical output. **A check that examines nothing reports success.** 10th occurrence 2026-08-12 — a twelve-line `<!-- verify: -->` annotation that could never be extracted, so a claim that had already regressed once went unchecked; 9th 2026-08-11 afternoon — six self-inflicted.)* **An annotation, a test and a check are mechanisms too** — "the file has a verify comment" is a config key, not an outcome. **Naming the caller is not sufficient.** Guards have shipped with *correct callers on the right paths* and still done nothing — one reverted downstream by a `COALESCE` merge, one short-circuited by an earlier commit point. Both passed unit tests on the predicate; a green test on the predicate proves only the predicate. If a guard's whole value is that it changes an outcome, **run it and print the resulting state**, and ask "is this the only writer of this field?" — not just "is my code reached?". **Never infer runtime behaviour from the presence of a config key.** Three smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end; a field initialised to `None` and populated somewhere you have not read; and **a feature validated on "production data" without naming WHICH STAGE** (the arXiv announce prefix is a 91.6% detector at collection and **0.000** after enrichment — both are production data). Two related traps: **a comment explaining why code is safe is a claim like any other**, and **if a criterion depends on "now", encode the criterion, never its answer**. → The catalogue of occurrences (NM#284, #94, NM#281, NM#300, cd v6) is in `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first (2026-08-12).** A `stage1_low` row's persisted score is an **e5 probe estimate** (ADR-006 hybrid inference), not a Gemma score. Measured: re-scoring 300 production rows on a production-parity box reproduced `stage2` rows **231/231 within 0.16 at median \|Δ\| 0.0000**, and **every** disagreement above 0.16 was a `stage1_low` row — 23% of rows. Mixing the two silently blends a probe distribution into a model-score distribution. This is the same shape as the length-field trap: the field exists, is populated, and means different things per row.
- **A CONTRACT TERM IS NOT EVIDENCE THAT IT BINDS AT EVERY CONSUMER — establish the precondition per consumer.** *(2026-08-16, llm-distillery#119.)* I put an ordering clause into a cross-repo contract on the strength of a four-cycle simulation at **one** consumer, and relayed it to the others as settled. It is necessary at NexusMind, which **re-reads the whole of `data/raw` every run** and therefore manufactures the stale-after-fresh sequence the clause exists to stop. It may be **cargo at ovr**, which reads filtered output written once per cycle and has run a bare hash-differs test at *four production sites* with no recorded thrashing. ⛔ **A term derived from one consumer's mechanics, stated in the contract, reads to every other consumer as a requirement with evidence behind it.** Name which consumer's mechanics produced a term, and let the others measure their own precondition rather than adopt it. *(Cost of the same session's related error: I described a cache from its **write** sites without reading where it is **consulted**, and reported a defect in a cache that already behaved correctly.)*
- **An issue that holds a FUTURE observation must never be referenced with `Closes`/`Fixes` by the PR that implements it.** *(2026-08-16, NexusMind NM#388.)* The two intentions contradict each other and **the merge resolves it toward closure, silently**: a dated watch was written correctly, cross-referenced in three places, and then closed by the `Closes #388` in the body of the PR whose evidence it was designed to receive. ⛔ **And the second carrier was equally dead** — the `docs/hypothesis-log.md` entry carried the date only inside its *Method* prose, with no `Review by:` field, which is the field `/curate` Step 0.6 actually sweeps. **Correct, fully written, cross-referenced, and reachable by nothing.** Both fixed and *verified* rather than asserted (`gh issue view --json state` → OPEN; `grep -c "Review by: 2026-08-23"` → 1). **A dated check needs a home that is OPEN on the date and a field that something sweeps** — being written down in three places is not the same as being surfaced in one.
- **A wrong-object read that returns a PLAUSIBLE number goes straight through — surprise is not a defence you can rely on.** *(2026-08-16.)* An ad-hoc reader reported `content_length 0/2265` against the canonical checker's `2265/2265`, because the field lives at `nexus_mind_attributes.<lens>.content_length` and not at top level. It was caught **only because zero was surprising enough to distrust**, not by any process — had the wrong path returned a believable figure it would have been filed as a measurement. ⭐ Sibling framing from the same day: **self-review found nothing at all.** Eleven-odd defects across four sessions were caught by another session re-deriving; the two apparent exceptions were authors *going to look at state they had just changed*, which is re-derivation with a shorter loop, not review. **Re-derive, or have someone else re-derive. Reading your own work again is not a control.**
- **Before using any source as evidence, establish what it excludes.** *(⚠️ **11th occurrence 2026-08-27 — I BUILT THE EXCLUDING SOURCE MYSELF.** `git archive HEAD` into a temp tree, as a before/after baseline for the reference checker: it ships TRACKED files only, so every gitignored path was absent and the run reported **240 findings against the real 1**. For a minute that read as a catastrophic regression in my own edit. **The baseline was not a worse version of the tree, it was a different tree.** Same shape as the 2026-08-24 keeper (*the shipped artifact exited 1 on a clean clone*) approached from the other side — there the gitignored evidence was missing from someone else's clone; here I manufactured the clone. ⚠️ The cheap copy tricks fail too: `cp -al` cannot hardlink across filesystems, and a `|| cp -a` fallback copies the repo INTO the half-made directory. 10th occurrence 2026-08-26 — A SOURCE THAT EXCLUDED ITS OWN TAIL, AND THE EXCLUDED PART WAS WHAT THE LOADED PART PROMISED.** The Claude Code auto-memory `MEMORY.md` declared at offset 164 that two ⛔ NO REPO FILE entries *"must not be trimmed: they are the only surviving record"*. The file was 26,645 bytes against a 24.4KB load limit, and both entries sat at offsets **24,905 and 25,445** — past the cut. **The guarantee loaded; the thing it guaranteed did not.** No instrument could have reported it: the notice and its subject were on opposite sides of the truncation, so reading the file as loaded shows a well-guarded index. ⭐ **A protection marker is a claim about the rest of the world — that no other copy exists — and it ages like any other state claim while reading as an instruction.** All seven of its claims had in fact been written into topic files, and its one unique atom had landed as a commit. **Before honouring OR removing such a marker, verify what it protects still needs protecting.** ⛔ Worse than stale: **full session files for both dates sat in the marker's OWN DIRECTORY** (14,194 and 9,502 bytes, sixty lines below it). The marker's literal words — NO REPO FILE — were true and irrelevant, and **a `ls` of its own directory refuted it.** Nobody ran one, because it read as an instruction. 9th occurrence 2026-08-23 — `datasets/adverse/*.jsonl` stores a 300-char EXCERPT, not the article. Every one of the 18 rows. Originals run 620–28,905 chars, and a two-oracle paid run against ledes-not-articles was one command away; the class-A test turns on the DOMINANT SUBJECT, which a lede cannot carry. Hydrate from `ovr.db`'s `articles` table. Caught before the spend, not after.**; **8th occurrence 2026-08-16 — a WINDOW is part of a source, and mine was the same length as the mechanism's period.** I bounded llm-distillery#119's reader exposure at "0 observed" over 50 retained collections spanning ~8 days. The mechanism that produces the class is eviction from a seen-URL store whose effective window is **~7.7 days** — so a repeat that requires straddling eviction had essentially no room to appear, and **that population must return 0 whatever the truth is.** Published in a public issue before it was checked; caught by the producer session, not by me. ⭐ The tell I missed: the zero was *satisfying*, and it arrived from a corpus I had not asked what it spans. Sibling error the same day: quoting a count off `ovr.db live_articles`, a legacy view off the build path — **two exclusions, one temporal and one structural, in one afternoon.** 7th occurrence 2026-08-12 afternoon — concluding an ABSENCE from a structure whose shape I had not established: I read `analysis.pre_enriched` over 1,070,665 rows, got 0, and nearly reported a dead stamp. The flags are at `nexus_mind_attributes/<lens>/pre_enriched`. **A wrong path and a dead field both read as zero, and the wrong one is the more exciting finding** — dump the keys that ARE there before reporting an absence. 6th occurrence 2026-08-11 afternoon — a PEER asserted a population claim from a doc whose caveat section they had read that same session and not re-read; verifying against their source rather than their report surfaced two further exclusions. 5th 2026-08-11 midday — see below; 4th 2026-08-09 — and this one was a **machine**, not a file.* I inventoried b650-gpu, found no judge verdicts, and reported the precision panel as UNADJUDICATED, blocking a whole track. The verdicts existed and had for three days: they live in the NexusMind checkout under `data/research/precision_panel*/`, which `.gitignore:230` excludes, so they were never copied to the GPU box. **A host is a source with an exclusion list too** — "I looked on the machine where the work was done" is the same error as "I read the file that only holds passers".*)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer. ⭐ **ONE ROOT, and it covers the INSTRUMENT as well as the source: THE INSTRUMENT WAS POINTED SOMEWHERE THAT CANNOT PRODUCE A POSITIVE, SO THE NEGATIVE CARRIED NO INFORMATION.** Found in three repos in three media on 2026-08-16 — a corpus shorter than the mechanism's period (the #119 case above), a validator run over 0 rows, and a grep over 0 files. A fourth, 2026-08-16, is the cleanest specimen because the number was never in doubt: measuring llm-distillery#121 (opinion/editorial surfacing), `nature_recovery` came back null with **68 of 92 within-source strata tied at 0 vs 0** — that lens surfaces 365 of 229,588 rows (0.16%), so at n≈10-30 per stratum most strata cannot produce a positive in *either* arm. The null was arithmetically correct and evidentially empty. **Before believing a negative, prove the instrument could have said yes.** ⚠️ **Second clause, because all of the above is only the broken-instrument half:** an instrument can be sound, its number *correct*, and still not be a function of the thing under test — a before/after whose baseline rests on an invariant the change does not touch. Nothing a reader checks comes back wrong. **Also ask what would have made the "before" different.**
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.
- **`pgrep -f "<pattern>"` cannot answer "is it running?" — and `pkill -f` cannot stop it.** *(**6th occurrence 2026-08-26, and it is this rule's own recommended remedy failing**: `systemctl is-active nexusmind.service` read `inactive` and the box was NOT idle — cleanup is a **separate unit** (`nexusmind-cleanup.service`, chained by `OnSuccess=`, running `scripts/main.py --cleanup-only` in its own cgroup) and it stayed `activating` another 8 minutes, executing the exact code path the deploy was about to replace. ⭐ **The service manager answers for the unit you NAME, and a chained unit is a different name.** Enumerate first — `systemctl list-units 'nexusmind*' --all` — then ask all of them; `OnSuccess=`/`Requires=`/`PartOf=` are part of what "is it running?" means. The chain was already recorded in `reference-sadalsuud-pipeline-chain` and I still queried one unit: **a documented mechanism you do not query is not a mechanism you have.** **5th occurrence 2026-08-25**: a wait-loop `until ! ps -eo args | grep -q "[m]ain.py"` never exited — the bracket trick protected the grep from itself, but the loop's own `echo "no main.py process running"` put the literal pattern on its command line, so **the watcher matched itself and waited forever**. Cost: a deploy held ~20 minutes after the box had gone idle, and three polls that reported a process which was my own waiter. The tell was there in the output the whole time — the matching line said `bash -c until`. ⭐ **PRINT THE MATCHING LINE. A count cannot show you that the match is you.** 4th occurrence 2026-08-21: `pkill -f -- "-L 11435:…"` matched and killed the invoking bash, which exited 144 and skipped the rest of the script. Kill by PID from `ps`, or kill on the far side of the ssh.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

