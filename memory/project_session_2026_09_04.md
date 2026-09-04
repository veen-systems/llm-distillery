# Session 2026-09-04 — the student is trained, and the instrument that chose it was inert

**Spend $0.** No oracle calls. No model deployed, no threshold moved, no probe, no
production path touched. Branch `fix/train-select-metric-inert`,
commits `1878e7b` (code + tests) and `a0f63d8` (provenance + docs), both **unpushed**.
Tag `exp-015-training-code`. Registry: **EXP-015**.

## What happened

`/update-drift` first: **0 releases behind**, agent-ready-projects v1.36.1 = latest tag,
remote HEAD equals the clone's. Three globals byte-identical to the v1.36.1 reference install
(525/222/204 lines, 0 differing), with the template comparison (24) and v1.34.2 (23) run as
controls so the zeros were a real minimum. One finding: the `agent-ready-papers` decline
citation has rotted a third time — `session-log.md` says `docs/TODO.md:4052`, the adoption
history says `:4108`, it is **:4763**.

Then phase 6. Splits prepared from `labels_v84_merged.jsonl` (6,586 rows → 5268/658/660,
zero id overlap, all six dimension columns non-constant). Trained on **b650-gpu**, CUDA,
`venv-prodparity`, 6 epochs, batch 8, seed 42.

## ⛔⛔ THE KEEPER — a flag that parsed, ran, and did nothing, for every filter ever trained

`--select-metric recall_at_20` was accepted by argparse and **inert**. `dimension_weights_list`
was built only under `if args.sample_weight_scale > 0` (default 0.0), and that same list is what
`compute_metrics` needs to emit `recall_at_k` / `recall_medium` / NDCG. With it `None`,
selection fell to `improved = val_metrics["mae"] <= best_val_mae` — **aggregate MAE, on a corpus
that is 95.20% floor**, which ADR-023 forbids ranking on.

⛔ **The blast radius was already on disk**: of 18 `training_metadata.json`, 16 carry
`sample_weight_scale` 0/None, and four DEPLOYED filters (`solutions v6`, `cultural_discovery v5`,
`belonging v1`, `investment_risk v6`) have no needle keys in `training_history.json` at all.

⭐ **The part that generalises is the suite's silence.** Nothing in `tests/` referenced
`training.train`, so *"573 tests pass"* was true and carried **zero information** about the
changed module. A green suite that cannot execute the changed lines is not evidence about them.
→ working rule, **17th occurrence**.

## ⛔ Six errors of mine, four found by review rather than by me

1. **I reported the flag as working without proving the outcome changed** — the rule's own text,
   in the message announcing the fix.
2. **A tautology offered as an outcome proof.** *"The pre-fix run contains that string 0 times"* —
   for a literal the same commit introduced. No pre-fix run could have contained it. A presence
   check on a new constant, dressed as a before/after.
3. **I used MAE's shape to reason about recall**, one message after naming that exact substitution
   as the trap: *"MAE fell monotonically, so there was no sign of a turn."* The owner pushed back;
   the re-run moved the kept epoch 6 → 4. ⭐ *"No sign of X"* from an instrument that cannot show X
   is not evidence about X.
4. **I called the metric noise-dominated having measured no variance**, and used that to argue
   against measuring.
5. **`importlib.metadata.version("sklearn")`** — the dist is `scikit-learn`, so the lookup could
   not have said yes; I nearly reported a missing dependency that was installed.
6. **A grep that matched a different key.** `threshold: null` in `thriving/v1` sits under
   `hybrid_inference.stage1`, not `scoring.tiers.medium`; I was one step from reporting a live
   `TypeError` that does not exist.

## ✅ /review-changes, 4 lenses — 4 blockers, 12 warnings, all fixed or filed

⭐⭐ **Verification is not review, again.** 599 green tests, four hand-run controls and a full
guard sweep found **none** of it. The lenses found: `medium_threshold` silently wrong for the
`tier_thresholds`/`min_score` schema (`resilience/v1` really deploys at 4.5, read as 4.0) with a
log line **asserting a provenance it never checked**; metadata describing the RUN sitting beside
a field documented as describing the CHECKPOINT (partially re-breaking F3); the 94.9% figure
computed with **uniform weights** — the very defect under repair (→ **#145**, `prepare_data.py`
`:173` is an unweighted mean); and the epoch-4-vs-6 claim having **no on-disk evidence at all**.

