# Session record — 2026-08-12 evening (fourth context of the day)

**Nothing deployed, no filter package touched, no oracle spend.** Eight commits,
all docs / memory / one analysis script. One issue closed, two commented, one
cross-repo evidence post. Five-message exchange with the FluxusSource session that
changed three of my conclusions.

---

## What the owner asked, and what happened

Opened as a status sweep — *"check sadalsuud, all outstanding hypotheses, GH
issues"* — then narrowed to **#106** and closed it, then ran the close ritual.

### sadalsuud: healthy

Cycle 16:02 → 17:06 exit 0, 0 failed units, load 0.03, disk 12%. `nexusmind` is
`inactive`/`disabled` between cycles — the `OnSuccess=` chain, not a missing
schedule. Stamps verified on that cycle: `content_length` **3,242/3,242** and
`stage_used` 100% in all six filters. `stage1_low` share ranges 9.8% (`uplifting`)
to **63.3%** (`solutions`) — most `solutions` rows carry a probe estimate, not a
Gemma score.

⚠️ **My first read of those stamps said 0/N.** Wrong path — `analysis.*` instead
of `nexus_mind_attributes.<lens>.*`. Caught only because the standing rule says
dump the keys before reporting an absence. Second occurrence of that exact trap in
two days.

**Observed, not previously written down: the per-cycle "above 4.0" line counts the
NORMALIZED score**, hardcoded at `scripts/main.py:1562` (again at `:3380`, parsed
into the dashboard by `generate_logs_summary.py`). It matches `weighted_average`
exactly (138 / 286 / 3) and is *not* the op-point count — `uplifting` reads 138
where **233** rows clear raw 4.5. Same family as ovr#304. Not filed; not a
regression; recorded here because the one number visible per cycle is not the
visibility number.

**`nature_recovery v4` clears the gate 0–3 times per cycle**, all 7 cycles in 24h
(0,1,2,3,0,3,3 on 2,000–3,700 scored). Standing state, not new — and the concrete
case for **#71**.

---

## #106 — CLOSED, then corrected the same evening

**Ruling: close as no longer load-bearing.** The residue is ≤0.128 normalized on
`belonging`, 0.0% of articles move ≥0.5, every enrichment-gate crossing is
downward — marginally *more* enrichment, the cheap direction under ADR-023.

**Then I over-scoped the supporting argument and the FluxusSource session caught
it.** I wrote that the deletion arm *is* the phase-out forecast, so the population
was being removed upstream anyway. Wrong: my arm deletes A+B+C; **ADR-007 retires
population A only** (55–59 country proxies). B (230 enabled) is out of scope and
hard by construction — those keys were repointed to GN *because* the native feed
died. **C (13 topic queries) can never be migrated at all**, so a permanent GN
floor exists regardless. No date and no rate **by design**: a proxy retires only
behind a native replacement verified collecting in production.

What survives: the decided deletion is strictly smaller, so the **safety** claim is
conservative in the right direction. What does not: *"stubs shrink by two-thirds"*
is the all-GN figure; the decided scope removes nearer **~40%** — recorded as an
order-of-magnitude caution, **do not quote**.

**Also corrected: FS#145 is an attribution instrument, not a migration lever.** I
had conflated it with ADR-007. It recovers a publisher *domain*; it yields no
fetchable URL.

The correction went on the issue as a second comment rather than a quiet edit.

---

## The H4 measurement — the durable output of the session

**Enrichment attempted 35,229 Google News proxy rows over nine days and replaced
ZERO of them.** 100.0%, CI 100.0–100.0, window 2026-07-31..08-08.

| arm | entered `pre_enrich` | C fail | C |
|---|---|---|---|
| `gdelt_constructive` | 147 | 1 | 0.7% |
| `gnews_eval` | 281 | 20 | 7.1% |
| `newsdata_eval` | 548 | 111 | ⚠️ 20.3% **pooling falsified — do not quote** |
| **`gn_proxy`** | **35,229** | **35,229** | **100.0%** |

