# LLM Distillery - TODO

## 2026-08-08 (afternoon) — proven by outcome, and a self-inflicted outage

Full record: `memory/project_session_2026_08_08.md` (same file, second half).

### ✅ NM#300 + LD#88 — VERIFIED on production rows, both CLOSED

- [x] **`content_length` 100% populated in all six filters** (17:10 cycle), from
      **0 of 50,605**. `stage_used` / `stage1_estimate` likewise 100%.
- [x] **It was FIVE allowlists in series, not two.** The morning's fix corrected
      hops 1 and 5; the 12:03 cycle still read **0 of 2,170** with both fixes
      provably loaded. The three unexamined hops were all on the
      response → result-object boundary (`gpu_client.py` dataclass, its
      construction, `main.py`'s dict conversion). The earlier "verified there is
      no third" checked the *article → disk* seam, which is true and is not where
      the loss was. **Patching the sender proves nothing unless the receiver's
      parser is checked too.**
- [x] **Bonus, unasked**: with `stage_used` on disk for the first time —
      **no surfacing article is ever probe-scored.** `stage1_low` rows peak at raw
      0.75–1.50 against op-points of 2.25/4.0, so `surfacing AND stage1_low` is
      **0** in every filter. The hybrid design's core safety claim, assumed since
      2026-02, measured at last.
- [x] Contract B `content_length` → `required`: **still NO.** Now populated, but
      promote only after it holds across several cycles; rows before
      `filtered_20260808_17*` are absent-or-null forever.

### 🔴 I took the pipeline down, and it was a decision, not a slip

`nexusmind.service` FAILED at 16:07 and would have failed every 4h. Not a crash —
the fail-closed deploy gate refused to ship because
`src/scoring/gpu_client.py.bak_nm300third_20260808` was untracked under a guarded
path. **I had decided ~20 minutes earlier to keep those `.bak` files as a
rollback for an unverified fix**, when the commits were already pushed and git
*was* the rollback. Recovered 16:23; the 16:07 collection was reprocessed, no
data lost, one cycle delayed. Gotcha logged (`0c14de4`) — patch in place and rely
on git, or write backups **outside** the repo.

### ✅ cd v6 — both cutover blockers cleared, NOT deployed

- [x] Hub repo `cultural-discovery-filter-v6` created (private, v5 adapter
      verbatim, md5-identical, OLD PEFT keys, no `resave_adapter.py`).
- [x] `normalization.json` fitted n=3,680, `raw_min` 4.0, from `filter_version=5.0`
      rows **deliberately** — the "needs a historical rescore" framing was
      circular (a rescore needs the Hub repo) and its stated reason applies to the
      firehose, not to the `raw >= 4.0` fit set where the probe blocks 1 of 2,653.
- [x] `--check-hub` **9/9**; loaded end-to-end from its own Hub repo and scored.
- [ ] **The cutover itself** — deferred by owner decision so it doesn't share a
      cycle with NM#300. Then refit normalization from real 6.0 rows, then #87.

### ✅ LD#93 step 4 — sized, then the sizing was withdrawn

- [x] **Verdict: do not set the cap.** A cap ≥ the op-point removes **zero** false
      positives (visibility keys on raw), and nothing short reaches `medium_high`
      (max 4.93), so its stated purpose is already met and any cap ≥ 5.0 is a
      no-op.
- [x] Two corrections, both caught by the FluxusSource session: the residual was
      understated 3× (post-ADR-007 is **8.0/cycle**, not 2.6 — ADR-007 retires 59
      `gn_*` proxies, not the 243 publisher-named GN feeds), and the "topic feeds
      emit solution vocabulary" mechanism was **refuted** — `google_news_uplifting`
      is 80 short rows and **0** surfacing. It is one feed × one lens:
      `energy_storage` on solutions, 56.8%, and 0% on the other five.
- [ ] Re-measure gated on **measured GN-URL share per cycle**, not on "migration
      complete" — FluxusSource says there is no near-term done.

### ✅ Shipped alongside

- [x] **NM#303** production contract validation (`11d5860`) — Contract B CLEAN
      over 27,831 rows; **Contract A had never met production either** → **NM#304**
      filed with 4 defects (priority max 8 vs a 1–10 scale, `word_count` required
      on body-less sources, `source_type` enum missing `social`, undeclared
      `eval_query`).
- [x] **Census check A hardened** (`3f1bf07`) — it false-positived on
      `enriched`/`enriched_at`, which are rare-but-working (0–3 per filter per
      cycle). My first patch referenced a variable that does not exist and
      `py_compile` was green; only executing it caught that.
- [x] **`commit-msg` hook fixed** (`8741fa1`) — it false-failed on private Hub
      repos with no `HF_TOKEN`, and its own advice on failure is `--no-verify`.
- [x] **Framework v1.15.1 → v1.17.0** (`c286bb3`), reconciled by content.
      **agent-ready-projects#33** filed: `install-global-skills.sh` installs from
      the working tree, so an adopter can receive unreleased, later-reverted
      content — which happened for ~42 minutes today.

### Board

**197** — LD 34 · NM 44 · ovr 89 · FS 14 · ps 12 · atlas 3.
Closed today: NM#300, LD#88. Filed: NM#304, agent-ready-projects#33.

## 2026-08-08 — the checks failed, the analysis didn't

Full record: `memory/project_session_2026_08_08.md`. New topic file:
`memory/stamp-contract-integrity.md`.

### ✅ LD#101 — CLOSED, confirmed by outcome

- [x] **Confirmed live on the 08:49–08:55 cycle.** `eval_aggregator` rows in each
      filter's output went **21 → 0**, all six. Control: that cycle's *input*
      carried **22** such articles, so they were collected, scored, and stopped.
- [x] **Committed out of drift** — it had been running as *uncommitted
      working-tree edits on sadalsuud*, with nothing in `ducroq/NexusMind`
      referencing `eval_aggregator` at all. Now `9fb441a`; box fast-forwarded,
      tree clean, the six `.bak` files verified byte-identical to `e63202b`
      before deletion.
- [x] **The 30 published rows: 4 suppressed, 26 left to expire.** Not a cleanup
      job — all sat inside the 10-day window and age out 08-09..08-14 on their
      own, and most are good global-south coverage (Iringa/Njombe pine
      smallholders, Tanzania science policy, tree-kangaroo conservation deed,
      Els Xiquets de Tarragona). Bulk deletion would have hit exactly the
      population Chain 14 protects. `ovr.news@75bde57`, via the
      `manual_suppression` config kill switch — **not** a DB edit, because the
      live site builds from the R2 copy.
- [x] **Re-checked after the build 2026-08-08 — PASS exactly as pre-registered.**
      `gdelt_constructive_madagascar_7ff89d70aaf8` **404**,
      `newsdata_eval_td_456de0a16300` **404**, control
      `newsdata_eval_bi_1c78d8e397b7` **200**. The control holding is the part
      that matters: the suppression list is not over-matching.
- [ ] **Loose thread:** eval-arm articles cluster at **9.4–9.99** on uplifting and
      solutions. Unusually good stream, or scorers over-rewarding it? Check
      against LD#91 and NM#289 upper-tail inflation.

### 🔴 The pre-registered check would have called this fix broken

The check was *"`source_filter excluded N` must exceed the 121 baseline"*. It came
in at **86** — lower. That line aggregates all excluded types and swings with
corpus composition (**69 → 121 → 86** in one day; investment_risk 519 → 545 →
946). It was never sensitive to the one type added. **A metric that moves for
reasons unrelated to your change cannot confirm your change.** Two more of my
instruments broke the same day (a `len>3` language heuristic; a watcher whose
hour-glob matched the *date*), against zero broken conclusions.

### 🟢 NM#300 — fixed, deployed, NOT yet proven *(SUPERSEDED — see the afternoon section: it was FIVE drops, and it is now verified and closed)*

- [x] **Two drops in series**, so fixing either alone changes nothing:
      `FilterScoreResult` in `deploy/gpu-server/main.py` is a Pydantic allowlist
      (**kills it first**), then `scripts/main.py`'s `analysis` allowlist.
      Verified there is no third — `analysis` is attached whole and written with
      `json.dumps(article)`.
- [x] **Both halves deployed.** Free: the scorer was already down with ollama
      holding the GPU, so no restart and ollama untouched. gpu-server half
      **proven on the box** by `ast`-extracting the model classes verbatim from
      the deployed file and executing them in the scorer venv.
- [x] **OUTCOME CHECK RAN AND FAILED** — the 12:03 cycle read **0 of 2,170** with
      both fixes provably loaded. *"Suspect a third drop"* was the right
      instruction and there were **three** more. Closed out in the afternoon
      section above.
- [ ] Promote `content_length` to `required` in Contract B **only after** the
      census shows it populated **across several cycles**. One green cycle is not
      enough for a field that reached zero rows for months.

### 🟢 Stamp census + contracts — new, and they found things nobody asked about

- [x] `scripts/stamp_census.py` (`e64a45f`) — checks **population** and
      **consumers**, which no schema can express. It **failed its own acceptance
      test on first run** (missed NM#300, because absent ≠ null; missed LD#94,
      because six filters averaged hide a single-filter constant). Both gaps are
      why checks A and per-filter constancy exist.
- [x] **Contract B 1.15.0** (`3030e35`) — first-ever validation against
      production: **908 violations**. `image_analysis.image_confidence` declared
      `0..1` is a **raw logit** (−12.330..6.365, median −2.696, 68.4% outside).
      Producer right, contract wrong since it was written; fixtures could never
      have caught it. **908 → 1**, that one real and left failing.
- [x] Filed **NM#303** (contract tests validate fixtures, never production) and
      **FS#138** (a `null` inside `tags`).
- [x] **LD#88 item 1 gained evidence**: the census found `stage_used` and
      `stage1_estimate` assigned by a writer and present on **no** row. Fixed and
      verified the same day; **LD#88 closed** (all four items).
      ⚠️ Check A also **false-positived** on `enriched`/`enriched_at` in the same
      run — rare-but-working, 0–3 per filter per cycle. Hardened in `3f1bf07`.

### Board

**196** — LD 36 · NM 43 · ovr 89 · FS 13 · ps 12 · atlas 3. Sediment **74**
(cutoff 2026-07-09 — quote the cutoff, it moves on its own).

**Chain 8 (Google News) is CLOSED** — `ADR-007` accepted, FS#120 + FS#119 closed,
native-first, GN proxies and all three eval arms retired. **Done by a parallel
session 30 minutes before I commented on the issue asking for a decision already
taken.** So the board now has **no calendar-bound item at all**.

## 2026-08-07 (night) — the dedup question answered by mechanism, and a deadline in trouble

Full record: `memory/project_session_2026_08_07_night.md`.

### 🔴 LD#101 — evaluation arms are scored AND PUBLISHED (filed tonight, needs an owner decision)

- [x] **DECIDED 2026-08-08: exclude via `excluded_source_types`** — because that
      mechanism **already is** "score, don't publish".
      `NexusMind/src/scoring/source_filter.py::apply_source_filter` marks
      **already-scored** articles as `passed_prefilter = False`, so scores are
      kept and the rows never reach `filtered/` or ovr.news. *I first recommended
      building the same gate in ovr.news, on the wrong premise that
      `excluded_source_types` prevents scoring — it does not, and
      `memory/nexusmind-data-sources.md` had said so since 2026-08-02.*
      No new code, no third-repo change, no LD#95 batch perturbation (the corpus
      is unchanged), and it keys on `type_classification`, which is verified to
      survive into `ovr.db`.
      **Count corrected: 30 published rows, not 28** — `source LIKE '%_eval_%'`
      misses `gdelt_constructive_*` entirely. The two extra are Traditional
      Chinese Taiwanese local news at tier `high` under a Madagascar query.
      **Never key on the source string.**
- [x] **SHIPPED 2026-08-08.** `eval_aggregator` added to `excluded_source_types`
      in all 6 live filters + `cultural_discovery/v6` (the cutover candidate), and
      `eval_aggregator` added to `KNOWN_SOURCE_TYPES` in
      `tests/unit/test_filter_config_schema.py` — the schema gate rejected it
      otherwise, exactly as designed. Suite green (269 passed, 4 skipped).
      Copied surgically to `NexusMind/filters/*/config.yaml` (**not** via
      `deploy_to_nexusmind.sh`), backups at `config.yaml.bak_20260808_074336`.
      No restart needed: `nexusmind.service` is a per-cycle process, dead between
      runs, so configs load fresh; `scripts/main.py:1016-1018` is the caller.
      **Verified by EXECUTING the guard on the deployed config**, not by reading
      the key — positive and negative control:
      `eval_aggregator → passed_prefilter False`, `news_regional → True`,
      `excluded_count 1`. All 6 confirmed `eval_aggregator=True, shadow_mode=False`.
