# LLM Distillery - TODO

## ▶️ START HERE — the ordered queue, as of 2026-10-09 (session close)

*A bare "continue" means this list, top down. Each line names the FIRST action. Item 0 is WAITING (dated) and items
2b/4b are done, so a bare "continue" before 2026-10-23 starts at item 2 (the read surface, ▶ lines).*

⏭ **FIRST, finish the 2026-10-09 close** (cut off by a usage limit, resumed the same day). ✅ Done: round 2's 3
warnings fixed, and a round 3 run on the fixes (adversarial, guarantee+doc, reachability+claims): 1 BLOCKER (the round-2
hook regex backtracked exponentially: 13 s on 25 × `ssh h `) + 4 warnings, all fixed. The hook is now a `shlex`
TOKENIZER (`scripts/hooks/block_pattern_kill.py`), not a regex; guard D and `check_adapter_matches_hub.py` refuse an
empty/stub (< 1 MB) adapter before hashing, so they never advise re-uploading one; the CLI checks a missing adapter
before `NO_HUB` and says NO PACKAGE for a missing version dir. Suite 1374 passed / 24 skipped (`.venv/bin/python`).
⚠️ **The tokenizer rewrite has had NO independent review** (the two-round cap was already spent; round 3 ran because
round 2 found the stub class again). Tests: 83 in its file, 6 mutants caught, the round-2 regex seeded red, 60,000
fuzz inputs with 0 exceptions. Owner: one fresh adversarial pass on that file alone, or accept. Still open from the
close: `/curate` (session file, index rotation), progress posts on LD#163 (the read surface: ~64.6 KB moved today,
not 108) and LD#134 (refcheck docs tier: docs-live 231 → 168, new uncommitted marker), the review-profile suite
baseline line (now 1374 / 24). Small: the hook is silently off when `CLAUDE_PROJECT_DIR` is unset.

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
   - Open, not blocking: single-person stories (owner unsure); FM-S1 judge strictness; harvest round 2 (~$9.70 est.).
   ⛔ **Never name the curator** in this repo or on GitHub (guards: `.githooks/`, gitignored `config/credentials/forbidden_names.txt`).

1. **Decision-0 sync to NexusMind** — ONE NexusMind commit. The sequence is in the archived block (item 1):
   - dry-run diff first
   - copy `filters/common/{filter_base_scorer,hybrid_scorer,cli}.py` together with every live package, deleting their `prefilter.py`
   - retarget NM's `test_prefilter.py` / `test_shared_infrastructure.py`
   - run the NM unit suite
   - ⚠️ since NexusMind#395 step 1, sadalsuud no longer auto-pulls: a **manual pull + scorer-image rebuild** is needed
   NexusMind's session runs it; ours is to tell them. LD#52 and LD#86 are closed.

