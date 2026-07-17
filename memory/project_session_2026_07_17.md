# Session 2026-07-17 — Wrap-up: review battery over Fix A, five findings fixed, curation

Short session: no new feature work. Ritual wrap-up of the 2026-07-16 Fix A session — the tree
was already clean and pushed (`main` == `nature-recovery-v4` == `a301e2b`), so the reviewable
unit was the merged range `ad1a7b9~1..a301e2b`.

## Review battery (11 agents: 3 lenses × distinct models + adversarial verify + live pytest)

Lenses: correctness (Fable), test-adequacy (Opus), docs-consistency (Sonnet); every finding
adversarially verified by an independent Opus skeptic. 5 confirmed, 2 refuted, all fixed:

1. **`--n-bins 0/1` → degenerate guard-green deployable table** (correctness, low). Anchoring
   pins `raw_min` to the op-point regardless of table shape, so a typo'd `--n-bins 1` wrote a
   loadable file normalizing the whole lens to ~0.02 with every guard green. Fixed: `n_bins < 2`
   fails closed in `fit_normalization()` (ValueError) AND the CLI (logger.error + exit 1).
2. **`sample_min` assertion was dead code in CI** (test-adequacy, medium). All 10 committed
   normalization.json are legacy pre-anchor (no `stats.sample_min`), so the one guard catching
   the #205 root cause for anchored fits never executed. Fixed: synthetic-package tests drive
   the REAL parametrized test body both ways (fires above `MAX_RAW_MIN`, passes below).
3. **"8 of 10 deployed filters sit at 4.0" comment** — real count is 10 of 10 fitted packages
   (only nature_recovery v4, unfitted, sits at 3.75). Corrected.
4. **ADR-014 schema block stale** — omitted `method`/`filter_name`/`filter_version`/`stats{}`
   while referencing `stats.sample_min` in the same sentence. Corrected to the real schema.
5. **FILTER_PLAYBOOK "7 of 9 fitted files"** → "7 of 10 (the other 3 are incident exemptions)".

Refuted by verifiers (correctly): "anchor breakpoint skipped when an article scores exactly at
the op-point" (only reachable via synthetic input the deploy path can't produce) and "invariant
doesn't cover live nature_recovery v4" (v4 has no normalization.json yet — #72; glob-based test
picks it up the moment one exists).

**Tests: 196 passed, 3 skipped** (was 194 + the 2 new synthetic-package tests).

## Framework drift check

