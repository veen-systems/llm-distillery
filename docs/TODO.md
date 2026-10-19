# LLM Distillery - TODO

## ▶️ START HERE — the ordered queue, as of 2026-10-19

*▶ **NEXT SESSION (set 2026-10-19 close; `/curate` done, all pushed). "continue" = these, in order:**
**(1) ✅ DONE 2026-10-19 (round 10, below in item 2: 472,366 → 444,103).** ~~#163 round 10, THINNING (owner 10-19: "start pruning, thinning, mechanizing, retiring").~~ Date-retirement is
exhausted (nothing in the gotcha log or sessions predates 10-01; ledger rows left are open or carry ⚠️). The surface lives
in the standing topic files: `working-rules` 26.0K, `stamp-contract-integrity` 25.5K, `score-batch-shape-noise` 25.4K,
`nexusmind-data-sources` 24.2K, `oracle-pricing-scheduling` 24.0K, `calibration-history` 22.1K (`wc -m`, 10-19). Per file:
move dated/closed narrative VERBATIM to its `archive/` twin (comm-lossless + 1-line mutant), keep each operative rule;
any rule restated in 2+ files → one home + pointer; any rule a check now enforces → its Mechanized row, prose to archive.
Target ≥ 30K; then ratchet the ceiling to the measured size + 2%.
**(2) #179 fixes, RULED 10-19 (issue comment 6267155020), in this order:** ✅ gate `scripts/score_ollama_oracle.py` for cloud
providers (DONE 10-19: deepseek/gemini gated before any call, own oracle key so another scorer's PASS never admits it —
a guarded prompt needs `--skip-canary` there; ollama ungated; 5 tests, 5/5 mutants killed) → ✅ human_thriving v9 mixed-prompt note in its package docs (DONE 10-19: `filters/human_thriving/v9/README.md`
§ Label provenance; 1,067 labels differ from any oracle output, 350 unexplained; THREE rules differ, not one) → ✅ Krippendorff's alpha/AC1 in
shared analysis code + fix `filters/cultural_discovery/v5/STATUS.md:37` (DONE 10-19: `ground_truth/agreement.py`,
reproduces Krippendorff 2011's published values; cd v5 line + `calibration_report.md` corrected: per-item verdicts lost) → the reader validator (strict for all; missing
provenance raises for new rows only, legacy = explicit `unknown`) and splits that keep provenance.
**(3)** #177 cross-family panel; review leftovers (the one-use PASS claim is read-check-write; a labelling run does not
compare its served model to the PASS's); #178 datasheets. Cleanup: b650 `~/llm-distillery/runs/canary_177b` (149 MB)
after the 2026-10-20 12:00 snapshot (re-hash, then rm; b650 rule). Item 0a stays dated ≥ 10-22, item 0 ≥ 10-23/24.*

