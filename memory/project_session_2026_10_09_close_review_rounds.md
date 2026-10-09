# Session 2026-10-09 (later) — the cut-off close, finished: review rounds 2–4 on the deploy guards and the kill-pattern hook

**Ask:** a bare "continue", which meant `docs/TODO.md` ▶ START HERE's first line: fix round 2's three adversarial warnings
(hook anchoring, the LFS-stub conflict between guards D and E, the CLI's NO_HUB-without-adapter exit 0), re-run the
battery, then the close (`/curate`, issue progress posts, the suite baseline). Later, the owner ruled four decisions
through AskUserQuestion: review the hook rewrite once more (an exception to the two-round cap), push after that,
post both issue comments now, and curate now.

## Threads

| Thread | State |
|---|---|
| Round 2's 3 warnings (a hook, b stub, c CLI) | closed — `caeaa4f` |
| Round 3 on the fixes (adversarial; guarantee+doc; reachability+claims) | closed — 1 BLOCKER (exponential backtracking) + 4 warnings, fixed in `caeaa4f` |
| Round 4 on the tokenizer alone (owner exception) | closed — 2 BLOCKERS + regressions, fixed in `b090140`. ⚠️ The round-4 FIXES themselves had no independent review (cap) |
| Push | closed — `caeaa4f`, `b090140` on origin/main |
| LD#163 / LD#134 progress comments | closed — posted (163: 64,590 B net over 4 commits; 134: docs-live 170 now, +1 traced, +1 NOT traced) |
| `/curate` | this file |
| Review-profile suite baseline line (1397 / 24) | open — the profile is a full-depth carve-out file; not edited here |
| docs-live +1 untraced (168 at `483c450` → 170) | open |
| Hook silently off when `CLAUDE_PROJECT_DIR` is unset | open, small |

## What shipped

- `scripts/hooks/block_pattern_kill.py` is a `shlex` TOKENIZER, not a regex (the round-2 regex took 13 s on 25 × `ssh h `).
  Joins `\`-newline, drops cat/tee heredoc bodies (the `"$(cat <<'EOF' …)"` commit idiom), treats redirections as
  non-separators, peels launchers with their option values, re-reads `-c` strings / ssh / watch / `$(…)`. Fails open on
  any internal error. 106 tests; 15 mutants caught across rounds 3–4; 60,000 fuzz inputs, 0 exceptions, worst 2.6 ms.
  Known gaps are listed in its docstring (real backticks, eval, tmux, `kubectl -n`).
- Guard D and `check_adapter_matches_hub.py` refuse an empty / < 1 MB adapter BEFORE hashing (never "re-upload" advice for
  a stub); the CLI checks MISSING before NO_HUB (exit 1, was 0) and says NO PACKAGE (exit 2). Live: belonging v3 and
  human_thriving v9 MATCH, uplifting v7 NO_HUB.
- A review note was itself wrong: 59,745 B is the gotcha log at `d742873`, not `483c450`.
- Suite: 1397 passed, 24 skipped (`.venv/bin/python -m pytest tests/ -q`, 2026-10-09, clean tree at `b090140`).

## Lessons (gotcha log 2026-10-09)

- Replacing a guard's implementation lost positives the old one caught, twice; every test, mutant and fuzz input came from
  the NEW code's model. Fix: a differential run, old vs new on one adversarial corpus. Recorded as the seventh mutation
  direction in the user memory `feedback-articulating-is-not-applying.md`.
- Mention-is-use recurred (x2): the hook refused my own edits to its tests; the Edit tool was the way round.
