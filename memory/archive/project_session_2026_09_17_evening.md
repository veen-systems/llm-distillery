# Session 2026-09-17 (evening) — ADR-013 widened, and review falsified my own compliance zero

**Cost: $0.** No oracle calls, nothing in `filters/`, **deploy N/A — inapplicable, not
skipped** (no filter package, model, calibration, threshold or op-point changed). No merge
(on `main`, repo convention). Issue **#160** filed.

## What was asked, and what shipped

Owner: *"framework internal language should be english"*, then *"make that edit"*, then
*"yes, add that line to CLAUDE.md"*.

ADR-013 widened from **lens/tab names** to **all framework-internal text** — docs, ADRs,
comments, memory, commit messages — carving out match patterns, boilerplate strippers and
test fixtures, which are **data the code matches against multilingual article text**.

## ⛔⛔ THE KEEPER — the positive control was of the WRONG CLASS

The first draft claimed **zero violations**. The sweep used a 36-token list of Dutch
**function words** (`niet`, `wordt`, `omdat`, …). The class ADR-013 polices is Dutch
**names**. Measured: that list scores **0** on both real violation sites.

**The instrument HAD a positive control and it passed** — it found the Dutch fixture
*sentences* at `uplifting/v7/prefilter.py:567` and `benchmark_models.py:61`. A Dutch
sentence and a Dutch lens name are different classes, and the control only proved the first.

⭐ **A positive control must be of the CLASS UNDER TEST, not merely the language/domain
under test.** This is `CLAUDE.md`'s own instrument rule, broken in the document where I was
asserting compliance with it.

Two open violations (#160, owner call — an ADR is a historical record):
`docs/adr/009-add-filters-first-reduce-later.md:25,34,35,37,60` (`Welzijn`/`Erfgoed`/
`Vooruitgang`) and `scripts/analysis/cross_filter_landscape.py` (39 occurrences).

⚠️ ADR-013's own Consequences `:86` already carried an open action — *"check TODO.md,
ROADMAP.md, ADR-012 appendix"* — and ADR-009 (2026-03-04, **older than ADR-013**) is exactly
the leftover it pointed at. The retracted sweep declared zero without reconciling it.

## Review: 5 BLOCKERs in ~34 lines of my own doc change

4 lenses, MEDIUM tier, one round. **The decision survived all four; every piece of evidence
I attached to it failed.**

| # | Finding |
|---|---------|
| 1 | *"`ADR-013` cited across five repos"* — **false**. 5 files, one repo; four other repos have **unrelated** ADR-013s. It was the sole justification for keeping a title that no longer matches |
| 2 | **Sign reversed.** `cultural_discovery/v5:105` is in `EXCLUSION_PATTERNS` — deleting it makes the filter block *less*: **specificity**, the ADR-023 priority, not recall |
| 3 | **19.9%/13.0% is a framing this repo retracted 2026-08-02**, attached to the wrong study (LD#86's 135/871 over 20 cycles, not NM#285's 8,283) |
| 4 | *"measured, not hypothetical"* — **backwards**. The prefilter is dead in production (NM#284); the cost is on the labelling path and is **unmeasured** → **H-LANG-1** |
| 5 | `CLAUDE.md:178` **permitted the original failure** — an agent naming a tab **"Verwondering"** was compliant, and that is the verbatim example ADR-013's Context `:44` exists to forbid |

⭐ **One lens finding REFUTED**: `wordt hersteld` is not a dead alternation branch —
leftmost-match returns it, measured. Don't take a lens at face value.
⭐ **I introduced one defect inside the fix**: wrote "12 files" where 12 is the **line**
count and the file count is **9**. Caught by checking my own new number.

## Framework: 6 releases behind (v1.40.0 → v1.45.1), stamp deliberately NOT bumped

All four user-global skills measured **byte-identical to the v1.45.1 reference install**
(0 differing lines, monotone fall to an exact zero). **3 adopt · 2 in force · 1 decline.**
⛔ **#166: three project lenses were annotated `NOT READ BY THE SKILL` and are not dead** —
verified at `~/.claude/skills/review-changes/SKILL.md:83`/`:300`. **They fired this session
and found real blockers.** Full triage + the decline's reason:
`docs/decisions/framework-adoption-history.md`.

## Not fixed, deliberately

**`CLAUDE.md:74` still carries the retracted 19.9%/13.0% framing** — six weeks on, in the
always-loaded file, which is where I took it from. Three more copies
(`HUMAN_THRIVING_V8_PLAN.md:176`, `cross-repo-prioritization.md:1173`/`:1359`) against two
carrying the correction. Separate change, deserves its own review.

## Files

`CLAUDE.md` (line 178), `docs/adr/013-english-lens-names.md`, `docs/adr/README.md`,
`docs/TODO.md`, `docs/decisions/framework-adoption-history.md`,
`memory/hypothesis-ledger.md` (H-LANG-1), this file, `memory/MEMORY.md`.
