# solutions v6 dimension hypotheses — archive of closed entries

*Moved VERBATIM from `memory/solutions-v6-dimension-hypotheses.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read surface), under
the 2026-09-27 ledger rule: entries whose verdict is closed (CONFIRMED / REFUTED / SETTLED / RESOLVED) move; open
entries, rulings and standing traps stay. Order kept; a block from inside a section repeats that section's heading.
THE ONE REAL DEFECT, UNTESTED and TRAPS stay live.*

## CONFIRMED

**H1 — the dimension is real, it is just rare.** When the oracle scores it, it
spreads properly: n=397 across all splits, mean 5.09, median 5.0, range 1.0–8.5,
with coherent exemplars (Amul Dairy Cooperative 8.5, community forestry in Nepal
8.0, a Rajasthan "River Parliament" allocating water across 70 villages 8.0).
Verify: `PYTHONPATH=. python3 scripts/research/solutions_v6_reweight_ablation.py`.

**H2 — the student learns it BETTER than it learns the other six.** 1,032 test
rows, b650, GPU. Conditional correlation on oracle-positive rows **r=0.622, the
highest of all seven** (others 0.373–0.573); false-fire rate on true-zero rows
**4.0%, the lowest**. It is the most precise dimension the filter has, which
under ADR-023 is the property worth having. Verify:
`PYTHONPATH=. python3 scripts/research/solutions_v6_dim_fidelity_report.py`.

**H3 — the score ceiling really does differ by solution type.** Weights sum to
1.00 and Step 2 of the oracle prompt mandates zeros, so maximum achievable
weighted score is **7.50 for pure tech, 9.00 for governance, 10.00 for
community/hybrid**. This is arithmetic. It is also inert — see R2.

**H4 — the concreteness gatekeeper is inert on the training corpus too (#94).**
8,451 of 10,297 rows have concreteness < 3.0; **0** of them exceed the 3.0 cap,
max weighted average 2.600, margin 0.400. Second population agreeing with the
issue's 191,616 production articles. **The inertness is EMPIRICAL, not
structural** — a row at concreteness 2.99 could reach 8.60; it does not because
low concreteness correlates with low everything. #84's router rework could
decouple that.

## REFUTED

**R1 — "the dimension is dead."** Refuted three ways: labels (H1), student (H2),
and the miss hunt. Screening all 1,953 on-topic zeros twice — keyword pass (201
hits), actor-centred pass requiring the community to be the *doer* (112 hits, 42
at/above weighted 4.0) — and hand-reading the strongest yielded **2 genuine
misses, not 20**. The 83% is base rate.

**R2 — "re-weighting would recover the ceiling."** At matched surfacing volume,
renormalising over permitted dimensions swaps **11 of 1,628 articles (0.7%)**;
dropping comm+gov entirely swaps 17 (1.0%). It is a near-monotone rescale: it
moves the scale, it does not reorder. No weighting change is worth making.

**R3 — "re-weighting would fix NexusMind's enrichment starvation (NM#319)."**
⚠️ **The most dangerous refuted item here, because the measurement was clean.**
Re-weighting moves ≥4.0 from 31.1% to 50.6% (tech alone 15.6% → 56.8%), which
looks decisive. It is an artifact. NexusMind's gate reads
`result["weighted_average"]` (`article_fetcher.py:1355`), and
`production_scorer.py:16-17` overwrites that field with the **NORMALIZED** score.
Normalization is a percentile CDF, so a monotone rescale maps back to the same
percentiles and the effect vanishes at the next refit. **This was one code read
away from being recommended.** The ablation script now prints the interception in
section 3 so it cannot be re-derived as a win.

**R4 — a decomposition of the 83.1% into "40.0% tech-shaped + 43.1%
governance-shaped".** Circular: both categories are defined *using* `comm == 0`,
so they sum to the zero rate by construction. `content_type` is **not stored in
the training splits**, so the prompt's forcing rule cannot be verified from this
data at all. Retracted the same session it was written.

