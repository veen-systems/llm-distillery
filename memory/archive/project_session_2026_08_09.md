# Session 2026-08-09 — corroboration: the change I was sent to ship was already refuted

**Headline: nothing shipped, and that is the correct outcome.** The task was to
turn "step 2" (title+body @ 0.92) into a production change. The production check
had already been done on 2026-08-06 and says **don't**. What I added is the
missing turn-over point, and three filed defects that matter more than the
threshold did.

## The framing error I inherited, and its cause

The brief said the 340-pair precision panel was **UNADJUDICATED** and that the
remaining work was a labelling pass. Both false. The panels were adjudicated by
the DeepSeek judge on 2026-08-06 and scored; the verdicts live in the **NexusMind
checkout** under `data/research/precision_panel*/judge_verdicts.jsonl`, which is
gitignored (`.gitignore:230 data/`) and therefore was never copied to b650. The
b650 `adjudicate.csv` is the *human* sheet, legitimately empty under the
no-hand-labelling rule.

`feedback-enumeration-is-not-inventory`, again: b650 excludes those files by
construction, and I read its silence as absence. **Establish what a source
excludes before using it as evidence** — including when the source is a machine.

## What was already known (registry, 2026-08-06)

OBS-13 / OBS-27 / OBS-28 / OBS-29 and **PROP-6 "DOES NOT SHIP AS SPECIFIED"**.
The representation claim survives (title+body beats title-only, AUROC 0.791 vs
0.771); the **0.96/0.92 threshold is refuted** — it rejects 70% genuinely
same-story pairs at its own margin and merges 86% fewer pairs. The registry's own
words: *"evidence points below 0.92 and the turn-over point is unmeasured."*

## What I added

**(a) Production embeds `title_raw`.** `story_dedup._prepare_text` →
`f"query: {title}"`, no stripping. `_normalize_title()` at `scripts/main.py:152`
serves exact duplicate-title rejection and never touches the embedding. The
hypotheses file had quoted the **`title_stripped`** row for the live config
(R 0.4909 vs the true 0.4864) — immaterial to the ordering, corrected anyway.

**(b) Turn-over point, panel v3** — 680 adjudicated pairs, fresh seed, four
configs, pre-registered rule written before the run
(`NexusMind/docs/investigation/2026-08-08-turnover-prereg.md`):

| config | merged pairs | precision (95% CI) | near-miss discarded | est. true | largest | ≥20 |
|---|---|---|---|---|---|---|
| title@0.92/0.88 (LIVE) | 948,399 | 0.173 [0.083,0.326] | 10% | 164,123 | 592 | 95 |
| title_body@0.92/0.88 | **17,692,176** | 0.004 [0.000,0.138] | 10% | 74,666 | 1051 | 128 |
| **title_body@0.94/0.90** | 496,299 | 0.344 [0.226,0.485] | 20% | **170,681** | 422 | 52 |
| title_body@0.96/0.92 | 134,012 | 0.451 [0.349,0.558] | 30% | 60,459 | 129 | 12 |

`0.94/0.90` passes all three pre-registered gates. **It is still not shippable**:
by the #95 standard (overlapping intervals → not distinguishable) it *ties* live,
and the live baseline itself moved **0.283 (v2) → 0.173 (v3)** at n_eff 36
because 83% of pair mass sits in giant clusters sampled 25 deep. **My D2 was
weaker than this project's own standard** — I compared a CI bound against a bare
point estimate. Deepen the giant stratum before this gates anything.

## The finding that outranks the threshold

**Primary scientific documents are 20.6–30.4% of everything merged and 0–14%
correct.** Excluding them moves precision 0.344 → **0.459**, more than any
threshold change. Structural, not tuning: a paper is a primary document, so two
outlets never independently corroborate it.

Chain, traced end to end:
1. **ducroq/FluxusSource#143** — arXiv category feeds prefix the body with
   `arXiv:NNNN.NNNNNvN Announce Type:`, shifting `content[:500]`, so
   `md5(title+content[:500])` never collides. **600 duplicate papers per 48
   cycles**, all same paper id AND same version (checked against arXiv's
   `replace` semantics). All 6 "true" academic merges in the panel were these;
   **0 of 85 false ones had identical titles**. Owner's fix is better than mine:
   **drop the plain `arxiv` feed** — removes 100% of the class for 77 papers/8
   days, and 0 titles appear in ≥2 category feeds. Distinct from FS#142 (a
   *store* failure) and FS#133 (dropping too much).
