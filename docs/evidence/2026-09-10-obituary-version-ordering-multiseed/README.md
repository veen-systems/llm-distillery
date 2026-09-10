# Is the obituary v3 -> v4 -> v5 recall ordering real? — No. It does not survive a change of seed.

**2026-09-10. €0 (local compute, b650-gpu).** Commissioned by ovr.news (their ADR-042 call),
approved on this side by the owner. The question, in their words: *"whether the v3 -> v4 -> v5
recall ORDERING is stable across seeds, or whether the bands overlap enough that the ordering
is a draw artifact."*

**Answer: the bands overlap at every threshold, and across five seeds the three versions
finish in three different orders. The version comparison cannot carry an ADR decision.**

⭐ **And the point estimate reverses.** The flag that started this was *"v4 traded recall
0.744 -> 0.608, the wrong direction under ADR-042."* Across seeds **v4 has the HIGHEST mean
recall of the three** at the live threshold. That does not make v4 better — the bands overlap
— it means the original claim was not merely unproven, it was pointing the wrong way.

---

## Result — recall at the live threshold 0.85, five seeds, eval n=1,537 (20.9% positive)

| version | recall mean | band [min–max] | spread | specificity mean |
|---|---|---|---|---|
| v3 | 0.7087 | [0.5963–0.8043] | 0.208 | 0.9923 |
| **v4** | **0.7739** | [0.7329–0.7981] | 0.065 | 0.9890 |
| v5 | 0.7671 | [0.6739–0.8012] | 0.127 | 0.9880 |

**All three pairwise bands overlap** (v3/v4, v4/v5, v3/v5) — at 0.85, 0.90 and 0.95 alike.

### Orderings actually observed across the five seeds

| threshold | orderings |
|---|---|
| **0.85** | `v3>v4>v5` ×2, `v5>v4>v3` ×2, `v4>v5>v3` ×1 |
| 0.90 | `v5>v4>v3` ×2, `v3>v4>v5` ×1, `v4>v3>v5` ×1, `v4>v5>v3` ×1 |
| 0.95 | `v5>v4>v3` ×2, `v3>v4>v5` ×1, `v4>v3>v5` ×1, `v4>v5>v3` ×1 |

At the live operating point the ordering reverses completely between seeds: two seeds rank
v3 first, two rank v5 first. **Every version wins under some seed.** Nothing here orders them.

Recall bands at the other thresholds: 0.90 — v3 0.6652 [0.5435–0.7950], v4 0.7460
[0.6770–0.7826], v5 0.7391 [0.6273–0.7919]. 0.95 — v3 0.5876 [0.4379–0.7640], v4 0.6981
[0.5839–0.7578], v5 0.6907 [0.5186–0.7702].

## ⚠️ The positive control here is WEAKER than the window study's — read this before quoting

Refitting each version's corpus at the **shipped seed 42** and comparing to the shipped
model's recorded scores on the heldout:

| version | corr with shipped | mean abs delta | verdict flips @0.85 |
|---|---|---|---|
| v3 | 0.9771 | 0.0252 | 30 / 1562 |
| v4 | 0.9713 | 0.0290 | 45 / 1562 |
| v5 | 0.9952 | 0.0089 | 10 / 1562 |

⛔ **A refit at the shipped seed is close to, but is NOT, the shipped model.** sklearn's
`MLPClassifier` is not bit-reproducible across environments even at a fixed `random_state`.
So this study measures **the distribution of models that each corpus + protocol produces**,
and treats each shipped version as one draw from it. That is exactly the question asked — but
it is a different claim from "I retrained v4", and nothing here should be quoted as a
reproduction of a shipped model. (Contrast the window study, where *re-scoring* with the
shipped pickle reproduced recorded scores to max |Δ| 1.7e-06.)

What the control does establish: correlations of 0.97–0.995 corroborate that each corpus is
the right one. A wrong corpus would not land there.

## Corpus identification — and the lookalike that would have answered a different question

Label counts match the shipped `training_config.json` exactly:

| version | file | n | pos | neg |
|---|---|---|---|---|
| v3 | `train_split_corpus.jsonl` | 11,295 | 2,672 | 8,623 |
| **v4** | **`v4b_train_seed.jsonl`** | 11,308 | 2,673 | 8,635 |
| v5 | `v5_train_seed.jsonl` | 11,329 | 2,694 | 8,635 |

⛔ **`v4_train_seed.jsonl` is NOT v4's corpus** — it holds 11,304 rows (pos 2,673, neg 8,631)
against v4's published 11,308 / 2,673 / 8,635. It is the obvious file to reach for by name and
it would have produced a clean-looking grid answering a different question.

## Leakage — computed, not hand-listed

v4 and v5 were corrected using rows drawn from the heldout split, so those rows must go. The
exclusion is computed as *every heldout row appearing in any version's training corpus*:

| version | heldout rows in its training corpus |
|---|---|
| v3 | **0** |
| v4 | 4 |
| v5 | 25 |
| union (excluded) | **25** -> eval set n=1,537 |

**This reconciles the published n=1,529 exactly.** There are **33 distinct panel-graded ids**
(21 hard positives ∪ 28 fn-delta ∪ 5 fp5, overlapping). The published figure excludes all 33
*graded* rows; this study excludes the 25 that actually *entered training*. The 8-row
difference is rows a human adjudicated but no model trained on.

Both criteria are defensible; they answer different questions, and "did any version see this
row in training" is the one a version comparison needs. ⚠️ Quoting a number from this study
beside the published `v5@0.90 prec 0.983 / rec 0.750` compares **n=1,537 against n=1,529** —
different denominators, and the exclusion is part of each figure.

Could the 8 rows change the conclusion? At most they move recall by ~2.5 points if all were
positives; the bands span 6.5–20.8 points and three different orderings occur. No.

## ⛔ What this does NOT establish

- **Seed is not separated from data.** Each version was trained on its own corpus only, so the
  seed effect and the data effect (v4's 12 hard negatives, v5's 21 hard positives) remain
  confounded. Separating them needs the same data under different seeds; ovr explicitly did not
  ask for it and it did not fall out of this design. **Not attempted, not claimed.**
- **This does not say v4 is better than v3 or v5.** It says the three cannot be ordered.
- **It says nothing about which version to deploy.** v5 is live at 0.85 and this study gives no
  reason to change that — it removes a reason that was being used to argue about it.

## Reproduce

```bash
scp scripts/multiseed.py scripts/reconcile.py b650-gpu:~/
ssh b650-gpu 'cd ~/llm-distillery && ./venv-prodparity/bin/python ~/multiseed.py'
ssh b650-gpu '~/llm-distillery/venv-prodparity/bin/python ~/reconcile.py'
```

Needs the obituary corpora staged on b650 (`training/data/`, gitignored). Embeddings cache to
`~/multiseed_cache/`. Window fixed at 128 (production; see the sibling
`2026-09-10-detector-window-128-vs-512` evidence for why widening was rejected).
