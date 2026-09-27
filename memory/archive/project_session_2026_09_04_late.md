# Session — 2026-09-04 (late): the cost question, and the instrument that answered it wrong three times

**Spend $0.** No oracle calls. Nothing deployed, nothing on the Hub, nothing written to
NexusMind — **deploy N/A, not skipped** (verified: `ls NexusMind/filters/` on sadalsuud has no
`human_thriving`; v8's weights are gitignored (#97) and live only on `b650-gpu`; phases 8 and 9
have not run).

Continues `project_session_2026_09_04_evening.md`. That session closed at `f5948f7`.

---

## What was asked

> *"write a note to the nexusmind peer session on the overhead. Then let us continue in the
> next session, let us wrap up, clean up the repo, update docs, then curate and commit. pls
> update hypotheses, todo's and GH issues. Also merge, push and deploy if that is applicable."*

Preceded by the question the note was supposed to relay: *"we always have a cost problem. My
cpu/gpu is heavily occupied, I believe the e5 probes are running on sadalsuud, rapidly wearing
the thing out"* → *"don't care about the b650, that is not in production. I care about
sadalsuud-gpuserver."*

## ⛔⛔ THE KEEPER — I was one message from sending a peer session a 4× error

The note was going to say *"~62 ms/article of overhead against 18.5 ms of compute, a 4×
multiplier"*. It came from pairing sadalsuud's `[timing] score` total over a **three-cycle**
window (1,209.1 s / 15 calls) with gpu-server's totals over a **twenty-hour** window
(1,656.8 s / 941 batches). Matched to one window: **0.30 ms/article and 1.18×.**

⭐ **The tell was absent, and that is the finding.** The *per-call* rates agreed across the two
windows — **80.6 s/call against 77.5 s/call** — so every sanity check on the pieces passed and
only the denominators were incomparable.

⭐ **"Recompute it a second way" would NOT have caught it.** Recomputing ms/article *confirms*
the error. It needed a quantity that cannot be formed without a shared denominator. The peer
independently offered "compute it a second way" as the generalisation, and sharpening it to
*"a way that cannot survive the specific confusion"* is the half that is actually load-bearing.

## The answer, after three of my own corrections

`docs/evidence/2026-09-04-scoring-overhead/`, **EXP-021**. Window 2026-09-03 06:20:46Z →
2026-09-04 11:31:00Z (**29.17 h, 8 cycles**, 146,433 articles), both journals asserted to
*cover* it.

| layer | total | per article |
|---|---|---|
| sadalsuud blocks on `score` | 3,127.1 s | 21.36 ms |
| gpu-server HTTP handler | 3,083.8 s (98.6%) | 21.06 ms |
| model compute | 2,647.5 s (84.7%) | 18.08 ms |
| → client + network | **43.3 s** | **0.30 ms** |
| → in-server, non-compute | 436.3 s | 2.98 ms |

**Multiplier 1.18×.** Whole pipeline **5,846.5 s / 29.17 h = 5.57% duty cycle**: `score` 53.5%,
**story dedup 42.4%**, prepare+rescore+write 4.1%.

