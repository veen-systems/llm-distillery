# Normalization + Deploy-Guard Hardening — Fix Plan

**Status:** BOTH FIXES EXECUTED. Fix A 2026-07-16 (review-hardened, merged). Fix B 2026-07-17
(git-archive staging, 52-assertion dry-run harness, 3-model round-5 review, merged `dcf6fc8`,
deployed + validated live through the canonical ExecStartPre chain — see the addendum inside
Fix B for the live evidence and remaining follow-ups).
**Held-branch note:** both holds RESOLVED. llm-distillery: anchor root fix superseded `a8309d4`'s
margin; branch merged to main. NexusMind: `fix/deploy-dirty-check-untracked` (`7e525ee`) was
superseded by Fix B and DELETED 2026-07-17 (recoverable from the sha).
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

### EXECUTED 2026-07-16 — result addendum

Anchor implemented as a PREPENDED breakpoint `(op_point, 0.0)` (not a re-spanned grid), so the
original 200-point lookup grid stays bit-identical and anchoring is provably inert for every
score >= the sample minimum. All four gates ran:
(1) all 10 filters green under restored near-equality (`EPS = OP_POINT_EPS = 0.01`, single-sourced
    from the fitter; margin deleted); (2) sparse fixture anchors to 3.75 and passes in-repo;
