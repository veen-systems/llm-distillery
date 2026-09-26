# Session 2026-07-10 — nature_recovery v4 op-point fix + normalization refit, both validated in production

Follow-on from the 2026-07-09 deploy session. This session hardened the v4 deploy, fixed a
systemic normalization bug on two other live filters, and validated everything against real
production output (not just live smoke tests). Branch `nature-recovery-v4`, `d6c3cf5..` pushed.

## What shipped (all deployed + validated in prod)

1. **Normalization refit — cd v5 + investment_risk v6 (task "(a)").** `fit_normalization.py` filtered on
   `analysis.filter_version` but production writes `nexus_mind_attributes.version` → `--filter-version`
   excluded EVERY article in BOTH the local loader and the embedded SSH extraction script, so cd v5 +
   invR v6 silently ran on linear `score_scale_factor` (never got percentile) since going live. Fixed both
   loaders (`str(v.get("version", v.get("filter_version")))`), refit (cd 2257 / invR 26375 prod articles),
   deployed via a clean `main` worktree (never touched the local `fix/269` WIP), live-verified
   `normalization_method: percentile`. Filed as augmented-engineering **#28**.

2. **Multi-model adversarial review (12 agents, opus/sonnet finders + haiku/fable/opus/sonnet verifiers).**
   4 findings raised, all 3 distinct ones confirmed real by MY reproduction (the review's own "cosmetic"
   downgrade of F1 was wrong — the verifier grepped NexusMind but never checked ovr.news, which is where
   the tier-visibility gate lives). See gotcha "verify the reviewer too".
   - **F1 (headline): the canonical filter's documented op-point `3.75` was wired to NOTHING.** Runtime
     `TIER_THRESHOLDS` hardcoded medium=4.0; no scoring code reads config's `tiers`; ovr.news hides
     tier=low ("only the top tiers make it to the site"). So v4 ran at un-tuned 4.0 the whole prior deploy
     and the [3.75,4.0) band was scored+hidden. Deploy verify was `grep -q 3.75 config.yaml` (inert field).
     **Fixed**: wired 3.75 into `base_scorer.py`, deployed, live-verified `_assign_tier(3.8)=medium`.
   - **F2**: `ground_truth_gate.py` hardcoded MEDIUM=4.0, no override → couldn't reproduce the deploy's
     cited numbers, would mis-select a future v5. Added `--threshold`, defaulting to read
     `scoring.tiers.medium.threshold` from config so the gate always matches what deploys.
   - **F3**: `train.py` `best_val_mae` recorded the global-min-MAE epoch, not the saved max-recall
     checkpoint → metadata cited an MAE the deployed model never hit. Now records the saved epoch's MAE.

3. **Re-gated v4 at 3.75, reproduced not assessed** (n=391 held-out, deployed adapters): v4 recall **0.650**
   / prec **0.848** / Spearman 0.821, dominates v2 (0.583/0.614) on every metric. Corrected docs — the
   config comment's advertised 0.60→0.66 gain does NOT reproduce (real gain 0.638→0.650); headline "0.67"
   is 0.65 on the deployed adapter (prec/Spearman/MAE match exactly; recall ~0.02 low = known CUDA
   nondeterminism draw). Fixed CLAUDE.md, STATUS.md, ADR-021, config + base_scorer comments.

## Production validation (complete-infra test, the real proof)

The user's other session ran the full Fluxus→Nexus→ovr pipeline. Auto-watched sadalsuud for fresh
`filtered_*.jsonl` and validated all three changes in **real output**:
- cd v5 + invR v6: `scale_factor → percentile` confirmed.
- nature_recovery v4: `[3.75,4.0)→medium` confirmed (1 article in band this batch, tiered medium;
  pre-fix it would have been low + hidden). normalization_method `none` (correct, fresh version).

Gotcha caught mid-validation: gpu-server logs in **UTC** (looked like clock skew / a stalled run); the
run was fine, just mid-flight scoring filters sequentially.

## Cross-machine state (all consistent, verified)

situla llm-distillery pushed to origin; NexusMind `main @ a34a781` on situla + sadalsuud; gpu-server
scorer deployed + healthy (7 filters); gpu-server `~/llm-distillery` training copy synced byte-identical
(base_scorer 3.75). Two production pushes to NexusMind main this session (138a892 normalization,
a34a781 base_scorer 3.75).

## Also
- Blog draft `dev.jeroenveen.nl/drafts/bias-without-a-self.md` — the "agent reproduces named cognitive
  biases despite no ego" post (mirror of `epistemic-humility`). Uncommitted by design (user's voice,
  awaiting cold re-read + citation verification + cross-model review).
- Framework bumped v1.10.4 → **v1.10.6** (no-op: v1.10.5/v1.10.6 are doc-only PATCHes, "pinned consumers
  need not bump"; v1.10.6's "agent-write boundary" principle is already how this session operated).
- New: FILTER_PLAYBOOK pit "a config value read by no code is inert"; 2 gotchas (inert op-point,
  verify-the-reviewer); filter-status.md nature_recovery v2→v4.

## Open follow-ups
- **#72** — v4 normalization refit once ≥200 v4 prod MEDIUM+ articles accumulate (~5/batch, so a while).
- **#71** — v5 recall (gather false-negatives + high-scorers from saved NexusMind output).
- **solutions v4** (#43) prompt drafting — the ADR-020 validation case (unchanged from prior sessions).
- Blog draft ship steps (user's call).
