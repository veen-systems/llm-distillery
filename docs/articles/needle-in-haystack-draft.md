# The Needle-in-Haystack Problem: Why Filtering for Constructive News Breaks Standard ML

*Draft for llm-distillery#30*

> **EDITION NOTE (2026-07-16).** This is the **technical master** — full numbers, model/oracle
> names, methods sections; all ongoing updates land here. A **public/reader edition**
> (de-vendored, softer, publisher CTA) lives at `ovr.news/docs/articles/needle-in-haystack-draft.md`
> and is re-derived from this master before publishing — never edited independently.

---

## The promise and the trap

"Just filter the news for what's actually working." It sounds like a weekend project. Grab an LLM, score some articles, train a classifier. Ship it.

We tried. It took us a year, seven filters, and a few humbling failures before we understood why this is fundamentally harder than it looks. Not because the technology is immature, but because the problem has a structural property that defeats standard approaches: **the thing you're looking for is rare, and the reason it's rare is the same bias you're trying to correct.**

ovr.news filters global news through five constructive lenses — from community bonds to ecosystem recovery to rediscovered historical knowledge. Each lens counters one or more cognitive biases that shape what the daily news cycle covers: negativity bias, atomization, eco-anxiety, learned helplessness, declinism, short-termism. Together they surface evidence that the world is more functional than the news makes it appear.

The engineering challenge: constructive news is a needle in a haystack, and the haystack is *designed* to hide the needle.

## Why keywords and sentiment fail

The first instinct is keyword matching. Surely "community" finds belonging, "long-term" finds foresight, "recovery" finds nature recovery?

It doesn't. What we're looking for isn't a topic — it's a *judgment*.

