---
name: project_session_2026_08_06_evening
description: 2026-08-06 evening — four owner decisions unblocked #87/#93-step-4/#98, cd v6 reached package parity, the ADR-012 rename backlog closed, and #97 found 812 rows of article text published in a public repo
metadata:
  type: project
---

# 2026-08-06 evening — decisions, not work

The session opened with the bottleneck stated as *three decisions only the owner
can make*. It was accurate. Almost everything below follows from taking them.

## What was decided, and what followed

**#95 step 2 — budget for the noise floor; don't try to remove it.**
The framing had to be corrected first: **"pin a batch size in production" was
never an available option.** `DEFAULT_BATCH_SIZE = 16`
(`filters/common/filter_base_scorer.py:50`) is already fixed and never varies;
the variable is batch *composition*, which the seeded shuffle already addressed.
#95's own "suggested next steps" offered pinning as live. It was not.

What shipped instead: an article predicted within **0.16** of the surfacing
threshold is *indeterminate*, every metric at that threshold carries a band, and
**two models whose bands overlap are NOT DISTINGUISHABLE**.
`scripts/gate/ground_truth_gate.py` prints it (`--noise-floor`, default 0.16;
`0` reproduces prior runs). Worked example, solutions v6 held-out, 19/1,032
indeterminate: **F1 0.739 [0.712, 0.771]**, recall 0.671 [0.659, 0.707].
**This is what unblocked #87 and #93 step 4** — neither needed the noise gone,
both needed a rule for what counts as a difference.
<!-- verify: grep -q "NOT DISTINGUISHABLE" scripts/gate/ground_truth_gate.py && echo PASS || echo FAIL -->

**#98 criterion 4 — strip the gate now.** 800 → ~90 lines. Then, on a follow-up
decision, full package parity (below).

**#94 — static invariant, not case-by-case removal.**
`tests/unit/test_gatekeeper_invariant.py`: a declared gatekeeper must have
`GATEKEEPER_CAP` below its medium tier threshold or it cannot change visibility,
the only outcome a filter has under ADR-016/ADR-022. Reads both values off the
**scorer class**, never config. Catches cd v5 (4.0 == 4.0) *and* solutions v6
(3.0 > 2.25) — the second was not how #94 framed it.

**Naming (unprompted, owner-initiated).** See "The rename backlog closed".

## cd v6: from unloadable to parity

Was: `base_scorer.py`, `config.yaml`, `prefilter.py`, `probe/`. Could not score.

Now: three inference modules, `calibration.json`, corrected
`score_scale_factor`, declarative prefilter, no gatekeeper.
`verify_filter_package.py` **7/7 offline**; 269 unit tests pass.

Three judgement calls worth not re-deriving:

- **Stage 2 loads from the Hub by default**, unlike nature_recovery v4. cd ships
  no local `model/` and never has, so a local default would wire the hybrid
  scorer to a directory that does not exist — the exact defect being cleaned up.
- **`calibration.json` keeps `filter_version: "5.0"`.** Correct, not sloppy: a
  calibration belongs to a *model*, and v6 does not retrain. Annotated with
  `reuse_note` so the next reader does not "fix" it.
- **`score_scale_factor` 1.2829 → 1.0 was the one live hazard.**
  `production_scorer.py` applies it as the linear fallback when
  `normalization.json` is absent — exactly v6's state — so it would have
  stretched every score by 28% silently. Only a live-scoring check catches that.

**Blocked on two things, neither doable from a laptop:** the Hub repo
`jeergrvgreg/cultural-discovery-filter-v6` **does not exist** (verified with
`--check-hub` — the one failing check), and `normalization.json` is unfitted.
v5's cannot be inherited even with an identical student, because the probe
screens ~50-65% of the firehose *before* the student, so the CDF is not v5's.

## The rename backlog closed (ADR-012 amended)

Owner reversed the pending renames on a reason ADR-012 never weighed: **its
three stated audiences are all internal**, and a HuggingFace repo is a public
standalone artefact where `discovery-filter-vN` / `recovery-filter-vN` drop the
qualifier that says what the model is about.

| Lens | Filter | Decision |
|---|---|---|
| Discovery | `cultural_discovery` | keeps its name — cancelled |
| Recovery | `nature_recovery` | keeps its name — cancelled |
| Solutions | `solutions` | confirmed as-is |
| Thriving | `uplifting` → **`human_thriving`** | at **v8**; not bare `thriving` |

