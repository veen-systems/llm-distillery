# Session 2026-09-27 (morning–midday): adj4p result, deploy review rounds 2–3, MEMORY.md thinned

**Opening ask:** "continue" → `docs/TODO.md` ▶ NEXT SESSION items 1–4. Later: "what do you recommend?", "is this as
good as it gets?", "help me", CRCD question → hand to the NexusMind peer; then "wrap up … update hypotheses, todo's
and GH issues … merge, push and deploy if applicable", then "we have time and tokens today" (continue after the
checkpoint).

## Threads
| thread | state |
|---|---|
| 1. adj4p diagnostic (b) | ✅ closed: EXP-043, H-TV4 SUPPORTED, README § Diagnostic (b), #151 comment |
| 2. Review round 2 on `054a0a3` | ✅ closed: `675c101`; round 3 (Sonnet, distinct model) on `675c101`: no blocker, 1 warning fixed (remedy: commit the sidecar) |
| 3. #165 finding | ✅ posted; design/ADR itself OPEN (NEXT SESSION 2) |
| 4. Thin `memory/MEMORY.md` | ✅ 14,349 → 10,519 B, `5c0a6f2`; clause-loss lens restored 5 items |
| Thriving adequacy after v7 drains | OPEN, owner's call: H-TV5 |
| Venezuela 7-article cluster | NOT OURS: NexusMind PR #542 handoff (story grouping, not dedup; PROP-8 pinning live 09-27 won't group it) |
| Deploy | N/A: nothing shipped to NexusMind changed; the deploy-script change is llm-distillery tooling |

## Measured
- adj4p (b650 CUDA, seed 42, best epoch 3): pool recall 0.933 [0.933, 0.933] / spec 0.860 [0.860, 0.900]; 660 adjudicated
  0.522 / 0.994; 660 oracle 0.371 / 0.995; flagged 3: 2.853 / 1.911 / 1.360 (all < 4.5). v9/adj4 reproduced 09-26 exactly.
- Live `ovr.news/search-index.json` ~11:30 CEST: 2,959 articles; thriving 706, belonging 747, discovery 701, solutions
  683, recovery 122; dates 09-17 → 09-27 (publication dates, not surfacing dates; the index does not say which model).
- Round-2/3 reviews: 4 then 0 surviving guard mutants; now 7/7 wiring mutants caught. Unit suite 988 passed, 17 skipped.

## Cost
$0 oracle. b650 GPU ~52 min (shared with a roofvision job from ~10:13).

## Left on machines
- b650: `filters/human_thriving/v8_adj4p` and `runs/human_thriving_v8_adj4p` (untracked; `rm -rf` to undo), as `v8_adj4`.
- local: `datasets/gate/ht_v10_2026-09-26/adj4p_*` (gitignored); `/tmp/claude-1000/si.json` and review scratch dirs.

## Afternoon (after the midday checkpoint, owner: "we have time and tokens today")
| thread | state |
|---|---|
| Retire step 3 (TODO −1) | ✅ `13045c9`: ledger 146,560 → 83,641; cross-repo 136,125 → 61,087; contracts plan 149,056 → 56,931 B. Independent lossless checker (mutation-tested); a review lens caught a reproduce command silently printing 0 (then 13 ≠ 17 until it read both files) and open contract items that had moved to the archive (moved back) |
| #165 → ADR-024 | ✅ drafted PROPOSED, `7c0712c`; Sonnet review: all facts held, 3 warnings fixed. ⭐ Production filters do not load from the Hub either (`use_hub=False`, `HF_HUB_OFFLINE=1`). Needs the owner's ruling + 5 questions |
| `/update-drift` | ✅ v1.49.0 → v1.49.2, both already in force, `a6cd7cf` (owner said "go") |
| `check_claude_md_trim.py` (TODO −1 step 4) | ⛔ REJECTED with evidence, `0ccbf14`: ≤ 2/3 seeds at 52/125 false flags |

Measured: curate read surface 1,486,729 → 1,355,588 chars (the gotcha log, ~250k, is the largest left).
⛔ Mine: my first `curate` marker grep used a regex where I meant a literal string and returned 0 for a present
marker. The first trim-check extractor saw only BOLD imperatives, and today's `CLAUDE.md` states the ADR-015
rule unbolded. The evidence script broke when it moved folders.
