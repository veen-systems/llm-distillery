# Tier `docs/` for `refcheck.py`, and keep it off the default scan set — 2026-09-17

**llm-distillery#134 step 2.** Step 1 (2026-08-28, `6d72848`) measured; this settles the
tier and answers the flag question. **Nothing under `docs/` was edited to satisfy the
checker**, and no reference was fixed — the rule the step-1 evidence states is that a
widening and a marking pass must never be the same change.

## The answer, first

**`--docs` does NOT come off the flag.** The live tier alone carries **254 findings, in
60 of the 111 files it scans**, against a default run of **0**. Promotion would replace
the 0 baseline — the thing that makes a *new* break visible — with a section a reader
learns to skip. The precondition is the **marking pass**, not more measurement.

## The tier

It lives in `refcheck.py` (`_tier_of_doc`), not in a README table.

| tier | directories under `docs/` | findings | files with findings | files scanned |
|---|---|---|---|---|
| **LIVE** | `<root>`, `adr/`, `agents/`, `articles/`, `checklists/`, `guides/`, `ideas/`, `proposals/`, `references/`, `templates/` | **254** | 60 | 111 |
| **FROZEN** | `_archive/`, `decisions/`, `evidence/`, `experiments/`, `reports/` | **124** | 48 | 131 |

Of the 111 live files, **8 are in a frozen directory** — 5 reached by routing, 3 as
undated indexes. The report prints that breakdown on the LIVE line, for the reason under
rule 2 below.

**FROZEN** means *a frozen account of a moment*: a reference that broke because the world
moved is not decay there, and editing the record to silence the checker is the compression
#123 forbids. Same rationale and same disposition as `memory/project_session_*.md` under
`--sessions`.

⛔ **The directory is not the tier, and the first draft of this change said it was.** It
warranted a directory-only rule with *"every frozen entry is dated by construction"* — an
absolute that is false, and the counterexample is load-bearing:
`docs/decisions/framework-adoption-history.md` is undated, was edited the same day, is
routed into from `CLAUDE.md` **twice**, and carries the largest finding count of any
single file in the frozen set. The rule froze it — *"never to be edited to satisfy this
checker"* — along with four more `CLAUDE.md` pointer targets and every undated index. The
review battery's adversarial lens found it; the 17 tests written to guard the tier did
not. So the tier is **three tests, in order**:

1. **LIVE if the directory says so** — anything not in `DOCS_FROZEN_DIRS`.
2. **LIVE if the always-loaded layer routes an agent into it.** That is the LIVE
   criterion's own wording, computed from `CLAUDE.md` and `memory/MEMORY.md` rather than
   hand-listed. Five files qualify today, all under `docs/decisions/`, and `CLAUDE.md`
   reaches one of them (`2026-08-25-pause-investment-risk.md`) for an **un-pause
   procedure** — a dated filename on an operational document.
3. **LIVE if the path carries no date *and sits directly in the frozen directory*** — an
   undated file among dated siblings is an index or a running history. `_archive/` is
   exempt: frozen by definition, not by date.
   ⛔ **The depth restriction is round 2 of the review repeating round 1's finding**, which
   is what turned two rounds into a census rather than a third. Undated at *any* depth
   admitted **13 files of which 10 are frozen accounts by this document's own
   definition**: six verbatim copies of **other repos'** ADRs under `docs/evidence/adr/`,
   two training reports for `sustainability_technology` (a filter removed 2026-08-03), an
   article draft and a log excerpt — **21 findings, 7.7% of the live total** that the
   promotion decision and the marking-pass sizing both rest on. A nested undated directory
   is a *collection* inside a frozen one. At depth 3 the rule admits exactly three files:
   `docs/decisions/README.md`, `docs/evidence/README.md` and
   `docs/evidence/hypothesis-log-excerpts.md` — two indexes and one excerpt file that is
   arguably frozen, carrying 1 finding. **That residue is named, not hidden.**

⚠️ **`ROUTED_FROM` is in-repo only, deliberately.** The user-level auto-memory index is
auto-loaded too, but it lives outside the repo and is absent on another machine or a fresh
clone — and a tier that differs by machine makes the split differ by who ran it. Measured:
including it changes nothing — the same routed set either way, and the same 5 files in
frozen directories — so the determinism is free.

