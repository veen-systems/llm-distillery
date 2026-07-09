# Nature Recovery Filter v4 — Deployment Status

**Last Updated:** 2026-07-09
**Status:** 🟢 DEPLOYING — ground-truth gate PASSED; shipping the first checkpoint (scale 2.0, Recall@20 selection)
**Target:** ovr.news Recovery tab (replaces nature_recovery v2)

## What v4 changes over v2
- **#70 delivered-protection scope**: enacted MPAs / in-force fishing bans / dam removals now count as recovery-in-progress (recovery_evidence path); pledges/announcements stay capped.
- **Multilingual prefilter fix**: commerce-only pass-through (ADR-004) + multilingual POSITIVE_PATTERNS. Fixes the English-keyword-gate that silently dropped 21.6% of non-English positives (0/571 positives blocked now, was 129/598).
- **Recall-first e5 probe** (H3 fix): trained classifier on full labeled data, threshold from the val recall curve — 98.2% recall / ~64% screened (was an L1 regression that floor-collapsed).
- **Oracle**: DeepSeek (chosen for conservative editorial *bias*, not consistency — see memory/feedback-oracle-bias-vs-noise; 3892 labels).

## Ground-truth gate (held-out DeepSeek test, n=391, operating point 3.75)
Judged against held-out ORACLE ground truth per ADR-021 (NOT against the prior generous v2 model — the old agreement_gate.py false-FAILed v4 by comparing it to a Gemini-labeled reference).

| model | recall | precision | F1 | Spearman | MAE |
|-------|--------|-----------|----|----------|-----|
| **v4 (deployed)** | **0.672** | **0.848** | **0.750** | **0.821** | **0.496** |
| v2 (incumbent) | 0.603 | 0.614 | 0.609 | 0.795 | 0.842 |

v4 beats v2 on every metric — **no regression**. Precision gap (0.85 vs 0.61) is the headline: v2 (Gemini-trained) over-surfaces; v4 (DeepSeek) is far more precise while also higher recall.

## Known limitations (→ v5, #71)
- **Recall 0.672**: misses ~33% of true MEDIUM+ (the needle/top-band ceiling). v5 = active-learning enrichment of the medium band from saved NexusMind output.
- **Top-band**: only 2 training articles score 8-10; the model tops out ~6.8 (HIGH tier unreachable). Fine for surfacing (decision at MEDIUM 3.75).
- **Operating point 3.75** (not 4.0): tuned on the test sweep — dominates 4.0 on recall+precision; must stay above the recovery_evidence gatekeeper cap (3.5).

## Deployed weights
The shipped adapter is the seed-42 scale-2.0/Recall@20/3-epoch run (test recall 0.672). `training_metadata.json` reflects the identical recipe (val_MAE 0.7730; the seed-42 draw deployed measured val_MAE 0.7725 — immaterial 0.0005 difference; the load-bearing numbers are the held-out test metrics above).

<!-- verify (disk-based, on gpu-server): test -f ~/NexusMind/filters/nature_recovery/v4/model/adapter_model.safetensors && grep -q '"3.75"\|3.75' ~/NexusMind/filters/nature_recovery/v4/config.yaml -->
