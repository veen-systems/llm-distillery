# human_thriving adj3 vs v8 on a week of production — the audit bar, written BEFORE any adj3 production score

**Written 2026-09-25 ~13:05, while b650 was scoring chunk 0 with v8. No adj3 production score existed.**
Owner, 2026-09-25: approved the 7-day window and chose the judge (**Claude blind, owner re-judges a
random 20 blind**). The bar below is the **assistant's proposal**; the owner did not rule on it.

## Question
If adj3 replaced v8, would readers see **less junk** (ADR-023's criterion), and what would it cost in
good articles no longer published?

## Population — computed by the pipeline, not chosen by hand
- Every `stage2` row in the last 42 files of sadalsuud's `data/filtered/human_thriving/`,
  `filtered_20260918_145649.jsonl` → `filtered_20260925_093350.jsonl`: **123,994 unique ids**
  (143,629 rows; 19,635 `stage1_low` rows are screened out by the shared e5 probe and cannot
  pass either model; 1 duplicate id). Production v8 passed **1,535** of them at raw ≥ 4.5.
- ⛔ **EXCLUDED, both models: 610 ids in any v8/adj1/adj2/adj3 train/val/test split, and every id
  in `docs/evidence/2026-09-24-thriving-more-positives/sample.jsonl`** (611 in window). adj3 was
  trained on production passers from this same week; judging it on them would be judging it on
  its own training data. The sample was drawn uniformly within strata, so the remainder stays a
  random remainder. Found by checking before writing this, not after.

## Scoring
v8 (`074209ff572c`) and adj3 (`4f4feac2ed6e`, its own calibration) on b650's 5090, same chunks,
same order, batch 16, `--require-device cuda`, calibrated arm; the weighted average comes from the
gate's own `load_scores(spec=...)`. Surfaced := ≥ 4.5.

**Control (stop condition):** b650-v8's passer set vs production v8's (`prod_v8_raw ≥ 4.5`) on the
same ids. If more than 10% of the union disagrees **outside** the 0.16 noise band, the re-scoring is
not production-faithful and the audit STOPS and is reported, not repaired.

## Groups (by b650 scores)
- **A — adj3 adds:** adj3 ≥ 4.5, v8 < 4.5. Where new junk would reach readers.
- **R — adj3 removes:** v8 ≥ 4.5, adj3 < 4.5.
- **B — both publish.**

Judged panel (seed 20260925): **A** all rows if ≤ 150, else 150 uniform; **R** the same; **B** 60 uniform.
Shuffled into one list, **blind**: the judge sees title, text, url and source only. No scores, no
group, no model name.

## Judge
Claude, under `docs/evidence/2026-09-24-thriving-adjudication-pilot/rubric_scope_v8-4.md` plus the
three rulings in `docs/decisions/2026-09-24-thriving-scope-rulings.md`, the verdict set used on
2026-09-24 (`in_scope`, `out_of_scope`, `harm_is_subject`, `response_to_harm`,
`no_person_benefits`), plus **`cannot_judge`** for text too short to judge (Google News echoes,
< 300 chars). **Junk := any verdict except `in_scope`.** `cannot_judge` rows are counted and reported per
group, and left out of the rates.

**Owner check (gates whether the result is reported as a measurement):** 20 panel rows drawn
uniformly (seed 20260925), re-judged blind by the owner. Binary in/out agreement **≥ 18/20** →
proceed. Below that, the Claude-judged figures are NOT reported as a result until the
disagreements are resolved.

## The bar — ADR-023
Junk share of what each model publishes, using group sizes as weights (the panel is design-weighted
by group, so the rates are re-weighted by N, never pooled raw):

    junk(v8)   = (N_B·j_B + N_R·j_R) / (N_B + N_R)
    junk(adj3) = (N_B·j_B + N_A·j_A) / (N_B + N_A)

D = junk(v8) − junk(adj3), 95% CI by bootstrap within each judged group (10,000 draws, seed 20260925).

- **WIN** iff the CI's lower bound is > 0: adj3 publishes a distinguishably smaller share of junk.
- **LOSE** iff the CI's upper bound is < 0.
- **NOT DISTINGUISHABLE** otherwise.

**Reported beside it, not gating (ADR-023: a missed positive costs nothing visible):** estimated
in-scope articles published per cycle by each model, and in-scope articles lost (N_R·(1−j_R)) and
gained (N_A·(1−j_A)). ⏸️ **Flag for the owner** if adj3's estimated in-scope output is below 50% of
v8's. That is a volume question for the owner, not a fail.

## Limits, stated now
- The judge's rubric also produced adj3's training labels; the owner's 20 are the independent part.
- One week, one seed, a single production window. Every per-cycle figure is over the audit
  population (exclusions removed), not the whole feed.
- v8 is not what Thriving serves today (`uplifting v7` is, #151). This audit compares candidate vs
  candidate; the cutover question comes after.
