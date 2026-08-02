---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

**Last updated: 2026-08-01 (evening re-inventory)**
Open: **llm-distillery 32 · NexusMind 36 · ovr.news 80 · FluxusSource 8 = 156.**
Repos: veen-systems/llm-distillery, ducroq/{NexusMind,ovr.news,FluxusSource}.

## Where we stand — one paragraph

Chain 3 (calibration/normalization) is **closed and verified live**. Chain 1
(obituary) has one cosmetic link left (ovr#204). Chain 8 (Google News) had both
FluxusSource links **close 07-31** and now hangs on a **calendar deadline
(FS#120, ~2026-08-14)** whose ovr-side dependency shipped. What replaced them is
a new cluster of **contract/plumbing defects found by adversarial review of the
same day's own work** — NM#284/#285/#286, ovr#277/#285 — all of the shape
"the mechanism exists, is configured, and cannot fire." Nothing in that cluster
is live-breaking today; **all of it gates decisions that are queued behind it.**
The one genuinely new *product* problem is **LD#91** (uplifting ranked a
child-trafficking investigation 6th of 3,530).

## Changes since the 2026-08-01 morning update

| What | Now |
|------|-----|
| **Chain 3 (calibration)** | **CLOSED** — verified live; NM#279/#280, LD#74/#76 closed. |
| **Chain 8 (Google News)** | **FS#118 + FS#119 both CLOSED 07-31.** ovr#275's resolver shipped (`623cc82`) and its per-source attribution surface shipped (`8ab610a`), unblocking **FS#120 — the only calendar deadline on the board, ~2026-08-14.** |
| **NM#284 (prefilters never ran)** | Stage 1 shadow deployed + verified. **Now blocked by NM#285.** |
| **NM#285 (NEW — P0)** | Shadow measures a **truncated `Article`** (title+content only) — url/source/description rules can never fire, so every observed pass rate is biased high by an unknown per-filter amount. **Gates every NM#284 enforcement decision, therefore gates LD#86, LD#87, LD#90.** Recommendation on file: **Option C — run prefilters pipeline-side.** |
| **NM#286 (NEW — P1)** | ADR-022 gaps: commerce has no `enforce` key, a consumer-side commerce drop in `enrich_survivors.py`, violence stamping skipped in 3 run modes. Items 1+2 **must move together**; item 3 must land **before any violence enforce flip**. |
| **NM#281** | Deployed + same-day corrected (`b85a467`). **4 first-time-in-production checks still unverified** — see Batch A.1. |
| **LD#91 (NEW — P0)** | uplifting scored a child-trafficking investigation raw 6.77 = **99.9th pct of 3,530**; it led the homepage with a trafficking price list as pull quote. Not a threshold problem — the scorer rewards narrative fragments over dominant subject. Sibling of LD#61, NM#231. |
| **ovr#284 (NEW — P0, legal)** | Comscore beacon served as hero on 13 articles → visitor IP/UA sent to a third-party analytics vendor with no basis. Needs an **Art. 5(2) record**, not just a code fix. |
| **ovr#285 (NEW — P0)** | Orphan reclamation **NULLs `raw_weighted_average` + `source_quality` every cycle**. Proven with before/after rows. **Blocks the ovr#283 floor decision** — that decision would otherwise be taken on null data. |
| **ovr#277 (NEW — P1, sequencing)** | `editorial_decisions` PK lacks `prompt_version`, so re-gating **destroys the before-side of any before/after comparison**. **Prerequisite for ovr#235 and therefore for ovr#270.** Chain 7 was previously sequenced wrong. |
| **ovr#280 cluster_id** | Diagnosis **REFUTED** — cluster_id IS on the wire (7,629/16,128 rows). Break is **downstream in ovr.news ingestion**; NM#278 is the real fix for the reader-visible symptom. |
| **NM#206** | Was already CLOSED — dropped from all batches. |

## Cross-Repo Dependency Chains

`→` means "blocked on" or "feeds into."

### Chain 1: Obituary Detector — COMPLETE except one link
```
LD#51 ✅ → LD#77 ✅ → NM#185 ✅ → v4 ✅ → LD#83 (v5 + ENFORCE @0.85) ✅ → ovr#204 ← ONLY LINK LEFT
```
Enforcement live + verified (1,158 blocked). Carryover washes out ~Aug 2–6 by
window. LD#85 (v6 relabel) PARKED indefinitely by owner.

### Chain 2: Violence Promotion — shadow, enforcement gated
```
LD#73 ✅ → NM#274 ✅ → NM#281 gate wiring ✅ (inert) → LD#82 (audit) + NM#286 item 3 → enforce
```
**Two hard gates before any flip:** LD#82 (v1 recall 0.55 → enforcing gates ~half
of true positives) and NM#286 item 3 (violence stamping skipped in 3 run modes).

