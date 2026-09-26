# Session 2026-07-30 — obituary v4 op-point evidence, v4@0.90 swap committed

## Trigger

Owner flagged an obituary on ovr.news the night before (`arabic_thearabweekly_d056412bf8cf`, "Farouq Hilal, the last guardian of Iraq's musical taste", flag API 2026-07-29 21:10). v3 shadow had caught it (0.977) — it reached the site only because shadow mode doesn't drop. **v4 scores it 0.937 — below the 0.95 op-point LD#83 planned to promote v4 at.** The issue's "FN just wastes 5ms" framing was wrong for a blocking prefilter; `memory/obituary-v4-hypotheses.md` item 3 marked FALSIFIED.

## Evidence gathered (LD#83, all reproduced by an independent reviewer)

- **Heldout sweep** (1,562 rows, v3+v4 rescored on gpu-server): v4's 5 FPs at 0.90 are the *identical set* as at 0.95 (all score ≥0.95) — zero marginal FP cost; recall 0.608 → 0.683. v4@0.90 vs v3@0.95: precision 0.979 vs 0.973, recall −6pt.
- **4-model blind panel** on the June-holdout marginal band [0.90, 0.95), n=37: **35/37 majority-obituary**, 1 FP (crime-report class), 1 split. phi4:14b lost Ollama mid-run (pipeline cycle started); every article kept ≥3 valid votes, majorities safe.
- Artifacts committed: `filters/common/obituary_detector/validation/artifacts/v4_oppoint_check_2026-07-30.json`, `grades_panel_v4_band_2026-07-30.jsonl`.

## Executed

- **NexusMind `02da4fe`** (pushed): obituary detector v3 → v4 in scorer service + preprocessor, v4 pickle SHA256s, `config/app.yaml` threshold 0.95 → **0.90**. **Still SHADOW** — stamps only; enforcement stays behind owner sign-off.
- **Not manually deployed** — and none needed: ExecStartPre `deploy_filters.sh` auto-fast-forwards (commit touches `deploy/gpu-server/main.py` ∈ `SCORER_PATHS`) and ships config + scorer atomically next cycle. RUNBOOK §durability note claiming otherwise was stale — corrected in NexusMind.
- llm-distillery `d4d0a5c` + wrap-up commit: evidence artifacts, memory updates, docstring/doc fixes (v4 inference.py both repos, NexusMind detector `__init__`/README).
- Review battery (correctness/opus, methodology/sonnet, deploy-risk/haiku): headline numbers reproduce exactly; findings all addressed or filed on LD#83.

## Next session (in order)

