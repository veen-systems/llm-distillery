# Class A (harm-adjacent) is BOTH a label defect and a student defect — three-oracle bake-off

**Measured 2026-08-20.** Scores: [`2026-08-20-class-a-valence-bakeoff-scores.json`](2026-08-20-class-a-valence-bakeoff-scores.json).
Harness + reproduce steps: `scripts/analysis/valence_bakeoff.py`.
Companion: [`2026-08-20-uplifting-v7-oracle-genre-bias.md`](2026-08-20-uplifting-v7-oracle-genre-bias.md) (#125, class B).

## One-line answer

**Of three class-A rows, one fails on all three oracles (a label defect the v8 prompt
can fix) and two are the student alone (which the prompt cannot reach).** A prompt-only
v8 would have fixed roughly a third of the class the owner ranked worst.

## The question

`uplifting v7` scores harm-adjacent stories at `human_wellbeing_impact` **6.66–7.75**.
Those numbers are **student** scores from production. Nobody had ever asked the oracle.
The fork: if the oracle agrees, v8's prompt rewrite fixes class A; if only the student
does, it cannot.

## Method

Same prompt (`filters/uplifting/v7/prompt-compressed.md`), same clean/compress/sanitize
path, `temperature=0.3` on all three arms. Weighted average re-derived from the deployed
`DIMENSION_WEIGHTS` — a plain weighted average of raw dimensions, **no gatekeeper and no
calibration**, so it is not identical to the student's production `raw_weighted_average`.
Directionally sound; not the same quantity to two decimals.

Article text is the **exact text the scorer saw** for 8 of 10 rows, pulled from
`sadalsuud:~/local_dev/NexusMind/data/filtered/uplifting/` by `id`; content lengths match
`content_original_length` exactly. Two class-A rows predate the ~14-day archive window and
were refetched (greyhounds 2892/2917 = 99.1%; Namibian 3652/3652 = 100%).

## Result — class A (n=3), bar `max_acceptable_wa` = 3.85

| article | student | Gemini | DeepSeek | qwen3:14b | reading |
|---|---|---|---|---|---|
| Five men arrested … raping a minor | **6.85** | **7.62** | **6.25** | **7.30** | **all three fail — label defect** |
| Greyhounds / NZ racing ban | **5.86** | 2.30 | 3.95 ⚠️ | 2.00 | oracles right, **student is the outlier** |
| Rethink Business Centre Management | **6.09** | 1.55 | 1.80 | 4.35 | oracles right, **student is the outlier** |

⚠️ 3.95 is 0.10 over the bar — **inside the ±0.16 band, therefore indeterminate** (#95).

Means: student **6.26**, Gemini 3.82, DeepSeek 4.00, qwen3 4.55.

**The shared failure is robust.** Three independent model families — Google, DeepSeek,
Qwen — all place a rape-arrest story between 6.25 and 7.62. Run-to-run noise (below)
cannot produce that.

### The mechanism: cap-firing is the whole story on class A

| arm | caps fired (content_type ≠ `solutions_story`) |
|---|---|
| Gemini | **3/10** — `corporate_finance`, `doom_framed` ×2 |
| DeepSeek | 1/10 — `doom_framed` |
| qwen3:14b | **0/10** |

**Where a cap fired, the oracle got it right. Where the residual `solutions_story` bucket
was assigned, it failed.** On the shared-failure row all three assigned `solutions_story`
— i.e. **`individual_crime` (max_score 3.0, trigger "Single arrest, trial, conviction,
sentencing of individual(s)") did not fire on an article headlined "Five men arrested."**
The cap exists, matches on its face, and no oracle reaches for it. That is a concrete,
cheap prompt fix and it is the highest-value single edit identified so far.

⭐ **Gemini fires caps 3× more than DeepSeek — replicating the `cultural_discovery` v5
measurement (Gemini 60% vs DeepSeek 26%) on a different filter and a different prompt.**

## Controls

**Harness validation (positive control).** Sylvia Earle returned **2.55**, matching the
oracle value recorded in `datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md`
to two decimals. The harness reproduces the production oracle path.

**⚠️ Oracle run-to-run noise — the uncomfortable one.** Same oracle, same prompt, same
article, 10 days apart: **mean |Δ| 0.82, max 2.25** (EBA 2.70 → 0.45), n=7.

That is **5× the #95 batch-composition floor**, and it is a *fourth* noise floor with its
own population and mechanism (`feedback-noise-floor-per-population`). Consequences:
- **A single-run oracle score is not a measurement.** Average k runs (ADR-020's rule:
  cut noise by averaging the correctly-biased oracle).
- **Any acceptance gate phrased as "record X scores below 3.85 on one oracle run" is
  unsound.** It must be a k-run mean with a stated band.
- n=3 with single runs makes the *direction* strong and the *estimate* weak.

## Caveats

- **n=3 on class A.**
- ⛔ **Class B (7 rows) is selection-confounded and carries no weight here** — those rows
  were chosen in August *because* the oracle scored them below 4.0, so "the oracle scores
  them low" is true by construction. Reported in the JSON for completeness only.
- **The #91 flagship is missing.** The Hindu trafficking piece is now paywalled: 490 chars
  of 14,546 (3.4%). Scored as a flagged-confounded probe on the lede alone — the *most*
  misleading fragment, carrying every feature `why_adverse` lists — Gemini **3.70**,
  DeepSeek **3.90**, against the student's **6.77**. Suggestive that the student is the
  outlier there too; not counted.

## Consequences for `human_thriving` v8

1. **The prompt rewrite is necessary and not sufficient for class A.** It fixes the shared
   label defect; it cannot fix a student that scores 6.09 where all three oracles say ~1.7.
2. **Playbook §4b (production-feedback retraining) is the right tool for the residue** —
   collect production positives, panel-verify, **add confirmed FPs as hard negatives**,
   retrain. $0 oracle cost. (§4a probe-split remains closed: it preserves the high band.)
3. **Growing the class-A slice feeds both**, which makes it the critical path twice over.
4. **Vendor choice is second-order.** No oracle choice fixes a defect all three share, and
   the vendor gaps (0.18 on class A means) sit inside the 0.82 noise. **Build strictness
   into the mechanism, not the purchase order.**

---

## Footnote 2026-08-21 — don't misread `cap_applied: null`

`cap_applied` is **None on 236,879 of 236,879** production rows — but **not** for the
reason an earlier draft of this file gave. The runtime cap path never reads `content_type`:
`NexusMind/src/scoring/production_scorer.py:713` calls `detect_caps(filter_name, title,
content)`, a regex matcher, and `cap_triggers.py:103` is `_TRIGGER_REGISTRY = {}` —
**empty by design since 2026-07-14**, when `nature_recovery/climate_doom` was retired after
3 production bites, 3 false positives and 0 saves. So `detect_caps` returns `[]` for every
filter and the stamp correctly records "no cap applied".

⛔ **The stamp is not dead; the mechanism is deliberately disarmed and one registry line
from live.** The earlier "either populate the field or delete it" recommendation was wrong.
⚠️ Note this also means the five `content_type` caps in `uplifting v7`'s `config.yaml` are
inert because nothing *triggers* them, not because a field is missing.

⚠️ Kept short on purpose. The cap is a *mechanism detail*, not the defect. Two of the
three class-A rows are cases where the oracle was already right — no cap is involved — and
on the third a cap would have clamped the output without repairing the reading that
produced `human_wellbeing_impact` 7.5 on a rape-arrest story. **The defect is that the
scorer reads harm as wellbeing.** Do not let the greppable mechanism displace it.