⚠️ **The routing pattern needs a left boundary, and the first version had none.** It
matched `NexusMind/docs/ARTICLE_RECORD.md` from its `docs/` onward — `CLAUDE.md` carries
two such cross-repo paths — and registered them as routing targets for files of ours that
do not exist. They were inert only because no local file shared those names. Anchoring
took the routed set from **17 to 15, and all 15 now resolve**; `../docs/…`, which
`memory/MEMORY.md` writes, still matches, because the boundary sits in front of the
optional `../`. ⚠️ **What it still cannot see**, stated because an unnamed residue is read
as zero: the pattern is context-blind. A path inside a fenced code block, inside a
sentence saying it does *not* exist, or inside a `~~struck~~` deletion marker still
registers as routed. That over-includes into LIVE — more scanned, not less — and the
count is printed.

**Two departures from step 1**, both because the files said otherwise:

- **`reports/` and `experiments/` are FROZEN.** Step 1's *table* tiered both live. All
  three `.md` files in `docs/reports/` are `*_2025-11-17.md` (a fourth file is an undated
  PDF, which the checker does not scan); `docs/experiments/` holds one dated benchmark.
- **`templates/` is LIVE**, reversing step 1's *proposal* of "frozen or marked". A
  template is a *maintained* document whose paths are non-resolving **by purpose**, and
  the instrument already has the purpose-built mechanism for that: the
  `<!-- placeholder -->` marker, which **counts** them in their own section. Dropping a
  maintained file from the scan to hide paths known not to resolve is the silent skip this
  whole instrument exists to prevent. The cost of the honest option is 4 findings, all in
  `docs/templates/`, until the marking pass.

## What else changed in the instrument

1. **`--docs-live` / `--docs-frozen`**, alongside `--docs`. ⛔ **`--docs` keeps meaning all
   of `docs/`** — every number on record for it (339, 401, 376, 377 across four surfaces)
   was measured that way, and narrowing a flag to a subset makes those readings wrong in
   documents that cannot know it happened. `--docs-live` is the **preview of what
   promotion would put in the default set**.
2. **`### FINDINGS BY TIER`**, emitted whenever docs are in scope. The split was
   hand-written and hand-recomputed; *a hand-built population is what every measurement
   error this project has made turned out to be.* It prints **two** file counts, because
   one word cannot carry both: the first draft's "212 findings over 103 files" was read as
   *103 files have findings* when 103 was the files **scanned** — a ~2× error in the
   number that sizes the marking pass. A tier not in the scan set prints **`not scanned`**,
   never `0`: the first draft printed the zero under `--docs-live` and `--docs-frozen`,
   i.e. in the two runs this change exists to add, with a test asserting it was correct.
3. **An untiered `docs/` subdirectory raises.** Defaulting to live would put findings in
   the default set the day promotion happens; defaulting to frozen would hide them
   forever. A run that cannot say what its scan set excludes must not print a number.
   ⚠️ **Not the three-outcome exit contract** — a recorded *Decline* at v1.29.0, re-adopted
   and reverted twice since (2026-08-29, and 2026-09-11 → 09-12;
   `framework-adoption-history.md`). That was a *verdict* nothing read. This aborts
   **before** any verdict, and what carries it is the printed demand, which the human
   running the audit reads. ⚠️ It cannot fire on the default invocation, which scans no
   docs; the automatic catcher is `test_every_docs_subdirectory_is_tiered`.
4. **An unrecognised ARGUMENT raises — and "unrecognised" is not "starts with `--`".**
   The first version checked only `--`-prefixed tokens while its own message asserted
   "there are no positional arguments": `refcheck.py . CLAUDE.md memory/MEMORY.md` — the
   `/audit-context` command with its one flag dropped — ran to exit 0 and printed the full
   default report, which is precisely the "small, reassuring findings count" the guard was
   written against. `-docs`, `-h` and an em-dash `--docs` did the same, and em dashes are
   everywhere in this repo's prose. All four reproduced before the guard was widened.
   ⚠️ **Upstream's checker takes `--sibling-root` and positional arguments; this fork takes
   neither.** A command copied from the skill runs a different program here.
