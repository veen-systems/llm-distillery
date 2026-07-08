# nature_recovery v4 — Remaining-Steps Runbook

*State as of 2026-07-08 autonomous session. Everything below the line is DONE +
committed on branch `nature-recovery-v4`. This runbook covers only what remains —
the steps that need gpu-server time and/or the HuggingFace token (your actions).*

## ✅ Done + committed (verified locally)
- C1(b) resolved; prefilter → commerce-only (recall 21.6%→1.3%, 129/598); prompt+config revised.
- Full re-label: `datasets/scored/nature_recovery_v4_final_deepseek.jsonl` (3892, DeepSeek, $4.81, 0 errors). Integrity-checked; multilingual positives validated.
- Review battery (4 models) → all findings fixed: **CRITICAL** v4 inference stack repointed v2→v4; POSITIVE_PATTERNS regex; prompt consistency; pipeline latent bugs; ranking metrics in `train.py`; `agreement_gate.py`.
- Splits: `datasets/training/nature_recovery_v4/{train,val,test}.jsonl` (3112/389/391), held-out disjoint.
- Balance remaining: ~$5.60 DeepSeek. **`huggingface_token` in secrets.ini is still EMPTY.**

## ⚠️ Two things only you can do
1. **Fill `huggingface_token`** in `config/credentials/secrets.ini` (needed for the v2 student download in the gate, and for any Hub upload).
2. **Approve deploy** — blocked this session (C4). Deploy only after the gate PASSES.

---

## 1. e5 probe (recall-first) — REWRITE FIRST, then train (gpu-server)
`scripts/train_probe.py` is L1-regression (H3 defect — see its header). Rewrite as a
recall-first classifier BEFORE training:
- binary target `y = (gatekeepered weighted-avg >= 4.0)`; class-weighted BCE / balanced sampling
- pick threshold from the **val recall curve** at target FN on MEDIUM+ (not val_mae)
- validate FN-rate on the **129 known-blocked positives** (reproduce with `scripts/nr_v4_prefilter_recall_check.py`)
- embedding `intfloat/multilingual-e5-small`
- write threshold-selection + FN-rate as pure functions and **unit-test them** (mirror `agreement_gate.py`)
```bash
# on gpu-server (venv + PYTHONPATH + HF_HUB_OFFLINE per memory/gpu-server.md)
PYTHONPATH=. python scripts/train_probe.py --filter filters/nature_recovery/v4 \
    --data-dir datasets/training/nature_recovery_v4 \
    --embedding-model intfloat/multilingual-e5-small
# set filters/nature_recovery/v4/config.yaml hybrid_inference.stage1.threshold from the curve
```

## 2. Student (Gemma-3-1B + LoRA) — train (gpu-server)
```bash
scp -r datasets/training/nature_recovery_v4 gpu-server:~/llm-distillery/datasets/training/
# on gpu-server:
export PYTHONPATH=.; export HF_HUB_OFFLINE=1
PYTHONPATH=. python training/train.py \
    --filter filters/nature_recovery/v4 \
    --data-dir datasets/training/nature_recovery_v4 \
    --sample-weight-scale 2.0        # UPWEIGHT positives (needle lever, config=2.0)
```
- `train.py` now reports **Recall@20/10/50, NDCG@10/20, FN@MEDIUM+, per-band MAE** and
  **selects the checkpoint on Recall@20** (not aggregate MAE). Read those, not MAE.
- Use `load_base_model_for_seq_cls()`; **OLD PEFT key format; never run resave_adapter.py**.
- ⚠️ Only **2** articles in the 8-10 band, ~24 high-band in train → the top is barely
  trainable (H4). Consider clip/ceiling the top tier; do NOT per-band-isotonic on 2-3 pts.

## 3. Verify the inference-stack fix at runtime (gpu-server — needs torch)
The v2→v4 repoint was only statically verified locally (no torch). Confirm construction:
```bash
PYTHONPATH=. python -c "from filters.nature_recovery.v4.inference import NatureRecoveryScorer; NatureRecoveryScorer(use_prefilter=True); print('constructs OK')"
```

## 4. Calibrate (after training)
```bash
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/nature_recovery/v4 --data-dir datasets/training/nature_recovery_v4 \
    --test-data datasets/training/nature_recovery_v4/test.jsonl
```
- Inspect the isotonic curve; only ~2 top-band anchors → violent extrapolation risk (H4).
- fit_calibration currently reports aggregate per-dim MAE only + writes a stale
  `score_scale_factor`; add per-band MAE and ignore the score_scale_factor write (ADR-014).

## 5. Agreement gate (blocks deploy) — needs HF token + gpu-server
```bash
# a) curate a delivered-protection probe set (metric 3 — NOT frozen; use the pilot's
#    genuine delivered set: Central Arctic ban, French Polynesia, São Tomé, Europe dams…)
#    → datasets/gate/nr_v4_protection_probes.jsonl  (held out of training)
# b) dual-score the frozen cohorts with BOTH students:
#    - v4 student (local model/)
#    - v2 student from Hub: jeergrvgreg/nature-recovery-filter-v2  (NEEDS huggingface_token)
# c) run the gate:
PYTHONPATH=. python scripts/gate/agreement_gate.py \
    --v2-scored <v2_cohort_scores.jsonl> --v4-scored <v4_cohort_scores.jsonl> \
    --gate-dir datasets/gate --protection-probes datasets/gate/nr_v4_protection_probes.jsonl
```
- Note the built-in caveats: Source-A is ~93% in training (metrics 2/4 = guard, not
  clean generalization); metric 3 SKIPS unless the protection cohort is curated.
- Commit `gate_report.json`; post to NM#229.

## 6. Deploy (ONLY if gate PASSES) — needs HF token; forbidden this session
- Build cd v5's doc set (STATUS.md, __init__.py, calibration_report.md, dimension_analysis/).
- Hub upload `jeergrvgreg/nature-recovery-filter-v4`; `deploy_to_nexusmind.sh` (fix hardcoded
  C:/local_dev roots) → sadalsuud → gpu-server + manual `scp` of `model/` (#67). Verify probes.
- Keep v2 until v4 verified. Close #60; #56 → PARTIAL; update #70. File the two cross-cutting
  issues (multilingual prefilter recall bug; dimension-collapse experiment).

## Judgment call made autonomously (review on return)
- **Did NOT re-spend ~$5 to re-label** after the prompt fixes: the integrity check showed
  the prompt issues had nil impact on the $4.81 labels (affected articles are all
  non-surfacing; gatekeeper + soft-penalty both verified working). If you want pristine
  labels for the reference filter, re-run: `python scripts/nr_v4_build_relabel_input.py`
  then `score_deepseek_production.py --config filters/nature_recovery/v4/config.yaml`.
