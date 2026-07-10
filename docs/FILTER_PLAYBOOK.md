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
- **`.gitignore` has `filters/**/probe/` — the probe pkl won't be committed by default**, leaving the source package non-reproducible (the pkl is ~0.5 MB and needed for hybrid inference). **`git add -f` the probe pkl** (belonging v1 + nature_recovery v4 both track theirs). Found 2026-07-10 checking v4's components.

### 5. Calibration + the top band
- **Fit `calibration.json` after every training run** (per-dim isotonic on val, ADR-008). Auto-loaded by the base scorer. Commit it.
- **Top of the scale is unreachable** (data density: ~2 articles at 8–10). Calibration can't invent range. Clip/ceiling the top; do NOT per-band-isotonic 2–3 points. Fix = more high-band data (active learning), not loss tricks.

### 6. Cross-filter comparability
- **Linearly rescaling each filter to 0–10 → the compressed filter hijacks the shared feed.** Calibration is within-filter (vs its oracle); cross-filter comparison needs **percentile normalization** from the *production* CDF (ADR-014), non-linear, refit per version. Don't retry z-score / P99 / val-CDF (all tested-dead, `calibration-history.md`).

### 7. The deploy gate (trust)
- **Gate judged the candidate against the PRIOR model → false FAIL.** Judge against **held-out ORACLE ground truth** (the oracle you chose = the editorial line), not the previous model. `scripts/gate/ground_truth_gate.py`, ADR-021.
- **Reference cohort was a different oracle's labels** (a `_v2_split`-tagged Gemini cohort +1.775 inflated) → the whole "12 student errors" was an artifact. On any surprising FAIL, **reproduce** — read the actual per-item labels before retraining. gotcha 2026-07-09, augmented-engineering#25.
- **"unit-tested"/"promoted to X.md" claimed but the file didn't exist.** A claim is false until the artifact exists — grep for it. `feedback-claim-requires-verify`.
- **Run the multi-agent review battery BEFORE any paid oracle run or "verified" claim**, not after. gotcha 2026-07-08.

### 8. Deploy (the outage-prone part — follow the checklist below)
- **Version-bump: inference modules still imported vN-1 → crashed the real entrypoint.** Repoint imports AND the `inference_hub.py` `repo_id: str = "...-vN"` default; construct the REAL scorer class (not `load_filter_package`, which masks stale imports by name-substring). `verify_filter_package.py` catches the repo_id. gotcha 2026-07-08, cluster #44/#52.
- **Keep PEFT adapters in OLD key format** (`.lora_A.weight`, `score.weight`). Never run `resave_adapter.py` before Hub upload (ADR-007). Verify: 0 `.default.` keys.
- **A fresh version must ship `score_scale_factor: 1.0` AND no `normalization.json`.** Production (`production_scorer.py`) applies `score_scale_factor` as the linear fallback when normalization.json is absent — a stale v2 value silently stretches scores + defeats the gatekeeper/threshold design. Only a LIVE-scoring check catches it (the base-scorer smoke test skips the wrapper). gotcha 2026-07-10.
- **Scaffolded `normalization.json` was a stale v2 copy** → would normalize vN through the old CDF. A fresh version ships with NO normalization.json; refit on ≥200 vN production articles. gotcha 2026-07-09, ADR-014.
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
7. Keep the prior version as fallback (rollback = delete the new dir; discovery falls back). Normalization refits once ≥200 production articles. *(→ 18-day normalization regression)*
8. Full Fluxus→Nexus→ovr run confirms on the next harvest cycle — verify with a **disk-based** check, never a transient port. *(→ 2026-07-04 phantom-outage gotcha)*

---

## When you point me here

Say *"new filter"* or *"retrain <filter>"* and start from this page. I will:
1. Read this + the canonical `nature_recovery v4` package.
2. Run the oracle bake-off (bias first), design/verify the prompt, enrich the data.
3. Train student + recall-first probe, judge on ranking metrics, calibrate.
4. Gate against held-out oracle ground truth, then deploy via the checklist above.
