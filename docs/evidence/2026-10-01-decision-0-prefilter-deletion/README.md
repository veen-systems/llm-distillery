# Decision 0: what deleting the per-lens prefilters changes in the oracle path

**Date:** 2026-10-01. **Decision:** delete every per-lens rule prefilter (owner, 2026-09-28;
NexusMind#284). **Record:** `docs/adr/019-per-category-exclusion-overrides.md`, *Amendment 2026-10-01*.
This directory holds the only copy of the numbers. Other documents point here and don't restate them.

## Population

| | |
|---|---|
| File | sadalsuud `/home/jeroen/local_dev/NexusMind/data/raw/content_items_20261001_080513.jsonl` |
| sha256 | `3b1efcc7414bcb7deec3ead327cf56f68a5e64da96f62bbfbba1eabf292dc784` |
| Rows | 5,177, one collection cycle (2026-10-01, ~08:05 CEST) |
| Stage | **PRE-enrichment** (NexusMind `data/raw/`). ⚠️ The oracle never labels these rows, and NexusMind's preprocessing writes back into `data/raw/` (`memory/nexusmind-data-sources.md`). |

The file is not committed: it is production article text. `data/raw/` has a retention window, so it
will expire there.

## Method

`gate_verdicts.py` runs `ground_truth.batch_scorer`'s own `load_filter_package` +
`make_oracle_prefilter` over every row, once per package. That is the code path an oracle run takes.
It ran twice on the same file:

- **before** on a tree that still had the prefilters (commit `fe6c018`);
- **after** on the working tree with them deleted.

`summarize.py` diffs the two runs into `gate_verdicts_summary.json` (per-package counts, no article
text). The recipe below was run end to end on 2026-10-01 and reproduced that file exactly.

## Result

Per package: rows that now pass, rows that are newly blocked, and whether the floor verdicts changed.
Out of the 5,177 rows, 3,113 pass the 300-char floor plus validation, both before and after.

| Package | Newly pass | Newly blocked | Floor verdicts identical |
|---|---|---|---|
| cultural_discovery v5 | 1,957 | 0 | yes |
| investment_risk v6 | 1,759 | 0 | yes |
| uplifting v7 | 150 | 0 | yes |
| belonging v1 | 90 | 0 | yes |
| cultural_discovery v6, nature_recovery v4, solutions v6 | 0 | 0 | yes |
| human_thriving v9 (control: never had a prefilter) | 0 | 0 | yes |

Two kinds of finding here:

- **Structural** (holds on any population, since it follows from the code): exactly the rows a lens
  rule used to block now pass, nothing is newly blocked, and the floor plus empty-body rejection are
  unchanged.
- **Magnitudes** (belong to this one cycle):
  - They are measured on pre-enrichment text, which is the short-skewed side.
  - 1,726 of investment_risk's 1,759 are the source rule `blocked_source:arxiv`, so that number is
    about this cycle's source mix.
  - Read them as a direction, not as the size of the next oracle run.

⚠️ **The three zeros for cd v6, nature_recovery v4 and solutions v6 are not a measurement.** Those
prefilters were pass-throughs (`EXCLUSION_PATTERNS = {}`), so this check could never have found a
block for them.

## Re-run

All paths absolute; outputs go to `$OUT`, outside the throwaway worktree.

```bash
LD=~/repos/veen-systems/llm-distillery
EV=$LD/docs/evidence/2026-10-01-decision-0-prefilter-deletion
RAW=/abs/path/to/content_items_20261001_080513.jsonl   # sha256 above
OUT=$(mktemp -d)
git -C "$LD" worktree add /tmp/ld-before fe6c018
(cd /tmp/ld-before && PYTHONPATH=. "$LD/.venv/bin/python" "$EV/gate_verdicts.py" "$RAW" "$OUT/before.json")
git -C "$LD" worktree remove /tmp/ld-before
(cd "$LD" && PYTHONPATH=. .venv/bin/python "$EV/gate_verdicts.py" "$RAW" "$OUT/after.json")
"$LD/.venv/bin/python" "$EV/summarize.py" "$OUT/before.json" "$OUT/after.json" "$OUT/summary.json"
diff <(python3 -m json.tool "$EV/gate_verdicts_summary.json") <(python3 -m json.tool "$OUT/summary.json")
```
