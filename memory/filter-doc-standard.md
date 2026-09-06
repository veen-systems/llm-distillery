---
name: filter-doc-standard
description: The standard documentation set for a deployed filter — a 6-file core (7 until 2026-08-21, when prefilter.py was dropped), plus cd v5's 2 optional extensions
metadata:
  type: reference
---

**Project standard for filter documentation** (locked in 2026-05-31, template = belonging v1).

**6-file core** every deployed filter should carry in `filters/{name}/v{N}/` (was 7 until 2026-08-21 — see item 3):
1. `config.yaml` — dims, weights, thresholds (per-dim `description:` is a **Hub-upload requirement**, not just docs — see gotcha-log)
2. `prompt-compressed.md` — the oracle prompt
3. ~~`prefilter.py` — declarative prefilter (ADR-018/019 shape)~~ ⛔ **REMOVED from the
   core 2026-08-21 (owner ruling).** A per-lens keyword prefilter is **optional, and for
   new filters the default is to omit it.** Reasons, all measured: it is **Latin-script
   only** wherever it exists (`uplifting v7`: **77** patterns, EN/NL/DE/FR — measured 2026-08-22 as a FOUR-LANGUAGE instrument covering 74.9% of production, Spanish filtered 0.89% vs English 8.89%; zero non-Latin
   script in 662 lines); it has **never run in NexusMind's production scoring path**
   (`use_prefilter=False`, `skip_prefilter=True` — NM#284, dead since 2026-02-10); and
   `nature_recovery v4` + `solutions v6` emit **zero lens blocks across 8,283 production
   articles**, so both complete packages already carry a file that does
   nothing. ADR-011's replacement is the **multilingual e5 probe**.
   ⚠️ This removes only the **per-lens** prefilter. The 300-char **oracle** floor
   (`ground_truth.batch_scorer.make_oracle_prefilter`, #93), `validate_article`'s
   empty-content check (**empty is not short**), and the shared commerce / obituary /
   violence gates are separate mechanisms and all stay. (ADR-004 covers **commerce only** —
   it says explicitly that other noise categories are *not* universal.)
4. `STATUS.md` — current deployment status
5. `DEEP_ROOTS.md` — the lens rationale / design intent
6. `README.md` — human-facing overview
7. `README_MODEL.md` — the Hub model card source. ⛔ **It was GITIGNORED repo-wide
   until 2026-09-06**, so five existed on disk, **none was tracked**, and a fresh clone
   had no model card for any filter while this standard required one and the parity
   checks counted it present. Un-ignored and all five committed. It is **generated, not
   written**: `scripts/deployment/upload_to_huggingface.py --filter <dir> --repo-name
   <id> --card-only` writes it without creating a repo, uploading anything, or needing
   `model/` on disk. ⚠️ **Pass `--selected-epoch` whenever the shipped checkpoint is not
   the last epoch trained** — the generator reads `training_history[-1]`, so
   `human_thriving v8` (epoch 4 of 6) would otherwise publish epoch 6's metrics beside
   epoch 4's weights, 14 numbers wrong with nothing saying so.

*(Numbering is kept at 1–7 with item 3 struck through, rather than renumbered, so that
existing references to "item 5 = DEEP_ROOTS.md" elsewhere do not silently shift. The
**core is 6 files**; item 3 is no longer one of them.)*

⛔ **Copying from `nature_recovery v4` or `cultural_discovery v5` re-introduces
`prefilter.py`** — both still ship one, because they predate this change. Delete it after
copying, and define `_load_prefilter` to set `self.prefilter = None` (it is an
`@abstractmethod` on `FilterBaseScorer`, so omitting it raises `TypeError` at scorer
startup and **no filter scores at all**). `scripts/analysis/filter_completeness.py` was
updated the same day; if it still lists `prefilter.py` in `core`, this change was reverted.

**2 optional extensions** for complex calibrations (added by cd v5):
- `calibration_report.md` — per-dim calibration narrative
- `dimension_analysis/` — per-dim diagnostic artifacts

⚠️ **`uplifting v7` cannot satisfy item 7 and that is recorded, not an oversight** —
it was rsync'd from gpu-server without `training_metadata.json` / `training_history.json`,
which are the card generator's inputs, so building one would mean reconstructing metrics
from a README narrative. Its `NO_HUB` file says so. `belonging v1` simply lacks the file.

✅ **`belonging v1` satisfies the standard again as of 2026-09-06** — it lacked
`README_MODEL.md` from 2026-08-21 (the template not meeting the core it defined), and the
card was generated with `--card-only` from its own committed `training_metadata.json` /
`training_history.json` / `config.yaml`. ⭐ **The gap was never that belonging was
special**: the file was gitignored repo-wide, so *no* filter had a tracked card and the
parity matrix was reading five on-disk files that a clone would not have. Complete
packages against the 6-file core are now **four**: `belonging v1`,
`cultural_discovery v5`, `nature_recovery v4` and `human_thriving v8` — enumerated by
testing for all six files, not by memory, because the first version of this sentence
said five and included `solutions v6`. ⛔ **`solutions v6` is NOT complete: no
`STATUS.md`, no `DEEP_ROOTS.md`** — which is exactly llm-distillery#126's committed
scope. `solutions v4` lacks the same two. ⚠️ `uplifting v7` lacks those two *and*
cannot have a card at all — see above. Full parity matrix: llm-distillery#126 — whose committed **scope is
`solutions v6` only**; the other filters appear there as context, not as work. Related: [[cd-v5-reference-status]].

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; listed in that recap but never committed. Grounded in MEMORY.md 2026-05-31 recap. -->
