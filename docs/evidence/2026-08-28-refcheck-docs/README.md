# #134 step 1 — `refcheck.py --docs`, run once, measured

**2026-08-28. Step 1 only: measure with the real instrument.** No reference was fixed, no
file under `docs/` was edited to satisfy the checker, and `docs/` is **not** in the default
scan set. The tiering decision (#134 step 2) is proposed at the bottom and not applied.

## The instrument

`tests/fixtures/reference-integrity/refcheck.py` now takes **`--docs`**, mirroring the
existing `--sessions`: it adds every `docs/**/*.md` to the scan set. It is flag-gated on
purpose — see step 2.

Two controls ran before the number was believed:

| control | result |
|---|---|
| seeded sensitivity harness (`run.sh`) before and after the edit | **33/33 PASS** both times |
| default run (no flag) diffed against the version at `HEAD` | **identical** except the new per-directory attribution section — the flag is off by default, proven by outcome, not by reading the code |
| `--docs` passed to the seed harness | inert (`SEED` overrides `DOCS`), so the harness measures what it measured before |

⚠️ **A prediction was written before the run** and is kept unedited beside this file
(`prediction_before_docs_run.txt`): central estimate ~110, range **60–250**, with an
explicit falsifier that *"over ~400 means something systematic is misfiring"* and that
**no number was to be reported before the per-directory breakdown was read**.

## The number

**Scan set 34 → 202 files. Findings 1 → 339, of which 338 come from `docs/`.**

⭐ **That is ABOVE my stated range**, so by my own falsifier it is a triage trigger, not an
answer. It is under the 400 that would have meant the instrument was misfiring, and the
breakdown below reconciles exactly (339 parsed = 339 reported = sum of every bucket), so
the count is real — but *338 findings is not 338 defects*, and the sections below say why.

| tier | files | findings | what they are |
|---|---|---|---|
| **LIVE** — top-level `docs/`, `adr/`, `agents/`, `guides/`, `proposals/`, `templates/`, `reports/`, `articles/`, `checklists/`, `ideas/`, `references/`, `experiments/` | 106 | **211** | 100 unmarked cross-repo · 99 not found anywhere · 12 collisions / stale markers |
| **FROZEN** — `evidence/`, `decisions/`, `_archive/` | 62 | **127** | 55 unmarked cross-repo · 71 not found anywhere · 1 collision |
| pre-existing (`memory/`) | — | 1 | the standing `narrative_risk.json`, deliberately left |

Reconciles: 106 + 62 = 168 files under `docs/`; 211 + 127 = 338 findings; 155 cross-repo +
170 not-found + 13 collisions/stale = 338.

Largest LIVE contributors: `docs/` top level **153**, `docs/agents/` **23**, `docs/adr/`
**15**. `docs/checklists/`, `docs/ideas/`, `docs/references/`, `docs/experiments/` and
`docs/evidence/reports/` are **clean**.

### Where the unmarked cross-repo references point

| sibling | refs unambiguously in exactly that repo |
|---|---|
| NexusMind | 73 |
| ovr.news | 25 |
| FluxusSource | 18 |
| agent-ready-projects | 16 |
| pipeline-atlas | 7 |
| personal, admin | 3 |
| **ambiguous — matched 2+ repos** | **13** |
| **total** | **155** |

⚠️ **This bucket means "a sibling repo contains a file with this path suffix" — necessary,
not sufficient.** It answers *would rung 4 resolve this if the prose named the repo*, not
*is this reference correct*. Common basenames (`main.py`) match several repos, which is
exactly what rung 4 reports as a collision — the 13 ambiguous rows above.

⛔ **A defect in my first triage script, caught and corrected, recorded because it is the
repo's signature shape.** `veen-systems` is this repo's own **parent** directory *and* is
re-listed as a child of the grandparent, so its tree contains every other repo — and the
first attribution therefore reported **137 of 156** references as "matched more than one
sibling". Excluding the container gives **13**. The buckets summed to the right total both
times: *closed accounting is not attribution*. `refcheck.py` itself is not affected — rung 4
only tries a repo whose name appears as a whole token in the surrounding prose.

## Why the raw 338 must not be spent as a defect count

Sampling the LIVE not-found set separates at least five classes, and only one of them is
decay:

1. **Template placeholders that must never resolve** — `docs/templates/ADR-TEMPLATE.md`
   contributes `path/to/file.py`, `../adr/001-title.md`, `../decisions/YYYY-MM-DD-title.md`.
   Fix is a `<!-- placeholder -->` marker, not an edit to the template's meaning.
2. **Rolling runtime artefacts quoted as bare basenames** — `filtered_20260826_051337.jsonl`,
   `blocked_20260824_130550.jsonl`, `flagged_20260826_031106_485.jsonl`. Rung 3 already
   understands `data/…`; it cannot fire on a basename with the directory stripped, and
   these files age out by design.
3. **Forward references** — `corpus_manifest.json` (#127, deliberately not written yet),
   `filters/human_thriving/v8/ground_truth_gate.json` (v8 does not exist yet). A plan naming
   its own output is not a broken reference.
4. **Unmarked cross-repo** — the 155 above; the fix is qualifying the prose, which is the
   same remedy the 2026-08-16 widening produced.
5. **Genuine decay.** Real, and this is what the run is for. Confirmed example:
   **`docs/README.md`, the repo's own documentation index, points at three agent documents
   that do not exist** — `agents/filter-harmonizer.md`,
   `agents/dimensional-regression-qa-agent.md`, `agents/oracle-calibration-agent.md`. What
   `docs/agents/` actually holds is `README_FILTER_HARMONIZER.md`.
   `docs/SYSTEM_OVERVIEW.md` repeats the first one.

⛔ **The FROZEN tier is the manufactured-findings risk #134 predicted, and it materialised.**
Its 71 not-found are dominated by 2025-11 decision records — `2025-11-10-model-selection-qwen-1.5b.md`
and its neighbours name Qwen-era files that were correctly deleted when the project moved to
Gemma. Those references are **correct as history**. Editing them to silence the checker is
the compression #123 forbids.

## Proposal for step 2 — tiering (NOT applied)

1. `docs/adr/` + top-level `docs/` + `docs/agents/` + `docs/guides/` + `docs/proposals/` +
   `docs/checklists/` + `docs/references/`: **live**, and candidates for the default scan
   set — but only *after* a marking pass, or the default run stops being readable and the
   1-finding baseline that makes a new break visible is lost.
2. `docs/evidence/` + `docs/decisions/` + `docs/_archive/`: **frozen**, stay behind the
   flag, exactly as `memory/project_session_*.md` already are.
3. `docs/templates/`: frozen or marked — its whole purpose is non-resolving paths.

⚠️ **Do not promote anything to the default set in the same change that fixes references.**
The 2026-08-16 precedent is that a widening's first run is dominated by marking work, and a
default run carrying 200 findings trains the reader to skip the section.

## Reproduce

```bash
python3 tests/fixtures/reference-integrity/refcheck.py --docs     # this log
bash  tests/fixtures/reference-integrity/run.sh                   # 33/33
```

Full output: `refcheck_docs_run.log` (this directory).

⚠️ **The log is a snapshot: 168 `docs/**/*.md` at run time.** This README was written
afterwards, so a re-run now scans 169 and the totals will differ by whatever it
contributes. `prediction_before_docs_run.txt` is `.txt` deliberately — it must not
become part of the surface it predicted.