### Chain 3: Normalization Refits — **CLOSED 2026-08-01**
Verified live across six consecutive cycles. No open links.

### Chain 4: Prefilter Resurrection — **NEW PRIMARY CHAIN**
```
NM#284 (stage 1 shadow) ✅ → NM#285 (truncation — gates the measurement)
                              → decide Option C (pipeline-side prefilters)
                              → LD#86 (cd enforce) → LD#87 (cd v6 op-point)
                              → LD#90 (harmonization: observed == declared)
```
**Everything downstream of NM#285 is measuring a biased number.** Four filters
cluster at ~0.59 by artifact; cd's 0.255 survives the objection, ir's does not.
Option C also dissolves NM#285, subsumes stage 1b, and matches how
commerce/obituary/violence already work. **Measure per-filter truncation effect
before committing.**

### Chain 5: Solutions Lens — largely complete
```
LD#43 ✅ → v4 ✅ → v6 (gate passed, normalized) ✅ → LD#84 (prompt router, v7 only) → NM#204 (closable as superseded)
```
solutions v6 is also the **real LD#90 mismatch** (declares 0.20, passes 0.59).

### Chain 6: Commerce — resolved, but contract gap reopened
```
LD#80 ✅ (v1 forced, verified) → NM#286 items 1+2 (no enforce key + consumer-side drop) ← MOVE TOGETHER
```
Watch signal: `_commerce_model == "gpu-server-unpinned"` in production means the
LD#80 guard regressed.

### Chain 7: Summarizer — **RE-SEQUENCED (was wrong)**
```
ovr#277 (non-destructive re-gate) ← PREREQUISITE
   → ovr#235 (held-out validation gate) → ovr#270 (gemma3:27b → gpt-oss:20b)
   ↔ ovr#267 (audit findings) ↔ ovr#276 (temp=0 non-determinism) ↔ ovr#286 (397 summary backfill)
```
Without ovr#277, measuring the after-side destroys the before-side. ovr#276
(lost byte-identical reproducibility) independently weakens any A/B.

### Chain 8: Google News — **DEADLINE-DRIVEN**
```
FS#118 ✅ → FS#119 ✅ → ovr#275 resolver ✅ (623cc82) + attribution surface ✅ (8ab610a)
   → FS#120 eval readout + ADR-007 decision gate ← DUE ~2026-08-14
```
The only calendar-bound item on the board. Eval identities collecting since
07-31; needs ~2 weeks. ovr#275 itself is closable after the ~Aug 2 backlog
washout check.

### Chain 9: Hero Images — **NEW**
```
NM#282 ✅ (ML logo classifier dead since 06-16) → ovr#281 (stock sticky + validateImageUrl false-rejects ~half)
   → ovr#284 (Comscore beacon: legal record + non-accidental control) → ovr#255 (academic stock photos)
   ↔ NM#227 / NM#222 / NM#183 / NM#182
```
ovr#281 measured: of 25 rescuable, 11 would succeed today (stickiness), 12 are
`validateImageUrl` false-rejects, 2 fetch failures. ~10% of articles affected.

### Chain 10: Dedup / Corroboration — **NEW**
```
ovr#280 (ovr-side ingestion of cluster_id — data IS on the wire) → NM#278 (threshold retune for title-only E5)
   ↔ NM#188 / NM#170 / NM#215 / NM#275(closed)
```
Do the ovr ingestion fix first — it is cheap and the data already exists.
**Caution on NM#278:** NexusMind *removes* rather than *labels* (~32%/run);
anything removed upstream can never surface as an "N sources" badge.

