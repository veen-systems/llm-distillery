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
- **`_violence_model` PASS** (resolved 2026-08-02) — `v1` on all 2,091 enriched
  rows, not `unknown`.
- **Shadow log PASS** (resolved 2026-08-02) — all six filters report,
  **`errors=0`** across 570 lines / ~8,765 scorings per filter.

### Shadow rollup (2026-08-01 14:00 → 2026-08-02 06:33 UTC)

| filter | observed | n | declared | verdict | top block |
|---|---|---|---|---|---|
| investment_risk | 0.642 | 8,770 | — | NO CONTRACT | `content_too_short_Nchars` (3,074) |
| uplifting | 0.593 | 8,764 | 0.20 | DRIFT | `content_too_short_Nchars` (3,074) |
| **cultural_discovery** | **0.263** | 8,764 | **0.25** | **MATCH** | `no_cultural_topic_signal` (6,164) |
| nature_recovery | 0.649 | 8,763 | 0.85 | DRIFT (downward) | `content_too_short_Nchars` (3,029) |
| belonging | 0.638 | 8,763 | 0.15 | DRIFT | `content_too_short_Nchars` (3,029) |
| solutions | 0.649 | 8,763 | 0.20 | DRIFT | `content_too_short_Nchars` (3,029) |

**The filter that MATCHes is the only one not dominated by the shared length
floor.** `content_too_short_Nchars` is top block for five of six at near-identical
counts — the same articles blocked five times by a `BasePreFilter` rule. Only cd's
dominant block is a real lens rule. Confirms the 08-01 sizing at ~3× the sample and
sharpens the case for **one global short-content gate before fan-out**.

**Four filters cluster at 0.638–0.649 = the NM#285 signature.** Truncated `Article`
means url/source/description rules cannot fire, so filters whose blocking doesn't
survive truncation converge on what the length floor alone yields. **Five of six
numbers cannot gate enforcement until NM#285 is measured; cd's can** (content-based
rule, and its in-path 0.263 agrees with full-row offline replay 0.245).

Written up on NM#284 (rollup), NM#281 (all four checks), LD#86 (cd validated at
n=8,764), LD#90 (drift table, three distinct failure shapes).

⚠️ **Do not re-declare any `expected_pass_rate` from these numbers yet** — a value
fitted to a truncation artifact bakes the artifact into config. Only nature_recovery
and cultural_discovery are safe to correct now.

**Incidental**: og:image backfill logged `528/2398 extracted, 1870 failed` (78%
failure). Same surface as ovr#281, which currently rests on an n=25 probe. Worth
adding as evidence *after* confirming the two failure counts mean the same thing.

## Lessons

- **Five instances in one day of one shape** — see the standing rule promoted to
  `memory/MEMORY.md`. Prefilter counted from a 100%-passers file; ovr#280 sampled
  the wrong nested structure; the framework family enumerated from
  `gh repo list`, which misses repos with no remote. Then twice more during the
  verification itself: **gpu-server logs UTC, sadalsuud CEST**, so `journalctl -S
  "16:45"` on a host whose clock read 14:54 returned nothing, and I nearly filed
  "shadow log not emitting" as a finding; the same 2h offset also made a
  `flagged_..._145144` filename look like a stale run-id when it was simply UTC.
  **Timezone is a form of "what does this source exclude?"** Each produced a
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

1. ~~Finish post-deploy checks 2 and 4~~ **DONE 2026-08-02 — all four PASS.**
2. **NM#285 measurement** — gates every queued enforcement decision. Now sharper:
   the four-filter cluster at 0.638–0.649 is the predicted artifact, so the
   per-filter truncation diff is the exact number needed.
3. **persuasion-scorer Phase 1** in its own session — brief already written into
   that repo's `MEMORY.md` and CLAUDE.md phase table.

## Related Memories

- [[project_session_2026_08_01]] — this morning
- [[cross-repo-prioritization]] — rewritten this session
- [[gotcha-log]] — the third-instance entry
