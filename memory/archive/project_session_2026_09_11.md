# 2026-09-11 — NM#474 review round 2: five more blockers, and I broke two things fixing them

**Spend: $0.** No oracle calls, no model training, no production data touched, nothing deployed.
Smoke tests ran on sandbox copies of real rows only.

**Commits.** NexusMind `feat/harm-detector-shadow-stamp`: `d35ab24`, `009a55e`, `f1a1f40` (pushed,
PR marked **ready for review**, ⛔ **not merged — CI still pending at session end**).
llm-distillery `main`: `5681c66`, `bb5a52d` (pushed).

## 1. The question that started it

Owner asked what "cross-lens" means for `#156` and whether per-lens gating is even reachable
(*"it will be hard to make this lens-dependent, i do not really see a path forward"*).

**It is reachable, and the mechanism already exists and already runs.** Verified by reading the
call path, posted to `#156`:

1. `scripts/main.py:4406–4420` — commerce → obituary → (harm) → `_stage_run_filters(input_files)`.
   Preprocessors rewrite raw rows in place; the filter stage reads them afterwards.
2. `scripts/main.py:1787` `scorer.score_batch(articles)` → `src/scoring/production_scorer.py:747–749`
   passes `article` whole into `_base.score_article`. Nothing strips `_`-prefixed stamps.
3. `filters/common/filter_base_scorer.py:67` → `_load_preprocessing_config()` reads
   `self.filter_dir / "config.yaml"` — each lens carries its own switch.
4. `_load_short_content_config` (196–219) + `_apply_short_content_cap` (278–301), called once at
   `_process_raw_scores:336`, mirrored for the hybrid Stage-1 branch at `hybrid_scorer.py:255`.
   Per-lens, stamp-reading, config-gated, exactly one decision point — ADR-022's shape.
5. Runtime-proven, not documentation: the sibling key `head_tail: true` is live on `uplifting v7`,
   `solutions v6`, `cultural_discovery v5`, `nature_recovery v4`, `belonging v1`.

⚠️ **Code-proven, NOT outcome-proven: `short_content.cap` is `None` on all 26 `config.yaml` files,
so that branch has never fired in production.** The first per-lens harm cap must demonstrate a
changed outcome on a real cycle.

⛔ **And there are no per-lens numbers to set a cap with.** Every harm figure is the
`uplifting v7` / `human_thriving v8` display-eligible panel. Solutions, belonging, nature_recovery
and cultural_discovery have **zero** harm measurements, and for at least two of them "no cap, ever"
may be right. Sequencing: stamp → accumulate → measure per lens → flip `uplifting v7` first.

## 2. The review — 3 lenses, 5 blockers, all fixed

Budget stated up front: guarantee-preservation + adversarial + doc-accuracy. Shell-correctness
skipped (no `.sh` changed). Baseline `origin/main`, 25 files, +1794/−3 → full battery.
Structural markdown pre-check: 1 file, 0 problems.

⭐⭐ **THE KEEPER — a green suite is a statement about the ORDER IT RAN IN.** Test fixtures named
`content_items_*.jsonl` in `tmp_path` are globbed by `contract_check.py:276` from the
**session-shared** pytest basetemp:

| run | result |
|---|---|
| `test_contract_check.py` alone | 52 passed |
| harm tests **first**, then contract_check | **6 FAILED**, 58 passed |
| reverse order | 64 passed |

Two sessions' *"1,649 pass"* were both true and both hid it, because `c` sorts before `h`. The
victim was the test that exists to prove that check does not false-red. (`H-HD9`)

⛔ **The recency key was mtime, and mtime is not recency for these files** (`H-HD7`). Commerce and
obituary run before the harm stage over the SAME list in the SAME order and rewrite each modified
file, so sequential rewriting leaves the truly-newest file with the OLDEST mtime. Steady state
hides it (only one file modified); a multi-file **cold start** — the one case
`max_articles_per_run` exists for — inverts fully, spending the budget on the oldest rows while
today's age out at `max_article_age_days: 3`. Measured on a real `data/raw`: **filename order and
mtime order diverge at position 0, 11 of 87 files ranked differently.** Now keyed on the
`(\d{8}_\d{6})` filename collection stamp; smoke-tested with mtimes inverted as upstream leaves
them — old key takes `20260901`, new key takes `20260903`.

