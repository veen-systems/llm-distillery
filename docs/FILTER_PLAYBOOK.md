# Filter Playbook — Single Source of Truth

**Read this first before creating or retraining ANY filter.** It compiles every hard-won
lesson so you don't re-scavenge the repo or fall into the same pits. Each rule links to its
source (ADR / memory / gotcha) so it stays maintainable — fix the source, not just this page.

- **This page's job:** the rules + the canonical example, not the step-by-step. Everything else is subordinate to it — the map below says what each doc is for so you never scavenge.

### Documentation map (what to open, what's dead)
| Doc | Use it for | Status |
|-----|-----------|--------|
| **`docs/FILTER_PLAYBOOK.md`** (this) | START HERE — compiled lessons + canonical example | **live, SSoT** |
| `docs/agents/filter-development-guide.md` | Full lifecycle depth (per-phase checklists, validation) | live |
| `docs/guides/filter-creation-workflow.md` | Quick step-by-step commands | live (companion) |
| `docs/RUNBOOK.md` | Deploy / train / score operations | live |
| `memory/gpu-server.md` | gpu-server env (venv, PYTHONPATH, HF_HUB_OFFLINE, scp-not-rsync) | live |
| `docs/adr/README.md` | Settled decisions (21 ADRs) | live |
| `memory/gotcha-log.md` + `memory/feedback-*.md` | Problem→fix archive + behavioral rules (the source of the pits below) | live |
| `docs/_archive/guides/getting-started.md` | — | **DEPRECATED** (Qwen-era) |
| `docs/_archive/guides/ground-truth-generation.md` | batch-scorer mechanics only | **DEPRECATED** (rest is stale) |
| `docs/_archive/guides/gpu-training-guide.md` | — | **superseded** → RUNBOOK + `memory/gpu-server.md` |
| `docs/_archive/guides/remote-sync-guide.md` | — | **superseded** (FreeFileSync → scp/rsync; see `memory/gpu-server.md`) |

---

## The canonical reference: `nature_recovery v4`

Copy its *shape*, not its metrics. It is the most complete worked example of the needle-filter
lifecycle + the V&V/gate/oracle-selection methodology (deployed 2026-07-10).

- **Package:** `filters/nature_recovery/v4/` · **Report:** `docs/reports/nature_recovery_v4_report.pdf`
- **Evidence data:** `docs/articles/nature_recovery_v4_evidence/` · **Deploy write-up:** `docs/nature_recovery_v4_DEPLOY_COMPLETION.md`
- Other references, each for its domain: **`belonging v1`** = prompt precision / oracle consistency (ADR-010) · **`cd v5`** = multi-oracle bake-off (ADR-020 draft).

---

## The pits — rules by lifecycle stage

Format: **the pit → the rule** (source). Skim the bold before each stage.

### 0. Oracle selection (highest-leverage decision — get it right first)
- **Defaulted to one oracle out of habit → wrong labels.** Select per-filter with a small bake-off (score ~300 stratified, judge the ~30-disagreement set with strong models). `feedback-oracle-selection-criteria`, ADR-020 draft.
- **Switched oracle to cut NOISE → wrecked BIAS ($100–200 lesson).** Noise (self-consistency) ≠ bias (editorial alignment). Choose the oracle for *bias*; cut noise by averaging k runs of the correctly-biased oracle, **never** by switching to a cleaner-but-differently-biased one. A clean, consistent, *wrong* teacher looks like progress. `feedback-oracle-bias-vs-noise`.
- **On penalty/exclusion flags, prefer the oracle that UNDER-fires** (a false penalty demotes a good article; a missed one is softer). `feedback-conservative-oracle-better`.
- **Treated oracle scores as truth.** The oracle is a *consistent labeler*; its self-MAE sets the student's floor (ADR-017). Stubborn high MAE on a dim → suspect label noise, fix the *prompt*, don't add data. `feedback-oracle-not-ground-truth`, ADR-010.

### 1. Prompt design
- **"max_score" cap read as advisory → oracle emitted raw scores.** Caps must be ARITHMETIC ("no dimension may exceed X"), and verify on a calibration sample before labeling. Or express as a per-dim SUBTRACTION (soft penalty, ADR-015) — the oracle follows those. gotcha 2026-05-29 / 2026-07-08.
- **Abstract carve-out language parsed too narrowly.** Enumerate carve-outs exhaustively + one contrastive example each. gotcha 2026-05-29.
- **Oracle outputs SCORES only** (0–10 per dim), never tiers — so thresholds change without re-labeling (ADR-016). Lenses overlap; never exclude adjacent-lens content (ADR-015).

