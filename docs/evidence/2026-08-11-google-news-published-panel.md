# Google News in production: the published panel

**Date:** 2026-08-11
**Population:** all 39 Google News articles in ovr.news `live_articles` — the
complete published set, not a sample
**Status:** measurement only. Nothing was fitted, changed or deployed.

---

## One-line answer

**The scores are mostly defensible; the publishing is not.** Roughly 33 of 39
headlines genuinely support the score they were given. The two real problems are
that half of `nature_recovery`'s Google News output is **duplicate stories**, and
that a handful of items carry framing the scoring dimensions structurally cannot
see.

## Why this panel and not the one that was asked for

The FluxusSource session asked for oracle re-scoring of *surfacing* Google News
rows, to establish whether they are wrong. That design was rejected for two
reasons and replaced:

1. **The oracle is not a valid instrument on this population.** The 300-char
   labelling floor exists *because* short content makes the model analyse the
   evaluation framework instead of the article
   (`ground_truth.batch_scorer.make_oracle_prefilter` docstring, #93). Median GN
   content length is **89 characters**. Re-scoring it with the oracle runs the
   instrument outside the range its own guard defines.
2. **Reader exposure is far smaller than the surfacing share**, so a sample of
   surfacing rows would mostly measure items no reader ever sees. The published
   population is **39 articles** — small enough to judge in full, with no
   sampling error.

The substituted question is *"does the headline support the score the student
gave?"*, which is answerable from 89 characters.

**What a pass does and does not mean.** A pass says the scores are defensible
*given a headline*. It does not say the articles are good, because there is no
article — so a clean result makes this a product question (should headline-only
items be published at all) rather than a scorer defect.

## Exposure

| population | items | avg content length |
|---|---|---|
| non-GN | 3,490 | **4,753 chars** |
| A `gn_*` country proxies | 33 | 120 |
| B/C `google_news` feeds | 3 | 124 |
| GN by url only | 3 | 92 |

**39 of 3,529 published articles (1.1%)** are Google News, against **25.7% of the
collected corpus**. Cross-checked two ways — by `source` and by
`url LIKE %news.google.com%` — because ovr#275's resolver could have rewritten the
URLs. Both give 39.

### The overall 1.1% hides a 14× spread

| filter | GN % of surfacing | GN % of published | attenuation |
|---|---|---|---|
| `nature_recovery` | 12.4% | **8.2%** | **1.5×** |
| `solutions` | 16.1% | 5.4% | 3.0× |
| `cultural_discovery` | 3.2% | 0.9% | 3.5× |
| `uplifting` | 3.3% | 0.7% | 5.1× |
| `belonging` | 3.5% | 0.2% | 20.8× |

**Correction recorded deliberately:** an earlier reading of mine claimed "~96% of
GN surfacing rows are removed downstream." That was a denominator error —
`solutions`' 16.5% surfacing share compared against the **all-filter** 1.1%
published share, two different populations. There is no single 96%-effective
filter. There *is* an unexplained 14× spread across filters; dedup plus the
publication window is the plausible account and is **not measured**. `displayScoreThreshold`
(ovr#304) is an unlikely explanation because it would attenuate uniformly.

## Finding 1 — half of nature_recovery's GN output is duplicates

The **19** published `nature_recovery` GN articles are **9 distinct stories**:

| copies | story | source feed |
|---|---|---|
| **6** | Nepal's tiger census — population 429, up from 355 | **all 6** `gn_asia_gn_nepal` |
| 3 | Senegal's Pink Lake regains its colour | all 3 `gn_africa_gn_senegal` |
| 3 | Kazakhstan releases an Amur tiger — rewilding | all 3 `gn_asia_gn_kazakhstan` |
| 2 | Walia ibex population 270 → 306 | all 2 `gn_africa_gn_ethiopia` |
| 1 each | mangroves rebounding; Niger's 200m trees; KARMOL Maputo mangroves; Malawi wild dogs; Nepal's new national parks | — |

Counted by hand. **An automated first pass got this wrong and the error is worth
recording**: crude shared-token grouping (≥3 tokens of length >3) merged the
Kazakhstan rewilding story into the Nepal census group and pulled in
`gn_africa_gn_zambia`'s "Endangered Wild Dogs Return to Malawi's Kasungu National
Park" on shared words like *return*, *population*, *national*, *park*. That
produced a false "Nepal story arriving through a Zambia proxy" reading, which was
briefly reported cross-repo before being withdrawn.

### This is story dedup, not content-hash dedup

**All six Nepal copies arrive through the same feed** (`gn_asia_gn_nepal`) and
carry **different text** — six outlets' headlines about one census (Inshorts, WWF,
The Himalayan Times, ETV Bharat, The Standard HK, The Climate Watch). Content-hash
dedup cannot catch them and should not: the bytes genuinely differ. So this is
**not** FluxusSource#133 (source-blind content-hash dropping), which is a different
defect in the opposite direction.

What failed is story-level clustering — NexusMind#188 / #278. **Plausible
mechanism, not measured:** these are 79–126 character headline-only items, which
is very little text for an embedding-based matcher to cluster on. If that is the
cause, headline-only items are structurally hard to dedup, and the GN population is
exactly the population that cannot be deduped *and* cannot be enriched
(NexusMind#310).

Combined with GN being **8.2%** of everything `nature_recovery` publishes, this is
the most reader-visible defect the panel found: readers of that lens saw the same
tiger census six times. It is FluxusSource#142 / NexusMind#188 arriving at readers.

## Finding 2 — framing the dimensions cannot see

Two published items where the score is arguably supported dimension-by-dimension
and the result is still wrong or unresolved. **Both scores below are the
NORMALIZED display score, not raw** — the per-dimension values are 4.4–7.2 in both
cases, and normalization is rank-in-batch by design (ADR-014).

**`belonging`, normalized 7.26, tier `high`** — `gn_europe_gn_serbia`, published
2026-08-03, id `gn_europe_gn_serbia_a38e949e1d30`:

> NEW CROSS ON THE CHURCH IN KAČANIK: Believers restored the shrine in a place
> where there are no Serbs since 1999!

```
rootedness 6.83 · purpose_beyond_self 6.63 · community_fabric 6.54
reciprocal_care 4.80 · slow_presence 4.71 · intergenerational_bonds 5.25
```

The dimensions are not hallucinating — shrine restoration *is* rootedness and
community fabric. What they cannot see is that Kačanik is in Kosovo, that
"where there are no Serbs since 1999" is a claim about ethnic absence in contested
territory, and that the exclamation mark and the outlet place it as ethno-national
framing rather than community belonging. Filed as its own issue.

**`uplifting`, normalized 8.95, tier `high`** — `gn_asia_gn_cambodia`, published
2026-08-08, id `gn_asia_gn_cambodia_eedfba43e99e`:

> Cambodia Cracks Down on 112 Human Trafficking, Sexual Exploitation Cases,
> Rescues 581 Victims

```
human_wellbeing_impact 7.17 · evidence_level 7.06 · benefit_distribution 6.22
change_durability 6.36 · justice_rights_impact 5.16 · social_cohesion_impact 4.41
```

**This one is NOT claimed as a defect.** 581 people rescued is a genuine positive
outcome and the dimensions read it correctly. Whether a sexual-exploitation
enforcement story belongs at tier `high` in a lens readers open for uplift is an
editorial ruling, not a measurement — and it is the same class as the
adjacent-lens question already open with the owner. Filed as a decision item.

Two further items are unresolved rather than wrong and are recorded here only:

- `uplifting` normalized 8.98 — *"Benin: pardoned by President Romuald Wadagni,
  Julien Kandé Kansou regains freedom."* A pardon is unjudgeable from a headline;
  it could be a corruption pardon and nothing in 97 characters would reveal it.
  This is the clearest single illustration of the headline-only problem.
- `solutions` normalized **9.58** and **9.25** on headlines of **109** and **71**
  characters (a district-heating digital twin; "China allocates 180m yuan for
  flood control"). Both are on-lens. Neither is a defensible confidence level for
  the amount of text involved.

## What the panel does NOT establish

- **Nothing about article quality**, because there are no articles — only
  headlines. That is the point, not a limitation of the method.
- **Nothing causal about the training-corpus mismatch in #105.** These are
  separate findings that share a root population.
- The judging was done by reading all 39 directly, not by a blind rubric or a
  second judge. At n=39 with a complete population that is proportionate, but it
  is one reader's call and the borderline items are marked as such rather than
  scored.

## Sources and what they exclude

- `ovr.db` `live_articles` on sadalsuud, read-only, 3,529 rows spanning
  2026-07-28 → 2026-08-11. This is the live set; `archive_articles` was not
  included, so items that rotated out are not counted.
- NexusMind `data/filtered/*/filtered_*.jsonl` for surfacing shares — 100%
  prefilter passers by construction, and drops source-type-excluded rows.
- NexusMind `data/raw/` for corpus shares — pre-enrichment, retains to 2026-07-28.

## Related

- #105 — training corpora vs today's labelling gate
- #91 — uplifting scoring narrative fragments over dominant subject
- #92 / #93 — short-content scoring and the labelling floor
- FluxusSource#142, NexusMind#188 — story dedup, which finding 1 belongs to
- FluxusSource#144, #145 — the Google News estate upstream
