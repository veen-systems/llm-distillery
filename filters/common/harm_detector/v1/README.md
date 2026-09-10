# Harm detector v1 — `harm_is_subject`, stamp-only

**Question it answers:** *is this article's dominant subject a harm* — a crime, disaster, war,
death or exploitation? Issue llm-distillery**#156**. Experiment `EXP-037`.

⛔ **IT STAMPS A SCORE AND DECIDES NOTHING. NO THRESHOLD IS SHIPPED.** ADR-022: *stamp always,
decide once.* Each lens's gate is a later config flip against a number already on the row. That
is not caution about the model — it is the only correct design here, because **the same article
is harmful under one lens's promise and constitutive of another's**: *"Community kitchens, boat
ambulances: Bihar copes with floods"* betrays Thriving's *"lives getting better"* and is arguably
exactly right under Solutions; Nature Recovery is **about** recovering from damage. Measured: of
the 9 articles both judges called harmful, **6 were already surfaced by another lens**.

⛔ **NOT DEPLOYED, NOT ENABLED.** The wiring is open as **NexusMind PR #474** (branch
`feat/harm-detector-shadow-stamp`), which ships `pipeline.harm_detector.enabled: false`.
⚠️ **That flag is NexusMind-side only** — review found the gpu-server loads the detector
unconditionally once the model directory is deployed, so "rollback = `enabled: false`" is true of
the stamping pass and **false of the server half**. NexusMind is frozen (owner, 2026-09-08).

## Architecture

```
title + " " + content  ->  frozen paraphrase-multilingual-mpnet-base-v2  ->  768-d
                       ->  StandardScaler  ->  5 x MLPClassifier(256,128)  ->  MEAN
```

Same contract as `obituary v5`, `violence_promotion v1`, `commerce v2`, except for the five heads.

⭐ **The ensemble is the fix for `H-DET2`, not a performance trick.** With everything else fixed,
`early_stopping=True` lets `random_state` choose the internal validation split. Measured on this
exact detector: at the val-picked operating point single seeds caught **0–3** of the 9 held-out
judged-harmful articles. **Shipping
"the best seed" is seed-shopping and ships a lottery ticket.** The mean of five removes the
choice, and it is nearly free — the embedding pass, which dominates, is shared.

## What it was trained on

`datasets/training/human_thriving_v8_scoped/`, rebuilt with `prepare_data.py --seed 42` after
`#155`. Positive class `oracle_meta["scope_verdict"] == "harm_is_subject"`:
**1,011 / 105 / 137** over train **5,268** / val **658** / test **660**.

## Measured — the ensemble

Held-out arbiter: the 137-row `EXP-031` panel (judged blind by both oracle families;
**0 of its ids appear in the training corpus**). "of 9" = both judges called it harmful;
"of 32" = Gemini did.

| gate | panel flagged | rate | of 9 | of 32 | test specificity | test recall |
|---|---|---|---|---|---|---|
| 0.30 | 10 | 7.30% | **3** | 7 | 0.9216 | 0.7445 |
| 0.50 | 6 | 4.38% | **3** | 5 | 0.9560 | 0.6934 |
| 0.70 | 4 | 2.92% | **3** | 3 | 0.9694 | 0.5839 |
| 0.85 | 3 | 2.19% | 2 | 2 | 0.9809 | 0.4307 |
| 0.90 | 1 | 0.73% | 0 | 0 | 0.9904 | 0.3650 |

⭐ **The ensemble holds 3 of 9 across a plateau from 0.30 to 0.70.** ⛔ **Corrected 2026-09-10 by
review — the earlier wording here said single seeds "bounced 0–3" over that plateau, and they do
not: over 0.30–0.70 they span 2–4, and at 0.30 three seeds catch 4, beating the ensemble's 3.**
The 0–3 spread is real but belongs to the *val-picked operating point*, not the plateau. So the
ensemble's value is that it removes the CHOICE of seed and is flat across a wide band — **not that
it beats every seed**, which the original sentence implied in the direction that flattered it.

