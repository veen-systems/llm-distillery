---
name: project_session_2026_09_10
description: The detector-architecture strand — four experiments, three closed, and two corrections I made against myself
metadata:
  type: project
---

# 2026-09-10 — the frozen-mpnet detectors: four questions, $0, nothing deployed touched

**Trigger:** a cross-session request from the ovr.news session. Their owner asked whether a
BERT-like encoder (RobBERT-2026, NeoBERT-base 275M) would beat what we run. Answer: **we
already run one.** The pre-scorer detectors are frozen **XLM-RoBERTa-base**
(`paraphrase-multilingual-mpnet-base-v2`, vocab 250,002, 12 layers, 768-d) with a
`StandardScaler` + `MLPClassifier(256,128)` head. Verified from the cached `config.json`, not
from a docstring.

**Spend: $0.** No oracle calls. Commits `8846369`, `e68838a`, `de3066d` (+ this curate).
Registry `EXP-033`–`EXP-036`; hypotheses `H-DET1`–`H-DET6`; issues **#158**, **#159** opened.

## What was settled

1. **Window 128 → 512 buys nothing** (`EXP-033`). Every seed band overlaps; violence_promotion
   *loses* recall at 0.95; 3.82× GPU cost, 3.68× CPU. **128 is now a defensible baseline**, which
   answers the "crippled baseline" objection to any future fine-tuning comparison.
2. **The v3/v4/v5 recall comparison is unusable** (`EXP-034`). Three different orderings across
   five seeds, all bands overlapping. v4's mean is the **highest**, reversing ovr's ADR-042 flag.
3. **The misses are a title/body POOLING conflict** (`EXP-035`). 44% of the 77 misses are the two
   halves of an article disagreeing inside one mean-pooled 128-token vector.
4. **The detector is not blind to non-Latin scripts** (`EXP-036`). Latin 1.252% vs non-Latin
   1.249% over 319,156 stamped production rows; every script reaches max ≈ 1.0.

## ⭐ The two corrections I made against myself, and they are the record worth keeping

**(a) I refuted a peer's hypothesis by testing their EXAMPLES, not their CLAIM.** ovr proposed
that a good obituary headline over a long biography gets dragged down. I scored their two example
headlines, found both at 0.98–1.00 title-only, and said *refuted*. Measured over the population:
**22.1% of all misses are exactly that mechanism.** Their two rows genuinely do not reproduce; the
class does. **"Refuted" needs a population behind it, not an example.**

**(b) I measured a magnitude against the wrong bar.** I added that dilution was *"real but
bounded; it does not reach 1e-4."* It never had to — it only had to cross **0.85**, the operating
point. The number was right and the reference point was wrong, and nothing fires on that.

⭐ Both landed on the same day as a third instance of the same family, peer-reported: two figures
of the same kind (**n=1,529** vs **n=1,537**, both "the obituary heldout") printed as comparable.
Three surfaces, one shape — **a real number checked against the wrong reference.**

## Traps hit, worth repeating

- **`v4_train_seed.jsonl` (11,304 rows) is NOT v4's corpus. `v4b_train_seed.jsonl` (11,308) is.**
  Identified by label counts against the shipped `training_config.json`, never by filename. A
  file off by one character and four rows would have produced a clean-looking grid answering a
  different question.
- **Leakage had to be computed, not hand-listed:** 25 heldout rows are in v5's training corpus,
  4 in v4's, 0 in v3's. Excluding the union gives n=1,537 and reconciles the published n=1,529
  (which drops all **33 panel-graded** rows — the 8-row gap is rows a human adjudicated but no
  model trained on).
- **`early_stopping=True` makes `random_state` pick the validation split.** Obituary recall at
  0.85 spans **0.6599–0.8081** with everything else fixed. Every shipped detector metric in this
  repo is one draw (**#158**).

## Cosmetic, filed not fixed

`NexusMind/deploy/gpu-server/main.py` hardcodes `model_version="v4"` in the obituary response and
its docstring still says SHADOW, while **v5 is what loads** (pickles md5-verified on the host) and
enforcement is live. The only caller discards the field — `_obituary_model` is stamped from
`MODEL_VERSION` = v5 on both branches — so **no stored row is affected.**

## State

Nothing deployed changed. **v5 stays live at 0.85.** No filter package, config or threshold was
touched. Both remote hosts left clean; sadalsuud was read-only.
<!-- verify: python3 scripts/verification/check_experiment_registry.py -->
