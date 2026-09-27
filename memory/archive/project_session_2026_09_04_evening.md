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

## ⛔ Neither phase moved the AGGREGATE number they were aimed at

⚠️ **Read this section together with the EXP-017 review below, which was written the same
evening and supersedes its headline.** Everything measured here is correct; the conclusion
drawn from it — that Phase C achieved nothing — is not. Aggregate recall pools the rows v8
exists to demote with the rows it exists to keep, so it cannot show whether v8 worked. And
the fleet comparison this section makes is **void**: v7 and v8 do not share a positive class.

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
  0.0762, z = 2.65.** Unweighted 0.0693, z 2.53; both SEs binomial, Kish deff 1.068 → z 2.45.
  ⛔⛔ **CORRECTED later the same evening — "screened harder" is the wrong framing and it was
  mine.** A routing rate POOLS positives and negatives, and only one is harm. Split by the
  oracle: **every positive is routed in both scripts (Latin 58/58, non-Latin 8/8)**; the whole
  gap is negatives (0.9043 vs 0.8293). The screen is **more efficient** on non-Latin, not
  harsher. `script_routing_gap.py` now prints the split and no longer emits the old verdict.
- **FN was 0 in every language and script cell — and that is nearly uninformative.** On 8
  non-Latin positives the rule-of-three upper bound is **0.375**. A 30% non-Latin FN rate
  would have produced this table more often than not.

### The causal test I proposed for it — and it refuted my own hypothesis

I claimed truncation was the mechanism, said the test was cheap, ran it, and it died:

- **Within Latin, where n is large:** rows that FIT in 512 tokens route **0.8520**; rows that
  are TRUNCATED route **0.9611** — truncated rows route *more* often, by 11 points, the
  opposite of the prediction. Length is confounded with substance.
- **Matching Latin against non-Latin within token bands:** size-weighted gap **+0.1009**
  against an unconditional **+0.0986**. Matching on token count moves it by nothing.

The truncation asymmetry is real and stays measured; it is simply not what produces the gap.

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

## ⭐⭐ REVIEWED THE SAME EVENING (EXP-017, $0) — and the phase's headline was wrong

Asked "is this going anywhere?" and measured rather than summarised, off the forward pass
already on disk.

⛔ **The fleet comparison this session leaned on is VOID.** Every recall figure was set beside
the deployed fleet's 0.59–0.72. But v7 and v8 do not share a positive class: on the same 660
test rows v7 calls **117** positive, v8 calls **35**, they agree on **30** — **Jaccard 0.246**,
v8 keeps **25.6%** of v7's positives. Recall is conditional on the true class, which is exactly
why it survives a change of base RATE and not a change of DEFINITION. *"Recall below all six"*
compared two different quantities that share a name, and I had propagated it to **six
surfaces**. The figures are right; the comparison was not.

✅ **Against what v8 actually exists for, it works.** Partitioning the rows v7 surfaced by what
the v8 oracle says: **87 junk** (v7 surfaced, v8 demotes) and **30 good** (both agree). At 4.5
the student removes **79/87 = 90.8% raw**, **82/87 = 94.3% calibrated**, keeping **17/30 =
56.7%** and **12/30 = 40.0%** of the good.

⭐ **The control rules out the boring explanation.** A student that had only learned "score
everything lower" would move those two together. AUC on the 117 disputed rows: **0.8454 raw /
0.8521 calibrated against v7's own 0.7218** — and at bar 3.0 it keeps **90%** of the good while
still removing **62%** of the junk. They move apart. It learned a distinction v7 lacked.

⭐ **Calibration is the better arm after all** — junk removed 90.8% → 94.3%, AUC 0.8454 →
0.8521, and it demotes one of the two class-A rows the raw student still surfaces. ⚠️ This does
not overturn "not distinguishable"; it says the aggregate metric was the wrong place to look,
because it pools the rows v8 exists to demote with the rows it exists to keep.

⛔ **Still open, and it is the real gap:** the student under-learns class-A on the *highest*
v7 rows — **2 of 6** score ~5 against an oracle of ~1, at v7 6.28 and 6.57, i.e. the rows a
reader is most likely to see. n=6; direction, not a rate.

⭐ **The generalisable part: an aggregate metric that POOLS the rows a change exists to demote
with the rows it exists to keep cannot show whether the change worked, and will report a real
improvement as "not distinguishable".**