⛔ **The 0.2008 stack floor was attributed to the WRONG ARCHITECTURE, in five places.** It is the
Gemma-3-1B student's (`uplifting v7`, 660 rows, b650 vs gpu-server's venv, CPU both sides);
mpnet + sklearn MLP is **UNMEASURED**. Worst copy: the `RuntimeWarning` text emitted into
production logs on every off-pin load. ⛔ **My first correction pass fixed ONE**, because I worked
from the review's list instead of grepping — the same shape as the DeepSeek surface count one
session earlier. Recorded in `memory/score-batch-shape-noise.md`.

⛔ **`_harm_detector_stack` omitted the libraries that own the embedding** (`H-HD8`) — `st-mpnet`
was a literal, so two runs under different sentence-transformers or torch versions stamped
byte-identical strings. Now a `stack_id` property on the detector, reading installed metadata:
`paraphrase-multilingual-mpnet-base-v2/st-5.6.0/torch-2.12.1+cpu/sklearn-1.8.0/cpu`.

Plus: the verify script the README points at **could never have run** — its `sys.path.insert`
pointed at `scripts/verification/`, which does not contain `filters/`, and its stamp assertion
wanted un-prefixed keys while `stamp()` returns prefixed ones (executed, not read). Both fixed.
⚠️ It still cannot run: `datasets/panel/panel_content.jsonl` does not exist here and cannot be
rebuilt from `panel_frame.jsonl` (no `content` on any of 137 rows), so its three claims are
unverified since the build session. The unchecked place is the 730-day sadalsuud archive.

## 3. What the smoke test proved that the suite could not

On 120 real production rows, sandbox copies: stamps land as floats in [0,1]; line counts and id
order preserved; the unparseable line preserved **verbatim**; pre-existing stamp not re-scored;
no verdict/threshold field anywhere; no non-harm field changed; idempotent on re-run; caps
enforced (25/25, `items_limit` 10/10, 2 files deferred); age window excludes 120 and writes
nothing. Contract A: all three harm stamps stripped ×80 → **0 violations**, and an injected
unknown stamp fired **40 errors** — the control could say yes. Config gate resolves **both ways**
(shipped `false`, flipping the YAML reads `True`), so the default is measured and not just a
missing key. Disabled costs a **23 ms** import with no torch/sentence-transformers/sklearn.

⚠️ Throughput measured 11.2–12.8 art/s at loadavg ~10.7 against the README's 19.9 — **not a clean
comparison** and not a refutation; needs an idle re-run before the derived "~3 min/cycle" and
"60–75 min" figures can be trusted. Checked and NOT a finding: a full re-parse of all 89 raw
files costs **3s**.

## 4. ⛔⛔ Two defects I introduced, one of which I pushed

**I shipped a broken `_load()` to llm-distillery `main` in `5681c66`.** Placing the new `stack_id`
property mid-`_load()` orphaned `_warn_on_stack_drift()` and the embedder assignment behind a
`return`; `_embedder` stayed `None`. **All 16 unit tests passed** — every one uses
`_FakeDetector`, so not one executes `_load`. A smoke run on real rows caught it in the worktree;
then the same defect rode a cross-repo `cp` I did from memory rather than `cmp`, and I pushed it.
Repaired in `bb5a52d`, caught by the first of the three coverage tests I was writing at the time.
⭐ **A sync is not a copy until you diff it.**

**And `git checkout -- <testfile>` destroyed an uncommitted test** during mutation testing. The
working rule bans whole-tree git verbs; this passed an explicit path so it read as compliant, but
`checkout` restores from HEAD and HEAD did not have the new work. Only the "restored: 17 passed"
count (18 was right) caught it. Switched to `cp` backups.

**9 mutations killed** overall: key reverted to mtime; fallback returning 0.0; ValueError guard
deleted; `stack_id` dropping the ST term; EMBEDDER replaced by the old literal; the orphaned-`_load`
defect itself; a register entry deleted; a 4th stamp with no register entry; and the fixture rename.

## 5. The flip's hard precondition, met

