# Session record — 2026-09-06

**$0 spend. No oracle calls.** One GPU pass on `b650-gpu` (660 rows, ~2 min).
**Deploy N/A, not skipped** — v8 is absent from sadalsuud's `NexusMind/filters/` (verified
this session, which is also what blocks Phase E) and carries `NO_HUB`.

Experiment: **EXP-026**. Continued the handoff in `docs/TODO.md` § *NEXT SESSION STARTS HERE*.

---

## The headline

**Phase 8 is CLOSED. The ADR-021 deploy gate ran and `human_thriving v8` has a number:
recall 0.343 / specificity 0.992** at the ruled op-point 4.50 calibrated, n=660, 35
positives (5.30% unweighted), precision 0.706.
`filters/human_thriving/v8/ground_truth_gate.json`, `docs/evidence/2026-09-06-v8-deploy-gate/`.

⛔ **Read the specificity first.** The owner's instruction this session, and it is now written
into ADR-023 as a rule about *reporting*, not only about tuning: **we prioritise HIGH
CERTAINTY over HIGH DETECTION.** A recall of 0.343 is that decision working — v8 surfaces
about a third of what the oracle calls on-lens and is right about 70% of what it surfaces.
It reads as a grade to anyone meeting it cold, and the reader most likely to misread it is a
future session of this project.

## What was done, in the order the handoff asked

1. **The CUDA re-score.** ⚠️ First finding, before any scoring: **b650's `~/llm-distillery`
   is not a git checkout**, and four files on the scoring path had drifted from the repo. A
   dump that feeds a deploy gate must be produced by the shipped program, so they were synced
   (pre-sync copies at `b650-gpu:~/llm-distillery/.presync_backup_20260906/`) and the
   differences checked file by file — docstrings plus one off-path argument, which is why the
   2026-09-04 CPU pass is still comparable as a device measurement. The other 60 modules under
   `filters/common/`, the v8 package and the two script dirs were already byte-identical.
   Dump written to `~/llm-distillery/ht_v8_test_dump_cuda/` — **not `/tmp`** — with sha256 in
   a committed manifest, and the device asserted **off the loaded object**
   (`parameters=cuda:0`) via a new `--require-device` flag, not off the flag passed.
2. **The gate**, with `--config` supplying the threshold so it matches what would deploy, and
   judged only against held-out oracle labels.
3. ⭐ **The device does not matter here — and it had to be measured to know that.** CPU vs
   CUDA on the same 660 rows: **0 verdict flips on both arms**, identical confusion matrices,
   the same 17 surfaced calibrated and 26 raw. Max |Δ| **0.1428** calibrated (411/660
   bit-identical) / **0.0508** raw (8/660). ⚠️ 0.1428 is **below** the #95 floor of 0.16, so
   zero flips is the expected outcome, not a surprising one — this bounds the device term for
   *this* population; v7's at the same 4.5 was 0.1956 with 3 flips.
4. **Phase E is BLOCKED, and the ordering is the reason.** `fit_normalization.py` fits from
   NexusMind production output and needs ≥200 rows above the op-point;
   sadalsuud's `data/filtered/` holds six filters and **no `human_thriving`**. Normalization
   comes after deployment, as it did for `solutions v6`. ⛔ The test split is not a substitute
   — it is a 25.1× design-weighted sample.
5. **NM#319 answered, in two regimes.** Before Phase E: `score_scale_factor: 1.0` passes raw
   through, so every surfaced article clears the 4.0 enrichment gate — nothing to do. After
   Phase E: anchoring puts the op-point at **normalized 0.0 by construction**, so the gate
   bites mid-population. Measured on `uplifting v7`, already in that state at the same
   op-point, 82 cycles 2026-08-23 → 2026-09-06, 251,461 rows: **18,041 surface (7.17%) and
   only 60.0% clear normalized ≥ 4.0** — 7,224 surfaced but un-enriched, the gate's effective
   bar being raw ≈ 5.05–5.13. Not a v8 regression; **fitting normalization is the step that
   turns it on**, and whether that is intended is an owner question.

## ⛔⛔ THE KEEPER — a recorded explanation, refuted by the measurement it caused

`STATUS.md` explained `EXP-015`'s raw recall **0.514** (18 TP) against this gate's **0.486**
(17) as *"a device difference — EXP-015 on b650-CUDA, this on CPU, i.e. the CPU→CUDA 0.1956
term landing near the bar."*

**It is not the device.** The device gives 0 flips (measured above). Nor is it the gatekeeper
or the clamp: computing the plain dot product and the gatekeepered, clamped WA over the same
dump moves **0 rows** across 4.5, on either device (`why_18_not_17.py`).

⭐ *A dismissal is a claim.* It survived two days because it named a **real, measured,
plausible** term — the one the reader was already primed for, on a filter whose entire
remaining risk was a device caveat. The dismissal was doing work no measurement had done.

