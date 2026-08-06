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

## Standing rule (promoted from gotcha log 2026-08-06 — 5th occurrence, one of them self-inflicted)

**Before shipping any gate, cap, threshold, config key or stamp, name the caller
that loads it — in writing.** A mechanism that is present, configured and
unreachable is this repo's defining failure, and it now has five instances:
ducroq/NexusMind#284 (per-filter prefilters never ran, six months), #94 (a
gatekeeper binding 0 times in 191,616 articles), ducroq/NexusMind#281 (a gate
that could never fire), ducroq/NexusMind#300 (the #93 `content_length` stamp
computed and then dropped before persistence — 0 of 50,605 rows), and
`filters/cultural_discovery/v6` (a `hybrid_inference` block and a probe pickle
shipped into a package with no inference module — **written the same day the
other four were documented**). The last one is the important one: knowing this
failure mode does not prevent it. Only running the check against your own work
does. **Do not infer runtime behaviour from the presence of a config key**, and
treat "the code is correct" as answering a different question from "the code
runs". Two smells that should trigger the check every time: a package that
passes its self-tests but has never been loaded end-to-end, and a field that is
initialised to `None` and populated somewhere you have not read.

- [CD v6 probe hypotheses](cd-v6-probe-hypotheses.md) — #98: what the e5 probe confirmed (per-language gap gone; batch-invariant, unlike #95), what it refuted (screening is a REGRESSION; 4 of 5 "recovered" positives are off-lens), and the traps (v6 cannot score — no inference module, no calibration)
- [Cross-repo prioritization](cross-repo-prioritization.md) — master issue landscape across 5 repos (**191 open**, re-queried 2026-08-05): P0-P4, **15 dependency chains**, 6 work batches, plus a Coverage section (stale — computed against 177). Chain 3 CLOSED; Chain 4 re-rooted on #93; Chain 8 deadline-driven (FS#120 ~2026-08-14). **Refreshed 2026-08-05 (late): two banded entries were closed (ovr#285 P0, NM#290 P1); new Chain 15 (lens commensurability — LD#96 + ovr#296, a placement decided by 0.043, inside #95's 0.16 noise floor); Batch C grew into a real compliance programme headed by ovr#292 (333 of 1,357 domains signal an AI opt-out), which LD#28 inherits. Also: llm-distillery's own 36 are grouped there, 14 of them untouched 30+ days.**
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

## Standing rule (promoted 2026-08-05 — 3rd occurrence, twice in one session)

**`pgrep -f "<pattern>"` cannot answer "is it running?" — it matches the shell
carrying the pattern, and over ssh the bracket trick does not survive quoting.**
It has now produced a wrong answer three times: twice blocking a production
deploy on 2026-08-03, twice more on 2026-08-05 (a false "still running" reported
to the owner, and a restart that silently did not launch). The failure is
convincing because the output *looks* like an answer. Use
`ps -eo pid,etime,args | grep -v grep`, or ask the service manager
(`systemctl is-active`), or read the log's last timestamp. **If a process check
decides whether you act, print the matching line before believing it** — a
self-match is obvious on sight and invisible in a count.

## Recent Sessions

- [2026-08-06 afternoon](project_session_2026_08_06_afternoon.md) — **#98 cd v6 probe shipped: held-out oracle FN 0/75 vs the keyword gate's 10/75; production surfacing blocked 337 (12.7%) → 1 (0.04%), 20 of 27 languages at 0.0%.** Threshold **2.50**, not the trainer's 3.025 — `train_probe.py` selects off the val curve, so its val FN is optimistic (1.3% reported, 6.7% held-out). **The review battery found 2 blockers in the same day's work, both mine**: v6 ships a `hybrid_inference` block + probe into a package with **no inference module and no calibration.json** (`_load_calibration` fails silent), and a val-vs-production rate comparison written *while correcting* an identical error. Two conclusions changed by self-correction: criterion 2 is a **regression** (63.7% vs 70.2% screening), and **4 of the 5 "recovered" positives are off-lens** (#87 inside the labels). **Probe is batch-invariant** (max |Δ| 3×10⁻⁶) unlike the student (#95). Also: **#99 filed** (English-only escape hatch, 66/516 en vs 0/265 non-en), **FS#120 answered** (pre_enrich fires at **500**; their `eval_query` is on 28 of 547 rows so their Chad/Tchad cut is unexecutable; 3 of 8 arms too small), **ducroq/NexusMind#300 filed** (#93 stamp computed then dropped, 0 of 50,605 rows). Four SSH assertions re-run after three slipped passes — all PASS. **NEXT: FS#120 harness (~08-14), then #98 criterion 4.**
- [2026-08-06](project_session_2026_08_06.md) — **four-lens review of the previous evening's commits: 4 blockers, 13 warnings, all fixed** (`b37b88e` here, `8ce017c` in ovr.news). **Every measurement held; the prose around them did not** — a duplicate footer link live on every page from a codebase fact asserted without a grep, `GPTBot 401 domains` published against a stated total of 333, ADR-003 contradicting itself three ways, and a guard test left stale while the table it enforces grew (the whole art. 50 marker was deletable with a green suite — now proved to bite). **Also: `~/.claude/skills/review-changes` pointed at `repos/personal` and silently won over this repo's own adapted copy — a global skill shadows a project-local one of the same name with no warning.** Symlink removed, two stale local copies deleted, four improvements ported in. A second session was live in ovr.news throughout; nothing of theirs was touched. **NEXT: FS#120 (~08-14).**
- [2026-08-05 evening](project_session_2026_08_05_evening.md) — **board refreshed (191 open, two banded P0/P1 entries were already closed) and the legal arc executed, almost all of it in ovr.news.** Five owner decisions recorded: oracle-to-third-party risk **knowingly accepted**; AI-crawler opt-outs **don't bind** the fetcher (ovr ADR-043); training is *"modelling, not mining"* (recorded here, with the counter-argument against itself); disclose on cards **and** search snippets; publisher is **Veen Systems**. **Two findings changed the work: the EMFA micro-enterprise exemption does not exist** (zero occurrences in the adopted regulation — ovr.news is probably in scope and has been since Aug 2025), **and the site published a data controller that does not exist** (Busara.eu). AI Act art. 50 now covered on every surface; EMFA art. 6 ownership published; GDPR art. 33(5) incident record written. New **Chain 15 (lens commensurability)** — ovr#296's 0.043 margin sits inside #95's 0.16 noise floor. **NEXT: FS#120 (~08-14).** Nothing committed.
- [2026-08-05](project_session_2026_08_05.md) — **LD#92 IDENTIFIED**: D3 (matched percentile depth) −1.119 is the *largest* effect, not the collapse the selection artifact predicted; gemini cross-check −1.351 kills the "judge penalises short input" alternative. Cap value now blocked **only** on #95. **`review-changes` skill adopted (framework v1.10.6 → v1.14.0), re-mapped not copied — its first run caught four of my own same-day errors.** GN measured as the stub source (14–17% of articles, 48–56% of stubs) → evidence into FS#120; **ovr#299 filed** (headline-only summaries are 83.4% invented; the model has a fixed length target and fills it). Harness **and fixtures** committed at last. **NEXT: FS#120 (deadline ~08-14), then #95 batch pinning.**
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
