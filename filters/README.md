# Filter Packages

This directory contains versioned filter packages for LLM Distillery.

**Current filter status → `CLAUDE.md` Production Filters table** (authoritative).
Per-filter MAE, training data, and Hub repo details → `memory/filter-status.md`.

## Active Filters

| Filter | Current | Status |
|--------|---------|--------|
| **uplifting** | v7 | Deployed (hybrid inference, NO_HUB — file-copy to NexusMind only) |
| **sustainability_technology** | v3 | Deployed (HF Hub, private) |
| **solutions** | v6 | Trained, gate passed 2026-07-27. Normalization pending. |
| **investment-risk** | v6 | Deployed (HF Hub, private) |
| **cultural-discovery** | v5 | Deployed (HF Hub + gpu-server, private). DeepSeek oracle. |
| **belonging** | v1 | Deployed (HF Hub, private) |
| **nature_recovery** | v4 | Deployed 2026-07-10 (HF Hub + NexusMind + gpu-server) |
| **foresight** | v1 | PARKED 2026-04-16 — merged into solutions v4 (#43) |
| **ai-engineering-practice** | v2 | Ready for oracle scoring (separate product, not ovr.news) |

## Filter Package Structure

```
filters/<filter-name>/v<version>/
├── prompt-compressed.md    # Oracle prompt
├── prefilter.py           # Fast rule-based filter
├── config.yaml            # Weights, thresholds, deployment specs
├── base_scorer.py         # Inference scorer
├── inference.py           # Local inference
├── inference_hub.py       # HF Hub inference
├── inference_hybrid.py    # Two-stage hybrid inference
├── calibration.json       # Isotonic regression calibration (ADR-008)
├── normalization.json     # Cross-filter percentile normalization (ADR-014)
├── model/                 # LoRA adapter weights
├── probe/                 # e5-small embedding probe (Stage 1)
└── tests/                 # Self-tests
```

## Development

- **Playbook**: `docs/FILTER_PLAYBOOK.md` — canonical reference for creating/retraining filters
- **Guide**: `docs/agents/filter-development-guide.md` — full lifecycle (9 phases)
- **Checklist**: `docs/agents/FILTER_CHECKLIST.md` — development checklist
- **ADR index**: `docs/adr/README.md` — 19 settled architectural decisions

## Oracle Output Discipline

- Oracle outputs **dimensional scores only** (0-10 per dimension + reasoning)
- Never tier/stage classifications — those are postprocessing
- Every dimension MUST have inline `❌ CRITICAL FILTERS` in the prompt

---

*Last updated: 2026-07-27*
