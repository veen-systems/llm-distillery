# 2026-09-01/02 — Phase B ran, ran out of money, and the guards held

**Spend: DeepSeek $4.78, Gemini 28 calls / 333,776 in / 9,231 out.** No model trained, no
threshold moved, no probe touched. One new filter package file (`filters/human_thriving/v8/
config.yaml`, labelling scope only) — **nothing reaches a path NexusMind runs, so deploy is N/A,
not skipped.** Commits `656601f..fd443a3` plus the scorer fix, all pushed.

Ruling record: `docs/decisions/2026-09-01-v8-oracle-ruling.md`.
Evidence: `2026-08-31-v8-no-regression-gate/`, `2026-09-01-v8-phase-b-preflight/`,
`2026-09-01-v8-oracle-choice/`, `2026-09-01-classA-full-read/`, `2026-09-01-phase-b-labels/`.
Registry: `EXP-007`, `EXP-008`, `EXP-009`.

---

## The arc

The owner asked to be **sure** before spending, on the grounds that *"we already labeled numerous
times, then later you forgot stuff."* That instruction is what produced most of this session's
value: every defect below was found by checking rather than by running.

## ⛔⛔ THE KEEPER — a 402 is not a per-row error

A 6,590-row k=3 corpus pass ran out of DeepSeek balance mid-flight. Pass 1 finished clean (6,586
rows, $3.45). Pass 2 got 4,078 rows in and then took **2,500 × `HTTP 402 Insufficient Balance`**.
Pass 3 made **6,586 doomed requests in 11 minutes**, wrote 6,586 error rows, printed
`Successful: 0  Errors: 6586` — and **exited 0**.

Two independent defects, both fixed: `402` was routed through the generic per-row error branch,
and `main()` returned `None` whatever happened. ⚠️ The `raise SystemExit` that guarded 401/403 was
**never a fix** — raised in a `ThreadPoolExecutor` worker it surfaces only at `future.result()`
and the executor drains every queued future first. Now an explicit `RUN_FATAL` flag checked
before each call; exit 2 on abort, 1 on any error, 0 only when clean. 7 tests, 5 mutations killed.

✅ **What caught it downstream was a guard written the night before.** `aggregate_k_runs.py`
refused to write anything. `average_oracle_runs.py`, which it replaced, silently intersects runs
and would have produced a label file.

## ✅ Three pre-flight defects, all caught before the bulk spend

1. **`filters/human_thriving/v8/` had no `config.yaml`**, and that file's `filter.name` selects
   the analysis field. Labels under v7's config make `prepare_data.py` write **0 examples to all
   three splits, print "TRAINING DATA PREPARATION COMPLETE", and exit 0**. Its own docstring says
   why, and the worse clause is the second: a **renamed** dimension becomes a silent column of
   zeros. ⚠️ The schema test had been passing **vacuously** — `ACTIVE_FILTERS` is hand-maintained.
2. **`average_oracle_runs.py` deletes `scope_verdict`**, making #135's flip rate unmeasurable
   after it runs; joins on `url` not `id`; silently intersects; and the shape documented in the
   RUNBOOK and `CLAUDE.md` exits 1.
3. **All 18 Gate B-A rows were 300-char excerpts** and nothing on the scoring path stops a paid
   run against them (`is_scrape_junk` floors at 25).

## ⭐⭐ "The window has rolled, so it is unrecoverable" was false

NexusMind archives **monthly** — 9 tarballs back to 2025-10. **18 of 18 adverse rows recovered**,
5,449 → 100,460 chars. ⛔ My first search globbed `*.jsonl*` over directories of `.tar.gz` and
returned `0 of 18` — **16th occurrence of *establish what a source excludes***. ⛔ The
FluxusSource archive is not a substitute: producer bytes, 447 chars where the enriched original
is 14,546.

## The oracle, ruled — and the bake-off already existed

⛔ **The ADR-020 bake-off the plan demanded had been run on 2026-08-23 and never written into the
plan**, which still carried the superseded n=3 *"Gemini is the stricter arm"* in the section a
reader consults while deciding how to spend $10. ⭐ **And its verdict does not survive the adopted
prompt**: the row it turned on (*"Five men arrested… for raping a minor"*) went from DeepSeek 3.00
vs Gemini **7.43** to **1.050 vs 1.025**, `harm_is_subject` 3/3 on both. Standing: DeepSeek 8/9
Gate B-A and STEP-1, Gemini 7/9; the row Gemini loses stably is the **#91 origin article** at
7.158. **Ruled DeepSeek** — on which row, not on the one-row margin.

## ✅ B5's reading half discharged — all 18 rows, no label reversed

⚠️ Not what the *"three of five drafts reversed"* rule predicts, and the difference is the point:
those were **drafts**. ⭐ The **Travelodge and nursery rows bracket §2's qualifier** — in one the
policy change genuinely is a trailing sentence (both oracles ~0.77); in the other it is a third
of the body, funded and commenced, and the gate flips. A **v8.1** fix, testable for ~6 calls.

## ⭐ What the interruption bought: a k=2 disagreement rate over 4,078 rows

Every prior flip figure rested on 8–9 rows or #135's n=200. **12.0%** of rows disagreed on
`scope_verdict` between identical runs; **4.98%** landed on opposite sides of the op-point;
gate-stable rows moved **0.100**, gate-flipped rows **1.550** — bimodal, exactly as #135 says.
⚠️ **Upper bound**: `stage1_low` is 0% covered and `neg_low` 16%, because pass 2 died partway
through a **cell-grouped** file. That coverage check is what makes the number usable.

## ⛔ Mine

- **Hit the 06:00–10:00 UTC peak twice**, having written the note that morning peak is the trap.
- **Launched three k=3 passes without probing the balance first.** One call would have shown the
  budget covered two passes, before $4.56 went into them.
- **`| tail` swallowed an exit code again** — I read a probe as exit 0 when it was 2. **[x4]**.
- **Substring-matched `"skipped"`** against raw JSONL and counted 9 skips; parsed, it was 4.
- **A shared test tmpdir** made a 403 case report `FATAL: HTTP 401` — cached `__pycache__` plus a
  resume, two stale-state bugs reading as a defect in the code under test.

## State at close

**Phase B incomplete: k=1 on 2,163 rows, k=2 on 4,423, pass 3 not started.** Nothing lost. A
detached finisher is armed for **12:00 UTC** (14:00 CEST, owner's call — clear of peak) to run
the remainder, aggregate and summarise; expected **≈$2.14**, taking the k=3 corpus total to
**≈$6.87** — which is essentially the **$6.92 H-V8-8 retracted** in favour of $10.32. That
retraction looks wrong: k=3 re-scores *the same* articles, and pass 2 measured **99.4% cache**.