(3) synthetic drift at 4.3 / 5.01 / 1.5 each fails with the regime-correct message;
(4) **gate 4 as originally worded is unsatisfiable** — byte-identity with a committed file is
    impossible for ANY code because the production reference window rolls (26 new cd v5 articles
    in 6 days moved the curve up to 0.195 normalized — 44x the code change's max effect). The
    code-isolating form ran instead: old-vs-new fitter on one identical live cd v5 pull → old
    grid bit-identical as suffix, behavioral delta 0 for scores >= sample_min, <= old-y[0]
    (0.0044) below it, deterministic.

A 3-model review battery (opus/correctness, sonnet/contract, fable/adversarial-ops) then found
11 findings; all verified ones fixed same-session. The important one (adversarial): anchoring
made gross biased-sample fits (#205 root cause, sample_min > 4.5) LOADABLE where the pre-anchor
fitter hard-blocked them → restored as a deploy-path gate on `stats.sample_min > 4.5` + the same
assertion in the invariant test. Also: deploy-path fits now REQUIRE a resolved op-point;
`--allow-below-op-point` / `--all-versions` / `--allow-thin-fit` all require `--analysis-only`
(whose --out must not be, or resolve to, a `normalization.json`); `--out` cannot retarget another
package; NaN scores excluded at load; loaders match only the filter's own attribute block
(hyphen/underscore-normalized: config says `cultural-discovery`, production writes
`cultural_discovery`). Residual accepted gap: a SUBTLY biased sample (sample_min <= 4.5, gap <=
0.5 above op-point) is indistinguishable from a legitimately sparse needle fit in the data —
recorded as `stats.sample_min` for audit, >0.5-gap advisory warning, representativeness stays an
operator check (playbook §6).

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

### EXECUTED 2026-07-17 — merged (`dcf6fc8`), DEPLOYED, validated live

Sign-off sequence ran same-day after user approval ("ok!" to the recommended order):
- **Pre-deploy checks both CLEAN.** sadalsuud: HEAD=7ef6029, zero untracked/dirty under deploy
  paths. Archive-staged `--delete` dry-run vs gpu-server: NOTHING deleted (three
  `cannot delete non-empty directory` warnings for retired versions whose exclude-protected
  model dirs block dir removal — pre-existing, non-fatal, rc=0).
- **Prompt-file decision MOOT:** sadalsuud has NO prompt-compressed.md/prompt.md in its tree, so
  the old rsync never shipped them — `prompt_hash` was already null in production; nothing to
  fold, nothing regressed. (Only prompt file on gpu-server is sustech v2's
  prompt-compressed-backup.md, which is tracked and ships.) Un-ignoring stays future hygiene for
  the next filter package that carries one.
- **Merged** ff-only to main (`7ef6029..dcf6fc8`), pushed. Manual watched deploy on sadalsuud:
  staging + both rsync passes + hash round-trip (`6f0458f3…`) all green; smoke then hit
  connection-refused mid-run — NOT a crash: the 16:08 pipeline cycle's ExecStartPre (new script)
  stopped/restarted the scorer under the manual run's smoke. Benign deploy-vs-timer race.
- **Definitive validation came from the canonical chain itself:** the 16:08:55 unattended cycle
  ran the new script as ExecStartPre → `status=0/SUCCESS`, all smoke fixtures passed, gpu-server
  `CODE_REVISION = 6f0458f3… @ 16:08:58`, `/health` healthy on CUDA.
- Cleanup: held branch `fix/deploy-dirty-check-untracked` (7e525ee) DELETED (superseded;
  recoverable from the sha recorded here); merged branch + worktree removed.
- **Follow-ups: ALL CLOSED same-day (user: "do the follow-ups and action too").**
  1. **Alert LIVE:** `OnFailure=nexusmind-alert@%n.service` drop-in on `nexusmind.service` +
     handler `scripts/alert_failure.sh` (NexusMind `395326c`, reworked `29fe798`) → **EMAIL via
     the chain's existing Gmail sender** (FluxusSource `[email_credentials]` on sadalsuud;
     engineer: "I do not want more services" — the initial ntfy.sh channel was retired same-day)
     + append to `data/alerts.log`; 3h burst guard armed only on confirmed send. Installed,
     self-tested end-to-end (delivery confirmed to the engineer's inbox). Best-effort, exits 0.
  2. **RUNBOOK updated** (§4 deploy): stale bullets fixed (full SCORER_PATHS, archive staging,
     push-completeness, per-fixture smoke bounds) + committed-only-deploys warning block.
  3. **Carve-out decision SETTLED BY EVIDENCE — stays.** One-time sha256 diff of all 36 tracked
     `*/model/` files vs gpu-server: ~half missing or differing (mostly READMEs / parked or
     superseded versions, but incl. a real content mismatch on foresight v1 adapter_config.json).
     Shipping repo copies would overwrite Hub-provenance files with drifted tracked copies —
     hashed-but-not-shipped remains the correct, documented behavior. Revisit only if the
     tracked copies are ever re-synced from the actual Hub pushes.

### Original implementation record (pre-sign-off)

**Decision: option 1, git-archive staging.** `git archive HEAD -- <SCORER_PATHS>` is extracted
to a mktemp staging dir (trap-cleaned) and every rsync/scp sources from it — the "loses
rsync `--delete`" caveat dissolves because rsync runs from the extracted tree. The two-pass
rsync structure survives unchanged (pass-1 `--delete` must keep excluding `model/`+`models/`:
gpu-server holds out-of-band LoRA weights under `*/model/` AND out-of-band safetensors next to
tracked pkls under `*/models/`). Option 2's untracked gate is included anyway as an
operator-intent guard (under archive, untracked files silently DON'T ship — the inverse wrong-deploy).
Branch: NexusMind `fix/deploy-set-git-archive` (`dcf6fc8`, off `main` 7ef6029). The held
`fix/deploy-dirty-check-untracked` (`7e525ee`) is superseded — delete after merge.

All round-4 checklist items closed: shared dirty definition between auto-pull guard and main
gate; no porcelain anywhere (`git ls-files` is config-independent); fail-CLOSED on git error via
sentinel; `|| true` diagnostics kept. Beyond the plan: push-completeness assertion (every
SCORER_PATHS entry must record itself shipped — a staged-but-never-pushed entry deployed green
in review round 5, now fails loudly); smoke fixtures moved into SCORER_PATHS and shipped from
staging; component-form rsync excludes (depth-1 `filters/model(s)/` was deletable while the gate
called it protected); `.gitignore` `models/` scoped to `/models/` (bare form made NEW prefilter
pkls silently un-addable + invisible to the gate — the #67 silent-503 shape).

**Verification:** 52-assertion dry-run harness in a scratch clone (session scratchpad `fixb/`),
real rsync against a fake remote with planted out-of-band weights — all three plan gates plus:
auto-pull-path variants of (a)/(b), git-failure fail-closed in both gates, depth-1 model-dir
survival, gitignored-straggler removal, staging-leak checks, hash recomputation post-auto-pull.
**The pattern held a SEVENTH time:** a 3-model review battery (correctness / adversarial-ops /
contract) on the freshly written fix found 7 verified defects (incl. two false "by construction"
comments and the swallowed GIT-ERROR sentinel); all fixed + re-harnessed same session.

**Pre-deploy checklist (sign-off gates):**
1. On sadalsuud: `git ls-files --others --exclude-standard -- filters/ src/filters/ src/scoring/ deploy/`
   must be clean (any file-copied-but-uncommitted filter package now BLOCKS every 4h cycle — by design).
2. On sadalsuud: run pass-1 rsync with `--dry-run --delete -v` against gpu-server and eyeball the
   deletion list (first archive deploy removes previously-shipped strays; runtime read-set audit
   says all enabled filters' artifacts are tracked, but gpu-server-only strays are unverifiable
   from the dev machine).
3. Decide `prompt-compressed.md`: recommended un-ignore + commit for deployed filters (it is
   runtime-read by `_compute_prompt_hash`; otherwise first deploy nulls `prompt_hash` provenance).
4. Decide tracked `*/model/` configs: currently hashed-but-never-shipped (documented carve-out,
   recommended status quo); closing it needs a one-time gpu-server config diff first.
5. RUNBOOK note + ideally an alert on `nexusmind.service` start failure (fail-closed gate means
   halts are now the failure mode, and they repeat every 4h unattended).

---

## Recommended order
Fix A first (self-contained, no production runtime, easy full verification), then Fix B (higher
stakes, needs the dry-run harness). Neither blocks solutions v4 (#43), which remains the primary
product goal — do whichever fits the session's appetite.
