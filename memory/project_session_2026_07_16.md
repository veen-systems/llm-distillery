# Session 2026-07-16 — #62 check clean, cap retirement confirmed, round-3 fixes HELD after round-4

## Real wins (shipped/verified)

- **#62 discovery-lens leakage check DONE — cd v5 HOLDS, no leak.** Ran the generalized
  version (the 5 original May examples aren't in the live 10-day window, so scanned for
  their *shape*): harm-reckoning/apology/restitution/colonial-reckoning detector over all
  80 cd v5 batches on sadalsuud (151,210 unique v5 articles). **624/649 harm-reckoning
  articles (96%) suppressed below raw 3.5**; genuine apology/reparations content scores
  0.67–1.81 via *learned dimension scores* (discovery_novelty + cross_cultural near zero),
  NOT a hard cap (`gatekeeper_applied: False` on all). One medium-tier edge case
  (Rijksmuseum Holocaust *displays*, raw 4.73) is a museum-exhibition piece, legitimately
  Discovery-adjacent per ADR-015. No `cd_v6_leakage_candidates.jsonl` needed; cd v6 (#23)
  stays a note. Committed `a17bf6e`. Scan scripts in scratchpad (`cd62_tight.py`, `cd62_detail.py`).
- **climate_doom cap retirement behaviorally confirmed.** `cap_applied` cutover exactly as
  predicted: 16:40 batch = 1 (pre-retirement, legit), 20:37 batch (first post-20:08 deploy)
  = 0, every batch since = 0. Both open prio-list verifications now closed.
- **Re-enchantment outlets exploration PARKED** (Byung-Chul Han-inspired divergence) —
  `docs/ideas/re-enchantment-outlets.md`, committed `5ffb01c`. Standalone oracle-only outlets
  are now a sanctioned destination for new lens ideas ([[project-standalone-outlets-direction]]).

## The round-3 → round-4 story (the pattern held a FIFTH time — on me)

The 2026-07-14 handoff pushed for a **round-3 review** of round-2's normalization/deploy fixes
(each prior round found defects in the last round's fixes). I ran it. It found real defects,
I fixed them (llm-distillery `a8309d4`, NexusMind branch `7e525ee`), and **verified each by
watching it fail on bad input**. Then, before pushing, I ran a **round-4 review of MY OWN
round-3 fixes** — and it found defects in them too, including a production-halting regression.

**DECISION: neither round-3 fix was pushed/merged. Both HELD for a focused hardening session.**
Rationale: no currently-deployed filter is affected (all 10 conform to within 0.0006 of
op-point), so zero production cost to holding; and the findings point to cleaner ROOT fixes,
not more inline patches.

### NexusMind `7e525ee` — actively harmful, do NOT merge
Changed the deploy dirty-check `git diff --quiet HEAD` → `git status --porcelain`. Round-4:
- **Production-halt regression (CONFIRMED, reproduced live).** `.gitignore` ignores only
  `*.safetensors` + tokenizer files INSIDE `model/`, NOT the dir. So porcelain flags an
  untracked `generation_config.json`/`config.json` under any `model/` dir and BLOCKS the
  deploy. This runs as `nexusmind.service` ExecStartPre every 4h; a fresh `model/` dir with
  untracked config (a normal filter-version bump) → scorer never starts → production scores
  zero. Old `git diff HEAD` returned rc=0 on the same state. My fix trades a rare latent
  silent-wrong-deploy for a common active halt — strictly worse. (My code comment claiming
  gitignore shields `model/` is false.)
- Sibling auto-pull guard (line 64) still uses `git diff HEAD` — two guards disagree.
- Fail-OPEN on git error (old was fail-closed); defeated by `status.showUntrackedFiles=no`.
- Also: rsync excludes are NARROWER than .gitignore, so gitignored files under `filters/`
  (DEEP_ROOTS.md, training_metadata.json, prompt-compressed.md, …) are shipped by rsync yet
  omitted from the CODE_REVISION hash — a *different* in-sync-is-a-lie gap for gitignored paths.

### llm-distillery `a8309d4` — net-positive but not ready, do NOT push
Changed the invariant test upper bound 4.5 → op_point+0.25 (via `_within_invariant` helper)
+ fitter pre/post-fit guards. Round-4:
- Fitter's own deploy-path write-guard STILL keys on flat 4.5, not op_point+margin — it
  writes a file the test would reject (fitter/test inconsistent; I fixed the test only).
- My "`--out` = analysis, never deploy" assumption is FALSE — `--out` can point at the
  package itself, defeating both new guards.
- **The 0.25 margin can false-positive a legitimately SPARSE needle fit** — exactly what the
  imminent nature_recovery v5 normalization (#72) will be (lowest article may sit >0.25 above
  a low op-point). Shipping 0.25 now would block the very next normalization job.
- `#205` error message wrong for the `>4.5` case (says "accepted+clamps"; loader REJECTS it).

## Candidate ROOT fixes for the hardening session (not inline patches)

1. **Normalization:** ANCHOR the CDF's lower edge to op_point in the fitter (`fit_normalization`),
   so `stats.raw_min == op_point` deterministically. This DISSOLVES the entire margin question
   (0.25 vs 4.5 vs sparse-fit jitter) and makes fitter-guard and test-invariant trivially
   consistent. Then the test can assert near-equality without false-positiving sparse fits.
2. **Deploy guard:** align dirty-check + CODE_REVISION hash + rsync to ONE definition of the
   deployed set. Options: deploy via `git archive` of HEAD (ships exactly what's hashed), OR
   build the hash from rsync's actual shipped file list. Either dissolves both the
   untracked-file AND gitignored-file gaps. Until then, the round-2 `git diff HEAD` stays
   (rare latent gap) — better than the porcelain halt.

Full round-4 findings: task outputs `ww59k1uwh.output` (NexusMind, 6 findings) and
`wcs9cbopi.output` (llm-distillery, ~7 findings) in the session tasks dir.

## Held-branch state
- llm-distillery: `nature-recovery-v4` carries `a8309d4` (held) — UNPUSHED. Do not merge to
  main until the hardening session resolves the margin + fitter/test consistency.
- NexusMind: `fix/deploy-dirty-check-untracked` (`7e525ee`, held) — UNMERGED. `main` stays at
  the stable `7ef6029`. Do not merge; the real fix is different (align deployed-set), so this
  commit is a reference, not a foundation.
