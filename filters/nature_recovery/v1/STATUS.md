# Nature Recovery Filter - Development Status

**Last Updated:** 2026-03-06
**Status:** Phases 1-9 Complete — Deployed to Hub + gpu-server

---

## Completed

- [x] **Phase 1: Planning** (2026-03-05):
  - [x] Concept grounding documented (DEEP_ROOTS.md)
    - Restoration ecology, rewilding science, planetary boundaries
    - 14 proven recoveries catalogued (ozone, bald eagle, Yellowstone wolves, Thames, etc.)
    - Clear "what this is NOT" section: doom, climate tech, greenwashing, appeals, announcements, gestures
  - [x] Dimensions consolidated from 8 to 6 (config.yaml)
    - Dropped: connectivity (5%), historical_validation (4%), attribution (3%) — too low weight for student to learn
    - Merged: permanence + connectivity → `protection_durability`
    - Reframed: attribution → `human_agency` (broader, more observable)
    - New structure: recovery_evidence (25%), measurable_outcomes (20%), ecological_significance (20%), restoration_scale (15%), human_agency (10%), protection_durability (10%)
  - [x] Dimension independence verified — all 6 pairs pass "high X + low Y" test
    - Key test cases: anecdotal recovery (high evidence, low data), trivial greening (high data, low significance), temporary shutdown (high agency, low durability)
  - [x] Gatekeeper defined: `recovery_evidence` < 3 caps overall at 3.5
    - Without evidence of actual recovery, article stays LOW — blocks doom, pledges, appeals
  - [x] Content type caps added for 6 lookalike categories
    - climate_doom (max 2.0), climate_tech (max 3.0), greenwashing (max 2.0), conservation_appeal (max 2.0), policy_announcement (max 3.0), symbolic_gesture (max 3.0)
    - Each has exceptions for edge cases (e.g., policy_announcement excepted if retrospective with outcomes)
  - [x] Weights verified: 0.25 + 0.20 + 0.20 + 0.15 + 0.10 + 0.10 = 1.00
  - [x] Tiers defined: HIGH >= 7.0, MEDIUM >= 4.0, LOW < 4.0
  - [x] Config updated: Gemma-3-1B, head_tail 256+256, target_samples 7000
  - [x] Phase 1 validated against guide checklist — all criteria PASS

### Phase 1 Validation Report

| Guide Requirement | Status |
|---|---|
| Purpose clear and specific | PASS — "evidence of measurable ecosystem recovery" |
| 6-8 dimensions with descriptions | PASS — 6 dimensions, each with scale, evidence_focus, critical_filters |
| Tiers defined with thresholds | PASS — 3 tiers (7.0 / 4.0 / 0.0) |
| At least 1 gatekeeper | PASS — recovery_evidence (threshold 3, cap 3.5) |
| Weights sum to 1.0 | PASS — verified |
| Use case documented | PASS — ovr.news Recovery tab |

| ADR-010 Requirement | Status |
|---|---|
| Crisp HIGH vs NOT boundary | PASS — "documented recovery with data" vs "doom/plans/tech/pledges" |
| Critical filters per dimension | PASS — all 6 dimensions |
| Content type caps (3-5+ categories) | PASS — 6 categories with exceptions |
| Gatekeeper dimension | PASS — recovery_evidence |

### Design Decisions

**Why 6 dimensions, not 8?**
ADR-010 finding: oracle consistency predicts MAE better than dimension count. Belonging v1 scored MAE 0.49 on 6 dimensions and cultural-discovery v4 scored 0.74 on 5. ⚠️ *Caveat added 2026-09-06:* this read *"outperforms"*. **Retracted as an ordering** — the two MAEs come from different splits with different positive rates, no band was computed for either, and **ADR-023 forbids ranking filters on MAE** (a more enriched split carries mechanically larger per-article error at identical quality). The design argument below does not depend on the comparison. The issue isn't count — it's whether each dimension is *observable* and *independently variable*. The old bottom-3 dimensions (connectivity 5%, historical_validation 4%, attribution 3%) totaled only 12% weight — too low for a 1B student to learn meaningfully.

**Why recovery_evidence as gatekeeper, not ecosystem_health?**
The original config used `ecosystem_health` with threshold 5.0. But ecosystem_health conflated "recovery happening" with "ecosystem importance." An article about a thriving coral reef that was never degraded would score high on ecosystem_health but isn't about *recovery*. The new `recovery_evidence` dimension specifically asks: "is nature bouncing back?" — more precise as a gatekeeper.

**Boundary with sustainability_technology:**
sustainability_technology scores *technologies* via LCSA (readiness, cost, lifecycle impact). nature_recovery scores *ecological outcomes*. A solar panel article → sustainability_tech. Fish returning to a river → nature_recovery. An article about solar panels reducing PM2.5 *and* documenting bird populations returning → both filters could score it, but on different aspects.

---

