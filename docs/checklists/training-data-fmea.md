# Training data FMEA: run before every training run

**When:** after the splits are built, before `training/train.py` (RUNBOOK § *Prepare data*). Owner, 2026-10-07: "this
should be part of the runbook". Origin: the belonging retrain, where two of these were found only because the owner
asked (`docs/evidence/2026-10-07-belonging-adj1-build/README.md`).

**The rule:** every row names a check that RUNS, or an owner acceptance with a date for this build. A row with
neither is an open gap and is listed as one in the build's evidence README. Prose alone does not stop a recurrence
in this repo (`feedback-prose-promotion-does-not-fire`).

```bash
python training/validate_training_data.py --data-dir datasets/training/{name}_v{N} --filter filters/{name}/v{N} \
    --production-sample <uniform random draw of recent production rows, full text> \
    [--language-stamps <id -> language JSON from FluxusSource's collection archives>]
```

The production sample is part of the build, not an extra: draw it the way
`docs/evidence/2026-10-07-belonging-adj1-build/draw_easy_negatives.py` does (every row of the lens's
`data/filtered/<lens>/` files, no Google News, >= 300 chars, excluding every evaluation id).

S = severity for readers: 3 a wrong article reaches readers or a gate is fooled; 2 the student learns a bias;
1 noise.

| id | Failure mode | Effect | S | Seen in this project | Check | On detection |
|---|---|---|---|---|---|---|
| FM-T1 | Training text unlike production text (pre-enrichment snippets vs enriched articles; another fetcher) | The student learns length/style instead of the lens | 2 | belonging 2026-10-07 (v1 rows median 589 chars vs ~2,300 in production) | `data_quality.parity`: length quantiles train vs production, positive share per length bin (validator stats) | Read it. If the positive share rises with length while production is long, add production negatives |
| FM-T2 | Text cut at N chars when the model reads head+tail | Wrong verdicts on long articles | 3 | belonging 2026-10-07 (20/295 gate verdicts) | Builds keep full text and RAISE on a cut row without it (`build_adj1.text()`, `gate.scoring_text`) | Recover full text (live window, then monthly archives) |
| FM-T3 | Labels made on different text than the student trains on | Label noise | 1 | belonging 2026-10-07 (cut-text labels) | Known by construction | Owner accepts or relabels |
| FM-D1 | The same story in train and val/test | An inflated val metric picks the checkpoint | 2 | not measured before 2026-10-07 | `data_quality.cross_split_twins` (url, title, >= 20 distinctive shared 8-word runs): validator ISSUE | Drop the val/test copy |
| FM-D2 | Language / source mix differs from production | The lens works only for some languages or sources | 2 | human_thriving v8 non-Latin gap; belonging positives from 124 sources | `data_quality.mix`, using the collector's `language` stamp (FluxusSource, langdetect). Never improvise a detector | Read it; owner decides |
| FM-D3 | Site boilerplate in enriched text | The student keys on site furniture | 1 | 2026-10-07 (one site's footer matched 13 stories) | `data_quality.boilerplate` | Read it |
| FM-H1 | A held-out / gate story in training under another id | The gate is fooled | 3 | belonging 2026-10-07 (21 harvest twins) | Content-twin check against the evaluation set; the gate refuses on overlap via the package's `training_manifest.jsonl` | Drop, then refuse |
| FM-H2 | An excluded id (pilot, exemplar, test, calibration) in training | Leakage into an evaluation | 3 | 2026-10-02 (test rows paraphrased into prompt examples) | A per-filter exclusion module that RAISES (`belonging_exclusions.assert_disjoint`) | Raise |
| FM-L1 | A demoted / hard-negative row still labelled MEDIUM+ | Teaches the opposite of the ruling | 2 | not yet | Label wa with the filter's weights AND gatekeeper (`data_quality.label_wa`) < MEDIUM, in the build | Raise |
| FM-L2 | A positive labelled below the op-point | A positive that teaches "out" | 2 | 2026-10-03 | Same, >= MEDIUM | Raise |
| FM-L3 | Ragged or out-of-range labels | Silent training garbage | 2 | n/a | `validate_training_data.py` structural + range checks | Issue |
| FM-L4 | Oracle outputs mixing prompt/rubric versions | Labels from two definitions | 2 | 2026-10-02 | Refuse mixed prompt hashes when reading oracle output | Raise |
| FM-L5 | Cheap labels (k=1) on a label source | Some label noise | 1 | by design, belonging 2026-10-07 | Report how many came out positive | Owner accepts |
| FM-S1 | Labelling conditions differ between training positives and gate positives (judge batch density) | Narrower training positives, lower gate recall | 2 | belonging 2026-10-03 (hit 0.257 vs 0.38) | None yet | Open |
| FM-S2 | Google News rows sent to the oracle | Labels on teasers GN cannot enrich | 2 | yes | Draws exclude `news.google.com` | Exclude |
| FM-S3 | A source declared lost when an archive holds it | Decisions on missing data | 2 | 2026-10-07 (393 rows; 17th occurrence) | None mechanized: read `memory/nexusmind-data-sources.md` | Open |
| FM-P1 | Plumbing writes 0 rows and exits 0 | Training on nothing | 3 | 2026-09-01 (`prepare_data.py`) | Exact expected counts in the build; validator "No data found" | Raise |
| FM-G1 | A gate input the rule does not define (unscored row, copied order file, the old model's weights under a new name) | A forged PASS | 3 | belonging gate review 2026-10-07 | The gate's refusals (row validation, order check, fingerprint, model-path check), exit 2 | Refuse |
| FM-G2 | Run-to-run score noise near the threshold | Verdict flips | 2 | 2026-10-07 (order noise up to 0.453) | Score in two orders; read the flip count at the deciding thresholds | Both orders must pass |

**Not covered (say so in every build README):** topic drift between collection windows; enrichment quality per row
(a wrong page, a paywall stub); the language of rows older than the collector archives.