Our belonging filter scores articles on six dimensions (defined in [llm-distillery/filters/belonging](https://github.com/ducroq/llm-distillery)): intergenerational bonds, community fabric, reciprocal care, rootedness, purpose beyond self, and slow presence. A LinkedIn article about "building community at work" contains all the right keywords. It scores 1.3 out of 10. A story about a 94-year-old making pasta with her granddaughter using her mother's recipe scores 8.5. No keyword distinguishes them. The difference is *what kind of community* — commodified versus organic, optimized versus lived.

Sentiment analysis fails in the opposite direction. Constructive news isn't positive news. A country admitting its drug war failed and shifting to treatment — that reads as negative. Our foresight filter scores it 6.1 because the *decision-making process* shows evidence-based course correction, systems awareness, and institutional durability. Meanwhile, a cheerful wellness listicle about living longer scores 1.3 on belonging because it commodifies community as a longevity hack.

The judgment we need — "does this article demonstrate genuine foresight / belonging / recovery?" — requires understanding intent, process quality, and evidence, not just topic or tone.

## Dimensional scoring: breaking judgment into measurable sub-factors

Our approach: decompose each lens into 6 weighted dimensions that can be scored independently on a 0-10 scale.

For foresight (counters short-termism):

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Time Horizon | 25% | How far ahead does the decision look? |
| Systems Awareness | 20% | Are trade-offs and second-order effects acknowledged? |
| Course Correction | 20% | Is there willingness to admit error and change? |
| Intergenerational Investment | 15% | Are future generations explicitly considered? |
| Institutional Durability | 10% | Will the decision survive a change of leadership? |
| Evidence Foundation | 10% | Is the decision grounded in evidence? |

An oracle (Gemini Flash) scores articles on these dimensions. Each score has explicit rubrics with calibration examples, critical filters, and anti-hallucination rules (evidence must be exact quotes from the article). The oracle outputs only scores — tier classification (high/medium/low) happens in post-processing, so thresholds can be adjusted without re-labeling.

This is expensive: roughly $0.0013–0.004 per article depending on the oracle (DeepSeek Flash at the low end, an 8K-token Gemini prompt at the high end), 1-2 seconds per call. We can't run this on every article forever. But we can use it to *teach* a smaller model.

## Knowledge distillation: invest energy once, infer forever

Knowledge distillation is the core of the pipeline. The oracle (Gemini Flash, cloud GPU, ~0.5s/article) scores thousands of articles. A student model (Gemma-3-1B, local CPU, 20ms/article) learns to replicate those scores.

The student is a Gemma-3-1B language model with a LoRA adapter — 13 million trainable parameters on top of a 1 billion parameter base. It takes article text in, outputs 6 continuous scores. After training, it runs locally, on CPU, at 20ms per article. No cloud, no API, no per-article cost.

At ovr.news scale (2,000+ articles, 7 filters, multiple runs per day), this is the difference between needing a cloud GPU budget and running on a mini PC. The energy investment happens once during training. After that, inference is essentially free.

But this only works if the student has good training data to learn from. And that's where the needle problem appears.

## The needle problem

When we trained the foresight filter, we scored 300 random articles from our news corpus. The distribution:

| Score range | % of articles |
|-------------|---------------|
| 0-2 (outside this lens) | 90% |
| 2-5 (some foresight) | 9% |
| 5+ (genuine foresight) | 1% |

A low score does not mean bad journalism — it means the article covers territory outside what this particular lens looks for; most of the 90% is competent, well-reported work on topics that simply aren't about long-term institutional decision-making. But from a training-data perspective, ninety percent of articles pile up at the bottom of the scale. The 2-5 range — where the model needs to learn the *gradient* from "a bit of foresight" to "strong foresight" — is almost empty. And the high-scoring articles that define what foresight looks like? Three articles out of 300.

This is not a labeling error. This is the negativity bias, measured. News selects for immediacy: this week's crisis, this quarter's earnings, this election's polls — and our corpus amplifies it, being composed mostly of general news outlets rather than policy journals or governance publications. Genuine foresight — decisions made for generations ahead — is not what newsrooms cover. It happens in governance documents, policy journals, institutional reforms. It's real, but it's rare in the daily news cycle.

A student model trained on this distribution learns exactly one thing: predict low scores for everything. That minimizes average error when 90% of your training data is noise. The resulting model has a technically acceptable loss but is useless — it can't distinguish a New Zealand wellbeing budget reform from a celebrity interview.

This same pattern appeared across our filters, and the correlation is clear:

| Filter | Concept rarity | Training MAE |
|--------|---------------|-------------|
| Investment-risk | Common (risk is everywhere) | 0.47 |
| Belonging | Common (community themes) | 0.49 |
| Nature recovery | Rare | 0.54 |
| Sustainability tech | Medium | 0.72 |
| Cultural discovery | Medium-low | 0.74 |
| Foresight | Very rare | 0.94 (before fix) |
| Thriving | Rare | 0.94 (unsolved) |

The rarer the concept, the worse the bimodal distribution, the harder the student model's job. This is a general property of semantic filtering for constructive concepts, not a bug in any particular filter.

But there's a trap in that table itself, and it took us longest to internalize: **for a needle filter, MAE is the wrong yardstick.** When 90% of articles are noise near zero, a model that predicts "low" for everything scores a *great* MAE — and is useless. MAE rewards being accurate on the majority you don't care about. Nature recovery made this concrete: v1 had a *better* MAE than v2 (0.45 vs 0.53) while having essentially zero discrimination — in production 98.6% of articles scored below 1.0. v2 looked "worse" on MAE but lifted **Recall@20 from 0.55 to 0.70** and NDCG@10 from 0.71 to 0.86 — it actually surfaced the right stories.

So we judge needle filters on **ranking metrics** — Recall@k, NDCG@k, and false-negative rate on the medium-plus articles — not on aggregate error. MAE is still fine for the balanced filters (investment-risk, belonging), which is why the table above tracks with rarity; but the moment a filter is a genuine needle, MAE stops measuring anything you care about and you have to switch instruments. (Reading the MAE numbers as the quality story is the single most common way to ship a needle filter that "looks fine" and finds nothing.)

## Two-stage screening: solving the needle problem

The solution separates two questions that the oracle was trying to answer simultaneously:

**Stage 1: "Is this article relevant?"** — handled by an embedding screener before oracle scoring.

We write 10-15 synthetic article summaries representing canonical examples of the concept (for foresight: New Zealand's wellbeing budget, Costa Rica's 30-year reforestation, Wales's Future Generations Commissioner). A small embedding model (e5-small, 33M parameters) computes cosine similarity between these seeds and every article in the corpus. The top candidates — articles that *look like* foresight — get sent to the oracle.

**Stage 2: "How much foresight does it contain?"** — handled by the oracle, scoring only relevant articles.

With pre-screened articles, the oracle can focus on gradients instead of binary classification. Content-type caps are softened (4.0-5.0 instead of 2.0-3.0) so that false positives from the screener land in the useful mid-range instead of being hard-capped at the noise floor.

The result:

| Score range | Before screening | After screening |
|-------------|-----------------|-----------------|
| 0-2 (outside lens) | 90% | 23% |
| 2-5 (some foresight) | 9% | 55% |
| 5+ (genuine foresight) | 1% | 20% |

The dead zone disappeared. The student model now has examples across the full score range. Foresight's MAE dropped from 0.94 to 0.75 — from unusable to on par with our mid-tier production filters.

The cost of this pre-screening step? Embedding 178,000 articles takes 15 minutes on a laptop CPU. The seeds take an hour to write. Compared to the oracle scoring cost (€4 for 3,500 articles), the screening is essentially free.

This pattern generalizes. Nature recovery used it first. Foresight proved it works for an even rarer concept. Thriving — currently paused at MAE 0.94 — is the next candidate.

The same embedding idea reappears at *inference* time, but with a twist. Once a filter is deployed, we don't want to run the 1B student on every article either, so a small e5 probe screens first and only promising articles reach the student. Here the probe isn't cosine-similarity to seeds — it's a small classifier trained on the labeled data, and crucially it's tuned **recall-first**: we pick its threshold off the validation recall curve at a target false-negative rate, not by minimizing error. On a floor-dominated corpus a probe trained to minimize error collapses to "reject everything" and silently drops the needles it exists to catch. Nature recovery's inference probe keeps ~98% of true medium-plus articles while skipping ~64% of the haystack — a screen has to be measured by what it *doesn't* wrongly discard, not by average accuracy.

## Distillation as energy investment

The standard framing of knowledge distillation is cost reduction: replace an expensive API with a cheap local model. That's true but insufficient.

The deeper framing is energy. An oracle scoring run is a one-time energy investment. It runs cloud GPUs for a few hours, scores a few thousand articles, and produces training data. After that, the student model runs on CPU — 20ms per article, no data center, no network round-trip. At 2,000 articles per day across 7 filters, the daily energy cost of inference is negligible compared to a single oracle run.

This is cathedral thinking applied to ML infrastructure: invest upfront to build something that runs efficiently for a long time.

The numbers for foresight: €4 in oracle scoring produced a model that will score millions of articles over its lifetime at essentially zero marginal energy cost. Even accounting for the GPU training time (~30 minutes on an RTX 4080), the energy payback period is measured in days, not months.

## What we don't solve

Honesty requires listing what's hard and what's still broken.

**Dimension correlation.** Our foresight filter's Time Horizon and Institutional Durability dimensions correlate at r=0.857. The oracle conflates them despite explicit instructions not to. The student model inherits this confusion. Cross-dimension exclusion notes in the prompt help but don't fully solve it. For now, we accept correlated dimensions as an imperfect approximation of concepts that are genuinely related.

**The fuzzy middle.** Systems Awareness (MAE 0.86) and Course Correction (MAE 0.79) are our worst-performing dimensions. They require subtle judgment — distinguishing "token caveat" from "genuine nuance" — that a 1-billion-parameter model struggles with. More training data helps (doubling from 1,374 to 2,761 examples improved every dimension) but there may be a floor below which small models simply can't go.

**Calibration on small datasets.** Isotonic regression calibration improved our validation MAE by 7.5% but was neutral on the held-out test set. With only 346 validation examples, the calibration overfits the validation distribution. This will improve as production data accumulates, but for now, our calibrated test MAE of 0.75 is the honest number.

**The 95% we throw away.** Pre-screening selects 2-3% of the corpus for oracle scoring. That means 97% of articles are never evaluated by the oracle. If a foresighted decision is described in unusual language that doesn't resemble our seed articles, the embedding screener won't find it. We accept this false-negative rate as the price of tractability.

**The top of the scale.** Our models can't reliably produce 8–10 scores, because there are almost no 8–10 examples to learn from — in one filter, 2 articles out of ~3,900. A regression model interpolates within the data it has seen; it won't extrapolate into a near-empty band, and the loss actively rewards hedging toward the populated middle. Calibration can't rescue this — isotonic calibration is monotonic and bounded by the range the model actually emits, so it can't invent range it never learned. The real fix is more top-end training data (active learning), which we haven't done. For now we clip the top and accept a compressed high end. It rarely matters for *surfacing* (the decision lives at the medium threshold); it only blurs "great" versus "exceptional."

## Comparing across filters: calibrate within, normalize across

A subtle consequence of all this: you cannot compare raw scores *between* filters. One filter surfaces 60% of articles as medium-plus, another 0.3% — a "5" means completely different things in each, and the compressed top band differs per filter too.

The tempting fix — linearly rescale each filter to 0–10 — is wrong, and we shipped that bug once. Linear stretching over-promotes the compressed filter: a mediocre nature-recovery article gets stretched up until it outranks a genuinely great uplifting one, and on a shared feed that ranks by max-score-across-filters, the compressed filter hijacks the front page.

There are two different jobs. **Calibration** makes a score honest *within* a filter — isotonic regression aligning the student to its oracle. It does not make filters comparable. **Cross-filter comparison** needs a separate, *non-linear* step: map each score to its **percentile in that filter's own production distribution**. Then "top 5% of recovery" and "top 5% of thriving" compare as equals — and the compressed top band stops mattering, because you're comparing standings within each population, never raw values across them.

And here is the trap inside the fix: **percentile normalization is exactly as good as its reference population**, and both production incidents this mechanism ever gave us were population errors — the model was right both times. Fit the reference population *below* the visibility threshold and invisible content defines the curve: our recovery filter's CDF was once fitted from raw ≥ 1.5 (median 2.19), so doom articles the model had correctly scored 2.2–3.3 surfaced at a normalized 5.2–8.3 — we misdiagnosed it as a model failure and shipped a keyword cap that took fourteen months to retire. Fit the population from *already-filtered* output and it never reaches down to the threshold: visible articles below the population's floor were crushed to ~0 (raw 4.6 → 0.02). The final method pins the population by construction — the fit refuses to run off the filter's own operating point, the CDF's lower edge is anchored *to* that operating point, and the lowest score actually observed is stored and guarded so a biased sample can't masquerade as a sparse one. For a needle filter there's one more wrinkle: at a 0.3% pass rate, waiting for a live reference population takes weeks, so we synthesize it by rescoring ~145K historical articles at the production base rate — never the enriched training set, which is a different population by design.

## Choosing the oracle: noise is not bias

The oracle isn't ground truth — it's a *labeler*, and a labeler has two independent failure modes. We conflated them once and it cost real money.

**Noise** is self-inconsistency: score the same article twice and the labeler disagrees with itself. It's easy to measure — re-score a sample, compute the spread — and it sets a floor on the student, which can never be more consistent than its teacher.

**Bias** is where the labeler sits relative to *your* editorial judgment: too generous, too harsh, rewarding the wrong things. Bias is *not* measurable by self-consistency. You have to read the articles where two candidate oracles disagree and judge which one is right.

These two axes pull apart, and optimizing the easy one wrecks the hard one. On nature recovery we tested two oracles on the same articles. One was 2.2× more self-consistent (noise 0.17 vs 0.38) — and it was also systematically more *generous*, scoring a corporate "sustainability changemaker" profile at 5.6 and a "6 practices" how-to listicle at 5.6: exactly the content the filter exists to reject. The conservative, noisier oracle matched our editorial line; the clean one did not. Switching to the low-noise oracle to "improve the labels" would have re-labeled the entire corpus toward the wrong bias — a mistake that's expensive precisely because clean, consistent, wrong labels look like progress.

The lesson: **choose the oracle for bias, and choose it per filter — never inherit a default, and never switch oracles just to cut noise.** If a correctly-biased oracle is too noisy, average several of its runs (noise falls as 1/√k) rather than swapping in a differently-biased one. Self-consistency is seductive because it's a number you can compute without judgment; bias is the one that matters and the one you can only see by reading.

## The pattern

The negativity bias in news isn't just an editorial problem. It's an engineering problem. It creates data distributions that defeat standard ML pipelines. When you filter for what's working in a world that selects for what's broken, you will hit the needle-in-haystack problem.

The solution is not a single technique but a pipeline:

1. **Oracle selection** — choose the labeler for editorial *bias*, per filter; noise you can average away, bias you can't
2. **Dimensional scoring** — decompose judgment into measurable sub-factors
3. **Embedding pre-screening** — find the needles before you score them (and screen recall-first)
4. **Soft scope gating** — let the oracle grade on a gradient, not a binary
5. **Knowledge distillation** — invest energy once, infer sustainably forever
6. **Measure with ranking metrics** — Recall@k / NDCG / false-negatives, not MAE; and compare across filters by percentile, not raw score

Each step addresses a specific failure mode. Pick the oracle for convenience instead of bias and you distill the wrong judgment. Skip the dimensional scoring and you're back to sentiment analysis. Skip the pre-screening and your training data is 90% noise. Skip the soft gating and you create dead zones in your score distribution. Skip the distillation and you're paying cloud API costs on every article forever. Judge it by MAE and you'll ship a needle filter that looks fine and finds nothing.

We didn't design this pipeline in advance. We discovered it by failing — thriving v1's bimodal distribution, foresight's first 300-article calibration batch, the seeds that got contaminated by corpus composition. Each failure taught us one piece.

The pipeline is now documented and reusable. The next filter we build will start from this template. If you're building semantic filters for rare concepts — in news or anywhere else — the pattern applies. The negativity bias is not unique to news. Any domain where the target signal is rare and the noise is systematically produced will have this property.

The needles are there. You just need a better way to find them.

---

*This article describes work on the [LLM Distillery](https://github.com/ducroq/llm-distillery) project, which powers the constructive news filters at [ovr.news](https://ovr.news).*
