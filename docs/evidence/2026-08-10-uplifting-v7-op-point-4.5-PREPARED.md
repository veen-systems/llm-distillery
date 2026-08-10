# `uplifting v7` operating point 4.0 → 4.5 — PREPARED, NOT DEPLOYED

**2026-08-10. Branch `uplifting-v7-op-point-4.5`. Nothing has reached production.**

## Why it is not deployed

A filter deploy restarts the scorer, and the change could not be verified until
**08:00 on 11 Aug** — the 04:00 cycle dies with the Odido uplink maintenance
(01:00–07:00). Shipping an unverifiable production change while the owner is away
is the wrong trade, so this is staged on a branch instead.

**It cannot reach production on its own.** Nothing scheduled invokes
`scripts/deploy_to_nexusmind.sh` — llm-distillery → NexusMind is manual. (Once a
change lands in *NexusMind's* repo it does ship automatically: `deploy_filters.sh`
runs as `ExecStartPre` on the 4-hourly `nexusmind.service`.) The branch exists so
that a routine `deploy_to_nexusmind.sh uplifting v7` for some unrelated reason
cannot pick this up unnoticed.

## What changed

| file | change |
|---|---|
| `base_scorer.py` | `TIER_THRESHOLDS` medium **4.0 → 4.5** — **the runtime source** |
| `config.yaml` | `scoring.tiers.medium.threshold` 4.0 → 4.5 + the decision record |
| `normalization.json` | **refitted at the new anchor**: n=15,698, `raw_min` 4.5 (was n=21,481 at 4.0) |
| `tests/unit/test_normalization_op_point.py` | expectation 4.0 → 4.5 |
| `ground_truth_gate.json` | re-run at 4.5; the 4.0 numbers preserved in the provenance block |

**The op-point is written down in four places** and they are now verified to
agree. That is not a design I chose — it is what the filter already had.

## The near-miss worth recording

`config.yaml` is **documentation**; `base_scorer.py`'s `TIER_THRESHOLDS` is what
runs. Changing the config alone would have been a **no-op in production** — this
repo's signature failure. It was caught not by review but by
`fit_normalization.py` refusing quietly to agree with itself:

```
WARNING: Operating point drift: base_scorer.py TIER_THRESHOLDS says 4.0,
config.yaml scoring.tiers says 4.5. TIER_THRESHOLDS is the runtime source and
wins here — but fix the mismatch, one of them is a lie.
```

It then fitted at **4.0** and had to be redone. A tool that argues with you is
worth more than a tool that obeys you.

## Verified before staging

- All four op-point sources agree at 4.5 (config, `TIER_THRESHOLDS`,
  `normalization.json` `raw_min`, the test expectation).
- **273 unit tests pass**, including `test_normalization_invariant.py`, which
  exists precisely to catch `raw_min` drifting off the tier threshold (NexusMind
  #161 and #205 were both that defect).
- **Runtime tier assignment executed**, not inferred: raw 4.39 → `low`, 4.49 →
  `low`, 4.50 → `medium`. Articles in [4.0, 4.5) stop surfacing, which is the
  intended effect.
- `raw_min` 4.5 sits **exactly on** `MAX_NORMALIZATION_RAW_MIN`. The production
  loader's guard is strict-greater-than, so 4.5 is accepted — with **zero
  margin**. 4.75 and 5.0 are unreachable without raising that constant in both
  repos.
- Deploy gate at 4.5: **recall 0.6111, specificity 0.9730, FPR 2.70%**
  (tp=132 fn=84 fp=12 tn=432), on-lens pinned at oracle ≥ 4.0.

## To deploy, when someone can watch a cycle

```bash
git checkout main && git merge uplifting-v7-op-point-4.5
bash scripts/deploy_to_nexusmind.sh uplifting v7 --dry-run   # DIFF THE OUTPUT FIRST
# .nexusmind-owns is empty, so the copy OVERWRITES; confirm nothing NexusMind
# added to filters/uplifting/v7/ is being deleted before running it for real.
bash scripts/deploy_to_nexusmind.sh uplifting v7
# then commit in NexusMind; deploy_filters.sh ships it on the next 4-hourly cycle
```

**Verify at the END of the run, not from the config:** the next cycle's
`filtered_*.jsonl` for uplifting must contain **no rows with
`raw_weighted_average` in [4.0, 4.5)**, and the surfaced count should fall by
roughly a quarter (measured estimate: ≈199 → ≈145 per cycle).

**Expect the 04:00 cycle on 11 Aug to fail regardless** — that is the Odido
uplink, not this change.

## What this does not fix

The highest-scoring junk. Five clearly-off-lens articles (oracle ≤ 2.0) survive
at 4.5, including one predicted **6.63** against an oracle of **1.80**. No
operating point in this range reaches them; that is llm-distillery#91's shape and
needs training-time work through the adverse probe suite.
