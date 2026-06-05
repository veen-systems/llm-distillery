# Calibration History

Long-arc record of scorer training, calibration, and oracle-prompt experiments — what worked, what didn't, and what shouldn't be retried. Loaded when calibration work starts.

## What lives here vs elsewhere

Per the governance schema in ducroq/llm-distillery#69:

| Category | Lives in |
|---|---|
| Scorer training, label-set, hard-negatives, oracle prompts | **this file** |
| Pipeline prompt behaviour (brand-voice, gate, summarization) | `ovr.news/docs/hypothesis-log.md` Dead Ends |
| Infrastructure, deployment, GPU contention, model loading | `ovr.news/memory/infra.md` and `vmodel/memory/gotcha-log.md` |
| Architecture / ADR-superseding decisions | `docs/adr/` (Superseded ADRs) |

Cross-link, don't duplicate: when a scorer retrain was triggered by a pipeline-prompt issue, each side has a one-line pointer to the other; the substance lives in whichever repo owns it.

---

## Dead Ends (don't retry these)

Compact "what we tried, why it failed, don't retry" entries. Pattern adopted from the vmodel pattern cluster — see [ducroq/agent-ready-projects#16](https://github.com/ducroq/agent-ready-projects/issues/16) for the cross-repo tracker. Sibling adoptions: [ovr.news commit 6132725](https://github.com/ducroq/ovr.news/commit/6132725) (shipped 2026-06-05), [ducroq/NexusMind#230](https://github.com/ducroq/NexusMind/issues/230) (pending).

- **Pure embedding + linear/MLP probe as substitute for fine-tuning** (uplifting v5 comparison, 2026-01). 12 embedding+probe combinations tested on uplifting_v5; best (e5-large-v2 + MLP) MAE 0.860 vs fine-tuned Qwen2.5-1.5B 0.680 — **+26.4% worse**. All others 32–48% worse on the dimensional-regression task; multilingual rerun (mpnet / MiniLM / multilingual-e5 / bge-m3) didn't close the gap. Full results in `research/embedding_vs_finetuning/results/uplifting_v5_comparison_report.md`; resolution note in `docs/OPEN_QUESTIONS.md` line 22. **Don't retry** replacing the fine-tuned student with frozen-embedding + probe for nuanced multi-dimensional regression — embeddings capture topic, not quality. Commerce binary classification is the exception (embeddings won 98.3% vs 97.8% F1, kept as `base_prefilter`).

- **Naive PyTorch dynamic INT8 quantization on Gemma-3-1B** (#24, 2026-03-07). Uplifting v6 val 50-article benchmark: 2.6× faster, 3.3× smaller — but MAE jumped FP32 0.749 → INT8 **1.378 (+0.63)**. FP16 on CPU emits NaN (no native x86 FP16 compute). Per-tensor dynamic quant with no calibration data destroys the score head and attention layers. Full benchmark in `docs/experiments/quantization-benchmark-2026-03-07.md`. **Don't retry** `torch.quantization.quantize_dynamic` as a one-line speedup — it nearly doubles MAE. The remaining viable paths on #24 are ONNX Runtime calibrated INT8, GGUF / llama.cpp, or smaller base-model retrain (Qwen2-0.5B uplifting reached MAE 0.760, see `docs/OPEN_QUESTIONS.md`).

- **Orthogonal-lens prompt design** (thriving v1, 2026-03 → PARKED 2026-04). Prompt added explicit "NOT Belonging" exclusion clauses + removed `social_cohesion_impact` to force semantic orthogonality between lenses. Result over 2 training attempts: val MAE 1.09 → 0.97, calibrated test MAE **0.94** vs uplifting v7 at 0.787 on the same Thriving tab. Bimodal score distribution (sparse 2–5 dead zone, 59% mixed-signal articles) is unlearnable for a 1B-param student; ~€41–46 oracle spend before PARKED indefinitely. See `memory/thriving-v1-scoring.md` and ADR-015. **Don't retry** "this is NOT [other lens], score 0–2" exclusion clauses in oracle prompts, and don't strip glue dimensions (e.g. `social_cohesion_impact`) trying to enforce orthogonality — lenses are overlapping perspectives, and ADR-014 percentile normalization handles cross-tab ranking already. **Cross-ref:** structurally the same lesson as [ovr.news hypothesis-log](https://github.com/ducroq/ovr.news/blob/master/docs/hypothesis-log.md) Dead Ends entry "Stack rules in the brand-voice prompt" (#229, 2026-06-01/02) — adding rules surfaces new failure modes, not fewer.

- **`score_scale_factor` linear stretch as cross-filter normalization** (Mar 2026, superseded by ADR-014). Filters' production distributions differ structurally (uplifting passes 62.8% as MEDIUM+; nature_recovery 0.3%); linear stretching can't fix a non-linear distribution mismatch. HOME tab `max(weighted_average)` made uplifting dominate, articles opened in wrong tabs. Rejected alternatives tested: z-score normalization (assumes normal — NR p95 stuck at 6.84), P99 max-scaling (NR p90 normalized to 1.94), val-set CDF (54% of NR articles tied at one value because val set has 70% at score 1.0). See `memory/gotcha-log.md` "score_scale_factor Is Linear" and ADR-014. **Don't retry** any global linear or moment-based normalization (`score_scale_factor`, z-score, P99 max-scaling, val-set CDF) as cross-filter harmonization. `score_scale_factor` remains only as the fallback path for filters that don't yet have `normalization.json`.

- **Universal noise prefilter beyond commerce** (sustainability_technology active learning, 2026-01-31). Initial plan: a universal noise filter for software tutorials, farming, policy, etc. — sustainability_tech showed 40% oracle waste on out-of-scope articles. Analysis showed each category is *signal* for another filter: farming → nature_recovery, software tutorials → augmented-engineering, policy → policy_analysis. Source-exclusion experiments tested at 33–56% precision (would block legitimate content like "heat pump retrofit testing" scoring 4.8). Only commerce is universal noise, already covered by `commerce_prefilter` v2 at 97.8% F1. See `docs/adr/004-universal-noise-prefilter.md` (Proposed → de-facto closed) and the repurposed `datasets/training/universal_noise_prefilter/`. **Don't retry** building a second "universal noise filter" for software / farming / policy. Accept ~30–40% oracle waste during training — the "wasted" zeros are valuable negative training examples for the student. Use filter-specific keyword prefilters + per-filter student scope.

- **`.nexusmind-owns` manifest as cross-repo divergence-management strategy** (#50, 2026-04-28 → retired 2026-05-04). The manifest declared `filter_base_scorer.py` and `hybrid_scorer.py` as "NexusMind-owned, won't be overwritten." On 2026-04-16 NexusMind's normalization application code was silently deleted; both copies became byte-identical (399 lines, no normalization). The manifest *claimed* divergence; nothing checked. All 7 filters silently de-normalized for **18 days** — acute on nature_recovery v2 (median 0.0, p90 0.3, 0.06% ≥4.0). Fixed by extracting to a wrapper class (`NexusMind/src/scoring/production_scorer.py`); manifest is now empty-by-default and any entry requires a tracked issue + deadline. See `memory/gotcha-log.md` "Manifest as Anti-Pattern" and ADR-014 implementation amendment. **Don't retry** an "X is owned by the other repo" manifest as the *primary* divergence-management mechanism — default to extraction (composition over inheritance, wrapper classes). "By design" is a claim about the implementation; verify by reading the runtime, not the design doc. **Cross-ref:** same family as ovr.news hypothesis-log Dead Ends entry "NexusMind embedding-dedup as sole source of truth" (corroboration cluster, seeded 2026-06-05) — both are cases where a shared assumption between repos was load-bearing but never verified at runtime.

---

## Maintenance

- Add an entry when an experiment is concluded as "don't retry" (not "paused — may revisit"). Paused experiments belong in `memory/thriving-v1-scoring.md` (and similar) or in an ADR; they should only land here once the door is closed.
- Keep entries to one paragraph (3–5 sentences). If the entry grows a multi-step rationale, link out to an ADR or gotcha-log entry instead of inlining it.
- The `**Don't retry** <scope> — <reason>` closing is mandatory; that's the line a future agent reads at session start to avoid the re-experiment.
- Reviewed as part of end-of-session `/curate` flow: "did any approach fail today that future-you should not retry?"
