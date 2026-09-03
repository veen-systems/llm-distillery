# Phase B2 has **12 rows** of headroom, not a corpus — the draw already took 80% of it

**2026-09-03. $0** — no oracle calls. Reads the b650 pool (`/home/jeroen/v8_corpus/pool_v2.jsonl`)
and the drawn corpus.

Plan §4b specifies Phase B2 as *"collect the student's production positives above the op-point
on the class-A shapes"* and add the confirmed false positives as hard negatives. **That is the
same population the 2026-08-29 corpus draw sampled**, and the draw consumed 79.7% of it.

---

## The number

| | |
|---|---|
| above-op stage2 pool rows (≥300 chars), 2026-08-15 → 08-29 window | 15,452 |
| **class-A positives** (`filters/uplifting/v7/prefilter.py` `crime_violence`, 37 patterns) | **59** |
| already drawn into the v8 corpus | **47** |
| **remaining for Phase B2** | **12** — listed in `undrawn_class_a.jsonl` |

Of the 47 already in the corpus, **32 carry oracle labels below the op-point**. A row in the
training set with a correct low label *is* a hard negative — so B2's step 3 is already done for
those, by construction, without anyone deciding to do it.

⚠️ **The 12 are all English** (`non_latin: 0`, as the manifest records for the supplement too).
The non-Latin class-A hole is 0% by construction and is filed separately as **#141**.

⚠️ **A window is part of a source.** 12 is bounded by the pool's window — 83 files,
`filtered_20260815_204839` → `filtered_20260829_170332`. A wider window yields more rows; this
is not a statement about how many class-A false positives exist.

## ⛔ The trap I fell into, recorded because the field is still there

The pool file carries a **`harm_title` field**, and it is **not the class-A instrument**. The
reduce pass that wrote the pool runs on a host that cannot import the filters package, so it
falls back to a hand lexicon; the draw **recomputes** the flag with the census instrument before
sampling. Reading the stored field gives:

| | rows above-op |
|---|---|
| pool's stored `harm_title` (fallback lexicon) | **660** |
| census instrument (`crime_violence`, what the ruling is about) | **59** |
| agree | 32 |
| stored-only | 628 |
| census-only | **27** |

⛔ **Neither is a superset** (agree 32, stored-only 628, census-only 27) — 27 census rows are
invisible to the stored flag. I first reported
682 (before the length floor) and would have concluded Phase B2 had ~600 rows of headroom, an
**11× overstatement in the direction that invents work**. The draw script's own docstring warns
about this in the function that exists to prevent it (`class_a_instrument()`), and the manifest
records which instrument ran.

⭐ *A field name is an assertion.* `harm_title` claims to be the harm-title flag; it is one of
two differently-defined harm-title flags, and the pipeline deliberately overwrites it in memory
without writing the corrected value back.

## What this means for the plan

**Phase B2 as written has almost no headroom left, because it was specified before the corpus
draw existed.** The draw absorbed its population. The remaining class-A work is **label quality
inside the corpus**, not corpus expansion:

1. **The 12 undrawn rows** — worth adding (~$0.02 at k=3), but they are 12, and several are
   near-duplicates of events the corpus already holds twice over (Vietnam's death-penalty
   proposal ×2, the Syria removal ×2, a Travelodge follow-up). Appending them changes the
   corpus hash and the manifest, so it is a decision, not a chore.
2. **The ~6 self-contradiction rows above the op-point** are the larger lever and point the
   *wrong way*: they train the student that a proposal, a plan and a set of preparations score
   above the op-point. See `docs/evidence/2026-09-03-classA-supplement-adjudication/` §4A.
3. **§1f's premise still stands and is still untested**: 2 of 3 class-A rows were the *student*
   disagreeing with all three oracles. Whether putting those rows in front of it with correct
   labels fixes that is a **Phase C measurement**, not something this analysis can settle.

## Reproduce

```bash
# on the workstation, with b650 reachable
ssh b650-gpu 'python3 -' < scratch/pull_above.py > above_op_pool.jsonl   # metadata only
PYTHONPATH=. python3 -c "from scripts.corpus.draw_v8_corpus import class_a_instrument; ..."
```
⛔ Apply `class_a_instrument()`; do **not** read the pool's `harm_title` field.
