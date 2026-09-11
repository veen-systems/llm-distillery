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
`llm-distillery#155`. Positive class `oracle_meta["scope_verdict"] == "harm_is_subject"`:
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

⚠️ **Read it against the null arm — and read the null's FLAG RATE before its catch count.**
The *"shuffled-label control caught 0 of 9"* defence holds at exactly one operating point: the
pre-registered val-picked rule. There the real arm flags **2.04%** of the panel and the null
**4.09%** — the null is genuinely rate-advantaged and still touches the 9 **zero** times. ⚠️ The
real arm's catch at that rule is **2.0 of 9** (band 0–3), not the 3 the table above reports at its
fixed gates.

⛔ **It does NOT hold across the plateau, and the wording here claimed it did until 2026-09-10.**
Over the 5-seed sweep (means over seeds, so not directly comparable to the ensemble table above):
at **0.65 and above the null flags 0.0 of 137 rows in all five seeds**, so its catch of zero is
**arithmetically forced, not measured** — an instrument that cannot say yes carries no information
when it says no. At **0.30 the null fires MORE than the real arm** (22.4 vs 10.6 rows), reversing
the defence outright. Full table: `docs/evidence/2026-09-10-harm-detector/` in llm-distillery.

## Verified

`scripts/verification/verify_harm_detector_v1.py` (**llm-distillery only** — it does not exist in
NexusMind; see the Artifacts note below) — run it wherever the detector is served.

- **The shipped module reproduces the builder**: max |Δ| **8.1e-07** over 137 rows. Not
  bit-identical because `panel_probs_ensemble` is stored rounded to 6 dp — ⚠️ **but rounding alone
  does not account for it**: 6-dp storage bounds one value's error at 5.0e-07, and 8.1e-07 is 1.62×
  that. The residual is the same order as the CPU-vs-CUDA term below (7.15e-07) and is consistent
  with the two hops running on different devices — **not verified**. Re-run both hops on one device
  before quoting this line as a precision claim.
- ⭐ **Device is immaterial for this detector**: CPU vs CUDA max |Δ| **7.15e-07**, and **0 verdict
  flips** at 0.30 / 0.50 / 0.70 / 0.85. ⛔ **Do not generalise this** — the Gemma student's
  CPU→CUDA term is **0.1956**. A floor belongs to a population and a mechanism, and this one was
  measured here, on this architecture, on these rows.
- Artifacts **byte-identical across both hops**, 6/6 (`models/SHA256SUMS.txt`).
- Contract held by `tests/unit/test_harm_detector_contract.py` (**llm-distillery only**; NexusMind
  ships `tests/unit/test_harm_preprocessor.py`, which asserts the stamping contract, not these
  three), which fails if a threshold appears in the module, if one reaches the built config, or if
  a declared head loses its hash.

⚠️ **Scores are not comparable across library stacks — and this architecture's own stack term is
UNMEASURED.** ⛔ The **0.2008** quoted elsewhere in the estate is the **Gemma-3-1B student's**
(`uplifting v7`, 660 rows, b650 vs gpu-server's venv, CPU both sides) — a different population and
mechanism, carried here as an order-of-magnitude caution only. Built with **sklearn 1.8.0**,
matching the other detectors' pickles.

## Artifacts

⚠️ **This differs by repo, and the vendored copy of this file cannot say so for itself.**
In **llm-distillery** `*.pkl` is gitignored (`.gitignore:73`), the pickles travel out-of-band, and
`models/SHA256SUMS.txt` is the manifest. In **NexusMind** the pickles are **committed** — 13.85 MB,
not ignored — each with its own `<file>.sha256` sidecar, and there is no `SHA256SUMS.txt`. That is
NexusMind's established convention (`obituary_detector` 9.8 MB, `violence_promotion` 29 MB are
committed the same way) and its deploy depends on it. `training_config.json` is tracked in both.

⛔ **Every repo-relative path below resolves in llm-distillery only.** This file is vendored into
NexusMind verbatim, so its Reproduce block is not runnable there.

## Wiring — NexusMind PR #474, **still a draft**

⭐ **In-process, not over HTTP** (owner direction, 2026-09-10). The other detectors call
gpu-server because the pipeline host has no GPU; NexusMind is consolidating into one GPU-hosted
package in the near term, which **removes that machine boundary** — and with it the chunking, the
request cap, the rate limiter, the two-deployable version skew, and a class of silent failure
where a changed response shape yields `None` scores that look real. Building the endpoint first
would have been building a deletion.

**Measured cost of staying in-process** — 137 real articles, mean body 4,189 chars, CPU:
**19.9 articles/s** on a 16-core Ryzen 7. ⚠️ **Measured on that box, not on the pipeline host.**
The pipeline host is an 8-core Ryzen 3, taken as **~2–2.5× SLOWER** (≈8–10 art/s, *derived, never
run there*), which puts a cycle's ~1,421-article intake at **~3 minutes** inside a 4-hour window.

1. Copy `models/` to the host; the loader now verifies every digest against `SHA256SUMS.txt` or
   per-file `.sha256` sidecars and **refuses to unpickle anything unverified**.
2. `pipeline.harm_detector.enabled: true`. `device: null` auto-selects CUDA when torch sees it.
3. ⛔ **Leave `max_articles_per_run` bounded.** An unbounded first run covers the whole
   `max_article_age_days` window — measured **34,661 articles, ~60–75 min** — which is
   llm-distillery`#152`'s outage shape. Newest files are stamped first, so the backlog drains
   over a few cycles and today's articles never wait.
4. Stamp only. **Gate nothing.** Then measure what it *would* block per lens, per cycle.
5. Only then a per-lens config decision. ⛔ **Never a cross-lens blocker.**

⚠️ **The panel behind every number here is `uplifting v7` / `human_thriving v8` display-eligible
rows only.** It says **nothing** about solutions, belonging, nature_recovery or cultural_discovery
— their numbers must come from the shadow stamp.

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