⚠️ **Read it against the null arm, not against zero.** In `EXP-037` a shuffled-label detector
caught **0.0 of 9** while firing at **twice** the rate. That is what makes 3 of 9 a signal.

## Verified

`scripts/verification/verify_harm_detector_v1.py` — run it wherever the detector is served.

- **The shipped module reproduces the builder**: max |Δ| **8.1e-07** over 137 rows. Not
  bit-identical because `panel_probs_ensemble` is stored rounded to 6 dp — that |Δ| **is** the
  storage precision.
- ⭐ **Device is immaterial for this detector**: CPU vs CUDA max |Δ| **7.15e-07**, and **0 verdict
  flips** at 0.30 / 0.50 / 0.70 / 0.85. ⛔ **Do not generalise this** — the Gemma student's
  CPU→CUDA term is **0.1956**. A floor belongs to a population and a mechanism, and this one was
  measured here, on this architecture, on these rows.
- Artifacts **byte-identical across both hops**, 6/6 (`models/SHA256SUMS.txt`).
- Contract held by `tests/unit/test_harm_detector_contract.py`, which fails if a threshold
  appears in the module, if one reaches the built config, or if a declared head loses its hash.

⚠️ **Scores are not comparable across library stacks.** The **stack** noise floor of **0.2008**
was measured on exactly this architecture (mpnet + sklearn MLP across sentence-transformers
versions). Built with **sklearn 1.8.0**, matching the other detectors' pickles.

## Artifacts

⚠️ **This differs by repo, and the vendored copy of this file cannot say so for itself.**
In **llm-distillery** `*.pkl` is gitignored (`.gitignore:73`), the pickles travel out-of-band, and
`models/SHA256SUMS.txt` is the manifest. In **NexusMind** the pickles are **committed** — 13.85 MB,
not ignored — each with its own `<file>.sha256` sidecar, and there is no `SHA256SUMS.txt`. That is
NexusMind's established convention (`obituary_detector` 9.8 MB, `violence_promotion` 29 MB are
committed the same way) and its deploy depends on it. `training_config.json` is tracked in both.

⛔ **Every repo-relative path below resolves in llm-distillery only.** This file is vendored into
NexusMind verbatim, so its Reproduce block is not runnable there.

## Wiring — open as NexusMind PR #474, **not merged**

1. Copy `models/` out-of-band to the serving host; verify against `SHA256SUMS.txt` **before**
   restarting anything.
2. Instantiate once and batch-score. ⚠️ **The shipped PR does NOT share the embedder** — the
   gpu-server holds three separate `SentenceTransformer` instances (commerce, obituary, harm).
   Sharing one is llm-distillery`#89`, deliberately not attempted during a freeze.
3. Stamp `_harm_is_subject_score` and `_harm_detector_model` on **every** article. **Gate nothing.**
   ⚠️ Note the leading underscores — `HarmDetectorV1.stamp()` returns *un*-prefixed names and is not
   what the pipeline calls (dead code; a name trap if anyone wires it in).
4. Let it run, then measure what it *would* block per lens per cycle from the stamp.
5. Only then a per-lens config decision. Thriving first; ⛔ **never a cross-lens blocker.**

⚠️ **`#152`'s cold-start trap applies to anything new entering the pipeline.**
⚠️ **The panel is `uplifting v7` / `human_thriving v8` display-eligible rows only.** It says
**nothing** about solutions, belonging, nature_recovery or cultural_discovery. Their numbers must
come from the shadow stamp — not from this table.

## Reproduce

```bash
# b650-gpu, venv-prodparity
python3 filters/common/harm_detector/training/build_v1.py \
    --splits datasets/training/human_thriving_v8_scoped \
    --panel-content datasets/panel/panel_content.jsonl \
    --panel-judges docs/evidence/2026-09-08-thriving-harm-panel \
    --out-dir filters/common/harm_detector/v1/models \
    --report filters/common/harm_detector/v1/calibration_report.json
python3 scripts/verification/verify_harm_detector_v1.py
```