### Chain 11: Score Provenance / Publication Floor — **NEW**
```
ovr#285 (stop NULLing raw_weighted_average) → ovr#283 (floor: decide or close won't-do)
   ← informed by LD#91 (a floor would NOT have caught it — raw 6.77 is genuinely 99.9th pct)
```

### Chain 12: Source Classification (dormant)
```
FluxusSource source_classification → NM#253
```
Neither side urgent.

## Priority Rankings

### P0 — Now

| ID | Repo | Title | Why P0 |
|----|------|-------|--------|
| **(carryover)** | NexusMind | Verify the post-14:04 cycle: 4 first-time-in-production checks | NM#281's corrected gate has never been observed live. `gpu-server-unpinned` = LD#80 regression. |
| **NM#285** | NexusMind | Shadow measures a truncated Article | Gates NM#284 → LD#86/#87/#90. Every queued enforcement decision waits on this number. |
| **LD#91** | llm-distillery | uplifting ranks child-trafficking investigation top-6 of 3,530 | Reputational, reader-visible, live. Scorer fidelity, not threshold. |
| **LD#92** | llm-distillery | uplifting over-scores sub-300-char stubs by ~1.9 raw pts | NEW 2026-08-02. ~460 false-positive articles per 8 cycles reaching the feed, uplifting alone. Oracle-verified (MAE 1.98 vs 0.87 control). Fix = cap/penalty, **not** a length gate — a gate drops ~half genuine content, skewed to non-English/global-south. |
| **ovr#284** | ovr.news | Comscore beacon as hero image | Real processing-without-basis event; needs an Art. 5(2) record. Legal, not just code. |
| **ovr#285** | ovr.news | Orphan reclamation NULLs raw_weighted_average + source_quality | Silent per-cycle data loss; blocks ovr#283. |

### P1 — This week

| ID | Repo | Title | Why P1 |
|----|------|-------|--------|
| **NM#286** | NexusMind | ADR-022 gaps (commerce enforce key, consumer-side drop, violence run-modes) | Items 1+2 must move together; item 3 blocks Chain 2. |
| **ovr#277** | ovr.news | editorial_decisions destructive on re-gate | Prerequisite for the whole of Chain 7. |
| **LD#82** | llm-distillery | violence v1 shadow audit | Defines what `enforce: false` is waiting on. |
| **FS#120** | FluxusSource | #119 eval readout + ADR-007 gate | **Hard date ~2026-08-14.** Dependency now shipped. |
| **ovr#280 → NM#278** | both | cluster_id ingestion, then dedup retune | Reader-reported: 5 articles = ~10% of a 52-article lens. |
| **ovr#281** | ovr.news | Stock heroes on ~10% of articles | Measured, decomposed, fixable in two independent halves. |
| **ovr#204** | ovr.news | Remove hardcoded obituary detection | Chain 1's last link; upstream verified. |
| **ovr#262** | ovr.news | Data archiving lossy & unreliable | Irreplaceable editorial signal lost forever. |
| **NM#244** | NexusMind | gpu-server 422s drop whole chunks, reason not logged | Silent data loss in scoring. |

### P2 — This month

| ID | Repo | Title |
|----|------|-------|
| **LD#86 / LD#87 / LD#90** | llm-distillery | cd prefilter enforce → cd v6 op-point → lens harmonization (**all downstream of NM#285**) |
| **ovr#235 → ovr#270** | ovr.news | Held-out gate, then summarizer swap (behind ovr#277) |
| **ovr#286** | ovr.news | Backfill 397 metadata-absence summaries |
| **ovr#276** | ovr.news | Editorial gate no longer byte-identical at temp=0 |
| **NM#231** | NexusMind | uplifting under-scores non-English documented-outcome news (sibling of LD#91) |
| **LD#61** | llm-distillery | Cross-filter trajectory-framing mis-lensing (sibling of LD#91) |
| **ovr#283** | ovr.news | Publication floor — decide or close won't-do (behind ovr#285) |
| **FS#121** | FluxusSource | fda/patent aggregators never run (hardcoded `all_sources`) |
| **LD#84** | llm-distillery | solutions oracle prompt router self-contradictory |
| **LD#81** | llm-distillery | Align sklearn across training + inference |
| **LD#89** | llm-distillery | Share frozen-mpnet embed pass between obituary + violence |
| **LD#23 / LD#70 / LD#71** | llm-distillery | cd evidence_quality; nr protection scope; nr v5 recall |
| **ovr#214 / ovr#255 / ovr#256** | ovr.news | Language leak; academic stock photos; US-centric abbreviations |
| **NM#221 / NM#220 / NM#96** | NexusMind | GPU multi-tenancy, Ollama coexistence, sustainable hosting |

