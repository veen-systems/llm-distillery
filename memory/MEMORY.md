# Memory Index

<!-- verify: python3 scripts/verification/check_index_budget.py -->
<!-- verify: python3 scripts/verification/check_index_budget.py --target project -->
<!-- verify: python3 scripts/verification/check_index_budget.py --target loaded -->
<!-- verify: python3 scripts/verification/check_index_budget.py --target pointers -->
<!-- verify: python3 scripts/verification/check_index_budget.py --target surface -->
<!-- verify: python3 scripts/verification/check_doc_claims.py -->
<!-- verify: python3 scripts/verification/check_claim_shapes.py -->
<!-- verify: python3 scripts/verification/check_training_provenance.py -->
<!-- verify: bash scripts/verification/check_framework_stamp.sh -->

⚠️ **This index is budgeted in SIZE, not lines** (bytes — the guard reads `"rb"`; say bytes when quoting it). It reached **54,808 chars in 91 lines** on 2026-08-15 (up 69% in three days) because entries grow by lengthening, so a line-count heuristic never fires. Session detail belongs in `project_session_*.md`; an entry here is a hook that answers *should I open that file?* ⛔ **This file is NOT auto-loaded** — it is reached by a `CLAUDE.md` pointer row. The always-loaded layer is `CLAUDE.md` plus the USER auto-memory index, budgeted together by `--target loaded` (#138).

⛔ **THE SESSION LOG HOLDS FOUR ENTRIES. The fifth is MOVED to [`session-log.md`](session-log.md), never compressed.** (#123, 2026-08-25.) The index was 69% session entries by character and grew ~600–900 per session against a fixed ceiling; hand-trimming recovered ~100 chars per line removed, so it lost roughly 6:1 — and every trim turned a finding into a pointer, which is how the always-loaded layer quietly stopped being a record. **Moving costs nothing and loses nothing.** A revision to an existing entry is as expensive as a new one, so budget for both.

*Standing rules moved to `CLAUDE.md` § Hard Constraints → "Working rules" on 2026-08-06 (context audit): they are always-needed constraints, and this file is navigational. This index is pointers + session log only.*


- **2026-10-13 — TODO 00 lab layout DONE (`lab.py move`, layout guard, prereg-inbox + stale-path checks; 10-12 data re-homed, training sets in the lab); ovr.news page ranking REPRODUCED (recency = the H-BB7 reorderer; editor boosts a no-op, ovr.news#390); formulas A/B/C/H replayed for the owner; daily baseline pre-registered** ([session](project_session_2026_10_13_lab_layout_site_ranking.md)) — $0 oracle; deploy N/A. ⛔ Mine: owner counts sent 1 low (uncorrected labels). ▶ **NEXT: qwen tags for the baseline when b650 is free; owner: ranking options, EXP-048 `lab` (a/b/c).**
- **2026-10-12 (evening) — belonging `focus` tag RULED; v3 FAILS the ≤ 6/30 bar (owner 10/30); candidate c2c ($0, personal training rows scaled down) FAILED its recall guard; the page's top is NOT v3's raw top (7/30 overlap, H-BB7); read surface → 519,680 at close** ([session](project_session_2026_10_12_belonging_c2c.md)) — $0 oracle; deploy N/A. ⛔ Mine: a gatekeeper build defect found after the verdict; an overclaimed tagger pass. ▶ **NEXT: TODO 00 lab layout rules (owner: first), then 0a.**
- **2026-10-12 — read surface (#163) pruned 758,893 → 549,178 chars in two rounds (round 2: owner ruled September rule stories + mid-month gotcha pass) + a surface ratchet; 3 gotcha classes mechanized (oracle 402 stop, prepare_data zero-match exit 1, wrong-interpreter banner), 4 catalogue entries retired; belonging 0a step 1: c2a re-gate premise fails by construction** ([session](project_session_2026_10_12_read_surface.md)) — $0 oracle; deploy N/A. ⛔ Mine: kill-hook backtracking test was RED at HEAD unnoticed. ▶ **NEXT: owner question in TODO 0a (are c2a's single-person `in_scope` rows "personal"?), then 0a step 2.**
- **2026-10-10/12 — belonging v3's top of page is mostly single-person (owner); bar RULED ≤ 6/30; situla RULED single source of truth: lab tool + manifest check (2 review rounds), all LD host data in ~/ld-lab, 18 host items deleted** ([session](project_session_2026_10_10_situla_ssot.md)) — $0 oracle; deploy N/A. ⛔ Mine: 2 retracted answers (v1 rows read as v3), 2 false claims to a peer, fixes refuted twice. ▶ **NEXT: TODO item 2 (read surface — owner: cleaning FIRST), then 0a (belonging top-30 count).**






- 🧭 **[`/audit-context` Step 8 — what each check has ever caught](../docs/decisions/2026-09-17-audit-step-attribution.md)** — the per-step catch table, and the standing rule that every audit close records findings WITH THE STEP THAT FOUND THEM. Step 7 had its first catch 2026-09-26 (`memory/archive/` was gitignored), so it is no longer a retirement candidate.

- 📓 **Older sessions — [`memory/session-log.md`](session-log.md)** — entries before the four above from 2026-09-22 on, VERBATIM (`grep -cE '^- ' memory/session-log.md`; do not quote a count from memory). Older ones are in `archive/session-log-*.md`; rotate with `scripts/maintenance/retire_memory.py sessionlog --before <date>`. The index keeps the newest four; `/curate` MOVES the fifth into the log rather than compressing it, so no finding is ever shortened to buy space. **Look there before concluding something was never recorded.** Session files dated before 2026-09 are in [`archive/`](archive/) (moved 2026-09-26 by `scripts/maintenance/retire_memory.py sessions`).

- [Date errors & the recency boost](date-error-recency-boost-hypotheses.md) — any date error landing inside the boost window wins it, invisibly. ⚠️ `collected_date − published_date` is NOT a fabrication instrument without a `source` breakdown. Read before touching dates, the boost or an age-derived figure
- [Hypothesis ledger](hypothesis-ledger.md) — ⭐ **start here to recall prior work**: open hypotheses; closed rows in [`archive/hypothesis-ledger-archive.md`](archive/hypothesis-ledger-archive.md) — grep both. ⛔ `H4` is defined in FOUR files — always qualify the id; corroboration ids live in NexusMind's V&V registry
- [Corroboration feature hypotheses](corroboration-feature-hypotheses.md) — the cosine/time/NER features already exist and were measured. **The threshold is not the lever** (a gate is). Read before proposing NER or matching-feature work
- [Google News corpus hypotheses](google-news-corpus-hypotheses.md) — ⛔ never oracle-re-score a GN row, never match GN on a `gn_` prefix, always say feeds vs rows vs items (up to 5× apart). Read before quoting any GN number
- [CD v6 probe hypotheses](cd-v6-probe-hypotheses.md) — #98 (the cd e5 probe): screening is a REGRESSION; v6 cannot score (no inference module, no calibration)
- [Cross-repo prioritization](cross-repo-prioritization.md) — issue landscape across 7 repos and the live chains. ⛔ **No board count is stated there — run the `gh` loop at its head and quote with a timestamp**; do not restore one
- [Stamp & contract integrity](stamp-contract-integrity.md) — the stamps were never validated; schemas check SHAPE only. Read before adding a stamp or trusting a stamped field. ⚠️ The contract is being REDESIGNED: read `docs/proposals/contract-a-redesign.md` first (#112 supersedes #111)
- [Opinion/editorial genre hypotheses](opinion-genre-hypotheses.md) — #121 (opinion genre): the within-source control dissolves the effect in 5 of 6 lenses. Read before quoting a #121 number or building a genre stamp
- [Filter status](filter-status.md) — current state of all production filters and in-development versions
- [NexusMind data sources](nexusmind-data-sources.md) — what each production artefact EXCLUDES; `filtered_*.jsonl` also drops source-type-excluded rows, `data/raw/` is pre-enrichment
- [Prefilter & length-floor hypotheses](prefilter-length-floor-hypotheses.md) — what each prefilter actually blocks; read before any enforcement flip
- [Batch-shape score noise](score-batch-shape-noise.md) — a score depends on its batch, not the article alone (#95). ⛔ **A floor belongs to a population and a mechanism** — five measured terms, never pick one by magnitude, never inherit one; v8's scope gate is a step function, not a floor. Read before any threshold or op-point measurement
- [Enrichment-delta hypotheses](enrichment-delta-hypotheses.md) — NM#310 (NexusMind: GN redirects never resolve, so GN is not enriched) is a compute story, not a quality story; enrichment moves evidence-quality dimensions most. Read before citing a pre/post-enrichment delta
- [GPU server](gpu-server.md) — venv, PYTHONPATH, HF_HUB_OFFLINE, ollama conflict, training setup
- [b650 GPU](b650-gpu.md) — the training node, RTX 5090 since 2026-09-17: ⛔ re-dump older b650-CUDA dumps, never diff them; ⛔ production serves on GPU, so match the DEVICE before diffing a replay against production scores
- [Gotcha log](gotcha-log.md) — problems/fixes from 2026-09 on, the unreachable-mechanism catalogue, the Mechanized table; older entries in [`archive/gotcha-log-archive.md`](archive/gotcha-log-archive.md) — grep both
- [Calibration history](calibration-history.md) — Dead Ends (#69): read before calibration, scorer or oracle-prompt work
- [Gemma-3 model](gemma3-model.md) — Auto mapping fix, key format; read before debugging model loading or PEFT
- [Oracle pricing & scheduling](oracle-pricing-scheduling.md) — ⛔ **Gemini Batch is a price we CANNOT PAY** (no call site); among implemented paths DeepSeek off-peak wins. The lever is the per-prompt cache ceiling (#131)
- [ovr lens set](ovr-lens-set-current.md) — current lens→filter→tab mapping
- [Filter doc standard](filter-doc-standard.md) — deployed filter documentation set
- [CD v5 reference status](cd-v5-reference-status.md) — cultural_discovery v5 as the DeepSeek-oracle reference, ADR-020 methodology
- [Obituary detector](project-obituary-detector.md) — enforcement state, live false negatives, the four SSH verify assertions. Read before touching or reading the junk gates. 44% of misses are title/body pooling (#159, `obituary-v4-hypotheses.md`); NOT blind to non-Latin (H-DET6, ledger archive)
- [Obituary v4 hypotheses](obituary-v4-hypotheses.md) — small-N hard negatives work, panel beats oracle labels. ⛔ its v3/v4/v5 numbers are SINGLE-SEED and the ordering does not survive (#158)
- [Violence promotion v1 hypotheses](violence-promotion-v1-hypotheses.md) — recipe transfer confirmed; the recall gap is the open question
- [Uplifting v7 training](uplifting-v7-training.md) — training history; v7 deployed (hybrid inference)
- [Thriving v1 scoring](thriving-v1-scoring.md) — PARKED indefinitely (ADR-015); resume commands
- **Before 2026-08-01 — 23 session files in `memory/archive/`** (`ls memory/archive/project_session_2026_0[57]*.md`): cd v5, nr v4 and solutions v4–v6 deploys, 2026-07-17 deploy hardening, 2026-07-31 refit day. ⛔ A pointer is not a summary — open the file, do not infer the session from its name