2. **ducroq/FluxusSource#144** — can't gate on `type_classification`. 308 Google
   News feeds collide on domain `google.com`; **86% of `academic` rows are Global
   South news** (Myanmar, DR Congo, Syria, Sudan). Retiring Google News fixes only
   67% — `smithsonianmag.com`/`sciencealert.com`/`statnews.com` have ONE category
   each and are `academic` because they *write about* science. MDPI and Frontiers
   are right **through the same wrong branch**.
3. **ducroq/NexusMind#305** — detect it from article features instead. Union of
   academic-API metadata / `[Clinical Trial]` prefix / DOI: **1.000 recall on
   arXiv-PubMed-trials, 0.000 on Guardian, Ars, Smithsonian, STAT, ScienceAlert.**
   The apparent 1.8% FP is mostly CrossRef/OpenAlex/Semantic Scholar/Nature — the
   feature found primary literature my source list had missed. Gap: MDPI/Frontiers
   RSS at 0.241.

## Two lessons worth keeping

- **STAGE TRAP.** The arXiv prefix is 91.6% reliable at collection and **0.000**
  in NexusMind production — enrichment re-fetches the body. Had I measured only on
  the b650 replay corpus I would have shipped a dead detector, the #284/#300 shape
  exactly. **Measure a feature at the stage it will run.**
- **SCHEMA.** Contract A (`fluxussource-output.schema.json`) is
  `additionalProperties: false` — stamping at collection **requires** a schema
  change. Contract B is permissive, so a stamp there passes silently and is
  invisible to `stamp_census.py`. Never `required` initially (NM#300).

## Features probed (599 adjudicated pairs; news-only cut n=505)

| feature | AUC |
|---|---|
| **time proximity** | **0.809** |
| numeric overlap title+body | 0.581 |
| is_cross_language | 0.570 |
| not_same_source | 0.554 |
| rare numbers (≥4 digits, non-year) | 0.503 |
| length agreement | 0.453 (inverted) |

**Shared numbers REFUTED** — good argument (digits survive translation), no
signal. **Time CONFIRMED and independently replicated** (0.809 vs INST-10's
0.798, different panel/seed/sample; improves when academic pairs are removed).
It is built, `temporal.enabled: false`, blocked only on certification by a
non-author — the highest value per effort here. Academic subset had 6 positives;
nothing reported from it.

## My own errors this session, all caught by checking

1. Quoted **91%** of cross-language near-misses as real (v2, 10/11). **Does not
   replicate** — v3 gives 2/4 = 50%. Direction holds on every config in both
   panels; the magnitude was one small draw and I led with it.
2. Rogan-Gladen printed values **>1.0** — I fed it the judge's error rates instead
   of sensitivity/specificity. Fixed, verified against OBS-22's anchor
   (0.364 → 0.438).
3. Called the `academic` label "broken" from example sampling; the direct check
   showed arXiv *is* tagged correctly. Conclusion held, first evidence didn't.
4. Hypothesised the label was per-article topic — it is **100% per-source**.
5. Said `classify_type` had **no callers**; my grep excluded the defining file. It
   is called by `compute_heuristic_score` in that same file.

## State at close

- **Nothing deployed. No production config changed in any repo.** No deploy was
  applicable — this session produced measurements, docs and issues only.
- FluxusSource checkout had **another session's uncommitted work**
  (`memory/*`, `project_session_2026-08-08d.md`) — left untouched, explicit paths
  only, per the whole-tree rule.
- Panel v3 data: `NexusMind/data/research/precision_panel_v3/` (gitignored).
  Reproduction scripts on b650 `~/nm-sweep/`: `feature_probe.py`,
  `fs_hash_check.py`, `fs_dupe_kind.py`, `arxiv_overlap.py` — kept deliberately as
  the evidence behind FS#143.
- agent-ready-projects verified current (v1.18.0, 0 behind).
