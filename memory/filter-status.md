# Filter Status

> **CLAUDE.md is authoritative.** This file keeps the extended per-filter MAE / data
> counts that don't fit in CLAUDE.md; if you just want current production state, read
> CLAUDE.md's Production Filters table. The tables below must be reconciled against it.
>
> <!-- verify: bash scripts/verification/check_prod_filters_table.sh -->

## ⛔ Before you read any table here: HIGH CERTAINTY OVER HIGH DETECTION

**ADR-023.** These tables put a recall column next to a specificity column across six
filters, which invites exactly the ranking the project forbids. **Specificity is the
criterion; recall is a constraint to satisfy, never a target.** A false positive reaches a
reader and costs trust; a false negative is invisible and the slot refills within the cycle.
**The filter with the lowest recall in a column is not the worst one**, and a change that
raises recall without holding specificity is a regression. Read every recall figure beside
its split's positive rate — the column is there — and never rank on MAE.

⚠️ `human_thriving v8` gate note (EXP-027, epoch 5 vs superseded epoch 4) — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16). v8 is SUPERSEDED by v9 (2026-09-25).

## ADR-021 deploy-gate results — the whole fleet, first complete 2026-08-10

Before 2026-08-10 only **3 of 6** deployed filters had ever been measured.
`belonging v1`, `cultural_discovery v5` and `investment_risk v6` were live with no
recall, no specificity, no number of any kind — so #102's "uplifting is the
specificity outlier" was a claim over half the population. It survived completion.

At each filter's op-point **as of 2026-08-10** (i.e. before the two moves above):

| filter | recall | specificity | FPR | n | split positive rate |
|---|---|---|---|---|---|
| uplifting v7 | 0.736 | 0.919 | **8.1%** | 660 | 32.7% |
| investment_risk v6 | **0.761** | 0.955 | 4.5% | 1045 | 15.6% |
| solutions v6 | 0.671 | 0.972 | 2.8% | 1032 | 16.2% |
| nature_recovery v4 | 0.650 | 0.979 | 2.1% | 391 | 15.3% |
| cultural_discovery v5 | 0.587 | 0.980 | 2.0% | 857 | 8.8% |
| belonging v1 | 0.600 | 0.985 | 1.5% | 738 | 11.5% |
| belonging v3 ⚠️ different instrument | 0.916 | 0.930 (weighted) | — | 422 (held-out set 3, judged) | 19.7% |

**Read recall and specificity only.** They are conditional on the true class, so
the split's positive rate does not distort them. Precision, MAE and F1 are
base-rate dependent and are NOT comparable across these rows (ADR-023) — which is
why the `MAE` column in the table above must not be used to rank anything.

**All measured on CPU; production serves on GPU** — worth 1 verdict flip at a 4.0
op-point on uplifting v7 (#104, open).
`docs/evidence/2026-08-10-fleet-deploy-gate-completion.md`.

**`cultural_discovery v5`'s gatekeeper binds 0 times in 857 rows** — the #94
shape, second instance found in this project. Unexamined.
>
> The check asserts every filter in CLAUDE.md's Production Filters table has a
> same-version row here (name separators normalized; `thriving` and
> `ai-engineering-practice` excluded — neither is a production filter here).
> This file may carry *extra* historical rows (cd v4, nr v2) — that's its job.
>
> **Anchoring history** (two 2026-08-01 failures of the table check) — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16).
> Hence (two earlier anchors each broke the check): the range is now bounded by dedicated `prod-filters-table:{start,end}`
> HTML sentinels that carry no other meaning and so have no reason to be
> renamed, and the check **fails loudly if any anchor is missing** rather than
> silently widening. A verify that cannot fail is worse than no verify.

## Production Filters

<!-- prod-filters-table:start -->

