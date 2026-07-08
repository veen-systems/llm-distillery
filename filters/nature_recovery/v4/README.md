# Nature Recovery Filter

**Version**: 2.0
**Status**: Deployed (HuggingFace Hub, gpu-server, sadalsuud)
**Philosophy**: "Nature recovers when we let it, and faster than we expect"
**Purpose**: Detect documented ecosystem recovery — hope grounded in data, not aspiration
**Target**: ovr.news Recovery tab

## What changed in v2

v1 had zero discrimination in production — 98.6% of articles scored below 1.0 (#41). Root cause: extreme class imbalance (95% noise) caused the model to predict near-zero for everything.

v2 fixes this with:
1. **Active learning enrichment** — 237 MEDIUM+ articles added (3,280 → 3,517 total)
2. **Score-based sample weighting** — `--sample-weight-scale 2` upweights positive articles from 5% to ~41% of loss

### Results

| Metric | v1 | v2 |
|--------|-----|-----|
| Val MAE (calibrated) | 0.507 | 0.533 |
| MEDIUM+ MAE | 2.49 | 1.87 |
| Recall@20 | 0.55 | **0.70** |
| NDCG@10 | 0.71 | **0.86** |
| False negatives (oracle>=2, student<2) | 41% | **17%** |
| Student score range | [0, 5.08] | [0, 6.25] |
| Probe MAE | 0.50 | 0.49 |

Overall MAE is slightly worse because v1 cheated — predicting zero for everything gives low MAE when 95% of articles are noise. The ranking metrics show the real improvement.

## Concept

Finds articles with **measured evidence** that ecosystems recover when human pressure is removed or restoration is applied. Grounded in restoration ecology, rewilding science, and proven recoveries (ozone layer, Yellowstone wolves, Thames fish, bald eagles).

Deliberately excludes: climate doom, climate tech (-> sustainability_technology), greenwashing, fundraising appeals, policy announcements without outcomes, symbolic gestures.

See `DEEP_ROOTS.md` for full scientific and philosophical grounding.

## Dimensions (6)

| # | Dimension | Weight | Role |
|---|-----------|--------|------|
| 1 | recovery_evidence | 25% | GATEKEEPER — is nature actually recovering? |
| 2 | measurable_outcomes | 20% | Quantified data: before/after, populations, areas |
| 3 | ecological_significance | 20% | Keystone species, critical habitats, trophic cascades |
| 4 | restoration_scale | 15% | Geographic scope and temporal duration |
| 5 | human_agency | 10% | Recovery caused by deliberate action or policy? |
| 6 | protection_durability | 10% | Will this recovery last? |

## Anti-Contamination (ADR-010)

| Content Type | Max Score | Example |
|---|---|---|
| climate_doom | 2.0 | "Extinction crisis accelerates" |
| climate_tech | 3.0 | "New solar panel efficiency record" |
| greenwashing | 2.0 | "Company pledges net zero by 2050" |
| conservation_appeal | 2.0 | "Donate to save the rainforest" |
| policy_announcement | 3.0 | "Government to protect 30% of ocean" |
| symbolic_gesture | 3.0 | "1,000 trees planted on Earth Day" |

## Training

- **Model**: Gemma-3-1B + LoRA (13M trainable / 1B total)
- **Data**: 3,517 articles (2,811 train / 352 val / 354 test)
- **Sample weighting**: scale=2.0 (weight = 1 + WA * 2)
- **Epochs**: 3 (best at epoch 3)
- **Calibration**: isotonic regression, val MAE 0.632 -> 0.533 (+15.7%)
- **Probe**: e5-small MLP, MAE 0.49 (early stop epoch 24)

## Deployment

- HuggingFace Hub: `jeergrvgreg/nature-recovery-filter-v2` (private)
- gpu-server: `~/NexusMind/filters/nature_recovery/v2/`
- sadalsuud: `~/local_dev/NexusMind/filters/nature_recovery/v2/`

## Remaining

- [ ] Normalization — needs production CDF (NexusMind must switch to v2 first)
- [ ] Hybrid threshold recalibration on production data
- [ ] ovr.news Recovery tab frontend integration

## Key Design Decisions

- **Consolidated from 8 to 6 dimensions**: Bottom 3 (5%, 4%, 3% weight) too low for student model to learn.
- **recovery_evidence as gatekeeper** (not ecosystem_health): More precise — "is nature bouncing back?" not "is this ecosystem important?"
- **Boundary with sustainability_technology**: This filter scores *ecological outcomes*; sustainability_tech scores *technologies* via LCSA.
- **ADR-010 applied**: Critical filters per dimension, content type caps, gatekeeper.
- **Sample weighting for needle filters**: Standard MSE training fails on 95/5 class imbalance. See `memory/sample-weighting-needle-filters.md`.
