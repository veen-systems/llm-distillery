# Violence promotion v1 hypotheses — archive of closed entries

*Moved VERBATIM from `memory/violence-promotion-v1-hypotheses.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read surface), under
the 2026-09-27 ledger rule: entries whose verdict is closed (CONFIRMED / REFUTED / SETTLED / RESOLVED) move; open
entries, rulings and standing traps stay. Order kept; a block from inside a section repeats that section's heading.
Open questions, design decisions and the 2026-08-26 window section stay live.*

## Confirmed

1. **The binary-preinfilter recipe transfers cleanly.** Same frozen-embedder + MLP architecture (mpnet-base-v2 → StandardScaler → MLP(256,128)) that worked for commerce_prefilter and obituary_detector works for violence_promotion too. Inference code, oracle.py, calibration_report, CHANGE_REQUEST — the template is mature and reproducible.

2. **The prompt boundary holds on smoke tests.** The oracle prompt's core discriminator — "does this article make violence seem normal, acceptable, desirable, or a source of progress?" — produces correct classifications on the 5 canonical test cases (combat=0.997, recovery=0.035, weapons-as-progress=0.989, peace=0.000, borderline-economic-framing=0.721).

3. **DeepSeek is cost-effective for binary labeling.** 2,000 articles ≈ $0.45 total. The JSON response format with temp=0 produces clean parseable scores. Same pattern validated on obituary_detector.

4. **Shadow-deploy is the correct first step for prefilter classifiers.** The model has known gaps (recall 0.55, only 1,957 training samples) but shadow mode costs nothing in content loss. Production data will reveal which error classes actually matter.

## Settled 2026-08-01 (NM#281)

9. **The enforcement path now exists, default-off, and is a config flip.**
   `pipeline.violence_promotion.enforce: false` → `_enforce_violence_promotion()`
   in NexusMind's `scripts/main.py`. Flipping it after LD#82 needs no new mechanism and no
   deploy. **Caveat carried in the config comment:** at recall 0.55, enforcing
   gates roughly half of true positives — precision-first by construction, so
   question 5 below becomes an owner decision, not a modelling one.

10. **Fail-open is now an explicit decision, not an accident.** If the detector
    errors, articles are unstamped and **admitted**. Correct for a
    precision-first gate — fail-closed would empty the corpus on any model
    failure — but it means a silent model failure admits everything, with only
    an ERROR line as signal. `_enforce_violence_promotion` keys on `is True`
    (not truthiness) so unstamped and non-bool values can never cause a drop.

11. **The first gate implementation could not fire** (found by adversarial
    review the same day, before any flip). It was placed in `_is_duplicate`,
    which runs *before* violence stamping — `enforce: true` would have dropped
    zero while logging `0 violence`. Fixed in `b85a467`. **Lesson for whoever
    flips it: verify from the `Violence promotion ENFORCED: dropped N` line,
    not from `filtered_*.jsonl`,** which only ever contains survivors.

12. **Three run modes silently skip stamping entirely** (NM#286): single-filter
    runs, `--no-dedup`, and a shared-dedup exception all leave `_article_cache`
    empty, so the detector never runs. Combined with fail-open, those modes
    admit everything. Fix before enforcing.

## Settled 2026-08-23 — the audit ran, enforcement is ON and verified

**#82 closed as measured.** Full detail in `docs/BINARY_GATE_STANDARD.md` and #82's comments.
NexusMind `25d0ae2`: `enforce: true`, `threshold: 0.95`.

### ⭐⭐ Q5 and Q10 are both answered, and the frame was wrong

**Precision at 0.95 is 71–86%** (deepseek / qwen2.5, population-weighted over 3,200 flags;
judges agree on only 60/75 so treat it as a band). That is **below #82's own 0.90 bar** — and
enforcing anyway was correct, because **the bar was measured on the wrong population.**

⛔ **99.6% of flagged articles never reach a lens operating point** — 21 of 5,882, against 7.8%
for articles generally. A precision figure over all flags describes articles no reader could see.

⛔ **Q10's premise is refuted for this gate: raising the threshold does NOT buy usable
precision.** Across all flags it does (86% → 93% at 0.99), but among the 21 that *surface* the
scores interleave completely — the top scorer (**0.9988**) is a POW-exchange false positive and a
true positive sits at **0.9546**. Raising to 0.99 blocks 3 of the 21: 1 wrong, 2 right.
**Do not "optimise" the threshold later; the config comment says so.**

**What enforcement actually trades** (my adjudication of all 21, not a panel): ~10 correctly
removed (India's *"Big milestone: 1st 100% indigenous AK-203"* — in **`solutions`**; Ethiopia's
Air Force *"technological muscle"* at `uplifting` **5.31**; Air Assault Forces listing 26
liberated villages at **4.66**) against ~10 wrongly removed (UN clearing unexploded ordnance
*to protect civilians* at **5.39**; Syria–Russia ending military use of two bases at **5.21**;
Iraq's 6M-weapon registry at **5.34**; repatriation of bodies and 103 POWs). **Net-positive under
ADR-023**, and ~1 article/day either way.

### Q6 answered: it is a CLASS, not an outlier — and there are four

The Su-57-crash shape generalised. The FP classes, all inside v1's **own declared negative
class**: **de-mining / UXO clearance**, **disarmament and base-closure deals**, **weapons
registration / arms control**, **repatriation of remains and POWs**. Criterion 2 of #82 ("no new
FP classes") therefore **passes** — it fails at edges it already knew about.

`datasets/adverse/violence_promotion_hard_negatives.jsonl` — **8 confirmed** (both judges).
⛔ **Keyword harvesting was 92% wrong**: 244 candidates → 100 judged → 8 kept. Most POW/remains
matches are war roundups that genuinely *are* violence. ⭐ **Mine the SURFACING set instead** —
FPs run ~50% there vs ~8% among keyword matches. That is the v2 corpus strategy.

### ⭐ Q9 answered by accident, and it is the finding with the longest reach

Enforcing **removed the gate from the record**. `_is_violence_promotion` had 2 distinct values
only because it ran in shadow; from the next cycle it is **constant-`False`**, exactly like
`_is_commerce` and `_is_obituary` — which are constant across 25,122 rows not because they are
broken but because each gate's positives are dropped before persistence.
⛔ **Turning a gate on makes it unobservable.** The block ledger (`docs/BLOCK_LEDGER_SPEC.md`) is
the fix, and this is what makes it time-sensitive.

