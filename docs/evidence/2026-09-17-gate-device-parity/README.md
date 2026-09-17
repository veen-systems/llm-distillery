# The device costs one filter two false positives, and four filters move 2-2.6x the noise floor without changing a single verdict (`EXP-041`, 2026-09-17)

⛔ **Headline: 1 of 6 live filters flips at its op-point, and it is the one serving readers.**
`uplifting v7` moves **2 rows of 660 (0.30%)** between CPU and CUDA, **both on the false-positive
side**: `fp` **14 → 16**, specificity **0.9687 → 0.9642** (**−0.0045**). Under ADR-023 that is the
metric that decides, and the direction is the unsafe one — **the device production actually serves
on is the one with more junk**. The other five filters flip **0** rows at their op-points.

⭐ **And the magnitude is not where the risk is.** Max calibrated |Δ| per filter runs **0.1572 to
0.4218** — `human_thriving v8` at **0.4218 is 2.6× the #95 floor** — and those four filters produce
**zero** verdict changes. **Read the flip count, not the magnitude**, in both directions: a large
delta far from the bar is harmless, and a 0.0045 specificity move at the bar is not.

Spend: **$0**. b650-gpu (RTX 5090), `venv-prodparity`, both arms on one box with only
`CUDA_VISIBLE_DEVICES` differing. Pre-registration: `PREREGISTRATION.md`, committed at `9dd8d03`
**before** the first dump (and carrying a marked correction, `64f3e89`, made before any result was
read). 4,338 held-out rows, 12 dumps.

## At each filter's op-point

Op-points established by **executing** `TIER_THRESHOLDS`, cross-checked against
`normalization.json` `stats.raw_min` and the gate artifact's own `threshold`. **A = CUDA** (what
production serves on), **B = CPU** (what every published number was measured on).

| filter | op-point | rows | flips | bit-identical | max \|Δ\| | recall A→B | specificity A→B |
|---|---|---|---|---|---|---|---|
| **`uplifting v7`** | 4.5 | 660 | **2 (0.30%)** | 5/660 | 0.1572 | 0.6103 → 0.6103 | **0.9642 → 0.9687** |
| `human_thriving v8` | 4.5 | 660 | 0 | **0/660** | **0.4218** | 0.3143 | 0.9856 |
| `cultural_discovery v5` | 4.0 | 857 | 0 | 6/857 | 0.2701 | 0.5867 | 0.9795 |
| `belonging v1` | 4.0 | 738 | 0 | 7/738 | 0.3176 | 0.6000 | 0.9847 |
| `nature_recovery v4` | 3.75 | 391 | 0 | 2/391 | 0.3083 | 0.6290 | 0.9787 |
| `solutions v6` | 2.25 | 1032 | 0 | 1/1032 | 0.1941 | 0.6707 | 0.9711 |

Signed mean (B − A) is between **−0.0024 and +0.0002** everywhere: **noise, not a shift**. Rows
above the #95 0.16 floor: uplifting **0**, human_thriving 1, cultural_discovery 3, belonging 2,
nature_recovery 2, solutions 2.

⛔ **`uplifting v7` has the SMALLEST max |Δ| of the six and is the only one that flips.** Whatever
ranks filters by device sensitivity, it is not the size of the delta.

## ⚠️ These are not the gate artifacts' own numbers, and must not be quoted as them

`filters/uplifting/v7/ground_truth_gate.json` publishes recall **0.6111** / specificity **0.9730**
(tp=132 fn=84 fp=12 tn=432). This run's CPU arm gives **0.6103 / 0.9687** (fp=14) on the same split
and the same op-point. **The gap is the TRUTH definition, not the device**: the gate's on-lens cut
is the oracle's *gatekeepered* weighted average, while `diff_box_parity.py` uses the plain weighted
sum, so the two draw different positive sets. ⛔ **Only the A-vs-B difference inside this table is a
device measurement.** The absolute figures are this instrument's, not the gate's.

⭐ For scale: the −0.0045 specificity move sits well inside the band the gate already carries for
`#95` batch composition, **specificity_band [0.9572, 0.9820]** — about **55× narrower** than the
indeterminacy that artifact already declares.

