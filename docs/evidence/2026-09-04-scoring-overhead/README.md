# Is scoring wearing out sadalsuud? — measured, and three of my own answers were wrong first

**2026-09-04. $0**, logs only. Raised by the owner: *"we always have a cost problem. My
cpu/gpu is heavily occupied, I believe the e5 probes are running on sadalsuud, rapidly
wearing the thing out"* — then narrowed: *"don't care about the b650, that is not in
production. I care about sadalsuud-gpuserver."*

Reproduce (`--out` is **not** optional — the bare command prints to stdout and saves
nothing):

```bash
D=docs/evidence/2026-09-04-scoring-overhead
python $D/measure_scoring_overhead.py --since '36 hours ago' \
    --until '2026-09-04 16:10' --out $D/overhead.json | tee $D/overhead.txt
```

Needs `ssh sadalsuud` and `ssh gpu-server` from the workstation. ⚠️ Keep `--since` tight: a
wide one streams the whole retained journal over ssh and does not return.

---

## The short answer

**No — the filter probes do not run on sadalsuud, and the box spends 5.6% of its day on the
pipeline. But the load is not where anyone looking at it expected, including me.**

`score` costs sadalsuud **52.1 min per 29.17 h** and is 98.6% accounted for by gpu-server's
own handler time. **Story dedup costs 41.3 min in the same window** — 42.4% of the
pipeline's blocking time against `score`'s 53.5% — and **at most 4.4% of it is GPU work.**

⚠️ **What that remaining 95.6% is has NOT been separated.** It is clustering *plus* the
article-embedding pass's client-side overhead, and the instrumentation cannot split them.
An earlier draft of this document called it "clustering on sadalsuud's CPU". That was
asserted by subtraction from a bucket nobody had enumerated — see §7.

## 1. There is no CPU scoring path for the FILTERS — and that is a config read

`NexusMind/config/app.yaml` on sadalsuud, read 2026-09-04: `require_gpu: true`,
`host: "gpu-server"`, `port: 8000`, `cpu_fallback.enabled: false`.

⛔ **Those keys sit under `scoring:`, and this block is about the filter path only.** Story
dedup is a *preprocessing* stage and never consults them; sadalsuud has no GPU at all
(`nvidia-smi` absent from `$PATH`) and `NexusMind/src/preprocessing/story_dedup.py`'s own
loader falls back to `SentenceTransformer(model_name, device="cpu")` when nothing else is
arranged — so **the config predicts a CPU e5-large pass.** It does not happen
(`main.py:2648` injects a GPU embedder), and only the log says so. Config in one direction,
runtime in the other; §7 is what that cost.

⚠️ The layer split in §2 is the runtime evidence for the filter path — 98.6% of sadalsuud's
scoring wall time is accounted for by gpu-server's *own* response timings. ⚠️ **Good
evidence, not proof.** It is a ratio of two independently-summed totals with no call-level
pairing; a second client on the scorer would push it past 100%. The script now asserts the
layers nest and refuses if they do not.

## 2. Where the scoring wall time goes

Window **2026-09-03 06:20:46Z → 2026-09-04 11:31:00Z (29.17 h)**, **8 cycles**, 40 `score`
calls over 5 filters, **146,433 articles**, 1,521 batches, 1,521 HTTP 200s, **0 non-200**.
Both journals are asserted to *cover* the window, not merely to be filtered to it.

| layer | total | per article | share |
|---|---|---|---|
| sadalsuud blocks on `score` | 3,127.1 s | 21.36 ms | 100% |
| gpu-server HTTP handler | 3,083.8 s | 21.06 ms | **98.6%** |
| model compute (hybrid batch) | 2,647.5 s | 18.08 ms | **84.7%** |
| → client + network | **43.3 s** | **0.30 ms** | 1.4% |
| → in-server, non-compute | **436.3 s** | **2.98 ms** | 14.0% |

**Multiplier sadalsuud-wall ÷ GPU-compute = 1.18×.**