`docs/article_record_status.yaml` now classifies all three stamped fields.
`article_record_register.py:318` errors for a NexusMind-owned field observed on rows and
classified nowhere — inert while disabled, firing on **all three at once** the first cycle after
`enabled: true`. Simulated against the real register: **0 errors** with the entries, and a 4th
unlisted field still errors.

⚠️ **No `record_path` on any of the three, deliberately.** The record schema declares no
`nexusmind.signals.harm_*` and `validate_status` rejects a dangling pointer — verified against a
deliberately bogus control path, which produced the identical error. That entry is owed **after**
`stamp_census.py` confirms population, which cannot happen while the stage is disabled.

`test_every_field_this_stage_stamps_is_classified_in_the_register` reads the field list off
`HarmPreprocessor`'s class attributes, not a typed list — a fourth stamp fails the test.

## 6. Parked with owner agreement, recorded on the PR

- `deferred_over_cap` counts only whole files skipped. Measured: a 50-row file at cap 7 logs
  *"0 files deferred to a later cycle"* while **43 rows** sit unstamped. Production's shape (one
  big file per cycle) makes it read 0 on every cycle that has a backlog.
- A valid-JSON **non-object line crashes the stage** (`AttributeError`, measured), aborting it and
  leaving remaining files unstamped. Reachable via the `aggregator_export_*.jsonl` glob —
  **0 such files exist in production today**.
- A NaN score would write invalid JSON into `data/raw` (`allow_nan=True`, no finiteness check).

## 7. Owner decisions taken this session

1. **NM#474**: mark ready, then merge. Merge and enable remain two separate calls.
2. **Clear next**: the register entries and `inference.py` coverage. The three robustness warnings
   above are parked.
3. **Next priority**: the remaining $0 harm arm.

⭐ **And the "two $0 routes" is really ONE.** `EXP-032` route 2 — *a detector trained on the
existing labels* — **is** `EXP-037`, already run. What remains is route 1, **per-run scope
disagreement**: 178 rows with ≥1 `harm_is_subject` run-vote and a non-harm final verdict (1 above
the op-point), 178 harm rows with split run votes, 1,079 `scope_flipped`. `analyze.py`'s first
version never read those fields.

## Next session

⛔ **0. OWNER, at session close: `/update-drift` FIRST, then `/audit-context`** — the
   framework stamp is wrong (claims byte-identical to v1.36.1; the installed skills carry
   v1.39.0/v1.40.0 content), the memory layer is what moved upstream, and `audit-context` is the
   oldest skill installed. The bloat itself: corpus **2,387,361 chars**, 8× the read threshold,
   **27% of it in `gotcha-log.md` alone** (649.8 KB, 454 entries, no rotation rule — `#123` one
   layer down). ⚠️ Drift adoption deletes zero bytes; it is the prerequisite.

1. ✅ **`NM#474` MERGED** (`01a9809`, CI green 4m37s; 1,655 pass on main; `enabled: false` intact;
   sadalsuud untouched at `b9e8cdb`, no harm code, so NOT deployed — production is frozen and
   enabling is a separate call). Originally: — CI was still pending after ~30 minutes at session end. Check
   `gh pr checks 474`, then `gh pr merge 474 --merge` (the repo uses merge commits). ⛔ Enabling
   is a separate owner call and production is frozen, so the merge lands dormant code.
2. **The per-run scope-disagreement arm** ($0) — the last free route before the ~$3.2–3.6 pool.
3. **Three carried decisions**: ovr.news ADR-045 recency vs `#85` governance; `H-DET5` (re-measure
   across the `EXP-033` seed set first); `filters/resilience/v1` delete-vs-index.
4. ⛔ **A claim I made mid-session and RETRACTED at curate: `EXP-032`–`EXP-037` are NOT missing.**
   All **37** are in `experiments/registry.jsonl`, which is the registry; `experiments/README.md`
   is its **schema doc** and contains no ids by design. I grepped the README — because
   `CLAUDE.md`'s pointer row named it as the registry — got two hits, and reported six
   experiments unregistered. The doc-accuracy lens made the identical error from the identical
   pointer. `check_experiment_registry.py` said `entries 37, untraceable 0` the whole time.
   Pointer corrected. ⭐ **Two readers making the same wrong inference from one pointer is a
   defect in the pointer, not a coincidence** — and the checker that disagreed with me was
   right and was sitting in the index header.
