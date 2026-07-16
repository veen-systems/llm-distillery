# Normalization + Deploy-Guard Hardening — Fix Plan

**Status:** READY TO EXECUTE (next session). Written 2026-07-16 while context was fresh.
**Why a plan, not a patch:** rounds 2→3→4 each found defects in the prior round's fixes,
including a production-halt regression in my own round-3 fix. These are ROOT fixes, done
with fresh context + full verification — not more inline patches under end-of-cycle pressure.
**Held branches (do NOT merge as-is):** llm-distillery `nature-recovery-v4` carries `a8309d4`;
NexusMind `fix/deploy-dirty-check-untracked` carries `7e525ee`. Both are references, not
foundations. Full findings: `memory/project_session_2026_07_16.md` + task outputs
`wcs9cbopi.output` (llm-distillery, ~7 findings) / `ww59k1uwh.output` (NexusMind, 6 findings).

---

## Fix A — Anchor the normalization CDF to op_point (llm-distillery)

**Root problem:** `raw_min` floats to the empirical *sample minimum*, which creates the whole
margin ambiguity (0.25 vs 4.5) and the #205 clamp risk. A sparse needle fit whose lowest
article sits above op_point both false-fails the test AND clamps the [op_point, raw_min) band.

**Root fix:** in `fit_normalization()` (`filters/common/score_normalization.py`), anchor the
CDF's lower x-edge to op_point — extend so `x[0] == op_point` regardless of the sample's actual
minimum. Then `stats.raw_min == op_point` deterministically, and the ambiguity disappears.

**Then, downstream (mostly reverting my round-3 complexity):**
- `test_normalization_invariant.py`: restore near-equality `abs(raw_min - op_point) < EPS`;
  DELETE `ABOVE_OP_POINT_MARGIN` (no longer needed). Keep the `_within_invariant` single-helper
  shape so both tests still can't drift.
- `fit_normalization.py`: pre-fit AND post-fit guards key on op_point consistently. **Fix the
  `--out` semantics** — round-4 proved `--out` can point AT a package `normalization.json`, so
  "`--out` = never deploy" is FALSE. Either add an explicit `--analysis-only` flag, or have the
  guard check whether the output path is a package file. Guards must not be bypassable by `--out`.
- Fix the `#205` error message: it must correctly describe BOTH regimes — op_point+ε..4.5
  (loader ACCEPTS, silently clamps) and >4.5 (loader REJECTS at load). My round-3 message
  wrongly said "accepted" for the >4.5 case.
- Fix the self-contradictory "Refit at --min-score {op_point}" advice when op_point itself >4.5
  (point at fixing base_scorer TIER_THRESHOLDS instead).

**Verification gates:** (1) invariant test green on all 10 deployed filters (they already conform);
(2) a synthetic SPARSE fixture (lowest article 4.05, op 3.75) now ANCHORS to 3.75, not false-fail;
(3) a synthetic #205 drift still caught; (4) re-fit one real filter and confirm identical output
to its committed normalization.json (no behavior change for dense fits).
**Blast radius:** fitting logic (future refits) + test + tooling. No production runtime. MUST
re-verify existing filters produce unchanged CDFs.

---

## Fix B — One definition of "the deployed set" (NexusMind)

**Root problem:** three mechanisms each define "what gets deployed" differently →
- dirty-check: `git diff HEAD` (tracked only) or my `git status --porcelain` (respects .gitignore)
- CODE_REVISION hash: `git rev-parse HEAD:<path>` (tracked HEAD only)
- rsync: working tree minus `*/model/`, `*/models/`, `__pycache__/`, `*.pyc`
Gaps: untracked non-ignored files ship but aren't hashed/caught (the round-3 bug); gitignored
files under `filters/` ship via rsync but aren't hashed (round-4 finding #2); and my porcelain
guard HALTS on untracked `model/` config files (production-halt regression, round-4 #1).

**Root fix — decide in-session between:**
1. **Deploy via `git archive HEAD`** (ship exactly what the hash names). Cleanest: hash and
   deploy become the same set by construction. Caveats: loses rsync `--delete`; the out-of-band
   `model/` weights (gitignored, pushed separately) and the in-git `models/` pkls (second rsync
   pass) must still be handled — archive won't include gitignored paths (correct for LoRA
   weights, but verify the committed prefilter pkls still ship).
2. **Interim (lower risk):** restore round-2 `git diff HEAD` (kills the porcelain halt), then add
   an EXPLICIT untracked check that mirrors rsync's excludes:
   `git ls-files --others --exclude-standard -- <paths>` filtered to drop `*/model/`, `*/models/`,
   `__pycache__/`, `*.pyc` — fail-closed. Catches an untracked `src/scoring/*.py` but NOT a
   `model/` config file. Keep the exclude list in ONE place shared with the rsync command.

**Regardless of option, also fix (round-4 findings):**
- Sibling auto-pull guard (line ~64) still uses `git diff HEAD` — make it consistent.
- Pin `git status --untracked-files=normal` (config-independent) if porcelain is used anywhere.
- Fail-CLOSED on git error (my version fail-opens via empty command substitution).
- Restore `|| true` on the diagnostic `git status --short` (nonzero under `set -e` aborts wrong).

**Verification gates (NEVER let this run live-untested as ExecStartPre):** dry-run
`deploy_filters.sh` in a scratch clone and confirm — (a) untracked `src/scoring/*.py` → BLOCKS;
(b) untracked `model/generation_config.json` → does NOT block; (c) clean tree → deploys and the
round-trip hash matches. Only after all three, deploy through the canonical chain.
**Blast radius:** production deploy path. HIGH.

---

## Recommended order
Fix A first (self-contained, no production runtime, easy full verification), then Fix B (higher
stakes, needs the dry-run harness). Neither blocks solutions v4 (#43), which remains the primary
product goal — do whichever fits the session's appetite.