### P3 — Backlog

LD#52, LD#66, LD#48, LD#88 (hygiene batch), NM#196, NM#82, NM#23, NM#185,
NM#187, NM#188, NM#170, ovr#63, ovr#55, ovr#19, ovr#278 (safe-fetch defence in
depth), ovr#254 + FS#105 (systemd units, same gap both repos), FS#11, FS#103,
FS#107, FS#114.

### P4 — Future

LD#38, LD#40, LD#43, LD#24, LD#78, LD#79, ovr#232, ovr#223, ovr#211, ovr#213,
ovr#242, ovr#133, FS#19, plus the ovr `positioning`/`outreach` block
(#137–#160, 20 issues — a separate non-engineering track).

## Sequenced Work Batches

### Batch A — Next session (forced order)
1. **Verify the post-14:04 cycle** — `_commerce_model` reads `v1`; `_violence_model` present; `violence_blocked` gone from the Loaded line; belonging + nature_recovery appear in the shadow log with `errors=N`.
2. **NM#285 measurement** — per-filter diff of in-path shadow vs offline replay over full rows. Then decide Option C.
3. **NM#286** — items 1+2 together; item 3 before any violence flip.
4. **LD#82** violence audit.
5. Only then: **LD#90** program, **LD#87** op-point re-derivation.

### Batch B — Reader-visible quality (can run in parallel with A)
1. **LD#91** — uplifting dominant-subject failure. Read alongside LD#61 and NM#231; likely one shared mechanism.
2. **ovr#285** → then **ovr#283** decision.
3. **ovr#280** ingestion fix → **NM#278** retune.
4. **ovr#281** — stock heroes (two independent halves: stickiness, validate false-rejects).
5. **ovr#204** — remove hardcoded obituary filter.

### Batch C — Legal / compliance
1. **ovr#284** — Art. 5(2) record + a hero-image egress control that is deliberate rather than accidental.
2. **ovr#274** — full threat-surface security review (standing).
3. **ovr#278** — safe-fetch defence-in-depth leftovers.

### Batch D — Deadline track
1. **FS#120** — eval readout, ADR-007 gate, **~2026-08-14**. Start the readout script well before the date; ovr#275's attribution export is live.
2. Close **ovr#275** after the ~Aug 2 backlog washout check.

### Batch E — Summarizer (strictly sequenced)
1. **ovr#277** (non-destructive re-gate) → 2. **ovr#276** (determinism) → 3. **ovr#235** (gate) → 4. **ovr#270** (swap) → 5. **ovr#286** (backfill).

## Housekeeping (opportunistic)

- Delete retired sustech/foresight dirs (post-drain — due now).
- Sync `score_normalization.py` (44-line divergence LD ↔ NM).
- LD#49 / LD#48 — remove superseded filter versions; normalize Hub naming.
- FS#105 + ovr#254 — version systemd units in-repo.
- NM#91 sadalsuud healthcheck drift (operator decision).

## Standing Operator Decisions (Jeroen's call)

- **NM#285 Option C** — run prefilters pipeline-side? (recommendation on file)
- **ovr#283** — publication floor: yes/no/won't-do.
- **ovr#284** — how the Art. 5(2) record is written and by whom.
- **LD#85** obituary v6 relabel — PARKED; reactivate on obit-flag or over-block harm.
- NM#91 healthcheck drift; uplifting v7 NO_HUB backup; cd v5 config-schema exemptions.
- FluxusSource: 71 DEAD disable candidates; OVER_POLLED audit; global-broadening yield check.

## Related Memories

- [[project_session_2026_08_01]] — the session this update follows
- [[project_session_2026_07_31]] — Chain 3 deploys
- [[project-obituary-detector]] — Chain 1 details
- [[filter-status]] — per-filter MAE/status
- [[calibration-history]] — Dead Ends (read before calibration/scorer work)