### 2. Training data
- **Trained on the raw feed → 99%+ noise, student predicts zero.** ENRICH: screen the corpus for signal-bearing articles first (ADR-003), use e5-seed screening for needles (ADR-011), active-learning for rare tiers (ADR-005). Raw nature_recovery is ~0.3% MEDIUM+; training is enriched to ~15%.
- **Val set is NOT production-representative** (enriched) — don't fit normalization or read "real" rarity off it. ADR-014.

### 3. Metrics (needle filters especially)
- **Judged by MAE → shipped a floor-predictor that surfaces nothing.** For needle filters (MEDIUM+ < ~25%), MAE is the wrong yardstick — a "no to everything" model wins MAE and is useless. Use **Recall@k / NDCG@k / FN@MEDIUM+**. MAE is fine only for balanced filters. gotcha "MAE Is Misleading", dev-guide Issue 4.

### 4. Stage-1 probe (hybrid inference, ADR-006)
- **Probe trained as L1 regression → floor-collapsed, dropped needles.** Train it **recall-first** on the FULL labeled set (`scripts/train_probe.py --objective recall`): binary MEDIUM+ target, class-weighted BCE, threshold from the val recall curve at a target FN — not by minimizing error. Report FN@MEDIUM+, not probe MAE. `feedback-probe-training-data`.
- The shared `EmbeddingStage` screens on `weighted_avg(6-dim) >= threshold` and does NOT apply the gatekeeper at Stage 1 — keep the 6-dim output contract; don't change shared math for one filter. dev-guide Phase 6c.
- **Commit the probe pkl** (`filters/<name>/v<N>/probe/*.pkl`) — it's ~0.5 MB, needed for hybrid inference, and the source package isn't reproducible without it. As of 2026-07-10 the `.gitignore` commits filter probes by default (the old blanket `filters/**/probe/` + `*.pkl` double-ignore was fixed with a `!filters/*/v*/probe/*.pkl` negation); just confirm `git status` shows it staged.

### 5. Calibration + the top band
- **Fit `calibration.json` after every training run** (per-dim isotonic on val, ADR-008). Auto-loaded by the base scorer. Commit it.
- **Top of the scale is unreachable** (data density: ~2 articles at 8–10). Calibration can't invent range. Clip/ceiling the top; do NOT per-band-isotonic 2–3 points. Fix = more high-band data (active learning), not loss tricks.

### 6. Cross-filter comparability