The rule needed a **third clause**: ADR-012 reads as "rename to the lens name, or
don't", a binary with no room for `{qualifier}_{lens}` — which is what left
`uplifting` unresolved for five months. Now: (1) lens name stands alone → rename
to it; (2) filter name already carries the qualifier → keep it; (3) neither →
build `{qualifier}_{lens}`. `human_thriving` also dissolves a blocker unrelated
to descriptiveness: `filters/thriving/v1` exists as a separate parked filter
(ADR-015), so bare `thriving` would have landed on an occupied directory.

Cost today: **zero**. None of the renames had happened.

## #97 — the one finding nobody expected

Models came back clean: **zero of the 333 opted-out domains carry a
`User-agent: *` reservation**, so ADR grounds 1-3 cover the already-trained
filters. Hub artefacts carry no article text; splits are gitignored.

**But `git ls-files '*.jsonl'` found 812 committed rows holding full article
bodies — 2,364,068 characters — in a PUBLIC repo**, 160 from opted-out domains.
That is **republication, not mining**: ground 2 ("the artefact cannot reproduce
the input") is silent, because these files *are* the input.

Remedied same day on the owner's call — capped at 300 chars: **45 files, 834
rows, 1,889,627 characters removed**. Truncated rows carry `content_excerpt` and
`content_original_length`; ids, urls, titles, scores and labels byte-identical.
**Does NOT unpublish** — the text remains in public git history; history was not
rewritten.
<!-- verify: test -f docs/decisions/2026-08-05-tdm-opt-out-training-data.md && grep -q "1,889,627" docs/decisions/2026-08-05-tdm-opt-out-training-data.md && echo PASS || echo FAIL -->

**One file deliberately left alone:**
`filters/common/commerce_prefilter/training/splits/test.jsonl` (115 rows). It is
the live evaluation input for an enforcing gate, read at `max_length=512`
**tokens**, so a 300-char cap changes what the model sees and invalidates the
metrics in that gate's `TRAINING_REPORT.md`. Delta unmeasurable here — no
`transformers` on this box.

## Two of my own errors, caught by self-review

1. **"five scheduled renames, one carried out"** in the ADR-012 amendment. It is
   **four** — `belonging` "already matches" is not a rename, wisdom/education
   were never built. Corrected before the final commit; the wrong figure is in
   the `a6566ad`/`0ea8759` commit message, which is immutable.
2. **A commit landed on the wrong branch.** The parallel session moved HEAD from
   `main` to `docs/event-identity-encoder-plan` mid-session; my commit went on
   top of theirs. Caught because `git push origin main` said "Everything
   up-to-date" immediately after a commit — which cannot both be true. Fixed by
   cherry-picking onto main and moving their branch ref back with `git branch -f`
   (**not** `reset --hard`), so their working tree was never touched.

## The premise that did not survive checking

Carried in as "delete 3 dead `excluded_source_types` values". **They are not
dead.** All three have live emitters in FluxusSource —
`heuristic_scorer.py:117-122`, `credibility.yaml:154/159`,
`app.yaml:436/475/532`. The "dead" claim traced to a note that solutions' store
drops no rows, but `filtered_*.jsonl` **excludes source-type-excluded rows by
construction**, so it is the one place they cannot appear. Circular evidence;
deleting would have removed a live exclusion. Recorded on #88.

## Next session

1. **cd v6 cutover** (gpu-server): create `cultural-discovery-filter-v6` from the
   v5 adapter verbatim (old PEFT key format, no `resave_adapter.py`), fit
   `normalization.json` from a production-representative historical rescore, run
   the ground-truth gate on the real model, cut over **stamping-only** (ADR-022).
2. **#87** — now unblocked. Dimension weights, the `heritage_significance`
   near-constant, the 4.5-vs-4.0 provenance gap. Note v6 has no gatekeeper, so a
   re-derivation is against an ungatekeepered weighted average.
3. **#93 step 4** — also unblocked; the cap value is a threshold fit, so state it
   against the 0.16 band.
4. **#97 residue** — the 115-row commerce split, on gpu-server: truncate and
   re-baseline `TRAINING_REPORT.md`, or untrack it as the split it is.
5. **FS#120** — nothing until ~2026-08-14, then one command.

## Related

- [[cd-v6-probe-hypotheses]] · [[score-batch-shape-noise]] ·
  [[prefilter-length-floor-hypotheses]] (cd section superseded at v6) ·
  [[ovr-lens-set-current]] (naming table) · [[filter-status]]
