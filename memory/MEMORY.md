# Memory Index

## Standing rule (promoted from gotcha log 2026-08-01 — 3 instances in one day)

**Before using any source as evidence, establish what it excludes.** This applies
to data (`filtered_*.jsonl` is 100% passers by construction), to nested structures
(`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior
work (`gh repo list` misses repos with no remote), to literature (a search
snippet reported a model's *worst* two techniques as its best), and — added
2026-08-02 — to **time** (`data/raw/` is pre-enrichment, so it cannot stand in
for what the scorer saw: 0.008 vs a true 0.647) and to **a second exclusion on
an artefact you already thought you understood** (`filtered_*.jsonl` drops
source-type-excluded rows too, worth 0.129 on investment_risk). A clean-looking
result from an unexamined source is the hardest kind to falsify, because being
right supplies no pressure to check how you got there. If it's a denominator, a
baseline, or a claim of absence — enumerate the source first, and if the owner
knows the set, ask them rather than inferring it.

## Standing rule (promoted from gotcha log 2026-08-03 — 2nd occurrence in this tree)

**A parallel agent session may be working in the same checkout, so no git verb
may take the whole tree as its argument.** `git add -A`, `git stash` with no
pathspec, `git checkout .`, `git clean` — each one's blast radius is every
modified file, including work you did not make and cannot see. First occurrence
(2026-08-03 morning) swept a seven-file filter sync into a docs commit; second
(same day, evening) stashed another session's `image_analysis.py` while
baselining a test suite, producing a "before" measurement of a tree that never
existed and 8 phantom failures. **Always pass explicit paths**, and before
committing in a shared repo run `git status --porcelain` and stage only what you
recognise. If a sweep is discovered after push, record it — do not rebase
history another session may hold.

- [Cross-repo prioritization](cross-repo-prioritization.md) — master issue landscape across 5 repos (**177 open**): P0-P4, **14 dependency chains**, 6 work batches, plus a Coverage section naming the 57 issues in no band. Chain 3 CLOSED; Chain 4 re-rooted on #93; Chain 8 deadline-driven (FS#120 ~2026-08-14). **Updated 2026-08-03: new Chain 13 (score reproducibility — #95 sits under every threshold decision) and Chain 14 (non-English quality, four repos, root NM#292). Third pass records the four changes shipped that evening.**
- [Filter status](filter-status.md) — current state of all production filters and in-development versions
- [NexusMind data sources](nexusmind-data-sources.md) — what each production artefact EXCLUDES; `filtered_*.jsonl` also drops source-type-excluded rows, `data/raw/` is pre-enrichment
- [Prefilter & length-floor hypotheses](prefilter-length-floor-hypotheses.md) — what each prefilter actually blocks (measured 2026-08-02); #93 shipped + synced 2026-08-03; read before any enforcement flip
- [Batch-shape score noise](score-batch-shape-noise.md) — **a score is not a function of the article alone**: batch composition moves it up to 0.17 and flips 7-9% of near-boundary surfacing decisions (#95). Read before any threshold/op-point measurement
- [GPU server](gpu-server.md) — venv, PYTHONPATH, HF_HUB_OFFLINE, ollama conflict, training setup
- [b650 GPU](b650-gpu.md) — Arian's 3090 Ti training node: access (account jeroen), uv venv, staged data, cross-box score-skew warning
- [Gotcha log](gotcha-log.md) — problem/fix archive
- [Calibration history](calibration-history.md) — Dead Ends section: approaches known to fail (#69); read before calibration/scorer/oracle-prompt work
- [Gemma-3 model](gemma3-model.md) — Auto mapping fix, key format details; read before debugging model loading or PEFT issues
- [Oracle pricing & scheduling](oracle-pricing-scheduling.md) — DeepSeek V4 peak/valley pricing; schedule batch jobs off-peak
- [ovr lens set](ovr-lens-set-current.md) — current lens→filter→tab mapping
- [Filter doc standard](filter-doc-standard.md) — deployed filter documentation set
- [CD v5 reference status](cd-v5-reference-status.md) — cultural_discovery v5 as DeepSeek-oracle reference example, ADR-020 methodology
- [Obituary detector](project-obituary-detector.md) — ENFORCEMENT ON v5@0.85, VERIFIED + overnight-checked 2026-07-31; site carryover washes out ~Aug 13 (owner: no purge); 2 live v5 FNs banked on LD#85 (parked)
- [Obituary v4 hypotheses](obituary-v4-hypotheses.md) — small-N hard negatives work, panel beats oracle labels; "FNs are cheap" FALSIFIED 2026-07-30
- [Violence promotion v1 hypotheses](violence-promotion-v1-hypotheses.md) — recipe transfer confirmed, prompt boundary holds, recall gap is the key open question
- [Uplifting v7 training](uplifting-v7-training.md) — training history; v7 deployed (hybrid inference)
- [Thriving v1 scoring](thriving-v1-scoring.md) — PARKED indefinitely (ADR-015); scoring status, resume commands

## Recent Sessions

- [2026-08-03 evening](project_session_2026_08_03_evening.md) — **all three junk gates verified against the running box**: obituary enforcing (max surviving score 0.8488, zero ≥0.85), commerce enforcing (LD#80 `v1` pin holds), violence inert by design. **Commerce provenance fix** (86.4% of corpus had a verdict with no model version) and **seeded cycle replay for #95** both DEPLOYED. sustech v3 + foresight v1 REMOVED (#64 closed). Scorer call path settled — `/home/hcl/llm-distillery/` on gpu-server is a stale decoy. **#90 not ready: audit which template elements are load-bearing (#94, #92) before spreading.** **NEXT: verify next cycle (run-seed line + commerce `processed` ≈21,000 once)**
- [2026-08-01 afternoon](project_session_2026_08_01_afternoon.md) — four-repo re-inventory (156 open, **12 chains**, new P0 set incl. LD#91/ovr#284/ovr#285); **persuasion-scorer split out** as a verified system under three agent-ready frameworks (LD#78/#79 externalized); post-deploy checks 1+3 PASS (`_commerce_model: v1`, `violence_blocked` gone from Loaded line), 2+4 pending mid-cycle. **NEXT: finish checks 2/4, then NM#285 measurement**
- [2026-07-31](project_session_2026_07_31.md) — obit carryover diagnosed (47 shadow-era + 2 v5 FNs); LD#76 11-agent audit falsified shared-root-cause; EXECUTED: uplifting+belonging refits, cd topic gate (#86), NM#280 tier fix — all deployed; ADR-022 written; LD#90 harmonization program (renames: thriving/discovery/recovery). **NEXT: verify ~12:00 cycle (3 checks), then close NM#279/#280, LD#74/#76/#86**
- [2026-07-30](project_session_2026_07_30.md) — S1: v4 op-point evidence + swap. S2: deploy verified, FN-delta gate FAILED, DeepSeek-commit review. S3: v5 trained + review battery + June panel, owner adjudication (grief-vs-news), ENFORCEMENT v5@0.85 shipped, b650 commissioned
- [2026-07-28](project_session_2026_07_28.md) — obituary v4 retrain, violence_promotion v1 shadow-deploy, solutions v6 normalization fitted
- [2026-07-27 evening](project_session_2026_07_27_evening.md) — LD#49/#68/#63/#57 closed; NM#276/#206 closed; curate
- [2026-07-27](project_session_2026_07_27.md) — solutions v6 gate PASSED, obituary NM#185 Phase 3 deployed, playbook update
- [2026-07-26 evening](project_session_2026_07_26_evening.md) — solutions v6 train (probe-split retraining, val MAE 0.476)
- [2026-07-26](project_session_2026_07_26.md) — multi-repo triage, cross-repo dependency chains, P0-P4 priority ranking
- [2026-07-22](project_session_2026_07_22.md) — solutions v4 deployed & live-scoring, ADR-020, NexusMind cutover
- [2026-07-21](project_session_2026_07_21.md) — solutions v4 gate, nr v4 ground-truth comparison, calibration fixes
- [2026-07-20](project_session_2026_07_20.md) — solutions v4 hybrid scorer, probe threshold calibration, production prep
- [2026-07-19](project_session_2026_07_19.md) — solutions v4 training, calibration, normalization fitting
- [2026-07-18](project_session_2026_07_18.md) — solutions v4 rename (ADR-012), oracle rescore, training data prep
- [2026-07-17](project_session_2026_07_17.md) — Fix A normalization hardening, Fix B deploy hardening, review battery
- [2026-07-17 evening](project_session_2026_07_17_evening.md) — Fix B EXECUTED: git-archive staging, deploy validation
- [2026-07-16](project_session_2026_07_16.md) — normalization anchor fix (#205 root cause), calibration audit prep
- [2026-07-14](project_session_2026_07_14.md) — climate_doom cap retired, nr v4 op-point wiring, normalization refits
- [2026-07-11](project_session_2026_07_11.md) — nr v4 training, calibration, ground-truth comparison
- [2026-07-10](project_session_2026_07_10.md) — nr v4 deployed, normalization refit, op-point validation
- [2026-07-09](project_session_2026_07_09.md) — nr v4 ground-truth gate, multi-model review, ADR-021
- [2026-07-08](project_session_2026_07_08.md) — nr v4 oracle rescore, prompt fixes, protection scope (#70)
- [2026-07-04](project_session_2026_07_04.md) — nr v4 planning, ground-truth design, oracle selection
- [2026-05-31](project_session_2026_05_31.md) — cd v5 deployed, #62 leakage resolved, DeepSeek oracle reference
- [2026-05-29](project_session_2026_05_29.md) — cd v5 #62 hard-negatives, oracle prompt v5 deltas
