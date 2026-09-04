# Session 2026-09-04 (evening) — v8 can score, and the threshold that screens it belongs to one probe

**Spend $0.** No oracle calls. Nothing deployed, nothing reached NexusMind or the Hub.
Commit `b9f60a1` on `main`, **unpushed**. Registry: **EXP-016**. Phase 6b (Stage-1 probe)
and phase 7 (calibration) of `docs/RUNBOOK.md`, both complete.

Everything ran on `b650-gpu`, **CPU**, `venv-prodparity` (torch 2.11.0+cu130,
transformers 5.0.0, sklearn 1.8.0). ⚠️ Those are **gpu-server's** pins, not sadalsuud's,
which is what runs the pipeline — `memory/b650-gpu.md`'s 2026-08-29 correction.

## What v8 gained

It could not score an article this morning. It can now, on b650: `base_scorer.py`,
`inference.py`, `inference_hybrid.py`, `probe/embedding_probe_e5small.pkl` (+ `.sha256`)
and `calibration.json`. ⛔ The weights are still gitignored (#97) and live only on b650, so
a fresh clone loads the package and cannot run the student. "Scoreable" is a statement
about one host.

## ⛔ Neither phase moved the number they were aimed at — and that is the finding

`docs/TODO.md` had named recall as the target (raw test 0.514). After both phases:

| arm | recall @4.5 | specificity | band overlap |
|---|---|---|---|
| raw | 0.486 | 0.9856 | recall [0.400, 0.514] |
| calibrated | 0.343 | 0.9920 | recall [0.314, 0.400] |

The gate's own #95 bands **overlap on recall, specificity and F1 — NOT DISTINGUISHABLE.**
⚠️ On recall the overlap is a **single shared endpoint** (0.400, 14/35 both) and the gate's
test is inclusive, so a floor a hair under 0.16 would flip that headline.

**Why neither lever worked, established rather than guessed:**

- The **probe is recall-safe** — 0 FN at the adopted 1.75 on val (31 positives) and test
  (35). Stage 1 was never what limits recall.
- The **calibration is the same ranker as raw**: Spearman **0.9977**, 1.95% of sampled
  pairs discordant, AUC **0.9474 → 0.9488**, AP 0.5474 → 0.5648, and at matched flag count
  every difference is **≤2 articles with inconsistent sign** (k=17 +2, 20 0, 26 −1, 30 0,
  35 −1, 43 0, 50 −1, 60 +1).

⭐⭐ **So the recall drop at a fixed 4.5 is a THRESHOLD effect, not a model effect.**
Calibration compresses the top of the *weighted average*, so 4.5 calibrated flags **17**
test rows where 4.5 raw flags **26** — a 34.6% cut in surfaced volume. ⛔ **Phase D must
re-derive the op-point on the calibrated scale**; carrying v7's 4.5 across is not keeping
the operating point, it is tightening it. ⚠️ Not a per-dimension rule: 3 of 6 top ends
*expand* on test; the weighted average compresses because the 0.30-weighted
`human_wellbeing_impact` does.

## ⛔⛔ THE KEEPER — the Stage-1 threshold belongs to the PROBE, not to the recipe

1.75 was chosen against the owner's 2026-08-28 *hold-near-pass-through* ruling
(design-weighted routing **0.8876 val / 0.8935 test**), **not** the script's own
FN-budget pick of 2.825, which collapses routing to ~0.52 and surfaces the single
non-Latin FN.

Then the control. `--seed 7` — same data, same objective, same code, **better** val BCE
(0.9209 vs 0.9611), still 0 FN — gives a probe on which that same 1.75 routes
**0.7406 / 0.7567**. A **~14 pp collapse in Stage-2 routing from the seed alone**, every
recall number unchanged. The probe's score *scale* moves with the seed; its *ordering*
does not. And **Stage 1 is silent by design** — a screened-out article produces no score,
no log line, nothing — so a 14-point tightening has no symptom.

✅ Guarded: `config.yaml` records `probe_sha256` **beside** the threshold and
`inference_hybrid.py` refuses to construct on a mismatch. ⚠️ Deliberately a **different
pin** from `probe/*.pkl.sha256`, which travels with the probe (a retrain regenerates it)
and so can only catch corruption. Mutation-killed.

## ⭐ Hashing is the wrong reproducibility test

Two seed-42 runs on the same host produced pickles with **different sha256** — 134 of
541,144 bytes, all torch storage keys derived from **memory addresses**. The tensors are
identical (all six `np.array_equal`, `max|Δ| 0.000e+00`, scaler identical).
`sha256sum` would have reported *not reproducible* about a fully reproducible artifact.

## The multilingual question is half-answered, and the answered half is adverse

With the keyword prefilter dropped (ADR-018/019 *Amendment 2026-08-21*) the probe is the
only layer carrying multilingual selection. At 1.75, pooled over both splits:

- **Design-weighted routing: Latin 0.8979 (n=1,187) vs non-Latin 0.8218 (n=131), gap
  0.0762, z = 2.65.** Unweighted 0.0693, z 2.53. Both SEs binomial and so optimistic;
  measured Kish deff 1.068 → z 2.45. **Non-Latin content is screened harder.**
- **FN was 0 in every language and script cell — and that is nearly uninformative.** On 8
  non-Latin positives the rule-of-three upper bound is **0.375**. A 30% non-Latin FN rate
  would have produced this table more often than not.

⭐ **Routing asymmetry CONFIRMED; recall asymmetry NOT MEASURED and not measurable at this
n.** llm-distillery#141 is the blocker. Directly relevant to **H-V8-10**.

## Mechanisms added, each proven to change an outcome

- `train_probe.py --seed` (probes were **unseeded**; the artifact now records seed, device
  and the library stack, because a cross-version sklearn unpickle only *warns* and neither
  hash can see it). The shipped probe was **retrained under the version-recording code**
  and verified content-identical, so the mechanism has actually produced an artifact.
- v8's `inference_hybrid.py` **reads** `hybrid_inference.stage1.threshold` and raises when
  absent — the first filter in the repo where that key is not inert.
- `fit_calibration.py` **refuses** to write `score_scale_factor` when the filter has no
  `normalization.json`. It computed **1.3787** here — a 1.38× stretch on every *normalized*
  score, which is what feeds cross-filter ranking and NexusMind's
  `pipeline.enrichment.min_score: 4.0`. ⚠️ Second-order: the write also silences NexusMind's
  own missing-normalization warning, because `_check_required_artifacts` treats the mere
  presence of the key as "uses scale factor".
- `probe/*.pkl.sha256`, the **first in the repo** — which makes
  `_verify_pickle_integrity` able to fail for the first time since it was written.

## ⛔ /review-changes, 5 lenses — 3 blockers, 14 warnings, and 623 green tests found none of it

**Two blockers were mine and bad:**

1. *"Every other `inference_hybrid.py` hardcodes `DEFAULT_THRESHOLD = 1.00`"* — asserted on
   **six** surfaces including a **constant name**, and true of **2 of 13** (others 0.75,
   1.225, 1.25, 1.50, 2.25, 2.50). Worse, its own next clause said *"they agree today, so
   it is harmless"* and `nature_recovery v4` ships config **3.225** against runtime
   **0.75** — the divergence the paragraph cites as cautionary is **live**. One grep away.
   ⭐ *A constant's name is an assertion, read far more often than the note beside it.*
2. The **routing-gap significance test was UNWEIGHTED**, inside an evidence directory whose
   thesis two sections above is that a sample rate describes no population. Fixed by
   recording Σw per group; reweighting made the gap **larger**, so the finding was never at
   risk and the reporting was. ⭐ *Writing the caveat is not applying it.*

**And three mechanism defects of this repo's signature shape, all caught pre-commit:**

- `probe_recall_report.py` promised in its own help text and in the JSON's own
  `design_weight_note` to omit weighted columns without `--corpus`, and emitted them
  unconditionally — the field there, populated, a different instrument from its name.
- `dump_student_scores.py`'s presence control raised **after** writing and closing all
  three output files.
- The no-prefilter refusal in `base_scorer.py` was **unreachable on the hybrid path**
  (`_create_stage2_scorer` hardcodes `use_prefilter=False`) — a documented refusal that
  could not fire, which is the shape it was written to prevent.

**A near-miss with no symptom:** `.gitignore`'s scratch rule `*_test.*` was swallowing
`probe_recall_report_test.json`, the sole source for every test-split number published
here. `git add <dir>` omitted it with no message, exit 0, while its `_val` sibling staged
fine. → *establish what a source excludes*, **18th occurrence**.

## ⭐ The commit-msg hook blocked the commit, and it was right

"deploy-class word detected" → `[FAIL] hub: cannot check — no repo_id extracted`. v8 ships
neither `inference_hub.py` nor a `NO_HUB` sentinel, so the verifier cannot tell
*deliberately not on the Hub* from *check broken*. ⛔ **NO_HUB was NOT added** — the plan's
§3c calls a Hub repo for v8 *optional*, so writing it would assert an undecided deployment
choice. Owed before phase F.

## Not done, deliberately

- **`scripts/deploy_to_nexusmind.sh:110-115` is blind to untracked files** — the gate whose
  stated purpose is stopping unreviewed code reaching NexusMind, proven experimentally by a
  review lens. Eight of v8's ten package files were untracked at the time, so a brand-new
  package is exactly the case it misses. One added `git ls-files --others` closes it, but
  that gate has **no bypass flag** and it is a production deploy path — owner's call.
- **NO_HUB**, above.

## Test and guard state

**623 passed, 11 skipped, 1 failed** — the failure is the pre-existing
`cultural_discovery v5` relative-import (llm-distillery#139), proven unrelated: v8 is not
among the 8 filters `find_trained_filters()` enumerates (it requires local weights).
Registry PASS (16 entries, **159** metrics, 0 untraceable), doc-claims 5/5,
budgets pass, verify-annotations exit 0 (21 pass / 0 fail).

## On the owner's machine

Killed one stale wait-loop of mine on b650 (pid 1377375). Left deliberately:
`b650-gpu:~/llm-distillery/ht_v8_test_dump/` (the 660-row raw-logit pass, so the 16-minute
CPU run need not repeat), `datasets/ht_v8_corpus.jsonl`, `/tmp/probe_seed{42,7}.pkl`,
`/tmp/probe_v2.pkl`. ⚠️ **pid 16598 on b650 has been spinning for 35 days** — an old
`while pgrep -f "uv pip install"` loop that matched its own command line. Harmless; not
mine to kill.

## ▶ NEXT

**Phase 8, the gate** — and its first job is the **op-point re-derivation on the calibrated
scale**, not a pass/fail on the inherited 4.5. Then **H-V8-15**, whose revisit trigger
("only if phases 6b/7 leave recall short of the fleet") has now **fired**.
