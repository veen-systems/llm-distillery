---
name: project_session_2026_09_26_update_drift
description: /update-drift v1.45.1 → v1.49.0 — four adopt items landed, CLAUDE.md thinned 38.1k → 17.7k, retiring mechanized, two review rounds
metadata:
  type: project
---

# Session 2026-09-26 (afternoon) — `/update-drift` to v1.49.0, and the read surface thinned

**Spend:** $0. No oracle, no GPU. **Deploy:** N/A — no filter, `filters/common/` or NexusMind-bound file changed.

## The ask, and the threads

1. **`/update-drift`** — ✅ closed. v1.45.1 → **v1.49.0**, 5 releases. v1.49.0 was released mid-triage (tag 11:27:00), and the global skills were reinstalled from it at 11:27:06. Record: `docs/decisions/framework-adoption-history.md` § 2026-09-26.
2. **Owner steer, mid-session.** Rank framework work by token reduction: less harness verbosity and doc bloat, retirement to archives, mechanization, English only. ✅ Applied as the triage priority.
3. **"fix it all"** — ✅ closed. All four adopt items landed, then the stamp was bumped.
4. **Wrap up, curate, commit, push; deploy if applicable** — ✅ in this session. Deploy is N/A.

## What landed

- **`check_framework_stamp.sh`** reads the skill list from `GLOBAL_SKILLS` in the installer at the stamped tag (upstream #200). 28 tests.
- **`scripts/maintenance/retire_memory.py`** retires by heading DATE, both ISO and `(Feb 2026)`. Upstream's `[RESOLVED` prefix would have moved 1 of the 15. It has 18 tests, and 12 mutants were killed over two review rounds.
  - 79 pre-September session files moved to `memory/archive/`.
  - 15 Feb–May gotcha entries moved to the gotcha archive.
  - Archived session probes still run under `run_verify_annotations.py --sessions`.
- **`CLAUDE.md` 38,141 → 17,749 chars.** The frontmatter now holds only the stamp; its operative rules moved verbatim to the history file. The one rule that must govern every session (user-global skills: never re-create local copies) is now a sentence in the loaded body.
  - Closed **llm-distillery#122** (frontmatter never loads). This session confirmed it: the loaded copy began at `# CLAUDE.md`.
- `memory/filter-status.md`'s cd v6 row no longer claims "no normalization.json" (it was fitted on 2026-08-08, `4ee3b58`).

## Review

`/review-changes`, HIGH tier.

**Round 1** ran 6 lenses: guarantee-preservation, adversarial, doc-accuracy, shell-correctness, reachability and claim-verification. sync-safety did not fire. It found 1 blocker and about 12 warnings:
- the "0 `[RESOLVED`" claim, which was false;
- a lossless check that was equal by construction;
- five operative clauses dropped from `CLAUDE.md`;
- a false "cd v6 cannot score";
- archived probes that stopped running without any message.

**Round 2** ran 2 lenses: adversarial and doc-accuracy. It found 1 blocker, which my round-1 fix had introduced: a moved file could be resurrected at its old path. It also found:
- a half-rewritten glob command;
- inline triple backticks being read as a fence;
- `../memory/` links the rewrite missed;
- a stale noise-floor clause (0.1956 and "CUDA→CUDA unmeasured" are both superseded).

All of it is fixed. The shapes are in `memory/gotcha-log.md` (2026-09-26 entry) and in § Mechanized (2 live rows, 1 proposed).

**Verified:**
- `.venv/bin/python -m pytest tests/ -q`: 983 passed, 25 skipped.
- Doc claims 7/7; `check_framework_stamp.sh` exit 0; the budget and filter-table checks pass.
- verify-runner: 40 of 73 annotations ran and all passed; 11 are manual.

## Open

**Next is item −1 in `docs/TODO.md`:** move `memory/gotcha-log-archive.md` into `memory/archive/` (curate still counts its 467k), then thin `memory/MEMORY.md`.

**Tracked as `H-CTX-3`:** whether the `CLAUDE.md` trim loses behaviour in use.