1. **Verify auto-deploy landed**: `curl gpu-server:8000/health` lists `obituary_detector_v4`; Farouq rescores 0.937 → flagged at 0.90. ⚠️ Never `git pull` on sadalsuud without letting `deploy_filters.sh` run — pull-only = unvalidated v3@0.90 stamps.
2. **Owner gate — FN-delta check** (LD#83): which articles does v4@0.90 miss that v3@0.95 caught (~20 on heldout)? Panel-grade them. Real obituaries in the gap → v5 or lower op-point.
3. LD#83 carry-overs: `_obituary_model` version stamp (shadow corpus is a v3/v4 mix for ~7 days — indistinguishable per-row); panel-check the 5 surviving heldout FPs (never independently validated); dead `has_model` guard.
4. Then: shadow flag-rate review → owner sign-off → enforce → ovr#204.
5. Still queued from before: LD#76 calibration audit (P0), #82 violence shadow audit, NM#206 timeout handling.

## Archived obituary history strata (moved from project-obituary-detector.md, 2026-07-31 audit)

### History 2026-07-30 (superseded strata — kept as evidence — kept as evidence; Status above is current)

**[SUPERSEDED by v5@0.85 enforcement] v5@0.92 SHADOW swap committed 2026-07-30 evening (owner: "do it all") —
NexusMind `89f3c58`, CI green, auto-deploys next pipeline cycle (~20:00; verify
same way as the v4 deploy: health lists `obituary_detector_v5`, log "Obituary
detector v5 loaded successfully", stamps `_obituary_model: "v5"`).** Vendored
v5 pkl+sha256 into NexusMind, updated EXPECTED_HASHES + all 9 swap literals
(deploy-risk review map). Threshold 0.92.

**[Enforcement-blocked framing SUPERSEDED by owner recall-first directive] June-increment panel MEASURED (2026-07-30, 40/65 v5-new flags, 4-model):
29 obit / 6 unanimous-not / 5 split → maj-prec 0.725, strict 0.829; at deployed
0.92: 0.714/0.806; at 0.95: 0.684 — THRESHOLD-INSENSITIVE (all 6 over-blocks
score ≥0.92).** v4's marginal band was 0.946. Enforcement stays blocked:
the fix is owner adjudication (`adjudication_worksheet_2026-07-30.md`, 14 rows,
awaiting owner verdicts) feeding a v6 with owner-authoritative labels on the
crime/accident-death + memorial/tribute boundary. Grades:
`grades_panel_v5_june_increment_2026-07-30.jsonl` (d332edc).

(b650 details moved to `memory/b650-gpu.md`.)

Owner decisions (2026-07-30): keep v4@0.90 as interim shadow (superseded same
evening by the v5@0.92 swap on "do it all"); v5 retrain on gpu-server approved
and executed same day.

v5 = v4 corpus + the 21 panel-graded FN-delta hard positives (11,329 rows, 2,694
pos; seed `training/data/v5_train_seed.jsonl` on gpu-server, same train_v1.py
recipe). Results (heldout n=1529 after excluding the 33 panel-graded rows —
28 FN-delta + 5 FP5, labels suspect/moved to training; eval:
`validation/artifacts/v5_eval_2026-07-30.json`, script `validation/eval_v5.py`):

**3-reviewer battery 2026-07-30 (correctness/methodology/deploy-risk, all
findings below verified by hand before recording):** the original excl-33 table
was misleading — it deleted v4's own 5 FPs (hence its fake "precision 1.000")
and 12 panel-graded rows NOT in v5's training set, which are exactly where v5's
over-block signal lives (v5 flags 6/7 panel-REJECTED FN-delta rows + both
panel-confirmed-real FP5 rows). **Corrected table** (exclude only the 21
training rows + 3 v4-hard-negatives that sat unexcluded in heldout since
07-28, n=1538): v3@0.95 prec 0.979 / rec 0.728; v4@0.90 0.979 / 0.728;
**v5@0.90 0.964 / 0.749 (+7 TP, +4 FP)**; **v5@0.92 0.967 / 0.734** —
statistically marginal either way (in-corpus heldout also has ~15% near-dup
contamination vs training; June is the only clean holdout and is unlabeled).

- **v5@0.92 dominates 0.90** [op-point superseded: owner chose 0.85 recall-first]: fits the same 19/21 gate
  articles, catches Farouq (0.9546), one fewer heldout FP, 12 fewer June flags.
- **Strongest v5 evidence** (reviewer-added): ovr.news 203 production
  borderlines — v5 flags only the known Bharathiraja TP at 0.90 (v3 flagged 4).
  No over-blocking on the production distribution; v4's legacy-tribute fix kept.
- Hard-negative regression: none (12 v4 hard negatives ≤0.4402); Farouq caught.
- **OPEN before ENFORCE sign-off** (shadow-deploy at 0.92 is low-risk anytime):
  (1) panel-grade ~40 of the 65 v5-new June flags — est. 17–20% are
  rule-violating over-blocks (health explainers, alive-person stories, TV
  schedule pieces); "June recall recovered" is partly precision lost, increment
  unmeasured; (2) owner adjudication of ~10 disputed labels — the 4-model panel
  drifts broader than the owner rule (memorial events / legal-process /
  legacy-tribute classes graded "obituary"; ≥2 of the 21 hard positives violate
  the KEEP clause, e.g. the Filip memorial festival) — circular since the same
  panel failed v4 and labeled v5's training rows; (3) v5's own new FPs (elephant
  obit 0.994, Einstein 0.989) are NOT oracle mislabels — earlier framing wrong.
- OOF sweeps are fold-seed-noisy ±5pt (v4b spans 0.61–0.71 rec@0.95 across
  seeds) — never compare OOF across versions; the 0.70→0.60 "drop" is mostly
  noise, real shift ≈2pt.
- Deploy prep for the eventual swap (from deploy-risk review): NexusMind
  `deploy/gpu-server/main.py` pins v4 pickle SHA256s (`EXPECTED_HASHES`,
  enforce-on, load in lifespan without try/except — stale hashes crash the
  WHOLE scorer). v5 hashes: mlp `6f271360d42a…`, scaler `16c79508a516…`. Swap
  blast radius: main.py + src/preprocessing/obituary.py + config/app.yaml
  (~9 literals). v5 pkls + .sha256 companions must be vendored into NexusMind's
  own repo first — deploy_filters.sh archives NexusMind HEAD, never reads
  llm-distillery. Until then gpu-server is the only v5 binary holder besides
  the workstation working tree.
- Reproducibility fixed post-review: `training/build_v5_seed.py` +
  `validation/artifacts/graded_ids_2026-07-30.json` committed.

**v4@0.90 shadow DEPLOYED + VERIFIED 2026-07-30 12:08 cycle** (auto-pull clean
fast-forward to c5f1df2; scorer logs "Obituary detector v4 loaded successfully";
health lists `obituary_detector_v4`; Farouq rescores **0.9372 → flagged** via the
deployed endpoint). `_obituary_model` version stamp + hoisted `has_model` guard
shipped in NexusMind `3f5c328` (next cycle).

**[RESOLVED same day — v5 trained, enforcement shipped @0.85] OWNER GATE FAILED (2026-07-30): enforcement sign-off BLOCKED, v5 retrain needed.**
FN-delta panel (4-model blind, n=28 gap articles v3@0.95 catches / v4@0.90 misses):
**21/28 majority-obituary** (12 unanimous), 5 split, 2 not. Five confirmed misses
score <0.70 on v4 — unrecoverable by threshold; the v4 hard-negative set
overcorrected on the crime/accident-death class (which the sharpened-broad rule
BLOCKS when death is the main subject). FP5 counter-check: only 2/5 of v4's
heldout FPs are real (3 are oracle mislabels incl. "Bardot funeral hoax") — v4
true precision > measured 0.979. Evidence: `validation/artifacts/
rollup_fn_delta_fp5_2026-07-30.json` + grades files (aaef1d0); LD#83 comment.

**v5 retrain direction:** add the 21 panel-confirmed FN-delta articles as hard
POSITIVES (ready-made, panel-graded) to balance v4's 12 hard negatives.
**Open owner decision:** interim shadow = keep v4@0.90 (Farouq class + ovr-FP fix,
stamps attributable via `_obituary_model`) vs revert to v3@0.95 (better recall,
21 real obits, near-equal precision). Asked in LD#83 comment 2026-07-30.

## Related Memories

- [[project-obituary-detector]] — full status, op-point evidence, deploy expectations
- [[obituary-v4-hypotheses]] — item 3 falsified
- [[cross-repo-prioritization]] — Chain 1 updated
- [[gotcha-log]] — 3 new entries (blocking-prefilter recall framing, Ollama panel contention, RUNBOOK vs SCORER_PATHS)

---

# Session 2 (2026-07-30, ~09:00-12:30) — deploy verified, gate FAILED, DeepSeek-commit review

## Obituary v4 (LD#83)

1. **Deploy verified**: push (08:28) postdated the 08:08 cycle start — NOT a failure;
   12:08 cycle auto-pulled (clean ff to c5f1df2), loaded v4, Farouq → 0.9372 flagged
   via deployed endpoint. deploy_filters.sh auto-pull worked exactly as designed.
2. **FN-delta owner gate FAILED**: 21/28 gap articles are real obituaries (panel);
   five <0.70 on v4 → v5 retrain needed, enforcement sign-off blocked. FP5: 3/5 of
   v4's "FPs" are oracle mislabels. Evidence aaef1d0; decision rule + owner question
   in LD#83 comment. See [[project-obituary-detector]].
3. Carry-overs shipped (NexusMind 3f5c328): `_obituary_model` stamp, has_model guard
   hoisted to production path.

## DeepSeek-commit review (owner request): 4 parallel reviewers over Jul 26-30 commits

Fixes: llm-distillery 403429d + aaef1d0 (pushed), NexusMind 3f5c328 + 6728a77
(pushed after deploy verification, ships next cycle). Headliners:
- **LD#80 rollback was a production no-op** (`if False:` gated the wrong branch;
  66 /commerce/predict calls post-"rollback") — commerce now forced local v1.
  Verify next cycle: journal "LD#80: ignoring gpu-server", zero /commerce/predict.
- **Code-drift check false-fired every run** (hash missing smoke_test component,
  3rd occurrence of the same drift) — fixed, verified byte-exact vs deploy stamp.
- solutions v6: FILTER_VERSION/hub repo_id said v5; v6 weights now on Hub
  (jeergrvgreg/solutions-filter-v6); verifier 7/7.
- ground_truth_gate falsy-0.0 record drop; violence oracle label poisoning +
  empty-batch crash (NM#274 shadow module); story_dedup embedding_version loss
  ("query: query:" corruption) + empty-text cluster collapse; consent-guard
  substring negation; EXPECTED_FILTERS stale (would've blocked scorer startup
  ~2026-08-01); .gitignore probe negation inert.
- Issues filed: LD#84 (v6/v7 prompt router contradiction — don't edit committed
  prompts, prompt_hash provenance), NM#278 (dedup thresholds unretuned for new
  embedding space).

