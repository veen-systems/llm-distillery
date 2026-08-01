---
name: project_session_2026_08_01_afternoon
description: "Session 2026-08-01 (afternoon) — four-repo re-inventory (156 open, 12 chains, new P0 set); persuasion-scorer split out as a verified system under three agent-ready frameworks; 2 of 4 post-deploy checks confirmed"
metadata:
  type: project
---

# Session 2026-08-01 (afternoon)

Continues [[project_session_2026_08_01]] (morning: refits verified, NM#284 found,
NM#281 shipped + corrected).

## 1. Four-repo re-inventory

**156 open** — LD 32 / NM 36 / ovr 80 / FS 8. Since the morning update: 13 closed,
12 opened. **Net flat on a very productive day** — the review practice is finding
real defects about as fast as they drain, so "backlog shrinking" is the wrong
success metric right now.

Rewrote `memory/cross-repo-prioritization.md`: 8 chains → **12**.

- **Chain 3 (calibration) CLOSED** — verified live across six cycles.
- **Chain 8 (Google News)** — FS#118 + FS#119 both closed 07-31; ovr#275's
  resolver (`623cc82`) and attribution surface (`8ab610a`) shipped. Now purely
  deadline-driven: **FS#120 due ~2026-08-14, the only calendar-bound item.**
- **New primary chain** NM#284 → **NM#285** → {LD#86, LD#87, LD#90}. NM#285 is the
  choke point: the shadow measures a truncated `Article`, so every downstream
  enforcement decision is being read off a biased number.
- **New chains 9** (hero images), **10** (dedup/corroboration), **11** (score
  provenance).
- **Chain 7 (summarizer) RE-SEQUENCED** — ovr#277 is a *prerequisite*, not a peer.
  Its PK lacks `prompt_version`, so re-gating destroys the before-side of any
  comparison. Running ovr#270 first would have burned the baseline.

New P0: NM#285; **LD#91** (uplifting ranked a child-trafficking investigation 6th
of 3,530, led the homepage); **ovr#284** (Comscore beacon as hero — needs an
Art. 5(2) record, not just a code fix); **ovr#285** (orphan reclamation NULLs
`raw_weighted_average` every cycle).

**The load-bearing set is 14 of 156.** ~20 ovr issues are positioning/outreach and
~15 are idea capture — they inflate the count without being work anyone is behind
on. Offered a triage pass to close/milestone ~35–40 at zero engineering cost;
not yet taken up.

## 2. persuasion-scorer split out (llm-distillery#78/#79)

New repo **`veen-systems/persuasion-scorer`** (private). LD#78/#79 stay open as
definition/origin and now carry pointers.

**Corpus finding that reframed the whole thing.** LD#78's suggested first step
("score one week of existing corpus") would have produced a degenerate result. The
ovr.news substrate is **94% centrist** by `bias_category` (left 176 / right 230 of
6,726 classified, n=20,516 full-text) and `data/raw/` is **91% RSS stubs**
(median 21 words; enriched text only in `data/filtered/*/`, median 1,370 chars).
It's a low-manipulation *control group*, not a probe corpus — the needles were
removed upstream by design. **A separate product needs a separate corpus.**

**Literature audit changed the design.** There is a canonical taxonomy —
SemEval-2023 Task 3, 23 techniques in 6 coarse categories, EC-published annotation
guidelines. The first (invented) taxonomy omitted *Attack on Reputation* entirely,
which is the category models detect best. Granularity, not oracle choice, is the
binding constraint here (κ≈0.594 clustered vs κ≈0.309 intent-based; under ADR-017
the oracle's self-consistency sets the student's floor) — which **inverts
FILTER_PLAYBOOK §0's usual ordering**. Fine-grained span labelling is where LLMs
demonstrably fail (GPT-4 macro-F1 0.13–0.16 vs RoBERTa-CRF 0.67), which is a
direct hit on #79-B's span-highlighting feature.

> ⚠️ **All of those figures are UNVERIFIED** — from search results plus two paper
> fetches, no DOI resolved. Flagged as such in the new repo's DR-002 and MEMORY.md.
> Phase 1 there is the anti-hallucination pass.

**Built as a verified system**, composing three frameworks (DR-004):
`agent-ready-assessment` @`79cc2bd` (the instrument — three-document
prompt/rubric/form pattern, rubric- and prompt-design review, score calibration),
`agent-ready-papers` v2.4.0 (the claims inside it), `agent-ready-projects` v1.12.0
(the project). Four DRs, two hypothesis-log bets with pinned falsification methods.

**Only 6 oracle calls were spent all session** — a guard-only probe of the four
Step-1 confusions. 6/6 pass, and two mirrored op-eds (same topic, opposite
politics) scored *identically* on agenda-intent, so the flip test held.

## 3. Post-deploy verification — 2 of 4 confirmed

Against the 16:08 cycle, first since the 13:35 NM#281 deploy.

- **`_commerce_model` PASS** — `v1` on all 2,496 commerce-scored rows; absent in
  the 12:07 pre-deploy cycle. **Not `gpu-server-unpinned`, so the LD#80 guard
  holds.**
- **`violence_blocked` gone from the Loaded line PASS** — now reads
  `commerce, obituary, dup-url, dup-id, dup-title, old, future, no date`. This is
  the `b85a467` fix confirmed in production: the drop moved out of load time,
  where it sat inside `_is_duplicate` and could never have fired.
- **`_violence_model` and the belonging/nature_recovery shadow lines: PENDING** —
  both land during enrichment/scoring and the cycle was still mid-run (og:image
  backfill at 16:24). A background watcher was armed.

**Incidental**: og:image backfill logged `528/2398 extracted, 1870 failed` (78%
failure). Same surface as ovr#281, which currently rests on an n=25 probe. Worth
adding as evidence *after* confirming the two failure counts mean the same thing.

## Lessons

- **Third instance in one day of one shape** — see the standing rule promoted to
  `memory/MEMORY.md`. Prefilter counted from a 100%-passers file; ovr#280 sampled
  the wrong nested structure; the framework family enumerated from
  `gh repo list`, which misses repos with no remote. Each produced a
  clean-looking, wrong result, and being right supplied no pressure to check.
- **The framework question answered itself.** Asked whether llm-distillery's other
  prompts should be grounded the same way. Mostly no: the existing lens prompts
  encode *editorial taste*, and they already have a stronger check — held-out
  oracle ground truth and the ADR-021 deploy gate. The discriminator is **"does
  this prompt make claims checkable against something other than itself?"**
  Grounding is for contested concepts with no ground truth. The one internal
  candidate is the LD#91 / LD#61 / NM#231 mis-lensing cluster, where fixes keep
  not sticking — usually a sign the underlying concept is under-specified.
- **A hypothesis was falsified before it was tested**, by the owner naming a repo.
  Recorded as a withdrawal rather than a quiet edit, and the surviving forecast was
  made *harder* (the assessment agents now run first, as the control arm).

## Next session

1. **Finish post-deploy checks 2 and 4** — watcher output, or re-run against the
   next completed cycle.
2. **NM#285 measurement** — gates every queued enforcement decision.
3. **persuasion-scorer Phase 1** in its own session — brief already written into
   that repo's `MEMORY.md` and CLAUDE.md phase table.

## Related Memories

- [[project_session_2026_08_01]] — this morning
- [[cross-repo-prioritization]] — rewritten this session
- [[gotcha-log]] — the third-instance entry