Per-filter: uplifting 813.8 s (26.0%), belonging 710.3 s (22.7%), nature_recovery 695.0 s
(22.2%), cultural_discovery 518.4 s (16.6%), solutions 389.6 s (12.5%).

Routing: prefilter_blocked 1.66%, **stage1_low 35.16%**, stage2 63.18%. ⛔ **That is the
five DEPLOYED filters' screens pooled** — not any one filter's, and specifically not
`human_thriving v8`, whose own adopted threshold routes ~89% onward (`EXP-020`).

## 3. The whole pipeline against this box

Printed by the script, so no document recomputes it by hand:

| | 29.17 h window | share |
|---|---|---|
| `score` | 3,127.1 s | 53.5% |
| **story dedup** | **2,477.5 s** | **42.4%** |
| prepare + rescore + write | 241.9 s | 4.1% |
| **pipeline blocking total** | **5,846.5 s** | **duty cycle 5.57%** |

⚠️ `pre_enrich` and `source_filter` log **0.0 s** on all 40 calls. The lines exist and are
populated, so the instrument works — but 0.0 s is *rounded to one decimal*, not proven zero.

⛔ **Still unmeasured**: collection, enrichment, the ledger and the build. This is three
stages plus two consumers, not an enumeration of everything the box does.

## 4. What is worth fixing, at its real size

Not the client — 0.30 ms/article. Two things inside gpu-server:

1. **The model is not held resident.** 43 embedding-model loads, 73 filter unloads, 35
   GPU-memory frees in 29 h — load/unload per filter per cycle. That is what the 436.3 s
   (14.0%) of in-server non-compute buys.
2. **Cold cost lands on small batches.** Slowest single `/filter/*/score` response:
   **5,526.3 ms** (belonging). An earlier sample caught
   `POST /filter/cultural_discovery/score [200] 3342.5ms` for a **one-article** batch.

⭐ **The ceiling is small**: eliminating *all* in-server non-compute takes `score` from
**52.1 to 44.8 min per 29.17 h — a saving of 7.3 min.** Worth doing if cheap; not a cost
problem. (⚠️ 44.8 min is compute **plus** client/network. First written here as 44.1, which
is compute alone.)

## 5. Every other consumer of gpu-server, named

Because leaving them out is how §3 went wrong the first time:

| endpoint | calls | gpu handler time |
|---|---|---|
| `/embeddings/encode` | 158 | 107.8 s |
| `/obituary/predict` | 285 | 28.1 s |
| `/models/unload` | 35 | 11.6 s |

## 6. What this says about the Stage-1 gate question (`EXP-020`)

**The gate addresses none of it.** Tightening Stage-1 reduces *compute* — 84.7% of a total
that is itself 3.1% of sadalsuud's day. The 2026-08-28 hold-near-pass-through ruling turned
on there being no Stage-2 cost constraint; this is the evidence that there still is not one.

⚠️ The 3.1% is robust — it uses only sadalsuud's own journal. The 84.7% is `compute/wall`
and depends on both journals covering the window, which is now asserted rather than assumed.

## 7. ⛔ Three corrections, all mine, all the same shape

**7a. "~62 ms/article of overhead, a 4× multiplier."** Paired sadalsuud's `score` total from
a **three-cycle** window (1,209.1 s / 15 calls) with gpu-server's totals from a **twenty-hour**
window (1,656.8 s / 941 batches). Matched: **0.30 ms/article, 1.18×.** ⚠️ **The tell was
absent** — the *per-call* rates agreed across the two windows (80.6 s/call against 77.5
s/call, the latter from the 16 h read: 1,938.6 s over 25 calls), so every check on the pieces
passed and only the denominators were incomparable. ⭐ **"Recompute it a second way" would not
have caught this**: recomputing ms/article *confirms* the error. It needed a quantity that
cannot be formed without a shared denominator.