*A bare "continue" means this list, top down. Each line names the FIRST action. Item 0 is WAITING (dated, ≥ 10-23/24);
item 0a's next action is dated ≥ 10-22 (the on-site count on live ranking H). Item 0b (#157, label provenance) LANDED
2026-10-16. Item 1 is NexusMind's.
Item 2 (#163, the read surface): keep pruning (owner 2026-10-14 and 10-15: "pruning, thinning, mechanizing, retiring").*

0. ⏸ **BELONGING v3 is LIVE (since NexusMind run `bd00dad6`, 2026-10-09 00:08–01:24 CEST), replacing v1. Nothing to do before
   2026-10-23 unless ovr.news messages.** Read `filters/belonging/v3/STATUS.md` first (evidence, rollback rule, refit notes);
   history in `docs/evidence/2026-10-08-belonging-candidate2-plan/PLAN.md`; all three held-out sets are SPENT. Measured first
   file: 3,673/3,673 rows `version "3.0"`, 19 stage-2 raw ≥ 4.0 (0.52%; v1 ~2.2%). Posted on #170 (the belonging switch issue).
   - 📅 **2026-10-23: ovr's rollback panel** (EXP-028 re-run). Agreed with ovr: sample and goods/day use **v3-scored rows only**
     (ids from NexusMind rows with `belonging.version == "3.0"` joined to ovr's published_observations); too few → ovr delays
     the panel, never mixes in v1. Apply the rollback rule in STATUS.md; rollback = NexusMind's kept previous scorer image +
     sadalsuud revert (NOT removing v3).
   - 📅 **≥ 2026-10-24: refit `normalization.json`** on `version == "3.0"` rows only (`fit_normalization.py --filter-version`);
     fix `filter_version` in calibration.json + normalization.json then; post the date on #170. Earlier only if v3's share of
     raw ≥ 4.0 rows passing normalized ≥ 4.5 falls clearly below v1's 47–66% per file (469/872 = 54% over v1's last 7 files;
     the "< 100%" trigger was wrong — different populations — and fired falsely 2026-10-09).
   - Open, not blocking: FM-S1 judge strictness; harvest round 2 (~$9.70 est.). Single-person stories: see 0a.
   ⛔ **Never name the curator** in this repo or on GitHub (guards: `.githooks/`, gitignored `config/credentials/forbidden_names.txt`).

0a. **BELONGING v3's TOP OF PAGE vs the owner's bar (≤ 6 of 30 single-person stories, judged as a WEEKLY AVERAGE,
   ruled 2026-10-14).** Bar + rulings: `docs/decisions/2026-10-10-belonging-personal-story-bar.md`; ledger H-BB6–H-BB8;
   history: TODO-archive § *Moved 2026-10-14* and § *Moved 2026-10-15* (the full 0a text of 2026-10-15, verbatim).
   State: v3 fails on the owner's one count (10/30, 10-12, old ranking). Ranking H is LIVE since 2026-10-15 (first build
   07:40:42Z; ovr.news commit `07cdb7e0`, ducroq/ovr.news#391, veen-systems/pipeline-atlas#170). Offline replay EXP-049:
   on the qwen floor the OLD ranking fails the bar (6.40, dated, post hoc), H is undetermined (5.20). The training lever
   is CLOSED (owner 2026-10-15): c2c (EXP-048) and c2d (EXP-050) both failed the community recall guard.
   - ▶ **FIRST ACTION, on or after 2026-10-22: the on-site re-baseline of v3 on the LIVE H page.** Pages: the daily
     capture in `~/lab/llm-distillery/inbox/ovr-lens-pages/` (`belonging_<UTC>.html`, 10-15 → 10-21, 7 builds). Steps: (1) write
     `PREREGISTRATION.md` BEFORE reading any page's tags (bar = weekly mean ≤ 6; a qwen mean ≤ 6 is undetermined, > 6 is
     conclusive; predictions); (2) `lab.py move` the 7 pages into a lab `experiments/` tree; (3) parse each page's top 30
     ids, tag on b650 with EXP-049's qwen tagger unchanged (`tag_qwen.py`, `system.txt`, reuse rule + 10-id determinism
     control), report the weekly mean and the worst day. ⚠️ The 10-15 T0750Z/T0755Z files were captured by hand that
     morning; the 16:30 ones are the daily series. Owner's own count is the stronger instrument: offer it.
   - **Over 6 is NOT an automatic rollback** (v3's rollback rule predates the bar; owner's call).
   - ovr (2026-10-16, ovr EXP-060 `9d60310f`): ducroq/ovr.news#391 closes on this count. ⚠️ **Never ship two ACTIVE scorers
     on one lens** (e.g. a belonging version beside another) without telling ovr first: under ranking H, ADR-050's
     per-lens normalisation moves no card only because each lens has one scorer; ovr re-runs `adr050-shadow-diff.ts`.
   - ⏰ **The capture is a user crontab line on situla** (owner OK 2026-10-15; the only line): five lens pages
     (`https://ovr.news/en/{belonging,thriving,solutions,discovery,recovery}/`) daily at 16:30 local (14:30Z until
     10-24, 15:30Z from 10-25). Inert from 2026-11-16 (UTC date guard). Hardened at the 10-15 close (review): `curl -fsSL --retry 2`, so an error page is
     never saved as a page; errors go to `curl.err` in the same dir (cron has no mail here). situla is a laptop: a run
     missed while asleep is NOT caught up, so expect gaps; each file name carries its UTC time. ⛔ **After 2026-11-15 REMOVE it: `crontab -r`.**
     Beyond Belonging it serves LENS ASSIGNMENT (H-LA2, "narrow lens first", never tested against the owner): when the
     owner pastes an article that looks like it is on the wrong tab, find it in that day's pages and record it.
   - Lab: the 10-10 `~/lab/llm-distillery/inbox/` heap (37 backlog citations) is still a later pass (#172, item 00 archived 2026-10-14).

0b. ✅ **#157 (oracle label provenance), phase 1 of veen-systems/pipeline-atlas#169 — LANDED 2026-10-16** (owner order
   2026-10-15: https://github.com/veen-systems/pipeline-atlas/issues/169#issuecomment-6189722887). Every live label
   writer now stamps `prompt_sha256` (full; `prompt_hash` kept as its 12-hex prefix), `served_model` (from the
   RESPONSE), `system_fingerprint` (DeepSeek; `__absent__` elsewhere) and `model_digest` (ollama). Writers:
   `ground_truth/batch_scorer.py`, `scripts/score_deepseek_production.py`, `scripts/score_ollama_oracle.py` (record
   root), the violence oracle and the obituary relabeller; one shared module, `ground_truth/oracle_provenance.py`. A
   missing served model is RUN-FATAL everywhere. Reader that acts: `scripts/oracle/aggregate_k_runs.py` refuses k runs
   that disagree on prompt or served model. Proven live 2026-10-16 (3 rows per scorer path + 1 per detector oracle,
   stamps read back). ⚠️ What it does NOT buy: `served_model` is the TIER (`deepseek-flash`, bare `gemini-2.5-flash`),
   so a V4→V4.1-style swap stays invisible unless `system_fingerprint` moves — UNKNOWN. ⚠️ batch_scorer and the scripts
   hash the same prompt file differently (stripped vs raw): never join across scorers on the hash. Not stamped (legacy
   or one-off): `scripts/validate_deepseek_oracle.py`, `ground_truth/llm_evaluators.py`, the commerce oracle,
   `scripts/analysis/valence_bakeoff.py`; `scripts/oracle/average_oracle_runs.py` (superseded) drops all stamps.
   ▶ Open: does the fingerprint move on a model change? Watch it across the next real runs (comment on #157).

1. **Decision-0 sync to NexusMind** — ONE NexusMind commit. The sequence is in the archived block (item 1):
   - dry-run diff first
   - copy `filters/common/{filter_base_scorer,hybrid_scorer,cli}.py` together with every live package, deleting their `prefilter.py`
   - retarget NM's `test_prefilter.py` / `test_shared_infrastructure.py`
   - run the NM unit suite
   - ⚠️ since NexusMind#395 step 1, sadalsuud no longer auto-pulls: a **manual pull + scorer-image rebuild** is needed
   NexusMind's session runs it; ours is to tell them. LD#52 and LD#86 are closed.

2. **THE READ SURFACE (#163). "prune, thin, mechanize, retire".** Rounds 1–3 landed 2026-10-12: 758,893 → 514,588 chars (519,680 at close, after the session's new records).
   ✅ **Round 10 (2026-10-19, thinning): 472,366 → 444,103**, ceiling 478,386 → 452,985. The six standing files,
   VERBATIM moves to their `archive/*-archive.md` (two new: `score-batch-shape-noise`, `calibration-history`), each
   `comm` lossless (C locale) + 1-line mutant reports 1: working-rules 25,995 → 20,546, stamp-contract 25,532 → 21,550,
   score-batch 25,353 → 21,196, nexusmind-data-sources 24,159 → 20,832, oracle-pricing 23,972 → 20,836,
   calibration-history 22,055 → 13,602 (each Dead End keeps title + full "Don't retry" verdict live, narrative
   elided with `…` + archive link — an excerpt, every kept fragment verbatim). −28.3K, short of the 30K target:
   what remains is operative or shares lines with a rule. No cross-file dedup done (rules' homes are within the set).
   Two stale claims corrected: `score_ollama_oracle.py` DOES stamp `prompt_hash` since #157; score-batch's "FOUR".
   ⚠️ `comm` under the default locale gives false 'missing' lines — use `LC_ALL=C`.
   ✅ **Round 9 (2026-10-19): 474,995 → 472,012** (headroom 3,391 → 6,374; ceiling unchanged — +2% would raise it).
   Verbatim: 10 Mechanized rows (`live`, 0 occurrences, 09-17..09-26) → gotcha archive § *Mechanized rows moved
   2026-10-19*, pointer left in the table. Ledger: nothing movable (H-JO1/BV6/BB4/BB7/ND1 still carry ⚠️ or rulings).
   ✅ **Round 8 (2026-10-18): 475,230 → 469,090** (headroom 3,156 → 9,296; ceiling unchanged, already ~+2%). Verbatim,
   tool-checked: `retire_memory.py gotcha --before 2026-10-16` (4 entries, 45,043 → 41,987) and `sessions --before
   2026-10-16` (the 10-15 session file; index link rewritten). Ledger rows judged NOT movable yet: H-BB4/H-BB7 carry
   ⚠️ open caveats or back live TODO 0a; H-ND1 is two days old. H-CTX-3's revisit DONE the same day: SUPPORTED, weakly (ledger row).
   ✅ **Round 7 (2026-10-16): 477,749 → 469,006**, ceiling → 478,386. Verbatim: `gotcha-log.md` 50,962 → ~42.8K (the
   `## Mechanized` post-table prose of 09-17, the 08-25 watcher entry — class `live` — and `retire_memory.py gotcha
   --before 2026-10-15`, 3 entries); `hypothesis-ledger.md` H-HD11 + H-DEV2 (closed). ⏰ **OWED: H-CTX-3's revisit
   (the CLAUDE.md halving) was due 2026-10-15** — its method is a count over ~10 sessions of findings rooted in a rule
   that used to be spelled out in CLAUDE.md; not run.
   ✅ **Round 6 (2026-10-16): 498,514 → 477,669**, ceiling → 487,222. The four standing files thinned by VERBATIM
   moves of closed material to their `archive/*-archive.md` (each: `comm` lossless + 1-line mutant reports 1):
   `filter-status.md` 30,059 → ~17.5K, `stamp-contract-integrity.md` 28,704 → 25,753, `nexusmind-data-sources.md`
   27,550 → ~24.4K, `oracle-pricing-scheduling.md` 26,783 → ~24.2K. Also: a title split by an old mid-line insert in
   `nexusmind-data-sources.md` restored; filter-status's stale "#151 not decided" corrected. ▶ **Next levers:**
   un-applied thinning proposals (restatements of CLAUDE.md:33 ADR-023 in `filter-status.md`, ~1K; `data/raw`
   written-back twice); `gotcha-log.md` (51K) and `hypothesis-ledger.md` (45K) remain the two largest.
   ✅ **Round 5 (2026-10-15 close, owner: same words): 505,983 → 498,514**, ceiling → 508,484. Verbatim: gotcha + sessions
   `--before 2026-10-13`/`10-14` (5 entries, 3 session files), H-BB8's row → ledger archive § *Moved 2026-10-15* (pointer
   kept), TODO 0a's history → TODO-archive. Found and repaired: a substring-anchored insert had split the gotcha log's
   intro and hidden 4 entries from `retire_memory.py`. MECHANIZED: the `cp -r` package-import gotcha (`train.py`).
   ▶ **Next levers:** thinning the four 26–30K standing files (`filter-status.md`, `stamp-contract-integrity.md`,
   `nexusmind-data-sources.md`, `oracle-pricing-scheduling.md`) — a rule restated in 3 files is 2 too many.
   ✅ **Round 4 (2026-10-14, owner: "pruning, thinning, mechanizing, retiring"): 524,035 → 503,152**, ceiling → 513,215.
   Verbatim: `retire_memory.py sessions --before 2026-10-12` (3 files) and `gotcha --before 2026-10-12` (4 entries);
   `hypothesis-ledger.md` 51,066 → 43,662 at the move, 43,859 after the H-BB7 ruling (`H-CX3` row + the H-AR prose → archive § *Moved 2026-10-14*, exact
   reconstruction asserted). ▶ **Next levers (no ruling needed for verbatim moves of closed material):** the gotcha log's
   `## Mechanized` "first positives in prose" (~4.5K), `H-HD` prose paragraphs (8K section), and `score-batch-shape-noise.md`
   (25K, standing: backs the #95 Hard Constraint). Thinning is the harder lever: a rule restated in 3 files is 2 too many.
   ✅ **Round 3 (session close 2026-10-12): 549,572 → 514,588**, ceiling → 524,900. Verbatim moves: 6 session files before
   10-09 (`retire_memory.py sessions --before 2026-10-09`); `gpu-server.md` 11,390 → 6,711 (the pre-07-22 ssh-agent saga);
   `prefilter-length-floor-hypotheses.md` 27,832 → 20,683 (step-4 cap verdict and 08-11 re-measure, both closed, with a
   one-line verdict pointer each). The round-2 plan text: `docs/TODO-archive.md` § *Moved 2026-10-12*.
   ✅ **Round 2, part 1 (2026-10-12, later) — within existing rulings: 603,408 → 586,944**, ceiling lowered 611,700 →
   598,700. Verbatim, lossless + mutant 1 each: `hypothesis-ledger.md` 54,673 → 50,075 (closed rows H-CX1, cd-v6
   H1–H3/H5–H7, sol-v6 ×8, H-CTX-2, H-BB2; kept H-CX3, H-CTX-1, H-BV6, H-BB4 — open marker or ruling);
   `session-log.md` 13,906 → 6,018 (`retire_memory.py sessionlog --before 2026-10-01`, the monthly rule);
   `project-obituary-detector.md` 13,173 → 9,195 (retired v3/v4 history, pre-09-01).
   ✅ **Part 2 (owner RULED 2026-10-12, both "yes"): 586,944 → 549,178**, ceiling → 560,200. `working-rules.md` 50,046 →
   ~26K: the 16 SEPTEMBER occurrence stories moved verbatim (exact reconstruction + mutant), each pointer keeps the
   ordinal count (`check_doc_claims.py` rule-ordinals went RED on the first draft, which dropped it — fixed: 21 and 25,
   unchanged). `gotcha-log.md` 64,720 → ~51K: `retire_memory.py gotcha --before 2026-10-09` (second mid-month pass).
   ▶ (superseded by round 4 above; H-CX3 moved 2026-10-14) **Next levers toward 500K (not ruled):** `hypothesis-ledger.md` H-CX3 (6.4K, no closed word — superseded by the
   09-26 `CLAUDE.md` halving?), the gotcha log's `## Mechanized` "first positives in prose" (~4.5K, 09-17), and
   `score-batch-shape-noise.md` (25K, judged standing — backs the #95 Hard Constraint).
   Measured 2026-10-12 at close: **758,893 chars** (+3,086 since 10-10).
   Measured 2026-10-10: **755,807 chars** (`/curate` Step 0's command; all of it in `memory/`, there is no
   `docs/work-items/`). History of the passes so far: `docs/TODO-archive.md` § *Moved 2026-10-10*; posted on #163.
   Every move is VERBATIM to `memory/archive/` with a lossless check (`sort | comm`, C locale; a one-line mutant must
   report 1). Biggest lever first:
   - 0. ✅ **DONE 2026-10-12: the hook transcript replay — 0 regressions.** Corpus: 34 top-level transcripts (5,190 Bash
     commands, 5,073 unique) + 397 subagent ones (4,405 / 4,349), timestamps 2026-09-11 → 2026-10-12. HEAD blocks 6 + 1,
     `caeaa4f` 5 + 1. ONE verdict differs, OLD=None → NEW=pgrep: `pgrep -u nobody \⏎ -f …` (the line-continuation fix,
     already pinned at `tests/unit/test_pattern_kill_hook.py:79`). Of the 7 HEAD blocks, 6 are real invocations (one
     remote, inside `ssh … '…'`) and 1 is a `python3 <<EOF` body (the documented non-cat-heredoc gap). Script: session
     scratchpad, not kept. ⚠️ The corpus holds only 7 positives, so this measures FALSE positives far better than recall.
     ⛔ **But the replay compared VERDICTS, not TIME, and missed a real failure** — the suite's 5 s bound
     (`test_no_catastrophic_backtracking`) was RED at HEAD (2000 × `ssh h ` 8.03 s; `caeaa4f` was already over on
     `watch`, 5.98 s). Cause: rest mode re-read every remainder twice per nesting level. Fixed 2026-10-12 (second
     reading only when it differs): 0.30 s, 106/106, replay unchanged, dropping the second reading is caught.
     Original instruction: **FIRST (owner, 2026-10-10): the hook transcript replay.** Run every real Bash command from this project's
     Claude Code transcripts (`~/.claude/projects/-home-jeroen-repos-veen-systems-llm-distillery/*.jsonl`, the
     `tool_use` inputs where `name == "Bash"`) through `scripts/hooks/block_pattern_kill.py` at `caeaa4f` AND at HEAD
     (`offending()` via importlib; build target names by concatenation so this hook does not refuse the script).
     Print only the commands whose verdict DIFFERS and read each one: NEW=None/OLD=hit is a regression until
     explained. Fix and add a test for each; also report how many commands the corpus held and how many HEAD blocks.
     Local only, no agents. Why: the round-4 fixes (`b090140`) had no review, and each rewrite today lost positives.
   - a. ▶ **The 11 `memory/*-hypotheses.md` files: 261,785 chars (35% of the surface).** First action: per file, list
     the sections/rows whose verdict is closed (SUPPORTED / REFUTED / CLOSED / MOOT) with their bytes, then move them
     under the 09-27 rule the ledger already uses. Largest first: ✅ `corroboration-feature-hypotheses.md` **THINNED 2026-10-12: 78,438 → 7,401 chars**,
     body VERBATIM in `memory/archive/corroboration-feature-hypotheses-archive.md` (`sort | comm` 0 missing, one-line
     mutant 1); surface measured after it: **693,439**. Was: **RULED 2026-10-10: THIN
     it** (supersedes 10-09's "keep"): keep the file and its pointer; rewrite the stale 2026-08-07 summary into a short
     current one (~5–10 KB) naming the three newest dated findings (the gate is the lever, 08-09; production is 79.3%
     sub-threshold artefact, 08-16/17; combining features beats the threshold, 08-17); move every dated section
     VERBATIM to `memory/archive/` (lossless check). Then
     ✅ `prefilter-length-floor-hypotheses.md` **37,478 → 27,832** (2026-10-12: closed entries 1–7, Q9, H-LF1–3 moved
     verbatim to `memory/archive/prefilter-length-floor-hypotheses-archive.md`; open H-L1/H-LF4/Q8/10–12 and the live
     "do not set the cap" decision stay; hypothesis 5's executable verify annotation kept live), ✅ `date-error-recency-boost-hypotheses.md` **33,176 → 16,811** (H-D1/H-D2 RESOLVED + two superseded framings
     moved verbatim),
     ✅ `uplifting-oracle-genre-hypotheses.md` **29,543 → 20,610** (H-UP1/2/3/7/11/12 + H-CV1 sections moved verbatim; the
     table and the owner RULINGS stay). ✅ **2a DONE 2026-10-12 (second pass):** `google-news-corpus` 19,695 → 6,160,
     `violence-promotion-v1` 12,412 → 7,709, `enrichment-delta` 9,306 → 6,270, `solutions-v6-dimension` 7,066 → 4,412.
     **Deliberately NOT moved:** `cd-v6-probe` (a pending cutover; its CORRECTIONS section amends CONFIRMED, so
     splitting them separates a correction from its claim), `obituary-v4` (same coupling: the 2026-09-10 addendum
     amends items 3 and 5), `opinion-genre` (no closed section; its verify annotation greps its own text). The 11
     files: 261,785 → 131,876 chars.
   - b. **The date rule on the reference files** (owner, 2026-10-09: dated before 2026-09-01 moves, unless the class
     recurred since): ✅ `cross-repo-prioritization.md` **37,191 → 16,968** (2026-10-12: the 12 sections whose NEWEST date predates
     09-01 appended verbatim to its existing archive; standing rules, chains 2/4/6/7/12/14 stay). ⚠️ The newest-date proxy
     is UNSAFE for the four below: their pre-09-01 sections are mostly standing traps CLAUDE.md points at — judge each. ✅ `oracle-pricing-scheduling.md` **35,176 → 26,128**
     (V4-card blocks + the superseded/historical ones; all 3 verify checks stay live), ✅ `stamp-contract-integrity.md`
     **34,024 → 28,437** (NM#300 history, the 08-13 single-run measurements, the SUPERSEDED counts; lessons kept in hooks).
     **Judged KEEP, untouched:** `filter-status.md` 29,730 (backs CLAUDE.md's recall/spec table) and
     `nexusmind-data-sources.md` 27,275 (its pre-09-01 sections ARE the traps CLAUDE.md's ⛔ rows point at). 2b done.
   - c. **Mechanize, then retire.** The gotcha log (63,914) keeps 11 catalogue entries only because their classes
     have no `live` row; each new live check lets one move. **RULED 2026-10-10: a RATCHET ceiling on the surface**:
     `check_index_budget.py --target surface` (same command as `/curate` Step 0), ceiling = today's measurement + ~2%,
     LOWERED to the new measurement after each pruning pass; green now, can only tighten. Seed it red first.
     ✅ **Ratchet BUILT 2026-10-12**: `--target surface`, ceiling 611,700 (= 599,709 + 2%); seeded red at 599,000
     (exit 1) first; equals `/curate` Step 0's `wc -m` to the character; 6 tests, 5 mutants each caught; wired as a
     `verify:` line in `memory/MEMORY.md` (runner: 36 blocks). It prints "RATCHET: lower SURFACE_CEILING" once a pass
     leaves > ~4% headroom. ⚠️ `/curate` (user-global skill) still runs its own shell command — same number. Left in
     2c: the gotcha-log catalogue entries (needs a `live` check per class).
     ✅ **Catalogue pass 2026-10-12: 4 of 11 entries moved** (verbatim, to `memory/archive/gotcha-log-archive.md`)
     because their classes went `live` in `## Mechanized`: `pkill -f` (the hook), the 402 (NEW: `score_ollama_oracle.py`
     had no 402 abort and a SystemExit the executor drained past; now a run-fatal flag, 4 tests), the wrong interpreter
     (NEW: `tests/conftest.py` prints a banner), `prepare_data.py` zero examples (NEW: exits 1; also its DOCUMENTED call
     died on `import ground_truth` without PYTHONPATH — fixed). Left (7): their classes are judgement-shaped (wrong
     population, retention, monthly archives, head-N sampling, a self-matching watcher, shared temp dir, mention-is-use).
     ✅ `prepare_data.py` renamed/missing dimension now RAISES (owner 2026-10-14; was a silent column of 0s);
     `tests/unit/test_prepare_data_missing_dimension.py`, mutation-tested (6/10 red on the old code).
   - d. ✅ **2026-10-12: the backlog was ~12 KB, not 25** (the 10-09 pass had moved most). Moved verbatim: 4 boxes
     closed on recorded evidence or duplicated elsewhere, + 4 empty headings. ✅ Both owner calls ruled 2026-10-14: `H-V8-3`
     closed as moot; § *Other Filters* moved verbatim to TODO-archive § *Moved 2026-10-14*.
     Original line: **`docs/TODO.md` below START HERE** (~25 KB of section backlog). Audit each section: close, archive or keep
     (§ *Commerce Prefilter SLM*, § *Prefilter Quality (Apr 2026)*; check against decision 0 and ADR-004 first).

3. **Owner, standing:**
   - H-TV5: one last look at the Thriving tab ~2026-10-06, then close.
   - #156 adverse pool (~$3.2–3.6): DEFERRED. ⚠️ When a lens first CONSUMES `harm_is_subject` (any NexusMind filter
     `config.yaml` naming it), tell the pipeline-atlas session BEFORE it lands: its check goes red on that by design (2026-10-10).
   - Belonging shadow harm cap: a NexusMind change, low priority, v2's before/after instrument.
   - **Host data (#172):** sadalsuud + sadaltager cleaned 2026-10-12; b650 + gpu-server wait for the owner ("stay as they
     are for now"); triage `~/lab/llm-distillery/inbox/` before any cited tree's host copy goes.
   - **#174:** do the oracle vendors' terms allow training on their outputs? Unassessed.

4. **Small, ours** (detail in the archived block's numbered items):
   - **#173:** the experiment protocol is prose; make the registry enforce it.
   - **#172:** the 37-unit lab-manifest evidence backlog (`scripts/verification/lab_manifest_baseline.json`).
   - LD#134 step 3, the marking pass (`docs/decisions/2026-09-17-refcheck-docs-tier.md`).
     **Started 2026-10-09:** the mechanical slice. `--docs-live` 231 → **214** unique, 0 new findings, default scan
     still 0: unqualified sibling paths that exist in exactly ONE sibling got the repo prefix, in 9 live docs. NOT
     touched: `docs/TODO-archive.md` and `docs/CONTRACTS_PLAN-rounds-archive.md` (verbatim archives; their ~20 such
     refs stay), and one command run from inside the NexusMind checkout. The rest is judgement, classified then:
     115 bare basenames, 48 paths found nowhere, 12 collisions, 10 sibling-prefixed but gone, 5 in several siblings.
     ✅ #97 disposition ruled (owner): a counted `<!-- uncommitted: #NNN -->` marker, built and seeded (`85e2845`).
     ✅ **Non-basename pass done 2026-10-09 (owner: "the 75"):** 45 live references dispositioned by hand in 23
     files: placeholder for class names and upstream/private paths, strike for removed/never-committed files,
     repo prefix where the context names the repo. `--docs-live` 214 → **168**, 0 live non-basename findings
     left, default 0, run.sh 47/47 then (48/48 after the close review). Three of my markers were wrong (COVERS NO PATH) and were fixed.
     ▶ **Left:** 118 bare basenames (rule-level question: most are run outputs) and the ~51 findings inside the
     two verbatim archives (`docs/TODO-archive.md`, `docs/CONTRACTS_PLAN-rounds-archive.md`). Those are a TIER
     question, not a marking one: the archives sit in the live tier because they live in `docs/` root.
   - ✅ LD#160 follow-up CLOSED: the nature_recovery v1/v2/v4 tab note was put in English on 2026-10-07 (`fe12a2f`,
     owner ruling); `KNOWN_OPEN` is empty. This line stayed stale until 2026-10-14 and named the Dutch word outside a
     quote, which kept the suite red. Full history: TODO-archive § *Moved 2026-10-10*.
   - LD#134: `--docs-live` is **170** (2026-10-10), 168 at `483c450`: +1 is `filtered_20261009_093632.jsonl` in this
     file's archive copy (a sadalsuud data file), **+1 not yet traced**.
   - Hook: `block_pattern_kill.py` is silently OFF when `CLAUDE_PROJECT_DIR` is unset (settings entry exits 0).
   - ✅ Branch `docs/event-identity-encoder-plan` — **ruled 2026-10-10:** plan posted verbatim on LD#100, branch deleted
     (local + origin; was `0c283c6`).
   - H-MECH-1: watch, 2 batteries left.
   - #158: the heldout detector band (b650).
   - #104 item 1: likely MOOT if gpu-server is retired.

4b. **Oracle model migration (Google notice, 2026-10-08) — NOT urgent, nothing breaks on `gemini-2.5-flash`.** Google will
   reject `thinking_budget` (400) and `temperature`/`top_p`/`top_k` on its UPCOMING models; our call sites send both
   (`ground_truth/batch_scorer.py:805-833`, `scripts/score_ollama_oracle.py:274-277`). ✅ **Retirement date checked
   2026-10-09: NONE announced.** Gemini API deprecations page (ai.google.dev/gemini-api/docs/deprecations, "Last
   updated 2026-10-09 UTC"): `gemini-2.5-flash` "No shutdown date announced"; a listed date would be "the earliest
   possible" one. We call the Gemini API with an API key (`genai.Client(api_key=...)`, `batch_scorer.py:606`), not
   Vertex, so the Vertex/Enterprise retirement date a search summary quoted (2026-10-20, not opened) does not apply.
   ⚠️ **The nearer risk is ACCESS, not retirement**: changelog 2026-09-18, "we are limiting access to the 2.5 models
   to users who have actively used them in the past ... not deprecated and will continue to be served until further
   notice". Unknown whether that is per key, project or account: a NEW key or project may be refused. ✅ **Access confirmed 2026-10-19**: belonging's
   canary runs (EXP-053, 9 runs of 100 + L1) were served `gemini-2.5-flash`. ▶ Trigger now: a dated shutdown on that page, or a refusal. When migrating: `thinking_budget=0` is the cost lever (~80% of
   output tokens per the code comment) and `thinking_level="minimal"` is not known to equal it — measure $/article NAMING THE
   PROMPT; dropping `temperature=0.3` plus a new model = a new oracle, calibrate against the current one first (ADR-010).

5. **NexusMind's, nothing of ours:**
   - NexusMind#395: step 1 LIVE on sadaltager since 2026-09-29.
   - ⚠️ **gpu-server answers SSH again** (2026-10-02 07:03, `up 99 days`): it never went down; the
     2026-09-28 "outage" was reachability. Tell the owner and the NexusMind session before they decide anything
     on "gpu-server is gone" (#104 item 1, orphan dirs).
   - NM#286 item 3 (PR #561): its outcome check.
   - ADR-024 steps 4–5.
   - NexusMind#558 (OOM).

**Cloud pilots: STOPPED by the owner 2026-09-29.** Do not start one without the owner.
---

## Backlog sections — MOVED 2026-10-09 to `docs/TODO-archive.md` (read surface, #163 item e)

*Moved VERBATIM, not re-verified: Commerce Prefilter SLM, Training Pipeline, Score Calibration, Hybrid Inference, Energy-Efficient
Inference, Deployment, Infrastructure, Post-#52 followups, Prefilter Quality, Cross-Filter Normalization, Documentation. Their
open boxes: `grep -n '^- \[ \]' docs/TODO-archive.md` under § *Moved 2026-10-09*. Commerce v1 0.990 is LIVE and verified
(NM#527); its open retrain/multilingual boxes are there.*

## Filters

*The `[x]` history that stood here (Production Ready, In Active Development, Active Learning In Progress) moved
VERBATIM to `docs/TODO-archive.md` § *Moved 2026-10-02 (afternoon): § Filters history* (read surface, #163 item e).
Current filter state lives in `memory/filter-status.md` and the `CLAUDE.md` table.*

### Parked Ideas

- [ ] **Measuring "true AI adoption" in SMEs and larger companies** - PARKED 2026-08-11 by Jeroen ("interesting, park it as an idea"). Owner side question. **Answer: not as asked** — our corpus is articles, adoption happens at firms, so it measures adoption *discourse*, not adoption. SMEs are ~99% of firms and ~0% of coverage; 25.7% of the corpus is GN headline stubs; no firm-level ground truth to validate against. **What it WOULD answer well:** of AI-adoption claims in the press, what share are concrete deployments vs announcements — the `solutions v6` shape, whose tech/hybrid tiebreak already makes that discrimination. **The pivot that reaches the literal question: job postings** (firm-level, size-linkable, exists for SMEs; needs a FluxusSource vacancies feed). **Cheap first probe with a kill criterion: base-rate screen of the existing corpus, ~1h, no oracle spend — if AI-adoption content is a fraction of a percent, stop.** Precedent for that kill: `solutions v6`'s `community_practice_strength` is a sourcing problem, not a modelling one. Full note in **`docs/ideas/ai-adoption-measurement.md`**. Re-check #103 (DeepSeek price rise) before any oracle spend.

- [ ] **Re-enchantment outlets (wonder lens / standalone digests)** - PARKED 2026-07-16 by Jeroen ("some other time"). Byung-Chul Han-inspired exploration: wonder/mystery/myth as lens or standalone oracle-only outlet (no distillation needed at digest scale, ~$6.50/wk). Six ideas + four cheap probe plans (<$3 total: Residue query $0 → Wonder probe ~$0.50 → form-scoring feasibility ~$1-2 → Ledger design note $0) with kill criteria in **`docs/ideas/re-enchantment-outlets.md`**. Hard constraint if resumed: "unexplained" needs an `epistemic_honesty` gatekeeper (misinformation magnet otherwise). Below solutions v4 (#43) and the #62 check in priority.

## ☐ Open threads inside ARCHIVED ledger rows (2026-09-27 retire; rows in `memory/archive/hypothesis-ledger-archive.md`)
- [x] `H-V8-3`: the reorder's multiplicity question "is still open": no pre-registered family was ever run. v8 is superseded by v9, so likely moot; close it or run it. **CLOSED 2026-10-14 (owner): moot, v8 is retired.**
- [x] `H-V8-26`: its revisit trigger is a ~50-article hand-audit of v8's reader-facing precision; no audit record was found (review 2026-09-27). Moot now that v9 is live? Owner call. **CLOSED 2026-10-01 (owner): moot — v8 no longer serves readers; the live question is `H-TV5`.**

## ☐ Unchecked boxes carried out of the archived sections (2026-09-24)

*Copied mechanically from `docs/TODO-archive.md`: every `- [ ]` line in a moved section, under
that section's heading. ⚠️ **Not re-verified** — many are probably done or overtaken; the
queue is ▶ START HERE, not this list. Close or delete a line once checked against its section.*


*2026-10-12 (item 2d): moved VERBATIM to `docs/TODO-archive.md` § *Moved 2026-10-12*: the done language-rule box; the solutions short-content cap and its GN-share re-measure gate (superseded by the recorded verdict "do not set `short_content.cap`", 2026-08-08/11, `memory/prefilter-length-floor-hypotheses.md`); the summariser fixed-budget question (open there as Q12); NM#286 item 3 (tracked in START HERE item 5); and four headings left with no boxes.*

**From:** 2026-08-08 — the checks failed, the analysis didn't
- [ ] **Loose thread:** eval-arm articles cluster at **9.4–9.99** on uplifting and
- [ ] Promote `content_length` to `required` in Contract B **only after** the

**From:** 2026-08-07 (night) — the dedup question answered by mechanism, and a deadline in trouble
- [ ] **Remediate the 30 already-published rows** — reader-facing, ovr.news side,
- [ ] **Check the Zimbabwe funeral row against the obituary gate** (enforcement is

**From:** 2026-08-05 — TDM / training-data position, and the two carve-outs it leaves open
- [ ] **The `tdm_opt_outs.json` scan is unscheduled.** It has run exactly once (2026-08-04). A reservation added tomorrow is invisible. Quarterly is enough for a signal that moves this slowly — the implementation sketch in #28 is retained there as the thing to build **if this decision is ever reversed**, not as work to do now.

**From:** 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

**From:** 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) **The rename half is CLOSED as of 2026-08-06 — do not re-open it here.** ADR-012 amended: `cultural_discovery` and `nature_recovery` KEEP their names (their Hub repos are public standalone artefacts; `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about), `solutions` confirmed as-is, and `uplifting` → **`human_thriving`** at v8 — not bare `thriving`, which is an existing parked directory. What remains under #90 is the template half only.
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question). **RULED 2026-10-01 (owner): keep, rescoped to NORMALIZATION FRESHNESS only (the prefilter half died with decision 0); later, after belonging v2.**
