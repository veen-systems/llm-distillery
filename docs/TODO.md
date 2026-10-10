# LLM Distillery - TODO

## ▶️ START HERE — the ordered queue, as of 2026-10-10 (session close)

*A bare "continue" means this list, top down. Each line names the FIRST action. Item 0 is WAITING (dated), item 1 is
NexusMind's, so a bare "continue" before 2026-10-23 starts at **item 2, step 0** (the hook replay), then 2a.*

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

2. **THE READ SURFACE (#163) — ▶ a bare "continue" starts HERE. Owner, 2026-10-10: "prune, thin, mechanize, retire".**
   Measured 2026-10-10: **755,807 chars** (`/curate` Step 0's command; all of it in `memory/`, there is no
   `docs/work-items/`). History of the passes so far: `docs/TODO-archive.md` § *Moved 2026-10-10*; posted on #163.
   Every move is VERBATIM to `memory/archive/` with a lossless check (`sort | comm`, C locale; a one-line mutant must
   report 1). Biggest lever first:
   - 0. ▶ **FIRST (owner, 2026-10-10): the hook transcript replay.** Run every real Bash command from this project's
     Claude Code transcripts (`~/.claude/projects/-home-jeroen-repos-veen-systems-llm-distillery/*.jsonl`, the
     `tool_use` inputs where `name == "Bash"`) through `scripts/hooks/block_pattern_kill.py` at `caeaa4f` AND at HEAD
     (`offending()` via importlib; build target names by concatenation so this hook does not refuse the script).
     Print only the commands whose verdict DIFFERS and read each one: NEW=None/OLD=hit is a regression until
     explained. Fix and add a test for each; also report how many commands the corpus held and how many HEAD blocks.
     Local only, no agents. Why: the round-4 fixes (`b090140`) had no review, and each rewrite today lost positives.
   - a. ▶ **The 11 `memory/*-hypotheses.md` files: 261,785 chars (35% of the surface).** First action: per file, list
     the sections/rows whose verdict is closed (SUPPORTED / REFUTED / CLOSED / MOOT) with their bytes, then move them
     under the 09-27 rule the ledger already uses. Largest first: `corroboration-feature-hypotheses.md` 78,438 — **RULED 2026-10-10: THIN
     it** (supersedes 10-09's "keep"): keep the file and its pointer; rewrite the stale 2026-08-07 summary into a short
     current one (~5–10 KB) naming the three newest dated findings (the gate is the lever, 08-09; production is 79.3%
     sub-threshold artefact, 08-16/17; combining features beats the threshold, 08-17); move every dated section
     VERBATIM to `memory/archive/` (lossless check). Then
     `prefilter-length-floor-hypotheses.md` 37,478, `date-error-recency-boost-hypotheses.md` 33,176,
     `uplifting-oracle-genre-hypotheses.md` 29,543.
   - b. **The date rule on the reference files** (owner, 2026-10-09: dated before 2026-09-01 moves, unless the class
     recurred since): `cross-repo-prioritization.md` 37,191, `oracle-pricing-scheduling.md` 35,176,
     `stamp-contract-integrity.md` 34,024, `filter-status.md` 29,730, `nexusmind-data-sources.md` 27,275.
   - c. **Mechanize, then retire.** The gotcha log (63,914) keeps 11 catalogue entries only because their classes
     have no `live` row; each new live check lets one move. **RULED 2026-10-10: a RATCHET ceiling on the surface**:
     `check_index_budget.py --target surface` (same command as `/curate` Step 0), ceiling = today's measurement + ~2%,
     LOWERED to the new measurement after each pruning pass; green now, can only tighten. Seed it red first.
   - d. **`docs/TODO.md` below START HERE** (~25 KB of section backlog). Audit each section: close, archive or keep
     (§ *Commerce Prefilter SLM*, § *Prefilter Quality (Apr 2026)*; check against decision 0 and ADR-004 first).

3. **Owner, standing:**
   - H-TV5: one last look at the Thriving tab ~2026-10-06, then close.
   - #156 adverse pool (~$3.2–3.6): DEFERRED. ⚠️ When a lens first CONSUMES `harm_is_subject` (any NexusMind filter
     `config.yaml` naming it), tell the pipeline-atlas session BEFORE it lands: its check goes red on that by design (2026-10-10).
   - Belonging shadow harm cap: a NexusMind change, low priority, v2's before/after instrument.
   - **Belonging single-person stories (H-BB6, 2026-10-10):** owner: the top of the page shows "at least half personal stories". Needs the
     owner's bar ("a few" = ≤ k of the top N), then the top-of-page composition check (`experiments/README.md` § *Protocol*).
     First, free: which positives c2a (EXP-046) missed. Evidence `docs/evidence/2026-10-10-belonging-v3-top-of-page/`.
   - **Host data (situla = source of truth, 2026-10-10):** triage `~/ld-lab/inbox/` FIRST (a cited tree can only be
     re-pulled while the host copy exists), then the owner's per-item go to delete host copies, only after a restic
     snapshot holds them. List: `docs/evidence/2026-10-10-host-data-inventory/README.md`.

4. **Small, ours** (detail in the archived block's numbered items):
   - Enforce the experiment protocol (`experiments/README.md` § *Protocol*, 2026-10-10): it is prose today. Add a
     `reader_visible` field plus composition / live-check artifacts to the registry schema and make
     `check_experiment_registry.py` fail a reader-visible decision without them.
   - The lab-manifest evidence backlog (`check_lab_manifests.py` BACKLOG lines, frozen in
     `scripts/verification/lab_manifest_baseline.json`): cite what was pulled, shrink the baseline, mark the rest lost.
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
   - ✅ LD#160 follow-up still OPEN (owner call): `filters/nature_recovery/{v1,v2,v4}/config.yaml` carry `ovr.news
     'Herstel' tab` in a notes string; v4 is DEPLOYED (editing changes a live package's bytes at the next sync).
     Listed as KNOWN OPEN in `check_framework_language.py`. Full history: TODO-archive § *Moved 2026-10-10*.
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
