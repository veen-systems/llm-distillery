# H-V8-8 — does the k=3 repeat discount survive at corpus scale?

**Written before the first call. 2026-08-29.**

## The claim under test

Phase A runs 2–3 cost **$0.000266/article** against run 1's $0.000519 because the identical
prompt came back **~1 minute later** and DeepSeek served the prefix from cache. A 6,590-row
corpus pass takes **~30 minutes**, so by the time pass 2 starts, pass 1's prefix may be gone.
**DeepSeek's cache TTL has never been measured here.** The k=3 corpus cost (~$6.9 vs ~$21.7)
rests on this assumption.

## Design — and why it is NOT "re-score the same rows"

⛔ The obvious design (score 50 rows, wait, re-score **the same** 50) measures the wrong thing:
it lets the *article text* be cached too, which a real corpus pass never gets — every article in
a corpus pass is new. The only thing a corpus pass can reuse is the **shared prompt prefix**.

So: **four disjoint sets of 50 rows** from the 200-row Phase A cohort, one per lag. Any cache
hit at t+30 is the template prefix surviving 30 minutes with *different* article text behind it
— which is exactly the corpus-pass question.

| pass | rows (cohort order, seeded shuffle `seed=8829`) | lag |
|---|---|---|
| P0 | 1–50 | t = 0 |
| P1 | 51–100 | t + 30 min |
| P2 | 101–150 | t + 60 min |
| P3 | 151–200 | t + 90 min |

Prompt: **`prompt-candidate-tail.md`** (the reordered arm). It is the only arm where this
question exists — the as-is prompt puts the article near the front and measured **0.0%** cache
on its first pass, so its prefix is broken by construction.

Readout: `prompt_cache_hit_tokens / prompt_tokens`, per row (persisted since 2026-08-28) and
aggregated per pass.

## Predictions, stated before looking

- **P0 hit rate: 85–92%.** Phase A arm A run 1 measured 89.2% (a 200-row pass warms its own
  prefix after the first row or two).
- **P1/P2/P3 hit rate: 85–95% if the TTL exceeds 90 minutes; near 0–5% if it does not.** I
  expect **the former** — my prior is that DeepSeek's cache is measured in hours, not minutes.
  ⚠️ I have not read a documented TTL and am not going to infer one from vendor prose; that is
  the point of measuring.
- **A partial result is possible and is the most interesting outcome**: a hit rate that decays
  (e.g. 89% → 89% → 40% → 0%) would put the TTL *inside* the window a corpus pass occupies.

## Instrument check — can it say "no"?

Yes, and it already has — **twice, on this exact code path**:
- today's no-regression run, **arm B run 1 at 18:15:53**, printed **0.0%** cache hit — 78
  minutes before this file was written;
- the Phase A batch's arm B run 1, **2026-08-28**, printed **0.0%** over 200 rows.

⛔ **A first draft of this line said the Phase A observation was "four hours ago". It was
~28 hours** — the Phase A runs are dated 08-28 and only their write-up is dated 08-29, which
the directory name (`2026-08-29-v8-phase-a-k3`) hides. Caught by the doc-accuracy review lens.
A zero here would be a real zero, not a dead field.

## What a result means

- **All four ≥85%** → the k=3 discount survives; ~$6.9 for a reordered k=3 corpus pass stands.
- **Decay inside 90 min** → k=3 as three separate passes is mis-costed. The fix is already
  named in the ledger and costs nothing to adopt: **schedule k=3 as three back-to-back calls
  per article** rather than three passes over the corpus.

⛔ This measures **cache**, not labels. It says nothing about which prompt to adopt.

---

## OBSERVATION LOG — appended after each pass, never edited above this line

**P0, 19:33:41 → 19:33:51. Cache hit 99.5%, 50/50 rows OK, 0 errors.**
⚠️ **Prediction MISSED, and the miss is the finding.** I predicted 85–92% for P0 on the
assumption it would start cold and warm itself. Measured: **zero rows had a full-prefix miss**
(max miss 128 tokens, median 65 — the article tail only, which is all the reordered prompt
leaves uncached). The prefix was **already hot**: the last call carrying it was the
no-regression run at **18:15:45**, so it had survived **77.9 minutes of inactivity** before P0
touched it.

⭐⭐ **That accidental gap is larger than any lag this design was going to test, and it
reframes the hypothesis.** H-V8-8 asks whether the k=3 repeat discount survives a ~30-minute
corpus pass. But a corpus pass **calls continuously** — every article re-warms the shared
prefix — so the prefix never goes 30 minutes unused during one. The TTL only has to exceed the
gap *between* passes, and it is already measured at ≥78 minutes.

⛔ **This does not close H-V8-8 yet** and the scheduled passes still run: one accidental
observation, one prefix, one time of day. P1/P2/P3 test 30-minute gaps deliberately, with the
per-row miss distribution recorded rather than the aggregate alone.
