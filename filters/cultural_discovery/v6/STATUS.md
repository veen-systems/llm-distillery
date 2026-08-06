# cultural_discovery v6 — STATUS

**IN DEVELOPMENT. Not deployed. Not on the Hub.** (#98, opened on the owner's
2026-08-06 directive; scope agreed the same day: *probe first, dimensions later*.)

> **This package cannot score an article.** It contains `base_scorer.py`,
> `prefilter.py`, `config.yaml` and `probe/` — and nothing else. There is no
> `inference.py`, `inference_hybrid.py` or `inference_hub.py`, so nothing reads
> the `hybrid_inference` block or the probe pickle. There is also no
> `calibration.json` and no `normalization.json`, and **nothing inherits them
> from v5** — `_load_calibration` sets `self.calibration = None` *silently* when
> the file is absent, so adding an inference module and deploying would yield an
> uncalibrated scorer with no warning. Both gaps are in "Still to do" below.
> Recorded this loudly because a config block wired to nothing is this repo's
> signature defect (NexusMind#284, #94, NexusMind#281).

## What v6 is

One change: topic screening moves from keyword rules to a
`intfloat/multilingual-e5-small` probe, bringing cultural_discovery in line with
`nature_recovery v4` and `solutions v6`. An embedding probe cannot carry a
per-language keyword-coverage gap by construction — which is the defect #86 spent
2026-08-06 patching by hand (453 stems across ~25 languages).

Not changed: dimensions, weights, tier thresholds, the `evidence_quality`
gatekeeper, the oracle prompt, the student model. Those are #87, blocked on #95.

The v5 keyword gate is **still in `prefilter.py`, unchanged**. It is not removed
until the owner acts on the results below — that is #98 criterion 4.

## Acceptance measurement (2026-08-06)

All three gating criteria pass. Every number below is measured, not projected.

### Criterion 3 — FN on MEDIUM+ against oracle ground truth

Held-out test split, `datasets/training/cultural-discovery_v5/test.jsonl`,
n=857, 75 MEDIUM+ positives. This is the only arm judged against *oracle* labels
rather than against the deployed student, per ADR-021.

| | FN on MEDIUM+ | recall | screens out (this split) |
|---|---|---|---|
| **probe @ 2.50 (shipping)** | **0/75 = 0.0%** | 100% | 51.2% |
| probe @ 3.025 (trainer-selected) | 5/75 = 6.7% | 93.3% | 64.8% |
| keyword gate (453 stems) | 10/75 = 13.3% | 86.7% | 50.8% |

At the shipping threshold the probe misses nothing this split contains, at the
same screening rate as the gate it replaces. At 3.025 it still misses half as
many positives as the gate while screening 14 points more, though those two
Wilson intervals overlap (2.9–14.7% vs 7.4–22.8%) and at n=75 that comparison
alone does not separate them.

Read the screening column here as split-local only — see the production table
for the number that governs deployment.

### Criteria 1 and 2 — production window

64 cycles, `filtered_20260724_085740` .. `filtered_20260803_210045`,
156,226 scored rows, 2,653 surfacing (raw ≥ 4.0), 17 high-tier.
Both arms computed in a single pass over identical rows.

**Shipping threshold is 2.50** (see the threshold note below); 3.025 is shown
because it is what `train_probe.py` selected and it is the more favourable
column on screening.

| | baseline (gate) | **probe @ 2.50** | probe @ 3.025 | #98 target |
|---|---|---|---|---|
| gate pass rate | 0.2983 (exact) | **0.3629** (±0.0054) | 0.2204 (±0.0046) | not materially less screening |
| → screens out | 70.2% | **63.7%** | 78.0% | |
| surfacing blocked | 337 = **12.7%** | **1 = 0.04%** | 26 = 1.0% | ≤ 12.6% |
| English | 12.4% | **0.0%** | 1.0% | ≤ 11.7% |
| non-English | 13.2% | **0.1%** | 1.0% | ≤ 14.0% |
| high-tier blocked | 0 | **0** | 0 | 0 |

The per-language spread does not merely improve, it collapses: at 2.50 exactly
one surfacing article in the whole window is screened out (Portuguese), and
every other language sits at 0.0%.

Criterion 2 is the one place the probe is **worse** than the gate: at 2.50 it
screens 63.7% of the firehose against the gate's 70.2%, i.e. ~6.5 points less.
Accepted because the surfacing cost falls from 337 articles to 1 — the screening
given up is screening of material that was never going to surface.

**Not a valid justification, though it reads like one:** "63.7% matches
`nature_recovery v4`'s ~64%". nr v4's figure is a **val** screening rate on its
own label set; 63.7% is a **production firehose** rate. Different populations,
different denominators. cd v6's own val-set equivalent is 51.2%, which is not
~64%. An earlier version of this file made that comparison; it was a review
finding on 2026-08-06 and is the same category error as the screening-parity
claim corrected below.

Do not carry the test-split screening figures over to production: the label set
is positive-enriched (9% MEDIUM+) against a 1.7% surfacing rate in the firehose,
so the two screening rates are genuinely different quantities. An earlier draft
of this file claimed 2.50 was at screening parity with the gate; that came from
the test split and is wrong for production.

### Reproduce

```bash
# on sadalsuud, from the NexusMind repo root (the post-#86 gate must be staged —
# sadalsuud's own checkout still carries the 235-stem pre-fix version)
scp <llm-distillery>/filters/cultural_discovery/v5/prefilter.py sadalsuud:/tmp/cd_v5_gate_postfix.py
# --offset counts back from a GROWING file list, so 15 selects a different
# window every day. The window measured here is the 64 cycles ending
# filtered_20260803_210045 (first: filtered_20260724_085740). To reproduce it,
# recompute the offset against today's listing:
#   ls data/filtered/cultural_discovery/filtered_2026*.jsonl | \
#     grep -n filtered_20260803_210045   # -> N
#   offset = (total files) - N
python3 scripts/gate/extract_probe_ab_rows.py --gate /tmp/cd_v5_gate_postfix.py \
    --cycles 64 --offset "$OFFSET" --sample 30000 --seed 42

# on gpu-server
HF_HUB_OFFLINE=1 PYTHONPATH=. python scripts/gate/score_probe_ab.py \
    --filter filters/cultural_discovery/v6 --threshold 2.50 \
    --labelled datasets/training/cultural-discovery_v5/test.jsonl \
    --gate filters/cultural_discovery/v6/prefilter.py
HF_HUB_OFFLINE=1 PYTHONPATH=. python scripts/gate/score_probe_ab.py \
    --filter filters/cultural_discovery/v6 --threshold 2.50 \
    --rows /tmp/cd_v6_ab_rows.jsonl --summary /tmp/cd_v6_ab_summary.json
```

Pass `--threshold 3.025` to either command to reproduce the trainer-selected
column in the tables above.

## Read these before quoting the numbers above

**The threshold shipped is 2.50, not the 3.025 `train_probe.py` selected.**
`--target-fn 0.02` was requested. The trainer picks the threshold off the **val**
recall curve, so val FN is optimistic by construction — it reported 1.3% at
3.025, and the held-out test split gives **6.7%** at the same threshold. Val and
test independently both give FN exactly 0.000 at every threshold ≤ 2.50 (0/152
positives across the two), so 2.50 is supported by the split it was not selected
on. Owner decision 2026-08-06.

**But the recall gain is smaller than 6.7% → 0.0% makes it look.** All five
held-out positives recovered by dropping to 2.50 were read. **Four are off-lens**:

| oracle wa | probe wa | article |
|---|---|---|
| 4.20 | 2.895 | ImmunoStruct — deep learning for immunogenicity prediction |
| 4.65 | 2.633 | Flock exposed its AI-powered cameras to the internet |
| 4.78 | 2.779 | How French spies are betrayed by advertising data |
| 5.62 | 2.678 | Lauwersoog dyke gap as sea-level-rise protection |
| 4.05 | 3.011 | Identity of a homeless man found dead in Amsterdam, after 33 years |

Only the last reads as cultural. The oracle scored the others ≥ 4.0 on
`discovery_novelty` + `evidence_quality` with `cross_cultural_connection` at 0–2
— which is #87's lens-fidelity dilution appearing in the labels, not a probe
defect. So the FN metric here is partly measuring label noise.

2.50 remains the right choice, but **not** on the grounds that those five are
losses. The reason is structural: recall is Stage 1's job and precision is Stage
2's. Using a screening threshold to suppress off-lens content would hide lens
policy in the wrong layer, and those four articles reach the student and the 4.0
op-point either way — if they surface, that is #87, and tuning this threshold
would only conceal it.

**Criterion 1 is an agreement measurement, not an independent one.** "Surfacing"
means the deployed *student* scored the article ≥ 4.0. The probe and the student
are trained on the same oracle labels; the keyword gate never was. Some of the
probe's advantage on criteria 1–2 is that shared training signal rather than
better judgement. Criterion 3, against oracle labels, is the arm that does not
have this problem — and the probe wins there too, which is why the conclusion
holds. Do not quote the 12.7% → 1.0% figure as if it were a ground-truth result.

**Do not read per-article agreement inside the noise floor.** 347 of the 2,653
surfacing rows (13.1%) sit within |0.16| of the 4.0 op-point, which is the
batch-composition noise floor #95 measured. Claims of the form "the probe agreed
with the gate on this article" are not evidence for those rows.

That caveat applies to the **raw student score** side of the comparison only.
**The probe itself is batch-invariant** — measured 2026-08-06 across shuffled
order, chunk size 256 → 97 and encode batch 64 → 13 → 1: max |Δ| **3×10⁻⁶**,
mean 5×10⁻⁷, **zero threshold flips at 2.50**, and zero articles sitting within
max|Δ| of the threshold. So unlike student scores (#95, |Δ| ≤ 0.162), a probe
decision on a given article is reproducible. Reproduce with
`scripts/gate/probe_batch_invariance.py`.

**The window is not byte-identical to #86's.** #86's held-out run was 64 cycles
07-23..08-03 with 2,768 surfacing rows; this is 64 cycles 07-24..08-03 with
2,653, because another production cycle has landed since. The baseline
reproduces closely (12.70% vs 12.6% surfacing blocked; pass rate 0.2983 vs
0.3014), and the A/B itself is internally exact — both arms walk the same rows.

## Still to do before this can deploy

1. ~~Owner decision on the threshold.~~ **Settled 2026-08-06: 2.50.**
2. Criterion 4 — strip the topic gate and the four exclusion categories, bring
   `prefilter.py` to the `BasePreFilter` declarative shape (ADR-018/019).
   **Not started; deliberately.**
3. #99 — `DISCOVERY_PATTERNS` also feeds `classify_content_type`, which the probe
   does *not* replace. Decide in scope, not by omission.
4. ADR-012 rename to the exact lens name (Discovery) belongs with this bump.
5. **Make the package loadable.** It has no `inference.py`,
   `inference_hybrid.py` or `inference_hub.py`, so nothing reads
   `hybrid_inference` or the probe. Port them from v5 when v6 gets a model.
6. **Add `calibration.json` and `normalization.json`.** They are *not* inherited
   from v5 — there is no such mechanism, and `_load_calibration` fails silent
   (`self.calibration = None`, no warning) when the file is missing. An earlier
   version of this file claimed inheritance made it "consistent"; that was
   wrong, and it is the failure mode where a deploy scores uncalibrated and
   nothing says so. Either copy v5's (valid only while v6 reuses v5's student)
   or refit — but the file must exist.
7. Ships stamping-only per ADR-022 — a probe actually runs, unlike the rule
   prefilter (ducroq/NexusMind#284), so enforcement is a separate config flip.

Items 5 and 6 were both review findings on 2026-08-06, not known gaps — the
package read as complete until the lenses were run against it.