5. **`_relroot()` — a latent cwd bug, found while writing the tests.**
   `os.path.relpath(d, ROOT)` on an **already-relative** path resolves it against the
   **CWD**. Every report section that grouped by directory was therefore cwd-dependent and
   emitted `../../..` keys whenever the checker ran from outside the repo — which is
   exactly what `REFCHECK_ROOT` exists for. The rung-1b `docdir` computation was a second,
   independent spelling of the same predicate and now calls the same helper.
6. **The flags line prints on both branches.** It sat only in the `>34 docs` branch, and
   the default scan set is *exactly* 34 documents — so the one run anybody makes routinely
   said nothing about its own scope, against a comment promising to "always say which
   flags were in effect".

## Drift, re-scored under one rule by a committed script

`scripts/analysis/refcheck_tier_reparse.py` re-tiers a saved log with the rule imported
from `refcheck.py` — not restated, or it would be the second copy this change exists to
remove. Both sides below come from it, and today's side reproduces the instrument's own
`FINDINGS BY TIER` line exactly (254 / 124), which is the cross-check that the script and
the checker agree.

| tier | 2026-08-28 log | 2026-09-17 | Δ |
|---|---|---|---|
| LIVE | 245 in 60 files | **254 in 60 files** | +9 |
| FROZEN | 93 in 35 files | **124 in 48 files** | +31 |
| non-docs | 1 | 0 | −1 |
| total | 339 | **378** | +39 |

⛔ **This is not a rot rate, and two earlier readings of it were.** The first draft of this
record said *"frozen grew ~7× faster"*; #134's 2026-09-17 comment said *"~8×"*. Over those
twenty days the whole `docs/` corpus went from **168 files to 242**, the growth almost
entirely **dated evidence directories** — which are the frozen tier by construction. More
frozen findings because there are more frozen files is not decay. **The promotion decision
rests on neither figure**: 254 live findings against a 0-finding default stands alone.

⚠️ **Two biases, both stated rather than corrected.** The two runs are not the same
instrument — rung 3 left the STALE `resolves` disjunction on 2026-09-17 (`ad32356`), which
can only *remove* findings — and the routed-into override is applied against **today's**
`CLAUDE.md`, because the August copies are not in the log. Both deltas are lower bounds.

## Two review rounds, then a census

Round 1 (4 lenses) found 6 classes; round 2, scoped to what the fixes could break, found
6 more. ⛔ **Round 2's first finding was round 1's finding again** — an unmeasured
absolute justifying a tier rule, over a population nobody had enumerated — and the round
cap's own remedy for a class seen twice is a **census, not a third round**. Two were run:

- **Every absolute about behaviour** in the prose this change adds. Adjudicated:
  prescriptions and quotations of the refuted claim stand; **three descriptions did not**
  and are fixed — *"it cannot reach the docs tier, and that is structural"* (a `SEED`
  under `docs/` does reach it), *"every assertion here is POSITIVE about the scan set"*
  (several are negative, and the discipline is the pairing, not the polarity), and an
  unevidenced *"every github.com URL"*.
- **Every count either tool prints** — 12 surfaces in `refcheck.py`, 7 in the re-parser —
  against the population it is over. One defect each, both already the fixes above; the
  rest are over their own scan set by construction, and a directory with no findings is
  *named as clean*, never printed as a zero.

## Controls

A scan-set change is invisible in the place people look: a narrowed set reports *fewer*
findings, which reads exactly like a repo that got cleaner.

