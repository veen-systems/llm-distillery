# Session 2026-07-04 (+ 07-05 freshness fixes) — hygiene, issue triage, framework adoption

Light hygiene session — no code or filter changes. Memory correction + issue triage + framework
adoption. Moved out of MEMORY.md 2026-07-10.

- **DeepSeek V4 peak/valley pricing** (email 2026-07-04). Mid-July 2026 pricing introduces 2x peak surcharge (peak UTC 01:00–04:00 + 06:00–10:00 = 08:00–12:00 CEST is the trap). Rule: run oracle batches off-peak (noon–midnight CEST). New reference memory `oracle-pricing-scheduling.md`; solutions v4 pickup annotated. Commit `7f5ee4a`.
- **gpu-server scorer architecture correction.** Chased a phantom "scorer down" alarm — it was stale memory, not an outage. `nexusmind-scorer.service` is a `static`, **on-demand** unit fired per run in the FluxusSource → NexusMind (sadalsuud) → gpu-server chain; inactive-between-runs is normal. Confirmed via `FluxusSource/memory/nexusmind.md` + `systemctl show` (`Result=success`). Fixed MEMORY.md prose + replaced two curl-`localhost:8000/health` verify snippets with disk-based checks. New gotcha logged. Commit `ca23efa`. **(NB 2026-07-10: this is why a `systemctl is-active = inactive` between pipeline runs is normal, not an outage.)**
- **Issue triage** (24 → 22 open). Closed **#39** (dup of #23) and **#53** (hyphen/underscore divergence — resolved on disk to underscore-only + NexusMind `filter_loader` now enforces underscore-only per their ADR-019). Re-scoped **#23** (cd `evidence_quality` 1.31 → ~0.90 in v5, cliff removed via ADR-015 soft-penalty) to a v6 target, and **#52** (residual = class-name drift `sustech/v3`→PreFilterV2 + `NR/v2`→PreFilterV1, + #66 fully-declarative remainder).
- **Framework adoption v1.9.0 → v1.10.4.** Bumped `CLAUDE.md` pin; added the v1.10.0 session-start drift-check row to Before You Start (the change we were missing — which is *why* the drift went unnoticed). curate skill already carried v1.10.0 Step-0 sub-steps 6/7. v1.10.1–v1.10.4 are docs/maintainer-only, no adopter action. Optional not-yet-adopted: `hypothesis-log.md` pattern (v1.10.0). *(Framework since advanced to v1.10.6, adopted 2026-07-10 — also no-op.)*

## Freshness flags (resolved)

- ~~The 2026-05-31 recap claimed "6 new memory entries" that never existed on disk.~~ **RESOLVED 2026-07-05**: verified absent everywhere (repo + user-level), then reconstructed all 6 from the recap description + verifiable repo content (ADR-020 draft, CLAUDE.md, ADR-010/012/013/015). Recap claim corrected; index pointers added; `[[cd-v5-reference-status]]` link now resolves. Each file carries a reconstruction note.
- MEMORY.md recap was a **month behind git** — the June obituary_detector v3 work (#51, commits `87e9962`/`9692bcb`/`dd9c3c4`) has no recap entry (git-only; noted here rather than reconstructed).