- [x] **Phase 2: Prompt Architecture** (2026-03-05):
  - [x] Oracle prompt rewritten in belonging v1 production pattern (prompt-compressed.md)
  - [x] Step 1 scope check with IN SCOPE / OUT OF SCOPE and NOISE Detection Checklist
  - [x] Inline CRITICAL FILTERS on all 6 dimensions (before scale tables)
  - [x] Gatekeeper rule stated inline at recovery_evidence dimension
  - [x] 10 contrastive examples showing dimension independence (5 annotated key patterns)
  - [x] Pre-classification step with 6 content type caps (matching config.yaml exactly)
  - [x] 3 validation examples with JSON: HIGH (8.5, bald eagle), MEDIUM (5.8, Adriatic fish), LOW (1.2, extinction doom)
  - [x] Anti-hallucination rule: EXACT QUOTE requirement
  - [x] Modern format with INPUT DATA placeholder (no .format() conflicts)
  - [x] JSON schema: 6 dimensions + content_type, NO tier/stage/overall_score fields
  - [x] Structure validated against belonging v1 — all checks PASS

### Phase 2 Validation Report

| Guide Requirement | Status |
|---|---|
| Prompt format: modern with INPUT DATA placeholder | PASS |
| Header: Purpose, Version, Focus, Philosophy, Oracle Output | PASS |
| Scope section: IN SCOPE / OUT OF SCOPE | PASS |
| Gatekeeper rules documented and positioned correctly | PASS |
| All dimensions have inline critical filters + scoring rubrics | PASS |
| Contrastive examples showing dimension independence | PASS |
| JSON output: NO tier/stage classification fields | PASS |
| Content type caps match config.yaml | PASS |
| Anti-hallucination rule present | PASS |
| Validation examples: HIGH, MEDIUM, LOW with JSON | PASS |

- [x] **Phase 3: Oracle Validation** (2026-03-05):
  - [x] Scored 87 articles (43 from 100-article sample + 44 from 60 recovery-enriched candidates)
  - [x] Tier distribution: 1 HIGH (1%), 2 MEDIUM (2%), 84 LOW (97%) — confirms needle-in-haystack
  - [x] Gatekeeper working: 0 violations (recovery_evidence < 3 correctly caps overall at 3.5)
  - [x] Content type caps working: policy_announcement, climate_doom, climate_tech all correctly capped
  - [x] Content types detected: 71 out_of_scope, 7 climate_tech, 3 policy_announcement, 3 climate_doom, 3 ecosystem_recovery
  - [x] Dimension independence: insufficient positive articles (n=3) for reliable correlation analysis
    - The 3 positives DO show meaningful variation (e.g., high human_agency + lower protection_durability)
    - High correlation matrix (r=0.74-0.99) driven by uniform zero/one scores on out_of_scope articles
    - Will reassess after batch labeling with screen+merge yields more positives
  - [x] Oracle scoring quality: oracle correctly distinguishes recovery articles from doom, tech, appeals
  - **Verdict: PROCEED to batch labeling.** Oracle is discriminating well. Dimension independence needs more data but shows promise on the few positives we have.

- [x] **Phase 3b: Embedding Screening** (2026-03-06):
  - [x] Extracted 3 positive articles as e5-small embedding seeds
  - [x] Screened 595,351 articles from 4 corpus files using cosine similarity to centroid
  - [x] Produced 415 unique candidates (top 0.07% by similarity)
  - [x] Similarity range: 0.958 (top) to 0.898 (500th), median corpus: 0.839
  - [x] Methodology documented as ADR-011: Embedding-Based Screening for Needle Filters
  - Oracle-scored 248 candidates: 14 HIGH (5.6%), 68 MEDIUM (27.4%), 166 LOW (66.9%)
  - Dimension correlation (MEDIUM+ only, n=82): all pairs r<0.73 — no problematic redundancy
  - Methodology documented as ADR-011: Embedding-Based Screening for Needle Filters

- [x] **Phase 4: Prefilter** (2026-03-05):
  - [x] Rewritten using filters.common.base_prefilter.BasePreFilter
  - [x] 7.5% pass rate on random corpus (nature-related content only)

- [x] **Phase 5: Batch Labeling** (2026-03-06):
  - [x] Scored 3,050 prefilter-passing random articles (negatives)
  - [x] Merged with 248 embedding-screened + 87 Phase 3 validation articles
  - [x] Total: 3,280 unique scored articles after deduplication
  - [x] Distribution: 17 HIGH (0.5%), 103 MEDIUM (3.1%), 3,160 LOW (96.3%)
  - [x] Training splits prepared: 2,623 train / 328 val / 329 test

- [x] **Phase 6: Training** (2026-03-06):
  - [x] Gemma-3-1B + LoRA on gpu-server, 3 epochs
  - [x] Val MAE: 0.540 (Epoch 1: 0.782, Epoch 2: 0.580, Epoch 3: 0.540)
  - [x] Best model saved at epoch 3
  - [x] All inference files created: inference.py, inference_hub.py, inference_hybrid.py

