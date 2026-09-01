# Phase B pre-flight — three things that would have wasted or stranded the run

**2026-09-01. Spend $0.0182** (25 calls, 0 errors). ⚠️ **Billed at PEAK**: the calls ran at
07:0x UTC on a Tuesday, inside the 06:00–10:00 UTC window. Off-peak would have been $0.0091.
The amount is trivial; the lesson is not — `memory/oracle-pricing-scheduling.md` names the
morning peak as *"the trap — it overlaps normal working hours, exactly when you'd kick off a
job at your desk"*, and that is precisely what happened. **The 6,590-row run must not start
before 10:00 UTC.**

No model trained, no threshold moved, nothing deployed.

## Why this exists

The owner asked for certainty before committing ≈$10.32, on the grounds that *"we already
labeled numerous times, then later you forgot stuff"*. Three defects were found that the
labelling run itself could not have surfaced, and all three are now fixed. A fourth — the
oracle vendor — is a decision, not a defect, and remains open.

---

## 1. The chain after labelling wrote **zero examples and exited 0**

`filters/human_thriving/v8/` held four markdown files and no `config.yaml`. Everything
downstream takes `--filter filters/{name}/v{N}` and reads that config, and the config's
`filter.name` is what selects the analysis field: `human_thriving` → `human_thriving_analysis`.

Label with `uplifting`'s config — which is what Phase A and every v8 experiment did — and the
next step does this:

```
$ python3 training/prepare_data.py --filter <v8 dir named human_thriving> \
      --input <labels carrying uplifting_analysis> --output-dir splits
Analysis field: uplifting_analysis
  Train: .../train.jsonl (0 examples)
TRAINING DATA PREPARATION COMPLETE
exit 0
```

⛔ **Zero examples, a success banner, exit 0.** `convert_to_training_format`'s own docstring
says why: *"Articles without analysis are silently skipped; missing dimensions default to
score 0."* The second clause is the worse one — a **renamed** dimension does not vanish, it
becomes a silent column of zeros on every row, which is a wrong label rather than a missing
one, and nothing downstream distinguishes them.

**Fixed** by writing `filters/human_thriving/v8/config.yaml` (labelling-time scope) and
proving the corrected chain end to end on 8 real corpus rows:

| | |
|---|---|
| scorer, real command shape | `field=human_thriving_analysis`, six dims correct, `filter_version: 8.0-deepseek`, `prompt_hash 003cd35a5122`, prefix cache exactly **10,368** tokens |
| `prepare_data.py --filter filters/human_thriving/v8` | **6 train / 2 test**, `labels: [6.0, 2.0, 7.0, 7.0, 3.0, 7.0]`, `all-zero? False` |
| control: same labels, config renamed to `uplifting` | **0 examples, "COMPLETE", exit 0** |
| the link that is easy to skip — the **aggregated** file, not raw scorer output, into `prepare_data.py` | **6 train / 2 test**, `labels: [5.0, 4.0, 6.0, 6.6667, 5.6667, 7.0]` (the thirds are the k=3 means), tiers 50/50 medium/low |

⚠️ That last row is checked separately on purpose: the aggregator adds keys the scorer never
writes (`runs`, `scope_verdicts_per_run`, `weighted_mean_all`), and `prepare_data.py` reads the
analysis object directly when it has no `dimensions` key. Verified both ways — by reading
`calculate_overall_score`, which iterates only `dimension_names`, and by running it. ⓘ Note in
passing that the tier metadata it stamps is an **unweighted** mean of the six dimensions, not
the weighted average; the script says tiers are "metadata only, not used in training", so this
is pre-existing and harmless, but do not read a tier out of a split file as a score.

⚠️ The config is deliberately **incomplete**. `hybrid_inference` and the normalization anchor
land at Phases C and E; the blocks that would otherwise be inherited unread — `prefilter`,
`content_type_caps` — are omitted **with the reason written where the block would have been**,
because a key that looks live and is dead is this repo's signature defect. The `oracle:` block
records the decision as **OPEN** rather than defaulting it.

⭐ **A weight change needs no re-labelling** (ADR-001): the oracle emits per-dimension scores
0–10 and the weighted average is computed downstream. So plan §9 Q4 (`social_cohesion_impact`
at 0.20) does **not** gate the spend. Dropping a dimension is likewise free. Only *adding* one
would force a re-score, and none is proposed.

---

## 2. The k=3 aggregation step deleted the evidence it was supposed to report

`scripts/oracle/average_oracle_runs.py`, verified against real run files:

| defect | proof |
|---|---|
| the RUNBOOK and `CLAUDE.md` document `--runs file1.jsonl …`; it takes **directories** | `ERROR: Run directory not found: …/nr_A1.jsonl`, **exit 1** |
| it **replaces** the analysis object with six averaged numbers | output sample is exactly six floats — `scope_verdict`, `dominant_subject`, `content_type` and every evidence quote gone |
| it joins on `url`, not the scorer's own `id` | two rows sharing a url merge |
| it keeps only rows present in every run, silently | log line, exit 0 |
| output filename hardcodes `v1` | `uplifting_v1_averaged.jsonl` |

The second is the one that matters: the RUNBOOK's own #135 instruction is *"before averaging,
check whether the prompt has a binary gate; if it does, report the flip RATE, not the mean"* —
and after this script runs, the flip rate is **unmeasurable**.

**Fixed** by `scripts/oracle/aggregate_k_runs.py`: joins on `id`, keeps every run, refuses
partial coverage, and writes **both** aggregates plus the per-run verdicts.

### ⭐ And the two aggregates are not close

Measured on 8 rows scored k=3 through the real path:

```
⚠️ SCOPE GATE FLIP RATE: 2/8 rows disagreed on scope_verdict across k=3
   |mean_all - mean_major| on the 2 affected rows: median 1.304  max 1.383
```

| id | verdicts | `weighted_mean_all` | `weighted_mean_major` |
|---|---|---|---|
| `global_news_UN_news_…` | in_scope / response_to_harm / in_scope | **3.667** | **5.050** |
| `west_african_premium_times_…` | harm_is_subject ×2 / in_scope | 1.850 | 0.625 |

⛔ **On the first row the aggregation choice decides which side of the 4.5 operating point the
label lands.** The old script made that choice silently, took the plain mean, and deleted the
verdicts that would have shown it. 1.30 points is ~3× the oracle decoder floor (0.436) and 8×
the #95 batch band (0.16).

⚠️ **The 25% is NOT a corpus flip rate** — see §3. And at n=8 its interval contains #135's
5.3% comfortably; it is quoted here to show the two aggregates *diverge*, not to estimate a
rate.

⭐ **The choice does not have to be made before the money is spent.** The tool keeps every
run, so `--aggregate all` (the default, and what Phase A measured) can be revisited from the
same files afterwards. What could not be revisited is the evidence the old script deleted.

---

## 3. ⛔ `head -N` of the corpus is the class-A supplement, not a sample

`corpus_v8_final.jsonl` is **grouped by design cell**, and the first **47** rows are exactly
`pos_clear|latin|classA` (18) + `pos_marginal|latin|classA` (29) — the 47-row class-A
supplement awaiting adjudication. Row 48 is `pos_clear|non_latin|-`.

The 8 rows used above are therefore **all class-A, all English, all Latin script** — the
harshest, most harm-adjacent stratum in the corpus and the one where the scope gate is most
contested by construction. Any "quick dry run on the first N rows" of this file measures that
stratum and looks like a sample. *(82 rows carry a `classA` cell in total; the other 35 sit in
ordinary strata and are **not** contiguous, so the grouping is partial.)*

⭐ **This makes the 2-of-8 flip observation interesting in its own right**, for the 47-row
adjudication rather than for the corpus: on the class-A supplement the gate is contested and
the aggregation rule moves labels across the op-point. It is 8 rows and should be re-measured
on all 47 at labelling time.

---

## 4. Gate B-A's inputs: 18 excerpts → 18 full articles

All 18 rows of `datasets/adverse/uplifting.jsonl` shipped as **300-character excerpts**
(`content_excerpt: true`) against originals of 620–28,905. `CLAUDE.md` already records this as
the 9th occurrence of *establish what a source excludes*, with *"a paid run against them was
one command away"* — and nothing on the scoring path stops it: `is_scrape_junk` floors at
**25** characters, and the 300-char oracle floor lives only in
`ground_truth.batch_scorer.make_oracle_prefilter`, which the DeepSeek path does not use.

⛔ **The premise that they were unrecoverable is wrong.** It appears in llm-distillery#127's
comment thread and in the 2026-08-30 rulings as *"their windows have rolled — unrecoverable"*.
The live `data/filtered/` window rolls at ~14 days; the rows are **archived monthly** in
`NexusMind/data/archived/nexusmind_YYYY-MM.tar.gz`, 9 tarballs reaching back to 2025-10.

```
recovered 18 of 18; still excerpts: 0
{"rows": 18, "rehydrated": 18, "still_excerpt": [], "rejected": 0}
```

**3 from the live window, 15 from `nexusmind_2026-08.tar.gz`.** Content characters
**5,449 → 100,460 (18.4×)**; every recovered length equals the row's recorded
`content_original_length` exactly; **9 of 9 class-A rows are now full text**; no other field
changed on any row.