⚠️ **And my first replacement for it overclaimed in the same way.** I wrote "it is the dtype",
naming three differences in the same sentence and concluding from one. The review caught it.
The two paths differ in **dtype** (production holds 342 bf16 params against 364 fp32, score
head in bf16; `eval_ht_v8.py` forces fp32), **adapter loading** (`load_lora_local` →
`get_peft_model` + a hand-rolled remap vs `PeftModel.from_pretrained`) and **batch size**
(16 vs 8) — and **none was isolated**. Registered as **`H-V8-23`** with a falsifier, and
recorded in `memory/score-batch-shape-noise.md` as a candidate term that is **not a number to
quote**. ⭐ What is established is the decision-relevant half: **production serves bf16 through
`load_lora_local` at batch 16 — this gate's own path — so 17 is production's number whatever
the mechanism turns out to be.**

## ⛔⛔ VERIFICATION IS NOT REVIEW — 6th session running

Before the review: **715 tests, doc-claims, claim-shapes, the registry checker and both
budget guards, all green.** A five-lens `/review-changes` then returned **3 blockers, all in
code this change added**, plus warnings:

1. ⭐ **THE FLAGSHIP HOLE — the tests written to prove the feature could not see the worst
   failure it has.** None of the four new writer tests varied the *scores* between the two
   gate runs, so mutating `report["provenance"] = prior["provenance"]` into
   `report.update(prior)` — which reverts every freshly computed metric to the previous
   file's — **passed all four**. A retrained model's gate report would have kept the old
   model's recall. Found by the adversarial lens mutating the real file.
2. **The provenance carry-over reintroduced, one layer up, the exact defect it was written to
   prevent.** A rerun on a different dump, device or checkpoint kept prose describing the old
   run — beside a freshly correct `inputs` block that made it look newly attributed. Now
   stamped with a fingerprint of the inputs it described, in three states: `matches` /
   `UNVERIFIED` (hand-written, never stamped) / `⛔ STALE`. ⚠️ **My first fix conflated the
   last two** and the "unchanged inputs do not cry stale" test failed — correctly: a warning
   that fires on every rerun is ignored within a day.
3. **A `--config` that cannot be read fell through to `nature_recovery v4`'s constants** —
   `load_scoring_spec` swallows every exception — and printed a full table at someone else's
   operating point (threshold 4.0, gatekeeper cap 3.5), exit 0. Now refused.

Warnings acted on: the dump script's own `Usage:` docstring still taught **both** hazards this
change exists to remove (no `--require-device`, `--out-dir /tmp`); "mutation-tested three
ways" read as more coverage than existed; and doc-accuracy found a **pre-existing stale
sentence eight lines from text this commit edited** ("it has no `base_scorer.py` yet … 4.5 is
currently a documentation value"), now corrected.

⭐ **A guard I wrote caught me the same day.** The registry checker refused
`tests_before = 715` as untraceable to any artifact — the same number the claim-verification
lens independently could not reproduce. Both counts dropped; **a suite total is a property of
the machine and the tmpdir, not of a change.**

✅ Reachability and guarantee-preservation returned clean, and established something worth
keeping: **`ground_truth_gate.json` has no reader in either repo** — NexusMind's
`_check_required_artifacts` reads only `calibration.json` and `normalization.json`, and
NexusMind's own `.gitignore` excludes it. It is evidence, not config.

## Documentation: HIGH CERTAINTY OVER HIGH DETECTION (owner, this session)

Stated plainly where a reader meets a recall figure, not only in metric vocabulary:

- **ADR-023** leads with it, and gains a section making it bind **reporting**: any document
  publishing a recall figure states the priority beside it.
- **`scripts/gate/ground_truth_gate.py` prints it above every table**, and writes it into the
  report JSON — so it travels with the number instead of depending on whoever writes the
  summary. Mutation-tested three ways, including *printed but below the table*.
- `CLAUDE.md`'s Hard Constraint, `docs/adr/README.md`, `docs/FILTER_PLAYBOOK.md`,
  `memory/filter-status.md` (which puts a recall column next to six filters and so invites
  exactly the forbidden ranking), `STATUS.md`, `docs/TODO.md` and the gate's `provenance`.
- ⚠️ **`CLAUDE.md`'s fleet table had a column headed `MAE` holding recall/spec values** — the
  one metric ADR-023 says never to rank on, labelling the two it says to use. Renamed.

## Files, and what to know next session

- New: `docs/evidence/2026-09-06-v8-deploy-gate/` (README, DUMP_MANIFEST, `device_delta.py`,
  `why_18_not_17.py`, both outputs), `filters/human_thriving/v8/ground_truth_gate.json`.
- `scripts/gate/ground_truth_gate.py`: `inputs` + `priority` + provenance fingerprinting +
  the config refusal. `scripts/analysis/dump_student_scores.py`: `--require-device`.
- ▶ **NEXT: phase 9, deployment.** The doc set (`DEEP_ROOTS.md`, `README.md`,
  `README_MODEL.md`) is what actually blocks shipping; the weights are on b650 only and v8
  carries `NO_HUB`, so decide the transport before the deploy. Phase E follows deployment.
