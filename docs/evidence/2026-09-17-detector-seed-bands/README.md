# The first banded detector artifacts, and seed 42 is the bottom draw on one of them (#158, 2026-09-17)

⛔ **Headline: the seed rule now produces bands, and on the obituary corpus the seed every shipped
number was published at is the WORST of the five.** `oof_recall_at_0.85` per seed:
**42 → 0.7275** · 7 → 0.7587 · 13 → **0.7873** · 101 → 0.7565 · 2026 → 0.7561. At 0.95 the same
ordering holds at the bottom: **42 → 0.6184** against a max of **0.7361**. Seed 42 is the minimum
at both thresholds measured.

⚠️ **One corpus, two thresholds — not a claim that 42 is pessimistic in general.** On the violence
corpus seed 42 lands mid-band (0.5498 against 0.5403–0.5829, the median).

Spend: **$0** — no oracle calls. b650-gpu (RTX 5090), `venv-prodparity`, device cuda.
⛔ **Nothing shipped was touched**: both runs wrote to scratch directories
(`~/exp158-band-proof`, `~/exp158-violence-proof`), and no model artifact was replaced.

## Why this run exists

`#158` is a REPORTING defect: `early_stopping=True` lets `random_state` pick the internal
validation split, so a head trained with everything else fixed is one draw. The fix (commit
`842e39e`) moved the rule into `filters/common/detector_seeds.py`, made both trainers run
out-of-fold once per seed over `EXP-033`'s set, and added a checker. ⛔ **But at that commit the
checker reported `0 banded`: the mechanism was in place and no artifact had ever been produced by
it.** That is this repo's signature defect shape, so the trainers were run.

**Both trainers, because only one had executed.** The obituary edit was proven by a run and the
violence edit was not, and two files changed in the same commit are not one change.

## What came out

### Obituary detector, `v5_train_seed.jsonl` (11,329 rows, 2,694 positive), 5-fold OOF

| metric | min | median | max | spread | seed 42 |
|---|---|---|---|---|---|
| `oof_recall_at_0.85` | 0.7275 | 0.7565 | 0.7873 | **0.0598** | **0.7275 (min)** |
| `oof_precision_at_0.85` | 0.9018 | 0.9141 | 0.9196 | 0.0179 | — |
| `oof_f1_at_0.85` | 0.8123 | 0.8292 | 0.8407 | 0.0284 | — |
| `oof_recall_at_0.95` | 0.6184 | 0.6778 | 0.7361 | **0.1177** | **0.6184 (min)** |
| `oof_precision_at_0.95` | 0.9245 | 0.9378 | 0.9498 | 0.0254 | — |
| `oof_f1_at_0.95` | 0.7491 | 0.7866 | 0.8196 | 0.0705 | — |

### Violence promotion detector, `training_scored.jsonl` (1,957 rows, 211 positive), 5-fold OOF

| metric | min | median | max | spread | seed 42 |
|---|---|---|---|---|---|
| `oof_recall_at_0.95` | 0.5403 | 0.5498 | 0.5829 | 0.0427 | **0.5498 (median)** |
| `oof_precision_at_0.95` | 0.9077 | 0.9355 | 0.9661 | 0.0584 | — |
| `oof_f1_at_0.95` | 0.6845 | 0.6925 | 0.7214 | 0.0369 | — |

⭐ **The violence run reproduces the SHIPPED number exactly**: `filters/common/violence_promotion/
v1/models/training_config.json` publishes `oof_recall_at_0.95` **0.5498**, and seed 42 here is
**0.5498**. Same corpus, same protocol, same seed, a different box and seven weeks later.

⛔ **The obituary run does NOT**: shipped v5 publishes **0.6002**, this run's seed 42 is **0.6184**.
So the exact reproduction above was reachable and was not guaranteed — the instrument can say
"different", and on the other detector it did. ⚠️ `EXP-034` already measured why: a refit at seed
42 correlates 0.9771/0.9713/0.9952 with the shipped heads but **is not them**, and v5's corpus is a
reconstruction (`build_v5_seed.py`).

## ⛔ These are NOT the numbers in `#158`'s issue body

`#158` quotes **heldout** recall at 0.85 spanning **0.6599–0.8081** (`EXP-033`). Everything here is
**out-of-fold recall on the training corpus** — a different population and a different instrument.
The two spreads (0.148 there, 0.0598 here) are not comparable and neither reproduces the other.
What both say is the same qualitative thing: the seed moves recall by more than the differences
these detectors get compared on.

## What this does NOT establish

- **That any shipped model should be replaced.** `#158` is explicit that it does not claim that,
  and nothing here changes it. Obituary v5 stays live at 0.85.
- **That seed 42 is systematically pessimistic.** Two thresholds on one corpus; the other corpus
  disagrees.
- **A heldout number for either detector.** No heldout set was scored in this run.
- ⚠️ **Anything about the GPU swap.** Both runs are Blackwell-only; there is no Ampere arm, so
  nothing here separates the seed effect from the device (`EXP-038` is the parity record).

## Files

`obituary_v5corpus_training_config.json` · `obituary_v5corpus_calibration_report.json` ·
`violence_v1corpus_training_config.json` · `violence_v1corpus_calibration_report.json` — the
artifacts as the trainers wrote them, renamed only to sit side by side.

⚠️ **Renamed deliberately, and the guard says so**: `check_detector_metric_bands.py --root` on this
directory prints **CANNOT VERIFY** rather than PASS, because these are records of one run and not
shipped artifacts, so they must not count as guarded sites. Pointed at the scratch dirs on b650 it
printed **`2 site(s) examined, 2 publish metrics — 2 banded, 0 declared single-seed`** for each
detector, which is the outcome `842e39e` could not claim.
