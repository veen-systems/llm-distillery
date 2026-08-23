# Binary gate standard — commerce, obituary, violence, and the crime blocker

**2026-08-23.** Comparison of the three deployed binary gates, what to harmonize, what to leave
alone, and the shape `crime` (#129) should be built to.

Verified against the packages in this repo **and the running box** (sadalsuud), not from memory.

---

## 1. What is already the same — more than expected

All three are the same machine and the same contract:

- Frozen `paraphrase-multilingual-mpnet-base-v2` (768-d) → `StandardScaler` → sklearn
  `MLPClassifier` → `predict_proba`. CPU, ~90ms/article, 50+ languages.
- Identical private surface: `_load_models()`, `_prepare_text(article|str)`.
- Identical public surface: `batch_predict(articles, batch_size=32)`, `get_score(article) -> float`.
- Identical constructor: `(threshold: float, model_dir: Optional[Path], device: str = "cpu")`.
- Identical return dict: `{is_<concept>: bool, score: float, inference_time_ms, version}`.
- Identical stamp triple on the article: `_<concept>_score`, `_is_<concept>`, `_<concept>_model`.
- Identical config triple: `enabled`, `threshold`, `enforce`.
- Versioned package dirs (`v1/`, `v2/` …) with the model under `v*/models/`.

**A new gate is therefore a small subclass, not a new design.**

## 2. What differs

| | `commerce_prefilter` | `obituary_detector` | `violence_promotion` |
|---|---|---|---|
| deployed version | v2 | v5 | v1 |
| class name | `CommercePrefilterV2` | `ObituaryDetectorV5` | `ViolencePromotionFilterV1` |
| predicate method | `is_commerce` | `is_obituary` | `is_violence_promotion` |
| code default threshold | 0.95 | 0.90 | 0.95 |
| **live** threshold (config) | 0.95 | **0.85** | 0.95 |
| `enforce` **default if key absent** | **`True`** | `False` | `False` |
| package `config.yaml` | ✗ | ✗ | **✓** |
| `oracle.py` + `prompt.md` in package | ✗ | ✗ (prompt embedded in a validation script) | **✓** |
| `calibration_report.json` | ✗ (`training/backtest_results*.json`) | ✓ per version | ✓ |
| panel/validation tooling | `docs/compare_commerce.py` | **✓ `validation/panel_audit*.py`** | ✗ |
| pipeline stage | `src/preprocessing/commerce.py` | `src/preprocessing/obituary.py` | **`scripts/main.py`, two inline methods** |
| drop point | `_is_duplicate` load gate | `_is_duplicate` load gate | **`_enforce_violence_promotion()`** |
| **saves what it blocks** | ✗ (`save_blocked: true` is **inert**) | ✗ | **✓ `data/prefiltered_out/violence_promotion/`** |

### Which differences are load-bearing and which are accident

- ⭐ **The drop-point split is load-bearing, and correctly documented.** `_is_duplicate` runs inside
  `load_articles`, which `_run_shared_dedup` calls **before** violence stamping — so a check there
  is a no-op for violence. Commerce and obituary work there only because their preprocessors
  rewrite the input JSONL earlier in the run. `scripts/main.py:1115` warns against "restoring" a
  check without moving the stamping. **The cause is ORDERING, not design.**
- **The `enforce`-default split is deliberate**: commerce has enforced unconditionally since
  ADR-004, so a missing key must preserve enforcement; the other two were opt-in after a shadow
  run, so a missing key must not silently arm them.
- **Everything else is accident** — three naming conventions, three package layouts, and one
  inert config key.

## 3. ⭐⭐ The one that matters: only ONE of three can be audited

**`violence_promotion` was auditable on 2026-08-23 solely because it wrote its flagged articles
to `data/prefiltered_out/`.** 166 files, 11,826 rows — that corpus is what turned a 26-day
stall into an hour's work and a verified production flip (#82).

**`commerce_prefilter` and `obituary_detector` are enforcing in production right now and save
nothing.** There is no way to ask what they removed, no way to measure their precision, and no
way to notice a regression. `commerce_prefilter.save_blocked: true` sits in the live config and
**has no consumer anywhere in the codebase** — grep returns nothing.

⛔ **A gate that drops content and keeps no record of what it dropped cannot be audited, and its
false positives are unobservable by construction.** Obituary blocks at 0.85, the most aggressive
threshold of the three, on a model whose own README records recall 0.75 — and nobody can see
what that costs.

## 4. Proposal

### P1 — every gate writes what it blocks *(do this first; it is the cheapest and worth the most)*
Give commerce and obituary the same `data/prefiltered_out/{gate}/flagged_<ts>_<n>.jsonl` output
violence already has. Then make `save_blocked` real or delete it — an inert key is worse than no
key. **⚠️ Include `content`**: violence's flagged files carry title/url/score only, which forced
today's audit to re-hydrate from `data/filtered/`. Write enough to adjudicate from.

### P2 — one stage shape
Move violence stamping to `src/preprocessing/violence.py`, running before the load gate, so all
three stamp in preprocessing and all three drop in `_is_duplicate`. This deletes the two-phase
special case and the warning comment that guards it. **Verify by executing**, not by reading:
the current arrangement exists precisely because an earlier check silently did nothing.

### P3 — a shared base class
`filters/common/binary_gate.py` holding `_load_models`, `_prepare_text`, `batch_predict`,
`get_score`, and a generic `predict()`; subclasses declare `CONCEPT`, `VERSION`,
`DEFAULT_THRESHOLD`. Keep the per-gate predicate (`is_commerce`…) as a thin alias so no caller
changes. **~95% of the three inference files is already identical.**

### P4 — standard package contents
Every gate ships: `v*/inference.py`, `v*/models/`, `v*/config.yaml`, `v*/calibration_report.json`,
`oracle.py` + `prompt.md` (the labelling definition, in the package, not inside a validation
script), `training/`, `validation/panel_audit.py`, `README.md`, `docs/CHANGE_REQUEST_NEXUSMIND.md`.

### ⛔ P5 — do NOT rename anything
`commerce_prefilter` / `obituary_detector` / `violence_promotion` stay. Three deployed packages,
cross-repo copies, config keys and stamp names on persisted rows — ADR-012 closed a rename
backlog for exactly this reason. **Fix the shape for new gates; leave the names.**

## 5. What `crime` (#129) inherits

Build it as the union of the best of each:

| from | take |
|---|---|
| **violence** | `oracle.py` + `prompt.md` in the package; `config.yaml`; `prefiltered_out/` writing; stamp-then-enforce with `enforce` default **false** |
| **obituary** | `validation/panel_audit.py` and the multi-judge pattern; per-version `calibration_report.json`; the **"primary purpose" sharpening** — block the crime *event*, keep pieces that merely use a crime |
| **commerce** | nothing structural; it is the least standardised of the three |

Plus, from the 2026-08-23 audits:

- ⛔ **Ship `prefiltered_out/` writing WITH CONTENT from day one.** Auditability is not a
  follow-up; it is the thing that determines whether the gate ever gets enforced.
- ⛔ **Judge the gate on the SURFACING population.** 99.6% of violence flags never reach a lens
  op-point; precision over all flags described articles no reader could see. Measure precision
  over articles that are flagged **and** clear a lens threshold.
- ⛔ **Mine hard negatives from the surfacing set too** — FPs ran ~50% there vs ~8% among
  keyword-matched flags.
- ⚠️ **`qwen3:14b` is not a usable panel lab** (unparseable on 74/75, and it zeroed a
  positive control on 2026-08-22). Use `qwen2.5:14b` + a second judge, and always include a
  random-negative control arm that proves the judge can say no.
