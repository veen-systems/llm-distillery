# The obituary detector's misses are a title/body POOLING conflict, not euphemism

**2026-09-10. €0 (local compute, b650-gpu).** Picked up ovr.news' remaining thread: a
euphemistic title with no death token scores 0.0001 on v5, which looks like a frozen-embedding
lexical-coverage weakness. Question asked here: **how big is that class in a real labelled
population, and is euphemism actually the mechanism?**

**Answer: euphemism is not the main mechanism. 44% of the detector's misses are a title/body
conflict inside a single mean-pooled 128-token window — and 22% of them are exactly the
failure ovr described, which I had told them was refuted. That correction is the main result.**

Scored with the shipped v5 pickle (control: full-text rescore reproduces the recorded
`v5_score` to max |Δ| **1.67e-06**). Population: the obituary heldout, 1,562 rows, 344
positives (22.0%).

---

## The verdict is carried by the title

Over the 344 positives, comparing score(title alone), score(body alone) and score(full text):

- **median |full − title-only| = 0.0107** — the full-text score is very nearly the title score
- median |full − body-only| = 0.0178
- positives whose **title alone passes** 0.85: n=244 → **93.0%** pass on full text
- positives whose **title alone scores < 0.15**: n=48 → only **31.2%** pass on full text

## Mechanism taxonomy of the 77 misses (computed, not hand-labelled)

v5 misses **77 of 344 positives** at the live 0.85 (recall 0.7762 on this set).

| class | n | share | mechanism |
|---|---|---|---|
| **A** | **17** | 22.1% | title alone **passes**, full text does not → **body dilutes a good title under the op-point** |
| **B** | 17 | 22.1% | title fails, body alone **passes** → title overrides a body that reads as an obituary |
| **C** | 43 | 55.8% | neither title nor body passes → no signal either way |

**A + B = 44% of all misses are title/body disagreement** — the two halves of the article
pointing opposite ways, averaged into one 128-token mean-pooled vector that lands between them.

Class A in detail: median title **0.9556** → median full **0.6529**, a median drop of **0.3394**.
**7.0% of every positive with a passing title is dragged under by its own body.** It includes
titles containing the literal word *obituary*:

```
title 0.9997 -> full 0.6529   Dame Gillian Wagner obituary
title 0.9996 -> full 0.6603   Dame Sarah Anderson obituary
title 0.9981 -> full 0.3021   Stewart Cheifet, PBS host who chronicled the PC revolution, dies at 87
title 0.9989 -> full 0.7550   NSW's first female governor Dame Marie Bashir dies aged 95
title 0.9982 -> full 0.2512   Muere uno de los hombres arrastrados por el mar en Lanzarote
```

## ⛔ This corrects what I told ovr.news on 2026-09-09

I tested their two example headlines, found both score 0.98–1.00 title-only and stay above
0.85 under 128 tokens of padding, and concluded their diagnosis — *"a euphemistic headline over
a long biography embeds as a history piece"* — was refuted, adding that dilution is *"real but
bounded; it does not reach 1e-4."*

**The refutation of their two specific examples stands. The generalisation was wrong twice:**

1. **Their mechanism is real and is 22% of all misses.** A good obituary title *is* dragged
   under by its body, routinely.
2. **"Bounded" was the wrong test.** Dilution does not need to reach 1e-4 — it only needs to
   cross **0.85**, and it does, on 17 rows. I measured the magnitude against zero when the
   only bar that matters is the operating point. Same shape as
   `feedback-caveat-premise-check`: a correct measurement aimed at the wrong bar.

What they got wrong is only the *label*: the class is not euphemistic titles. Class C, where
lexical coverage would live, is dominated by **death-as-news** — crime, accident and disease
reports (*"Hindu man crushed to death in Bangladesh"*, *"Two die in Lagos-Ibadan Expressway
crash"*, *"Local health officials identify first pediatric flu death in Ohio"*). Whether those
are obituaries at all is the open **definitional** dispute (LD#51 broad rule vs LD#85's
adjudicated rule vs ovr's ADR-045 recency axis), not a model defect. ⚠️ That reading comes from
inspecting titles, not from a measured split — **it is an observation, not a share.**

## A candidate fix falls out — measured once, NOT a recommendation

If class A is a pooling failure, scoring the title separately and taking the max should recover
it. On the same heldout at 0.85:

| rule | recall | specificity | precision | fp |
|---|---|---|---|---|
| current (full text) | 0.7762 | 0.9901 | 0.9570 | 12 |
| `max(title, full)` | **0.8256** | 0.9770 | 0.9103 | 28 |
| `max(title@0.90, full)` | 0.8198 | 0.9811 | 0.9246 | 23 |
| `max(title@0.95, full)` | 0.8023 | 0.9836 | 0.9324 | 20 |
| **`max(title@0.99, full)`** | 0.7936 | **0.9885** | 0.9512 | **14** |

Plain max buys **+0.0494 recall for −0.0131 specificity** (+16 false positives on 1,218
negatives). The gated variant at 0.99 buys **+0.0174 recall for −0.0016 specificity** — six
more obituaries caught for two more clean articles blocked.

Under the owner's 2026-07-30 recall-first directive for this gate, over-blocking is accepted
collateral, so plain max is defensible. Under ADR-023's general rule specificity is the budget,
so the 0.99 gate is. **That is an owner decision and this document does not make it.**

## ⛔ Limits — read before quoting any number here

- **One model, one seed.** Everything is the shipped v5 (seed 42). Whether the taxonomy shares
  or the max-rule gain survive a retrain is **untested** — and the sibling study measured a
  seed band of 0.127 on this exact metric. The rule comparison itself is seed-free (two
  decision rules over one fixed model, same 1,562 rows), but its generalisation is not.
- **This heldout contains the 25 leaked rows** (they are in v5's training corpus), so recall
  0.7762 is mildly optimistic against the published 0.750 on n=1,529. The taxonomy *shares* are
  the finding; the absolute recall is not.
- **Nothing here is multilingual evidence.** All 344 positives are Latin-script — the corpus
  holds **zero** non-Latin obituary positives. ⭐ This population **cannot** answer whether the
  detector misses Greek, Korean or Arabic obituaries; a zero from it would be guaranteed. If
  that question matters, it needs a corpus built for it.
- The max-rule table is a **diagnostic probe**, not a proposed change. No config, threshold or
  package was touched.

## Reproduce

```bash
scp scripts/*.py b650-gpu:~/
ssh b650-gpu 'cd ~/llm-distillery && ./venv-prodparity/bin/python ~/euphemism.py'   # title dominance + FN class
ssh b650-gpu 'cd ~/llm-distillery && ./venv-prodparity/bin/python ~/taxonomy.py'    # A/B/C taxonomy
ssh b650-gpu 'cd ~/llm-distillery && ./venv-prodparity/bin/python ~/maxrule.py'     # candidate fix
ssh b650-gpu 'cd ~/llm-distillery && ./venv-prodparity/bin/python ~/fnlist.py'      # all 77 titles
```

Siblings: `2026-09-10-detector-window-128-vs-512` (why the window stays 128),
`2026-09-10-obituary-version-ordering-multiseed` (why v3/v4/v5 cannot be ordered).
