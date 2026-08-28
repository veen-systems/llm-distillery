# v8 Gate 0 — the three reserved corpus numbers, decided 2026-08-28

**Status:** owner-ruled 2026-08-28. **No spend, no draw, no training yet.** These are the
three quantities `docs/HUMAN_THRIVING_V8_PLAN.md` § Phase 0 deliberately left unstated so
they would be *chosen* rather than inherited. Gate 0 cannot pass without them.

**Evidence they rest on:** `docs/evidence/2026-08-28-v8-phase0-drawable-population.md`
(drawable population n = 179,111 articles, `news.google.com` excluded, window
2026-08-14 → 08-28; score-mass table over n = 160,641 stage-2 rows). ⛔ Every production
figure below is from the **drawable** population — the GN-inclusive census gives different
numbers for all five Gate 0 targets, which is what the 08-28 correction was about.

---

## 1. Positive base rate — **19.5%, an enrichment factor of 2.0× recorded, not accidental**

**Ruled:** draw to ~19.5% positives (raw weighted average ≥ 4.5), i.e. **2.0×** drawable
production's measured **9.76%**.

| | production (drawable) | v7 corpus | **v8 spec** |
|---|---|---|---|
| positive rate | 9.76% | 28.22% | **19.5%** |
| enrichment factor | 1.0× | 2.9× (accidental, unstated) | **2.0× (recorded)** |

**Why not "match production".** ADR-003 screen+merge enrichment exists *because* positives
are rare; a 9.76% draw spends the oracle budget on obvious negatives. The defect the plan
named was never that v7 was enriched — it was that 2.9× was **accidental and unstated**.
The fix is a recorded factor, corrected for downstream in class weighting or calibration.

**Why not keep 2.9×.** The corpus is already **4.21× over-weighted** in the visible band
(5.5–10) and **0.43×–0.68× thin** at 1.5–3.5, where stage-2 false positives are born and
where ADR-023 says the expensive error lives. Halving the factor is what frees budget to
move there.

**Derived, not ruled** *(my arithmetic from the ruling plus rule 2 below — check it against
the split, do not treat it as measured)*: at 19.5% with the positive mix held at 63.5/36.5,
the 4.5–5.5 band lands at ≈12.4% of the corpus and the 5.5+ band at ≈7.1%, i.e. ≈2.0×
production's 3.562% instead of today's 4.21×.

### Binding sub-rules carried from the plan (not re-decided here)

1. **Add no mass above 5.5.** Already 4.21× over-weighted; 15.8× at 7.0–7.5 and 134× at
   7.5–8.0.
2. **Hold the positive MIX at production's 63.5% marginal (4.5–5.5) / 36.5% high (5.5+)** —
   *not* the v7 corpus's 46.8/53.2. Enrich the positive **rate**; never reshape the positive
   **class**. This is the mechanism behind the FN trap in §2.
3. **Spend the freed budget on 1.5–3.5**, the thinnest region and the origin of stage-2 FPs.

---

## 2. Stage-1 aggressiveness — **hold near pass-through**

**Ruled:** retrain the e5 probe on the v8 corpus, but **do not screen harder**. Re-derive
the threshold only far enough to preserve today's routing (**88.6%** of articles to
stage 2); do not tune stage 1 for cost saving in v8.

**Why.** The probe's threshold of 1.00 was calibrated when MEDIUM was 4.0 and was never
re-derived after #102 moved the op-point to 4.5 — `config.yaml` calls it *"conservative
rather than tuned"*. That slack is the **only** reason its false-negative exposure is
small, because:

> v7's probe recall was estimated on a positive population **1.36× easier** than the one it
> serves. Production's positives are **63.5% marginal**; the v7 corpus's are **46.8%**.
> `P(pred < t | y = 1)` is invariant to how *common* positives are, but not to the
> distribution *within* the positive class — and marginal positives are exactly the ones a
> screen misses. **This is a live condition today, not a v8 hypothesis.**

A harder screen converts that slack into unrecoverable false negatives. The probe is a
recall-safe screen by design — the one place ADR-023's asymmetry is **inverted**, so the FN
is the expensive error there (`train_probe.py --objective recall`). The plan's own rule
applies: *a harder screen buys cost saving **and** FN risk; if the saving is not needed, do
not buy it.* No stage-2 compute constraint was claimed, so it is not needed.

**Still required regardless:** validate FN@MEDIUM+ on a **production-mix cohort**
(63.5/36.5) via `train_probe.py --recall-check-file` — never on the enriched val split,
which is the biased instrument this section is about.

⚠️ **This is a v8 decision, not a permanent one.** Re-open it only with a measured stage-2
cost problem in hand, and only with an FN ceiling named *before* the sweep.

---

## 3. Class-A supplement TP/FP balance — **3:1 TP:FP**

**Ruled:** of the harm-in-title ("class-A shape") rows in the corpus — target **≥ 0.70%**
of the corpus, matching drawable production — approximately **75% true positives** and
**25% false positives**.

| | shape | should score |
|---|---|---|
| **TP, ~75%** | harm *answered*: rescues, convictions, survivor recovery, restorative justice, falling harm rates | **high** — these are §5b shapes |
| **FP, ~25%** | harm is the **dominant subject**; the positive is incidental or absent | **low** — the class-A defect |

**Why not FP-only.** Stated in the plan and it is the whole point: a corpus carrying only
the false positives teaches *"harm words → suppress"* and **destroys the §5b no-regression
set** — whose rows (Brussels survivor meets perpetrator 6.55, $30M abuse settlement 5.85,
Myanmar amnesty 5.38) are precisely harm-lexicon-positive rows that must keep scoring high.

**Why deliberately FP-richer than reality.** §1g's screen found *most* harm-lexicon hits
above the op-point were true positives (158 title hits → 9 promoted class-A FPs + 5 parked
line calls). Mirroring that ~9:1 would leave roughly one supplement row in ten carrying the
defect signal. ⛔ **And no rate may be inherited from that screen anyway — the lexicon is a
candidate generator, not a population** (plan §1g). 3:1 is a chosen teaching ratio: enough
negative signal for the rule to learn, still TP-dominant enough that §5b survives.

⛔ **Sample the supplement ABOVE the op-point** (ADR-023): that is where junk reaches
readers. Do not hunt the cheap error below it.

---

## What this unblocks

Gate 0's remaining items are now execution, not decision:

1. Stage the corpus on b650 with a `corpus_manifest.json` (#127) whose counts **reconcile
   against a freshly prepared split** — not a `json.dump` in the code. The manifest records
   the **window**, not just the counts: the archive holds ~14 days and it **rolls**, so a
   draw taken next week is a different population.
2. Report the language/script distribution against production's (**non-Latin ≥ 9.76%**).
3. Report the short-form coverage (drawable p10 = **235 ch**, median **1,900**; under-floor
   share **11.93%** = 21,374 articles) — or state that the filter is long-form only.

⛔ **All of it before any oracle spend.**
