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
