# Reviewing the 6,586 labels before anything trains on them

**2026-09-02. $0** — analysis only, no calls. Reviews `labels_k3.jsonl` and the per-run files
from `EXP-010`. Nothing under `filters/` changed; no model, threshold or probe touched.

⚠️ **Read this before Phase C.** These labels are the training targets. Every defect here becomes
a property of the student, and the student is what reaches readers.

---

## 1. Anti-hallucination: the evidence quotes hold, at **0.063%**

The v8 prompt requires each dimension's `evidence` to be an **EXACT QUOTE** or one of three
sentinels. Nobody had checked that at scale. Over **39,516 evidence slots** (6,586 rows × 6
dimensions, from `run1` — the aggregate drops evidence strings by design):

| | | |
|---|---|---|
| sentinel (*"No evidence in article"* etc.) | 31,916 | **80.767%** |
| verbatim in the payload | 7,168 | **18.139%** |
| punctuation or requoting only | 224 | 0.567% |
| half verbatim — stitched or trimmed | 183 | 0.463% |
| **no match — paraphrase or invention** | **25** | **0.063%** |

⭐ **99.94% of evidence strings are either the prescribed sentinel or traceable to the text the
oracle was given.** The remaining 25 are mostly ellipsis-joined fragments, a translated Arabic
quote rendered in English, and one row where the model wrote its own sentinel wording instead of
the prescribed one.

### ⛔ The instrument was wrong three times, and each correction shrank the defect 

This is the finding that generalises, so it is recorded rather than tidied away:

| what I compared against | "defect" rate |
|---|---|
| the **full article** | 1.19% |
| the **compressed view** (`smart_compress`, head 560 + tail 240 words) | 1.19%, and 1 quote "from the elided middle" |
| the **exact payload** `build_prompt` sends — title + source + date + body | **0.063%** |

The first pass overstated by **19×**. The cause each time was the same: I had not established
what my *own source* excluded. The title line is in the payload and not in `content`, so every
quote from a headline read as a fabrication — and headlines are exactly what a model reaches for
when the body is thin. ⚠️ Only **1** slot in 39,516 quoted the elided middle, so
`smart_compress` is not a meaningful factor at this corpus's length distribution.

## 2. All six dimensions are alive; none is dead

| dimension | weight | ≤2.0 | median | p90 | p99 | max | distinct values |
|---|---|---|---|---|---|---|---|
| `human_wellbeing_impact` | 0.30 | 77.9% | 1.00 | 5.00 | 7.00 | 8.33 | 31 |
| `social_cohesion_impact` | 0.20 | 84.4% | 0.67 | 3.00 | 6.33 | 8.33 | 27 |
| `justice_rights_impact` | 0.15 | 92.1% | 0.67 | 2.00 | 6.33 | 9.00 | 27 |
| `evidence_level` | 0.10 | 77.3% | 0.67 | 5.00 | 7.33 | 9.00 | 27 |
| `benefit_distribution` | 0.10 | 79.9% | **0.00** | 4.33 | 6.00 | 8.00 | 25 |
| `change_durability` | 0.15 | 77.2% | 1.00 | 5.00 | 7.00 | 9.00 | 29 |

⛔ **A high zero rate is base rate, not breakage** (`memory/solutions-v6-dimension-hypotheses.md`)
— this corpus is 93% below the op-point by construction. Every dimension reaches 8+ somewhere,
so none is inert. ⚠️ `benefit_distribution` is the only one with a median of exactly **0.00**;
worth watching at Phase C, not acting on now.

⭐ **25–31 distinct values per dimension against ~21 for a single run** — this is the discrete-score
problem `average_oracle_runs.py` was originally written to fix, and k=3 does fix it.

## 3. The `evidence_level` gatekeeper is reachable, and it bites on 32 rows

| | |
|---|---|
| rows below the `evidence_level < 3.0` threshold | **5,284 = 80.2%** |
| rows where the 3.0 cap actually **lowers** the weighted average | **32 = 0.49%** |

⭐ **Screening a lot and changing almost nothing are different things**, and only the second is
what a gate does. This one is not inert — LD#94's `concreteness_gatekeeper` binds 0 times in
191,616 articles — but 32 rows is close to the line, and quoting the 80.2% as the gate's effect
would be wrong by 165×.

