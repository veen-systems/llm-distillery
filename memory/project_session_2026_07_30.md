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
