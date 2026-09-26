# 2026-08-23 evening — a prompt fix, then a 26-day stall broken in production

**Spend ≈$0.49 estimated** (Gate A re-runs ≈$0.47, DeepSeek judging ≈$0.02). **One production
change**, verified. 9 commits llm-distillery, 2 NexusMind, all pushed.

Started at "where were we" on `human_thriving` v8. Diverged — via lens overlap → a crime-detector
idea → the violence filter — and the divergence produced the day's most valuable result.

---

## 1. `human_thriving` v8 step 1 — the diagnosis was wrong, and that was the finding

⭐⭐ **"Gemini ignores step 1" was wrong. Step 1 was OUTVOTED by five later instructions.** Found
by reading **dimension-level** output instead of the weighted average: Gemini's v8 scores on the
arrest row were *identical to v7* (`evidence_level` 7.0 every run, so the gatekeeper never got a
chance) and DeepSeek's pass came from step 2b alone. **Step 1 fired on neither oracle.**

Six contradictions, five *after* step 1: `STEP 2`'s "COMPLETELY INDEPENDENTLY"; §4-D's surviving
`>50%` doom test at `max_score 4.0` plus its investigative-journalism exception; §4-E's
`individual_crime` at 3.0; §7 reminders 8–9 restating both **in the recency position**; and an
output schema recording **no scope decision at all**. ⛔ **Every cap was inert** — `content_type`
has no consumer (v7 declares `content_type_caps`, ships no `postfilter.py`).

**Fix:** all six, plus `dominant_subject` + `scope_verdict` as the first two JSON keys binding
every dimension, plus the **occasion test** (*background does not displace the occasion; length
does not vote*). **Class A 4/9 → 9/9 DeepSeek, 4/9 → 8/9 Gemini; class B 3/3 both. The 4.4-point
oracle disagreement is closed** (arrest row 1.00 / 1.05). ⭐ Run-to-run spread collapsed
unprompted: Gemini max **5.25 → 0.80**.

Detail: `docs/evidence/2026-08-23-step1-rewrite-r2-r3.md`,
`memory/uplifting-oracle-genre-hypotheses.md`.

## 2. Two owner rulings

- **Accountability = IS ANYONE BETTER OFF**, not "was it delivered". ovr `BRAND.md` says a harm
  *"only"* answered fails — so a conviction with no named beneficiary is 0-2, while a settlement
  paid, an amnesty releasing people, remains returned are in. My "arrest out, conviction in"
  reconciliation was too generous and is superseded.
- **Money committed is not a protection established.** Rwanda's $46M leaves the no-regression set.
- ⛔ **Neither has a test.** The 15-row gate set contains no accountability row. **Oldest debt.**

## 3. ⭐⭐ violence_promotion: 26 days of shadow → ENFORCING and VERIFIED

The answer to *"why was it never effectuated"* is that **it was** — as a shadow run since
2026-07-28, stamping 100% of rows. What never happened was the flip, gated on #82's audit. **The
audit was blocked on nobody reading 11,826 flagged rows already on disk.** It took an hour.

**Precision 71–86%** at the live 0.95 — *below* #82's own 0.90 bar. Flipped anyway, and correctly:
⛔ **99.6% of flagged articles never reach a lens op-point** (21 of 5,882 vs 7.8% generally), so
the bar described articles no reader could see. Among the 21 the trade is ~10 weapons-glorification
articles removed (India's *"Big milestone: 1st indigenous AK-203"* — **in `solutions`**; Ethiopia's
Air Force at `uplifting` **5.31**) against ~10 good ones lost (UN clearing unexploded ordnance
**5.39**; Syria–Russia base closure **5.21**; Iraq's 6M-weapon registry **5.34**). **ADR-023
answers that in one line.**

⛔ **The threshold is NOT the lever** — among the 21 the scores interleave: top scorer **0.9988**
is a POW-exchange FP, a TP sits at **0.9546**. The config comment carries this.

**Verified:** *"dropped 444 article placements across 6 filters"*, **444 = 74 × 6 exactly**, none
of the 74 in that cycle's output. #82 closed; NexusMind `25d0ae2`.

## 4. Four documents, and a naming decision

- `docs/BINARY_GATE_STANDARD.md` — the three gates are **one machine** (~95% identical code).
  ⭐⭐ **Only violence writes what it blocks**; commerce and obituary enforce in production and
  keep no record, so their FPs are unobservable by construction. `save_blocked: true` has **no
  consumer**. ⚠️ **commerce runs v1, not v2** — deliberate rollback.
- `docs/BLOCK_LEDGER_SPEC.md` — P0 (owner idea): stamp `_blocked_by` at the drop point; **the
  reason string already exists and is thrown away**. Owner ruling: *what is done is done* — mark
  blocked articles processed, which also ends ~22,000 re-evaluations per cycle.
- `NexusMind/docs/ARTICLE_RECORD.md` — **owner-named**. 132 fields, declared nowhere until now.
  Deliberately not a contract (no counterparty: **0 of 6,000 ovr.db rows carry any gate stamp**)
  and not a schema. Generated, not hand-edited.
- **#129** filed (crime detector), **deliberately parked** until violence proves the pattern.

## 5. ⛔ Five self-corrections

1. **A verification that scanned zero files reported CLEAN** — UTC-named flagged files vs
   locally-named filtered files. 2nd occurrence of *prove the instrument could say yes*.
2. **"Aged out of retention"** — the 730-day archive had all four articles.
3. **"Violence adds an eighth reason string"** — it produces **none**; it just does not append.
4. **commerce v2** — v1 is live, deliberately.
5. **The date** — everything dated 2026-08-24; it was the 23rd, and it reached a production config.

⭐ Four of the five were in the last hour of work. Stop earlier.

## Next session

`docs/TODO.md` top block. Three independent threads: **🅐 the v8 accountability control set**
(oldest debt, ~$0.24), **🅑 the block ledger** (now time-sensitive — enforcing violence removed
the last gate signal from the record), **🅒 populate The Article Record**.
