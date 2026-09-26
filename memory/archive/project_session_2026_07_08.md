# Session 2026-07-07 → 07-09 — nature_recovery v4 build (planning + code + oracle re-label), pre-deploy

The v4 build arc before the deploy session (which is `project_session_2026_07_09.md`). Two working
days: planning/pivot (07-07/08) then code + oracle-labeling execution (07-08/09). **Nothing deployed
in these days** — training/gate/deploy were staged. Moved out of MEMORY.md 2026-07-10 to keep the
every-session index lean.

## 07-08/09 — nature_recovery v4 EXECUTED (code + re-label)

Executed the v4 plan through the code + oracle-labeling phases; **nothing deployed** (no model yet — training/gate/deploy staged, see `docs/nature_recovery_v4_RUNBOOK.md`). 8 commits `edc117a..046fa0d` on `nature-recovery-v4`, pushed.

- **C1 → (b)**: redefined `recovery_evidence` so delivered protection (enacted+in-force) scores ≥3 → clears the runtime gatekeeper via labels (gatekeeper code untouched; `content_type` never reaches inference, so the exemption option was unbuildable). Prefilter → commerce-only pass-through (recall bug 21.6%→1.3%, 129/598). Prompt+config: #70 path, `conservation_appeal` cap→soft-penalty, individual-animal example, oracle→deepseek.
- **§A.5 falsification pilot PASS** ($0.04, 28 stratified incl. multilingual): delivered protection surfaces (Central Arctic ban 1.8→5.15), pledges/decline/appeals stay capped. Then **full re-label 3892** (DeepSeek, **$4.81**, 0 err). Integrity-checked (hard caps not self-applied but gatekeeper handles it — see gotcha); 187 non-English positives score correctly.
- **4-model review battery** (opus×2 + sonnet×2) caught what my self-verify missed — esp. the **CRITICAL** v4 inference stack still importing v2 (would crash `NatureRecoveryScorer()`; my "verified both paths" only tested a replicated loader). All findings fixed: inference repoint, POSITIVE_PATTERNS regex, prompt consistency, pipeline latent bugs.
- **Metrics settled, not reinvented**: per filter-dev-guide Issue 4 (nr v1→v2 lineage), needle filters use **Recall@20/NDCG@10/FN@MEDIUM+** not MAE. Instrumented in `train.py` + checkpoint selection moved off aggregate MAE. `agreement_gate.py` written (4 NM#229 metrics; Source-A-not-independent + missing-protection-cohort caveats baked in).
- Balance ~$5.60. `huggingface_token` still empty. 3 new gotchas logged (version-bump imports; DeepSeek hard-cap non-application; review-before-spend).

## 07-07/08 — nature_recovery v3 → v4 planning

Big planning session; **no filter shipped** (deliberately paused). Full plan: **`docs/nature_recovery_v4_plan.md`** (read `## 0` first — 4-model review corrections).

- **v3 → v4 pivot.** Started as v3 decline-framing retrain (lld#60/#56); pivoted to **v4** (#70) when the oracle exercise showed delivered protection wins (MPAs / protected acreage) should surface as recovery — a prompt change. #70 filed.
- **DeepSeek single-oracle re-score DONE** ($3.99, balance ~$0.51): 3,641 corpus+negs + 831 editorial-publish positives → 448 confirmed positives (**high-band 3→36**) + 383 boundary negs. Validated: decline→1.5, positives preserved, DeepSeek correctly demotes Gemini/editorial over-labels (conservative-correct). **Labels gitignored on disk + backed up → `~/backups/nr_v4_labels_20260708.tar.gz`.**
- **4-model label audit** surfaced: (1) prefilter drops **21.6% of genuine recovery** — English keyword gate on a 20+-language firehose (project-wide: 13 prefilters, only belonging ships a probe); fix = strip to commerce-only + **multilingual e5-small probe**; (2) 6 dims ≈ 1 (PC1=91% halo) → protection can't be elevated by weighting, needs prompt/gatekeeper change; (3) conservation_appeal hard cap = MAE cliff → soft-penalty (cd v5 mechanism); (4) high-band too sparse to calibrate.
- **4-model PLAN review** (folded into `§0`): **C1** — the runtime `recovery_evidence` gatekeeper (cap 3.5 < 4.0) defeats #70 by construction → decide gatekeeper treatment first; **commit-nothing** risk; **deploy=NO** (no model/gate yet); reorder probe-last; full re-label (not partial); merge via `merge_cd_v5_deepseek_final.py` shape.
- **Also filed:** ovr.news **#262** (data archiving is lossy/unreliable — why rotted articles were unrecoverable). Scorer `score_deepseek_production.py` generalized (`--config`/`--prompt`). Branch `nature-recovery-v3` (rename to v4 on resume).
