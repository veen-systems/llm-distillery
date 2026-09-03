# Re-scoring every above-op row under v8.4 — 140 of 456 demote, and 115 were invisible to the generators

**2026-09-03.** 2,736 calls, **0 errors**, all six passes complete at 456/456. Balance probed
before launch. Prompt `prompt-v8-4.md`, `sha c4705408c477`, k=6, `--aggregate all`.

## Why the whole above-op population and not the 50 staged rows

The 50 staged rows were chosen by the self-contradiction and future-tense **generators**. A
generator finds what it was written to find. Above the op-point is where a bad label reaches a
reader (ADR-023), so the population — not a sample of it — is the right unit.

**That decision is what the result vindicates:** of the 140 demotions, **115 were rows no
generator flagged**. Sampling would have found 25 of 140.

## The result

| | v8 k=3 | v8.4 k=6 |
|---|---|---|
| above the op-point | 456 | **316** |
| **demoted below it** | — | **140 = 30.7%** |
| mean score | 5.208 | 4.641 |
| mean per-row sd | — | 0.438 |

Largest drops among rows no generator flagged, all with the oracle's own v8 `dominant_subject`:

| v8 → v8.4 | article | what it was |
|---|---|---|
| 6.00 → **0.93** | *Good News in History, August 18* | "historical milestones and anniversaries" |
| 5.13 → **0.52** | Moderna/Merck mRNA cancer vaccine, phase 3 (ko) | "a clinical trial showing… reduces recurrence" |
| 5.28 → **0.91** | *«Προσωπικός Βοηθός»* (el) | "the **opening of the platform for applications**" |
| 5.03 → **0.72** | *COP17 in Mongolia* | "COP17 **conference** on land degradation" |
| 4.93 → **0.92** | Hamas peace-agreement statement (el) | "**reiterating commitment** to a peace agreement" |
| 4.77 → **0.79** | EU wildfire response (pt) | "EU **mobilizing** firefighting resources" |
| 4.65 → **0.72** | Alcalá de Henares festivals (es) | "the **programme** of the 2026 festivals" |

⭐ **These are the shapes the clauses were written for**, reached in seven languages, and none of
them was flagged by a Latin-script generator. *"EU mobilizing resources"* is §1's money-committed
rule verbatim; *"reiterating commitment"* and *"opening of the platform for applications"* are A3.

## ✅ The §4 "DO NOT SUPPRESS" check — the protection that matters holds

Matched against the oracle's own v8 `dominant_subject` over the 140 demotions:

| §4 category | demoted |
|---|---|
| **transitional justice** | **0** |
| repair received | 1 |
| recovery narrative | 3 |
| measured improvement in a harm | 7 |
| medical outcome | 11 |

⭐ **Zero transitional-justice rows.** The plan states that *"a v8 that fixes class A by
suppressing transitional justice or recovery narratives has failed, whatever Gate B-A says"* —
that is the check, and it passes.

## ⛔ Three caveats that must travel with this

1. **One demotion looks wrong.** The Moderna/Merck **phase 3** result — a personalised mRNA
   cancer vaccine reducing melanoma recurrence in patients — went **5.13 → 0.52**. A phase 3
   trial has patients and a measured outcome; it is not the preclinical class-B shape. **Owner
   eye wanted.** (The other two medical movers look right: Queen Camilla discussing a diagnosis
   4.75 → 3.36, and an FDA approval 4.65 → 3.94 which barely moved.)
2. ⚠️ **Only 75 of the 140 demotions are stable** (sd < 0.5); the other 65 are not, and 118 of
   the demoted rows still return `in_scope` on some runs. Roughly half the demotions are score
   shifts inside `in_scope`, not verdict flips. **Do not describe all 140 as "the gate firing".**
3. ⛔ **The positive class shrank by 30.7%: 456 → 316, a base rate of 6.92% → 4.80%.** That is a
   real change to the training distribution, and it now sits **below** production's measured
   7.74%. Under ADR-023 the direction is the safe one, but Phase C must set the probe's
   objective against 4.80%, not against the old number.

## What was written

`datasets/scored/human_thriving_v8/labels_v84_merged.jsonl` — 6,586 rows, **456 replaced**.
⛔ **`labels_k3.jsonl` is untouched.** Provenance is per row and explicit:

```
prompt_hash: {'003cd35a5122': 6130, 'c4705408c477': 456}
k:           {3: 6130,             6: 456}
```

Both are gitignored (#97, article text at corpus scale). Per-row before/after with verdicts and
sds: `datasets/scored/human_thriving_v8/v8_4/comparison.json`.

## What this does NOT do

- **The 6,130 rows below the op-point keep their v8 k=3 labels.** That is deliberate: the
  bimodality concentrates there, `--aggregate all` already suppresses it, and ADR-023 calls
  those errors the cheap ones. A full re-label was considered and **rejected** — it would
  invalidate the label review, the class-A adjudication and every population figure measured
  today, to buy precision where errors do not reach readers.
- **No student exists yet**, so nothing here is a production claim.
