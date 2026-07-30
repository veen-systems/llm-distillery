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