⭐ **The filter probes do not run on sadalsuud.** But dedup does its own `multilingual-e5-large`
pass, and **at most 4.4% of dedup is GPU work** (`POST /embeddings/encode`, 107.8 s against
dedup's 2,477.5 s). **What the other ≥95.6% IS was not established** — clustering plus embedding
client overhead, not separable without instrumenting dedup.

## ⛔⛔ Three corrections, all mine, all the same shape, each landing after logging the last

1. **Two windows** (above).
2. **A config read presented as a runtime proof.** *"The e5 probes do not run on sadalsuud at
   all"*, from `require_gpu: true` + `cpu_fallback.enabled: false` + `host: gpu-server`. Those
   keys are under `scoring:`; dedup is a *preprocessing* stage and never consults them. ⭐ **The
   config predicted the OPPOSITE** — sadalsuud has no GPU and `story_dedup.py`'s loader falls
   back to `device="cpu"` — so only the log settles it, in both directions. Flagged by the
   NexusMind peer, whose own mechanism (CPU e5-large on sadalsuud) the log then refuted; they
   had read `story_dedup.py` and missed that `main.py:2648` injects a GPU embedder.
3. ⭐ **A subtraction named as a category, twenty lines after logging (2).** *"86% of dedup is
   clustering on sadalsuud's CPU"* subtracted the `Centroid migration … embed_seconds=` timer —
   which times **only centroid re-embedding** — from dedup's wall. The article embedding pass is
   untimed on that side, so the remainder still holds its blocking HTTP wait. **The remainder of
   a subtraction is not a category; it is whatever is left, and it inherits every consumer
   nobody enumerated.**

Plus: *"every run logs `Story dedup: using GPU embeddings via gpu-server`"* — told to the peer —
is **false**; it was **7 of 8**, and the instrument cannot express "CPU" at all, because the CPU
branches log a phrase without the word `using`. `devices` was a `set`, and a set of size 1 is
produced identically by 1 of 8 runs and by 8 of 8.

## ⛔⛔ VERIFICATION IS NOT REVIEW — fourth consecutive session

Green throughout: 667 tests (1 pre-existing failure, #139), refcheck 0 dead, the registry
checker, both budget guards, `run_verify_annotations` 21/21, the structural markdown pre-check
0 violations. **`/review-changes` (4 lenses) then found 4 blockers and ~20 warnings**, including
every one of the three corrections above.

⭐ **The adversarial lens did not read the script — it stubbed `journal()` and ran 8 synthetic
scenarios through the real `main()`. 8 of 8 reported a wrong number and exited 0.** The
reachability lens independently found the same coverage gap and found (3).

⛔ **The live instrument defect: filtering a journal to a window is not the window being
COVERED.** Excluding over-coverage without under-coverage means a gpu journal starting after
`lo` gives one host the full window and the other a subset — **the same defect, the same
direction, every per-call rate still agreeing.** Demonstrated at **4.80× against a true 2.40×**.
⭐ **Every guard I had written was a refusal on an EMPTY read; the defect lives in a PARTIAL
one, and I had no word for that.** Checked on the real run rather than assumed: gpu-server's
journal begins 06:06:33Z against a window starting 06:20:46Z — covered. The `lo` gap a reviewer
flagged was the pipeline idling, not the journal being short.

## Also this session

- **H-V8-16 collision fixed.** Two hypotheses carried the id; the earlier (checkpoint selection,
  `d3a6f89`) keeps 16, the encoder-capacity one became **H-V8-18**, annotated in all three
  surfaces. ⚠️ Commit `93cdeac`'s subject still carries the retired id and cannot be rewritten.
- **New ledger rows: H-V8-19** (does the probe screen non-Latin harder? — REFUTED, the gap is
  entirely in the negatives) and **H-V8-20** (is tightening Stage-1 a compute trade only? —
  REFUTED, the probe's own scores become the published ones for screened-out rows).
- **Issues commented: #141** (truncation as a third thinning; the routing gap is not in the
  positives, so the Stage-1 gate is not what #141 must fix), **#128** (the tokenizer
  measurement — non-Latin shorter in chars, more tokens), **#100** (dedup priced; the encoder is
  14% of it, so a contrastive fine-tune changes quality, not cost), **#104** (the device gap
  showing up in a headline metric: recall 0.514 CUDA vs 0.486 CPU, one article).
- ⚠️ **Noticed, not chased:** `foresight` and `sustainability_technology` directories are still
  on sadalsuud although both were removed here 2026-08-03 (#43). They do not score — the
  measurement sees exactly five filters.

## Next session

**Phase 8 remains next and is unchanged: the op-point, on the calibrated scale, with the owner.**
Nothing here moves it. ⭐ **And the measurement removes the one thing that could have**: there is
still no Stage-2 cost constraint, which is what both the gating ruling and the "is the probe
enough" answer turned on.