| Filter | Ver | MAE | Cal. MAE | Data | Hub Repo | Deployed |
|--------|-----|-----|----------|------|----------|----------|
| uplifting | v7 | **0.84** (see note; do NOT rank on this — ADR-023) | — | 5.3K | (none — file-copy to NexusMind only) | **2026-08-11 OP-POINT 4.0 → 4.5** (#102; recall 0.6111 / spec 0.9730, was 0.7361 / 0.9189; normalization refit n=15,698 raw_min 4.5 — exactly on MAX_NORMALIZATION_RAW_MIN). Deployed to NexusMind `e84c8fc`, activates at the first cycle after 12:02. 2026-07-31 normalization REFIT (Apr-06 fit was unit-mismatched ×1.1976, LD#76/NM#279; raw 5.0 → norm 5.17, was ~3.0) |
| human_thriving | v9 | — (do NOT rank on MAE — ADR-023; gate on v8's 660 test ids, adjudicated labels: spec 0.998, FP 1, TP 8/23) | own calibration, 720 val | 5.8K | `jeergrvgreg/human-thriving-filter-v9` (private) | **2026-09-25 LIVE, REPLACES v8** in the reader-invisible slot (NM PR #530 `c9f955a`; production call read back `filter_version 9.0`, percentile normalization, CUDA). Student retrained on Claude-adjudicated labels + 186 new positives + 439 hard negatives; live-week junk share 33.8% → 14.9%. Op-point 4.5 (owner ruling; two band audits below 4.5 failed drift). Thriving reads it since 2026-09-26 (#151 ruled, ovr.news#373); `uplifting v7` is still scored. ⚠️ v8's fitted normalization was never deployed; v9's is. `filters/human_thriving/v9/README.md` |
| solutions | v6 | 0.476 | — | 8.2K | `jeergrvgreg/solutions-filter-v6` | 2026-07-27 gate passed; normalization fitted 2026-07-28; LIVE. v6 weights on Hub 2026-07-30 (was: v4 repo shared — that mismatch + FILTER_VERSION 5.0 fixed in 403429d). |
| investment-risk **PAUSED 2026-08-25** | v6 | 0.497 | 0.465 | 10.4K | `jeergrvgreg/investment-risk-filter-v6` (private) | **2026-08-11 OP-POINT 4.0 → 4.25** (recall 0.7239 / spec 0.9740, was 0.7609 / 0.9550; normalization refit n=38,637 raw_min 4.25). Deployed `3d358d3`. **First accuracy number ever measured 2026-08-10.** 2026-02-21 |

### uplifting v7 — the consumer lens is NARROWER than this scorer's name (#107)

⚠️ **Thriving, the ovr.news lens this filter feeds, carries a narrower predicate than
"uplifting" implies.** `ovr.news/docs/BRAND.md` at `a70609b` (2026-08-13) defines it as
*a process going well **for people***, which **excludes** two shapes the scorer will
happily score: **harm-answered-only** (a wrong met with a response, where the story is the
wrong) and **institution-beneficiary** (the gain accrues to an organisation, not to
people).

**#107 is SCOPED, not reversed.** The scorer is not defective — it is faithfully serving a
definition ovr had not published when v7 was trained. The consequence is a live source of
false positives *by the lens's definition* while being true positives by the scorer's.

⛔ **This binds the v8 prompt.** `human_thriving` v8 must encode the narrower predicate,
which is why ADR-012's rename `uplifting` → `human_thriving` is **load-bearing rather than
hygiene**: the new name is the one the lens's definition matches.

⛔ **`investment_risk` RETIRED downstream 2026-09-17** (NexusMind ADR-025, NM#499); retirement narrative and the superseded un-pause procedure — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16). The verify below still asserts the retirement.

<!-- verify: if ! ssh -o BatchMode=yes -o ConnectTimeout=5 sadalsuud true 2>/dev/null; then echo "CANNOT VERIFY: sadalsuud unreachable"; else C=/home/jeroen/local_dev/NexusMind/config/app.yaml; L=$(ssh sadalsuud "grep -c \"^    - .investment_risk.\" $C" 2>/dev/null); A=$(ssh sadalsuud "grep -c \"^  aegis_export:\" $C" 2>/dev/null); R=$(test -d /home/jeroen/repos/_archive/nexusmind-investment_risk && echo 1 || echo 0); echo "enabled_filters lines: $L | aegis_export blocks: $A | archive present: $R"; if [ "$L" = 0 ] && [ "$A" = 0 ] && [ "$R" = 1 ]; then echo PASS; else echo "RETIREMENT NO LONGER HOLDS — a filter, an export block or the archive changed"; exit 1; fi; fi -->

| cultural_discovery | v5 | — | 0.697 (val) | 8.5K | `jeergrvgreg/cultural-discovery-filter-v5` | 2026-07-31 multilingual topic gate added to prefilter (LD#86); **gate VALIDATED in production 2026-08-01 via NM#284 shadow: observed pass 0.255 vs declared 0.25 (n=2099, full cycle)** — but still NOT ENFORCED (NM#284); 2026-05-31 v5 (#62 flags; DeepSeek oracle) |
| cultural_discovery | v6 | — | (v5's, reused) | 8.5K | `jeergrvgreg/cultural-discovery-filter-v6` | ⛔ **CUTOVER ATTEMPTED, FAILED AND REVERTED 2026-08-13** *(this row said "DOES NOT EXIST YET / blocked on two things" until 2026-08-16 — it was two days behind an event only `CLAUDE.md` recorded)*: NM#348 merged `d5943d3`, stage 2 loaded from the Hub, which cannot work on gpu-server under `HF_HUB_OFFLINE`. Scorer returned 500, the smoke test caught it, **one cycle lost and no bad data**. Fixed and verified offline (`dcf2860`), **not redeployed**. Rollback of a future cutover = delete v6's dir on gpu-server, which makes v5 latest again. ⚠️ **v5 ALREADY runs two-stage** — `filter_loader.py:148` sets `hybrid_class` from the PRESENCE of `inference_hybrid.py`, not from `config.yaml`, so v6 does not introduce probe screening; it changes the probe and threshold (~63.7% vs a measured 54.9% `stage1_low`). Earlier state, still true of the package: **package parity reached 2026-08-06.** v6 = v5's student weights + an e5 probe + a commerce-only prefilter; **no retrain** (#98). Keyword gate, 4 exclusion categories, 3 domain blocklists and the `evidence_quality` gatekeeper (#94) all removed. `score_scale_factor` 1.0. *(Superseded 2026-08-08, `4ee3b58`: normalization fitted and the Hub repo created — both blockers cleared; this row said "no normalization.json" until 2026-09-26.)* Ships stamping-only per ADR-022. |
| cultural-discovery | v4 | 0.74 | — | 8K | `jeergrvgreg/cultural-discovery-v4` | 2026-02-20 (superseded by v5) |
| belonging | v3 | — | — | v1 splits reshaped + 237 pos + 135 hard neg + ~800 easy neg | `jeergrvgreg/belonging-filter-v3` | **LIVE 2026-10-09** (NexusMind run `bd00dad6`), replacing v1. Gated on held-out set 3 (binding pass rule v2): PASS. ~¼ of v1's volume. Rollback rule + refit ≥ 2026-10-24: `filters/belonging/v3/STATUS.md` |
| belonging | v1 | 0.534 | 0.489 | 7.4K | `jeergrvgreg/belonging-filter-v1` | REPLACED 2026-10-09 by v3. Earlier:  2026-07-31 normalization REFIT (Mar-30 fit drifted, survivors under-ranked +1.0–2.1; NM#279) |
| belonging | v2 | — | — | — | — | **DRAFT prompt only (2026-10-01), PARKED 2026-10-02.** The definition was ruled (MIDDLE + "doing"). The next model reshapes v1's TRAINING DATA instead, the human_thriving v9 recipe (`docs/TODO.md` item 0; ledger `H-BV7`). Evidence: `docs/evidence/2026-10-02-belonging-reader-snapshot/` |
| nature_recovery | v4 | recall 0.65 / prec 0.85 @3.75 | 0.48 | 3.9K | `jeergrvgreg/nature-recovery-filter-v4` | 2026-07-10 (DeepSeek oracle; #70 protection scope; op-point 3.75 wired into TIER_THRESHOLDS + validated in prod output, F1) |
| nature_recovery | v2 | 0.63 | 0.53 | 3.5K | `jeergrvgreg/nature-recovery-filter-v2` | 2026-04-19 — kept as fallback (rollback = delete v4 dir; discovery falls back) |

<!-- prod-filters-table:end -->

Table rows `human_thriving v8` (superseded by v9 2026-09-25), `sustainability_technology v3` and `foresight v1` (both removed 2026-08-03) — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16).

**Per-lens RULE prefilters + NM#284 shadow measurement (2026-08-01/02)** — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16). Prefilters DELETED 2026-10-01 (decision 0); standing lessons live in CLAUDE.md Hard Constraints.

**Runtime content-type caps: NONE (2026-07-14).** NexusMind's `cap_triggers.py` `_TRIGGER_REGISTRY` is empty, so `cap_applied` is permanently `null` on every filter. `nature_recovery/climate_doom` was the only one ever deployed (2026-05-08, #161) and was retired: 3 production bites, 3 false positives, 0 saves — all three the trigger word inside a non-doom construction (`evitar su extinción`, `en peligro crítico de extinción`, `deforestation-free`), which a polarity-blind regex cannot see. #161's actual cause was `normalization.json` fitted at raw ≥ 1.5 instead of the 4.0 tier threshold, inflating correctly-scored doom (raw 2.2–3.3) to normalized 5.2–8.3. Filters' `config.yaml` `content_type_caps` still declare the **oracle** contract and are inert at runtime; the scorer log reports them as INERT. Enforced by `tests/unit/test_normalization_invariant.py` (since 2026-07-16: raw_min must equal the op-point ±0.01 — the fitter anchors the CDF's lower edge there by construction; the old `[op_point, 4.5]` band is gone).

**Normalization (ADR-014, refit 2026-07-10):** `cultural_discovery v5` + `investment_risk v6` now ship `percentile` normalization.json (were silently on linear `scale_factor` — the `version`/`filter_version` fitter bug). `nature_recovery v4` ships NO normalization (fresh version, `score_scale_factor 1.0`); refit due at ≥200 v4 prod articles (#72).

Note: Hub repo naming is inconsistent — some use `{filter}-v{N}`, others use `{filter}-filter-v{N}`. Deploy scripts rely on the name embedded in `inference_hub.py`, so this doesn't break anything, but it's worth normalizing at the next bump.

All use Gemma-3-1B base + LoRA. All have local, Hub, and hybrid inference paths.

## In Development

| Filter | Ver | Status |
|--------|-----|--------|
| thriving | v1 | PARKED indefinitely (ADR-015) — orthogonal lens design caused bimodal distribution |
| solutions | v6 | **LIVE** — gate passed 2026-07-27 (F1 0.739), normalization fitted 2026-07-28, own Hub repo since 2026-07-30. |

Rows `foresight v1` and `sustainability_technology v3` (REMOVED 2026-08-03, #43) — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16).

<!-- NOTE: consumer-side concerns (which ovr.news lens/tab uses which filter, frontend rollout)
     live in the NexusMind and ovr.news repos. This repo produces filters; mapping filters to
     product surfaces is a downstream concern. -->

## Repo-wide audit (2026-07-27)

Six stale packages REMOVED (LD#49) — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16). The verify below keeps asserting their absence.

<!-- verify: for p in ai-engineering-practice/v2 sustainability_technology/v2 cultural-discovery/v3 investment-risk/v5 uplifting/v5 signs_of_wisdom/v1; do test -e "filters/$p" && { echo "FAIL: filters/$p still present"; exit 0; }; done; echo PASS -->

## Other Filters (not ovr.news)

| Filter | Ver | Status |
|--------|-----|--------|
| ai-engineering-practice (→ augmented-engineering) | v2 | Ready for oracle scoring |
| seece | v1 | Concept only |

## Standalone filter products (separate platforms)

- **augmented-engineering** (renamed from ai-engineering-practice)
- **health-tech** (planned)
- **education** (planned)
- **investment-risk** (deployed, also used standalone)

## Backlog

- Commerce prefilter v2 — v1 needs rework for multilingual embeddings and context size
- train.py nested model/model/ fix (#29)

---

## uplifting v7 — first accuracy record, 2026-08-09 (and how to read it)

`uplifting v7` was deployed ~April with **no MAE recorded at all**. Measured
against its held-out oracle test split (660 rows, never seen by training or by
the calibration fit), using the **deployed** `calibration.json` rather than a
fresh fit, so the number describes what production computes.
Artifact: `filters/uplifting/v7/ground_truth_gate.json`.

    MAE raw 0.8110 -> calibrated 0.8398
    at the 4.0 op-point: recall 0.7361  precision 0.8154  specificity 0.9189
                         f1 0.7737   216 positives of 660

⚠️ **Do NOT rank filters on that 0.84 (ADR-023).** Each test split has its own
positive rate — uplifting **32.7%**, solutions **16.2%**, nature_recovery
**15.3%** — and positives are genuinely harder (per-article MAE 1.1954 on
positives vs 0.6668 on negatives, 1.79×), so a more enriched split scores worse
for identical quality. Composition explains **+0.0919 of the 0.3435** gap to
nature_recovery — ~27%, not all of it, so the residual may be real; it simply is
not the objective.

**What the MAE rule was written against** (2026-08-09 MAE ranking, RETRACTED) — MOVED to [`archive/filter-status-archive.md`](archive/filter-status-archive.md) (2026-10-16).

**The comparable numbers**, both conditional on the true class:

| filter | positive rate | recall | specificity | FPR on true negatives |
|---|---|---|---|---|
| uplifting v7 | 32.7% | 0.7361 | 0.9189 | **8.1%** |
| solutions v6 | 16.2% | 0.6707 | 0.9723 | 2.8% |
| nature_recovery v4 | 15.3% | 0.6500 | 0.9789 | 2.1% |

**uplifting has the best recall and the loosest gate.** Under ADR-023 that is
the wrong side of the trade → **#102**.

**Calibration is NOT a net negative** (an earlier claim, retracted): it raises
MAE but is indistinguishable on the decision — 5 articles of 660 change side,
inside the 37-row (5.6%) indeterminate band. Do not refit or drop it on the MAE
reading.

**Caveats in the artifact, not just here:** run on b650 CPU, while **production serves on
GPU** — so the open term is the DEVICE (CPU→CUDA, |0.1956|, 3 flips at 4.5), not the box:
the host contributes 0.0000 once pins and device match (2026-08-10 decomposition);
the 32.7% test positive rate is enriched and does not transfer to production's
~9% surfacing rate without reweighting.

**Ground-truth gates still missing:** `cultural_discovery v5` (belonging v3 PASSED held-out set 3, 2026-10-08),
`investment_risk v6`.