**7b. "The e5 probes do not run on sadalsuud at all."** A config read stated as a runtime
fact, and wrong at the host level: story dedup runs its own `multilingual-e5-large` pass and
is 42.4% of the pipeline's blocking time. Flagged by a peer session working on dedup — whose
own mechanism (that the pass runs on sadalsuud's CPU) the log then refuted. Both of us
reasoned from source; neither had checked the log.

**7c. ⭐ "86% of dedup is clustering on sadalsuud's CPU" — the one I nearly shipped.** The
`Centroid migration … embed_seconds=` field times **only the re-embedding of cluster
centroids being drift-checked**, not the run's article-embedding pass, which is untimed and
unlogged on the sadalsuud side. So `dedup wall − embed_seconds` is not clustering: it still
contains the article pass's blocking HTTP wait, which by §2's own doctrine is *not*
sadalsuud CPU. **Asserted by subtraction from a bucket that was never enumerated** — the same
shape as 7b, twenty lines after logging 7b.

What can honestly be said instead, measuring the article pass from the side that sees it:

| | 29.17 h | 13.21 h |
|---|---|---|
| story dedup wall | 2,477.5 s | 1,216.2 s |
| gpu handler, `/embeddings/encode` | 107.8 s | 47.2 s |
| **share of dedup that is GPU work** | **≤ 4.4%** | **≤ 3.9%** |
| **remainder, sadalsuud-side** | **≥ 2,369.7 s (95.6%)** | **≥ 1,169.1 s (96.1%)** |

⛔ **The remainder is clustering PLUS the embedding client overhead, and they are not
separable with current instrumentation.** Note sadalsuud's own centroid timer reads 299.5 s
while gpu's handler time for *all* encode traffic is 107.8 s — so embedding carries
substantial client-side cost (158 round trips) that is not clustering. **A capacity argument
needs dedup instrumented, not this subtraction.**

⚠️ Two further instrument defects found in the same pass and now surfaced rather than fixed
silently: **7 device lines over 8 dedup runs**, so *"every run logs `Story dedup: using GPU
embeddings via gpu-server`"* — which I told the peer — is **false as stated**; it was 7 of 8,
and the instrument cannot express "CPU" at all (the CPU branches log a different phrase). And
**7 centroid-migration lines over 8 runs**, so the 12.1% embedding share sits on an unmatched
denominator. Both are printed by the script now.

## 8. Reproduction, and what it does and does not show

| | 29.17 h, 8 cycles | 13.21 h, 4 cycles |
|---|---|---|
| multiplier wall/compute | 1.18× | 1.18× |
| compute ms/article | 18.08 | 18.05 |
| score per cycle | 390.9 s | 390.9 s |
| dedup per cycle | 309.7 s | 304.1 s |
| shares score / dedup / other | 53.5 / 42.4 / 4.1% | 53.8 / 41.9 / 4.3% |

⚠️ **These windows are NESTED** (same `hi`, later `lo`), so this is a subset re-run, not an
independent replication. It cannot detect a journal-coverage gap, because a later `lo` sits
further inside whatever the journals retain. What it does show is that the rates are not an
artefact of one cycle.

## 9. Appendix — the guards were tested by execution, not by reading

A guard that has never fired is indistinguishable from one that cannot. All refusals exit **1**:

| input | result |
|---|---|
| `--since 'tomorrow'` | `no timestamped lines since 'tomorrow' — nothing was measured, which is not the same as nothing happened`, exit 1 |
| `--pipeline-unit nosuch.service` | same refusal, exit 1 |
| `--since '2020-01-01'` | no return in 120 s; now converted from a traceback to a message naming `--since` |

⭐ **And the test caught this repo's own status-laundering trap while running.** The first
invocation read the exit code as `$?` after a pipe into `tail`, which reports **tail's**
status: it printed `exit=0` for a run that exited 1. `${PIPESTATUS[0]}` gave 1. **A guard
proved through a pipe is not proved.**

⚠️ **Coverage was a live suspicion, checked rather than assumed.** A review flagged that the
committed run's `lo` sat ~8 h after the requested `--since` boundary — the fingerprint of a
journal that does not span what was asked for. Measured: gpu-server's journal begins
**06:06:33Z** against a window starting **06:20:46Z**, and both journals cover both ends. The
gap was the pipeline being idle, not the journal being short. The guard stays because the
next run may not be so lucky.
