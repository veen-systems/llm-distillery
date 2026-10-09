# Evidence Companion — Primary-Source Pointers

This folder collects the primary-source artifacts cited as load-bearing evidence in the **NLnet NGI Zero Commons Fund** application *"ovr.news: Open Methodology for Multilingual Editorial-Dimension Scoring"* (R&D-led restart, June 2026 round).

The application references three repositories — `llm-distillery` (this one, public under EUPL-1.2), `NexusMind` (private; methodology extraction scoped as R3 deliverable), and `ovr.news` (private; reader site live at https://ovr.news). To let reviewers verify cited claims without depending on private-repo access, the specific files cited as primary sources are reproduced here, frozen at submission time.

The work the funded grant produces remains the R3/R4 extraction-to-open-release work — this folder is *evidence of prior outputs*, not a substitute for the funded deliverables.

## Index — claim → evidence

| Claim ID | What it grounds | File |
|----------|-----------------|------|
| **R-4** | Cross-filter percentile normalization methodology (validated on 182K production articles; 5 alternatives empirically rejected) | [`adr/nexusmind-ADR-014-cross-filter-percentile-normalization.md`](adr/nexusmind-ADR-014-cross-filter-percentile-normalization.md) |
| R-4 (background) | Pre-ADR-014 linear scale-factor approach (now superseded) | [`adr/nexusmind-ADR-001-cross-filter-score-normalization.md`](adr/nexusmind-ADR-001-cross-filter-score-normalization.md) |
| R-4 (amendment) | Safety-valve fallback for thin-data filters (minimum-corpus boundary) | [`adr/nexusmind-ADR-018-normalization-safety-valve.md`](adr/nexusmind-ADR-018-normalization-safety-valve.md) |
| **R-5** | Multi-dimensional independence verification (max correlation 0.61 Social↔Gov on 1,702 sustainability articles; manual review 3/3 agreement) | [`reports/sustainability-technology-v2-ORACLE_CALIBRATION_REPORT.md`](reports/sustainability-technology-v2-ORACLE_CALIBRATION_REPORT.md) |
| **R-6** | Distilled classifier Val MAE 0.654 / Test MAE 0.717 across 6 LCSA dimensions; Qwen2.5-1.5B + LoRA, 1.18% trainable | [`reports/sustainability-technology-v2-TRAINING_REPORT.md`](reports/sustainability-technology-v2-TRAINING_REPORT.md) |
| **R-7** | Editorial-judgment architecture — composable rule-based selection (Chief Editor) | [`adr/ovr-news-ADR-029-chief-editor-layer.md`](adr/ovr-news-ADR-029-chief-editor-layer.md) |
| R-7 (companion) | LLM editorial review — multi-pass quality gate | [`adr/ovr-news-ADR-037-llm-editorial-review.md`](adr/ovr-news-ADR-037-llm-editorial-review.md) |
| R-7 (companion) | Lens taxonomy refactor — 5-lens consolidation | [`adr/ovr-news-ADR-038-lens-taxonomy-refactor.md`](adr/ovr-news-ADR-038-lens-taxonomy-refactor.md) |
| **R-8** + **R-12** + **R-13** | Continuous R&D operations (17 open + 8 resolved hypotheses); Discovery-lens degradation incident; cold-load vs eviction fault-family discrimination | [`hypothesis-log-excerpts.md`](hypothesis-log-excerpts.md) |
| **R-11** | "Needle-in-haystack: Why Filtering for Constructive News Breaks Standard ML" — publication-ready methodology article | [`articles/needle-in-haystack-draft.md`](articles/needle-in-haystack-draft.md) |

## What is NOT in this folder

- **Operational code** — NexusMind orchestration, ovr.news Astro site, FluxusSource RSS ingest. These are the systems that *produced* the cited artifacts but are out of scope for the evidence-companion role. Their R3/R4 open-release is part of the funded grant deliverables.
- **Business / strategic deliberation** — the full ovr.news hypothesis log includes funding-strategy, legal-entity, monetization, and project-worth-it entries. Only the two R&D-process entries cited as primary sources (R-12, R-13) are reproduced; see `hypothesis-log-excerpts.md` for scope.
- **HuggingFace model artifacts** — the two distilled classifiers (`jeergrvgreg/uplifting-filter-v5`, `jeergrvgreg/sustainability-technology-v2`) are already public on HuggingFace.

## Provenance + frozen-at-submit

Each file is a copy of the named source file in its private repo as of the application submission. They are not maintained here; the canonical versions remain in the private repos and will move with the R3 extraction work. If a reviewer needs the latest, contact the applicant per the NLnet application.

## License

This folder inherits the [llm-distillery](../../) repository's EUPL-1.2 license for code-shaped content. The methodology article (`articles/needle-in-haystack-draft.md`) is published under CC-BY-4.0.

## Cross-references

- Application: `freelance/grants/nlnet-commons-fund-2026-resubmit/application.md` <!-- placeholder --> (in the applicant's work-income repo, not public)
- Claim registry: companion `claims.md` in the same folder, with verification status per claim
- Methodology source for the V&V method: https://github.com/ducroq/agent-ready-papers (private at submission)
