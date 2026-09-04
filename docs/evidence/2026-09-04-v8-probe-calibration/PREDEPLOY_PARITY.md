# Is v8's scorer actually complete? — part-by-part against the five deployed packages

**2026-09-04, before any deploy decision. $0.** Compared `human_thriving/v8` against the
packages that demonstrably work in production — `uplifting/v7`, `cultural_discovery/v5`,
`belonging/v1`, `nature_recovery/v4`, `solutions/v6` — mechanically, not by eye.

⛔ **`verify_filter_package.py` cannot answer this and passing it proves little.** It reports
**7/7** on v8 today. It checks that parts are PRESENT and importable; it does not check that
they are CONSISTENT WITH EACH OTHER, and an inconsistent package scores silently and wrongly
rather than failing. That is the "absence counts as success" shape logged in `566254b`.

**Verdict: v8 is structurally complete. Four real gaps, all known and none of them a scoring
defect. Two consistency invariants were unguarded and are now pinned fleet-wide.**

---

## 1. Files — six the deployed five all have and v8 does not

| missing | verdict |
|---|---|
| `model/` | ⛔ **deploy blocker**, by design — weights are gitignored (#97) and live only on `b650-gpu`. Step 0.5's `check_weights_backed_up` already refuses on this; `verify_filter_package.py` does not. |
| `normalization.json` | expected — **Phase E**, not yet run |
| `ground_truth_gate.json` | expected — **Phase D**, not yet run |
| `prefilter.py` | ✅ **deliberate.** ADR-018/019 *Amendment 2026-08-21*: new filters ship no per-lens prefilter. Not a gap. |
| `README.md` | owed — `memory/filter-doc-standard.md`, with `DEEP_ROOTS.md` and `README_MODEL.md` |
| `prompt-compressed.md` | ⚠️ provenance only — see §3 |

Nothing else. v8 additionally carries its prompt lineage (`prompt-v8-*.md`, `PROMPTS.md`) and
the MAE-selected training arm, which no deployed package has and which cost nothing.

## 2. Code — the scorer classes are complete

Parsed every `base_scorer.py`, `inference.py` and `inference_hybrid.py` with `ast` and diffed
class attributes, methods and module constants against the union of the deployed five.

**v8 lacks exactly one thing any deployed package has: `DEFAULT_THRESHOLD` in
`inference_hybrid.py` — and its absence is the point.** v8 reads the Stage-1 threshold from
`config.yaml` instead, and `test_human_thriving_v8_stage1_threshold.py` fails if the constant
comes back. Every other attribute and method is present.

Runtime constants, checked against two deployed scorers and against themselves:

| | v7 | nr v4 | v8 |
|---|---|---|---|
| weights sum to 1.0 | ✅ | ✅ | ✅ |
| `DIMENSION_NAMES` == `DIMENSION_WEIGHTS` keys | ✅ | ✅ | ✅ |
| gatekeeper dimension is a real dimension | ✅ | ✅ | ✅ |
| `MAX_TOKEN_LENGTH` / `DEFAULT_BATCH_SIZE` | 512 / 16 | 512 / 16 | 512 / 16 |

## 3. Config — every key NexusMind reads, and what absence does

NexusMind touches four things on a package: `scoring`, `prefilter`, `content_type_caps` and
the class paths. Traced each against v8's config:

- **`prefilter`** → `production_scorer.py:338` reads only `prefilter.expected_pass_rate` and
  **returns `None` when absent**. That key was *deleted* from `nature_recovery` and
  `solutions` deliberately (#93) — v8 lacking it matches where the project moved.
- **`scoring.content_type_caps`** → `production_scorer.py:581` falls through to `or {}`, and
  the cap loop then does not execute. v8 documents its absence where the block would be.
- **`scoring`** → present, complete, dimensions and tiers both.
- **class paths** → resolved from files on disk, all three present.

⚠️ **`prompt-compressed.md`**: `filter_base_scorer._compute_prompt_hash` looks for exactly
that name (or `prompt.md`), so **v8's `prompt_hash` is `None`** where every deployed filter
has one. It feeds `get_metadata()`, which **nothing in NexusMind reads** — a provenance gap,
not a scoring defect. Resolve at Phase F **by copying, never renaming**: 6,586 labels record
`prompt-candidate-tail.md` as their provenance.

## 4. ⭐ The two invariants nobody was checking — now pinned

Both were found by this comparison, neither was violated, and both are the kind that fail
silently rather than loudly. `tests/unit/test_filter_package_consistency.py`, fleet-wide.

### (a) The config must match what the model was trained with

`_load_preprocessing_config` reads `preprocessing.head_tail.enabled` and **defaults it to
False when the block is absent**. `training_metadata.json` records `use_head_tail` for the run
that made the weights. If they disagree, **every article is truncated differently at inference
than in training** — no error, no log, no zero score, just a wrong number.

| filter | config says | trained with | |
|---|---|---|---|
| cultural_discovery v5 | True | True | ✅ |
| belonging v1 | True | True | ✅ |
| nature_recovery v4 | True | True | ✅ |
| solutions v6 | True | True | ✅ |
| **human_thriving v8** | **False (by absence)** | **False** | ✅ |
| uplifting v7 | True | *no `training_metadata.json`* | ⚠️ cannot verify |

**v8 is consistent — but consistent by absence, which is invisible.** All five deployed
filters state `enabled: true`; v8 states nothing and inherits the default.

⛔ **The live trap: `H-V8-15` arm (b) is literally `--use-head-tail`.** Retrain v8 with it and
forget the config block, and the deployed model is fed a differently-shaped article than it
was trained on, silently. The test now fails in exactly that case — mutation-verified.

⚠️ `uplifting v7` cannot be checked: it ships no `training_metadata.json`, which is the same
gap its own `NO_HUB` file documents. Skipped with a reason, not passed.

### (b) The probe must emit one score per dimension

`EmbeddingStage` rebuilds the probe from the pickle's own `model_config`, so a probe trained
for a different dimension count **loads without complaint** and weights the wrong slots.

| filter | probe in/out | dims | objective |
|---|---|---|---|
| uplifting v7 | 384 / 6 | 6 ✅ | *(not recorded)* |
| cultural_discovery v5 | 384 / **5** | 5 ✅ | *(not recorded)* |
| belonging v1 | 384 / 6 | 6 ✅ | *(not recorded)* |
| nature_recovery v4 | 384 / 6 | 6 ✅ | recall |
| solutions v6 | 384 / **7** | 7 ✅ | recall |
| **human_thriving v8** | **384 / 6** | **6 ✅** | **recall** |

The count is **not 6 everywhere** — cd v5 has 5 and solutions v6 has 7 — so a hardcoded check
would pass on four packages and be wrong on two. Mutation-verified by removing a dimension
from `solutions v6` and confirming the test fails.

⭐ v8's probe objective (`recall`) matches the two other needle filters. Three of six deployed
probes record **no objective at all**, because `--seed`/metrics recording postdates them.

## 5. Incidental finding: deployed probes are pickled on CUDA

A plain `pickle.load` of `cultural_discovery v5`'s probe **raises** on a CPU-only machine
(`Attempting to deserialize object on a CUDA device`). Production is unaffected —
`EmbeddingStage._load_probe` monkeypatches `torch.storage._load_from_bytes` to map to CPU,
under a lock, for exactly this reason. **v8's probe was trained on CPU and has no CUDA
tensors**, so it is the first probe in the repo that loads without that patch. Not a defect
either way; worth knowing before anyone writes a tool that reads probes directly.

---

## What is actually left before deploy

| | blocker? |
|---|---|
| weights on gpu-server | ⛔ **yes** — Step 0.5 refuses; `verify_filter_package.py` will not |
| Phase D gate + op-point on the calibrated scale | ⛔ **yes** |
| Phase E normalization | ⛔ **yes**, and it precedes deploy in the plan |
| retiring `uplifting v7` | ⛔ **yes** — the loader keys on the filter *directory*, so v8 arrives as a **seventh** filter and v7 keeps running unless retired |
| `README.md` / `DEEP_ROOTS.md` / `README_MODEL.md` | doc standard, Phase F1 gates on package parity |
| `prompt-compressed.md` copy | provenance only |

**No part of the scorer itself is missing or misimplemented.**