⚠️ **This measures the gate on the ORACLE LABELS, not in production.** In production it applies
to *student* scores over a different distribution. Do not carry 0.49% across.

## 4. ⭐⭐ The `--aggregate` choice, decided on data

`aggregate_k_runs.py` writes both `weighted_mean_all` and `weighted_mean_major`. **35 rows** —
0.53% of the corpus — land on different sides of the 4.5 op-point depending on which is used.

```
--aggregate majority PROMOTES above the op-point: 35
--aggregate majority DEMOTES below it:             0
```

**On every one of the 35, `all` is the more conservative rule.** Under ADR-023 — a false positive
reaches a reader, a false negative does not — that settles it: **`--aggregate all` is the right
default**, and it is what `labels_k3.jsonl` was written with.

Sampled, the rows `majority` would promote look like the promotion is wrong:

| `all` | `major` | verdicts | article |
|---|---|---|---|
| 4.37 | 6.10 | response_to_harm / in_scope / in_scope | *"Semriach kämpft gegen Abschiebung"* — a fight against a deportation |
| 4.23 | 5.83 | in_scope / in_scope / response_to_harm | *"Oposición y ONG piden liberar a los presos políticos"* — a demand, not a release |
| 3.75 | 5.20 | harm_is_subject / in_scope / in_scope | *"Waiyaki family **loses** fight for Nyari apartments"* |

⛔ **But the tidy explanation for this is WRONG, and it is recorded because it nearly shipped.**
I wrote that `all` is *systematically* lower because a minority `out_of_scope` run drags the plain
mean down. Across all **1,011** gate-flipped rows the split is **majority lower 47.2% / higher
41.5% / equal 11.3%** — near-balanced, not systematic. The 35 are a **selection effect**: they are
precisely the rows where majority is higher *and* `all` sits just under the line. The
recommendation stands; the mechanism I gave for it did not.

## 5. Spot-check of the strongest positives — three worth a second look

The top of the distribution is what the student learns as a strong positive. Most are sound —
a heart-transplant homecoming, a constitutional court victory for a coastal community, Lebanon
abolishing the death penalty, Venezuela releasing 1,046 political prisoners, Ethiopian health
coverage gains. ⚠️ Three are worth the owner's eye:

- **7.28 — *"EXPLAINER: 35 Years Ago Today, the World Held Its Breath"*.** A historical
  retrospective, scoring third-highest in the corpus, from a `neg_mid` cell. #107's predicate is
  *a process going well for people, **now***; a 35-year-old anniversary piece is not that.
- **6.63 — *"Prime minister: As a nation, we are now wealthier than ever"*.** A politician's
  assertion, not a documented outcome.
- **4.88 — La Tomatina** (22,000 people, 150 tonnes of tomatoes) and **4.87 — *"Zelensky arrives
  in Chisinau"***. Both sit just above the op-point, which under ADR-023 is exactly where a false
  positive reaches a reader. A festival and a diplomatic visit are neither harm nor delivered
  benefit.

⚠️ **These are candidates for the v8.1 prompt pass, not defects to patch in the labels.** Editing
labels by hand is how a corpus stops being reproducible.

## 6. What this review does NOT cover

- **No comparison against v7's labels.** ADR-021 judges against held-out oracle ground truth,
  never against the prior deployed model, and that gate is Phase D.
- **No student.** §1f measured 2 of 3 class-A rows as the *student* disagreeing with every
  oracle; nothing here touches that, and Phase B2 hard negatives remain the larger half.
- **The 47-row class-A supplement is still unadjudicated** — `tp_fp_status:
  adjudication-pending`. Its numbers are in `2026-09-01-phase-b-labels/` §4.

## Reproduce

```bash
D=datasets/scored/human_thriving_v8
PYTHONPATH=. python3 docs/evidence/2026-09-01-phase-b-labels/summarise.py \
  $D/labels_k3.jsonl $D/corpus.jsonl
```

⚠️ The evidence-quote check must compare against the payload `build_prompt` assembles, not
against `content` — see §1. The labels themselves are gitignored (article text at corpus scale,
#97).
