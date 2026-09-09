# Session 2026-09-08 (third), closing 2026-09-09 — #155: the field that was produced at label time and destroyed at split time

**Spend: $0.** No oracle calls, no GPU run. Commits `dc91cbd` + this one.
**Lane C's only blocker is cleared.** Lanes A and B untouched, on the owner's instruction.

## What the session was

Lane C of the three-lane plan (`docs/TODO.md`) — the cross-lens harm detector, #156 — was
blocked on exactly one thing: `training/prepare_data.py` discarding `scope_verdict` when it built
the train/val/test splits. That is #155, and it is what this session fixed.

## What shipped

`training/prepare_data.py` enumerated a six-key allowlist, so everything the oracle emitted beyond
the six dimension scores was dropped at split time — silently, with `COMPLETE` printed and exit 0.
Each record now carries every source field through, then overlays the derived ones, with the
analysis block whole under a stable, filter-agnostic key **`oracle_meta`**. Derived keys win over
same-named source keys; the analysis key itself is excluded from the passthrough so the block is
not written twice.

**Measured, regenerated to scratch — the committed splits were NOT touched:**

| split | n | `scope_verdict` | `harm_is_subject` |
|---|---|---|---|
| train | 5,268 | 5,268 / 5,268 | **1,011** |
| val | 658 | 658 / 658 | **105** |
| test | 660 | 660 / 660 | **137** |

That is #156's positive class, at **$0** of new oracle spend — which is the whole reason the
two-head proposal was not a re-labelling job.

## ⛔ The review found the fix incomplete, and its own guard weak

Three lenses (adversarial, reachability, doc-accuracy) on a MEDIUM-tier diff. **3 blockers,
4 warnings, 8 findings total, all fixed.** The two that matter:

1. **`scripts/merge_training_data.py` writes the same three files** from its own converter and had
   the identical defect, with **no tests at all**. Worse than a plain re-drop: it passes existing
   rows through whole, so a post-fix merge would have been **partially** covered, and anyone
   counting `scope_verdict` presence would have read the coverage gap as a real rate. Fixed; it
   now prints its `oracle_meta` coverage and warns when partial. First tests written for it.
2. ⭐⭐ **THE KEEPER — the review mutated the DATA, not the code, and my tests could not have.**
   Its mutation kept only non-list values in `oracle_meta`. **All 35 tests passed** while the real
   corpus lost `scope_verdicts_per_run` on **6,586/6,586** rows and `runs` on 6,130. Cause: my
   fixture called itself *"shaped like `labels_v84_merged.jsonl`"* and carried **12 scalar keys
   against the real 20**, omitting every list- and dict-valued key. So *"enumerated, not
   allowlisted"* was true **of the wrong population** — #155's own failure mode one level up, in
   the thing built to prevent it. A fixture is a hand-built population.

Also: nothing inspected the produced artifacts, which is how #155 survived a whole training cycle
— `training/validate_training_data.py` now reports `oracle_meta` coverage over **every** row and
warns on zero (a legitimate pre-fix directory, which must still validate) or partial. And the
doc-accuracy lens found correct new prose sitting beside stale prose I had written past, including
**two operator-visible `print` lines** still asserting the behaviour I had just removed.

**Ten mutations across the three guards, all killed**: allowlist restored, `oracle_meta` removed,
passthrough removed, update order reversed, analysis block duplicated, list-valued keys dropped,
dict-valued keys dropped, skip counter silenced, coverage check deleted, coverage sampled to 10
rows. Suite: **779 passed, 24 skipped**.

## ⚠️ `oracle_meta` is verbatim and heterogeneous — the trap for #156

Measured over all 6,586 rows. **Two shapes in one file:**

| | 6,130 rows | 456 rows |
|---|---|---|
| the six dimension values | `float` | `{"score": float}` |
| `runs` | a **list** of per-run detail | an **int** count |
| `weighted_mean_major` | present | **absent** |

`scope_verdict` is the **only** non-dimension key present on all 6,586. Same shape as the
`content_length` and `raw_weighted_average` traps `CLAUDE.md` names: `len()` raises on 456 rows,
reading `runs` as a count is silently wrong on 6,130. Condition on shape before reading a key.

## ⭐ A documented risk retired, and its control

`b11e42f` warned that re-running `prepare_data.py` re-draws the 5,268/658/660 splits every v8 gate
number is measured against. **It does not** — seed 42 on the same input reproduces them with
identical id order, identical labels, **0 rows moved**.

⛔ **I committed that before running its positive control.** The control, run afterwards:

| arm | train moved | val moved | test moved | sizes |
|---|---|---|---|---|
| **seed 42** (the claim) | **0** | **0** | **0** | 5,268 / 658 / 660 |
| seed 43 (control) | 1,044 | 584 | 599 | 5,268 / 658 / 660 |
| tier thresholds +0.5 (control) | 1,041 | 593 | 580 | 5,267 / 658 / **661** |

The instrument can say "moved", so the zero is real. The redraw risk belongs to a changed **seed**,
changed **`config.yaml` tiers** or a changed **input file** — not to re-running the script. Seed 43
replaces **599 of 660** test rows, which sizes what a redraw would have cost. ⭐ **The ordering was
the defect, not the result** — a confirming control supplies no pressure to run it, which is why it
has to come before the commit. 23rd occurrence in `memory/working-rules.md`.

⚠️ The **bytes** still change: `test.jsonl` `e361b517…` → `e524c632…`, same 660 rows in the same
order. That hash is pinned in `docs/evidence/2026-09-06-v8-deploy-gate/DUMP_MANIFEST.md`, now
annotated so a future session reads it as *the same test set with more fields*.

## State on the machine

- Committed on `main`: `dc91cbd` + the curate commit. **Pushed.**
- **`datasets/` was never written** — every regeneration went to the session scratchpad, and
  `datasets/training/human_thriving_v8/test.jsonl` still hashes `e361b517…`. The splits on disk
  still predate the fix; nothing regenerates them automatically.
- #155 **closed**. #156 and #150 commented with the numbers and the trap.
- ⛔ **NexusMind untouched.** The production freeze holds; no filter package changed, so there was
  nothing to deploy.

## Next session

**Lane C, #156** — see `docs/TODO.md` § NEXT SESSION STARTS HERE. Pre-register first, rebuild the
splits to a **new** directory, train the binary detector on `harm_is_subject`, **stamp only**.
Judge it on specificity, not recall (ADR-023).

⚠️ One loose thread, unrelated and pre-existing: five docs (`docs/ARCHITECTURE.md`,
`docs/README.md`, `docs/REPOSITORY_STRUCTURE.md` ×2, `docs/WAY-OF-WORKING.md`) still show
`prepare_data.py --data-source`, a flag that does not exist and dies on argparse. `CLAUDE.md` and
`docs/RUNBOOK.md` both already warn about it.