2. **THE READ SURFACE (#163) — owner: "prune, thin, mechanize, retire".**
   - **Done 2026-10-02:**
     - 2a: six dated entries moved out from under the gotcha-log template heading, verbatim (103.2 → 92.1 KB).
     - The START HERE block went 19.1 KB → this one.
     - Default refcheck 1 → 0 (a moot recall-cost hypothesis was marked).
     - Afternoon: § *Filters* `[x]` history moved verbatim to `docs/TODO-archive.md` (TODO 37.4 → 33.0 KB). Read surface
       measured at 908,775 chars (`/curate` Step 0's command).
   - **Done 2026-10-02 (evening):** `memory/session-log.md` rotated, 153 KB → 70 KB. Entries before 2026-09-01 and the
     frozen appendix moved VERBATIM to `memory/archive/session-log-2026-08-and-appendix.md` (0 lines lost, checked).
     Read surface: **911,068 → 838,699 chars** (`/curate` Step 0's command).
   - **Open, in order:**
     - c. **The unreachable-mechanism catalogue** (55 dated `###` entries).
       - **Keep-rule CHANGED (owner, 2026-10-02):** an entry whose class has a `live` row in § *Mechanized* moves
         VERBATIM to `memory/archive/`.
       - **Measured 2026-10-02:** 0 of the 55 entries NAME a live check, so this needs a per-entry judgement of which
         live check covers each class.
       - **Done 2026-10-09: the per-entry pass covers 1 of 55.** Moved verbatim: *THE COMMIT GUARD CANNOT READ
         NEGATION* (2026-08-28), covered by the 2026-09-29 negation row (`tests/unit/test_commit_msg_hook.py`, 101
         passed; it tests both gaps the entry names). Lossless check: 13 lines removed, 0 missing (`sort | comm`, C locale; a
         mutant dropping one line reported 1). Log 107,340 → 106,233 B. The other 54 have no `live` row: their fixes
         are prose rules, one-script fixes or tests without a Mechanized row (e.g. the 402 abort, `prepare_data.py` 0
         examples). Closest misses: the `|`-in-table entry (the `/review-changes` structural pre-check catches it but has
         no row), *mention is use* (the guard deliberately still counts mention). ⚠️ **This keep-rule cannot shrink the
         catalogue.** Shrinking it needs either new `live` rows (mechanize first) or a different rule. That is the owner's call.
       - ✅ **Ruled and done 2026-10-09 (owner): date rule + recent repeats.** Entries dated before 2026-09-01 move
         verbatim, except classes that recurred on/after 2026-09-01. **43 moved** (47.6 KB; log 106,233 → 59,745 B as committed in `d742873` (58,949 before the Mechanized row; 61,817 B after `235b1a1`); 625
         lines removed, 0 missing, mutant → 1). **11 stay**: 6 dated 09-01/02, plus pkill -f (10-02), the pgrep watcher
         (same class), the wrong interpreter (09-28), "aged out of retention" (recurred 10-07 as "source files expired"),
         the wrong-population precision bar (recurred 10-09 as the trigger comparing two populations).
       - ✅ **Owner also ruled: mechanize the top recurring class.** `scripts/hooks/block_pattern_kill.py`, a PreToolUse
         hook in the new `.claude/settings.json`, refuses `pkill -f` / `pgrep -f` in command position. Live row in
         § *Mechanized*. Undo: delete `.claude/settings.json`.
     - d. **2026-10-09:** the hypothesis ledger got the 09-27 rule again: 5 closed rows (H-HD16, H-BV4, H-BV9, H-BV11,
       H-BB1) moved verbatim, 56,148 → 53,622 B, 0 lines missing. Kept: H-JO1 (partial), H-BB4 (⚠️), H-BB2 / H-BV6
       (verdict word outside the rule). `corroboration-feature-hypotheses.md` and `working-rules.md` have NO closed rows,
       so any cut there is an owner call (asked 2026-10-09).
       - ✅ **Ruled + done 2026-10-09.** Corroboration: kept, marked DORMANT with a stale-summary warning (owner). 
         Working rules: rules and occurrence counts stay live; pre-2026-09-01 occurrence stories moved verbatim to
         `memory/archive/working-rules-archive.md` (4 blocks: source-excludes 4–15, name-the-caller 9–16, pgrep 4–6,
         the 08-15/16 population recurrences). 65,110 → 50,641 B (estimate was 35–40 KB off; measured 14.5 KB, because
         most of the largest bullet is September stories). Reconstructed byte-for-byte from the files on disk vs HEAD;
         a one-word mutant fails. The pgrep block carries a pre-existing duplicated fragment, kept as found.
     - d. ✅ session-log rotated (above); corroboration, working-rules and the ledger handled 2026-10-09 (above).
     - e. **`docs/TODO.md` below START HERE** (~31 KB of section backlog). Audit each section: close, archive or
       keep. Example: § *Commerce Prefilter SLM* and § *Prefilter Quality (Apr 2026)*. Check them against
       decision 0 and ADR-004 before touching them.

2b. **Rewrite `docs/RUNBOOK.md` § Deployment for NexusMind's image path (NM#395).** Production scores from a container image
   built by NexusMind (stage.py, docker build, restart, manual sadalsuud pull); our `deploy_to_nexusmind.sh` still probes
   gpu-server. belonging v3 went in by hand (NM 4901fb5). ⚠️ When it lands, TELL pipeline-atlas first: its verify greps the
   script's gpu-server probe and goes red (pipeline-atlas PR #122).
   - ✅ **RUNBOOK half done 2026-10-09:** § Deployment rewritten. Steps 1–3 are ours, step 4 is NexusMind's hand-off
     (image build, container swap keeping the previous one, manual sadalsuud pull, rollback = kept image + revert),
     and step 5 verifies from the output: both commands were run on sadalsuud, 4,812/4,812 rows of `filtered_20261009_093632.jsonl` `3.0`,
     `revision_match: true`, scorer `hcl-ct102` (the host varies per cycle, NexusMind#591). New
     `scripts/deployment/check_adapter_matches_hub.py` (6 tests, 2 mutants caught). ⛔ **Its first version derived the Hub repo from the directory name and 404'd for
     cultural_discovery, human_thriving and nature_recovery; my "live" check had used only belonging. Fixed at close
     (review): repo id from `inference_hub.py`, all six live filters checked against the real Hub.**
   - ✅ **SCRIPT half done 2026-10-09** (pipeline-atlas told first; they said go: their verify greps the old
     `--weights-preplaced` help text and turning red is expected). Guard D now compares this checkout's adapter
     with its Hub copy (fails closed when it cannot ask, skips `NO_HUB`); no ssh left in the deploy path.
     `--weights-preplaced` survives with the new meaning. Guard C's rollback advice no longer says "remove vN".
     FILTER_PLAYBOOK checklist items 5/7 and the chain line updated (item 7 said "rollback = delete the new dir").
     Live run: belonging v3 → MATCH, uplifting v7 → NO_HUB skip, both exit 0. 5 mutants caught.
     ✅ **pipeline-atlas messaged 2026-10-09 with `3e6244f` on origin** (was: owed: message pipeline-atlas with the pushed commit) (they need (a) the commit on origin, (b) the flag
     survives, (c) no ssh, (d) local adapter vs the Hub RECORD only — never what a scorer host serves).

3. **Owner, standing:**
   - H-TV5: one last look at the Thriving tab ~2026-10-06, then close.
   - #156 adverse pool (~$3.2–3.6): DEFERRED.
   - Belonging shadow harm cap: a NexusMind change, low priority, v2's before/after instrument.

4. **Small, ours** (detail in the archived block's numbered items):
   - ✅ `cultural_discovery v5` `raw_min` 4.0006 vs 4.0 — **closed 2026-10-07, no change:** a pre-anchor legacy fit
     (2026-07-10; the fitter anchors raw_min to the op-point since 07-16). The tolerance IS recorded:
     `OP_POINT_EPS = 0.01` (`scripts/normalization/fit_normalization.py`), enforced by
     `tests/unit/test_normalization_invariant.py` (passes). Effect: raw in [4.0, 4.0006) normalizes to percentile 0.
     A refit would be a NexusMind deploy for a 0.0006-wide band. `test_normalization_op_point.py` reads only
     `base_scorer.py`, which is why it never saw this.
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
   - ✅ The retracted 19.9%/13.0% framing — **closed 2026-10-07:** already gone from `CLAUDE.md`; the 3 remaining copies
     (`docs/HUMAN_THRIVING_V8_PLAN.md`, `memory/cross-repo-prioritization.md` ×2) now carry the retraction beside them.
   - ✅ LD#160 **done 2026-10-07** as ruled: ADR-009 dated note (no rewrite); `cross_filter_landscape.py` renamed to
     English; `scripts/verification/check_framework_language.py` built and shown RED first (exit 1, 64 violations,
     all in that script), green after (`tests/unit/test_framework_language.py` seeds the class). ⚠️ **LD#160 follow-up
     (owner call):** the checker found a site nobody had listed: `filters/nature_recovery/{v1,v2,v4}/config.yaml`
     carry `ovr.news 'Herstel' tab` in a notes string. v4 is DEPLOYED, so editing it changes a live package's bytes at
     the next NexusMind sync. Listed as KNOWN OPEN in the checker until ruled.
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

### Other Filters
- [ ] ~~**future-of-education**~~ - DROPPED: education stories land naturally in Breakthroughs (research)
- [ ] **ai-engineering-practice v2** - Ready for oracle scoring (not ovr.news, separate product)
  - FluxusSource hardware sources active (1,193 articles)
  - Prompt calibration complete (~60% tier accuracy)
- [ ] **seece** - Corporate excellence (not ovr.news)
- [ ] **sustainability_economic_viability** - Sustainability sub-dimension (not ovr.news)
- [ ] **sustainability_policy_effectiveness** - Sustainability sub-dimension (not ovr.news)

### Parked Ideas

- [ ] **Measuring "true AI adoption" in SMEs and larger companies** - PARKED 2026-08-11 by Jeroen ("interesting, park it as an idea"). Owner side question. **Answer: not as asked** — our corpus is articles, adoption happens at firms, so it measures adoption *discourse*, not adoption. SMEs are ~99% of firms and ~0% of coverage; 25.7% of the corpus is GN headline stubs; no firm-level ground truth to validate against. **What it WOULD answer well:** of AI-adoption claims in the press, what share are concrete deployments vs announcements — the `solutions v6` shape, whose tech/hybrid tiebreak already makes that discrimination. **The pivot that reaches the literal question: job postings** (firm-level, size-linkable, exists for SMEs; needs a FluxusSource vacancies feed). **Cheap first probe with a kill criterion: base-rate screen of the existing corpus, ~1h, no oracle spend — if AI-adoption content is a fraction of a percent, stop.** Precedent for that kill: `solutions v6`'s `community_practice_strength` is a sourcing problem, not a modelling one. Full note in **`docs/ideas/ai-adoption-measurement.md`**. Re-check #103 (DeepSeek price rise) before any oracle spend.

- [ ] **Re-enchantment outlets (wonder lens / standalone digests)** - PARKED 2026-07-16 by Jeroen ("some other time"). Byung-Chul Han-inspired exploration: wonder/mystery/myth as lens or standalone oracle-only outlet (no distillation needed at digest scale, ~$6.50/wk). Six ideas + four cheap probe plans (<$3 total: Residue query $0 → Wonder probe ~$0.50 → form-scoring feasibility ~$1-2 → Ledger design note $0) with kill criteria in **`docs/ideas/re-enchantment-outlets.md`**. Hard constraint if resumed: "unexplained" needs an `epistemic_honesty` gatekeeper (misinformation magnet otherwise). Below solutions v4 (#43) and the #62 check in priority.

## ☐ Open threads inside ARCHIVED ledger rows (2026-09-27 retire; rows in `memory/archive/hypothesis-ledger-archive.md`)
- [ ] `H-V8-3`: the reorder's multiplicity question "is still open": no pre-registered family was ever run. v8 is superseded by v9, so likely moot; close it or run it.
- [x] `H-V8-26`: its revisit trigger is a ~50-article hand-audit of v8's reader-facing precision; no audit record was found (review 2026-09-27). Moot now that v9 is live? Owner call. **CLOSED 2026-10-01 (owner): moot — v8 no longer serves readers; the live question is `H-TV5`.**

## ☐ Unchecked boxes carried out of the archived sections (2026-09-24)

*Copied mechanically from `docs/TODO-archive.md`: every `- [ ]` line in a moved section, under
that section's heading. ⚠️ **Not re-verified** — many are probably done or overtaken; the
queue is ▶ START HERE, not this list. Close or delete a line once checked against its section.*


**From:** 🔵 PREVIOUS SESSION — **ADR-013 widened to all framework text; review found my own evidence unsound and the compliance zero FALSE. Framework 6 releases behind, s
- [x] **Mechanize the language rule (#160)** — done 2026-10-07: `scripts/verification/check_framework_language.py`
  (names in framework text; commit messages still unread). See START HERE item 4.

**From:** 2026-08-09 — corroboration: the shippable change was refuted, the gate is the lever

**From:** 2026-08-08 (afternoon) — proven by outcome, and a self-inflicted outage
- [ ] Re-measure gated on **measured GN-URL share per cycle**, not on "migration

**From:** 2026-08-08 — the checks failed, the analysis didn't
- [ ] **Loose thread:** eval-arm articles cluster at **9.4–9.99** on uplifting and
- [ ] Promote `content_length` to `required` in Contract B **only after** the

**From:** 2026-08-07 (night) — the dedup question answered by mechanism, and a deadline in trouble
- [ ] **Remediate the 30 already-published rows** — reader-facing, ovr.news side,
- [ ] **Check the Zimbabwe funeral row against the obituary gate** (enforcement is

**From:** 2026-08-07 (late) — coverage pass, a refuted plan, one instrument shipped

**From:** 2026-08-06 evening — four owner decisions taken, three backlogs closed

**From:** 2026-08-06 — cd v6 probe (#98), the English escape hatch (#99), and an instrument for FS#120

**From:** 2026-08-05 — TDM / training-data position, and the two carve-outs it leaves open
- [ ] **The `tdm_opt_outs.json` scan is unscheduled.** It has run exactly once (2026-08-04). A reservation added tomorrow is invisible. Quarterly is enough for a signal that moves this slowly — the implementation sketch in #28 is retained there as the thing to build **if this decision is ever reversed**, not as work to do now.

**From:** 2026-08-02 — Chain 4 measured: two of the previous day's own P0 conclusions overturned
- [ ] **Fit the solutions short-content cap** (#93 step 4) — **#92 no longer blocks it; #95 still does.** The second-op-point re-run ran 2026-08-05 and the defect is **identified**: D1 (both arms ≥2.25) −0.790, D2 (≥4.00) −0.861, **D3 (matched percentile depth) −1.119** [−1.61,−0.61], cluster-bootstrap p Holm-corrected 0.0032 / 0.0012 / <1.5e-4. The selection artifact predicted D2 markedly more negative and D3 → 0; D2 moved −0.071 and D3 is the *largest*. A gemini-2.5-flash cross-check on the same D3 sample gives **−1.351** [−1.73,−0.96] — two oracles with clearly different absolute bias, same gap, which rules out "the judge penalises short input". Harness + fixtures committed (`scripts/diagnostics/ld92_*.py`, `tests/fixtures/ld92/`). **Remaining blocker is Batch F.1 (#95)**: the cap value is a threshold fit and inherits the |Δ| ≤ 0.16 batch-composition noise floor. Also weigh the recall cost against NM#231/#292 before setting a value — `gn_africa_*` / `gn_asia_*` feeds lead solutions' short-and-clearing list.
- [ ] **Does the scorer share the summariser's fixed-budget failure? (NEW, ovr#299)** For English sources, summary content words absent from the article *and* title run 31.6% (1000+ chars) → 73.9% (120–299) → **83.4% (<120)**, monotone over 18,756 summaries. The mechanism there is a fixed output length target (medians 1159/968/875/1065 against a 40× input range) that the model fills — compressing an article, generating from a headline. **Open for this repo: whether the student has an analogous behaviour, or whether its short-content error is purely vocabulary-without-subject.** The fixes differ — one is a budget, the other a cap — so this is worth one experiment before building either.
- [ ] **NM#286 item 3** (violence stamping skipped in single-filter / `--no-dedup` / dedup-exception runs). Verified in code; **live blast radius zero today** (production runs multi-filter, violence `enforce: false`), so it is an audit gap, not admitted violence. Still a hard prerequisite for any violence enforce flip, with LD#82.
  - ⛔ **2026-09-28: the premise is gone and the fix is not in.** Violence has ENFORCED since 2026-08-23 (`config/app.yaml` comment on sadalsuud); `_run_violence_promotion_prefilter` still returns with NO stamps when `_article_cache` is empty (read on sadalsuud today), and `_enforce_violence_promotion` fails open. Live multi-filter cycles stamp, so today's exposure is a shared-dedup exception or an ad-hoc single-filter run. `10344 unstamped articles left in place` (the **05:21** enforcement line, not 09:05 as first written) = dedup-removed copies: nexusmind-55 matched it exactly in 3 cycles (1,724 × 6 filters = 10,344; 1,395 × 6 = 8,370; 1,518 × 6 = 9,108), removed afterwards by per-filter cached dedup — arithmetic identity, not an id-level join. Confirmed unfixed at NexusMind HEAD `9dfcf2a`; scheduling is the owner's call in that session, fix = NM#286's plus an outcome check (unstamped SURVIVORS after dedup = 0). NexusMind's code; owner to decide whether to raise it on NM#286.

**From:** 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

**From:** 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) **The rename half is CLOSED as of 2026-08-06 — do not re-open it here.** ADR-012 amended: `cultural_discovery` and `nature_recovery` KEEP their names (their Hub repos are public standalone artefacts; `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about), `solutions` confirmed as-is, and `uplifting` → **`human_thriving`** at v8 — not bare `thriving`, which is an existing parked directory. What remains under #90 is the template half only.
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question). **RULED 2026-10-01 (owner): keep, rescoped to NORMALIZATION FRESHNESS only (the prefilter half died with decision 0); later, after belonging v2.**