⭐ **And a regression the fix itself introduced**: `recall_at_k` clamped with `min(k, n)` is
**identically 1.0 when n ≤ k** — verified, deliberately poor predictions score 1.000 at n=8/15/20 —
so with the strict `>` every small-val run pins epoch 1 forever. Pre-fix those runs fell back to
MAE and behaved sanely.

⭐ **The new test earned itself on its first run**, catching a defect in my own fix: I borrowed
`fit_normalization`'s `_lowest_nonzero` rule, and `resilience/v1` ships `high 6.5 / medium 4.5 /
low 2.5`, so it resolved to **2.5**. Almost every other filter sets `low: 0.0`, which makes the two
definitions coincide. ⭐ **A rule validated on the population where two definitions coincide has
not been validated.**

## ✅ EXP-015 — and the two arms are NOT distinguishable

Correcting selection **did** change the kept epoch (6 → 4), so the defect was not cosmetic. But
`recall_medium` **saturates at 0.5806 across epochs 4/5/6** — 18/31 — so the strict `>` tie-break
chose the epoch, not the metric (**#144**). On the untouched test split epoch 4 leads at 4.5 by
**two articles** on recall and two on specificity; **epoch 6 leads on both at 4.25**; they split at
4.0. ⭐ *A model that changes rank under a 0.25 threshold move is not distinguishable.* Reinforced
by **seed 42 not being bit-reproducible on CUDA** (0.5601 vs 0.5605, same code and data).

Raw test @4.5: **recall 0.514, specificity 0.9856**, positive rate 5.30%. Specificity matches or
beats the fleet; **recall is below all six** (0.59–0.72) — ⛔ but those are post-calibration and
v8 is not, so it is indicative only.

## ⛔ A traceability hole I created, and cannot fully close

`git commit --amend` orphaned `0697f5a`, the tree that actually produced the weights. Tagged
`exp-015-training-code` so gc cannot take it. ⛔ **A retrain does not recreate the artifact** —
seed 42 is not bit-reproducible here — so the choice before phase 9 is *retrain under a real
commit and rewrite the provenance*, or *record the exception*. Recommended: fold it into whatever
phase 6b/7 concludes, so the artifacts are written once.

## Issues

Filed **#144** (tie-break: strict `>` keeps the earliest of tied epochs; ties are routine because
`recall_medium`'s resolution is `1/n_positives`) and **#145** (`prepare_data.py` unweighted mean).
Commented on **#139** (the pre-existing `cultural_discovery v5` import failure, hit twice — and
⚠️ verifying it by stashing in a *fresh clone* yields a **skip**, not a pass, because the fixture
needs gitignored weights), **#136** (the deploy-guard blocked a docs commit on the project's own
idiom *"the shipped one"*), and **#127** (v8 now has provenance, but hand-built provenance records
the author's memory, not the run).

## ▶ NEXT — and this was done the same day, in a second session

**Phase 6b PROBE + phase 7 CALIBRATION** were completed on 2026-09-04 as **EXP-016**
(`docs/evidence/2026-09-04-v8-probe-calibration/`). ⛔ **Neither moved recall**, which is what
this section predicted they would: the probe is recall-safe (0 FN at the adopted 1.75 on both
splits) so Stage 1 was never the constraint, and the calibration is close to a monotone
rescale (Spearman 0.9977 against raw, AUC 0.9474 → 0.9488). ⚠️ **The 0.514 named above is a
b650-CUDA figure**; the CPU pass reads 0.486, one article apart. The live levers are now the
**phase-8 op-point re-derivation on the calibrated scale** (4.5 calibrated flags 17 test rows
where 4.5 raw flags 26) and then **H-V8-15** (clamp 0→1.0; `--use-head-tail`), one variable at
a time.
