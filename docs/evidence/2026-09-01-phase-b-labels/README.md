# Phase B — **INTERRUPTED at k≈1.6.** The DeepSeek balance ran out mid-corpus

**2026-09-01/02. Spend $4.56 on the three passes** ($4.61 including the day's smaller runs).
⛔ **The labelling is NOT complete and there is no aggregated label set.** Nothing is lost:
pass 1's 6,586 labels are on disk and intact.

| pass | scored | junk | errors | wall | cost (off-peak) |
|---|---|---|---|---|---|
| **run1** | **6,586** | 4 | 0 | 33.9 min | **$3.4513** |
| **run2** | **4,078** | 4 | **2,508** | 23.8 min | **$1.1084** |
| **run3** | **0** | 4 | **6,586** | 11.1 min | **$0.0000** |

```
2500x  HTTP 402: {"error":{"message":"Insufficient Balance", ...}}   (run2)
6586x  HTTP 402: {"error":{"message":"Insufficient Balance", ...}}   (run3)
   8x  Max retries: HTTP 429                                          (run2)
```

So the corpus stands at **k=1 on 2,512 rows and k=2 on 4,078** — the ruling requires k=3, and
#135's step function is the reason it does.

✅ **The guard built the night before did its job.** `aggregate_k_runs.py` refused outright —
*"FATAL: 6586 id(s) are not in every run and --allow-missing is 0. No output written."* — so no
partial label set exists to be mistaken for a finished one. That refusal is the only thing that
caught this downstream, and it is exactly the failure mode `average_oracle_runs.py` would have
absorbed silently by intersecting the runs.

---

## ⛔ Three defects in the scorer, all fixed 2026-09-02

### 1. A run-fatal status was treated as a per-row error

`402 Insufficient Balance` fell through to the generic `return {"error": ...}` branch. Result:
**pass 3 made 6,586 doomed requests in 11 minutes** against an empty account, wrote 6,586 error
rows, and printed `Successful: 0  Errors: 6586`.

⚠️ **`raise SystemExit` was not the fix, and is why the existing 401/403 handling was already
unreliable.** Raised inside a `ThreadPoolExecutor` worker it surfaces only when the main thread
calls `future.result()`, and the executor's context manager drains every queued future first.
The fix is an explicit `RUN_FATAL` flag that every worker checks **before** calling, so the
first 402 stops all further requests deterministically.

### 2. The script exited **0** on total failure

`main()` returned `None` regardless, so `Successful: 0  Errors: 6586` and a clean run were
**indistinguishable to any caller**. Now: **exit 2** on a run-fatal abort with a FATAL block
naming the status, the body and the resume command; **exit 1** if any rows errored; 0 only when
clean.

### 3. The cost line priced any endpoint with DeepSeek's card

On the Gemini arm earlier the same day it printed `Estimated cost: $0.00 off-peak / $0.00 peak`
— because that endpoint returns no cache fields. **That is not a price, it is a wrong number
wearing a dollar sign.** It now prints `NOT PRICED` and names the host whenever `--base-url` is
not DeepSeek.

**Guards:** `tests/unit/test_scorer_run_fatal.py`, 7 tests + 2 subtests, **5 mutations killed** —
including *"402 back to a per-row error"* (the exact defect) and *"drop the short-circuit: keep
calling after the account is empty"*. A clean-run control is included so a guard that always
failed could not pass the suite.

⚠️ **The test fixture needed isolating per invocation and the reason is worth keeping**: reusing
one temp directory made the 403 case report `FATAL: HTTP 401`, because Python served a cached
`__pycache__` copy of the previous stub *and* the scorer resumed from the earlier output. Two
stale-state bugs in the fixture, both of which read as a defect in the code under test.

---

## Resuming — what it costs and why it is cheap

`load_already_scored()` skips only **successfully** scored ids; error rows carry an `id` but no
analysis field and are **deliberately retried**. So a resume re-runs exactly what is missing:
2,512 rows for pass 2 and 6,586 for pass 3.

⭐ **And both will run at ~99.4% cache**, because those articles are already in DeepSeek's
whole-request cache from pass 1 — measured, not assumed: pass 2's completed portion hit
**99.4%** with a mean miss of **66 tokens/article** against pass 1's ~1,190.

Pass 2's completed 4,078 rows cost **$1.1084**, i.e. **$0.000272/row** at that cache rate, so
the remaining **9,098 rows ≈ $2.5**, and **k=3 lands near $7.1 total**. ⚠️ That is an
extrapolation from one measured rate, not a measurement — the honest bound remains the $10.32
ceiling. It does confirm the direction: H-V8-8's retracted **$6.92** was closer to right than
the figure that replaced it, because k=3 re-scores *the same* articles.

```bash
# top up the account first, then re-run the SAME commands; ids already scored are skipped
D=datasets/scored/human_thriving_v8
for r in 2 3; do
  PYTHONPATH=. python3 scripts/score_deepseek_production.py \
    --input $D/corpus.jsonl --output $D/run$r.jsonl \
    --config filters/human_thriving/v8/config.yaml \
    --prompt filters/human_thriving/v8/prompt-candidate-tail.md --concurrency 8
done
PYTHONPATH=. python3 scripts/oracle/aggregate_k_runs.py --runs $D/run1.jsonl $D/run2.jsonl \
  $D/run3.jsonl --config filters/human_thriving/v8/config.yaml --out $D/labels_k3.jsonl
PYTHONPATH=. python3 docs/evidence/2026-09-01-phase-b-labels/summarise.py \
  $D/labels_k3.jsonl $D/corpus.jsonl
```

⚠️ A resume **appends**, so `run2.jsonl` will hold the 2,508 error rows alongside their
successful retries. `aggregate_k_runs.py` skips error rows before de-duplicating and takes the
last scored row per id, so this is handled — but do not `wc -l` the file and read it as a row
count.

## What pass 1 already establishes

- **The labelled corpus is 6,586, not 6,590.** Four rows are scrape junk — all JavaScript-required
  boilerplate at 357–489 chars (two Bluesky, one Slate crossword, one La Jornada). All are
  **above** the corpus's 300-char floor, so length did not catch them and pattern matching did.
  They sit in `neg_low` / `stage1_low`, so composition impact is negligible.
- **Pass 1 cost $3.4513 against H-V8-8's predicted $3.44/pass** — the per-pass figure was right.
- ⛔ **No corpus-wide scope-flip rate yet.** It needs k=3 by definition. Every flip figure this
  project has is still 8 or 9 rows (2/8 on the class-A head sample, 1/9 on each oracle arm).

---

## ⭐⭐ The interruption bought one thing: a k=2 disagreement rate over **4,078 rows**

Every scope-flip figure this project had rested on **8 or 9 rows** (2/8 on the class-A head
sample, 1/9 on each oracle arm) or on #135's **n=200**. Pass 1 and the completed part of pass 2
give the same articles scored twice, at $0 extra.

| measured over 4,078 rows scored twice | |
|---|---|
| `scope_verdict` **disagreed** between the two runs | **488 = 11.97%** |
| rows landing on **opposite sides of the 4.5 op-point** | **203 = 4.98%** |
| \|Δ weighted average\|: mean / median / p90 / p99 / max | 0.422 / 0.100 / 1.050 / 3.700 / 5.200 |
| rows moving more than the 0.436 decoder mean floor | 1,223 = **30.0%** |
| \|Δ\| on the **488 verdict-flipped** rows | median **1.550**, max 5.200 |
| \|Δ\| on the **3,590 verdict-stable** rows | median **0.100**, p99 1.650 |

⭐ **The distribution is bimodal exactly as #135 describes** — a step function, not a noisy
continuum. A gate-stable row moves 0.1; a gate-flipped row moves 1.55. `1/√k` describes the
former and cannot touch the latter.

⚠️ **This is an UPPER BOUND on the corpus, and the reason is the interruption itself.** Pass 2
stopped partway through a file that is **grouped by design cell**, so these 4,078 are a prefix,
not a sample: `stage1_low|*` is **0% covered** (0 of 621) and `neg_low|latin|-` only 16%. Those
are the lowest-scoring strata, where the gate is least contested. The corpus-wide rate is lower
than 11.97%.

⚠️ **And it is not comparable to #135's 5.3% as a like-for-like.** That was production-mix at
n=200; this corpus was deliberately drawn to over-sample the boundary. Two populations, not a
contradiction — but it does mean **the gate is more contested in the training corpus than the
plan's 5.3% implied**, which raises rather than lowers the value of k=3.

### What it settles about k

- ⛔ **k=1 is not defensible.** Roughly 5% of rows — of the order of 250–330 corpus-wide — would
  carry a coin-toss label on the visibility decision itself, and they are not randomly
  distributed: they are the boundary cases the student most needs to learn correctly.
- ⚠️ **k=2 detects but cannot resolve.** It tells you *which* 488 rows disagreed and nothing
  about which reading is right. There is no majority to take.
- ✅ **k=3 is the cheapest k that resolves**, which is what H-V8-6 concluded from a different
  direction (residual 3.750% → 2.452% → 1.945% at k=1/3/5).