| control | result |
|---|---|
| default run vs `HEAD`, by outcome | **two lines** differ and no others: the working-tree **count**, which moves with the files this change adds (the checker walks the filesystem), and the new `flags: (none)` — item 6 above, which is a deliberate addition to this branch |
| `--docs` vs `HEAD`, by outcome | identical except the new `FINDINGS BY TIER` section; the total is unchanged, so the flag's meaning is preserved by measurement, not by assertion |
| `--docs-live` + `--docs-frozen` | 254 + 124 = 378 = `--docs`, and each tier run alone reproduces its own line from the combined run |
| the tier's out-of-scope line | `--docs-live` prints `FROZEN  not scanned`, not `FROZEN 0` |
| rung-1b `_relroot` dedup | `--docs` output **byte-identical** before and after the refactor |
| seeded sensitivity harness | **40/40 PASS** — the two new cases are the argument guard, the one part of this change `run.sh` can reach (it runs on `argv`, above the `SEED` short-circuit). Both directions: 7 unrecognised arguments rejected, 4 known flags still accepted. |
| `tests/unit/test_refcheck_docs_tier.py` | **37 tests**, against fixture trees with `REFCHECK_ROOT` *and* `HOME` redirected |
| `tests/unit/test_refcheck_tier_reparse.py` | **6 tests** on the re-parser, which shipped with none — every one about its ability to say NO: a tier never scanned, a log with no header to reconcile against, a header that disagrees |
| mutation test | **18 mutants, 18 killed** — ⚠️ **a manual run, not a committed harness**: the mutants were applied to a working copy and reverted, so a reader cannot re-run them, only re-create them from this list. Includes the three that survived the first version of these tests: a tier overridden by a DUPLICATE entry with the original text intact, a tier declared only in a COMMENT, and the hit/scanned column swap |
| full suite | green — the baseline count lives in `.claude/review-profile.md`, which is meant to be its only live copy |

⛔ **The two tier tests in the first version were source-text greps** —
`src.split("DOCS_TIER = {")[1]` and a string match — while one of their docstrings claimed
it asserted "against the code". Both now run the checker against a fixture tree and read
what it did. *A name is an assertion*, and that one was lying, inside the test written to
stop a hand-kept tier.

## Step 3, which is now the open work

**The marking pass over the live tier**, then promotion in a *separate* change.

Precedent for what it can achieve: `memory/` went **23 → 0** on 2026-09-17, mostly by
moving references into the counted placeholder section rather than by fixing them.
⚠️ **That 0 is scoped to the DEFAULT scan set** — `CLAUDE.md`, `memory/*.md` and the
auto-memory index — and `docs/TODO.md` carries an explicit warning against quoting it
wider, which is why it appears here as a precedent for the METHOD and not as a target
number. Its own 23 → 0 breakdown is quoted nowhere here because the published split does
not sum; *closed accounting is not attribution* applies to a precedent too. `docs/` has never had that pass, so its 254 is the *unmarked* rate.

⛔ **254 is not 254 defects.** The step-1 triage separates at least five classes and only
one is decay — template placeholders, rolling runtime artefacts quoted as bare basenames,
forward references, unmarked cross-repo (the largest bucket: 100 of the 211 findings step
1 tiered as live), and genuine decay. One confirmed instance of the last, still unfixed
and still the best argument for the whole issue: **`docs/README.md`, the repo's own
documentation index, points at three `docs/agents/*.md` files that do not exist.** ⚠️ Two
of the three now exist **one directory deeper**
(`docs/agents/templates/dimensional-regression-qa-agent.md`,
`docs/agents/templates/oracle-calibration-agent.md`) — the reference is wrong by one
segment, which is decay, not absence.

⚠️ **One disposition the marking pass must settle and step 1 did not**: a *deliberately
uncommitted* artifact (`phaseA_cohort200.jsonl` — full article text at scale is the #97
hazard) is a correct reference to a file that will never be on disk. The extractor has
`asserted-absent`; this is the adjacent case, and without a disposition every evidence
directory that follows the #97 rule generates permanent findings. This record's own
reference to it is one of the 124.

## Reproduce

```bash
python3 tests/fixtures/reference-integrity/refcheck.py               # default: 0
python3 tests/fixtures/reference-integrity/refcheck.py --docs-live   # the promotion preview
python3 tests/fixtures/reference-integrity/refcheck.py --docs        # both tiers
bash  tests/fixtures/reference-integrity/run.sh                      # 40/40
.venv/bin/python -m pytest tests/unit/test_refcheck_docs_tier.py \
                              tests/unit/test_refcheck_tier_reparse.py -q   # 43 passed
python3 scripts/analysis/refcheck_tier_reparse.py \
        docs/evidence/2026-08-28-refcheck-docs/refcheck_docs_run.log # the August side
```

⚠️ **The `--docs` totals are deliberately not written beside those commands.** Every
`--docs` figure on record drifted within a day of being written, including this record's
own first draft, which printed 377 in a block a reader is told to execute while predicting
378 six lines earlier. Run it and read the line.
