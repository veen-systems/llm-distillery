---
name: filter-doc-standard
description: The standard documentation set for a deployed filter — belonging v1's 7-file core, plus cd v5's 2 optional extensions for complex calibrations
metadata:
  type: reference
---

**Project standard for filter documentation** (locked in 2026-05-31, template = belonging v1).

**7-file core** every deployed filter should carry in `filters/{name}/v{N}/`:
1. `config.yaml` — dims, weights, thresholds (per-dim `description:` is a **Hub-upload requirement**, not just docs — see gotcha-log)
2. `prompt-compressed.md` — the oracle prompt
3. `prefilter.py` — declarative prefilter (ADR-018/019 shape)
4. `STATUS.md` — current deployment status
5. `DEEP_ROOTS.md` — the lens rationale / design intent
6. `README.md` — human-facing overview
7. `README_MODEL.md` — the Hub model card source

**2 optional extensions** for complex calibrations (added by cd v5):
- `calibration_report.md` — per-dim calibration narrative
- `dimension_analysis/` — per-dim diagnostic artifacts

Use belonging v1 as the copy-from template for a new filter. Related: [[cd-v5-reference-status]].

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; listed in that recap but never committed. Grounded in MEMORY.md 2026-05-31 recap. -->
