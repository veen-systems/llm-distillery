# 2026-09-22 (rulings) — three decisions executed, and review refuted four of my own claims

**$0.** No oracle calls, no GPU, no training. **Deploy: N/A — deliberately not done**, and
that is the ruling, not an omission (`uplifting v7` still scores). Commit `974bd94`.

## What was ruled, in session

The same three rulings had arrived that morning **via the NexusMind peer session and were
refused as relays**; the owner then gave them directly here. `ADR-022` → option (a);
`#154` → option 1 (test the gap, not the bound); `NM#319` → accept.

## Done

- **`ADR-022` amendment RULED (a)** — DRAFT line struck, `#156`'s body corrected in place with
  a dated block. ⚠️ `deciders:` needed nothing: it was already `[Jeroen Veen]`, which is the
  confusion the queue item itself warned about. Clause 4's prerequisite (`NM#521`) was found
  **already discharged** at `NM 007be0a` — unblocked, still unimplemented. `#161` closed.
- **`#154` FIXED** — `MAX_SAMPLE_GAP = 0.5`, its own constant, gap-relative, in the fitter and
  the invariant test together. Outcome-proven through the real CLI both directions. `#154` closed.
- **Phase E FITTED** — 2,976 rows, `raw_min == op_point == 4.5` asserted as exact equality.
- **Suite 922 → 932**, clean tree, alone on the machine.

## ⛔ Four of my own claims refuted by `/review-changes` (6 lenses)

1. *"unchanged at the 3.75/4.0 op-points"* — **false**. A flat 0.5 is stricter below 4.0,
   identical at 4.0, looser above. All three directions now have their own test.
2. **Deleting the advisory left the band the fix OPENS silent.** A fit drawn from enriched
   output starts at raw 4.794 — gap 0.294, under the limit, missing 13% of the span, which is
   #205's literal root cause. Span-relative advisory added; fires on exactly that fixture.
3. ⭐⭐ *"60.0% of surfaced rows clear the enrichment gate"* — **a TAUTOLOGY**, and the repo had
   retracted the same number at n=202 two weeks earlier. See below.
4. *"Jaccard 0.246 (`EXP-030`)"* — **EXP-030's is 0.127**; 0.246 is two ORACLES on 660 labelled
   rows. The evidence file's lines 128-139 exist to prevent that substitution. Also: my own
   rewrite had **dropped** the "attributed not re-derived" marking off the peer's corpus rates.

## ⭐⭐ THE KEEPER — three written warnings, zero fired

The in-sample tautology was recorded in **three** places on the task's own routing path:
`memory/gotcha-log.md:7209` (a dated entry with that exact title), `docs/RUNBOOK.md`'s Phase E
section, and `filters/human_thriving/v8/STATUS.md:149`. I read none of them and recomputed the
number on **15× the rows**, reporting it as a correction. A bigger sample felt like a better
measurement; the quantity was never a function of the model.

**Six** already-promoted patterns recurred in this one session (the table is in the auto-memory
`feedback-prose-promotion-does-not-fire`). ⇒ **`H-CTX-1`: writing a lesson down does not
prevent its recurrence — REFUTED as a remedy.** What caught all six was review, at ~900 K
subagent tokens.

## Measured: the read surface (`#163`, owner-raised)

Bare-"continue" path **605,198 B / 7,362 lines** before any work starts — `docs/TODO.md` alone
is **546,771 B / 6,977 lines**, `memory/gotcha-log.md` is **715,093 B**, `CLAUDE.md` routes to
**30** topic files. `curate`'s own corpus is **2,554,790 chars, 8.5× its skill's 300 K
do-not-read threshold** — the curation step can no longer read its own inputs.
⇒ **`H-CTX-2`: capping the always-loaded layer (`#133`) was the right fix to the wrong file**;
the growth moved to what `CLAUDE.md` points at, which has no budget by design.

## Also

- **`#162` filed**: `tests/unit/test_experiment_registry.py` plants its fixtures in the REAL
  tracked `experiments/registry.jsonl` and restores in a `finally` — a killed run leaves it
  corrupted. It happened mid-review; three reviewers each measured a different failing count.
- A control fired and was **not** repaired by deleting it:
  `test_fit_calibration_config_write.py` went red the moment the fit landed, exactly as its own
  message predicted. Re-pointed to SEARCH for a qualifying package; mutation-checked.
- ⚠️ **One guard disappeared on commit**: `deploy_to_nexusmind.sh:135` refuses a filter dir with
  untracked files, and `normalization.json` was untracked. Now only the operator stands between
  the fitted CDF and production.

▶ **NEXT: `docs/TODO.md` ▶ START HERE — item −1, the read surface, MECHANIZE first.**
