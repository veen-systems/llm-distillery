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

## Later in the same session (after the NEXT list below was first written)

**Context audit run (`547e9a9`).** Untracked `.claude/settings.local.json` (12.4 KB
of another machine's config, `C:/Users/scbry/...`, no credentials). Recovered two
auto-memory files whose "Promoted to" claims pointed at files that never existed.
Framework stamp 1.14.0 -> **1.15.0** with a reconciliation record. Moved the four
standing rules out of `MEMORY.md` into CLAUDE.md Hard Constraints (index is
navigational; 116 -> 56 lines). 36 unresolved doc references -> 0. **My first
reference check reported 31 broken + 67 collisions, essentially all false** — it
double-prefixed cross-repo paths and counted class nouns like `config.yaml` as
collisions. Fixed the check rather than reporting the noise.

**FS#120 answered and the harness built (`b5135c0`).** `scripts/gate/measure_enrichable_rate.py`,
dry-run on 08-03..08-06. Told FluxusSource their denominator confounded enrichment
success with native article length and supplied a conditional instrument (column C).
Answered their question back: **no GN proxy is typed `firehose_aggregator`** — and
in fact those three excluded types match *no source in the estate*, so they drop
nothing for six filters; `investment_risk`'s `social` is the only real one, which
narrows the "worth 0.129" claim in `nexusmind-data-sources.md`. Recorded on #88.

**The GN finding that reframes their gate.** GN proxy enrichment succeeds **0 times
in 14,198** (max content 277 chars). Verified it is "always failed" not "never
attempted": `SKIP_DOMAINS` is empty, `pre_enrich()` gets the same list about to be
scored, and replacement needs 300+ chars while the longest GN row is 277. Then read
all 49 GN articles that surfaced: **not junk** — Niger health insurance, South Sudan
rangers, Somalia formula-advertising ban, Burundi trachoma elimination — from **~40
distinct national outlets**. I had predicted UN/institutional publishers and was
**wrong**; it is local journalism. Also found **240 of FluxusSource's 312 GN sources
are `q=... site:<one-domain>`** — a named outlet fetched through Google for no
reason. That is a conversion, not a decision, and does not belong in the 08-14 gate.

**Two errors of mine, both corrected publicly on FS#120.** (1) I reported feed-
discovery hit rates of 17% then 8%; the second was *worse* because I raised
concurrency and got throttled. Neither is a measurement — told them not to use
either. (2) I proposed *building* a discovery job that **already exists** in
FluxusSource as `scripts/gn_to_native_upgrade.py` (plus `discover_country_feeds.py`
for the country half). My throwaway script is deleted, uncommitted. Lesson worth a
gotcha entry: I applied "check what a source excludes" to data all session and then
did not apply it to a sibling repo's `scripts/` before building.

## NEXT — agreed with the owner at the end of this session

**The bottleneck is three decisions, not work.** Three threads are parked behind them:

1. **#98 criterion 4** — strip cd v6's keyword gate, move to declarative
   `BasePreFilter`. Acceptance passed decisively (held-out oracle FN 0/75 vs the
   gate's 10/75). Owner call.
2. **#94** — static invariant (`GATEKEEPER_CAP < medium TIER_THRESHOLD`) vs
   case-by-case removal. Evidence added: cd's gatekeeper fires 34.8% of the time and
   can never change an outcome because cap == threshold. Owner call.
3. **#95 step 2** — measurement and docs are DONE (±0.30 band re-score flipped 7.1%
   of solutions / 9.1% of uplifting). What remains is the call: pin a batch size in
   production, or give op-points a noise margin. Seeding shipped, but that is
   *replay*, not stability. **#87 and #93 step 4 are both stuck behind this.**
   If only one decision gets made, make this one — it unblocks two others.

**Work to do without the owner, in this order:**

1. **#97** — ~30 min. Assess the six deployed filters against the #28 training-data
   position. Expected answer "nothing to do"; deliverable is that sentence appended
   to `docs/decisions/2026-08-05-tdm-opt-out-training-data.md`. Open since 08-05.
2. **#88** — execute the hygiene batch, including today's finding: delete the three
   dead `excluded_source_types` values and narrow the `nexusmind-data-sources.md`
   claim to investment_risk.
3. **#84** — solutions oracle Step-1/Flag-A router self-contradiction. Self-contained.

**Leave alone:** #99 (only its `classify_content_type` half survives whatever is
decided on criterion 4), #87 and #93 step 4 (blocked on #95), #90 (three data
points against it), and the v6 package gaps (defer until #87 settles the student,
so it is not done twice).

**FS#120 needs nothing until 08-14**, then one command — see
`filters/cultural_discovery/v6/STATUS.md` and the reproduce block in
`scripts/gate/measure_enrichable_rate.py`. The native-feed conversion work lives in
**FluxusSource**, not here, and uses their existing tooling.
