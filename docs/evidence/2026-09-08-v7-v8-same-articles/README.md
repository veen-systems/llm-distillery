# uplifting v7 vs human_thriving v8 — the same articles, the free comparison (2026-09-08)

⛔ **Headline: the cutover is not a swap, it is a 7× cut.** On the **same 15,372 production
articles**, `uplifting v7` surfaces **1,184** and `human_thriving v8` surfaces **168**. v8 is
almost a subset of v7 (**152 of 168 = 90.5%** of v8's passers also pass v7), so at cutover the
Thriving tab **loses 1,032 articles and gains 16**.

⛔ **And it is NOT a threshold difference — tested against a null that could have said so.**
Volume-matched (v8's top 1,177, i.e. an op-point of 2.820 instead of 4.50) only **57.5%** are v7's
passers. The live alternative is *"v8 is a noisier, rescaled v7"*, so that null was built: monotone
noise on v7, tuned until its Spearman with v7 **matches v8's**, then quantile-mapped onto v8's
exact marginal. It gives volume-matched overlap **76.8%** [75.9, 77.8] and within-union rho
**0.5630** [0.5318, 0.5897], against v8's **57.5%** and **0.3436**. Both are far outside. Lowering
v8's bar does not reconstruct v7's feed, and neither would adding noise to v7.

⚠️ **Two corrections to the first version of this file, both from the same-day review, and the
second one is the reason the null above is decisive.**
1. The within-union figure read **0.224**: the script ranked over all 15,372 rows and then
   correlated those *global* ranks inside the 1,200-row subset, which is not Spearman.
   `scipy.stats.spearmanr` on the committed manifest gives **0.3463** on that frame.
2. §2 was computed over **all** rows, which mixes instruments — 3,162 rows carry a Stage-1 **e5
   probe estimate** rather than a Gemma score on at least one lens. On that mixed frame the noise
   null gives overlap **64.4%** and rho **0.3654** [0.3281, 0.4172] against actual 57.0% / 0.3463:
   **the actual sits inside the null's range, so the published evidence did not exclude the very
   thing its headline claimed.** On the clean both-stage2 frame it is excluded decisively. The
   conclusion was right; the evidence for it was not.

⚠️ **This measures WHAT CHANGES, not which is better.** There are no labels here. `EXP-029`
measured v8's live scope precision at **0.968**; no comparable number exists for v7 on live
output, and judging the 1,032 dropped rows is the part that costs money. **This is the free half
of #151's Blocker 3, and it is the half that was missing.**

Reproduce:

```bash
D=docs/evidence/2026-09-08-v7-v8-same-articles
# on sadalsuud (20-50 MB per cycle per lens; extract there, analyse here)
scp $D/extract.py $D/extract_lenses.py sadalsuud:/tmp/
ssh sadalsuud 'python3 /tmp/extract.py /tmp/v7v8_records.jsonl'
ssh sadalsuud 'python3 /tmp/extract_lenses.py /tmp/v7v8_lenses.jsonl' 2> $D/extract_lenses.txt
scp sadalsuud:/tmp/v7v8_{records,lenses}.jsonl /tmp/
python3 $D/compare.py /tmp/v7v8_records.jsonl /tmp/v7v8_lenses.jsonl $D/union_manifest.jsonl
python3 $D/flip_overlap.py
```

⚠️ **The two intermediates are NOT committed** (32 MB), and sadalsuud retains `filtered_*.jsonl`
for about 14 days — so §2 becomes unreproducible once these four cycle files age out. §1, §3, §4
and §5 all re-derive from the committed `union_manifest.jsonl` indefinitely.

Committed output: `compare.txt`. Committed data: `union_manifest.jsonl` — the 1,200 rows either
lens surfaced, with both raw scores, the set each falls in, and which other lenses carry it.
`flip_overlap.py` / `flip_overlap.txt` cross-check the sets against `EXP-029`'s prompt flips and
need no inputs beyond the two committed evidence directories.

## Population

Four **consecutive complete cycles**, both lenses, paired by collection cycle rather than by
filename timestamp (each lens stamps the moment *it* finished):

| cycle | uplifting file | human_thriving file | articles |
|---|---|---|---|
| c1 | `filtered_20260907_175421` | `filtered_20260907_180414` | 6,210 |
| c2 | `filtered_20260907_212528` | `filtered_20260907_213122` | 3,189 |
| c3 | `filtered_20260908_012236` | `filtered_20260908_012812` | 2,954 |
| c4 | `filtered_20260908_052700` | `filtered_20260908_053231` | 3,019 |

⚠️ **c1 is the backlog cycle** (#152, the pipeline outage). It is **2.45×** normal by the 09-08
panel's own denominator and **2.03×** against the mean of c2–c4 here — two denominators, one
cycle; the label is inherited, not re-derived in this evidence. The per-cycle v7/v8 ratio is
**6.3×–7.7×** with c1 at 7.5×, so the finding is not a c1 artifact — but absolute counts here are
four cycles, not a per-cycle rate.

⚠️ **What this source excludes:** `filtered_*.jsonl` is written under an
`if result["passed_prefilter"]` guard and also drops source-type-excluded rows, so it is not the
collector's population. That does not bias *this* comparison — both lenses are read through the
same guard, and the two article sets are **identical**: symmetric difference **0** in every cycle,
checked on sets and not on counts. **The range over which they could have differed is the whole
cycle** — up to 6,210 rows in c1 — because each lens keeps its own `processed_ids` file and its
own prefilter state.

⭐ **And the instrument could have said otherwise.** Per-lens pools in this same data *do* differ:
`solutions`, read from the same cycles by the sibling extractor, carries **6,209** rows in c1 and
**3,190** in c2 against uplifting/human_thriving's 6,210 and 3,189 — differences of exactly the
shape a symmetric-difference check reports, and it reported none between the two lenses under
test. Committed as `extract_lenses.txt` rather than asserted in prose. ⚠️ Consequence, small and
stated: **≤2 articles**' `solutions` status in §4 is therefore unknown or extraneous.

⚠️ **v8's 168 matches the 168 counted on 09-08 — but that is a CODE-PATH reproduction, not an
independent one.** Same four files, same predicate (`raw ≥ 4.5`, which is what
`fit_normalization.py` resolves the op-point to), different script. It shows the extractor did not
mangle the count. It is not a second population.

## Controls — they run in `compare.py` and assert, they are not claims in prose

1. **Same articles.** Verified on the id *sets* per cycle; symmetric difference **0**, four times.
2. **My threshold is the pipeline's.** `raw >= 4.5` reproduces the row's own `tier != "low"` on
   **all 15,372 rows of both lenses**, so the op-point in this analysis is the deployed one and
   not a constant retyped from a config. **With a presence control**, because a check that cannot
   fail proves nothing: substituting v7's **normalized** score disagrees on **530** rows.
   ⚠️ **That presence control is FIELD-specificity, on ONE lens.** It proves the extractor kept
   `raw_weighted_average` and `weighted_average` apart and that `tier` follows the raw one. It
   says nothing about whether 4.5 is the right constant, and it **cannot be run on v8 at all** —
   v8 has no `normalization.json`, so its two fields are equal by construction and `alt` would be
   structurally 0. v8's arm of control 2 is uncontrolled, and v8's arm is the one the cutover
   ruling rests on.
3. **No double counting.** 15,372 distinct ids across the four cycles; no article scored twice.
4. **Nothing SURFACES off a probe estimate.** Every surfaced row on both lenses is `stage2`, so
   `raw_weighted_average` is a Gemma output everywhere §1, §3, §4 and §5 use it. ⚠️ **Two
   corrections here.** It was a PRINT, not an assert, in the first version — a prose claim inside
   the section that exists to say its claims execute; it asserts now. And the first version's
   gloss, *"a Gemma output everywhere it is used here"*, was **false**: v7 1,604 and v8 1,881 rows
   are `stage1_low`, and while none of them surfaces, they are in the corpus, so §2's all-rows
   statistics mixed two instruments. §2 now leads with the both-stage2 frame.
5. **Every cross-lens row joins a paired article.** 0 fail. Without it §4 would silently
   understate coverage and so overstate the number that section is quoted for.

## 1. Surfacing

| | v7 | v8 |
|---|---|---|
| surfaced of 15,372 | **1,184** | **168** |
| pass rate (Wilson 95%) | **7.702%** [7.291, 8.134] | **1.093%** [0.940, 1.270] |
| tier `high` (raw ≥ 7.0) | 17 | **0** (max raw 6.222 vs v7's 7.560) |
| gatekeeper applied | 50 | 2 |

Overlap: **both 152 · v7-only 1,032 · v8-only 16 · Jaccard 0.127**.

⚠️ **Jaccard 0.127 here vs 0.246 on the 660-row eval split (#151 Blocker 3) is not a
contradiction and not a correction — it is a DIFFERENT QUANTITY on a different population, and
the first version of this file said only "population".** 0.246 is the Jaccard between the two
**oracles' label sets** on 660 labelled rows (v7's oracle calls 117 positive, v8's calls 35, they
agree on 30 → 30/122). 0.127 is the Jaccard between the two **deployed students' surfaced sets**
on 15,372 unlabelled production articles. Labels vs student output, two instruments.

The populations differ too: the split's positive rate is **5.30% unweighted** (35/660) and
**3.1638% design-weighted** — ⚠️ the first version attached the unweighted figure to the word
*design-weighted* — against a **1.09%** production pass rate; v7's own label rate on those same
660 rows is 17.7%. Neither number transfers, and because Jaccard is base-rate sensitive, **do not
read 0.127 < 0.246 as "the students disagree more than their oracles do"** — that comparison is
not available from these two figures.

## 2. A stricter v7, or a different order?

⛔ **Two frames, and the primary one is `both-stage2`.** `raw_weighted_average` is a **Gemma
output only when `stage_used == "stage2"`**; on a `stage1_low` row it is the e5 probe's estimate
(`hybrid_scorer.py`). 1,604 v7 and 1,881 v8 rows are `stage1_low` — none of them surfaces, so §1,
§3, §4 and §5 are unaffected — but they are in the corpus, so **every all-rows statistic mixes two
instruments**. n = 12,210 rows are stage2 on both lenses.

| | both-stage2 (primary) | all rows (mixed) |
|---|---|---|
| n | **12,210** | 15,372 |
| v7 / v8 surfaced | 1,177 / 168 | 1,184 / 168 |
| v8 op-point matching v7's volume | **2.820** | 2.823 |
| overlap of v8's top-K with v7's set | **677 = 57.5%** | 675 = 57.0% |
| random-top-K chance level | 9.64% | 7.70% |
| Spearman rho, whole frame | **0.7177** | 0.5551 |
| Spearman rho **within the surfaced union** | **0.3436** (n=1,193) | 0.3463 (n=1,200) |
| Pearson r on raw scores | 0.7609 | 0.7133 |
| v8 − v7 per article | median **−0.839** | median −0.726 |

**The noise null is what makes this a finding rather than a description.** "Random top-K" is a
straw null — nothing would produce it. The null worth excluding is *v8 = a monotone-noisy,
rescaled v7*, Spearman-matched and mapped onto v8's own marginal:

| | NULL | ACTUAL |
|---|---|---|
| **both-stage2**: volume-matched overlap | 76.8% [75.9, 77.8] | **57.5%** |
| **both-stage2**: within-union rho | 0.5630 [0.5318, 0.5897] | **0.3436** |
| all rows (mixed): volume-matched overlap | 64.4% [62.2, 67.1] | 57.0% |
| all rows (mixed): within-union rho | 0.3654 [0.3281, 0.4172] | 0.3463 ⛔ *inside the null* |

Rank agreement over the whole frame is **0.7177** and drops to **0.3436** inside the surfaced
union — exactly where ordering decides what a reader sees. And the level shift is **not uniform
across dimensions**:

| dimension | both-stage2 Δ | all rows Δ |
|---|---|---|
| `benefit_distribution` | **−1.360** | −1.155 |
| `justice_rights_impact` | **−1.220** | −1.053 |
| `evidence_level` | −1.130 | −0.982 |
| `social_cohesion_impact` | −1.014 | −0.884 |
| `change_durability` | −0.951 | −0.781 |
| `human_wellbeing_impact` | **−0.882** | −0.618 |

v8 moved least on the dimension the lens is named for and most on distribution and rights.
⚠️ **The six dimension NAMES are shared; the RUBRICS are not** — v7 and v8 have different oracle
prompts, so each delta is a difference between two definitions, not a change in one quantity.

## 3. The disagreement is not #95 noise

Of the 1,032 v7-only rows, **28 (2.7%)** sit within a 0.16 batch-composition floor of v8's
op-point; median v8 score on them is **2.833**, i.e. 1.667 below the bar. Of the 16 v8-only rows,
**2** are within the floor of v7's. So **97% of the disjoint set is outside the floor** — measured
as *not within 0.16 of the other lens's op-point*. ⚠️ That is weaker than "a genuine difference of
opinion", which is how the first version put it: a pure level shift (median Δ −0.839) produces the
same pattern, and §2 shows part of the disjointness **is** a level effect.

⚠️ **The 0.16 is IMPORTED, and it is the SMALLEST measured term.** A floor belongs to a population
and a mechanism; none has been measured for `human_thriving v8`'s batch composition. Sensitivity,
so the choice is visible rather than decisive:

| floor | provenance | v7-only rows within it |
|---|---|---|
| 0.1428 | v8's own device term (`EXP-026`) | 26 |
| **0.16** | #95 batch composition, other filters | **28** |
| 0.1956 | CPU→CUDA device | 37 |
| 0.2008 | library stack | 42 |
| 0.25 | beyond any measured term | 60 (5.8%) |

Even at 0.25 the conclusion holds: **≥94% of the dropped set is outside any measured floor.**

## 4. Where the dropped articles go — this is the part that changes the decision

Also free: the other enabled lenses scored these same cycles. ⚠️ Their pools are **not** identical
(`solutions` carries 6,209 rows in c1 against 6,210), so `compare.py` asserts that every
cross-lens row joins a paired article — **0 fail**, which is what keeps the "carried by none"
share from being inflated.

| set | n | carried by ≥1 other lens | by none |
|---|---|---|---|
| **v7-only (dropped at cutover)** | 1,032 | **461 = 44.7%** | **571 = 55.3%** |
| both | 152 | 121 = 79.6% | 31 = 20.4% |
| v8-only (added) | 16 | 5 = 31.2% | 11 = 68.8% |

Baseline for any article in the corpus: **7.65%**. Per lens on the dropped set: `solutions` 337,
`belonging` 128, `cultural_discovery` 68, `nature_recovery` 11. (`investment_risk` is PAUSED since
2026-08-25 and writes no files — absent by design, not missing.)

So **~55% of what the cutover drops is surfaced by no other lens** — 571 rows over four cycles —
while ~45% is already on another tab, which ADR-015 says is correct rather than a defect.
Conversely the articles the two lenses **agree** on are the most multi-lens of all (79.6%), and
the 16 v8 adds are the least (68.8% appear nowhere else).

⛔ **Two things this does NOT say, both of which the first version of this file did say.**
1. **"Leaves ovr.news entirely" overstates it.** What is measured is *surfacing* — `tier != "low"`
   in `filtered_*.jsonl`. Reaching a reader is downstream of that: NM#319's enrichment gate reads
   the normalized score, and the reader population is `getArticlesForBuild`, not surfacing. Nobody
   checked whether all 1,032 are currently published. **"Surfaced by no other lens" is the claim
   the measurement supports.**
2. **"≈143 per cycle" was 571 ÷ 4, and c1 is the backlog cycle.** Per cycle the uncovered counts
   are **242 · 128 · 96 · 105**; the three normal cycles average **110**. Use that, or use the
   four-cycle total — not the mixed average.

## 5. What the sets look like

- **v7-only** is 56.5% English and its top scorers are environment, science and
  policy stories — rangelands at COP17, ecosystem recovery after fire, renewable-energy
  commitments, an AI procurement-transparency piece — i.e. mostly `solutions` and
  `nature_recovery` material that v7 also rated highly. That is the shape #107 predicts.
- **v8-only** is 16 rows, 10 English, spanning schools reopening in Madrid and Austria, two High
  Court rulings on personal rights, a 9/11 legacy feature and a Hanoi night race.

**Checked against `EXP-029`'s 12 prompt flips** (`flip_overlap.py`): **2** of the 16 v8-only rows
are flips (Hong Kong schools 5.075, Madras HC 4.554), and **10 of the 12 are in the `both` set** —
v7 surfaces them too.

⛔ **The first version read that as "the owed prompt work is NOT what separates the lenses". That
was a count comparison across two very different denominators, and on RATES it points the other
way.** Within the panel cycle: v8-only **2/6 = 33.3%**, both **10/56 = 17.9%** — flips are
**1.87× enriched** among v8-only rows. Fisher exact two-sided **p = 0.328**. ⚠️ **Six rows cannot
answer this either way**; what changed is that the published direction was wrong, not that the
opposite is now established.

⚠️ **What does survive, because it needs no rate:** 10 of the 12 flips are articles **both** lenses
surface. If a v8.1 student inherits a corrected scope, those rows leave **v8's** passer set while
v7 keeps them until cutover — so fixing the prompt makes the supply gap in §1 **wider**, not
narrower. Direction only; a retrain has not been run.

Full lists in `compare.txt` §5; every row in `union_manifest.jsonl`.

## What this does NOT establish

- **Not which lens is right.** No labels. The judged comparison of the 1,032 dropped rows is
  unfunded; `EXP-029`'s design (DeepSeek re-grading a DeepSeek-distilled student) also cannot be
  reused for v7, whose oracle family differs.
- **No pre-registered prediction.** This run was exploratory — the closest prior number was the
  eval split's Jaccard 0.246, and it is a different quantity (above). Recorded as exploratory
  rather than dressed up as a confirmed expectation.
- **Four cycles, an 11h38m window (2026-09-07 17:54 → 2026-09-08 05:32 CEST), one season of the
  news.** The ratio is stable across the four but the window is a window.
- **v8 has no fitted normalization yet** (Phase E, `normalization_method: "none"`). That changes
  cross-lens *ranking*, not the surfacing decision measured here, which is raw on both lenses.

## Consequences for #151

The forced order in #151 is unchanged, but step 5 — the owner ruling — now has its number.
A straight swap cuts the Thriving tab's supply by **86%** (1,184 → 168 per four cycles) and
removes ~143 articles/cycle from ovr.news altogether. Options that follow from the measurement,
not a recommendation:

1. **Cut over as-is** — accept an 86% supply cut for a lens whose live scope precision is 0.968.
   ⚠️ **That 0.968 is the top of a three-judge spread of 0.651–0.968 on the same 63 articles**
   (`EXP-029`); no single-judge precision number there is trustworthy to better than ±16 points.
2. **Fix the prompt first (#153, #143), retrain, re-measure** — 7 of the 12 `EXP-029` prompt flips
   sit in `[4.5, 5.0)`, so a v8.1 changes this comparison and running the ruling before it wastes
   it. ⚠️ But per §5 it changes it in the adverse direction: 10 of those 12 are rows **both**
   lenses surface, so a corrected scope shrinks v8's set while v7 keeps them until cutover.
3. **Lower v8's op-point** — measured here and it does **not** reconstruct v7's feed (57% at
   volume parity), so it buys volume of a different kind, and ADR-023 says the bar moves only on
   a specificity argument.
4. **Keep both** — the current state; the cost is double scoring, which is already paid.