- **The complete method (math, fit convention, guard table, reproduction steps, incident numbers) is `docs/NORMALIZATION_METHOD.md`** — the canonical reference; this section is the operational digest.
- **Read `docs/adr/014-cross-filter-percentile-normalization.md` before touching normalization.** Everything below is a consequence of it, and on 2026-07-14 an agent spent hours "discovering" a bug that ADR-014 specifies on purpose. The three things it gets wrong when unread:
  - **Normalization exists ONLY for ovr.news** — HOME-tab cross-lens ranking and article-tab assignment. It is *not* a filter-quality mechanism. Uplifting passes 62.8% MEDIUM+ and nature_recovery 0.3%, so raw scores are not comparable across lenses; percentile rank makes "how exceptional is this *for its own lens*" comparable. Don't reason about it as if it gates quality.
  - **Tier is REASSIGNED on the normalized score, by design** (ADR-014's pipeline: calibrate → weighted average → gatekeeper → normalize → *reassign tier* → display_rank). So **`raw >= threshold` together with `tier: low` is CORRECT, not a bug** — the article is at the bottom of its own MEDIUM+ population. Both an agent and a review model read this as a defect on the same day. `production_scorer.py`'s module docstring explains it; read that before filing anything.
  - **Fit at `raw >= the filter's own tier threshold`** — that is what ADR-014's "production MEDIUM+ data" means. 7 of 10 fitted files sit at exactly `raw_min == 4.0` (the other 3 are the incident exemptions). This is now enforced: `tests/unit/test_normalization_invariant.py`.

- **`raw_min` off the tier threshold is the only normalization failure this project has ever had — in both directions.** Fit **too low** → sub-visibility content maps into the visible band: nature_recovery v2 at 1.5 (fit-set median 2.19) mapped correctly-scored doom at raw 2.2–3.3 to normalized 5.2–8.3, put decline stories on the Recovery lens at 8.34/10, was misdiagnosed as a *model* failure, and spawned a keyword cap that took 14 months to retire (**NexusMind#161**). Fit **too high** → everything between the threshold and `raw_min` clamps to ~0 via `np.interp`'s edge behaviour: foresight v1 at 5.01 sent raw 4.60 → wavg 0.02 (**NexusMind#205**). Guards now exist on both sides — `MAX_NORMALIZATION_RAW_MIN=4.5` at load, and the fitter refuses `--min-score` below the op-point — but the invariant test is what catches it at commit time. Since 2026-07-16 the fitter also **anchors** the CDF's lower edge to the op-point (`raw_min == op_point` by construction, dense or sparse), so `raw_min` can no longer drift; the bias signal moved to `stats.sample_min` (lowest article actually observed) — a `sample_min` far above the op-point means the fit population never reached the visibility threshold (the #205 root cause; the fitter hard-blocks it above 4.5 and the invariant test rejects it in a package). Guard-relaxed fits require `--analysis-only` with an `--out` not named `normalization.json`.

- **Scope the fit to one version.** `fit_normalization.py` now defaults `--filter-version` to the config's own version. It previously defaulted to None and the documented command omitted it, so a fit blended distinct models' distributions: fitting nature_recovery v4 against the live rolling window pulls in **114,252** articles from other versions. Two sessions were burned on CDFs that were quietly blended.

- **A fit under 200 articles is not a fit.** `MIN_NORMALIZATION_ARTICLES=200`; below it ProductionScorer silently falls back to linear `score_scale_factor`, so a thin fit yields a file that looks deployed and is inert. The fitter now refuses. For a needle filter that's weeks of live accumulation — don't wait, rescore a production-representative historical harvest (below).
- **Linearly rescaling each filter to 0–10 → the compressed filter hijacks the shared feed.** Calibration is within-filter (vs its oracle); cross-filter comparison needs **percentile normalization** from the *production* CDF (ADR-014), non-linear, refit per version. Don't retry z-score / P99 / val-CDF (all tested-dead, `calibration-history.md`).
- **A fresh version ships without `normalization.json` → a weeks-long cold-start where it's mis-ranked against every other lens.** With no normalization, `production_scorer.py` emits RAW `weighted_average`; every OTHER lens emits *normalized* scores. Cross-lens assignment (ovr `canonical-lens.ts` picks the highest `weighted_average` across scorers) and ovr's uniform display gate (`ranking.displayScoreThreshold`, calibrated for normalized scores) then both treat the new filter unfairly — under-ranked and under-shown — until ≥200 production MEDIUM+ accrue, which is **weeks for a needle** (nature ≈ 0.3% MEDIUM+ → ~3–4/batch). **Close the cold-start at deploy: rescore a *production-representative historical harvest* with the new model to synthesize the production CDF, then fit `normalization.json` before go-live** — don't wait for live accumulation. The corpus exists (FluxusSource `~/local_dev/FluxusSource/data`, 1.2 GB; NexusMind filtered output, 100K+ articles). **It must be at the production base rate** (~0.3% MEDIUM+ → ~145K rescored articles to reach 200 MEDIUM+), NOT the enriched training/val set (§2 — enrichment skews the CDF harsh). `production_scorer.py`'s `MIN_NORMALIZATION_ARTICLES=200` guard enforces this: a thin fit (e.g. 33 articles) is silently rejected and the filter stays raw. Why this wasn't the default: ADR-014 framed normalization as fit-from-*live*-production and the doc encoded "wait for ≥200 production articles" — nobody separated "don't use *enriched* data" (true) from "you *can* rescore *historical production* data now" (also true). **Evidence:** nature_recovery v4 shipped raw-only 2026-07-10; for the ~10-day v2→v4 window overlap, still-in-window *inflated* v2 scores out-ranked fresh v4 articles on ovr → "no new nature articles" even though v4 was producing *more* genuine MEDIUM+ than v2 (v2's fuller feed was ~90% normalization inflation of raw≈2 tier=low articles). gotcha 2026-07-11.

### 7. The deploy gate (trust)
- **Gate judged the candidate against the PRIOR model → false FAIL.** Judge against **held-out ORACLE ground truth** (the oracle you chose = the editorial line), not the previous model. `scripts/gate/ground_truth_gate.py`, ADR-021.
- **Reference cohort was a different oracle's labels** (a `_v2_split`-tagged Gemini cohort +1.775 inflated) → the whole "12 student errors" was an artifact. On any surprising FAIL, **reproduce** — read the actual per-item labels before retraining. gotcha 2026-07-09, augmented-engineering#25.
- **"unit-tested"/"promoted to X.md" claimed but the file didn't exist.** A claim is false until the artifact exists — grep for it. `feedback-claim-requires-verify`.
- **Run the multi-agent review battery BEFORE any paid oracle run or "verified" claim**, not after. gotcha 2026-07-08.

### 8. Deploy (the outage-prone part — follow the checklist below)
- **Version-bump: inference modules still imported vN-1 → crashed the real entrypoint.** Repoint imports AND the `inference_hub.py` `repo_id: str = "...-vN"` default; construct the REAL scorer class (not `load_filter_package`, which masks stale imports by name-substring). `verify_filter_package.py` catches the repo_id. gotcha 2026-07-08, cluster #44/#52.
- **Keep PEFT adapters in OLD key format** (`.lora_A.weight`, `score.weight`). Never run `resave_adapter.py` before Hub upload (ADR-007). Verify: 0 `.default.` keys.
- **A config value read by NO code is inert — grepping for it "verifies" nothing.** nature_recovery v4's tuned operating point (`scoring.tiers.medium.threshold: 3.75`) was consumed by zero scoring code; the runtime `TIER_THRESHOLDS` hardcoded medium=4.0, so v4 ran at the un-tuned 4.0 for its whole deploy while every doc claimed 3.75 (ovr.news hides tier=low, so the [3.75,4.0) band was scored+hidden). The deploy check was `grep -q '3.75' config.yaml` — it passed on the inert field. Verify a config value is actually **read + applied at runtime** (trace it to the code path, or assert the live behavior it should produce), never that the string exists. Same shape as the score_scale_factor pit below. Found by the multi-model review, 2026-07-10 (F1).
- **A fresh version must ship `score_scale_factor: 1.0` AND no `normalization.json`.** Production (`production_scorer.py`) applies `score_scale_factor` as the linear fallback when normalization.json is absent — a stale v2 value silently stretches scores + defeats the gatekeeper/threshold design. Only a LIVE-scoring check catches it (the base-scorer smoke test skips the wrapper). gotcha 2026-07-10.
- **Scaffolded `normalization.json` was a stale v2 copy** → would normalize vN through the old CDF. A fresh version ships with NO normalization.json; refit on ≥200 vN production articles — **or synthesize the CDF at deploy via a production-representative historical rescore (§6) to avoid the weeks-long cold-start.** gotcha 2026-07-09, ADR-014.
- **`deploy_filters.sh` excludes `*/model/`** (#67) → code lands without weights → strict startup weight-check crashes the WHOLE scorer (discovery uses LATEST version, so a new dir auto-activates). **Pre-place the model** on gpu-server before the rsync (it's preserved by the exclude). gotcha #67 + investment-risk symlink outages.
- **Same-seed re-train ≠ the evaluated model** (CUDA nondeterminism gave recall 0.55 vs 0.67). Back up the approved model+calibration+metadata together at approval time; if you must re-train, re-run the gate on the new weights. gotcha 2026-07-09.
- **`deploy_to_nexusmind.sh` swept unrelated WIP / is Windows-pathed.** Explicit-stage only the deploy paths; watch `filters/common` rsync for contamination (obituary_detector, 2026-07-09); it still needs Linux porting (`C:/local_dev`, `python`→`python3`). gotcha 2026-05-23.
- **`.nexusmind-owns` empty by default** — production-runtime concerns live in NexusMind's `production_scorer.py` wrapper, not in shared `filters/common` math. Sync common freely; don't let a manifest hide 18-day silent divergence. gotcha "Manifest as Anti-Pattern".

---

## Deploy safety checklist (each item = a past outage it prevents)

Canonical chain: **llm-distillery git → NexusMind git → sadalsuud `deploy_filters.sh` → gpu-server.** Full write-up: `docs/nature_recovery_v4_DEPLOY_COMPLETION.md`.

1. `verify_filter_package.py --check-hub` passes (imports / repo_id / version / Hub fresh). *(→ #44)*
2. Ground-truth gate PASS vs held-out oracle labels; no regression vs incumbent. *(→ ADR-021)*
3. Remove stale `normalization.json` if the version is fresh. *(→ ADR-014)*
4. NexusMind commit is **only** the filter dir — no model weights (gitignored), no `filters/common` contamination. *(→ 2026-05-23)*
5. **Pre-place `model/` on gpu-server** before `deploy_filters.sh` (survives the `*/model/` exclude). *(→ #67)*
6. Scorer restarts healthy: `/health` OK + **all N filters have weights** + live smoke test scores the fixture in range (wrong weights → <1.0). *(→ investment-risk outages, systemd-context gotcha)*
7. Keep the prior version as fallback (rollback = delete the new dir; discovery falls back). Normalization refits once ≥200 production articles — **or fit at deploy from a production-representative historical rescore (§6) to avoid the cold-start where the new version is mis-ranked against normalized lenses.** *(→ 18-day normalization regression, 2026-07-11 cold-start)*
8. Full Fluxus→Nexus→ovr run confirms on the next harvest cycle — verify with a **disk-based** check, never a transient port. *(→ 2026-07-04 phantom-outage gotcha)*

---

## When you point me here

Say *"new filter"* or *"retrain <filter>"* and start from this page. I will:
1. Read this + the canonical `nature_recovery v4` package.
2. Run the oracle bake-off (bias first), design/verify the prompt, enrich the data.
3. Train student + recall-first probe, judge on ranking metrics, calibrate.
4. Gate against held-out oracle ground truth, then deploy via the checklist above.
