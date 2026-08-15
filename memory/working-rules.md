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

### Every measurement error this project has made was a HAND-BUILT POPULATION

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

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — and then prove the outcome changed at the END of the run.** *(⚠️ **12th occurrence 2026-08-15 — a GATE THAT TRACKS AN EVENT INSTEAD OF A PROPERTY**: FluxusSource's `7bc20a0` was gated "not for deploy until NexusMind's envelope declaration merges." It merged, so the gate reads green — while three `content_meta` shape mismatches stand, one of which fails validation closed. **A gate written as "wait for X to merge" tracks whether X happened, never whether the two shapes agree.** 11th occurrence 2026-08-15 — the MEASUREMENT form: I reported "0 non-canonical across all three timestamp fields" as outcome proof when **two of the three had 0 rows present**; the check counted violations and never presence, so absent and clean produced identical output. **A check that examines nothing reports success.** 10th occurrence 2026-08-12 — a twelve-line `<!-- verify: -->` annotation that could never be extracted, so a claim that had already regressed once went unchecked; 9th 2026-08-11 afternoon — six self-inflicted.)* **An annotation, a test and a check are mechanisms too** — "the file has a verify comment" is a config key, not an outcome. **Naming the caller is not sufficient.** Guards have shipped with *correct callers on the right paths* and still done nothing — one reverted downstream by a `COALESCE` merge, one short-circuited by an earlier commit point. Both passed unit tests on the predicate; a green test on the predicate proves only the predicate. If a guard's whole value is that it changes an outcome, **run it and print the resulting state**, and ask "is this the only writer of this field?" — not just "is my code reached?". **Never infer runtime behaviour from the presence of a config key.** Three smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end; a field initialised to `None` and populated somewhere you have not read; and **a feature validated on "production data" without naming WHICH STAGE** (the arXiv announce prefix is a 91.6% detector at collection and **0.000** after enrichment — both are production data). Two related traps: **a comment explaining why code is safe is a claim like any other**, and **if a criterion depends on "now", encode the criterion, never its answer**. → The catalogue of occurrences (NM#284, #94, NM#281, NM#300, cd v6) is in `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first (2026-08-12).** A `stage1_low` row's persisted score is an **e5 probe estimate** (ADR-006 hybrid inference), not a Gemma score. Measured: re-scoring 300 production rows on a production-parity box reproduced `stage2` rows **231/231 within 0.16 at median \|Δ\| 0.0000**, and **every** disagreement above 0.16 was a `stage1_low` row — 23% of rows. Mixing the two silently blends a probe distribution into a model-score distribution. This is the same shape as the length-field trap: the field exists, is populated, and means different things per row.
- **Before using any source as evidence, establish what it excludes.** *(7th occurrence 2026-08-12 afternoon — concluding an ABSENCE from a structure whose shape I had not established: I read `analysis.pre_enriched` over 1,070,665 rows, got 0, and nearly reported a dead stamp. The flags are at `nexus_mind_attributes/<lens>/pre_enriched`. **A wrong path and a dead field both read as zero, and the wrong one is the more exciting finding** — dump the keys that ARE there before reporting an absence. 6th occurrence 2026-08-11 afternoon — a PEER asserted a population claim from a doc whose caveat section they had read that same session and not re-read; verifying against their source rather than their report surfaced two further exclusions. 5th 2026-08-11 midday — see below; 4th 2026-08-09 — and this one was a **machine**, not a file.* I inventoried b650-gpu, found no judge verdicts, and reported the precision panel as UNADJUDICATED, blocking a whole track. The verdicts existed and had for three days: they live in the NexusMind checkout under `data/research/precision_panel*/`, which `.gitignore:230` excludes, so they were never copied to the GPU box. **A host is a source with an exclusion list too** — "I looked on the machine where the work was done" is the same error as "I read the file that only holds passers".*)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer.
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.
- **`pgrep -f "<pattern>"` cannot answer "is it running?"** *(3rd occurrence, twice in one session.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