## The prediction scorecard — two refuted, one unfalsifiable

| prediction | outcome |
|---|---|
| flips per filter **0–3** | ✅ held (0–2) |
| ⭐ **filters with ≥1 flip: 3–6 of 6** | ⛔ **REFUTED — 1 of 6.** "Nothing makes the others special" was wrong; `uplifting v7` is special and the delta size does not explain why |
| max \|Δ\| per filter **0.10–0.25** | ⛔ **REFUTED on 4 of 6** — 0.2701, 0.3083, 0.3176, **0.4218** |
| specificity change **≤0.01** everywhere | ✅ held (max 0.0045) |
| recall change **≤0.02** everywhere | ✅ held (0.0000 at every op-point) |
| `H-DEV2`: `solutions v6` flips **≥ the median filter** | ⚠️ **UNFALSIFIABLE as written.** The median was **0** and solutions scored **0**, so "≥ median" could not fail. The *idea* — a lower bar sits deeper in the score mass — got no test |

⛔ **`H-DEV2` is the methodological keeper.** A comparative prediction against a statistic that can
come out at the floor has no failing branch. **Predict an absolute, or name the value that would
refute it.**

## What this buys, and the decision rule it lands on

The pre-registered rule's middle branch: **≤0.01 specificity everywhere, but ≥1 flip** ⇒
**stamp `device` on every gate artifact and carry the term as a known band** (`#104` item 3,
option B). Re-measuring every gate on GPU is **not** warranted by this: one filter, two rows,
0.0045 on a metric whose declared `#95` band is 55× wider.

⚠️ **This does not clear a future gate comparison.** ADR-021 compares a candidate against held-out
ground truth, and before this run the tree held — over **all eight** gate artifacts, enumerated by
glob and not from a list — **4 recording `cpu`** (`uplifting v7`, `cultural_discovery v5`,
`belonging v1`, `investment_risk v6`), **1 recording CUDA** (`human_thriving v8`), and **3
recording nothing** (`nature_recovery v4`, `solutions v6`, and `solutions v4`, which had no
`provenance` block at all). A cross-filter comparison today is already mixing devices.

**Shipped with this run:** the three silent gates now carry `device: "UNRECORDED"` with a stated
reason, the **six live** filters carry a `device_parity` block with this run's numbers — ⚠️ **not
all eight**: `investment_risk v6` (retired downstream, NM ADR-025) and `solutions v4` (superseded)
were not re-measured, and say `device` without a parity block rather than borrowing another
filter's term — and
`scripts/verification/check_gate_device_stamp.py` fails if a gate ever again declines to say.
Its PASS output prints the census and warns when the tree holds more than one device — because a
tree where every gate answers can still be a tree that mixes them.

## What this CANNOT establish

- **That gpu-server behaves like b650.** CUDA-to-CUDA across the two boxes is still unmeasured and
  they are now different architectures. This is the device AXIS on one box.
- **Anything about production rows.** Held-out test splits, not live articles.
- **A bound under a different batch.** Both arms scored the same split in the same order, so `#95`
  batch composition is held fixed, not measured. The 0.16 floor appears here only as the reporting
  threshold.
- **Why `uplifting v7` is the one that flips.** Two rows near a bar is not a mechanism.

## Files

`PREREGISTRATION.md` (with its corrections) · `diff_output.txt` — the full 190-line output for all
six filters, including per-dimension max deltas and both arms' confusion matrices.

**The dumps are in `datasets/parity/`**, the tracked home this repo already uses for parity
evidence, named to its convention and listed in its README. ⭐ **`EXP-041`'s own `uplifting v7` pair
came back BYTE-IDENTICAL to `EXP-038`'s** (sha256 equal on both arms, two separate processes about
nine hours apart on the same box, venv, device and split), so only ten files were added and **the
device term here carries no run-to-run component**. ⚠️ One filter, two arms, two runs — a control
for this experiment, not a determinism claim about the student in general.

Registry: `EXP-041`. Ledger: `H-DEV1`, `H-DEV2`.
