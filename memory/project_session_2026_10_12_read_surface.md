---
name: project-session-2026-10-12-read-surface
description: Session 2026-10-12 — TODO item 2 (#163 read surface) done: 758,893 → ~597,723 chars, surface ratchet, 3 gotcha classes mechanized and 4 catalogue entries retired, TODO backlog archived; belonging 0a step 1 done (c2a re-gate premise fails by construction; judge-boundary question for the owner)
metadata:
  type: project
---

# Session 2026-10-12

**Spend:** $0 oracle. Three Claude review subagents (surface ratchet; close: code-correctness lens, doc-claims lens). No GPU. **Deployed:** nothing. Commits `1a936dd` ..
`84bf683` (12) + two close commits, on main, pushed at close (owner: "merge, push and deploy if applicable"; deploy N/A, no package changed).

## Threads

| Thread | State |
|---|---|
| Step 0: kill-hook transcript replay | ✅ 0 verdict regressions; `test_no_catastrophic_backtracking` was RED at HEAD (8.03 s) — fixed, 0.30 s |
| 2a: 11 hypothesis files | ✅ 261,785 → 131,876 chars, closed blocks moved verbatim to `memory/archive/`; cd-v6-probe, obituary-v4, opinion-genre deliberately NOT moved (corrections amend closed blocks / nothing closed) |
| 2b: filter-status, nexusmind-data-sources | kept: backing CLAUDE.md's table and ⛔ rows; newest-date proxy unsafe for trap-dense files |
| 2c: ratchet | ✅ `check_index_budget.py --target surface`, `SURFACE_CEILING = 611_700`, 7 tests, verify line in `memory/MEMORY.md` |
| 2c: catalogue | ✅ 4 of 11 retired after their classes went live (pkill hook; 402 run-fatal in `score_ollama_oracle.py`; wrong-interpreter banner in `tests/conftest.py`; `prepare_data.py` zero match exits 1 + repo root on `sys.path`) |
| `check_claim_shapes.py` | ✅ skips git-ignored files (33 MB tokenizer.json pushed it to ~112 s vs 120 s timeout) → ~22 s |
| 2d: TODO backlog | ✅ ~12 KB (not 25); 4 boxes + 4 empty headings to `docs/TODO-archive.md` |
| 0a step 1 (belonging) | ✅ gate reproduced 43/63; positives are both-judges `in_scope`, bar class is `out_one_moment` → premise fails by construction. ⚠️ ~9/20 misses look single-person by Claude's NON-blind title read; owner question before step 2 |
| AI Studio Prepay | owner-reported switch recorded; billing and auto-reload NOT checked |
| Cross-session | ovr-news-68 (DeepSeek balance 1.59 after ovr's $3.92): replied nothing in LD needs DeepSeek soon. pipeline-atlas-5d: check inventory sent |

## What I got wrong

- The kill-hook backtracking test was red at HEAD and the prior session's close did not catch it (`caeaa4f` was already
  over budget on `watch`). Caught only because step 0 ran the suite.
- My wrong-interpreter banner fired under the RIGHT interpreter (symlinked venv python); its tests used a
  non-symlink fake. Caught by the close review, not by me.

## Close review (2 lenses)

- Code lens: the wrong-interpreter banner FIRED UNDER `.venv` — `.venv/bin/python` is a uv symlink to an interpreter
  outside the venv and the check resolved it. Fixed (judge by `sys.prefix`), symlink test added. Also: the 402 stop
  covers the DeepSeek path only; Gemini 401/403 still retries 3× per row (noted in the gotcha stub, not fixed).
- Docs lens: 0 lines lost in the moves; one stale ledger description (GN, violence sections "there") corrected.
- GH: progress posted on #163 (the read surface) and #170 (belonging v3 switch).

## Owner calls pending

`H-V8-3` moot now v9 is live?; § *Other Filters*; should `prepare_data.py` refuse a renamed dimension (today: a column of
zeros); the `test_framework_language` failure on a Dutch tab name in `docs/TODO.md` (LD#160, ADR-013, closed); AI Studio auto-reload unconfirmed; 0a judge-boundary question.

Full suite (.venv, at close): 1451 passed, 24 skipped, 1 deselected (`test_framework_language`: red on two pre-existing lines, pre-existing at `37aac9b`).
