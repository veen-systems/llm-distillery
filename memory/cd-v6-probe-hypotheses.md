---
name: cd-v6-probe-hypotheses
description: cultural_discovery v6 (#98) — which hypotheses about replacing the keyword topic gate with an e5 probe were tested, confirmed, refuted, or are still open. Read before touching cd v6 or arguing from its numbers.
type: project
---

# cultural_discovery v6 probe — hypotheses (2026-08-06)

Package `filters/cultural_discovery/v6/`, issue #98. Scope agreed with the owner:
**probe first, dimensions later** — the scoring strand stays on #87.

Companion files: `filters/cultural_discovery/v6/STATUS.md` (full measurement),
`prefilter-length-floor-hypotheses.md` (the sibling gate-enforcement record),
`score-batch-shape-noise.md` (#95, whose floor does *not* apply to the probe).

## CONFIRMED

**H1 — a multilingual embedding probe removes the per-language coverage gap.**
Held-out production, 64 cycles, 2,653 surfacing rows. Keyword gate blocks 12.7%
of surfacing articles (en 12.4% / non-en 13.2%); probe @ 2.50 blocks **1 article
in 2,653** — 20 of 27 languages at exactly 0.0%, only Portuguese non-zero. The
gap does not narrow, it disappears, which is what "cannot have a per-language
keyword gap by construction" predicts.
<!-- verify: filters/cultural_discovery/v6/STATUS.md "Criteria 1 and 2" table -->

**H2 — the probe beats the gate on ORACLE ground truth, not just on agreement
with the student.** Test split, 75 MEDIUM+ positives: probe @ 2.50 FN **0/75**,
gate **10/75**. This is the arm that matters, because criteria 1–2 measure
agreement with a student that shares training labels with the probe while the
gate never did.

**H3 — the probe is batch-invariant; #95 does not have a probe analogue.**
Shuffled order, chunk 256 → 97, encode batch 64 → 13 → 1: max |Δ| **3×10⁻⁶**,
mean 5×10⁻⁷, **zero threshold flips**, zero articles within max|Δ| of the
threshold. Student scores move up to |0.162| (#95); probe scores do not. So a
per-article probe decision IS reproducible, and #95's caveat attaches to the raw
score side of any probe-vs-gate comparison, never to the probe side.
<!-- verify: PYTHONPATH=. python scripts/gate/probe_batch_invariance.py on gpu-server -->

**H4 — `train_probe.py`'s reported val FN is optimistic by construction.** It
selects the threshold off the val recall curve and then reports FN on that same
curve. At 3.025 it reported val FN 1.3%; held-out test gives **6.7%**, 5×
higher. Not a bug in the trainer — a selection effect that any future filter
using `--objective recall` will inherit. **Always re-measure FN on a split the
threshold was not selected on.**

## REFUTED

**H5 (refuted) — "the probe screens at least as much as the gate."** It does
not. On the production firehose the probe @ 2.50 passes 0.3629 against the
gate's 0.2983 — it screens **63.7% vs 70.2%**, i.e. 6.5 points *less*. #98
criterion 2 is a genuine regression, accepted only because the surfacing cost
falls from 337 articles to 1.

**H6 (refuted) — "63.7% is fine because it matches nature_recovery v4's ~64%."**
nr v4's figure is a **val** screening rate on its own label set; 63.7% is a
**production firehose** rate. Not comparable. cd v6's own val-set equivalent is
51.2%. This was written into `config.yaml` and `STATUS.md` before a review lens
caught it — the *second* val-vs-production category error in the same day's
work, after a screening-parity claim with the identical shape.

**H7 (refuted) — "the 5 positives the lower threshold recovers are recall wins."**
All five were read. **Four are off-lens**: an immunogenicity-prediction paper,
Flock surveillance cameras, ad-data deanonymisation of French spies, a
sea-level-rise dyke. The oracle scored them ≥ 4.0 on `discovery_novelty` +
`evidence_quality` with `cross_cultural_connection` at 0–2 — #87's lens dilution
inside the labels. So "FN 6.7% → 0.0%" partly measures label noise. **2.50 is
still right, but on the structural argument** (recall is Stage 1's job,
precision is Stage 2's; a screening threshold is the wrong place to hide lens
policy), not on the FN count.

## OPEN

- **Does removing the gate change anything measurable?** Criterion 4 is not
  started. The A/B says the probe is strictly better at *screening*, but the
  gate also blocks four exclusion categories (tourism_fluff, celebrity_art,
  political_conflict, appropriation_debate — 55 of 337 blocks in the window)
  which the probe does not obviously replace.
- **#99 — `classify_content_type` is a second consumer** of
  `DISCOVERY_PATTERNS` and is *not* replaced by a probe. Unresolved by v6.
- **Whether the probe would hold up under enforcement.** It has never run in
  production; unlike the rule prefilter (NexusMind#284) a probe actually
  executes, so this turns cd screening reader-visible for the first time.

## RESOLVED 2026-08-06 evening (owner decisions)

- **Criterion 4 executed.** Keyword gate, four exclusion categories, three domain
  blocklists and the custom `apply_filter` deleted; `prefilter.py` 800 → ~90
  lines. `classify_content_type` went with them — **the open question above
  ("what replaces it") resolved to "nothing, because nothing consumed it"**:
  grepped before deleting, its only callers repo-wide were the self-tests inside
  each cd version's own `prefilter.py`. #99 closes by removal.
- **Package parity reached.** Three inference modules, `calibration.json` copied
  from v5, `score_scale_factor` corrected 1.2829 → 1.0. Stage 2 loads from the
  **Hub by default**, unlike nature_recovery v4 — cd ships no local `model/`.
- **The gatekeeper is gone** (#94). Never bound on 8,551 labelled articles, and
  its cap equalled the op-point, so it could not change visibility.
- **The student is UNCHANGED.** v6 = v5's weights + new screening. This is why
  copying v5's calibration is correct and copying its normalization would not be.

## Traps

- **Both blockers CLEARED 2026-08-08; the package is ready, the cutover is not
  done.** `jeergrvgreg/cultural-discovery-filter-v6` now exists (private, v5's
  adapter verbatim — `adapter_model.safetensors` md5
  `bd4e79f2716ca1a4cb47209e6d0e0199` on both repos, 364 OLD-format
  `.lora_A/.lora_B.weight` keys, 0 `.default.`), `normalization.json` is fitted
  (n=3,680, raw_min 4.0), `--check-hub` is **9/9**, and the package was loaded
  END-TO-END from its own Hub repo and scored (on-lens 6.47/medium vs off-lens
  0.59/low, `calibration loaded: True`). **v6 is still NOT deployed** — nothing
  has been changed in production.
- **`normalization.json` must NOT be *copied* from v5 — but fitting it from
  v5-scoped production rows IS valid, and the "historical rescore" framing was
  both overstated and circular.** The fitter refuses only because it scopes to
  `filter_version=6.0` while all 222,360 production rows are `5.0`; and a v6
  rescore needs the Hub repo first (cd loads its student from the Hub), so this
  blocker sat *behind* the other one. The population argument is about the
  **firehose**; the fitter uses only rows at `raw >= 4.0`, where the probe
  removes **1 of 2,653** and **0** high-tier (#98 STATUS.md). The one thing that
  could have invalidated reuse — `score_scale_factor` 1.2829 → 1.0 — does not:
  `production_scorer.py` computes `raw_weighted_average` at post-processing
  step 1, *before* the scale factor, which appears only in the fallback branch.
  Justification is recorded in the artifact's own `provenance_note`.
  **Refit from real 6.0 rows once ≥200 surfacing rows accumulate after cutover.**
- **`--check-hub` returns `repo not found` for a private repo when `HF_TOKEN` is
  unset** — Hub 404s rather than leak existence, and the script says so in a
  comment. Its first run here was a false FAIL on a repo that existed. Export
  `HF_TOKEN` from `config/credentials/secrets.ini` before believing that check.
- **`_load_calibration` fails silently** when the file is missing (`self.calibration
  = None`, no warning). It is present now — but that is why its absence was
  invisible for as long as it was.
- **`--offset` in the reproduce commands counts back from a growing file list**,
  so the same offset selects a different window every day. Pin by filename.
- **sadalsuud's NexusMind still carries the 235-stem pre-`80dd399` gate.** Do not
  fix by syncing — v6 deletes that file. Recorded on #86.
