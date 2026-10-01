# Session — 2026-09-17 (after `final`): #156 closed with a negative, #158 mechanized, #104 answered

**$0 of oracle spend.** No oracle calls, no judge calls. GPU compute only, all of it on b650
(RTX 5090). **Deploy N/A — inapplicable, not skipped**: no model, calibration, normalization,
threshold, `config.yaml`, prefilter or inference path changed. **Merge N/A** — worked on `main`.
Pushed through `3098a1c`.

## What the session was asked for

Owner opened with *"i think we have a big list of todos and one of the important ones is the harm
detector?"*, then *"do it. i want results"*, then *"we have a nice gpu available, you know."*

## 1. `#156` — the last free route is closed, with a number (`EXP-039`)

**Per-run harm votes buy nothing.** Adding the 178 rows with ≥1 `harm_is_subject` run vote and a
non-harm final verdict moved the held-out panel catch by **−0.4 of 9 paired per seed** and cost
**~30% more panel flags for the same catch** (1.4 vs 2.2 at matched flag counts). Pre-registered
bottom bucket ⇒ ⏸️ **the ~$3.2–3.6 pool spend is now the owner decision**, not a ranked option.

⛔ **`H-HD11` is NOT ANSWERED and that is the honest verdict**: arm C (the 178 rows alone) caught
0 of 9, but reached test recall **0.0417–0.0833** and flagged **0.00%** of the panel above 0.40 —
the pre-registration's own positive control failed, so the zero is about 136 positives being too
few, not about the rows. ⛔ **Do not re-run this arm** without a bigger positive class and a new bar.

⭐ **Keeper: 4 of 5 seeds reproduced `EXP-037` EXACTLY across the GPU swap**, and seed 1 changed only
because `pick_threshold` is a **selection** step — a median **4.3e-05** probability wobble became a
**0.795 → 0.905** threshold move and one verdict flip. **Test recall was identical on all five
seeds, so a metric that looks stable across a hardware change says nothing about the flagged SET.**

Also corrected: `docs/TODO.md` said `NM#474` was unmerged and undeployed. It merged `01a9809` on
2026-09-11 and is **on sadalsuud**, dormant (`enabled: false`, stage returns `{"skipped":
"disabled"}` at `scripts/main.py:825`).

## 2. `#158` — the seed rule is in code, and it has produced artifacts (`EXP-040`)

`filters/common/detector_seeds.py` owns the seed set; both trainers lost `SEED = 42` and write
`seed_set` + `<metric>_band`. The **artifact** seed stays 42 on purpose. Nine pre-#158 sites carry a
`single_seed` declaration; commerce v2's says **UNRECORDED** because its config declares an
`MLPClassifier` while the tree's trainer builds a transformers `Trainer`.

⛔ **TWO SITES**: obituary's `models/` is gitignored, so the TRACKED copy of those numbers is
`v{N}/calibration_report.json` — checking only `models/` would have left 4 of 9 sites unguarded.

Then both trainers were RUN (only the obituary edit had ever executed): `0 banded` → **2 banded,
0 declared** per detector. ⭐ **On the obituary corpus seed 42 is the MINIMUM of five at both
thresholds**; on the violence corpus it is the median and reproduces the shipped 0.5498 exactly.

## 3. `#104` — answered at all six live op-points (`EXP-041`)

**1 of 6 flips, and it is the filter serving readers.** `uplifting v7`: **2 rows of 660**, both
FP-side, specificity **0.9687 → 0.9642** on the device production serves on. ⭐ **The magnitude does
not predict the risk**: `uplifting v7` has the SMALLEST max |Δ| (0.1572) and is the only one that
flips; `human_thriving v8` moves **0.4218 — 2.6× the #95 floor — with zero flips.**

Decision (pre-registered middle branch): **stamp, don't re-measure**. Six live filters gained a
`device_parity` block, three silent gates gained `device: "UNRECORDED"` with a reason, and
`check_gate_device_stamp.py` (10 tests, seeded red) now fails if a gate declines to say. Its PASS
warns that the tree holds **three distinct devices** — `human_thriving v8`'s gate was measured on
**CUDA** while `uplifting v7`'s was CPU, so ADR-021 comparisons were already crossing hardware.

## ⛔ Four errors of mine, all caught in-session

1. **The phantom test baseline.** `python3 -m pytest` (system interpreter, no deps) gave 13 failed /
   6 errors and I reported them to the owner as environmental and pre-existing. `.venv/bin/python`
   gives **0 failed**. `.claude/review-profile.md` warns about exactly this **six lines above** the
   baseline. Recorded there as occurrence two. ⭐ *The diagnosis being right is what made it useless.*
2. **Top-level grep for a nested field.** "No gate records a device" was false — it lives at
   `provenance.device`.
3. **Six gates from my own list; the tree holds EIGHT.** `investment_risk v6` (cpu) and
   `solutions v4` (no provenance block at all) were missed. The checker found them the moment it ran.
4. **An unfalsifiable prediction.** `H-DEV2` said `solutions v6` flips *"≥ the median filter"*; the
   median was **0**, so it had no failing branch.

## Numbers

Suite **922 passed, 25 skipped** (`.venv/bin/python`). 28 new tests. Three registry entries
(`EXP-039/040/041`), five ledger rows (`H-HD10/11/12`, `H-DEV1/2`), two Mechanized rows.
Issue comments posted to `#156`, `#158`, `#104`.

## ▶ Next

`docs/TODO.md` ▶ START HERE, which now opens with the owner decision (item 0) and carries the
heldout detector band (item 5) and `#104` item 1 (item 6).
