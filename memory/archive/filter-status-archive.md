# Filter Status — archive

Closed/historical blocks moved out of `memory/filter-status.md` (#163). Verbatim; not current state.

## Moved 2026-10-16 (#163 round 6)

Verbatim blocks moved from `memory/filter-status.md` (HEAD `9b6ec26` line numbers).

### human_thriving v8 gate note (was L19-27)

⚠️ `human_thriving v8` gate-passed at **recall 0.314 / spec 0.9856 / precision 0.550**
(20 surfaced, 9 FP) on the **retrained epoch-5** checkpoint, 2026-09-06, commit `64b469d`
(EXP-027). ⛔ **The widely-quoted 0.343 / 0.992 / 0.706 is the SUPERSEDED epoch-4 model** —
orphaned by a `git commit --amend` and retrained rather than shipped with a provenance
exception. All four #95 bands overlap, so the two are **NOT DISTINGUISHABLE**; the point
estimates move adversely and 6 of the 9 FPs are `in_scope` boundary cases, not junk.
It is deliberately NOT
in these tables: it is not deployed, and its positive class is not v7's (Jaccard 0.246), so
its recall is not commensurable with the rows below.

### Anchoring history (was L65-73)

> **Anchoring history — two failures, both of the same kind.** (1) The original
> `diff | head -20` form compared two differently-formatted tables and could
> only ever emit MANUAL CHECK NEEDED. (2) Its 2026-08-01 replacement anchored
> its awk range on the literal `**Per-filter`, and the very next commit renamed
> that heading to `**Per-lens RULE prefilters:` — the range then ran unbounded
> to EOF and swept in unrelated sections. It still printed PASS, because
> `comm -23` tolerates junk in the second stream, so it looked healthy while
> checking something else entirely. Caught by adversarial review the same day.
>

### human_thriving v8 table row (was L87-87)

| human_thriving | v8 **(superseded by v9 2026-09-25)** | 0.539 (gate, calibrated; do NOT rank on this — ADR-023) | 0.6066 test (**worse**, −3.6%) | 6.6K | `jeergrvgreg/human-thriving-filter-v8` (private) | **2026-09-07 DEPLOYED + ENABLED** — NexusMind `9245f2c` (PR #452 shipped the package, **PR #453 enabled it**: #452 alone left it out of `pipeline.enabled_filters`, so nothing called it). ✅ **SCORING CONFIRMED 2026-09-08** — first cycle to score was `filtered_20260907_180414.jsonl` <!-- placeholder -->, 6,210 articles, **63 above the 4.50 op-point** (the 12:10 cycle died in image enrichment, #152). ⭐ **First live-output audit (`EXP-029`, $0.16, n=62): scope precision 0.9677 [0.890, 0.991] vs the gate's 0.850, not distinguishable; only 2 of 62 off-lens. The defect is the PROMPT, not the student — swapping it for the documented rubric moves 12 articles out of `in_scope`, paired McNemar p=0.0034, and those 12 are STATUS.md's three owed v8.1 gaps (#153).** ✅ **Phase E FITTED 2026-09-22** on **2,976** rows (of 296,636 scored), `raw_min == op_point == 4.5` **exactly** — asserted as equality, not "under the cap", because the loader's test is a strict `>` and a failure is silent. #154 ruled (option 1) and fixed: the guard compared `sample_min` against an absolute 4.5 that IS this filter's op-point, making it a DENSITY test — it blocked the 202-row fit (`sample_min` 4.5069) and allowed the 2,976-row one only because `round(4.500042, 4) == 4.5`, a 5e-5 rounding window it had a ~22% chance of landing in (inferred from the measured density, not measured). Now `sample_gap > MAX_SAMPLE_GAP (0.5)`. ADR-021 gate (EXP-027, epoch 5, CUDA): recall **0.314** / spec **0.9856** / precision 0.550 panel, **0.6073 production-mix** (EXP-028), n=660, 35 positives. Op-point **4.50 calibrated**. ✅ **Phase E normalization FITTED** (`docs/decisions/2026-09-22-phase-e-fit-and-the-154-guard.md`). ⚠️ It also ARMED NM#319, owner-accepted. ⛔ **Do not quote a % here — 60.4% and 60.0% are the SAME TAUTOLOGY at two sample sizes**: normalized 4.0 is the fit sample's own 40th percentile, so ≈60% is arithmetic for any percentile-normalized filter (`memory/gotcha-log.md` § *in-sample share*). Quote the effective **raw** bar, **4.794** against op-point 4.50. `uplifting v7`'s 40%-un-enriched IS out-of-sample (82 cycles, 18,041 surfaced) and is the real comparison. ⛔ **Fitting is NOT a cutover**: v7 still scores. ⭐ **v7-vs-v8 on the same 15,372 production articles (`EXP-030`, $0): v7 surfaces 1,184, v8 surfaces 168** — a 7× cut, both 152 / v7-only 1,032 / v8-only 16, and volume-matching v8 does NOT reconstruct v7's set (57.0% at parity, Spearman 0.224 within the surfaced union). ⚠️ **`uplifting v7` remains LIVE**: this deploy CREATED human_thriving, it retired nothing, and which one feeds the Thriving tab is an OPEN OWNER DECISION. Adapter sha256 `074209ff…` |

### sustainability_technology v3 table row (was L88-88)

| sustainability_technology | v3 | 0.72 | — | 10.6K | `jeergrvgreg/sustainability-technology-v3` | 2026-02-21 (retired from ovr.news — superseded by solutions v6) |

### investment_risk retirement narrative (was L109-115)

⛔ **`investment_risk` is RETIRED downstream since 2026-09-17 — NexusMind ADR-025 (NM#499), not merely paused.** It was paused 2026-08-25 (owner: *"aegis is dormant, nobody reads it - pause it"*); two things then made the pause permanent, per that ADR: **the corpus its op-point was measured on no longer exists** (FluxusSource retired all 194 publisher-named Google News proxies on 2026-09-16, enabled GN feeds 302 → 40 — exactly the `site:`-carrying population behind the 4.25 threshold, and one of the four feeds its config names as *"must keep passing this filter"* went with them), and **nothing consumed it**. ⛔ **Un-pausing is now a PROJECT, not a config edit**: the package must be restored from `/home/jeroen/repos/_archive/nexusmind-investment_risk/`, the op-point re-measured against a corpus without that population, and the Aegis consumer resurrected.

⚠️ **This is a NexusMind decision and it does not name llm-distillery.** What it archived is NexusMind's deployed copy plus the export runtime (**Deleted**: `scripts/export_aegis_narrative.py` — archived, with the classifier, the `pipeline.aegis_export` config block and the stage-4 call site; git history retains all of it). **`filters/investment_risk/v6/` in THIS repo is untouched and stays** — this is where filters are made. Contract C, the 251 days of `narrative_risk` archives and the historical record are **deliberately kept** by the ADR too: *a contract outlives its producer*.

⚠️ **The 2026-08-25 three-file un-pause procedure is now history, not instructions** — the `pipeline.aegis_export` block it names no longer exists in the deployed config. `TestSmokeFixtureAlignment` (`NexusMind/tests/unit/test_filter_integrity.py`), the guard born from that incident, is generic (*no fixture may name a disabled filter*) and stays. Records: `docs/decisions/2026-08-25-pause-investment-risk.md` (the pause, superseded) and NexusMind `docs/adr/ADR-025-retire-investment-risk-and-the-aegis-export.md` (the retirement).

⛔ **Found by the curate verify runner on 2026-09-17, hours after the ADR landed** — the pause probe went FAIL because the config block it counted was gone. **The check was the control working**; it was rewritten to assert the retirement, not repaired to go green.

### foresight v1 table row (was L127-127)

| foresight | v1 | 0.744 | 0.75 | 3.5K | `jeergrvgreg/foresight-filter-v1` | PARKED 2026-04-16 (#43) |

### Per-lens RULE prefilters / NM#284 shadow measurement (was L131-184)

> ⛔ **2026-10-01: the per-lens rule prefilters below are DELETED** (decision 0; ADR-019 *Amendment 2026-10-01*). These two paragraphs are the 2026-08-01 finding that led there — history, not current state.

**Per-lens RULE prefilters: DECLARED but NOT ENFORCED in production (NM#284, found 2026-08-01).** Scope precisely: this is the per-lens rule prefilter only — `filters/{name}/v{N}/prefilter.py`, the ADR-018/019 `BasePreFilter` subclasses (regex/keyword on title+content). Every filter's `config.yaml` said `prefilter: enabled: true` (blocks removed 2026-10-01), but the GPU scorer builds each with `use_prefilter=False` (NexusMind `deploy/gpu-server/main.py` L915) and calls `score_batch(skip_prefilter=True)` (L1318), which makes the guard `if self.use_prefilter and not skip_prefilter` false in **both** `filter_base_scorer.score_batch` and `hybrid_scorer.score_batch`. Dead since `66582e7` (2026-02-10).

**Verified NOT affected** (each checked, not assumed): the **e5 probe** (Phase 2 of `hybrid_scorer.score_batch`, ungated by `skip_prefilter` — live log shows `stage1_low=7..19, stage2=77..85` per 100 articles); **commerce / obituary / violence** (separate `src/preprocessing/` stages with their own stamps); the **NM#189 source-type allowlist** (`shadow_mode: false`, enforced in NexusMind `src/scoring/source_filter.py`); and the same rule prefilters in the llm-distillery oracle/training path (true until their deletion on 2026-10-01).

⚠️ **Do NOT verify prefilter state from `data/filtered/{name}/filtered_*.jsonl`.** That file only receives rows where `passed_prefilter` is true NexusMind `scripts/main.py`’s `if result["passed_prefilter"]:` write guard, so it is 100% passers by construction and can never show a block. An earlier version of this note cited "0 blocks per cycle" from exactly that file — invalid evidence, corrected 2026-08-01. Use instead the pipeline line `Filter X complete (N scored, M prefiltered)` and the NM#284 shadow log, both of which see pre-drop counts. The ~350–360 `prefiltered` per lens per cycle is the source-type allowlist plus validation failures, **not** lens rules (five lenses with different rules landing within 10 of each other is the tell; investment_risk differs at 821 because it also excludes `academic` + `social`).

The finding rests on: (1) the code above; (2) the in-path shadow measurement — cd reports `observed_pass` 0.255 pooled over 2,099 articles *at the scorer*, which would read ≈1.000 if the gate were already enforcing upstream; (3) magnitude — cd's gate blocks 71% on replay vs 15.6% actually dropped.

NM#284 stage 1 (shadow measurement, deployed 2026-08-01 `5d53774`) logs observed
vs declared pass rate per batch. **Superseded by the 2026-08-02 measurement
(NM#285) — the first-cycle n≈2,099 table is no longer the reference.**

Full-contract replay, 4 cycles, n=8,283 per filter (same-row FULL vs
`{title, content}` A/B, so the truncation effect is isolated):

| filter | observed (full) | declared | length blocks | lens blocks | truncation effect |
|---|---|---|---|---|---|
| cultural_discovery v5 | 0.2605 | 0.25 | 0 | 6,103 | +0.0005 |
| uplifting v7 | 0.5873 | 0.20 | 2,949 | 469 | +0.0028 |
| investment_risk v6 | 0.7605 | *(none)* | 1,454 | 117 | +0.0097 |
| belonging v1 | 0.6321 | 0.15 | 2,950 | 99 | +0.0008 |
| nature_recovery v4 | 0.6438 | ~~0.85~~ **deleted** | 2,950 | **0** | +0.0000 |
| solutions v6 | 0.6438 | ~~0.20~~ **deleted** | 2,950 | **0** | +0.0000 |

Three things this replaced:

1. **The "mismatch" verdicts were not drift.** `nature_recovery v4` and
   `solutions v6` declare `EXCLUSION_PATTERNS = {}` by design (commerce upstream,
   ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides — a no-op with
   nothing to override. Both reduce to `validate_article()` +
   `MIN_CONTENT_LENGTH` and are byte-identical because they are the same filter.
   `expected_pass_rate` **deleted** from both (`3ed47e1`), not corrected: 0.644 is
   "fraction of articles ≥300 chars", a corpus statistic.
2. **"Stage 2 is a global short-content gate" is REFUTED** (#93). Length is
   87–100% of blocking for four of six filters, and a length gate is the wrong
   shape — short content clearing an op-point is as likely to be genuine as long
   content (uplifting 67% vs 65% oracle-validated). Fix is a cap/penalty.
3. **investment_risk's logged rate is biased by the shadow denominator**, which
   counts articles `source_filter` discards *after* scoring (2,193 of 8,765).
   ⚠️ Treat **0.129 as an upper bound on the discrepancy, not a measured bias**
   (corrected 2026-08-02): the excluded rows' true pass rate is UNMEASURED. The
   0.008 figure I first quoted came from `data/raw/`, which is pre-enrichment
   and therefore invalid for anything length-dependent; the only other estimate
   is circular. Measuring it properly needs the pipeline instrumented, not a
   file replayed. See `memory/nexusmind-data-sources.md`.

**cultural_discovery's rate matches and is still not safe to enforce** — 15.5%
of surfacing articles blocked, 0% of high tier (#86). Rate agreement and
safety-to-enforce are independent properties. The loss is **entirely
`no_cultural_topic_signal`** (9.9% en vs 19.2% non-en; the other three rules fire
*more* on English) — uneven `TOPIC_GATE_PATTERNS` keyword coverage, not a
language effect: German 4.9% and French 5.3% sit *below* English.

### foresight / sustainability_technology In-Development rows (was L200-201)

| foresight | v1 | **REMOVED 2026-08-03** (#43) — merged into solutions; the ~2026-08-01 delete-after date passed and the drain completed. Package in git history; production output archived to sadalsuud `~/retired_filters_foresight_sustech_20260803.tar.gz`. Closed #64 (its normalization refit) as superseded. |
| sustainability_technology | v3 | **REMOVED 2026-08-03** — replaced by solutions (ADR-012). Same archive. |

### Repo-wide audit (2026-07-27) body (was L209-218)

Ran `scripts/deployment/verify_filter_package.py --check-hub` across every `filters/*/v*/`.

- `ai-engineering-practice/v2` — `config.yaml filter.version` says 1.0 in a v2 dir → **REMOVED** (LD#49)
- `sustainability_technology/v2` — cross-version imports from v1 (#44 failure mode, pre-v3) → **REMOVED** (LD#49)
- `cultural-discovery/v3` — no default `repo_id` in inference_hub.py signature → **REMOVED** (LD#49)
- `investment-risk/v5` — references placeholder `your-username/investment-risk-filter-v5` → **REMOVED** (LD#49)
- `uplifting/v5` — Hub `last_modified` before local `training_history.json` → **REMOVED** (LD#49)
- `signs_of_wisdom/v1` — package structure incomplete (0 checks pass) → **REMOVED** (LD#49)

All 6 superseded by newer versions in production. Cleaned up 2026-07-27.

### What this rule was written against (2026-08-09 MAE ranking, retracted) (was L263-272)

**What this rule was written against** *(moved here from `CLAUDE.md` 2026-08-16;
the imperative stays there)*: on **2026-08-09** an agent produced a six-filter
quality ranking on mean absolute error and recommended a calibration change on
it. **Both were retracted.** MAE is the wrong instrument twice over — it weights
every article equally while the product only cares about the thin band at the
op-point, *and* each split's own positive rate makes a more enriched split carry
larger per-article error for identical model quality. ⚠️ **Do not overstate the
retraction either.** Composition explains only the ~27% above, so the ranking was
invalid **as made** while the residual it rested on may still be real. Two
separate claims; retracting the first does not establish the second is false.
