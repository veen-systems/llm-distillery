# Read-surface round 1 tools (2026-10-12, `docs/TODO.md` item 2, #163)

Copied VERBATIM from the session scratchpad so round 2 can reuse them. Not generalised: dates and the
TODO item label are written into `mover.py`'s archive header; edit them before reuse.

- `mover.py SPEC.json` — moves line ranges of a memory file verbatim to `memory/archive/<stem>-archive.md`
  (appends when the archive exists), leaves hook lines in place, then runs a lossless check and a mutant
  check (drop one archived line → must report exactly 1 missing).
- `dates.py` — newest-date per section, a proxy for "closed". ⚠️ Unsafe on trap-dense files
  (`filter-status.md`, `nexusmind-data-sources.md`): an old date there is often a standing trap.
