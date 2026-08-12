# Session 2026-08-12 — three owner rulings, a measured residue, and two framework releases

**Shape of the session:** a decision session that turned into a measurement
session and then a framework-adoption session. Nothing was deployed. No filter
package, model, adapter or `normalization.json` changed.

## The four open rulings — three answered

| item | outcome |
|---|---|
| **#107** — does `uplifting` need a pleasant subject or only a positive outcome? | **RULED + CLOSED: positive outcome suffices.** Also settles the three held adjacent-lens rows (coffee frog, Buenos Aires estancia, Antalya nomadic tents) |
| **#109** — the label-correctness instrument | **Arm A approved** (cd v5 cross-oracle re-score, ~$1.20). **Arm B held on gaps 1–4** |
| **#106** — does `belonging`'s specificity on stubs still matter? | **Owner chose "measure the residue, then rule."** Measured; awaiting the one-line close |
| **should ovr.news enrich** | Still deferred behind ovr#312. Unchanged |

**#107's ruling is status-quo-confirming, so nothing ships.** The owner added
that a retrain is wanted anyway; the home for any subject-weighting work is
`human_thriving` v8 (ADR-012 amended, #90), scoped against **#91's** mechanism —
which this ruling explicitly does **not** cover, because there the dominant
subject and the scored text *disagree*.

**#109's blocker was never cost** (≤$7 both arms; Arm B can be $0 on b650 with
local judges). It is that Arm B's judge model is unnamed and the obvious default,
Gemini Flash, is the model that *made* `investment_risk v6`'s labels. Precedent
for the fix: cd v5's 4-oracle consensus (Qwen3:14b, Phi4:14b via
`scripts/score_ollama_oracle.py`).

## The #106 measurement — and why it was worth running

The "close it" option rested on the normalization-CDF residue being negligible.
**Nobody had measured it.** Method: fit the repo's own CDF twice per filter on the
same population — once as-is, once with Google News removed, same `anchor_min` —
and apply both mappings to the non-GN articles, so GN presence is the only
variable. GN matched on `'news.google.com' in url`, never a `gn_` key prefix.

| filter | GN % of fit | max normalized Δ | crossing normalized 4.0 |
|---|---|---|---|
| `uplifting v7` | 3.4% | 0.077 | 119 (0.78%) |
| `investment_risk v6` | 9.1% | 0.048 | 101 (0.28%) |
| `cultural_discovery v5` | 2.8% | 0.077 | 23 (0.62%) |
| `belonging v1` | 3.4% | 0.128 | 60 (1.12%) |
| `nature_recovery v4` | 12.1% | **0.367** | 3 (0.86%) |
| `solutions v6` | 16.5% | 0.234 | 84 (1.13%) |

**Three findings worth more than the table:**

1. **The op-point already de-selects GN in four of six filters.** GN is ~24% of
   scored passers per lens directory but 2.8–3.4% of the `uplifting` /
   `cultural_discovery` / `belonging` fit populations. The models score the stubs
   below the op-point — correct behaviour, not luck.
2. **The direction is one-way and it is the cheap direction.** Every article that
   crosses NexusMind's normalized-4.0 enrichment gate crosses it **downward**;
   zero go the other way in any filter. GN's low-end mass *inflates* percentiles,
   so its presence causes marginally **more** enrichment. It cannot surface
   anything — visibility is `raw >= op-point` (ADR-022).
3. **The largest residue is not the filter the issue was about.** `nature_recovery
   v4` at 0.367 is a **small-fit** problem: 397 rows against a
   `MIN_NORMALIZATION_ARTICLES` floor of 200. Carried to **#71**.

Evidence: `docs/evidence/2026-08-12-gn-share-of-normalization-cdf.md`. Reproduce:
`PYTHONPATH=. python scripts/research/gn_normalization_cdf_share.py --ssh sadalsuud`.

## The GN phase-out question, answered with a rate

The owner asked whether this matters given GN is being retired. **Measured: no
detectable decline.** GN share of scored passers by day, all 85 cycle files,
2026-07-29 → 08-12:

