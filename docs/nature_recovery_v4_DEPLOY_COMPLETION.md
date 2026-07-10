# ✅ COMPLETED 2026-07-10

**Deploy finished** once sadalsuud recovered (it had been power-cycled; back up ~05:4x).
Canonical chain ran clean: NexusMind git `8d2b8d0` → sadalsuud `git pull` + `deploy_filters.sh`
→ gpu-server (model pre-placed to survive the `*/model/` rsync exclude) → **scorer healthy,
all 7 filters smoke-passed, `nature_recovery wa=7.31`**. Two pre-deploy bugs caught + fixed:
stale v2 `normalization.json` (removed) and obituary_detector `filters/common` contamination.
Only the full Fluxus→Nexus→ovr end-to-end confirmation remains (fires on the next harvest run).
The historical runbook below is retained for reference.

---

# nature_recovery v4 — Deploy Completion Runbook

*State as of 2026-07-09. v4 is STAGED and gate-passed but NOT yet activated in
production, deliberately. This runbook is the remaining atomic activation.*

## Why it's staged, not activated

The ground-truth gate PASSED (v4 beats v2 on every metric vs held-out DeepSeek:
recall 0.672 / precision 0.848 / F1 0.750 / Spearman 0.821, operating point 3.75).
But at deploy time three infra conditions made an autonomous production cutover
unsafe (would risk the "no pipeline errors" mandate):

1. **sadalsuud was unreachable** (`ssh sadalsuud` timed out) — it's the host that
   rsyncs NexusMind → gpu-server. The canonical chain can't complete without it.
2. **The gpu-server SSH link was flaky** (intermittent `exit 255`).
3. **NexusMind discovery uses the LATEST version** (`src/filters/filter_loader.py:46`)
   — the instant v4 lands in gpu-server's NexusMind dir it auto-activates on the
   next pipeline run. Combined with `deploy_filters.sh` excluding `model/` (#67 +
   the strict startup weight-check), a code-only rsync of v4 would crash the whole
   scorer. So pushing v4 to NexusMind git was intentionally deferred — it would
   queue exactly that broken activation.

## What IS done (safe, reversible, prod untouched)

- ✅ Hub upload verified: `jeergrvgreg/nature-recovery-filter-v4` (private) — OLD key
  format, all files present (adapter, tokenizer, config, card, metadata).
- ✅ llm-distillery git: full package committed (model weights gitignored; Hub +
  gpu-server carry them). Deploy artifacts, STATUS.md, ground-truth gate + tests.
- ✅ Deploy model = seed-42 scale-2.0/Recall@20 checkpoint (test recall 0.672),
  staged on gpu-server at `~/llm-distillery/filters/nature_recovery/v4/` (model +
  calibration + config 3.75). calibration md5 `588a67d…` matches the deploy model.
- ✅ v2 remains the live production version (v1/v2 on gpu-server; v4 NOT there).

## Remaining activation — run when sadalsuud is up AND someone can watch a run

Pre-req: `ssh sadalsuud true && ssh gpu-server true` both succeed.

1. **Push v4 to NexusMind git** (from this workstation — model weights are gitignored,
   so this is code+config+calibration). The Windows-pathed `deploy_to_nexusmind.sh`
   needs porting (`C:/local_dev` roots + `python`→`python3`); either fix it or do the
   equivalent manually:
   ```bash
   NM=/home/jeroen/repos/veen-systems/NexusMind
   cp -r filters/nature_recovery/v4 "$NM/filters/nature_recovery/"        # model/ is gitignored
   cp -r filters/common/* "$NM/filters/common/"                            # honor .nexusmind-owns (empty)
   git -C "$NM" add filters/nature_recovery/v4 filters/common
   git -C "$NM" commit -m "Deploy nature_recovery v4 (ground-truth gate passed; recall 0.672 prec 0.848 vs v2)"
   git -C "$NM" push origin main
   ```
2. **sadalsuud pulls + deploys to gpu-server:**
   ```bash
   ssh sadalsuud "cd ~/local_dev/NexusMind && git pull origin main && bash scripts/deploy_filters.sh"
   ```
3. **Manual model scp (#67 — deploy_filters.sh excludes model/):** the model already
   lives on gpu-server at `~/llm-distillery/.../v4/model/`, so a gpu-server-LOCAL copy
   is most reliable (no network for the 85MB):
   ```bash
   ssh gpu-server 'cp -r ~/llm-distillery/filters/nature_recovery/v4/model ~/NexusMind/filters/nature_recovery/v4/ 2>/dev/null || rsync -a ~/llm-distillery/filters/nature_recovery/v4/model/ ~/NexusMind/filters/nature_recovery/v4/model/'
   ssh gpu-server 'test -f ~/NexusMind/filters/nature_recovery/v4/model/adapter_model.safetensors && echo MODEL_PRESENT'
   ```
4. **Verify the scorer loads v4 healthy BEFORE trusting a pipeline run** (gpu-server has torch):
   ```bash
   ssh gpu-server 'cd ~/NexusMind && PYTHONPATH=. HF_HUB_OFFLINE=1 python3 -c "from deploy.gpu_server.main import ... "  # or the scorer health path
   # minimally: construct the v4 scorer + score the canonical article, expect wa>=4.0
   '
   ```
   Then run the deploy smoke test (`deploy/smoke_test_articles.jsonl` has the Yellowstone
   wolves article, `min_weighted_average: 4.0`).
5. **Restart + health:** confirm `/health` healthy, v4 in discovered list, "Model
   validation passed: all N filters have weights" (guards the investment-risk-class
   whole-scorer crash).
6. **Normalization check** (guards the 18-day silent ADR-014 regression): after a real
   run, confirm `filtered_nature_recovery_*.jsonl` carries non-null `raw_weighted_average`
   + `normalization_method`. nature_recovery v4 has NO `normalization.json` yet (fresh
   version) — fit it once ≥200 v4 production articles accumulate (`fit_normalization.py
   --filter-version 4.0`); until then `weighted_average` is the raw post-calibration score.
7. **Keep v2 until v4 verified live**, then close #60, mark #56 PARTIAL, update #70.

## Rollback

v4 not yet active, so rollback = do nothing (v2 stays). After activation, rollback =
remove `~/NexusMind/filters/nature_recovery/v4/` on gpu-server (discovery falls back to
v2 as latest) + revert the NexusMind commit.

<!-- verify staged (disk-based): ssh gpu-server 'test -f ~/llm-distillery/filters/nature_recovery/v4/model/adapter_model.safetensors && grep -q "3.75" ~/llm-distillery/filters/nature_recovery/v4/config.yaml && echo STAGED_OK' -->
