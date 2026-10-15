# LLM Distillery - TODO

## ▶️ START HERE — the ordered queue, as of 2026-10-14

*A bare "continue" means this list, top down. Each line names the FIRST action. Item 0 is WAITING (dated, ≥ 10-23/24),
item 0a waits on ovr.news shipping the ranking the owner ruled on 2026-10-14; its offline replay on H can run meanwhile.
Item 1 is NexusMind's. Item 2 (#163, the read surface): round 4 on 2026-10-14 took it to the figure in item 2;
keep pruning (owner 2026-10-14: "pruning, thinning, mechanizing, retiring").*

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
   history up to 2026-10-14: TODO-archive § *Moved 2026-10-14*. State: v3 fails on the owner's one count (10/30, 10-12);
   qwen (a floor) counts 4 / 8 / 5 on 10-11 / 10-12 / 10-13 on the CURRENT ranking (`docs/evidence/2026-10-13-belonging-daily-baseline/`);
   candidate c2c FAILED its recall guard (EXP-048, with a build defect: H-BB8).
   - ✅ **H is LIVE (ducroq/ovr.news#391):** ovr.news commit `07cdb7e0`, first production H build 2026-10-15 ~07:39Z
     (Cloudflare Pages `bab11cb7`), per ovr-news-47; settings `ranking.freshSlots=5, freshSlotHours=24,
     ageBandEdgesHours=[72,168]` (`src/lib/config.ts`). Their check: the live page's first 8 cards match H locally;
     Belonging top 30 = 6/24/0 (< 24 h / 1–3 d / older). Latent gap: page-level filters (short summary, NL without a
     Dutch translation) run AFTER the fresh slots, so fewer than 5 fresh cards can lead (0 cards today).
     pipeline-atlas: filed by ovr-news-47 as veen-systems/pipeline-atlas#170 (commit, build time, settings, the stale
     Stage 9/10 lines); confirmed open 2026-10-15.
   - ▶ **NOW RUNNING (from 2026-10-15): re-baseline v3 on the LIVE H page**, 7 daily builds 10-15 → 10-21, read
     ≥ 2026-10-22. ⏰ **Owner OK'd 2026-10-15: a user crontab line on situla** saves the five lens pages
     (`https://ovr.news/en/{belonging,thriving,solutions,discovery,recovery}/`) daily at 16:30 local to
     `~/ld-lab/inbox/ovr-lens-pages/<lens>_<UTC>.html`. Extended the same day (owner: all five lenses, until 2026-11-15)
     so it also serves LENS ASSIGNMENT (H-LA2, "narrow lens first", tested only vs judges, never vs the owner; the owner
     keeps wondering about tabs). First files 2026-10-15T0750Z (Belonging only) and T0755Z (all five); the first H build
     was 07:40:42Z. 16:30 local is 14:30Z until 10-24, 15:30Z from 10-25 (CET); the Belonging re-baseline (10-15..10-21)
     is unaffected. Date guard: inert from 2026-11-16 (UTC). ⛔ **Then REMOVE it** (`crontab -r`; it is the only line).
     Pre-register the on-site count BEFORE reading any page's tags; move files into a lab `experiments/` tree
     (`lab.py move`) before citing them. The qwen count per day (b650, $0; reuse
     `count.py` / `select_v3.py`, add the H order from `replay.py` `order("H hybrid")`), report the weekly mean and the
     worst day. Pre-register it first.
     ✅ **Offline replay DONE 2026-10-15 (EXP-049, `docs/evidence/2026-10-15-belonging-h-replay/`):** qwen floor, 5
     in-range builds. Primary (as pre-registered): H 4.80 vs control 5.60, both undetermined under the pre-registered
     rule (a floor mean ≤ 6 cannot pass). Review refuted the sticky-removal rule; the post-hoc DATED variant
     reproduces the 10-13 baseline 30/30 and gives H 5.20, **control 6.40: the current ranking fails the bar even on
     the floor** (post hoc). Use the dated builds as c2d's H instrument (`--dated` on `build_population.py` /
     `select_v3.py` / `count.py`). The on-site re-baseline above still runs once H ships.
   - **Then (owner RULED 2026-10-14: "prepare now, judge on H"):** c2d, a cap-aware retry (scale the five non-gatekeeper dimensions so community_fabric stays ≥ 3.0; assert
     each changed row's EFFECTIVE score is 4.4; same seeds), judged on the same weekly H instrument. $0 oracle. Pre-register c2d, train on b650 (2 seeds), replay
     v3 and c2d on H over the same 7 days; don't wait for ovr.news to ship H.
   - Over 6 is the case for the next candidate, NOT an automatic rollback (v3's rollback rule predates the bar; owner's call).
   - Lab: the 10-10 `~/ld-lab/inbox/` heap (37 backlog citations) is still a later pass (#172, item 00 archived 2026-10-14).

1. **Decision-0 sync to NexusMind** — ONE NexusMind commit. The sequence is in the archived block (item 1):
   - dry-run diff first
   - copy `filters/common/{filter_base_scorer,hybrid_scorer,cli}.py` together with every live package, deleting their `prefilter.py`
   - retarget NM's `test_prefilter.py` / `test_shared_infrastructure.py`
   - run the NM unit suite
   - ⚠️ since NexusMind#395 step 1, sadalsuud no longer auto-pulls: a **manual pull + scorer-image rebuild** is needed
   NexusMind's session runs it; ours is to tell them. LD#52 and LD#86 are closed.

2. **THE READ SURFACE (#163). "prune, thin, mechanize, retire".** Rounds 1–3 landed 2026-10-12: 758,893 → 514,588 chars (519,680 at close, after the session's new records).
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
     are for now"); triage `~/ld-lab/inbox/` before any cited tree's host copy goes.
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
   notice". Unknown whether that is per key, project or account: a NEW key or project may be refused. Our last
   Gemini calls were 2026-10-07/08 (belonging). ▶ Trigger now: a dated shutdown on that page, or a refusal. When migrating: `thinking_budget=0` is the cost lever (~80% of
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