| | mean of daily shares | **pooled** |
|---|---|---|
| first half (07-29 → 08-04) | 25.03% | **24.83%** (25,608 / 103,152) |
| second half (08-05 → 08-12) | 24.34% | **23.69%** (30,811 / 130,084) |
| whole window | — | **24.19%** |

**Quote the pooled share, not the mean of daily shares** — daily row counts vary
8,403–21,618, so the two are different quantities. Caught by this session's own
review battery *after* the mean-of-shares number had been posted to
FluxusSource#145; corrected there the same session. The gap is −1.14pp pooled vs
−0.69pp by mean-of-shares, so the correction leans *slightly* toward a decline and
**changes nothing**: still well inside the 19.8–29.5% daily spread.

FluxusSource moved **6 of ~59** proxy feeds on 2026-08-08 and what improved was
*length on those feeds* (median 89 → 326), not GN volume. **A decline of a few
points would be invisible at that spread — read it as "not yet detectable", not
"not happening."**

**The reframe that matters: the experiment IS the phase-out forecast.** Removing
GN from the pile is what a completed migration does, so the deltas above predict
the post-migration refit — a small downward step, arriving all at once whenever
someone refits, since `normalization.json` is fitted manually and committed.

**And 0.367 is a floor, not a ceiling.** Migration *replaces* rather than
*deletes*: removing N low rows drops both the count below an article and the
total, while replacing them with rows scoring above it drops only the count below.
The second pushes percentiles down further. **Arithmetic, not measured.**

Notes posted to **#71** (refit + the interaction with v5's plan to lower the cut
below 3.5, which pulls *more* GN into the fit) and **FluxusSource#145** (with a
request: ping us at a migration milestone so all six refit in one pass).

## Framework: v1.21.0 → v1.23.0

Last session recorded v1.22.0 as "an unreleased candidate branch in another
session's checkout; do not pin it". **Both v1.22.0 and v1.23.0 released that same
evening.** Triage: 2 adopted, 0 declined, 1 n/a, 2 already in force, 1 deferred —
`docs/decisions/framework-adoption-history.md`.

**The substance was v1.22.0's verify runner, and its adopter action was real.**
The framework's own changelog measured this repo at `12 pass, 9 fail, 5 error,
3 malformed`. After commit `6a96271`'s repairs plus today's: **25 pass, 0 fail,
0 error, 0 malformed, 6 manual, exit 0**, all 38 annotations accounted for (7 are
prose mentions inside code spans — 6 in `memory/gotcha-log.md`).

⚠️ **One annotation needs `VERIFY_TIMEOUT=120`** — the LD#92 DiD check is a
source-clustered bootstrap taking ~50s against a 30s default. It is **not
broken** (verified exit 0). It is annotated in place so a future default run does
not read a timeout as a broken claim.

## What I got wrong

1. **A twelve-line `<!-- verify: -->` annotation that had never run** — backing
   the NexusMind#300 "100% populated" claim, a claim that had *already regressed
   once* after being called fixed. The file looked annotated. **10th occurrence
   of the unreachable-mechanism catalogue**, and the lesson generalises: an
   annotation, a test and a check are mechanisms too.
2. **A JSON argument does not survive `ssh`** — the research script failed on its
   first end-to-end run. `ssh host cmd arg` hands a *string* to a remote shell,
   which re-splits it. Caught only because the skill's rule is to run the script,
   not to ship it read.

Both in `memory/gotcha-log.md`.

## Next session

`docs/TODO.md` top block is current.

- **#106** needs a one-line close (or a decision to keep it open) — the
  measurement supports closing.
- **#109 Arm A is the only runnable work.** ~half a session of build. **The cd v5
  splits are NOT on the workstation** — they live on b650-gpu at
  `/home/jeroen/llm-distillery/datasets/training/`.
- **#109 Arm B** needs a non-Gemini judge named before anything is spent.
- **ovr#312** — wait for the number before re-opening the enrichment question.
- **Deferred:** v1.23.0's `<!-- placeholder -->` markers, to the next
  `audit-context` run.

⚠️ **`CLAUDE.md` is over the 35k soft target** (36.6k, under the 40k warning).
Table padding is not the cause and the footer is already a pointer; getting under
needs a structural decision. **Flagged, not taken** — second session running.