⚠️ **NOT from the FluxusSource archive.** Those 1,593 tarballs hold **producer** bytes: three
rows whose enriched originals are 14,546 / 2,917 / 3,652 characters appear there at
**447 / 133 / 441**. The long text is NexusMind's enrichment, so NexusMind is the only source.
This is the same shape as the Die Presse candidate rejected on 2026-08-30 for having 149
characters of producer text behind 2,033 of enrichment.

⭐ **One row was rejected six times before the tool was right, and the rejection was correct
behaviour.** `north_african_tsa_algerie_…` matched on length (2,638) but failed a strict
`startswith`: excerpting had collapsed newlines to spaces (`"Canada. Cette"` against the live
row's `"Canada.\nCette"`), and that row is also the only excerpt that is not exactly 300
characters — it is 355. The prefix check is now whitespace-normalised **for the comparison
only**; the text written back is the source byte-for-byte, and the length check stays exact
because it is the constraint that catches a rewritten article reusing an id.

---

## What was checked and found sound

- **Corpus**: 6,590 rows, sha256 `5e2cf729…` matching `experiments/registry.jsonl`. 0 duplicate
  ids, **0 duplicate urls**, 0 empty; no `__provenance__` header row; **0 Google-News rows**;
  **min content exactly 300 characters** — the floor is baked into the corpus, which matters
  because the scoring path applies none; no pre-existing `*_analysis` field.
- The v8 prompt emits **exactly** v7's six dimension keys, so v7's dimension set is the right
  basis for the labelling config.
- `smart_compress` caps the oracle's view at **800 words**: **17.1% of the corpus (1,125 rows)**
  is truncated to head-560 + tail-240. Same as Phase A and cultural_discovery v5, so it is the
  established path — but this "long-form only" corpus is scored on a compressed view, and the
  student's own `max_length` is 512 with head/tail 256+256.
- **b650 cannot run Phase B**: `~/llm-distillery` there is not a git checkout — no `scripts/`,
  no v8 prompts, no `secrets.ini`. The run executes from the workstation. ⛔ **Not staged via
  `/tmp`, which is tmpfs (15 G, RAM)** — the defect fixed on 2026-08-30. `datasets/` is
  gitignored on a 466 G disk with 228 G free, and is the runbook's own convention.

## ⚠️ `$10.32` is a ceiling, not an estimate

H-V8-8 priced k=3 as 3 × a full pass, on the reasoning that *"a corpus pass scores 6,590
different articles every time"*. That is true of **one** pass. k=3 re-scores the **same**
articles, and whole-request caching is exactly what Phase A's cheap repeats were.

Measured here, unintentionally: the two no-regression rows scored on 2026-08-29 came back on
08-31 with `prompt_cache_hit_tokens` **11,904** and **12,160** against a 10,368-token prefix,
`miss` **56** and **20** — a whole-request cache that survived **two days**. Unmeasured is
whether 6,590 *distinct* prompts stay cached, which is a **capacity** question, not the TTL
question H-V8-8 answered.

⭐ **And caching does not defeat k=3**: three ~100%-cached runs of the Rappler row still
returned 5.25 / 4.65 / 5.40. Caching is on input tokens; the completion is resampled.

**Cheap check before committing:** run pass 1, then 50 rows of pass 2, and read the hit rate.

## Reproduce

```bash
# the corrected chain, end to end
PYTHONPATH=. python3 scripts/score_deepseek_production.py --input <rows> --output r1.jsonl \
  --config filters/human_thriving/v8/config.yaml \
  --prompt filters/human_thriving/v8/prompt-candidate-tail.md --concurrency 8
PYTHONPATH=. python3 scripts/oracle/aggregate_k_runs.py --runs r1.jsonl r2.jsonl r3.jsonl \
  --config filters/human_thriving/v8/config.yaml --out labels.jsonl
PYTHONPATH=. python3 training/prepare_data.py --filter filters/human_thriving/v8 \
  --input labels.jsonl --output-dir datasets/training/human_thriving_v8

# the rehydration (run ON the host that holds the archive)
python3 scripts/dataset/rehydrate_adverse.py --in datasets/adverse/uplifting.jsonl \
  --out uplifting_full.jsonl
```

Tests: `tests/unit/test_aggregate_k_runs.py` (10) and `tests/unit/test_rehydrate_adverse.py`
(8), **18 passing, 8 mutations all killed** — including "drop the partial-coverage refusal",
"majority mean silently uses all runs", "join on url instead of id", "never report a gate
flip", "drop the length check" and "drop the prefix check". The mutator asserts it mutated.
