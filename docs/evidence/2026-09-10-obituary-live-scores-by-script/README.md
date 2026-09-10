# Is the obituary detector blind to non-Latin scripts in production? — No. Flag rates match at 1.00x.

**2026-09-10. €0, no labelling.** Run because the day's three other studies were all measured
on a heldout whose 344 positives are **100% Latin-script** — a population that cannot answer a
multilingual question, and would have returned a guaranteed zero if asked. The concern: obituary
enforcement is **live at 0.85** and actually drops articles, and ~39–42% of the input stream is
non-English.

**Answer: the detector is not blind in any script. Latin flags 1.252% of articles, non-Latin
1.249% — a ratio of 1.00x — and every script with meaningful volume produces confident
detections up to ~1.0.** The "structurally blind, guaranteed zero" hypothesis is dead. This
does **not** establish that per-language *recall* is equal; see Limits.

---

## Population — established before any rate was quoted

`data/raw/content_items_*.jsonl` on sadalsuud. `ObituaryPreprocessor.process_files` stamps
these **in place and drops nothing** (the enforcement drop happens later, in the dedup gate),
so this is *every loaded article*, not survivors. That distinction is the whole reason this
source was chosen over `data/filtered/*` — which is written under a passer guard and is
100% passers by construction.

| | |
|---|---|
| files | 90 |
| **window** | **2026-08-26 .. 2026-09-10** (16 distinct days — retention-bounded) |
| rows | 323,550 |
| carrying `_obituary_score` | **319,156 (98.64%)** — the other 4,394 are excluded |
| `_obituary_model` | `v5` on 100% of stamped rows |
| flagged `_is_obituary` | 3,994 (1.25% of stamped) |

## Result

| script | n | share | flag@0.85 | ≥0.5 | p50 | p90 | p99 | max |
|---|---|---|---|---|---|---|---|---|
| Latin | 294,491 | 92.27% | 1.252% | 1.94% | 0.0000 | 0.0027 | 0.9296 | **1.0000** |
| Greek | 7,585 | 2.38% | 2.123% | 3.69% | 0.0000 | 0.0233 | 0.9792 | **1.0000** |
| Arabic | 5,371 | 1.68% | 0.410% | 0.73% | 0.0000 | 0.0018 | 0.2736 | **1.0000** |
| Hangul | 3,866 | 1.21% | 0.621% | 1.24% | 0.0005 | 0.0311 | 0.6595 | **0.9996** |
| Cyrillic | 2,901 | 0.91% | 0.724% | 1.17% | 0.0000 | 0.0018 | 0.6107 | **0.9999** |
| Hebrew | 2,616 | 0.82% | 1.835% | 3.02% | 0.0000 | 0.0158 | 0.9734 | **0.9999** |
| Han | 1,573 | 0.49% | 1.208% | 1.97% | 0.0000 | 0.0079 | 0.9321 | **0.9998** |
| Devanagari | 303 | 0.09% | 1.320% | 1.32% | 0.0000 | 0.0014 | 0.9295 | **0.9992** |
| Kana | 256 | 0.08% | 3.125% | 5.08% | 0.0001 | 0.0206 | 0.9899 | **0.9997** |
| Armenian | 193 | 0.06% | 0.518% | 1.04% | 0.0000 | 0.0002 | 0.1832 | **0.9971** |
| Thai | 1 | — | — | — | — | — | — | — |

**Latin 1.252% vs non-Latin 1.249%, ratio 1.00x** (n = 294,491 vs 24,665).

## Why the `max` column is the load-bearing one

A flag *rate* confounds detector behaviour with the true obituary base rate, which plausibly
differs by region and source mix — so a low rate proves nothing on its own. The discriminator
that does **not** confound that way is the upper tail: **if the detector can see obituaries in
a script at all, some articles in that script must score high.** A script whose maximum over
thousands of articles stayed low would be blind rather than low-base-rate.

Every script reaches ~1.0. The instrument can say yes everywhere. That is the finding.

⚠️ Arabic (0.410%) and Hangul (0.621%) run 2–3x below Latin while still producing max ≈ 1.0 —
consistent with a genuinely lower obituary rate in those feeds, and equally consistent with
degraded recall. **This measurement cannot separate them.** If labelling money is ever spent on
this question, those two are where it should go.

## ⛔ Limits

- **This measures neither recall nor precision.** There are no labels. It measures *whether
  and how often the detector fires*, by script. A matched flag rate is consistent with matched
  recall and also with both arms being wrong in the same proportion.
- **16-day window**, retention-bounded. Print the window with any figure taken from here.
- **1.36% of rows carry no stamp** and are excluded; they are not assumed to be non-obituaries.
- **Dominant-script assignment** over the first 400 characters of title+content. Mixed-script
  articles land in one bucket; 0.73% of titles mix scripts (measured separately by ovr.news).
- Script is **detected from characters**, deliberately not read off the `language` field, which
  is known wrong on this corpus (a German ntv article carries `"language": "en"`).

## What this changes

The non-Latin corpus build — proposed as the next spend because it was the largest unmeasured
thing in the chain — **is deprioritised**. The urgency argument was that a live gate might be
structurally unable to fire on 40% of the stream. It fires at the same rate. Per-language recall
remains genuinely unmeasured, but it is now an ordinary open question rather than a suspected
live defect.

## Reproduce

```bash
scp scripts/*.py sadalsuud:~/
ssh sadalsuud 'python3 ~/obit_script_probe.py'   # population + stamp census first
ssh sadalsuud 'python3 ~/obit_by_script.py'      # the split
```

Read-only; no numpy on that host, so percentiles are computed on sorted lists. Siblings:
`2026-09-10-obituary-title-body-pooling` (which named this gap), and the window and
version-ordering studies of the same date.