`docs/evidence/2026-09-04-v8-probe-calibration/PHASE_C_REVIEW.md`, `EXP-017`.

## ⛔⛔ EXP-018 — a bigger encoder, a registered prediction, and I was substantially wrong

Asked whether `multilingual-e5-large` closes the probe/student gap. Registered the prediction
as **H-V8-18 before running it**, including a falsifier. ⚠️ Written down that day as `H-V8-16`, a **collision** with the checkpoint-selection hypothesis from the previous session; renumbered to 18 on 2026-09-04, the earlier claim keeping 16.

| arm | whole-split AUC | AP | AUC on the 117 disputed rows |
|---|---|---|---|
| v7 (baseline) | — | — | 0.7218 |
| probe e5-small | 0.8710 | 0.3779 | 0.7517 |
| **probe e5-large** | **0.9016** | **0.4972** | **0.8169** |
| student raw | 0.9474 | 0.5474 | 0.8454 |
| student calibrated | 0.9488 | 0.5648 | 0.8521 |

**Scoring it honestly.** Whole-split 0.9016 landed inside my predicted 0.89–0.91 ✅. The
disputed-rows figure **exceeded my point prediction** of *"at most ~0.80"* ❌ while not
reaching my stated falsifier of 0.83. It landed **between the two**, so I am not claiming the
prediction held: the substantive claim — *capacity will not help, this is the wrong kind of
signal* — is **substantially wrong. Capacity closes 70% of the gap** (0.0652 of 0.0937).

⭐⭐ **And by the resolution I pre-registered (differences under ~0.05 are not resolvable at
this n), e5-large and the STUDENT are NOT DISTINGUISHABLE on the disputed rows** — 0.0285
apart.

✅ **The operational conclusion survives, for a different reason than the one I argued.**
Cost, measured on the same 5,926 articles and the same CPU: **47:13 against 4:14 — 11.1×.**
That disqualifies e5-large in both roles: as a Stage-1 screen it would cost ~14 ms against
the student's ~19 ms while still routing ~89% onward; as a replacement it is ~27% cheaper for
AUC 0.9016 against 0.9474. **Right answer, wrong reasoning.**

⚠️ **The 11.1× is CPU-only and the GPU ratio is UNMEASURED** — production serves on
gpu-server. The rejection rests on that one number, so it is also the one measurement that
would reopen it.

## ⭐⭐ EXP-019 — the owner's question, asked properly: is the student needed at all?

**Owner: *"people keep telling me I do not need this student on top of a vectorizer with just
an MLP head. But that is not proven not to be true."* They were right, and the framing was the
correction.** Every probe I had compared was trained as a **screen** (`--objective recall`),
which optimises the weighted average as a binary classifier and supervises the six dimensions
through an auxiliary L1 weighted **0.1**. Judging that on AUC and concluding the student is
necessary is close to a strawman.

| arm | AUC | AP | ΔAUC vs student (paired bootstrap) |
|---|---|---|---|
| probe recall, e5-small | 0.8710 | 0.3779 | +0.0778 [+0.0281, +0.1416] |
| probe recall, e5-large | 0.9016 | 0.4972 | +0.0480 [+0.0064, +0.0962] |
| **probe REGRESSION, e5-small** | **0.9035** | 0.4055 | **+0.0452 [+0.0113, +0.0883]** |
| probe REGRESSION, e5-large | 0.9021 | **0.5209** | +0.0468 [+0.0091, +0.0860] |
| student, calibrated | **0.9488** | **0.5648** | — |

⭐ **The objective mattered more than the encoder.** Regression lifts e5-**small** past
e5-large's recall-trained score at **1/7th the compute**; with regression, e5-large buys
**nothing** on AUC. It also removes the inflation: per-dim MAE **2.073 → 0.762**, bias
**+1.699 → −0.298** (student 0.614, ~0).

**Verdict by the rule fixed before the run** (*replacement requires the CI on ΔAUC to include
zero*): **all four fail — the student is not replaceable on this evidence.** ⚠️ But the honest
framing is a **trade**: the student finds **~6 more of 35 positives at every surfacing
volume** — 17% of the positive set — for **11.7×** the compute. Editorial, not statistical.