## Next session

1. Owner: LD#83 interim-shadow decision (v4@0.90 vs v3@0.95) + v5 retrain kickoff
   (21 panel-graded hard positives ready in rollup_fn_delta_fp5_2026-07-30.json).
2. Verify next cycle (~16:00): commerce local-v1 ("LD#80: ignoring gpu-server",
   no /commerce/predict), no CODE DRIFT warnings, `_obituary_model` stamps present.
3. Then still queued: LD#76 calibration audit (P0), #82 violence shadow audit,
   NM#206 timeout handling.

## Post-wrap addenda (same session)

- **CI break + fix**: 6728a77 broke `tests/test_gpu_client.py` (mock had 5 subprocess
  results, fixed code makes 6 calls). Fixed in 85aac22 (mock derived from
  _SCORER_PATHS, asserts rev-parse HEAD: calls), CI green. **Gotcha: the pre-push
  battery ran `tests/unit` only — CI runs `tests/` incl. root-level files. Always
  run the full non-integration suite (952 tests) before pushing NexusMind.**
- **QA health check (12:43) diagnosed**: nature_recovery 7/52 missing summaries =
  Google News RSS stubs (news.google.com/rss/articles/CBMi… redirect URLs, content
  79-99 chars < 100-char summarize floor; enrichment can't resolve the redirect).
  Chronic ingestion issue, not an incident → **ovr#275** (3 fix options). Bonus:
  5/7 are the same Nepal-tiger story surviving same-source dedup at 0.92 (feeds
  NM#278). The solutions avg-9.0 score_anomaly warning = stale QA baseline of 7
  (solutions has averaged ~9 for a week, pre- and post-normalization) — owner
  one-liner to bump the baseline, no scoring problem.

## Session 3 (same day, ~16:00–20:30) — obituary DONE through enforcement

1. 16:00-cycle verification all green (LD#80 local-v1 line, zero /commerce/predict
   since 16:00, no drift lines, `_obituary_model: "v4"` stamps live).
2. **v5 trained** (gpu-server; v4 corpus + 21 FN-delta hard positives) →
   **3-reviewer battery** (correctness: all numbers reproduce; methodology:
   excl-33 eval biased both ways → corrected excl-24 table; deploy-risk: swap
   map incl. EXPECTED_HASHES crash risk) → **June-increment panel**: 0.71–0.83
   precision, threshold-insensitive.
3. **Owner adjudicated 14 boundary rows**: grief-vs-news rule (flips both
   sharpened-broad clauses) → LD#85 (v6 relabel + retrain on b650).
4. **Owner recall-first directive** ("I just hate obits coming through") →
   **ENFORCEMENT SHIPPED: v5 @ 0.85**, NexusMind `b904edc` (after shadow swap
   `89f3c58`): `obituary_blocked` in dedup gate after commerce, config-gated
   (`pipeline.obituary_detector.enforce`), stamps always written. CI green.
   <!-- verify: ssh sadalsuud "journalctl -u nexusmind.service --since today --no-pager | grep -m1 'obituary,'" -->
5. **b650 commissioned** (3090 Ti 24GB, account `jeroen`, uv venv, corpora +
   v3/v4/v5 copied, 831 rows/s embed; ST-version cross-box skew gotcha logged).
6. Lens scoring proven NOT an obit backstop (102 flagged rows passed lens
   thresholds in one cycle, mostly belonging).

**Next session first**: verify first enforced cycle (log `N obituary` in Loaded
line, `obituary_blocked>0`, health `obituary_detector_v5`, stamps v5) → ovr#204
→ LD#85 (owner reviews new rule wording before relabel) → LD#76 (P0), #82, NM#206.