- [ ] **Confirm on the next cycle's log** (00:02 / 04:00 grid) — the `N scored,
      M prefiltered` line should show the eval arms among the prefiltered. That is
      the end-of-run outcome check; the guard test above proves the predicate and
      the load, not the production run.
- [x] **`memory/nexusmind-data-sources.md` updated** with the two traps this
      creates: corpus statistics over `data/filtered/*` will silently omit the
      eval arms, and FS#120's funnel must be read from the **GPU scorer log**,
      not from `filtered/`.
- [ ] **Remediate the 30 already-published rows** — reader-facing, ovr.news side,
      independent of the decision.
- [ ] **Check the Zimbabwe funeral row against the obituary gate** (enforcement is
      ON at v5@0.85). If it scored under threshold it is a live false negative and
      belongs in `memory/project-obituary-detector.md`.

- [ ] **FS#133's question is STILL OPEN — my "arbitrary" answer was retracted
      the same night.** The dedup survivor *within a run* is decided by
      `as_completed()` completion order — that part holds, though it is
      **untestable**: no fetch-duration field exists anywhere. But my premise
      ("both drops happened inside one source") is an **instrument artefact** —
      only **4,116 of 40,693 hashes (10.1%) carry a source**, so cross-run drops
      are structurally undetectable and every countable drop is same-run *by
      construction*. FS#133's own first comment said not to conclude from n=2; I
      did. **The cross-run mechanism is the bigger one and it is systematic**:
      `seen_hashes` persists 30 days, so the winner is whichever *run* polled
      first, set by `update_frequency` — GN feeds are **1 sub-12h vs 159 non-GN
      sub-12h**, i.e. **publisher-correlated**. And the loss is **sticky for up to
      30 days**, not reversible next run. Re-read after the next cycle: incumbents
      now carry sources, so cross-run drops become visible for the first time.
- [ ] **Measure near-duplicate SURVIVAL, not just deletion.** In the 20:06 run,
      **6 cross-source syndicated stories survived** dedup (different snippet →
      different hash) against **2 dropped** — one survivor being the same story as
      a drop, via a third outlet. Exact-hash dedup may not be where the
      corroboration evidence goes at all. Nobody has measured this.
- [x] **FS#134 DECIDED: delete.** Four independent grounds; the signal already
      exists downstream (E5 cosine at `cross_source_threshold=0.88`), it degrades
      cross-language, wiring it into dedup makes corroboration *worse*, and the
      emit-instead option is blocked by a live `numpy.uint64` JSON bug. Deleting
      drops `scipy` too — **114 MB of a 450 MB venv** — and removes the import
      that caused a 26-hour outage on 2026-06-30. Posted to FS#134.
- [x] **Board maintenance DONE** — NM#225 → Chain 15 (**re-dated 2026-05-28; the
      chain is 71 days old, not 2, and NM#225 is its root and the most actionable
      of the three derivations**), NM#226 → Chain 13, NM#254 → Chain 16 (it holds
      the SemEval-2023 taxonomy decision), **Chain 17 (NER) promoted** into the
      canonical chain list with five dependents.
- [x] **Cross-repo dependency audit: 13 live instances** of an OPEN issue citing a
      CLOSED dependency. FS#85 alone has **five** dependents (NM#223, ovr#222,
      ovr#223, ovr#231, ovr#232). Correcting comments filed on all uncorrected
      ones plus LD#38 (→NM#108), LD#56 (→NM#161), LD#23 (→NM#88).
      **Two were my own, filed the previous session** — FS#133 and FS#134 both
      cited NM#213 as the live consumer; NM#213 has been closed since 2026-05-23.
- [x] **Framework adoption verified by content, not by stamp** —
      `agent-ready-projects` v1.15.1 is genuinely installed (five marker strings
      present; installed mtime matches the commit to the second), `curate` body
      identical to template, no global `review-changes` shadowing the project one.
      `agent-ready-papers` is at v2.4.0 + 2 doc-only commits and is **not adopted
      here by design**.

### ⚠️ FS#120 (due ~2026-08-14, 7 days) — two measurement defects found

- [ ] **`newsdata_eval`: the local-publisher share is 40% / 12% / 8%, and that is
      probably H3's ANSWER, not a defect to fix.** ~~Same defect as GNews; add
      `country_queries`~~ — **WITHDRAWN, and it would have damaged the gate.**
      NewsData sends `country=` with **no `q=` at all**: it filters on *publisher
      location*, so it is the **geographic** arm, while `gnews_eval` uses `q=`
      only because its free tier can search topic alone. A comment at
      `newsdata_eval_aggregator.py:104-108` says exactly this and I read past it.
      Adding `country_queries` would convert the only geographic arm into a second
      topical one and destroy the like-for-like comparison against GDELT.
      My "77–97% off-topic" therefore measured the **wrong property** — an article
      from a Chadian publisher about cricket is *correctly* returned. Re-measured
      on publisher over the same 8 runs: **Chad 40.0%** genuinely local
      (`alwihdainfo`), **Madagascar 11.8%** (58.8% is `ign_za`, a South African
      video-game site), **Burundi 8.3%** (79.2% is `thecitizen_co_tz`, Tanzanian).
      **Score H3 on `metadata.publisher_name`, not article topic**, and re-derive
      at the API response — those denominators (65/34/24) survive a 49% dedup drop.
- [ ] **`items/day` is censored** — every eval identity is capped per run
      (`max_articles: 10` × 3 countries = 30; GDELT `max_records` 30–50 hardcoded).
      `gnews_eval` sat at exactly 30 in **13 of 44 runs (29.5%)** — and the more
      informative half is the floor: **21 of 44 runs returned only 10**, i.e. two of
      three countries yielded nothing. (30 is the ceiling *by arithmetic*, 3 countries
      × `max_articles: 10`, not an empirical discovery.) The readout must say it
      compares *tier ceilings* against the GN proxies' uncapped RSS supply.
- [ ] **H2 (GDELT starvation) — my "76% → 66%" was REFUTED; the sign is backwards.**
      Full record: pre-fix **66.4%** (122 runs) → post **76.9%** (13) / **80.0%**
      (10); Fisher **p = 0.546**; items/run 19.1 → 10.0. My "76% pre" was the
      issue's last-8-runs snapshot and my "66% post" was Aug 7 alone, dropping four
      post-fix Aug-6 runs that all yielded zero. I also split on the GitHub **close
      time** rather than the deploy time (`git reflog`: `0fa9ffa` 08-05 18:09,
      `61be1b1` 08-06 07:49 — two commits, the first still broken). **What holds:**
      FS#125's *coverage* half is real; the *yield* half cannot move — it is an
      external per-IP quota shared by two identities, and the plan doc already says
      "~50% zero is the designed behaviour". **H2's real question is whether the
      free tier is viable at all** — FS#125's Option 3, still undecided, and
      FS#132 still gates `gdelt_constructive`'s half.
- [ ] **Every rate in the readout needs a "measured over which window, across
      which config changes" line.** The eval period contains FS#125 (08-06),
      FS#128 (08-06) and the GNews `country_queries` change (08-05). I published a
      72.6% figure that straddled the FS#125 boundary and had to correct it.

## 2026-08-07 (late) — coverage pass, a refuted plan, one instrument shipped

Board was reported unchanged at **195 open** — *corrected 2026-08-07 night to **198**; this pass never re-counted after filing FS#133/#134*. The work was in what it does not cover, and in
one finding upstream. Full record: `memory/project_session_2026_08_07_late.md`.
Feature-level detail: `memory/corroboration-feature-hypotheses.md`.

- [x] **Cross-source dedup stamp SHIPPED + DEPLOYED** — `ducroq/FluxusSource@4994d61`,
      live on sadalsuud. Collection dedup drops on `md5(title + content[:500])`
      **with no source comparison**, so the same wire copy from two outlets is
      deleted before NexusMind ever embeds it. Drop behaviour unchanged; the
      collision is now counted and reported at INFO. **FS#133.**
- [x] **FS#134 filed** — MinHash + Jaccard implemented, `datasketch` pinned,
      **zero call sites**. Wire it up as a corroboration feature or delete it.
- [x] **NM#232 planned, then refuted by a six-lens review.** Findings filed on the
      issue. Do not build as specified: its consumer list omits the only consumer
      with code (the matching model — **NM#188/NM#301**; NM#213 is CLOSED), which wants a cross-lingual *offline
      re-run*, not a CPU pipeline stage.
- [x] **Dependency corrections filed** on NM#223 and ovr#222 — both cite
      `FluxusSource#85`, which is CLOSED and re-homed to NM#232.
- [x] **Read the cross-source count** — done 2026-08-07 night, and the count is
      **not yet readable**: only one run has carried the stamp (20:06), giving 2
      drops; the timer is 6 runs/day and the figure stays a floor until
      ~2026-09-06. **The question it was meant to answer was settled by reading
      the call path instead** (see the night block above). Step 3 of the
      corroboration track is still gated — but expect "the pairs were never
      there", not "the pairs are biased".
- [x] **Board maintenance** — done 2026-08-07 night, plus Chain 17 promoted and
      seven stale entries corrected (NM#213/#220/#91, LD#43/#49, FS#125/#126) and
      a count error fixed (**198 open, not 195** — the pass never re-counted after
      filing FS#133/#134).
- [ ] **Owner call**: does `ducroq/augmented-engineering` (34 open, **1 closed
      ever**) belong on the board? CLAUDE.md mandates filing evidence into it.

## Commerce Prefilter SLM - NEEDS REWORK

ML classifier for commerce/promotional content detection. Cross-cutting prefilter for all filters.

**Status:** v1 complete but needs redo - concerns about multilingual embeddings and context size.
**v1 is the version running in production** — force-pinned by LD#80 because **v2 underperformed v1** on production traffic. There is no v3.

- [x] **v1 Training data collection** - 2,847 examples (commerce + journalism)
- [x] **v1 Model training** - DistilBERT, MiniLM, XLM-RoBERTa compared
- [x] **v1 Backtesting** - 56,336 articles, threshold optimization
- [ ] **Re-measure the miss rate before retraining** ← **DO THIS FIRST (added 2026-08-07)**
- [ ] **NM#223 is a live input to this and is blocked** (found 2026-08-07 late) —
      NER entity-density as an *additive* commerce signal, explicitly "does not
      replace the v3 retrain planned in NM#185 Phase 2". It is blocked on
      **NM#232**, not on the closed `FluxusSource#85` its body still names.
      Nothing here should assume entity features will be available.
- [ ] **Redo with proper multilingual embeddings** - Current approach may not handle Dutch/multilingual well
- [ ] **Redo with proper context size** - May need longer context

### The v3 case is tracked in ducroq/NexusMind#185, and its evidence has decayed

Found 2026-08-07 while re-querying the cross-repo chains. NM#185 bundles the
obituary blocker (shipped, enforcing at 0.85 since 07-30) with a **commerce v3
retrain that was never started** — which is why Chain 1 read as complete when it
was half done.

**Before any v3 training run, re-measure.** NM#185's commerce evidence is the
2026-06-25 reader-flag audit, whose headline was that the recoverable miss set
was **100% scored by `sustainability_technology`** — a filter **deleted
2026-08-03** (#64, superseded by `solutions`). The product-launch-in-
sustainability-framing pattern presumably still arrives, but it is now scored by
`solutions v6`, which has a different prompt, a different op-point and an e5
probe in front of it.

**Open hypothesis:** the commerce miss rate under the current five-lens set is
materially lower than the 2026-06-25 audit implies, and v3 may not be warranted
at all. Unmeasured. Deciding it costs one count, not a training run.

See `filters/common/commerce_prefilter/docs/` for full documentation.
<!-- verify: ls filters/common/commerce_prefilter/ | grep -E '^v[0-9]+$' -->
<!-- verify: gh issue view 185 -R ducroq/NexusMind --json state --jq .state -->

---

---

## Filters

### Production Ready
- [x] **uplifting v6** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.673 (was 0.688 in v5), 12% faster inference
  - Gemma-3-1B base model (was Qwen2.5-1.5B)
  - 10,495 training articles with data sculpting: active learning (495 MEDIUM enrichment) + label correction (57 crime articles capped)
  - v5 crime news issue fixed via manual label correction in training data
- [x] **uplifting v5** - Superseded by v6
  - Val MAE: 0.68, 10,000 training articles
- [x] **sustainability_technology v1** - Deployed on HuggingFace Hub
  - Test MAE: 0.690
- [x] ~~**sustainability_technology v3**~~ — **REMOVED 2026-08-03**, replaced by solutions. Package deleted; recover from git history. Entry kept for the training record below, not as a statement of what is deployed.
  - Val MAE: 0.734 (calibrated test: 0.724), Gemma-3-1B
  - 10,608 training articles (v2 10,039 + 569 active learning enrichment)
  - All 3 inference paths: local, Hub, hybrid (probe MAE 0.91)
- [x] **sustainability_technology v2** - Superseded by v3
  - Val MAE: 0.71, 7,990 training samples
- [x] **investment-risk v6** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.497 (calibrated: 0.465), Gemma-3-1B
  - 10,448 training articles (v5 10,198 + 250 active learning enrichment)
  - Tier simplification: RED/YELLOW/GREEN/BLUE/NOISE -> high/medium_high/medium/low
  - All 3 inference paths: local, Hub, hybrid (probe MAE 0.557)
- [x] **investment-risk v5** - Superseded by v6
  - Test MAE: 0.484 (excellent)
  - 10,000 training articles
- [x] **cultural-discovery v5** - Deployed on HuggingFace Hub + gpu-server (private) — 2026-05-31
  - Val MAE: 0.697 (v4 was 0.74), Gemma-3-1B
  - 8,551 training articles, DeepSeek V4 Flash oracle (first non-Gemini lineage)
  - Resolves llm-distillery#62 discovery-lens leakage via F/G/H/I/K soft-penalty flags (historical_harm_reckoning, commemoration, perpetrator_biography, decline, launch)
  - Provisional reference example for ADR-020 methodology (multi-oracle calibration + agent judging)
  - Target: ovr.news Discovery tab
- [x] **cultural-discovery v4** - Superseded by v5; on disk locally + git + HF Hub for rollback if needed
  - Calibrated test MAE: 0.74 (v3 was 0.77), Gemma-3-1B
  - 8,029 training articles (v3 7,827 + 202 active learning enrichment)
  - All 3 inference paths verified (local, Hub, hybrid)
- [x] **cultural-discovery v3** - Superseded by v4

### In Active Development (priority: ovr.news tabs)
- [x] **belonging v1** - Deployed, val MAE 0.49 (calibrated), 7,370 articles. Next: ovr.news tab
- [x] **nature_recovery v2** - Deployed to Hub + gpu-server + sadalsuud (Hub upload actually completed 2026-04-19 after #44; prior commit claimed it without uploading)
  - Val MAE 0.53 (calibrated), probe MAE 0.49, 3,517 articles
  - v1 had zero discrimination (#41); v2 uses sample weighting (scale=2)
  - Recall@20: 0.70 (v1: 0.55), NDCG@10: 0.86 (v1: 0.71), false negatives: 17% (v1: 41%)
  - Hub: `jeergrvgreg/nature-recovery-filter-v2` (private)
  - Remaining: normalization (needs production CDF), ovr.news Recovery tab frontend
- [x] **uplifting v7** - ADR-010 prompt rewrite, deployed with hybrid inference (2026-04-06)
  - v7 prompt: scope check, anti-hallucination, reframed assessment dimensions
  - Hybrid inference: probe MAE 1.10, threshold 1.00, 0.5% FN, 1.07x speedup
  - Evolved into thriving v1: renamed, social_cohesion_impact removed, 3-run averaging planned
- [ ] ~~**thriving v1**~~ - PARKED indefinitely. Uplifting v7 (MAE 0.67) stays as Thriving tab.
  - Root cause: orthogonal lens design created bimodal distribution (ADR-015)
  - A fixed thriving v2 would converge back to uplifting v7. Not worth retraining.
  - Assets preserved in `memory/thriving-v1-scoring.md` if ever revisited
- [x] ~~**foresight v1**~~ — **REMOVED 2026-08-03**, merged into solutions (#43, closing out #64). Was signs_of_wisdom. Package deleted; recover from git history.
  - Val MAE 0.75, 3,480 training articles, 6 dimensions
  - Hybrid inference: probe trained, threshold 2.25 (default, calibrate on production data)
  - Remaining: ovr.news Foresight tab frontend integration

### Active Learning In Progress
- [x] **cultural-discovery v5** - **DEPLOYED** (HF Hub, DeepSeek oracle, MAE 0.70). Stale `[ ]` corrected 2026-08-03 — the entry below describes the training-data prep that has long since shipped. Live follow-ups are #86 (prefilter is dead in production — measured, DO NOT enforce) and #87 (v6 scope: lens-fidelity + op-point re-derivation).
  - Oracle-scored 473 production MEDIUM+ articles with Gemini Flash (active-learning lane, 2026-04-06)
  - Smooth distribution (bell curve centered at WA 4.8), no bimodality
  - 2026-05-29: #62 hard-negatives cohort added — 49 articles labeled with v5 oracle prompt (5 new pre-classification flags F,G,H,I,K)
  - v5 prompt deltas: TRAJECTORY OVER VOCABULARY principle, CAP ENFORCEMENT clamp rule, F carve-out covers wartime restitution (Modigliani fixed), J intentionally omitted (handled by `filters/common/obit_signal.py` per #51)
  - Cohort stats: production v4 mean 8.27 → v5 oracle mean 4.05; 44 hard-negatives + 5 calibration-confirmed positives (tagged `_v5_oracle_reclassified`)
  - Next: train on gpu-server, calibrate, retrain probe, deploy
- [x] **nature_recovery v2** - Trained, calibrated, deployed (2026-04-16)
  - Sample weighting (scale=2) + active learning enrichment (237 articles)
  - Remaining: normalization (needs production CDF), hybrid threshold recalibration

### Other Filters
- [ ] ~~**future-of-education**~~ - DROPPED: education stories land naturally in Breakthroughs (research)
- [ ] **ai-engineering-practice v2** - Ready for oracle scoring (not ovr.news, separate product)
  - FluxusSource hardware sources active (1,193 articles)
  - Prompt calibration complete (~60% tier accuracy)
- [ ] **seece** - Corporate excellence (not ovr.news)
- [ ] **sustainability_economic_viability** - Sustainability sub-dimension (not ovr.news)
- [ ] **sustainability_policy_effectiveness** - Sustainability sub-dimension (not ovr.news)

### Parked Ideas

- [ ] **Re-enchantment outlets (wonder lens / standalone digests)** - PARKED 2026-07-16 by Jeroen ("some other time"). Byung-Chul Han-inspired exploration: wonder/mystery/myth as lens or standalone oracle-only outlet (no distillation needed at digest scale, ~$6.50/wk). Six ideas + four cheap probe plans (<$3 total: Residue query $0 → Wonder probe ~$0.50 → form-scoring feasibility ~$1-2 → Ledger design note $0) with kill criteria in **`docs/ideas/re-enchantment-outlets.md`**. Hard constraint if resumed: "unexplained" needs an `epistemic_honesty` gatekeeper (misinformation magnet otherwise). Below solutions v4 (#43) and the #62 check in priority.

## Training Pipeline

- [x] **Data preparation pipeline** - Stratified splits working
- [x] **Training script** - Gemma-3-1B + LoRA working (was Qwen2.5-1.5B)
- [x] **Context length experiments** - 1024/2048/head+tail tested
  - 1024tok: MAE 0.652, 2048tok: MAE 0.627
  - head+tail (256+256): MAE ~0.69 (deployed to production)
  - See `docs/IDEAS.md` for full results
- [x] **Stage 2 model comparison** - Gemma-3-1B adopted as default Stage 2. Wins on both uplifting (MAE 0.652 vs 0.660) and cultural-discovery (MAE 0.743 vs 0.755). 8% faster, fewer params. Qwen-0.5B rejected (MAE 0.760)
- [x] **Gemma-3-1B training support** - `training/train.py` updated with `load_base_model_for_seq_cls()` for both initial and resume paths
- [x] **Stage 2 model selection** - Gemma-3-1B adopted as default (was Qwen2.5-1.5B). Larger models deferred.
- [ ] **Training monitoring improvements** - Better logging, early stopping

## Score Calibration (ADR-008)

Post-hoc isotonic regression to correct MSE score compression at inference time.

- [x] **Shared calibration library** - `filters/common/score_calibration.py` (fit, apply, save, load)
- [x] **CLI fitting tool** - `scripts/calibration/fit_calibration.py` (works for any filter)
- [x] **Uplifting v6 calibration** - Fitted on 1,049 val articles, val MAE 0.673 -> 0.653 (+3.1%)
- [x] **Cultural-discovery v4 calibration** - Fitted on 803 val articles, test MAE 0.77 -> 0.74 (+4.4%)
- [x] **Base scorer integration** - `_load_calibration()` + `apply_calibration()` in `_process_raw_scores()`
- [x] **sustainability_technology v3 calibration** - Fitted on 1,061 val articles, test MAE 0.725 -> 0.724
- [x] **investment-risk v6 calibration** - Fitted on 1,045 val articles, val MAE 0.497 -> 0.465 (+6.5%)
- [x] **belonging v1 calibration** - Fitted on 738 val articles, val MAE 0.534 -> 0.489 (+8.3%)
- [x] **nature_recovery v1 calibration** - Fitted on 328 val articles, val MAE 0.540 -> 0.507 (+6.2%)
- [x] **nature_recovery v2 calibration** - Fitted on 352 val articles, val MAE 0.632 -> 0.533 (+15.7%)

## Hybrid Inference Pipeline (ADR-006)

Two-stage pipeline: fast embedding probe (Stage 1) + fine-tuned model (Stage 2).

- [x] **Shared infrastructure** - `filters/common/embedding_stage.py`, `hybrid_scorer.py`
- [x] **Uplifting v5 integration** - `inference_hybrid.py` + MLP probe
- [x] **Calibration script** - `evaluation/calibrate_hybrid_threshold.py`
- [x] **Threshold calibration** - Calibrated on 24K production articles. Probe retrained (v2): MAE 0.49, bias +0.007. Threshold 3.5 → 1.7% FN rate on MEDIUM+
- [x] **Speed benchmark** - RTX 4080: e5-small 1.3ms + Qwen 37.9ms. Threshold 4.5 → 2.09x on skewed data, ~2.5-3x in production
- [x] **Stage 2 model evaluation** - Gemma-3-1B adopted as default Stage 2 model. Confirmed on two filters: uplifting v5 (MAE 0.652 vs 0.660, tier 86.6% vs 85.4%) and cultural-discovery v3 (MAE 0.743 vs 0.755, tier 94.6% vs 94.5%). 8% faster inference, 38% faster training
- [x] **Generalize to other filters** - Phase A complete: inference_hybrid.py + probe dirs + calibration fix for sustainability_technology v2, investment-risk v5, cultural-discovery v3
- [x] **Train probes + calibrate thresholds** - Phase B complete: e5-small MLP probes trained and calibrated for all 3 filters
  - sustainability_technology v2: probe MAE 0.707, threshold 1.25, 1.2% FN, 1.25x speedup
  - investment-risk v5: probe MAE 0.497, threshold 1.50, 0.8% FN, 1.07x speedup
  - cultural-discovery v3: probe MAE 0.609, threshold 1.25, 0.0% FN, 1.52x speedup
- [x] **Cultural-discovery v4 probe** - Retrained for Gemma-3-1B, MAE 0.87, threshold 1.25, 3% FN, 1.51x speedup
- [x] **Sustainability_technology v3 probe** - Trained for Gemma-3-1B, MAE 0.91, threshold 1.25 (to be calibrated)
- [x] **Investment-risk v6 probe** - Trained for Gemma-3-1B, MAE 0.557, threshold 1.50
- [x] **Belonging v1 probe** - Trained for Gemma-3-1B, MAE 0.54
- [x] **Nature_recovery v1 probe** - Trained for Gemma-3-1B, MAE 0.50
- [x] **Nature_recovery v2 probe** - Retrained for v2 model, MAE 0.49 (early stop epoch 24)
- [x] **Foresight v1 probe** - Trained for Gemma-3-1B, threshold 2.25
- [x] **Foresight v1 calibration** - Fitted, calibration.json committed with filter package
- [x] **Uplifting v7 probe** - Trained for Gemma-3-1B, MAE 1.10, threshold 1.00 (#34)
- [x] **Harmonize all filters** (2026-04-06) - All 7 production filters now have hybrid inference with calibrated thresholds and `--compare` CLI. Fixed investment-risk import path bug (hyphen vs underscore). Deployed to sadalsuud + gpu-server.

## Code Quality (Feb 2026)

- [x] **FilterBaseScorer extraction** (#10) - Shared base class in `filters/common/filter_base_scorer.py`, all 4 production filters migrated
- [x] **load_lora extraction** (#11) - Shared `load_lora_model()` in `filters/common/model_loading.py`
- [x] **Code quality sweep** (#12-#19) - Resolved 8 issues: removed dead code, cleaned stale comments, fixed inconsistencies (-314 lines)

## Energy-Efficient Inference (#24)

- [x] **PyTorch dynamic quantization experiment** - 2026-03-07
  - Tested FP32/FP16/INT8 on uplifting v6, CPU-only
  - INT8: 2.6x faster, 3.3x smaller, but MAE +0.63 (unusable)
  - FP16: NaN on CPU (no native fp16 ALUs)
  - **Verdict:** Naive quantization rejected
  - See `docs/experiments/quantization-benchmark-2026-03-07.md`
- [ ] **ONNX Runtime INT8** - Calibrated quantization with representative data
- [ ] **Smaller base model retraining** - SmolLM-360M or similar sub-1B models
- [ ] **llama.cpp / GGUF** - Purpose-built CPU inference engine

## Deployment

- [ ] **Inference server** - Unified prefilter + model + postfilter pipeline
- [ ] **Batch processing** - High-volume article scoring
- [ ] **Production monitoring** - Latency, accuracy drift detection

## Infrastructure

- [x] **Prefilter evaluation framework** - Complete for sustainability_technology
- [ ] **Generalize prefilter evaluation** - Apply to all filters
- [ ] **Dataset QA pipeline** - Automated quality checks
- [ ] **Cost tracking** - Monitor API usage for oracle scoring
- [x] **Hub scorers: add torch_dtype parameter** - All 6 `inference_hub.py` files now accept optional `torch_dtype` param and pass it to `from_pretrained()`. Use `torch_dtype=torch.float16` on hardware without bfloat16 support.
- [x] **Deploy all filters to NexusMind** (#7) - All 6 filters deployed to gpu-server + sadalsuud + HuggingFace Hub
- [x] **Auto-compute score_scale_factor** (#22/#26) - Calibration script writes `score_scale_factor` to config.yaml; backfilled to all 6 filters
- [x] **Harmonize filters: llm-distillery as single source of truth** - Fixed drift between llm-distillery and NexusMind
  - base_prefilter.py: threading.Lock() for commerce detector (was bool flag)
  - investment-risk v5: merged source-based + content-pattern approaches, removed academic source blocking
  - Deployed all production prefilters to NexusMind (sadalsuud + gpu-server)
  - Verified 0 diff between all three locations
- [x] **Manifest-aware deploy script (#50)** - 2026-04-28. `.nexusmind-owns` at repo root + `--dry-run` + `--force-skip-owned-drift` in both `.sh` and `.ps1`. Lists `filter_base_scorer.py` and `hybrid_scorer.py` (NexusMind-owned). Deploy now exits non-zero on drift between distillery and NexusMind copies.
- [ ] **Harmonize prefilter structure across all 7 production filters (#52)** - Filed 2026-04-28. Survey shows 5 different override mechanisms, 3 with class/version drift between class name and dir, mixed flat-list vs dict containers. ~12-16h work; per-filter migration in priority order.
  - [x] **ADR-018** (2026-04-28) - Declarative shape decision documented; backwards-compatible BasePreFilter extension chosen
  - [x] **BasePreFilter extension** (2026-04-28) - EXCLUSION_PATTERNS / OVERRIDE_KEYWORDS / POSITIVE_PATTERNS / POSITIVE_THRESHOLD class attrs + default apply_filter() pipeline + _is_excluded / _has_override / _filter_specific_final_check helpers. All 7 production prefilters import + run unchanged (verified)
  - [x] **sustainability_technology v3 migrated** (2026-04-28) - 6/6 self-tests pass; behavior preserved
  - [x] **belonging v1 migrated** (2026-04-29) - 19/19 self-tests pass; behavior preserved. Data shape (EXCLUSION_PATTERNS dict, base-compiled patterns) harmonized; apply_filter stays custom because per-category positive-count thresholds + URL-based domain exclusions + obituary floor rule don't fit the base pipeline (ADR-018 explicitly permits this).
  - [x] **cultural-discovery v4 migrated** (2026-04-29) - 10/10 self-tests pass; behavior preserved. Data shape harmonized: EXCLUSION_PATTERNS dict + parallel EXCEPTION_PATTERNS_PER_CATEGORY dict (per-category exceptions don't fit base's single OVERRIDE_KEYWORDS slot). CULTURAL_DISCOVERY_BOOST_PATTERNS renamed to POSITIVE_PATTERNS so base compiles them. classify_content_type() preserved. Surfaced regression vs v3: v4's apply_filter doesn't call check_content_length (preserved as-is in this commit; tracked separately under Prefilter Quality below).
  - [x] **uplifting v7 migrated** (2026-04-29) - 12/12 self-tests pass; behavior preserved. Same EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY pattern as CD v4 for the 3 pattern-with-exception categories (corporate_finance, military_security, crime_violence); 4th category (pure_speculation) is count-based (speculation_count >= 3 AND outcome_count == 0) and stays as separate class attrs with an inline check after the dict iteration. classify_content_type preserved. ThrivingPreFilterV1 (which subclasses UpliftingPreFilterV7) verified working. Surfaced bug: Dutch `munitie` and similar multilingual patterns lack `\b` boundaries — fire on English substrings like "co-MMUNITIE-s" (preserved as-is; tracked under Prefilter Quality).
  - [x] **investment-risk v6 migrated + class drift fix** (2026-04-29) - 11/11 self-tests pass; behavior preserved. v6 now has its own InvestmentRiskPreFilterV6 class (was a re-export of V5). Backward-compat aliases (InvestmentRiskPreFilterV5 = V6, InvestmentRiskPreFilter = V6) + legacy prefilter()/get_stats() functions kept so existing imports don't break. base_scorer.py updated to reference V6 directly. Data-shape harmonization only — apply_filter stays custom because the source-based flow + matched-pattern reason strings + title-only clickbait don't fit the base pipeline.
  - [x] **nature_recovery v2 migrated** (2026-04-29) - 6/6 self-tests pass; behavior preserved. Single text-pattern category (disaster_no_recovery) with one parallel exception list (recovery framing) lives in EXCLUSION_PATTERNS / EXCEPTION_PATTERNS_PER_CATEGORY. Custom apply_filter retained because: (1) nature-relatedness check runs FIRST in the original order — base's final-check hook runs LAST and would change reason precedence; (2) reason strings are bare category names (not "excluded_<category>"); (3) original v2 doesn't call `check_content_length` — same gap as CD v4 (tracked under Prefilter Quality). Class-name drift V1→V2 deferred to the cleanup batch as planned.
  - [x] **foresight v1 migrated** (2026-04-29) - 10/10 self-tests pass; behavior preserved. Six block categories in EXCLUSION_PATTERNS dict; six positive-signal categories in custom POSITIVE_PATTERN_GROUPS dict (NOT base's POSITIVE_PATTERNS slot — semantics differ: foresight counts distinct *categories* with at least one match, while base's POSITIVE_THRESHOLD counts total matches). apply_filter stays custom for the distinct-categories-fired override + two pass reasons (`passed_positive_signals` for >=3 categories, `passed` for the no-block fall-through) + URL-based domain exclusions.
  - [x] **All 7 production filters now migrated** (2026-04-29) - sustech v3, belonging v1, cultural-discovery v4, uplifting v7, investment-risk v6 (+ class drift fix), nature_recovery v2, foresight v1. Only the deferred class-name drift cleanup batch remains as #52 work.
  - [ ] **Class-name drift cleanup batch** - sustech V2→V3, nature_recovery V1→V2 still pending. (investment-risk v6 own class — DONE 2026-04-29 as part of its #52 migration.) Deferred until remaining migrations done to avoid cross-repo coordination noise (NexusMind tests/unit/test_prefilter.py imports the V2 name).

## Post-#52 Review-Battery Followups

Items surfaced by the multi-agent code review of the migration commits (2026-04-29). Triaged in TODO.md as committed batches.

- [x] **RIP guard repair** (2026-04-29, commit `dd20749`). Code-reviewer caught that the `(?-i:\bRIP\b)` "fix" from `598fa72` was inert in production — `_get_combined_clean_text` lowercases input before pattern matching, so the inline case-sensitive flag had no uppercase chars left to enforce. Real fix: read the raw title directly and run a case-sensitive `\bRIP\b` against it. Title-only. 20/20 tests.
- [x] **POSITIVE_PATTERNS shadow rename** (2026-04-29, commit `7f22d01`). Refactoring agent flagged that belonging v1 + CD v4 shadowed `BasePreFilter.POSITIVE_PATTERNS` with incompatible semantics — a future maintainer setting `POSITIVE_THRESHOLD > 0` would silently activate wrong base behavior. Renamed to `POSITIVE_SIGNAL_PATTERNS` (belonging) / `DISCOVERY_PATTERNS` (CD) and compiled locally.
- [x] **CD v4 truncation** (2026-04-29, commit `e2595dc`). Security audit flagged CD v4 ran ~60 patterns against unbounded body. Added `[:MAX_PREFILTER_CONTENT]` slice in apply_filter + classify_content_type, matching uplifting v7's pattern.
- [x] **uplifting v7 multilingual `\b` boundary sweep** (2026-04-29, commit `d0916f4`). Far broader than the known `munitie`/communities bug — `viol`/`acquisition`/`fusion`/`auteur`/`association` were all unbounded multilingual alternations causing real false-positives on English content. All `\b` anchors added; locked-in test rewritten to expect correct `pure_speculation` outcome.
- [x] **Investment-risk v6 cleanups** (2026-04-29, commit `24af3f8`). `\bfed\b` keyword tightened (no longer fires on "fed up" / "force-fed"), `get_statistics` alias added for cross-filter naming consistency, reason-string raw-regex contract documented at construction sites.
- [x] **CD v4 colonial exception tightening** (2026-04-29, commit `ffffdf9`). Bare `\bcolonial\b` was too broad — bypassed celebrity_art on "colonial mansion auctioned by billionaire" et al. Dropped; surrounding repatriation/restitution/provenance patterns provide adequate coverage.
- [x] **`_check_domain_exclusions` hoist + `_pre_exclusion_check` hook** (2026-04-29, this commit). 4 identical implementations consolidated into `BasePreFilter._check_domain_exclusions` driven by a per-filter `DOMAIN_EXCLUSIONS` dict. Symmetric `_pre_exclusion_check` hook added to `BasePreFilter.apply_filter` (mirrors `_filter_specific_final_check` — useful for filters with a gate-in check that should short-circuit before exclusions). All 4 filter test suites pass; sustech v3 unaffected.
- [x] **ADR-019 first migration: belonging v1** (2026-05-22, commits `ba6b7cb` + `c1ebc98`). Per-category bypass logic (non-obit `has_exc OR pos >= threshold` rule, obit floor `pos >= 2 OR (has_exc AND pos >= 1)`) lifted out of `apply_filter` into `_compound_override_applies` hook. apply_filter shrank ~65 → ~30 LOC. Custom apply_filter retained for the three ADR-019-flagged reasons (URL-domain-first ordering, bare reason strings, case-sensitive `\bRIP\b` raw-title force-fire). 20/20 self-tests green; multi-agent review battery (code-reviewer + refactoring-guide + security-auditor in parallel) returned PASS with three inlinable findings (threshold>0 guard, assert on unhandled category, base docstring drift), all applied in `c1ebc98`.
- [ ] **Extend `_is_excluded` for per-category exceptions + migrate CD v4 / uplifting v7 to base pipeline** - Path narrowed by the belonging migration above: the architecturally-correct next move is the two-step path filed as **#66** (base `EXCLUSION_REASON_PREFIX` class attr + move domain checks into `_pre_exclusion_check`), which unblocks fully-declarative migration for belonging v1, CD v4, uplifting v7, foresight v1, and NR v2 simultaneously. ADR-019's hook signature widening (raw-article access) deferred until a second filter shows up needing case-sensitive raw fields. Original open questions still apply: (a) reason-string convention — covered by the prefix attr in #66; (b) CD v4 missing `validate_article` + `check_content_length` — base would add both, fixing the regression but changing observable behavior; (c) uplifting v7's count-based `pure_speculation` block doesn't fit the dict shape regardless.
- [ ] **Migrate nature_recovery v2 to fully-declarative shape via `_pre_exclusion_check`** - Bundle with #66 (the reason-prefix attr is the prerequisite). NR v2 has the same shape concerns as the post-#52 cluster: bare reason strings, missing `check_content_length`, and order-of-checks differences from the base pipeline.

## Prefilter Quality (Apr 2026)

- [x] **belonging v1 obituary leak (#45)** - 2026-04-28. 5 bypass classes patched (dies-with-verb, procession, vigil, RIP/rest in peace, killed-in-year), `dies at \d` → `\d+` bug fix, override floor on obit branch. Plus `(?-i:\bRIP\b)` follow-up after the case-insensitive false positive on "rip current".
- [x] **sustainability_technology v3 clickbait leak (#46)** - 2026-04-28. CLICKBAIT category added with 6 patterns (you-won't-believe, without-knowing, this-common, you're-probably, X-things-you-didn't, shocking-fact). Pattern 5 bounded `.{0,120}` after review caught cross-sentence FP risk.
- [x] **cultural-discovery v4/v5 missing content_length check** — CLOSED 2026-08-03 by #93, in the opposite direction from the one planned. No `apply_filter` calls `check_content_length` any more; the floor is enforced once, in the oracle path, for every filter. cd was the only filter whose *labelling* path had no floor, so #93 restores one there: measured on a short-skewed stress corpus (`data/raw`, 66% sub-300) that withholds ~40% of what cd would have sent to the oracle. The production-realistic share is lower and unmeasured — **re-measure before the next cd oracle run** (#87).
- [x] **nature_recovery v2 missing content_length check** — MOOT 2026-08-03 (#93). Not a gap any more: no prefilter checks length.
- [x] **uplifting v7 multilingual `\b` boundary leak** - FIXED 2026-04-29. Sweep of NL/DE/FR multilingual alternations added `\b` boundaries to every category in EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY. Big offenders cleaned up: `munitie` no longer fires inside "communities", `viol` no longer matches inside "violence"/"violation"/"viola"/"violin" (was a major crime_violence FP vector on English content), `fusion`/`acquisition` (false corporate_finance), `auteur` (false on "auteur theory"), `association` exception (over-broad bypass). Locked-in test case for "New Technology Could Transform Energy Production" rewritten — now correctly hits `pure_speculation` instead of bug-induced `military_security`. 12/12 tests pass; ThrivingPreFilterV1 subclass verified.
- [x] **Universal obituary detector (#51/#83)** — DONE through enforcement 2026-07-30 session 3: v5 trained (21 FN-delta hard positives), 3-reviewer battery corrected the eval (fair table excl-24; June-increment panel 0.71–0.83, threshold-insensitive), owner adjudicated 14 boundary rows (grief-vs-news rule, flips both sharpened-broad clauses), owner went recall-first ("I just hate obits coming through") → **ENFORCEMENT ON: v5 @ 0.85** (NexusMind `b904edc`, `obituary_blocked` in dedup gate, config-gated rollback via `pipeline.obituary_detector.enforce`). **Enforcement VERIFIED 2026-07-30 20:12 + overnight sanity check PASSED 2026-07-31** (1158→1208→1249 blocked, all-v5 stamps, zero post-enforcement obit leaks in 133 collected). ovr#204 handled ovr-side (editorial gate retired 2026-07-30; sentinel re-derivation ~5% after Aug 6; downstream death-rate 7.9%→2.9% past the boundary). Site carryover (47 flagged shadow-era articles + 2 v5 FNs) washes out by ~Aug 13 — owner accepted, no purge.
- [ ] **Obituary v6 (#85) — PARKED indefinitely (owner, 2026-07-30)**: v5@0.85 enforcement meets the recall-first requirement. Reactivate only if an obit reaches the site (owner flag) or over-blocking visibly hurts the feed. Plan preserved on the issue; b650 env + adjudicated golden set (14 rows) stay ready. **2026-07-31 FN evidence banked for reactivation** (memory/obituary-v4-hypotheses.md addendum 7 + #85 comment): community-mourning class regresses monotonically v3 0.68 → v4 0.44 → v5 0.12 (hard-negative interference); biography-rich obits are a stable all-version blind spot (~0.2–0.3, threshold can't reach).
- [x] **Violence promotion prefilter (#73)** — v1 shadow-deployed NM#274 (2026-07-28). Frozen mpnet-base-v2 + MLP(256,128), 1,957 training samples. OOF precision 0.936, recall 0.550 @0.95. Stamp-only per ADR-004. Next: shadow accumulation → panel validate → v2 retrain with more data (recall is low at 0.55).

## Cross-Filter Normalization (ADR-014)

- [x] **uplifting v6 normalization** - Fitted on production CDF
- [x] **belonging v1 normalization** - Fitted on production CDF
- [x] **cultural-discovery v4 normalization** - Fitted on production CDF
- [x] **sustainability_technology v3 normalization** - Fitted on production CDF
- [x] **uplifting v7 normalization** - Fitted on 73,986 production articles (2026-04-06)
- [x] **foresight v1 normalization** - Fitted on 623 articles (thin LUT, improves as data accumulates)
- [x] **nature_recovery v1 normalization** - Refitted on 76,500 articles (still clamped — extreme needle filter, #32)
- [x] **nature_recovery v2 normalization** - Fitted on 1,397 v2 production articles (filter_version=2.0, weighted_average >= 1.5), deployed to sadalsuud + gpu-server (2026-04-28). Patched `fit_normalization.py` with `--filter-version` to exclude v1 leftovers (19,948 articles correctly skipped). Curve: raw range 1.50–7.08, p95=4.49.
  - [x] **Follow-up VERIFIED 2026-05-04**: sustainability_technology JSONL on sadalsuud (1142 articles, 19:22 UTC pipeline run) shows `weighted_average=1.81`, `raw_weighted_average=4.42`, `normalization_method="percentile"` — both audit fields populated end-to-end for the first time since 2026-04-16. The verification revealed that the runtime application code itself had been silently deleted from NexusMind and gone unnoticed for 18 days; fix landed via Path B extraction into `NexusMind/src/scoring/production_scorer.py` wrapper class (NexusMind merge `0e80d92`). All 7 filters now populate the audit fields. See `memory/gotcha-log.md` "Manifest as Anti-Pattern" entry for full diagnosis.

## Documentation

- [ ] **Update filters/README.md** - Current status is outdated (Nov 2025)
- [ ] **Training guide** - Step-by-step for new filters
- [ ] **Deployment guide** - Production setup instructions
- [x] **HF Hub model card relicensing** (2026-05-22, commits `fb67d05` + `41d2108`, #65 closed). Source-side: `upload_to_huggingface.py:28` now declares `license: eupl-1.2` in the model-card YAML frontmatter. Hub-side: one-shot script `scripts/deployment/relicense_hub_repos.py` walked all 14 `jeergrvgreg/*` repos and rewrote the frontmatter `license:` line; verified post-upload on 3 repos (public uplifting-filter-v5, private belonging-filter-v1, private sustainability-technology-v3). Repo LICENSE + pyproject + upload template + 14 Hub model cards now all carry EUPL-1.2 consistently.
- [x] **deploy_to_nexusmind hardening: refuse-on-dirty + explicit staging** (2026-05-23, commits `4cf75dd` + `dd11727`). Fix for the origin-contamination hazard discovered during the 2026-05-22 belonging deploy: `git add -A` on NexusMind's working tree swept ~1,400 lines of unrelated story-dedup WIP into commit `7a595c4` and pushed it to origin without the author's review. Both `.sh` and `.ps1` now do (a) pre-flight `git status --porcelain` refuse-on-dirty check with `--force-dirty`/`-ForceDirty` escape hatch, and (b) explicit `git add $FILTER_PATH filters/common/` instead of blanket add. Printed server-pull instructions also corrected (sadalsuud at `~/local_dev/NexusMind`, gpu-server deploy via `bash scripts/deploy_filters.sh` from sadalsuud — not `git pull` on a stale `llm-distiller` hostname). Cross-referenced with NexusMind-side gotcha-log entry and `b12d554` documentation commit.

---

*Last updated: 2026-08-01*
## 2026-08-06 evening — four owner decisions taken, three backlogs closed

Session was decision-bound, not work-bound: three calls were blocking #87, #93 step 4
and #98, and a fourth (naming) had been re-scheduled through four version bumps.

- [x] **#95 step 2 — noise becomes a band.** See the corrected entry below; "pin a batch size" was not an option.
- [x] **#98 criterion 4 + package parity.** cd v6 can now score. Two prerequisites remain and neither is doable from a laptop — see "Next session".
- [x] **#94 — static invariant shipped.** `tests/unit/test_gatekeeper_invariant.py`: any filter declaring a gatekeeper must have `GATEKEEPER_CAP` **below** its medium tier threshold, or it cannot change visibility (the only outcome a filter has under ADR-016/ADR-022). Reads both values off the **scorer class**, never config. Catches cd v5 (cap 4.0 == 4.0) and solutions v6 (cap 3.0 > 2.25); both are EXEMPTIONS entries that must keep matching a real violation. cd v6 drops its gatekeeper entirely, so that exemption dies when cd v6 goes live.
- [x] **#97 assessed and remedied.** See the corrected CARVE-OUT 1 entry below.
- [x] **#88 items 2-4.** nature_recovery v4's `3.225` marked documentation-only (runtime `DEFAULT_THRESHOLD = 0.75`); its raw `high` tier 7.0 documented as structurally dead (calibrated ceiling 6.8) but KEPT, since ADR-022 reassigns tier on the normalized score where the band is reachable; investment_risk v6 tiers aligned to runtime (`medium` 3.0 → 4.0, declared `medium_high` 5.0 removed — the runtime has three tiers). **Item 1 (`stage_used` into row attributes) is NexusMind-side** and shares a root cause with ducroq/NexusMind#300.
- [x] **#84 v7 corrections written** next to the v6 prompt, not into it (`prompt_hash` is stamped into every scored result). The router points at a disposition that does not exist: "does NOT pass Step 1 → route to Flag A", but Step-3 flags apply only to articles that *passed* Step 1. Fix is a distinct **A2 `action_without_outcomes`** flag whose carve-out requires measured outcomes rather than committed resources.
- [x] **#99 closed by removal** — `DISCOVERY_PATTERNS` went with the keyword gate.
- [x] **ADR-012 rename backlog CLOSED.** Two cancelled, one confirmed, one named and scheduled. The ADR needed a third clause: its obvious reading is "rename to the lens name, or don't", a binary with no room for `{qualifier}_{lens}` — which is what left `uplifting` unresolved for five months.
- [ ] **NOT done, and deliberately: #87.** Unblocked now (it was waiting on #95) but not folded into #98 — that issue was scoped *probe first, dimensions later*, and merging them makes any change in the numbers unattributable.

**Self-review caught one of my own errors:** the ADR-012 amendment first said "five scheduled renames, one carried out". It is **four** — `belonging` "already matches" is not a rename and wisdom/education were never built. Corrected in the ADR before commit.


## 2026-08-06 — cd v6 probe (#98), the English escape hatch (#99), and an instrument for FS#120

- [x] **#98 probe trained and measured; all three acceptance criteria pass.** `filters/cultural_discovery/v6/`. Held-out oracle labels (test split, 75 MEDIUM+ positives): probe @ 2.50 FN **0/75**, keyword gate **10/75**. Production, 64 cycles / 156,226 rows / 2,653 surfacing, both arms in one pass over identical rows: surfacing blocked **337 (12.7%) → 1 (0.04%)**, high-tier **0 → 0**, every language except Portuguese at 0.0%. Full write-up in that directory's `STATUS.md`.
- [x] **Threshold is 2.50, not `train_probe.py`'s 3.025.** The trainer selects off the **val** recall curve, so val FN is optimistic by construction — it reported 1.3% where held-out gives 6.7%. Val and test independently both give FN 0.000 at ≤ 2.50 (0/152 positives).
- [x] **Two self-corrections, both recorded in the package rather than only in chat.** (a) Criterion 2 is a **regression** — on production the probe screens 63.7% against the gate's 70.2%; an earlier claim of parity came from the test split, which does not transfer (label set is 9% MEDIUM+ against a 1.7% production surfacing rate). (b) **Four of the five held-out positives** recovered by the lower threshold read as **off-lens** on inspection, so the FN gain is partly #87's lens dilution appearing inside the labels. 2.50 rests on recall being Stage 1's job, not on those five being losses.
- [x] **The probe is batch-invariant** — max |Δ| **3×10⁻⁶** across shuffled order, chunk 256→97, encode batch 64→1; zero threshold flips. Unlike student scores (#95, |Δ| ≤ 0.162), a probe decision is reproducible. `scripts/gate/probe_batch_invariance.py`.
- [x] **#98 criterion 4 EXECUTED 2026-08-06 evening** (owner call). Keyword gate, four exclusion categories and three domain blocklists deleted; `prefilter.py` 800 → ~90 lines, commerce-only pass-through on the ADR-018/019 declarative shape. `classify_content_type` deleted too — grepped first, only callers were each cd version's own self-test. **Package parity also reached**: three inference modules added, `calibration.json` copied from v5 (correct — the student is unchanged), `score_scale_factor` corrected **1.2829 → 1.0**, `normalization.json` still deliberately absent. `verify_filter_package.py` 7/7 offline.
- [x] **#99 filed** — `DISCOVERY_PATTERNS` is an English-only escape hatch: 66/516 English surfacing articles pass the cultural gate on lens-neutral science-journalism words, 0/265 non-English, all 66 read and none cultural. Also feeds `classify_content_type`, which a probe does **not** replace.
- [x] **FS#120 (~08-14) answered; the measurement is ours.** `pre_enrich` fires at **500**, not 300 (`config/app.yaml:171`). Their proposed denominator confounds enrichment success with native article length — supplied a third, conditional instrument. Blocking them back: `eval_query` is stamped on **28 of 547** eval rows, so their "drop Chad, keep Tchad" cut is unexecutable; and three of eight arms project to n≈13–35 by the 14th.
- [x] **ducroq/NexusMind#300 filed** — the #93 `content_length` stamp is computed by the scorer and lost before persistence: **0 of 50,605** rows carry it, though the deployed code is md5-identical to the repo. ADR-022's stamp half is not holding. Does **not** block FS#120.
- [x] **Four SSH-dependent verify assertions re-run** after slipping three curate passes; all PASS. Obituary blocked count 1208 → 2573 with no gap; rescore reproduces 07-31 to four decimals.
- [ ] **sadalsuud carries the pre-`80dd399` cd gate** (235 topic stems vs 453). Zero production effect — that prefilter does not run (NexusMind#284) — but flipping enforcement without syncing restores the exact skew #86 removed. Recorded on #86 as a trap; **do not close it by syncing**, since #98 deletes the file.

## 2026-08-05 — TDM / training-data position, and the two carve-outs it leaves open

- [x] **#28 decided — AI-crawler opt-out directives do not bar distillation training.** Record: `docs/decisions/2026-08-05-tdm-opt-out-training-data.md`. Grounds, strongest first: the directives name **other parties' crawlers** (of 333 flagged domains: GPTBot on 286, CCBot 270, Bytespider 235, ClaudeBot 231, Google-Extended 230 — we operate none; **corrected 2026-08-06, the first figures counted matching lines, not domains, and GPTBot's 401 exceeded the 333 total**); the student has a **regression head and cannot emit text at all**, so no output can substitute for a publisher's work; and the use is referral, not substitution. Sibling decision for the fetching layer is ovr.news ADR-043. **Recorded against itself:** *"modelling is not mining"* is not a distinction the DSM Directive draws — its TDM definition covers fitting a model to text. The position rests on the **Art. 4(3) reservation** question and on harm, not on being outside the definition; do not carry the shorter phrasing forward.
- [x] **#28's numbers were stale** — it cited 238/971 domains from March; the 2026-08-04 scan says **333/1,357**. Also **117 domains failed open** (unreachable, counted as clean) — a publisher behind a WAF that 403s non-browser agents scores clean, and that is exactly the publisher most likely to be reserving. Any future "we checked" is only as strong as those 117.
- [x] **CARVE-OUT 1 ASSESSED 2026-08-06 (#97).** Models clean: **zero of the 333 opted-out domains carry a `User-agent: *` reservation** — every signal names a third-party crawler we do not operate — so grounds 1-3 cover the already-trained filters with nothing left over. Overlap is real but irrelevant to that conclusion (solutions v6 29.5% of training rows, nature_recovery v4 14.6%). **Q2 did NOT come back clean**: the Hub is fine and splits are gitignored, but 812 committed JSONL rows carried full article bodies in a PUBLIC repo. That is republication, not mining — grounds 2-3 are silent on it. **Remedied the same day** (owner: truncate in place): 45 files, 834 rows, **1,889,627 chars removed**, capped at 300. Does NOT unpublish — the text remains in public git history; history was not rewritten.
- [x] **CARVE-OUT 2 — the oracle ships full article text to third parties.** Gemini Flash (Google) and DeepSeek receive complete article content under their own terms. None of the three grounds cover it, and ground 2 specifically fails because **the recipient is a generative model**. **Owner decision 2026-08-05: risk identified and knowingly accepted** — *"this is the only way I can do this, so if someone objects in future, let's see then."* Recorded with revisit triggers in `ovr.news/docs/compliance-register.md` §3 (it lives there because the summarisation path makes the same transfer; this repo is one of two callers).
- [ ] **The `tdm_opt_outs.json` scan is unscheduled.** It has run exactly once (2026-08-04). A reservation added tomorrow is invisible. Quarterly is enough for a signal that moves this slowly — the implementation sketch in #28 is retained there as the thing to build **if this decision is ever reversed**, not as work to do now.

## 2026-08-02 — Chain 4 measured: two of the previous day's own P0 conclusions overturned

Both P0 issues carried into this session had the **mechanism right and the target wrong**. Neither correction needed new tooling — one came from widening a sample, the other from reconciling a denominator.

- [x] **NM#285 measured, resolved as Option B** (`89f2e5b`, NexusMind main). Same-row full-vs-truncated replay, 4 cycles, n=8,283. Truncation effect: nature_recovery **+0.0000**, solutions **+0.0000**, cultural_discovery +0.0005, belonging +0.0008, uplifting +0.0028, investment_risk +0.0097. **The 0.638–0.649 cluster is NOT a truncation artifact.** Option C declined — its cost saving came almost entirely from the length floor, the one rule we now have evidence against enforcing; Option A buys a rounding error. Shipped instead: every shadow line carries `contract=title+content`, `pre_source_filter=true`, and `INCOMPLETE(inert:url,source)` derived from declared rule containers (not a hardcoded list), verified to flag exactly the four filters with a non-zero measured effect.
- [x] **Real cause of the cluster found.** `nature_recovery v4` and `solutions v6` prefilters are **pure length floors** — both declare `EXCLUSION_PATTERNS = {}` by design (commerce upstream, ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides, a no-op with nothing to override. Zero lens blocks across 8,283 articles. `expected_pass_rate` **deleted** from both (`3ed47e1`), not corrected — 0.644 is "fraction of articles ≥300 chars", a corpus statistic, not a lens spec.
- [x] **Larger, opposite-signed defect found underneath**: the shadow denominator counts articles `source_filter` discards *after* scoring. investment_risk logs 0.642 while the rate on articles that can reach production is **0.770** — 13× the truncation effect, other direction.
- [x] **LD#92 — IDENTIFIED 2026-08-05, supersedes the n=60 caveat below.** The two discriminating tests the 08-02 review demanded were run, predictions pre-registered in the sampler before any oracle call. **D3 (matched percentile depth, where the selection artifact is largely removed) is the LARGEST effect, not the collapse toward zero the artifact predicted** — see the cap entry below for the numbers. Second oracle confirms. Two bookkeeping defects in the first write-up were caught by the newly-adopted `/review-changes` skill and corrected: the p-values were article-level permutation (anticonservative under source clustering) and the verify command's data was never committed. Both fixed; fixtures now in `tests/fixtures/ld92/`.
- [x] **NM#286 items 1+2 shipped together** (`23a9068`, NexusMind main): `pipeline.commerce_prefilter.enforce` (default **true** — unlike obituary's false, so a config predating the key cannot silently open a live gate), and `enrich_survivors.py` now reads the same key instead of re-deciding. 920 tests green.
- [x] **LD#86 answered — DO NOT FLIP.** cd's rate matches its declared 0.25, but enforcing it costs **15.5% of surfacing articles** (135/871 over 20 cycles), 0% of high tier. **A matching pass rate and safety-to-enforce are independent properties.** The "skewed non-English" framing is **corrected**: German 4.9% / French 5.3% are blocked *below* English's 13.0%, so pooling was wrong. The entire gap is one rule — `no_cultural_topic_signal`, 9.9% en vs 19.2% non-en, while the other three fire *more* on English. It is uneven `TOPIC_GATE_PATTERNS` keyword coverage, which is fixable and falsifiable.
- [x] **Chain 4 root — length floor split out of the per-filter prefilters (#93)** — LD side shipped 2026-08-03. `apply_filter()` no longer gates on length in any filter; the floor moved to `make_oracle_prefilter` (labelling-time, where the framework-leakage rationale lives); every scoring result carries a `content_length` stamp; one config-gated `short_content.cap` exists and is **off everywhere**. A/B over 2,917 production rows: the oracle verdict is **byte-identical** for five of six filters (cd is the intended exception, above). **Still open:** sync `filters/common/` + the six prefilters to NexusMind, then re-run the NM#284 shadow — its pass rates will jump, and for the first time they will describe lens behaviour rather than a length floor (what LD#90 item 2 needs).
- [ ] **Fit the solutions short-content cap** (#93 step 4) — **#92 no longer blocks it; #95 still does.** The second-op-point re-run ran 2026-08-05 and the defect is **identified**: D1 (both arms ≥2.25) −0.790, D2 (≥4.00) −0.861, **D3 (matched percentile depth) −1.119** [−1.61,−0.61], cluster-bootstrap p Holm-corrected 0.0032 / 0.0012 / <1.5e-4. The selection artifact predicted D2 markedly more negative and D3 → 0; D2 moved −0.071 and D3 is the *largest*. A gemini-2.5-flash cross-check on the same D3 sample gives **−1.351** [−1.73,−0.96] — two oracles with clearly different absolute bias, same gap, which rules out "the judge penalises short input". Harness + fixtures committed (`scripts/diagnostics/ld92_*.py`, `tests/fixtures/ld92/`). **Remaining blocker is Batch F.1 (#95)**: the cap value is a threshold fit and inherits the |Δ| ≤ 0.16 batch-composition noise floor. Also weigh the recall cost against NM#231/#292 before setting a value — `gn_africa_*` / `gn_asia_*` feeds lead solutions' short-and-clearing list.
- [ ] **Reader-reported defects 2026-08-03, filed upstream — all three land outside this repo.** A single reader complaint about ovr.news decomposed into three defects in three different repos, which is the clearest instance yet of "the repo where a symptom appears is not the repo that owns the fix":
  - **FluxusSource#124** — feed titles/content stored with UTF-8→MacRoman mojibake (`años` → `a√±os`). **5.0% of articles** (463/9,343 in one day), concentrated in `baltic_lrt` / `spanish_*` / `vietnamese_*` / `german_*`; English essentially unaffected, which is why English spot-checks never saw it. Present in FluxusSource's own collection file before NexusMind reads it. **Relevant here:** it degrades multilingual embeddings, so it touches any cross-language work this repo does.
  - **NexusMind#290** — hero extraction publishes third-party page chrome (a Google Play badge) as the article image; reproduces on current code *with* NM#287 in place. No cross-domain check exists. Compounded by `hero_validation_cap: 200` against ~968 heroes/run, so ~79% are never validated and visibility of the defect is a lottery.
  - **NexusMind#291** — cross-source dedup threshold 0.88 sits above where genuine same-story pairs land (**measured 0.8355** on a confirmed RU/ES pair, `multilingual-e5-large`, title-only). Method note: the mojibake was my first hypothesis for this and was **measured and refuted** — repairing the encoding buys +0.013, nowhere near the gap.
- [x] **#95 step 2 SETTLED 2026-08-06 — and "pin `batch_size`" was never an available option.** `DEFAULT_BATCH_SIZE = 16` (`filters/common/filter_base_scorer.py:50`) is already fixed and never varies in production; the variable is batch *composition*, which the seeded shuffle already addressed. Owner decision: **budget for the floor, do not try to remove it.** An article predicted within **0.16** of the surfacing threshold is *indeterminate*; every metric at that threshold carries a band, and **two models whose bands overlap are NOT DISTINGUISHABLE**. `scripts/gate/ground_truth_gate.py` computes and prints it (`--noise-floor`, default 0.16; `0` reproduces prior runs). Worked example — solutions v6 on its own held-out test set, 19/1,032 indeterminate: **F1 0.739 [0.712, 0.771]**, recall 0.671 [0.659, 0.707]. **This unblocks #87 and #93 step 4**, which only needed a stated rule for what counts as a difference. NOT attempted, still open: whether fixed-length padding would make scores batch-invariant.

- [ ] **Price the upstream fix before the downstream one (NEW 2026-08-05).** Google News is 14–17% of scored articles but **48–56% of all sub-300-char stubs** (~3× over-represented, measured within-period over 149,075 solutions v6 rows / 80 cycles). Pre-enrichment already rescues ~62% and fires below **500** chars — the net is not too small; GN survives because its `url` is a `news.google.com/rss/articles/…` redirect, so the fetcher retrieves Google's redirect page. **Retiring the GN proxies removes roughly half the population the solutions cap exists to handle, at no recall cost to genuine articles.** That decision is FluxusSource#120, due **~2026-08-14** — the only calendar-bound item on the board. Evidence and a suggested `enrichable rate` readout column posted there. Sequence: FS#120 → then size the cap against what remains.

- [ ] **Does the scorer share the summariser's fixed-budget failure? (NEW, ovr#299)** For English sources, summary content words absent from the article *and* title run 31.6% (1000+ chars) → 73.9% (120–299) → **83.4% (<120)**, monotone over 18,756 summaries. The mechanism there is a fixed output length target (medians 1159/968/875/1065 against a 40× input range) that the model fills — compressing an article, generating from a headline. **Open for this repo: whether the student has an analogous behaviour, or whether its short-content error is purely vocabulary-without-subject.** The fixes differ — one is a budget, the other a cap — so this is worth one experiment before building either.
- [x] **#93 synced to NexusMind** 2026-08-03 (`c932065` content, `c1df13c` record; 950 NM tests pass). Surfaced and fixed a second drift — `investment_risk v6` blocked `arxiv`/`mastodon_`/`bluesky` in NexusMind since 2026-05-18 and never upstream (`e51309d` ports them back). **Diff both copies before every sync**; `.nexusmind-owns` is empty so nothing else compares them.
- [ ] **`foresight v1` still floors on length** — the one prefilter left calling `check_content_length` inside `apply_filter` after #93. Deliberately out of scope (PARKED, merged into solutions #43, not in the production set), but fix it at the same time as any un-parking so it does not silently re-inherit the shape #93 removed.
- [ ] **Re-run the NM#284 shadow** now that the length floor is out of the prefilters *(deployed to gpu-server 2026-08-03 ~15:45 CEST, rev `2d5c54aa…`; first cycle carrying it is 16:10)* — its pass rates finally describe lens behaviour, which is what LD#90 item 2 needs. Rates measured before 2026-08-03 are not comparable to ones measured after.
- [ ] **NM#286 item 3** (violence stamping skipped in single-filter / `--no-dedup` / dedup-exception runs). Verified in code; **live blast radius zero today** (production runs multi-filter, violence `enforce: false`), so it is an audit gap, not admitted violence. Still a hard prerequisite for any violence enforce flip, with LD#82.
- [ ] **Fix `no_cultural_topic_signal` multilingual coverage**, then re-run the identical LD#86 recall check — falsifies whether the language skew is the gate or the corpus.
- [x] **Retitle/relocate LD#92 to solutions** and correct the op-point in its body — done; the issue now reads "solutions v6 over-scores sub-300-char stubs (DiD −1.13) — NOT uplifting; original n=15 result did not replicate".

## 2026-08-01 — NM#281 gate contract + adversarial review of the day's own work

- [x] **NM#281 gate-contract harmonization** — shipped `0fd462b`, **corrected `b85a467`**, deployed. `_commerce_model` / `_violence_model` stamps; `pipeline.violence_promotion.enforce` (default false); `violence_blocked` accounting. Ships inert.
- [x] **Five-lens adversarial battery over the same day's changes** — found 2 blockers, both mine, both invisible to the tests shipped with them:
  1. **The violence gate could never fire.** Placed in `_is_duplicate`, which runs *before* violence stamping; `enforce: true` would have dropped 0 while logging `0 violence`. Commerce/obituary work there only because their preprocessors rewrite the input JSONL first. Fixed: drop moved to `_enforce_violence_promotion()` right after stamping; dead check removed; ordering asserted structurally (AST).
  2. **The shadow loader armed a dead branch.** Leaving `target.prefilter` populated makes `HybridScorer`'s third guard clause truthy — constructing the wrapper flipped a `use_prefilter=True` hybrid to blocking with null scores. Now restored to `None` after capture.
  Also fixed: the `MODEL_VERSION` getattr default was itself the v1-claiming bug the stamp prevents (→ `"unknown"`); shadow errors were dead code so a broken shadow logged nothing; digit-collapsing fragmented the histogram it existed to unify. **978 tests green** (was 969).
- [x] **NM#285 — RESOLVED 2026-08-02.** Measured: truncation is +0.0000 to +0.0097, so the cluster was never an artifact and the ~0.59 reading below was wrong. Option C **declined** on the measurement (see the 2026-08-02 section). Option B shipped `89f2e5b`.
- [x] **NM#286 — items 1+2 shipped 2026-08-02** (`23a9068`); item 3 still open and still blocks any violence enforce flip.

## 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected

- [x] **ovr#280 "upstream never sends cluster_id" — REFUTED 2026-08-01.** Measured on the live 12:4x cycle: **7,629 / 16,128 rows (~47%)** carry `nexus_mind_attributes.<lens>.source_quality.cluster_id`, with `corroborating_sources` + `other_sources` on exactly the same rows; present in the 2026-07-22 files too. The diagnosis had sampled `metadata.quality` (FluxusSource's block — its key list `bias_category, credibility_score, source_tier, type_classification` is quoted verbatim in the issue) instead of the per-lens NexusMind block one level deeper. **No NexusMind change needed**; ovr#280's Option A is already done, and the break is downstream between the JSONL and their DB. Posted to ovr#280.
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

## 2026-08-01 — Post-deploy verification + NM#284 (prefilters never ran in production)

Verification of the 2026-07-31 deploys: **refits and the NM#280 tier gate both green** (closed NM#279, NM#280, LD#74, LD#76). The third check — LD#86's cultural_discovery topic gate — was red, and the cause turned out to be architectural rather than cd-specific: **per-filter prefilters have never run in the production scoring path** since 2026-02-10. See the NM#284 items below and `memory/calibration-history.md` Dead Ends (two new entries).

## 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)

Full synthesis: LD#76 issuecomment-5140079896. Headline: **no shared root cause, no scale-collapse anywhere, no retrains needed**. `% norm < 0.5` retired as health metric (≈ 1−base-rate by construction; healthy investment_risk is itself 75% "invisible" by it). Healthy criteria going forward (from ir reference): raw p90 above op-point + populated spread-out MEDIUM+ band + separation intact + anchored fresh fit.

- [x] **uplifting v7 normalization refit** (NM#279) — **EXECUTED 2026-07-31**, **VERIFIED LIVE 2026-08-01**: raw 5.00 → norm ≈5.18 (was ~3.0), `percentile` on 2647/2647 rows. NM#279 closed.
- [x] **belonging v1 normalization refit** (NM#279 / #74) — **EXECUTED 2026-07-31**, **VERIFIED LIVE 2026-08-01**: MEDIUM+ p90 norm 8.71 (n=205 over 3 cycles), visible share 1.03% → 2.68%. NM#279 + #74 closed.
- [x] **NexusMind `_assign_tier` double-cut (NM#280)** — **DEPLOYED 2026-07-31, VERIFIED LIVE 2026-08-01**: `count(tier != low) == count(raw >= op-point)` holds exactly for all six live filters across six consecutive cycles (live from the 07-31 12:5x cycle). Restored visibility: uplifting +196%, ir +70%, belonging +82%, cd +67%, solutions +33%, nr +33%. Caps path untested in production (0 caps applied in these cycles). NM#280 closed.
- [ ] **cd v5 dead prefilter (#86)** — the gate is **correct and now production-validated, but still not enforced**. Verified 2026-08-01 by NM#284 **in-path** shadow measurement on the 12:46 cycle: **0.255 observed vs 0.25 declared (n=2099, full cycle)**, matching the fix's own offline validation (0.245 on 14,923 rows). *(An earlier claim here — "production stamps 2647/2647 pass, replay gives 28.8%" — was retracted: that baseline came from `filtered_*.jsonl`, which only receives `passed_prefilter: true` rows, so it is 100% passers by construction. See NM#284 issuecomment-5151154862.)* **Root cause is not cd-specific: the per-lens rule prefilter has never run in production** (NexusMind `deploy/gpu-server/main.py` L915 `use_prefilter=False` + L1318 `skip_prefilter=True`, since `66582e7`, 2026-02-10). e5 probe, commerce/obituary/violence, and the NM#189 source allowlist all verified running. Filed **NM#284**. #86 closes when NM#284 stage 3 flips cd to enforcement — the fix itself needs no further work.
- [x] **NM#284 stage 1 — shadow measurement** — **IMPLEMENTED + DEPLOYED + VERIFIED LIVE 2026-08-01** (`cd4fc6d` + `5d53774`, deployed ~11:59 CEST). `ProductionScorer` loads each filter's prefilter via the `_load_prefilter` hook (without flipping `use_prefilter`, keeping evaluation and enforcement separate levers) and logs observed vs declared pass rate. Enforces nothing; no schema change. Rollback `NM_FILTER_PREFILTER_SHADOW=0`. First cycle (12:46): **cd 0.255 vs declared 0.25 — LD#86 gate validated in production**; uplifting 0.525 vs 0.20; solutions 0.591 vs 0.20; ir 0.589 (no declared rate). Two defects the first live run exposed and fixed: drift judged at n=1 (smoke test scores one article/filter → six false "gate appears inert" alarms; now `MIN_SHADOW_SAMPLE=50`), and `expected_pass_rate: ~0.25` parsed as a YAML *string* and silently dropped.
- [ ] **NM#284 stage 1b — per-row shadow stamps into the JSONL**: needs `prefilter_shadow_pass` / `prefilter_shadow_reason` plumbed through gpu-server `main.py` (Pydantic `FilterScoreResult` drops unknown keys at the service boundary) → `src/scoring/gpu_client.py` → the `analysis` dict in `scripts/main.py`. Blocked on unrelated uncommitted WIP in `scripts/main.py` (image-classifier thresholds, NM#282) — staging it would sweep that in. Log-based measurement is sufficient for the enforcement decision, so this is a convenience, not a blocker.
- [x] **NM#284 stage 2 — global short-content gate before fan-out — REFUTED, DO NOT BUILD** (2026-08-02, superseded by #93 2026-08-03). The ~25%-of-inferences saving was real but it is bought by dropping content the oracle validates at the same rate as long content (uplifting: 67% short vs 65% long above the op-point), and the loss skews to the `gn_*` / `spanish_*` / `french_*` population NM#231 already flags as under-served. The floor is now a labelling-time precondition plus an off-by-default per-filter cap (#93), not a gate at any level. See `memory/calibration-history.md` Dead Ends before proposing this again.
- [ ] **NM#284 stage 3 — per-filter enforcement flip**, once a few cycles of shadow data exist. cd is the only filter whose observed rate currently matches its declared one, and it is also the one LD#86 needs. Op-point / normalization re-derivation for affected filters is downstream of the flip (gates #87).
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [x] **#75 CLOSED as measurement artifact 2026-07-31** (owner confirmed) — nature_recovery v4 is healthy.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) **The rename half is CLOSED as of 2026-08-06 — do not re-open it here.** ADR-012 amended: `cultural_discovery` and `nature_recovery` KEEP their names (their Hub repos are public standalone artefacts; `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about), `solutions` confirmed as-is, and `uplifting` → **`human_thriving`** at v8 — not bare `thriving`, which is an existing parked directory. What remains under #90 is the template half only.
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **`human_thriving` v8 — acceptance criteria (owner decision 2026-08-07).** Two open scorer-fidelity defects in `uplifting v7` are **not** separate work: they die in this retrain or they do not die. Both become held-out eval slices, judged under ADR-021 against oracle ground truth, and both carry #95's ±0.16 band — an article predicted within 0.16 of the op-point is indeterminate and cannot be counted as a pass.
  1. **#91 — dominant subject.** v7 scored a child-trafficking investigation raw **6.77**; it led the homepage with a trafficking price list as pull quote. The scorer rewards narrative fragments over what the article is *about*. Adverse examples are curated at `datasets/adverse/uplifting.jsonl` (`5be62dd`) — **2 records** today (6.7661 and 5.8601), so the slice must be grown before it can gate anything. **Criterion: every adverse record scores below `max_acceptable_wa`**, which the file itself declares as **3.85** (p90 of its reference population) — *not* the 4.0 op-point; the two are different bars and the file's own bar wins. Note both records are labelled `"editorial judgement … NOT oracle-scored"`, so this criterion is judged against an asserted upper bound, not against ADR-021 oracle ground truth — say so rather than implying otherwise.
    *Denominators, kept separate on purpose:* "median 1.36 / p90 3.85" is over **1,947** scored uplifting articles in `filtered_20260801`; the "6th of 3,530" ranking is a different, unstated population. Both derive from `data/filtered/uplifting/*.jsonl`, which is **100% passers by construction and drops source-type-excluded rows** — neither figure is currently re-derivable locally (the NexusMind mirror ends at `filtered_20260726`).
  2. **ducroq/NexusMind#231 — non-English under-scoring.** 19 panel-confirmed reader-facing documented-outcome articles score **3.52–4.42, median 3.74**, against a **4.0** op-point. **They are NOT mostly inside the noise band** — an earlier draft of this entry claimed that; ±0.16 around 4.0 is [3.84, 4.16], and every article listed in the issue is ≤3.74, missing by 1.6× the band at the median. The gap is real and larger than noise, which makes it a better criterion, not a worse one. **Blocker on using it at all:** the evidence file NM#231 describes as "(committed)", `data/held-out/golden-uplifting-2026-06-12.jsonl`, is neither on disk nor tracked in git — **the slice this criterion names cannot currently be enumerated.** Recover or rebuild it first. Note also NM#231's sample is drawn from a `weighted_average ∈ [3.5,4.5]` band with a ≥500-char floor (selection *into* a band around the op-point) and is measured against a "~5.0 hot-DB floor", not 4.0 — state which quantity the criterion means. **Criterion: the 19 clear the op-point, and the English/non-English mean-score gap is reported on one denominator** — not "improved", reported, so v9 has a baseline.
    This is Chain 14's *scoring* stage. It is **not** "the only stage not resolved" — an earlier draft said so and this repo's own board contradicts it: FS#124 (collection) and NM#291 (dedup) are both open and banded P1. Gating (#86) is the one that is measured and decided.
  Note the interaction: #91 wants the scorer to attend to the dominant subject, NM#231 wants it to stop discounting non-English framing. Neither is a threshold move, and a threshold move would trade them against each other — do not resolve either by shifting the op-point.
- [ ] **NM#231 re-measure after uplifting refit** — non-English under-scoring is real but secondary; size the residual model-side gap before considering v8 work. *(2026-08-07: superseded in scope by the v8 criteria above — the re-measure is now a v8 acceptance test, not a prerequisite study.)*
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question).

## 2026-07-27 Session — Small LD Issues Closed

- [x] **LD#49** — Remove 6 broken/superseded filter version dirs (`3e1ccec`). −61,314 lines.
- [x] **LD#68** — Add per-dim `description` field check to `verify_filter_package.py` (`c2ab571`).
- [x] **LD#63** — Branded/sponsored URL path blocking in uplifting v7 prefilter (`623ea51`).
- [x] **LD#57** — Schema gate for `source_filter:` block. Already implemented; closed.

## #52 belonging v1 migration notes (2026-04-29)

Belonging is the second prefilter migrated to ADR-018 declarative shape.
Diverged from sustech v3's "fully declarative" template in two ways:

1. **Data shape only.** Exclusion patterns moved into `EXCLUSION_PATTERNS`
   dict (compiled once by base `__init__`); per-category counts dropped from
   `get_statistics()` and rebuilt from the dict. Iteration order preserved.
2. **Custom apply_filter retained.** Belonging uses per-category
   positive-signal thresholds (3/3/3/2/3/2/special), not BasePreFilter's
   binary `OVERRIDE_KEYWORDS` bypass. Plus URL-based domain exclusions and
   the obit `pos>=1`-floor-when-exception-present rule. None of that fits
   the standard `apply_filter()` pipeline; ADR-018 explicitly allows
   "custom form" for this. The harmonization is at the *data* layer; the
   *control* layer stays specialized.

`POSITIVE_PATTERNS` class attr was kept (shadows `BasePreFilter.POSITIVE_PATTERNS`)
so base compiles it into `_compiled_positives`. `POSITIVE_THRESHOLD` stays at
0, so base's `_has_override` never reads it — belonging consumes the
compiled list directly via `count_pattern_matches`. Documented at the class
attr.

Pattern preservation verified by counts (9/7/9/9/7/6/11/6 exclusion
categories; 10 exceptions; 12 positives; 9 multilingual positives — all
identical to baseline) and 19/19 self-test pass.

No downstream consumers reference the renamed private attrs (verified via
grep across the repo); only the public class symbol + `apply_filter()`
contract are used by `base_scorer.py` and `verify_belonging_v1.py`.

## #52 cultural-discovery v4 migration notes (2026-04-29)

CD v4 is the third migrated prefilter. Same partial-declarative shape as
belonging — exclusion data harmonized, custom `apply_filter` retained.
But the divergence from base differs:

1. **Per-category exception lists.** Each exclusion category
   (appropriation_debate, political_conflict, tourism_fluff, celebrity_art)
   has its own escape-hatch list — celebrity_art has philanthropy /
   repatriation exceptions, political_conflict has reconciliation / peace
   exceptions, etc. BasePreFilter's single `OVERRIDE_KEYWORDS` slot is
   global; CD's exceptions are category-scoped. Modeled with a parallel
   `EXCEPTION_PATTERNS_PER_CATEGORY` dict keyed by exclusion-category name,
   compiled in `__init__` into `_compiled_exceptions_per_category`.

2. **classify_content_type method preserved.** Distinct from apply_filter
   — used (currently only by self-tests, but kept for API stability) to
   tag articles as `cultural_discovery` (>=2 positive boost matches) or
   one of the four exclusion categories or `general`. Rewritten on the
   new dict-based structure.

3. **CULTURAL_DISCOVERY_BOOST_PATTERNS → POSITIVE_PATTERNS.** Same trick
   as belonging: rename so base's `__init__` compiles them into
   `_compiled_positives`. POSITIVE_THRESHOLD stays at 0, so base's
   `_has_override` never reads them — only `classify_content_type` does.

4. **Surfaced bug: missing content-length check.** v3's `apply_filter`
   called `check_content_length` first; v4's does not. Looks like an
   unintentional regression when v4 was created. **Preserved as-is in
   this migration commit** (scope: zero behavior change). Tracked above
   under "Prefilter Quality" as a separate one-line fix at next CD bump.

Behavior preservation verified by 10/10 self-test pass plus identical
pattern counts (11/14, 17/12, 15/14, 15/14 across the four categories;
12 positives; 8/4/6 domain counts).

No downstream consumers (verified via grep): only `base_scorer.py`
references `CulturalDiscoveryPreFilterV4` as a class symbol +
`apply_filter()` call. Older CD versions (v1/v2/v3) keep their old
attr names internally — no cross-version import.

Next: uplifting v7 (flat-list-per-category, pattern-pair override — no count).

## #52 uplifting v7 migration notes (2026-04-29)

Uplifting v7 is the fourth migrated prefilter. Same shape as CD v4 for 3 of
4 categories, with one extra wrinkle: a count-based block.

1. **Three pattern-with-exception categories.** corporate_finance,
   military_security, crime_violence — all use the
   `EXCLUSION_PATTERNS` + `EXCEPTION_PATTERNS_PER_CATEGORY` pair, identical
   to CD v4's structure.

2. **One count-based block (pure_speculation).** Doesn't fit the
   pattern-with-exception shape. Outcome-evidence patterns are a parallel
   *count* check, not a per-pattern exception. Kept as separate
   `SPECULATION_PATTERNS` / `OUTCOME_EVIDENCE_PATTERNS` class attrs;
   inline check after the exclusion-dict iteration:
   `speculation_count >= 3 AND outcome_count == 0`.

3. **classify_content_type preserved.** Has a custom first-check ordering:
   "peace_process" wins when both military_security pattern AND its
   exception fire (e.g. military buildup article that's actually a peace
   accord). Standard category iteration follows. Speculation classification
   uses a looser threshold (>=2 / <=1) than apply_filter (>=3 / 0).

4. **Subclass ThrivingPreFilterV1 verified.** `filters/thriving/v1/prefilter.py`
   inherits from UpliftingPreFilterV7 with only a VERSION override. Public
   API preserved, so the subclass still works post-migration (verified with
   a smoke test exercising all 4 categories).

5. **Surfaced bug: multilingual `\b` boundary leak.** Dutch `munitie`
   (without `\b`) matches inside English "communities". Pre-existing v7
   FP — preserved here, tracked separately under Prefilter Quality.
   Same bug shape as the RIP/rip-current case (#45). Audit all 3
   multilingual exclusion lists at next uplifting version bump.

Behavior preservation verified by 12/12 self-test pass plus identical
pattern counts (21/11, 19/18, 37/25 across the three pattern-with-exception
categories; 7 speculation; 6 outcome-evidence; 8/4/6 domain counts).

No additional downstream consumers (verified via grep): only
`base_scorer.py` references `UpliftingPreFilterV7` directly, plus
`thriving/v1/prefilter.py` via inheritance — neither reaches into private
attrs.

Next: investment-risk v6 (re-exports v5; needs own class — class-name drift
fix is part of the migration).

## #52 investment-risk v6 migration notes (2026-04-29)

Investment-risk is the fifth migrated prefilter and the most structurally
divergent so far. Two things landed in this commit:

1. **Drift fix** — v6 was a thin re-export of v5 (importlib trick because
   the hyphen in `investment-risk` blocks normal imports). v6 now has its
   own `InvestmentRiskPreFilterV6` class. Backward-compat aliases
   (`InvestmentRiskPreFilterV5 = V6`, `InvestmentRiskPreFilter = V6`) plus
   legacy `prefilter()` / `get_stats()` functions preserved so existing
   imports keep working — including v6/base_scorer.py's import via
   importlib (now updated to call `InvestmentRiskPreFilterV6` directly).

2. **Migration to declarative shape** — but only data-shape harmonization;
   apply_filter stays custom for three reasons:
     - **Source-based filtering** runs against `source` / `source_type` /
       `id` fields, not URL or text. Has its own early-return flow:
       allowed-source -> pass, investment-keyword -> pass, blocked-source
       -> block, all before content patterns.
     - **Reasons include matched-pattern info** —
       `allowed_source:reuters`, `investment_keyword:recession`,
       `blocked_source:github`. The base pipeline's `excluded_<category>`
       shape would lose this signal.
     - **Clickbait operates on title only**, not combined text. Stays as
       a separate class attr with its own check below the EXCLUSION_PATTERNS
       iteration.

Three text-pattern categories did get the dict treatment:
fomo_speculation (8 patterns, no exceptions), stock_picking (6 patterns,
12 macro-context exceptions), affiliate_conflict (4 patterns, no
exceptions). The macro_context list is the only per-category exception
this filter has — modeled as `EXCEPTION_PATTERNS_PER_CATEGORY['stock_picking']`.

`(True, "default_allow")` and `(True, "passed")` are intentionally
distinct — investment-risk reports the *reason* an article passed, not
just the fact that it did. Default-allow means "no source/keyword/pattern
fired, falling through to the philosophy: when in doubt, score it."

Behavior preservation verified by 11/11 self-test pass plus identical
pattern counts (19 blocked sources, 25 allowed, 30 keywords; 8/0, 6/12,
4/0 across pattern-with-optional-exception categories; 5 clickbait).

Next: nature_recovery v2 (inline list in method form — simplest of the
remaining; class-name drift fix V1→V2 deferred to the cleanup batch).

## #52 nature_recovery v2 migration notes (2026-04-29)

Sixth migrated prefilter. Simplest of the lot — single text-pattern
category with a single recovery-pattern exception, plus a permissive
nature-relatedness gate.

The structure looked like a clean fit for *fully declarative* shape (sustech
v3 style — base apply_filter + `_filter_specific_final_check` for the
nature gate). But three behavior-preservation concerns ruled that out:

1. **Order**: nature-relatedness check runs FIRST today; base pipeline
   would run it LAST (via `_filter_specific_final_check`). Articles that
   are both off-topic and disaster-themed would change blocking reason
   from `not_nature_topic` to `excluded_disaster_no_recovery` — a
   user-observable change, no matter how rare.
2. **Reason strings**: current returns are bare (`"disaster_no_recovery"`,
   `"not_nature_topic"`); base prepends `excluded_<category>`.
3. **Content-length gap**: current v2 doesn't call `check_content_length`
   (same gap as CD v4 — see Prefilter Quality follow-ups). Base pipeline
   would add the call — also a behavior change.

Settled on data-shape harmonization with a custom apply_filter, same
strategy as belonging / CD v4 / uplifting v7 / investment-risk. The
disaster category fits the EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY
shape cleanly even though it's the only category in this filter.

Class-name drift (file v2 / class V1 / VERSION="1.0") preserved as planned
— part of the deferred cleanup batch alongside sustech V2→V3, gated on
NexusMind cross-repo coordination since their `tests/unit/test_prefilter.py`
imports the V1 name.

Behavior preservation: 6/6 self-test pass. Pattern counts: 33 nature
keywords (duplicate `deforestation` in the original list preserved
verbatim), 1 disaster regex, 1 recovery-exception regex.

Next: foresight v1 (count-based override — `POSITIVE_THRESHOLD = 3`).

## #52 foresight v1 migration notes (2026-04-29)

Seventh and final per-filter migration. Foresight's "count-based override"
turned out to NOT fit BasePreFilter's POSITIVE_THRESHOLD slot — the
semantics differ:

- Base `POSITIVE_THRESHOLD`: bypass when `sum(p.findall() for p in
  POSITIVE_PATTERNS) >= POSITIVE_THRESHOLD` — total match count.
- Foresight v1: bypass when `count(group_name for group in
  POSITIVE_PATTERN_GROUPS if any pattern in group matches) >= 3` —
  distinct categories with at least one hit.

A single repeated keyword in one foresight category counts as 1, not as N.
Migrating to base's semantics would have changed the bypass behavior —
some articles with 3+ matches all in one category would start bypassing
where they previously didn't, and vice versa.

Settled on: data-shape harmonization with a **custom slot**
(`POSITIVE_PATTERN_GROUPS`, not `POSITIVE_PATTERNS`) so the difference is
visible at the class definition. Six block categories DID move into
`EXCLUSION_PATTERNS` cleanly (no per-category exceptions). Custom
apply_filter retained for the distinct-categories-fired logic, the two
pass reasons (`passed_positive_signals` vs `passed`), and URL-based
domain exclusions.

Behavior preservation: 10/10 self-test pass; pattern counts
bit-for-bit identical to baseline (4/4/3/4/3/3 block; 8/4/4/6/3/15
positive; 8/5 domain).

## #52 retrospective (2026-04-29) — what we learned

**All 7 production filters now share a consistent EXCLUSION_PATTERNS data
shape**, even though only sustech v3 ended up using BasePreFilter's full
declarative pipeline. The other 6 retained custom apply_filter for one
or more of these reasons:

| Reason for custom apply_filter | Filters affected |
|---|---|
| URL-based domain exclusions | belonging v1, CD v4, uplifting v7, foresight v1 |
| Per-category exception lists | CD v4, uplifting v7, investment-risk v6 |
| Per-category positive-count thresholds | belonging v1 |
| Count-based block (not pattern-with-exception) | uplifting v7 (pure_speculation), foresight v1 (positive_categories) |
| Source-based filtering on non-URL field | investment-risk v6 |
| Matched-pattern reason strings (`allowed_source:reuters`) | investment-risk v6 |
| Title-only checks | investment-risk v6 (clickbait), belonging v1 (#45 obit) |
| Reason-precedence ordering depends on flow | nature_recovery v2 |
| Bare reason strings (no `excluded_` prefix) | belonging v1, CD v4, uplifting v7, NR v2, foresight v1 |
| Distinct pass reasons (`passed_positive_signals` etc.) | foresight v1 |
| Existing `check_content_length` gap to preserve | CD v4, NR v2 |

**The harmonization is in the *data*, not the *control flow*.** This is
the right call given the genuine variety of filter logic. ADR-018
explicitly permits "custom form" precisely for this case. Future filter
authors can:

1. Read EXCLUSION_PATTERNS to see what each filter blocks.
2. Read EXCEPTION_PATTERNS_PER_CATEGORY (or POSITIVE_PATTERN_GROUPS, or
   the filter-specific override slot) to see what pulls articles back through.
3. Read apply_filter for the specific control flow this filter needs.

That third step is no longer about hunting compiled-regex attributes and
helper methods scattered through the file.

**Surfaced bugs (preserved for zero-behavior-change scope; tracked under
Prefilter Quality):**
- CD v4 missing `check_content_length` call (regression vs v3).
- nature_recovery v2 missing `check_content_length` call.
- uplifting v7 multilingual `\b` boundary leak (Dutch `munitie` matches
  inside English "co-MMUNITIE-s"; same bug shape as RIP/rip-current #45).

**Remaining #52 work:**
- Class-name drift cleanup batch: sustech V2→V3, nature_recovery V1→V2.
  Deferred until cross-repo coordination with NexusMind (whose
  `tests/unit/test_prefilter.py` imports the V2 / V1 names).
- The three Prefilter Quality follow-ups above can be picked up with the
  next version bump on each filter.