⛔ **A documented prediction did not hold.** `train_probe.py` and ADR-011 warn regression
*"will likely collapse to a floor predictor"* below 25% positives; at 4.7% it did not, and beat
the recall probe by 3.25 AUC points. ⚠️ **This does not refute ADR-011** — its claim is about
regression **as a screen**, where collapse means unrecoverable Stage-1 false negatives, and
this tested it **as a scorer** without selecting a threshold. That claim remains untested.

⛔ **And it corrects my own observation from an hour earlier.** I had noted the student on GPU
(43.7 ms) beating the probe on CPU (47.2 ms) and concluded the two-stage design saves nothing.
That was the wrong device. **On GPU: e5-small 3.74 ms, e5-large 26.79, student 43.70** — the
probe is 11.7× cheaper. ⚠️ The screen still barely earns its keep at the **adopted** threshold,
for a different reason: routing ~89% gives 42.6 ms against 43.7 all-student, a **2.5%** saving
(at the probe's own 2.825, routing 52%, it would be ~26.5 ms). The hold-near-pass-through
ruling is what makes the screen nearly free of benefit — knowingly, since no Stage-2 cost
constraint was claimed.

## ⭐⭐ EXP-020 — the owner re-opened their own ruling, and it survives with two corrections

**Owner: *"I wonder if my decision was right, don't we need harder gating? 89% pass-through
does not sound needle to me."*** Measured, threshold selected on **val** and evaluated on
**test**:

| probe | thr | test routing | test FN | wtd routing |
|---|---|---|---|---|
| **recall e5-small (shipped)** | 2.825 | 56.5% | **1/35** | **52.1%** |
| recall e5-large | 2.350 | 47.6% | 2/35 | 43.2% |
| regression e5-small | 0.600 | 55.3% | 1/35 | 50.8% |
| regression e5-large | 1.150 | 30.3% | **6/35** | 25.6% |

**Harder gating is available: 89% → 52% weighted, a 38% cut in scoring cost, for ~1 needle in
35.** No change recommended — the ruling's premise (no Stage-2 cost constraint claimed) is
intact, and buying FN risk for a saving nobody needs is a bad trade under ADR-023.

⭐ **Three findings that make this more than a restatement.**
1. **A better ranker does not buy a safer screen** — regression e5-small ranks far better
   (AUC 0.9035 vs 0.8710) and lands on the same screen (55.3%/1FN vs 56.5%/1FN).
2. **89% is not slack.** Needle-ness is the 4.80% *base rate*; screen tightness is set by the
   *ranker's quality*. Demanding near-zero FN at AUC 0.87 forces a permissive threshold.
3. ⛔ **Tightening has a non-compute cost nobody had written down.** A screened-out row's
   **published scores and tier are the probe's**. Going 89% → 52% takes the corpus share
   scored by the weaker instrument from **11% to 48%** — and the shipped probe is inflated
   **+1.98** with per-dim MAE **3.4×** the student's. Any tightening must be paired with a
   regression probe, which removes the inflation.

⭐ **Break-even routing is 52.7%.** Below it the two-stage design wins on cost; above it
e5-large-alone does. The adopted 89% sits well above — **which is the only reason
e5-large-alone looked competitive in EXP-018/019 at all.**

⛔⛔ **AND IT CORRECTS EXP-019, WHICH I OVERSTATED.** I reported ADR-011's floor-collapse
prediction as *"did not hold"*. **It holds.** As a *scorer* regression does not collapse; as
a *screen*, regression e5-large drops **6 of 35 positives** at 30.3% routing — exactly as
ADR-011 describes. A probe can be the better scorer and the worse screen, and carrying a
verdict between the roles is the error I made.

## ▶ NEXT

**Phase 8 — and it is a VALUES call, not a pass/fail.** The question is *how much agreed-good
content is the last few points of junk removal worth?*, decided on the **calibrated** scale
where 4.5 means something different. The trade, held-out, raw arm — junk removed / good kept:
**3.00 → 62.1% / 90.0% · 4.00 → 82.8% / 73.3% · 4.50 → 90.8% / 56.7% · 5.00 → 96.6% / 23.3%**.
⭐ **Under ADR-023 the inherited 4.5 is defensible and possibly right**: 4.5 → 4.0 buys 5 good
articles and readmits 7 junk ones, the wrong direction when a false positive costs a reader.

⛔ **H-V8-15 is NOT the next move.** Its trigger fired on a comparison EXP-017 voided, and
under ADR-023 v8's low recall is the cheap error, deliberately chosen. Re-scoped in the ledger.
