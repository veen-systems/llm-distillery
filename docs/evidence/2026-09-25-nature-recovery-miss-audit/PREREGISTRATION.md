# Nature recovery miss audit — pre-registered BEFORE the sample is drawn or any article judged

**2026-09-25.** Owner: *"sometimes i see things on other lenses that could be nature recovery"*; approved
this audit. Design is the **assistant's proposal**. It is a MEASUREMENT, not a gate: nothing ships from it.

## Question
Of the articles another lens publishes, how many are Nature recovery stories that `nature_recovery v4`
misses, and **where do they leak**: the e5 probe (screened out before the model), the model (scored
low), or the cut-off (scored just under 3.75)?

## Population: computed by the pipeline, not chosen by hand
Same 42-cycle week as the Thriving audits (`filtered_20260918_145649` → `filtered_20260925_093350`).
Every article that passed ≥ 1 of uplifting (4.5), human_thriving (4.5), cultural_discovery (4.0),
belonging (4.0) or solutions (2.25) at stage 2, joined to its nature_recovery row. Counted
2026-09-25 before this was written: 16,795 such articles. Strata (N recounted by `build_sample.py`):

| stratum | what nature_recovery did | ~N | drawn |
|---|---|---|---|
| `nr_passes` | passed (raw ≥ 3.75); a precision control | 161 | 30 |
| `near_3.0_3.75` | model scored just under the cut-off | 62 | all |
| `low_2.0_3.0` | model scored low | 217 | 50 |
| `very_low_lt2` | model scored very low | 14,770 | 60 |
| `probe_screened` | e5 probe screened it out; the model never saw it | 1,585 | 100 |

Seed 20260928. Blind batches of 56, shuffled; the judge sees title, url, source and text only.

## Judge
Claude subagents, each in its own `/tmp/judge_*` directory, under `rubric_scope_nr-v4.md` (nature_recovery
v4's own STEP 1 scope check and §4 pre-classification, verbatim). Verdicts: `in_scope`, `out_of_scope`,
`cannot_judge` (text too short or broken; counted separately, left out of rates). No owner rulings exist for
this lens; the prompt's own rules apply (delivered protection IN, pledges OUT, conservation appeals without
outcomes OUT, single-animal events OUT).

**Stops, as in the Thriving audits:** 4 known-answer controls from nature_recovery v4's own held-out test
split (IN: `spanish_la_vanguardia_28c048d44378` lynx doubles, oracle 7.78; `east_african_new_times_rw_07ce2bcd52b6`
Akagera poaching ended, 7.60. OUT: `community_social_hacker_news_6e92bdd16207` Iran drying up, 0.4;
`semantic_scholar_d6a6f7990cb9` energy-efficiency technologies, 0.0) → **4/4 or STOP**. Pass B on a seeded
30% → **A-vs-B agreement ≥ 0.90 or the run is not used**; an A/B split counts as NOT in scope.
**Owner check:** 20 drawn at random, shown as translated text; ≥ 18/20 or the result is withheld until ruled.

## Reported
Per stratum: in-scope rate (Wilson 95%) and estimated misses per week = N_s × rate, with a bootstrap CI.
The leak split: probe vs model vs cut-off. `nr_passes` gives nr's precision on this population.

## Predicted before looking (so a surprise is visible as one)
`nr_passes` 60–85% in scope; `near_3.0_3.75` 30–60%; `low_2.0_3.0` 10–30%; `probe_screened` 2–10%;
`very_low_lt2` < 2%. Guesses from the prompt's narrow scope and the probe's recall-first design; if a
measured rate lands far outside its range, the instrument is checked before the finding is believed.

## Limits
Only articles OTHER lenses published: this measures misses readers could have seen elsewhere, not every
nature story in the feed. One week. Claude judge, no owner-validated pilot for this lens.
