# Session 2026-08-29 night → 08-30 — four hypotheses answered, the v8 corpus drawn twice, and five errors of mine that review found

**Spend $0.1252** (227 DeepSeek calls, 0 errors) across three experiments. **No model trained,
no threshold moved, no probe retrained, nothing in `filters/` changed, nothing deployed —
deploy is N/A, not skipped.** Six commits `b87b75e..5481419`, pushed through `edccb53`.

## What was answered

**H-V8-6 — is k=3 enough?** Yes, and the reason is priceable. A beta-binomial fitted across rows
gives P(the k-majority differs from the limit verdict): arm A production-mix **3.750% → 2.452% →
1.945%** for k=1/3/5. k=1→k=3 fixes **~86 rows of 6,590**; k=3→k=5 **~33 more**. The curve
flattens because the residual is rows whose gate probability is genuinely ~0.5 — #135's
*1/√k cannot touch a Bernoulli*, now with a price on each draw. Registry `EXP-001`.

**H-V8-9 — are the reorder's stricter labels better?** Yes, narrowly, and the safety half is
clean. Of 12 op-point crossings only **4 are stable in both arms**; on those the reorder is
right **3 of 4**. Separately, all three §5b no-regression articles were scored under both v8
arms **and** the v7 prompt: neither hazard is suppressed, and on the transitional-justice row the
reordered prompt is **best of the three** (+1.417 over v7). ⛔ The third row fails `raw > 4.5`
under **every** prompt including v7 — **acceptance criterion 2 is failing today**, which is a
defect that predates v8. `EXP-002`, `EXP-003`.

**H-V8-8 — does the repeat discount survive?** ⛔ **No, and it never existed for a corpus pass.**
The prefix cache *does* survive: 200 calls at t+0/30/60/90 min, every row hitting **exactly
10,368 tokens**, zero cold-prefix rows, flat 88.7–89.4%. But Phase A's cheap repeats were
re-scores of **the same 200 articles**, so the whole request cached. A corpus pass scores 6,590
*different* articles each time. Measured on fresh rows: **$0.000506–0.000534/article/pass**.
⇒ **k=3 over 6,590 rows is ≈$10.32 reordered / ≈$54.08 as-is, not $6.92** — landing exactly on
Phase A's own no-discount branch. **The reorder is 5.2× cheaper at corpus scale, measured.**
`EXP-004`.

**#127 — the corpus.** Drawn, staged on `b650-gpu:~/v8_corpus/` with a 600-row held-out
production-mix cohort, the manifest, and the pool so the draw re-runs after the archive rolls.
All six checks pass, including the two SHAPE clauses that previously had **no implementation**.
Visible band **3.74× → 1.95×**; low-middle **0.61× → 1.00×**. `EXP-005`.

## ⛔⛔ Five of mine, every one found by review, not by me

1. **A headline "independent validation" that was an ALGEBRAIC IDENTITY.** Over three draws,
   pairwise disagreement ≡ (2/3) × non-unanimity — always. "Four for four" was the in-sample fit
   residual rescaled and relabelled. **The sibling Phase A README already warned about that exact
   collapse**, and I re-imported it as corroboration.
2. **The class-A supplement sampled BELOW the op-point**, against a verbatim `⛔` in the spec.
   The 12 rows scored 1.16–2.08 — rows the student already gets right, so the arm was inert as a
   teaching signal, while the manifest reported PASS.
3. **A false control claim.** I said my histogram reproduced the census's "to within one row per
   bin (bin-edge convention differs)". It didn't, and it wasn't a convention: **CPython 3.12
   changed `sum()` to compensated summation**, and 34 of the same 6,590 rows land in different
   bins. I dismissed a real instrument disagreement and then used the false agreement as proof of
   same-instrument. *(A dismissal is a claim.)*
4. **A hand-built instrument under a comment claiming it was the census's.** My non-Latin
   detector was 50%/400 chars; the census's is 15%/2000. **This retracted a question I had put to
   the owner** — with the right ruler the pool is 9.74% against a 9.76% target.
5. **Two of my own background mutation runs raced and left the SOURCE mutated in the tree**, and
   a third run's `finally` overwrote my repair. Caught by one failing test whose numbers made no
   sense against the code I believed was there. ⭐ The staged corpus was cleared by comparing the
   manifest's `generator_sha256` to the repaired file — **an artefact that records the hash of
   its own generator can answer a question its author cannot.**

⭐ **Also fixed, from review:** clause (c) "spend the freed budget on 1.5–3.5" had **no
implementation** (negatives were copied from the pool at ratios 1.0006/1.0000/0.9999 — proof of
nothing happening); the FN-check cohort was silently deferred though the corpus *is* the probe's
training set; the positive class was being reshaped on the **script** axis (pool 0.917× → 0.994×,
then my over-correction to 0.434×, now 0.899×); `domain_of` used `.lstrip("www.")` — a character
set — mangling 1,897 rows; id-dedup is not text-dedup (1,450 rows); and the gate was one-sided
enough to pass a **29%** corpus against a ruled 19.5%.

## New infrastructure

- **`experiments/registry.jsonl`** — adapted from `veen-systems/augur`. Its registry only: this
  repo already has augur's hypothesis log (`memory/hypothesis-ledger.md`) and its evidence
  directories go further than augur's `artifacts` field. Adaptations: `spend_usd` required and
  never null; `subject`/`oracle`/`population` instead of `features`/`hyperparameters`; and
  **number traceability enforced** — augur's own `EXP-031` was an audit that found 19 untraceable
  numbers, so adopting the format without the check would have been adopting the defect.
  Backfilled `EXP-001..005`, 24 metrics, 0 untraceable.
- **`docs/HUMAN_THRIVING_V8_JOURNAL.md`** — the v8 build as one ordered chain, spend per row.
- **`scripts/corpus/{draw_v8_corpus,materialise_corpus}.py`** + 24 tests, mutation-tested.

## Next session

**Four owner decisions, all in `docs/TODO.md`:** adopt the reordered prompt (three independent
lines now favour it); fix or drop the no-regression row that fails criterion 2 **today, against
v7**; rule the class-A ratio question (the corpus reading is unreachable — 62 rows needed, 59
exist); and size Phase B's labelling run.