- [x] **Phase 7: Calibration** (2026-03-06):
  - [x] Isotonic regression fitted on 328 val articles
  - [x] Val MAE: 0.540 -> 0.507 (+6.2%)
  - [x] Test MAE: 0.489 (raw) -> 0.501 (calibrated, slight regression typical for small skewed datasets)
  - [x] Score range expansion working: negative predictions mapped to 0, compressed upper range expanded
  - [x] Tier recovery on val: medium 4 -> 5 (oracle: 11)

- [x] **Phase 8: Hybrid Probe** (2026-03-06):
  - [x] e5-small MLP probe trained on 2,623 train / 328 val articles
  - [x] Probe MAE: 0.50 (early stopping at epoch 29)
  - [x] Saved to `probe/embedding_probe_e5small.pkl`
- [x] **Phase 9: Deployment** (2026-03-06):
  - [x] Uploaded to HuggingFace Hub: `jeergrvgreg/nature-recovery-filter-v1` (private)
  - [x] Hub verification passed: PeftModel.from_pretrained() loads correctly
  - [x] Deployed to gpu-server: ~/NexusMind/filters/nature_recovery/v1/
  - [x] Import verified on gpu-server (GPU busy with existing scorer, model load deferred)
  - [ ] ovr.news Recovery tab integration (NexusMind frontend work)

---

## v2 Retraining (2026-04-15)

**Problem:** v1 model had zero discrimination in production — raw scores maxed at 6.52, 98.6% of 34,977 articles scored below 1.0 (#41). The recovery lens on ovr.news was effectively empty.

**Root cause:** Extreme class imbalance in training data. 95% of articles had WA 0-1 (noise). Standard MSE training learned to predict near-zero for everything — the MSE-optimal strategy when nearly all targets are zero. See `memory/sample-weighting-needle-filters.md` for full analysis.

**Fix:** Two changes combined:
1. **Active learning enrichment** — 237 production MEDIUM+ articles added (v1 3,280 → v2 3,517 total, WA>2 from 4.8% to 8.5%)
2. **Score-based sample weighting** — `--sample-weight-scale 2` (weight = 1 + WA × 2). Positive articles went from 5% to ~41% of total loss contribution.

**Training:** Gemma-3-1B + LoRA, 3 epochs on gpu-server, best model at epoch 3.

### v1 vs v2 comparison

Overall MAE favors v1 (0.448 vs 0.534) but is misleading — v1 scored low MAE by predicting near-zero for everything. Ranking metrics show the real improvement:

| Metric | v1 | v2 | Improvement |
|--------|-----|-----|-------------|
| Overall MAE | 0.448 | 0.534 | worse (misleading) |
| MEDIUM+ MAE | 2.490 | 1.874 | **+25%** |
| Recall@10 | 0.50 | 0.60 | **+20%** |
| Recall@20 | 0.55 | 0.70 | **+27%** |
| Recall@50 | 0.64 | 0.76 | **+19%** |
| NDCG@10 | 0.712 | 0.861 | **+21%** |
| NDCG@20 | 0.755 | 0.851 | **+13%** |
| False negatives (oracle>=2, student<2) | 41% | 17% | **-24pp** |
| Score range | [0, 5.08] | [0.01, 6.25] | wider |

**Key takeaway:** For needle-in-haystack filters, MAE is the wrong metric. Recall@k and NDCG measure what actually matters — does the lens show the right articles? v2 finds 70% of the top-20 articles (v1: 55%) and misses only 17% of positives (v1: 41%).

### Remaining steps for v2 deployment
- [ ] Fit calibration (isotonic regression on val set)
- [ ] Retrain e5-small embedding probe
- [ ] Fit normalization (production CDF)
- [ ] Upload to HuggingFace Hub
- [ ] Deploy to sadalsuud + gpu-server
- [ ] Update config.yaml version to 2.0

---

## Key Files

| File | Purpose |
|------|---------|
| `config.yaml` | Dimensions, weights, content type caps, gatekeeper |
| `prompt-compressed.md` | Oracle prompt (production) |
| `prefilter.py` | Rule-based nature content filter |
| `base_scorer.py` | Base class with dimensions, weights, tiers, gatekeeper |
| `inference.py` | Local model inference |
| `inference_hub.py` | HuggingFace Hub inference |
| `inference_hybrid.py` | Two-stage hybrid inference (probe + model) |
| `calibration.json` | Per-dimension isotonic regression |
| `model/` | LoRA adapter + tokenizer |
| `DEEP_ROOTS.md` | Scientific and philosophical grounding |
| `STATUS.md` | This file — development progress tracker |
| `README.md` | Summary and quick reference |

---

## Dimensions (weights)

1. **recovery_evidence** (25%) — Is nature actually recovering? **[GATEKEEPER]**
2. **measurable_outcomes** (20%) — Quantified data: before/after, populations, areas
3. **ecological_significance** (20%) — Keystone species, critical habitats, trophic cascades
4. **restoration_scale** (15%) — Geographic scope and temporal duration
5. **human_agency** (10%) — Recovery caused by deliberate action or policy?
6. **protection_durability** (10%) — Will this recovery last?
