# Datasets Directory

Local-only data used to train, calibrate and gate the filter scorers.

**Nothing here is in git** except this README and `.gitkeep` — `datasets/` is
gitignored. Treat every path below as "exists on the machine that produced it",
not "available after a clone".

---

## What is actually here

| Directory      | Holds                                                             | Used for                            |
| -------------- | ----------------------------------------------------------------- | ----------------------------------- |
| `training/`    | `train/val/test.jsonl`, one subdirectory per filter version        | student training                    |
| `scored/`      | Oracle-scored corpora, plus the batch inputs and logs that made them | label production, hard-case mining |
| `calibration/` | The same articles scored by several oracles, plus disagreements     | calibration, oracle-bias analysis   |
| `gate/`        | Held-out probes and per-model scored outputs — see below            | deploy gating                       |
| `screening/`   | Topic seed sets for finding candidate articles                      | corpus screening                    |

Present at time of writing: `training/{nature_recovery_v4, solutions_v4,
solutions_v6}`; `gate/` and `scored/` dominated by `nr_v4_*` (nature_recovery v4)
and `solutions_v*`. Filters absent here have not been through this pipeline.

**Naming**: `<filter>_<version>_<purpose>.jsonl`. `nr_` abbreviates
`nature_recovery`, but the abbreviation is not applied consistently
(`solutions_v4_*` is spelled out), so match on version and purpose rather than
prefix.

**A note on these names.** Most directories here are named for a *stage*
(`training`, `calibration`, `screening`) rather than a property of the data, and
`gate/` is named for its *consumer*. The data-honest name for `gate/` would be
`heldout/` — held out of training, carrying oracle labels — but it is referenced
by `scripts/gate/*.py`, the nature-recovery runbook and the plan docs, so it stays.
Know that the directory name describes who reads the file, not what is in it.

---

## "gate" means deploy-blocking evidence

A **gate** answers one question: _may this trained student be deployed?_ Score a
held-out cohort with the candidate, compare against oracle ground truth, and if it
fails, do not ship. `datasets/gate/` holds the evidence such a run needs —
deliberately **held out of training**, so the comparison is honest.

### Not the *gatekeeper*

`filters/*/base_scorer.py` defines `GATEKEEPER_DIMENSION`: a rule applied at
**inference** that caps an article when a required dimension is too low (for
nature_recovery v4, `recovery_evidence < 3.0` caps the article at 3.5, below the
surfacing threshold).

|              | gate                              | gatekeeper                 |
| ------------ | --------------------------------- | -------------------------- |
| **blocks**   | a model deploy                    | an individual article      |
| **runs at**  | release time                      | inference time             |
| **lives in** | `scripts/gate/`, `datasets/gate/` | `filters/*/base_scorer.py` |

Same root word, opposite objects. From an ovr.news context, note that "the
editorial gate" there is a third, unrelated thing — a retired LLM rule that
dropped articles.

### Probe kinds

- `*_heldout_probes.jsonl` / `*_heldout_ids.txt` — test-split articles kept out of
  training, with oracle scores. The main agreement cohort.
- `*_protection_probes.jsonl` — a curated cohort for one editorial claim (for
  nature_recovery: delivered protection). Note these are **positives** that must
  keep scoring well, not adverse examples.
- `*_named_probes.jsonl` — individually chosen articles that must score correctly;
  regression tests for known-hard cases.
- `*_oos_trainpool.jsonl` — out-of-sample pool; not a gating verdict.
- `*_test_scored.jsonl` / `*_scored_by_<version>.jsonl` — a cohort after scoring by
  one model. `ground_truth_gate.py` takes one per model plus a labels file.
- `*_sourceA_reference.jsonl` — **historical; do not gate on it** (see below).

Record shape, from `nr_v4_protection_probes.jsonl`:

```json
{
  "id": "positive_news_mongabay_bdb6a20f9553",
  "title": "In Kyrgyzstan, a climate-ready corridor gives snow leopards and herders room to roam",
  "content": "...",
  "url": "https://news.mongabay.com/...",
  "oracle_wa": 5.25,
  "recovery_evidence": 4.0,
  "protection_durability": 6.0,
  "protection_primary": true,
  "provenance": "test_split_heldout"
}
```

### Which gate script

Use **`scripts/gate/ground_truth_gate.py`**.

`scripts/gate/agreement_gate.py` is **superseded and must not produce a deploy
verdict.** It judged a candidate against the *previous student* rather than oracle
ground truth, and drew its cohort from `nr_v4_sourceA_reference.jsonl` — v2-era
Gemini labels, +1.775 inflated relative to the DeepSeek labels v4 trained on. A
deliberately conservative DeepSeek-trained student was measured against a generous
baseline, so its *correct* demotions counted as failures: a false FAIL. Judge
against held-out oracle labels; the oracle a model trained on is the chosen
editorial line. Kept for provenance only.

---

## `adverse/` — curated hard negatives (proposed)

Not yet created. Reserved for articles that **look like the lens and are not**,
with oracle labels near zero.

This is a property of the data, not a stage, which is why it gets its own
directory rather than living in `gate/`: adverse examples are useful as training
signal *and* as gate probes, and mixing them into a directory of positives-that-
must-keep-scoring makes both harder to reason about.

Why they need curating rather than sampling: random negatives
(`scripts/experiments/sample_v7_negatives.py`) teach the boundary between "in the
lens" and "unrelated" — a boundary the scorers already handle. They teach nothing
about the boundary that actually fails, between a story *about* a good outcome and
a story about harm that *contains* one.

Worked example — issue #91: an investigation into a community where girls are
raised into sex work scored **6.77 raw on `uplifting`, 6th highest of 3,530
articles**, against a median of 1.37. It opens on a mother determined her daughters
will escape, and the filter scored that thread rather than the article's subject. A
handful of such cases is worth thousands of random negatives.

Suggested shape: the probe record above, with `oracle_wa` near zero, a
`provenance` naming where the failure was observed, and a short `why_adverse`
string stating which surface feature misleads.

---

## Adding a filter to this pipeline

1. Screen candidates (`screening/` seeds) → oracle-score → `scored/`.
2. Split into `training/<filter>_<version>/{train,val,test}.jsonl`, holding out the
   probes you intend to gate on.
3. Put those probes in `gate/` with oracle scores and `provenance`.
4. Train, score the held-out cohort with the candidate, gate with
   `ground_truth_gate.py`, and only then deploy.

---

## History

Before 2026 this directory held a single 51,869-article `master_dataset.jsonl`
under `raw/` with global `splits/`, and this README documented that layout. The
project moved to per-filter, per-version datasets; `raw/`, `processed/`, `splits/`
and `test/` no longer exist. `.gitignore` still lists them, harmlessly.

_Rewritten 2026-08-01: the previous version documented only directories that no
longer exist, and none of the five that do._
