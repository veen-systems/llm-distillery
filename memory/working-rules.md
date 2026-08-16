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
`contracts/CHANGELOG.md` 1.18.0) guarded by a test whose name says so, which failed by
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
2026-08-14 — **and the correct statement was in that repo's own always-loaded index the
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

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — and then prove the outcome changed at the END of the run.** *(⚠️ **14th occurrence 2026-08-16 — I CLAIMED A MECHANISM I NEVER STARTED**: reported "watcher armed for the 08:02 delivery" in a session summary having launched nothing. The sentence had been true for the three previous deliveries and was written a fourth time from habit rather than from a launch. Caught only because the owner mentioned the time; `ps` settled it in three seconds. **How it fails is the reusable part: silently** — no notification, no error, just no fourth measurement, and the likely outcome was reporting "three clean and a fourth pending" indefinitely. ⭐ Committed on the same day as, and in the report about, a night spent cataloguing declared-but-uninvoked mechanisms. 13th occurrence 2026-08-15 — a STAMP THAT TURNS OFF ITS OWN CHECKER**: `CLAUDE.md`'s framework stamp was bumped to v1.26.0 on 2026-08-13 before either release was triaged, and the stamp is `/update-drift`'s only input — so every later run reported "current" and examined nothing. Two releases sat unreviewed, one carrying an explicit adopter action. **A stale stamp is safe; a premature one is the only value that can silence its own check.** Now probed, seeded against the real disagreement (frontmatter v1.25.0 vs footer v1.26.0) before being believed. 12th occurrence 2026-08-15 — a GATE THAT TRACKS AN EVENT INSTEAD OF A PROPERTY**: FluxusSource's `7bc20a0` was gated "not for deploy until NexusMind's envelope declaration merges." It merged, so the gate reads green — while three `content_meta` shape mismatches stand, one of which fails validation closed. **A gate written as "wait for X to merge" tracks whether X happened, never whether the two shapes agree.** 11th occurrence 2026-08-15 — the MEASUREMENT form: I reported "0 non-canonical across all three timestamp fields" as outcome proof when **two of the three had 0 rows present**; the check counted violations and never presence, so absent and clean produced identical output. **A check that examines nothing reports success.** 10th occurrence 2026-08-12 — a twelve-line `<!-- verify: -->` annotation that could never be extracted, so a claim that had already regressed once went unchecked; 9th 2026-08-11 afternoon — six self-inflicted.)* **An annotation, a test and a check are mechanisms too** — "the file has a verify comment" is a config key, not an outcome. **Naming the caller is not sufficient.** Guards have shipped with *correct callers on the right paths* and still done nothing — one reverted downstream by a `COALESCE` merge, one short-circuited by an earlier commit point. Both passed unit tests on the predicate; a green test on the predicate proves only the predicate. If a guard's whole value is that it changes an outcome, **run it and print the resulting state**, and ask "is this the only writer of this field?" — not just "is my code reached?". **Never infer runtime behaviour from the presence of a config key.** Three smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end; a field initialised to `None` and populated somewhere you have not read; and **a feature validated on "production data" without naming WHICH STAGE** (the arXiv announce prefix is a 91.6% detector at collection and **0.000** after enrichment — both are production data). Two related traps: **a comment explaining why code is safe is a claim like any other**, and **if a criterion depends on "now", encode the criterion, never its answer**. → The catalogue of occurrences (NM#284, #94, NM#281, NM#300, cd v6) is in `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first (2026-08-12).** A `stage1_low` row's persisted score is an **e5 probe estimate** (ADR-006 hybrid inference), not a Gemma score. Measured: re-scoring 300 production rows on a production-parity box reproduced `stage2` rows **231/231 within 0.16 at median \|Δ\| 0.0000**, and **every** disagreement above 0.16 was a `stage1_low` row — 23% of rows. Mixing the two silently blends a probe distribution into a model-score distribution. This is the same shape as the length-field trap: the field exists, is populated, and means different things per row.
- **Before using any source as evidence, establish what it excludes.** *(7th occurrence 2026-08-12 afternoon — concluding an ABSENCE from a structure whose shape I had not established: I read `analysis.pre_enriched` over 1,070,665 rows, got 0, and nearly reported a dead stamp. The flags are at `nexus_mind_attributes/<lens>/pre_enriched`. **A wrong path and a dead field both read as zero, and the wrong one is the more exciting finding** — dump the keys that ARE there before reporting an absence. 6th occurrence 2026-08-11 afternoon — a PEER asserted a population claim from a doc whose caveat section they had read that same session and not re-read; verifying against their source rather than their report surfaced two further exclusions. 5th 2026-08-11 midday — see below; 4th 2026-08-09 — and this one was a **machine**, not a file.* I inventoried b650-gpu, found no judge verdicts, and reported the precision panel as UNADJUDICATED, blocking a whole track. The verdicts existed and had for three days: they live in the NexusMind checkout under `data/research/precision_panel*/`, which `.gitignore:230` excludes, so they were never copied to the GPU box. **A host is a source with an exclusion list too** — "I looked on the machine where the work was done" is the same error as "I read the file that only holds passers".*)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer.
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.
- **`pgrep -f "<pattern>"` cannot answer "is it running?"** *(3rd occurrence, twice in one session.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

