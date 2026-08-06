# Session 2026-08-06 (afternoon) — cd v6 probe, FS#120 instrument, and a review that caught my own work

Continues the morning session (`project_session_2026_08_06.md`). Main @ `ccdbf9f`
+ this session's curate commit, pushed.

## What shipped

**#98 — cultural_discovery v6 probe: trained, measured, committed, pushed.**
`filters/cultural_discovery/v6/`. All three acceptance criteria pass.

- Held-out **oracle** labels (test split, 75 MEDIUM+ positives): probe @ 2.50
  FN **0/75**; keyword gate **10/75**.
- Production, 64 cycles / 156,226 rows / 2,653 surfacing, both arms in one pass
  over identical rows: surfacing blocked **337 (12.7%) → 1 (0.04%)**, high-tier
  **0 → 0**, 20 of 27 languages at exactly 0.0%.
- Threshold **2.50**, not `train_probe.py`'s 3.025 — the trainer selects off the
  val recall curve, so its val FN (1.3%) is optimistic by construction; held-out
  gives 6.7% at the same threshold. Val and test independently both give 0.000
  at ≤ 2.50.
- Harness committed: `scripts/gate/extract_probe_ab_rows.py` (sadalsuud, freezes
  one pass, baseline exact over all rows), `scripts/gate/score_probe_ab.py`
  (gpu-server, drives the real `EmbeddingStage`),
  `scripts/gate/probe_batch_invariance.py`.

**#99 filed** — `DISCOVERY_PATTERNS` is an English-only escape hatch: 66/516
English surfacing articles pass the cultural gate on lens-neutral
science-journalism words, **0/265 non-English**, all 66 read, none cultural.
Also feeds `classify_content_type`, which a probe does **not** replace.

**FS#120 answered — the measurement is ours, delivered on 08-14.** `pre_enrich`
fires at **500**, not 300 (`config/app.yaml:171`). Told them their proposed
denominator confounds enrichment success with native article length and supplied
a third, conditional instrument. Blocked back on two things only fixable before
their window opened: `eval_query` is stamped on **28 of 547** eval rows (their
"drop Chad, keep Tchad" cut is unexecutable), and three of eight arms project to
n≈13–35.

**ducroq/NexusMind#300 filed** — the #93 `content_length` stamp is computed and
lost before persistence: **0 of 50,605** rows, though the deployed code is
md5-identical to the repo. Does **not** block FS#120.

**Four SSH verify assertions re-run** after slipping three curate passes — all
PASS. Obituary blocked 1208 → 2573, no gap; rescore reproduces 07-31 to four
decimals.

## The review battery found two blockers in my own same-day work

Six lenses over `HEAD~2..HEAD`. **2 blockers, 4 warnings, 2 notes — all fixed.**

1. **BLOCKER** — v6 shipped a `hybrid_inference` block and a probe pickle into a
   package with **no inference module**, plus no `calibration.json` /
   `normalization.json`, and `STATUS.md` claimed these were "inherited from v5".
   There is no inheritance mechanism; `_load_calibration` fails **silently**.
   This is the repo's signature defect, committed by me on the same day I
   documented four other instances of it.
2. **WARNING** — the justification for accepting the criterion-2 regression
   compared cd v6's **production** screening rate to nr v4's **val** rate. Second
   val-vs-production error of the day, written *while correcting the first*.
3. **WARNING (fixed, no effect)** — `run_labelled` dropped `url` before handing
   rows to the gate, so its domain blocklists could never fire. Re-measured with
   urls: identical (10/75, 49.242%), because no test-split url hits those lists.
4. Reproduce commands pinned the window with `--offset`, which counts back from a
   growing file list and selects a different window every day.
5. Wilson CI was the non-surfacing stratum's, labelled as the combined estimate's.
6. `expected_pass_rate` and a stale `score_scale_factor` carried over from v5.

**Not refuted, and worth keeping**: the probe is **batch-invariant** — max |Δ|
3×10⁻⁶ across shuffled order, chunk 256→97, encode batch 64→1, zero threshold
flips. Student scores move up to |0.162| (#95); probe scores do not.

## Two self-corrections that changed conclusions, not just wording

- **Criterion 2 is a regression**, not parity: probe screens 63.7% vs the gate's
  70.2% on production. The parity claim came from the test split and does not
  transfer (9% MEDIUM+ label set vs 1.7% production surfacing rate).
- **Four of the five held-out positives** recovered by the lower threshold read
  as **off-lens** (immunogenicity paper, surveillance cameras, ad-data
  deanonymisation, a sea-level dyke) — #87's lens dilution inside the labels. So
  "FN 6.7% → 0.0%" partly measures label noise. 2.50 stands on the structural
  argument (recall is Stage 1's job, precision is Stage 2's), not the FN count.

## Deploy status: nothing deployed, deliberately

v6 is not deployable — see the blocker above. No Hub upload, no NexusMind sync,
no gpu-server filter deploy. The only remote changes were to gpu-server's
`~/llm-distillery/` **scratch** dir (v6 staged, three `filters/common/` files
refreshed from pre-#93) — not the deploy path (`~/NexusMind/filters/`), so
production scoring is untouched.

## NEXT

1. **FS#120 harness** — the only dated commitment (~08-14). Build and validate
   against 08-03→08-06 so the 14th is one command. Their three answers
   (`eval_query`, pooling, time-of-day) do not change its shape.
2. **#98 criterion 4** — owner call: strip the gate, move to declarative
   `BasePreFilter`. Also v6's two package gaps before it can ever deploy.
3. **#99**, the ADR-012 rename, and #94/#97/#84 remain untouched.