**State it as mechanism + measurement, never as a bare number.** FluxusSource
predicted it pre-gate from the URL scheme alone (a GN `url` is an opaque redirect,
so the fetch reaches a Google interstitial, never a body). Two derivations from
opposite ends, neither depending on the other. **Consequence: it will not drift** —
a property of the URL scheme, not of enrichment tuning, so no fetcher or
consent-detector change moves it (which also bounds NM#309).

⚠️ **The window cannot be extended and there is no remedy.** From 08-09 all six
filters exclude `eval_aggregator`; the arms stopped upstream 2026-08-11T14:06Z.
`data/raw` is pre-enrichment; `shadow_mode` stamps forward-only. Both considered
and **rejected** with FluxusSource — do not re-propose either.

Posted to NexusMind#310 and llm-distillery#93.

---

## The instrument that broke, and how it was found

A peer verified my clean `grep` instead of taking it on report, ran a **positive
control**, and found what my pattern structurally could not see: the harness
prefix-matches a *tuple*, and I had grepped only for string literals inside
`startswith(`. Their own first attempt pointed at a nonexistent path and returned a
clean-looking negative — the better half of the lesson.

That surfaced a real defect: `measure_enrichable_rate.py` builds its arm list from
*what it found*, so when the arms stop appearing it prints the baseline alone and
exits 0. **Measured: all three arms went to zero on 2026-08-09**, four days before
anyone looked, with the gate two days out.

**Cause, resolved across two sessions — and it was OURS.** All three of my
candidates (ADR-007 retirement, free-tier expiry, an FS#163-shaped silent skip)
were excluded from FluxusSource's own health snapshot. The arms reach `data/raw` on
08-09..08-11; since **2026-08-08 07:43** all six filters exclude `eval_aggregator`
(NexusMind `9fb441a`) — the arms' own `type_classification`. Collected, ingested,
**scored**, then dropped by the NM#189 source filter. The exclusion is correct and
deliberate: before it, the arms were being *published* (30 rows in ovr.db,
including a funeral/murder story at tier `high`, #101).

**Nothing was broken. The instrument broke, by a deliberate fix to the thing it
measures.**

---

## Five stale claims fixed, and two blockers found in my own guard

Three stale comments in `measure_enrichable_rate.py`, all **true when written** —
which is what makes them dangerous, since no test or reviewer flags them:

1. `--lens` help: solutions drops no rows "measured 2026-08-06" — falsified by our
   own change 48 hours later.
2. docstring: `content_length` never persists — fixed 2026-08-08 17:10, re-verified
   3,242/3,242 today. Still true for windows ≤08-08, so the derivation stays.
3. usage example `--end 2026-08-14` — a gate that closed on 08-08, over rows that
   stop existing on 08-09.

Then **`/review-changes` (HIGH tier, 5 lenses) found two BLOCKERs in the guard I
had just added**:

- **It keyed on key presence, not rows.** `st` is a `defaultdict` and the
  `--drop-eval-query` cut touches `st[key]["eq_present"]` *before* its `continue`,
  so an arm whose every row was dropped as 'Chad' exists with `rows=0` and the
  guard stayed silent — **in exactly the case it exists for**. Proven with a new
  fixture: before, no banner, exit 0; after, banner. Same shape as the defect it
  was written to catch, one level down.
- **The banner contradicted the docstring I wrote in the next commit** — it told
  the reader to try `shadow_mode`, which the header forbids. The doc-accuracy
  lens's own rule landing on me: the diff shows what changed, never what the change
  contradicted.

---

## Carry forward

- **Framework: pinned v1.23.0, upstream v1.25.0 (`889b038`)** — unchanged at close,
  so the triage table in `docs/TODO.md` is current. **First task next session**, by
  owner instruction.
- **#109 Arm B** — held on the unnamed judge model. **#104** — CPU-vs-GPU.
- **#71** carries the `nature_recovery` refit constraints; nothing more to add
  there this session (checked — its 07:25 comment already covers the 397-vs-200
  floor and the deletion-vs-replacement caveat).
- **H-E1** (`nature_recovery`'s +0.023 per-dimension check) still open and still
  costs nothing — the paired scores are persisted.

## Lessons worth the space

- **A grep for a pattern is not a grep for a behaviour.** Mine matched string
  literals inside `startswith(`; a tuple-driven match was invisible to it.
- **Verify a negative with a positive control on the same instrument** — a
  mis-aimed search and a true absence produce identical output.
- **A comment explaining why code is safe is a claim like any other, and it
  expires.** Two of the three I fixed were true when written. Give such a claim a
  date, not just a rationale.
- **Verify that what is protecting you is not an accident** — the health snapshot
  that excluded three causes in one query existed only because a retirement
  happened to take a backup. Same shape as FS#164's broken purge.
