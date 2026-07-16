# Publication Pipeline — Index & Plan

**Rule (the whole consolidation):** every draft has exactly ONE home — the repo that holds its
evidence — and every other location gets a pointer, never a copy. A duplicated draft diverges
silently (the needle draft already did: the ovr.news copy is frozen at 2026-04-19 while this
repo's copy kept evolving — same failure shape as the 2026-05-04 "manifest as anti-pattern"
gotcha). This file is the single cross-track index; update it when a piece moves stage.

**Stages:** `idea → pitch (claim + evidence list) → draft → review → published`.
**Maintenance rule:** an article that cites a mechanism gets updated in the SAME session the
mechanism changes (the normalization pieces were updated 2026-07-16 alongside Fix A). The
`/curate` doc-sync step should treat stale drafts as doc drift.

---

## Track A — Filter-stack methods (home: THIS repo, `docs/articles/`)

Technical/ML pieces whose evidence is llm-distillery's committed artifacts.

| Piece | Stage | Venue | Next step |
|---|---|---|---|
| `needle-in-haystack-draft.md` — the umbrella narrative (why constructive-news filtering breaks standard ML; the 6-step pipeline) | **draft, near-complete** | blog / long-form (ovr.news or dev.jeroenveen.nl) | final numbers pass; retire the stale ovr.news copy (below); publish FIRST — it frames every other piece |
| `cross-filter-score-normalization.md` — two-stage calibrate-within/normalize-across + population-pinning | **pitch, ready to draft** | arXiv tech report, 6–8 p | draft FROM `docs/NORMALIZATION_METHOD.md` (canonical, all numbers sourced); needs lit/novelty check + raw-vs-normalized baseline experiment |
| `hybrid-two-stage-needle-filter.md` — e5 probe (two recipes) + fine-tuned scorer cascade | pitch | arXiv or blog | needs the fixed-compute comparison run (scorer-alone vs cascade) |
| `oracle-consistency-beats-data-volume.md` — prompt precision predicts student MAE better than dataset size | pitch | blog first (natural experiment, n=6 filters) | tighten the cross-filter table; consider folding oracle bias-vs-noise ($100–200 catch) into it |

Evidence bundle: `nature_recovery_v4_evidence/` (gate.json, baselines, calibration, cost —
already structured for citation).

## Track B — ovr.news product & mission (home: `ovr.news/docs/articles/`)

Pieces about the product mechanics rather than the ML: lens taxonomy (5 lenses, scorers
decoupled — ADR-038 there), cross-lens ranking & tab assignment as a product story, "constructive
≠ positive" editorially, the bias-countering mission framing. Nothing drafted yet; the needle
draft's intro sections are the seed material. Start a mirror of this index there when the first
piece begins.

**Action needed (engineer sign-off):** `ovr.news/docs/articles/needle-in-haystack-draft.md` is a
stale 2026-04-19 duplicate of Track A's lead draft — replace it with a one-line pointer to this
repo's copy.

## Track C — Agent-engineering practice (homes: `dev.jeroenveen.nl/drafts/` + `augmented-engineering`)

Already a working pipeline (27 drafts, writing-guide, `adding-an-article` workflow, published
`.astro` pages). llm-distillery sessions contribute EVIDENCE, not drafts: file issues at
`ducroq/augmented-engineering` with pattern name + quantified results (per CLAUDE.md), e.g.
#30 (multi-model battery catches regression in the agent's own root fix, 2026-07-16). Drafting
happens in that pipeline, not here.

---

## Recommended order

1. **Needle-in-haystack** (Track A) — closest to done, frames everything; publishing it creates
   the reference the methods papers cite.
2. **Normalization methods paper** (Track A) — the canonical method doc exists as of 2026-07-16;
   the remaining work is a lit check and one baseline experiment, not writing from scratch.
3. **Oracle-consistency** (Track A, blog) — cheap to finish, standalone.
4. **Hybrid two-stage** (Track A) — blocked on the fixed-compute benchmark.
5. **Track B product pieces** — after the needle article is out and ovr.news has the traction
   story to tell.