- llm-distillery adopts **agent-ready-projects v1.10.6 = latest** (clone in sync with origin). ✓
- **agent-ready-papers latest is v2.3.1** (clone in sync). Not adopted here; adopters elsewhere:
  `brainstorm/vlonder` pinned **v1.3.0 (adapted)** — well behind; `essays_on_the_priesthoods`
  unversioned minimum-viable. Surfaced only (their own policy: don't auto-update).
- Stray: `~/repos/agent-ready-papers` has an uncommitted edit to
  `literature/sources/vrijenhoek-2021.md` (+29/−13). Left untouched.

## Curation / verify battery

- Local verify assertions: 12 PASS, 1 manual-check (filter-status vs CLAUDE.md table diff —
  schemas differ by design; content consistent on inspection), SSH-based checks ERROR from this
  workstation (no gpu-server route — known situla-class limitation, honest ERROR).
- **uplifting v7 verify rewritten**: old command probed `C:/local_dev` (stale Windows path) and
  the gitignored local `model/`. Now probes gpu-server (the actual deployment claim).
  **Finding for the engineer**: v7 weights are NO_HUB and absent from both repos on this Linux
  machine — only copies are gpu-server + the old Windows box. Consider a backup.
- Gotcha log: one new entry (dead-control recurrence, see log 2026-07-17); no unresolved
  lingering entries.
- CLAUDE.md at 12k chars — far under budget; no footer accretion.

## Carried state (unchanged from 2026-07-16 pickup)

- NexusMind **Fix B** is the next cross-repo job (held branch `7e525ee` reference-only, main at
  `7ef6029`); dry-run harness in a scratch clone, never live as ExecStartPre, sign-off required.
- **solutions v4 (#43)** remains PRIMARY (ADR-020 validation case); oracle batch off-peak.
- **#72** v4 normalization refit unblocked by Fix A but still blocked on data (needs the
  production-representative historical rescore, playbook §6).

## Addendum (same day, second wrap-up)

- **sustech v3 op-point drift FIXED** (`65484f4`) — the last cheap 2026-07-14 follow-up. config
  `tiers` now mirrors `TIER_THRESHOLDS` (medium 4.0; phantom `medium_high: 5.0` removed; both
  stale "3.0" gatekeeper comments corrected). Verified: `resolve_op_point` → 4.0, no drift
  warning; 196 tests green. Consistency sweep confirmed no consumers: commerce_prefilter's
  `medium_high` reference is historical training-data sourcing doc; v3 `inference_hybrid.py`'s
  membership check harmlessly includes the never-emitted name (diagnostic path; ADR-016 dropped
  tiers anyway). Deployed config copies inert, sync at next filter push.
- **#44 commit-msg hook earned its keep**: "deploy"-class word in the first commit message
  triggered full filter verification (Hub check → honest ERROR on this machine); resolved by
  softening the message, not `--no-verify`.

---

# Session 2026-07-17 (afternoon) — Fix B EXECUTED end-to-end: decided, built, reviewed, deployed, validated live

The deploy-hardening arc (2026-07-14 → today) is CLOSED. Everything below happened in one
session with explicit engineer sign-off gates ("ok!" to the recommended sequence; "do the
follow-ups and action too").

## What shipped (NexusMind `7ef6029` → `f6497fa`)

- **Decision: git-archive staging (plan option 1).** The "loses rsync --delete" caveat dissolved
  once the archive is extracted to a staging dir and rsync runs FROM it. Recon that shaped it:
  gpu-server's `filters/*/models/` holds out-of-band safetensors NEXT TO tracked pkls, and
  `*/model/` holds out-of-band LoRA weights next to tracked configs → the two-pass rsync
  structure and both excludes had to survive verbatim.
- **`dcf6fc8` — the fix.** `git archive HEAD -- SCORER_PATHS` → mktemp staging (trap-cleaned) →
  all rsync/scp source from staging. Untracked operator gate (`git ls-files --others
  --exclude-standard` filtered to exempt only `filters/**/model/`) shared by the auto-pull guard
  and the main gate; fail-closed on git error via sentinel with git-failure-specific messages;
  runtime push-completeness assertion (every SCORER_PATHS entry must record itself shipped);
  smoke fixtures moved INTO SCORER_PATHS and shipped from staging; rsync excludes switched to
  component form (`model/` not `*/model/` — depth-1 dirs were deletable while the gate called
  them protected); `.gitignore` `models/` scoped to `/models/` (bare form made new prefilter
  pkls silently un-addable — the #67 silent-503 shape, invisible to `git add`).
- **Verification: 52-assertion dry-run harness** (scratch clone pair + fake remote + ssh/scp
  shims; rsync REAL so --delete/--exclude semantics were genuinely exercised). All three plan
  gates + auto-pull variants of each + git-failure paths + planted out-of-band weights surviving
  --delete at every depth + gitignored stragglers removed + hash recomputed post-auto-pull.
  Preserved as a permanent fixture: `NexusMind/tests/deploy_dryrun/setup_and_run.sh` (`f6497fa`),
  validated green from its repo location.
- **The pattern held a SEVENTH time.** 3-model round-5 battery (correctness / adversarial-ops /
  contract) on the freshly harness-verified rewrite found 7 verified defects, all fixed +
  re-harnessed: two false "by construction" comments (one became the push-completeness
  assertion), swallowed GIT-ERROR sentinel in the auto-pull branch (git failures misdiagnosed as
  dirty trees), depth-1 exclude/gate contradiction, bare-`models/` gitignore trap, plus the
  hashed-but-never-shipped tracked model configs surfaced as a documented carve-out.
- **Deploy + live validation.** Sign-off checks both clean (sadalsuud untracked: empty; --delete
  dry-run: nothing deleted). Merged, pushed (via gh https — ssh key has no askpass in agent
  shell), pulled, manual watched deploy: hash round-tripped, then smoke "failed"
  connection-refused — NOT a crash: the 16:08 timer cycle's ExecStartPre stopped the scorer
  mid-smoke (deploy-vs-timer race, new gotcha entry). The canonical chain then validated the
  whole thing unattended: ExecStartPre status=0/SUCCESS, all fixtures green, gpu-server
  `CODE_REVISION=6f0458f3… @16:08:58`. Held `7e525ee` deleted.

## Follow-ups (all closed same-day)

1. **OnFailure→ntfy alert LIVE** (`395326c`): `nexusmind-alert@` template + best-effort handler
   (ntfy topic in gitignored `config/credentials/ntfy_topic`; also appends `data/alerts.log`).
   Installed, daemon-reloaded, self-tested — message verified delivered on the topic.
   **Engineer must subscribe** (see MEMORY pickup).
2. **RUNBOOK §4 updated**: stale bullets fixed + committed-only-deploys warning block.
3. **Model-config carve-out SETTLED BY EVIDENCE**: sha256 diff of all 36 tracked `*/model/`
   files vs gpu-server → ~half missing/differing (incl. foresight v1 adapter_config.json content
   mismatch). Shipping repo copies would overwrite Hub-provenance files → hashed-but-not-shipped
   stays, documented in-script. Revisit only if tracked copies are re-synced from Hub pushes.

## Incidental

- fluxus-{health,collection}.timer executable-bit warnings fixed on sadalsuud (chmod 644).
- Surfaced: sadalsuud `config/app.yaml` has uncommitted `healthcheck.enabled: true→false` (#91
  dead-man's switch disabled locally) — engineer to confirm intent.
- prompt-file question answered by production state: sadalsuud never had prompt-compressed.md /
  prompt.md → old rsync never shipped them → `prompt_hash` already null in production; the
  Fix B "deletion regression" concern was moot.

## Post-close addendum — alert channel swapped to email (engineer feedback)

"I do not want more services, I get health checks and emails from the chain several times a
week. Can't we integrate?" → ntfy retired same-day (`29fe798`): the handler now sends through
FluxusSource's existing Gmail `[email_credentials]` on sadalsuud (same sender/inbox as the
chain's emails), 3h burst guard whose marker arms only on a CONFIRMED send (a creds hiccup must
not silence the next real alert), log-only fallback if creds absent. Topic file deleted.
Self-test delivered to the engineer's inbox. Lesson for the log: before adding a notification
channel, inventory the channels the engineer already reads — the integration question should
come before the zero-install convenience argument.

Second polish same hour (`0150f67`): the self-test email hardcoded "Most likely cause: the
fail-closed deploy gate" for EVERY unit — the engineer pasted it back and the misdirection was
obvious (recurrence of the session's own theme: smoke test's "wrong values" race, swallowed
GIT-ERROR sentinel). Body now leads with journal evidence; the gate hypothesis appears only for
nexusmind.service, framed ExecStartPre-vs-crash. Embedded python re-verified via the no-creds
path. Final NexusMind main: `0150f67` (dev tracking ref resynced — https-URL pushes don't
update refs/remotes; fetch with an explicit refspec fixes it).
