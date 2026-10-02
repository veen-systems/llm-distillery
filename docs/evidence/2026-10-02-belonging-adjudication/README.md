# Belonging adjudication (2026-10-02): rubrics, three pilots, and the scope-oracle calibration

> ⛔ **REVIEW CORRECTIONS (2026-10-02 close): read § *Review corrections* at the end BEFORE quoting anything below.**
> - Pilot v2's owner check did NOT meet its bar (7/10 against ≥ 9/10).
> - Pilot v3's bar was NOT met: item 2 was not evaluated and item 3 never ran.
> - "~2–4% of passers" is superseded.
> - "No lift" is scoped.
>
> **The calibration is in [`CALIBRATION.md`](CALIBRATION.md).**

`docs/TODO.md` ▶ START HERE item 0, phase 1 (the human_thriving v9 recipe applied to belonging).

**Owner checkpoint, 2026-10-02: done.** The owner ruled the three open boundaries (Q1–Q3 in `rubric_belonging.md`),
choosing Claude's proposal each time:
- Q1, festivals: they count only when the people carry them.
- Q2, marches: the doing test wins for training, and Morwell stays P in the test set.
- Q3, programmes: they count when the participants build something.

The owner ruled the LINES. The per-row verdicts in `exemplars.tsv` are Claude's readings against those lines, and
the owner has not checked them row by row. Phase 2's owner spot-check is the row-level check.

**Cost:** $0. No oracle, no GPU. Reads were read-only on sadalsuud `data/filtered/belonging/`.

## Files

| file | what |
|---|---|
| `rubric_belonging.md` | the judges' rubric: the owner's rulings, one `out_*` verdict per junk class, and Q1–Q3 (ruled 2026-10-02) |
| `exemplars.tsv` | 51 exemplars: ids, titles, Claude's verdict and reason. No bodies (public-repo rule) |
| `build_exemplars.py` | writes `exemplars.tsv` and the gitignored `datasets/belonging_adjudication/exemplars_full.jsonl` (full text for the judges) |
| `fetch_exemplar_rows.py` | the sadalsuud fetch: reader-sample ids and curator-pick urls against every retained belonging file |
| `PREREGISTRATION.md`, `judge_instructions.md` | phase 2 pilot design and bar, written before any judging |
| `draw_pilot.py`, `build_pilot_inputs.py`, `key.jsonl` | the pilot sample (b650), the four blind judge inputs (gitignored), the key |
| `analyse_pilot.py`, `pilot_result.txt` | bar items 1, 2, 4 and the owner spot-check list |
| `rubric_belonging_v2.md` (now **v2.1**), `rubric_belonging_v2_0.md` (v2.0 verbatim; what pilots v2/v3 and calibration Step 4 ran on) | the research-grounded rubric |
| `exemplars_v2.tsv`, `build_exemplars_v2.py`, `dev_check_v2.tsv` | v2 exemplars (13 P / 9 B / 29 out) and the dev check |
| `PREREGISTRATION_v2.md`, `draw_pilot_v2.py`, `draw_prod_v2.py`, `build_pilot_inputs_v2.py`, `judge_instructions_v2.md`, `key_v2.jsonl`, `analyse_pilot_v2.py`, `pilot_v2_result.txt`, `spot_check_v2_*.tsv` | pilot v2 |
| `PREREGISTRATION_v3.md`, `extract_corpus_v3.py`, `retrieve_v3.py`, `draw_pilot_v3.py`, `build_pilot_inputs_v3.py`, `key_v3.jsonl`, `analyse_pilot_v3.py`, `pilot_v3_result.txt` | pilot v3 (enriched by e5 retrieval) |
| `CALIBRATION.md`, `calibrate_scope_oracles.py`, `oracle_scope_prompt.md`, `calib_key.jsonl`, `calibration_result.txt`, `calibration_v2_1_gemini.txt` | the three-way scope-oracle calibration |
| `curator_lens_match.py` | which lens the external curator's picks pass |

## Where the exemplars come from

- **Population:** two sets, both from `docs/evidence/2026-10-02-belonging-reader-snapshot/`:
  - the 200-row reader sample (198 found in the retained files)
  - the external curator's picks that reached belonging scoring (all 46 found, one under its reader-sample id; urls local-only in
    `datasets/external_curator/`)
- **Candidates read:** 83. These were 67 of the reader sample's 68 `fits` and `borderline` rows (one was not found)
  plus 16 curator picks that score ≥ 4.0. The 17th pick is also in the reader sample, so it was fetched under its
  reader id; it is in the reader sample's junk classes (cash aid from an NGO). Claude read the title and the first ~650 characters of each, a few further.
- **Adverse rows:** picked from the reader sample's junk classes by title and opening, 3 per class (4 for gifts).

| code | n | meaning |
|---|---|---|
| `P` | 6 | clear `in_scope` under the rulings as they stand |
| `B` | 6 | borderline: kept for the record, never a teaching example |
| `Q1` / `Q2` / `Q3` | 7 / 4 / 8 | illustrate a ruled boundary; the verdict is Claude's reading of the ruling |
| `out_*` | 20 | 2–5 per junk class |

**Review corrections (2026-10-02, same day):** the first draft had 14 `P` rows, and an adversarial review found
that 8 of them contradict the rubric or teach badly when read in full.
- Six moved to `B`: Kalumburu, Wayuu, the Nepal column, the Himalayan trails, the debate teaser and the mending event.
- The tutoring row moved to `Q3 out_other`: a non-profit programme, with the communes paying the tutors.
- The Gaza seed bank moved to `out_one_person`: one founder and his daughter.
- The horse race moved to `Q1 out_event_crowd`.
- Orange Shirt Day moved to `out_gift_official`: a government-sponsored commemoration.
- The Hebron farmer moved to `out_one_person`.

Six clear positives is thin. The pilot below says why: clear positives are rare in this corpus.

**Measured:** the counts and the fetch. **Claude's read:** every verdict and reason. The owner ruled the Q1–Q3 lines,
not the rows.

## What the "doing" test moved

The reader snapshot's verdicts predate the "doing" test. Re-read against it:
- Two of Claude's snapshot `fits` now read as adverse exemplars: the restored-mosque reopening (`out_gift_official`)
  and the charity run (`out_event_crowd`).
- Several more moved into Q1/Q2 (festivals, remembrance marches).

The snapshot's 16% `fits` share is therefore an upper bound under the current rules. It was not recounted.

## Guards and exclusions

- **No overlap with the v2 test set.** Three candidates were in it (Morwell, the Indigenous food summit, the convict
  ancestry essay) and were left out.
  - `build_exemplars.py` raises on an id or normalised-url overlap, and on a test row without an id.
  - The normaliser keeps the query string, because one site addresses articles by `?p=<id>`. The first version
    dropped it and flagged a false overlap.
- ⚠️ **The exclusion is enforced only against the v2 test set.** Phase 3 draws from v1 rows, which predate every
  exemplar. The phase-4 harvest builder must load `exemplars.tsv` and raise on any overlap.
- **Mutation checks, 2026-10-02:** dropping one fetched row exits 1; swapping in a test-set id exits 1. A re-run
  reproduces `exemplars.tsv` byte for byte.
- ⛔ **Exemplar ids stay out of every training draw and every evaluation set** (the v2 leakage lesson).
- **Phase 6/7 is unaffected.** The curator picks used here are not training rows, so the planned check of where the
  curator's stories score stays a measurement of the student. The judges, though, have seen them.

## Also done in this step

`build_test_set.py` was re-run from the existing full rows (`datasets/belonging_v2_test/test_set_full.jsonl`, labels
stripped). Exactly the three ruled labels changed, and the content is byte-identical. The test set is now 23 P / 68 F /
28 B, with Robinvale F → P, Morwell B → P and Charleville F → B.

## Rebuild

```bash
# want_ids.txt = reader_sample_200.tsv column 3; want_urls.txt = curator_match.tsv rows found (local only)
scp fetch_exemplar_rows.py want_ids.txt want_urls.txt sadalsuud:/tmp/
ssh sadalsuud 'python3 /tmp/fetch_exemplar_rows.py > /tmp/ex_rows.jsonl'   # ~1 min
scp sadalsuud:/tmp/ex_rows.jsonl /tmp/ && python3 build_exemplars.py /tmp/ex_rows.jsonl
```
⚠️ The files rotate (the window opens 2026-09-03), so the fetch fails once the oldest exemplar rotates out. Keep
`datasets/belonging_adjudication/exemplars_full.jsonl`.

## Notes for later phases

- **Morwell scores as a recall miss by design.** It stays P in the v2 test set (ruling (c)), but the training rubric
  puts remembrance alone out (Q2). A phase-6 report on the test set must say so beside the recall figure.
- **Ruling 1's "a community day" vs the doing test.** *(Claude's reconciliation; the owner has not checked it.)* A
  community day that builds or cleans something counts. One held only to celebrate does not.

## Phase 2 pilot result (2026-10-02)

Pre-registered in `PREREGISTRATION.md` before any judging. The output is `pilot_result.txt`. **Cost:** $0, with four
Claude subagents of ~80–100k tokens each.

| bar item | result |
|---|---|
| 1. known-answer controls | **4/4 on both passes** |
| 2. self-consistency A vs B (n=96) | **1.000 binary agreement, κ 1.000** (bar 0.90 / 0.75). Exact 8-class agreement is 90/96 |
| 3. owner spot-check | **FAIL: 3/10** (bar ≥ 9/10). All 10 were rows the judges put out. The owner said out on 3, in on 6 and unsure on 1 (`spot_check_owner.tsv`) |
| 4. presence | consensus disagrees with the oracle on 62 of 96 |

**Per stratum (consensus `in_scope`; not pooled, because of design weighting):**
- **`near`** [3.5, 4.0): **0/30**, against a prediction of 5–20%.
- **`above`** ≥ 4.0: **4/66**, against a prediction of 15–35%.
  - The out classes: one person 27, other 12, harm 6, gift/official 5, event 5, culture 5, cannot_judge 2.

⚠️ **Below the predicted range, so Claude read all 66 `above` rows' titles and reasons before believing it.**
- The verdicts read as right: v1's positives are mostly single-person viral and feel-good stories, such as a baby's
  hair, a CPR rescue, celebrity tributes and gardening how-tos.
- The prediction rested on a title-only read under a looser ruling, before the doing test and Q1–Q3.
- **One pattern for the owner to test:** a volunteer initiative told through its founder. The judges put it out
  every time but one (`out_one_person`: the lake man, the pet food bank, a founder's initiative).
- ⚠️ **Same-source caveat:** the predictor, the judges and this read are all Claude.

**What it means if item 3 passes:** of v1's 783 positives, roughly 6% (~45 rows, a per-stratum extrapolation with a
wide interval at n=66) survive as `in_scope`. The retrain's positives would then come mostly from the phase-4
production harvest, not from v1.

**Judge plumbing:**
- 8 quotes are not verbatim in `content`. Most are the article's title, which judges see as a separate field.
- One judge reported that another judge overwrote its temporary script in the shared scratchpad. It then fixed its
  `out.jsonl` by hand. The analyser checks that ids are in input order and that the verdict set is valid, and both
  passed.
- For the full run, give each judge its own scratch directory.

### Item 3 failed (owner, 2026-10-02): the rubric is stricter than the owner

**How the owner judged:** blind to the judges and the oracle, in session. Claude described each row in one or two
sentences, with the relevant ruling beside it. The owner did not read the full text.

| row | the story | owner |
|---|---|---|
| 1 | biography of the founder of Indian women's cricket | unsure |
| 2 | a teen rescues his elderly neighbours from a fire | in |
| 3 | a refugee organisation's children's festival, ~60 children | in |
| 4 | the Munduruku protest, and the government's promise to consult | out |
| 5 | a survey of disabled children at playgrounds | out |
| 6 | a job vacancy | out |
| 7 | the "Lake Man": a founder-led volunteer movement restoring 275 lakes | in |
| 8 | an 85-year-old sings at senior-home karaoke | in |
| 9 | 20,000 carers receive a national ribbon, nominated by neighbours and family | in |
| 10 | youth protesters oust Peru's president | in |

**What this means.** Per `PREREGISTRATION.md`, the rubric or the instructions get fixed, and the pilot re-runs on a
fresh sample. Several of the owner's in-calls sit against the rubric's classes:
- one person (2, 8)
- an event attended (3)
- an award campaign (9)
- a protest (10)

**Who decided what:**
- The owner ruled the middle definition, the doing test and Q1–Q3.
- `out_one_person` as a class, and "protest for demands is out", were Claude's labels. The owner never ruled on them.
- The owner's in-calls are the evidence of where the line sits.

### After item 3: the definition is reopened (owner, 2026-10-02)

- **The owner's picks for the new line:** community events, recognising carers and helpers, and protests that achieve
  a result.
- **One person helping others: split it** (ruled). An ongoing relationship of care or contribution counts. A one-off
  heroic act or a viral kindness does not.
- **The owner's question: "are we changing our dimensions too much?"**
  - *(Claude's read of the files.)* Yes. The doing test comes from ovr.news `docs/BRAND.md:84`, where it targets one
    narrow case: belonging whose occasion is a harm. That passage marks it "Undecided".
  - Applied to all of Belonging, it excludes what `intergenerational_bonds`, `rootedness` and `slow_presence` reward,
    which is 0.50 of v1's weight.
  - v1's prompt (STEP 1) defines lived belonging, and that definition covers the owner's in-calls.
- **Not decided:** which definition the rewritten rubric starts from. The owner chose to talk it through first.
- **Do not run phase 3 on `rubric_belonging.md`** as written.

### Which lens do the curator's picks belong to? (measured 2026-10-02)

**Method:** `curator_lens_match.py`, run on sadalsuud against every retained `data/filtered/<lens>/` file. The window
is 09-03 → 10-02; human_thriving's files start 09-07. A pick passes a lens when its row is `stage2` with raw ≥ the
lens's `normalization.json` `raw_min`:

| lens | `raw_min` |
|---|---|
| belonging | 4.0 |
| human_thriving | 4.5 |
| solutions | 2.25 |
| cultural_discovery | 4.0006 |
| nature_recovery | 3.75 |
| uplifting | 4.5 |

The per-pick table is local-only, in `datasets/external_curator/curator_by_lens.json`.

**Coverage:** all 46 picks that reach scoring are scored by every lens (36 for human_thriving, because of its
shorter window). Some rows are `stage1_low`: 4 each for cd, nr and solutions. They count as not passing.

| lens | picks passed |
|---|---|
| uplifting (still scored while it drains) | 38 / 45 |
| solutions | 32 / 45 |
| belonging | 17 / 46 |
| human_thriving | 14 / 36 |
| cultural_discovery | 8 / 46 |
| nature_recovery | 2 / 46 |
| no lens | 4 |

**Reading** (Claude's, discussed with the owner and agreed):
- The curator is a generalist constructive-news feed. Its nearest ovr analogue is the retired generalist lens, then
  solutions. No single lens matches it.
- Most of its belonging-passers also pass 3–4 other lenses: sailing, the 911 teams, NGO cash, vertical farming.
  Chasing them would pull Belonging toward solutions. That is how the doing test got overextended.
- **Owner decision (2026-10-02):** the curator is no longer Belonging's yardstick. It remains a question for ovr's
  selection across lenses, which is EXP-025's original question, and that question belongs to ovr.news.
- Belonging is replanned around a research-grounded definition: Baumeister & Leary 1995; McMillan & Chavis 1986.

**Caveats:**
- 46 picks over one month, matched on url.
- About half of the curator's in-window stories never reached our scoring.
- The pass counts are student scores, not oracle labels.

## Phase 1R and 2R: rubric v2 and the second pilot (2026-10-02, evening)

The plan was revised with owner approval; it is local at `~/.claude/plans/splendid-purring-acorn.md`.

**Rubric:** `rubric_belonging_v2.md`, approved by the owner. It rests on Baumeister & Leary 1995 and McMillan & Chavis
1986, both checked on 2026-10-02, plus v1's STEP 1 and the owner's rulings.

**Rulings made at the dev check** (`dev_check_v2.tsv`, against the first pilot's 10 rows):
- Protests count only when the article is about the community the movement built.
- A founder-told movement counts only when the volunteers and their bonds are shown.
- A portrait of one person at a shared event is out.
- Social clubs whose members keep meeting are in.
- One family passing a craft down the generations is in.

**Exemplars:** `exemplars_v2.tsv` has 13 P, 9 B and 29 out. ⚠️ The P rows cover collective action and place well,
but intergenerational ties, care and slow presence barely appear among the candidates.

**Pilot v2** (`PREREGISTRATION_v2.md`, `pilot_v2_result.txt`). Cost: $0, four subagents of ~95–112k tokens each.

| bar item | result |
|---|---|
| 1. controls | **4/4 in both passes**, including both newly ruled IN shapes |
| 2. A vs B | binary agreement **0.990**, κ **0.662**: **FAIL** (bar 0.75) |
| 3. owner spot-check | **7 agree, 0 disagree, 3 unsure** (`spot_check_v2_owner.tsv`). Under the ≥ 9/10 bar: **not met** |
| 4. presence | 68 of 99 consensus rows disagree with the oracle |

**Consensus `in_scope` rate per stratum:**

| stratum | in scope | predicted |
|---|---|---|
| v1 near | 0/30 | 5–25% |
| v1 above | 1/39 | 15–35% |
| production passers | **0/30** | 25–50% |

**Reading** (Claude's read, after reading all 70 above/prod rows):
- **The line is aligned.** The owner disagreed with the judges on 0 rows, against 6 in the first pilot.
- **The three unsure rows are boundaries, not errors:**
  - neighbours in a flooded street
  - a lone artisan's festival craft
  - a single mothers' workshop programme
- **Item 2 fails on prevalence, not on disagreement.** The passes differ on 1 row of 100. With ~2 in-scope rows in the
  sample, one disagreement caps κ near 0.66. **The bar was unreachable at this rarity** and was not checked before it
  was set (`feedback-prove-the-bar-is-reachable`). It is reported as FAIL and not re-scored.
- **The in-scope side is untested.** Only 1 consensus-`in_scope` row existed outside the controls.
- **Random samples contain almost no lived belonging.**
  - The production prediction came from the reader sample, whose rows had all won the top-50 cap (raw ≥ 5.6).
    A random passer sits much lower.
  - The judges' out verdicts on production read as right: a fashion show, a council report, protests, road spending.
- **The consequence for the plan:** phase 4's random harvest would yield almost no positives. Positives have to be
  RETRIEVED, using `scripts/screening/embedding_screener.py` (ADR-011, e5-small seeds) with the P exemplars as seeds.
  The pilot also needs an enriched stratum before κ and the in-scope side can be tested.

## Pilot v3, the enriched pilot (2026-10-02, late evening)

Pre-registered in `PREREGISTRATION_v3.md`; output `pilot_v3_result.txt`.
- **Retrieval:** `extract_corpus_v3.py` and `retrieve_v3.py` (e5-small, nearest-seed) over 344,855 distinct
  production stage2 rows. The seeds were the 13 P exemplars plus 5 pilot consensus-in rows.
- **Cost:** $0 API. GPU: ~4.5 minutes of embedding on the b650 RTX 5090. Four subagents of ~115k tokens each.

| bar item | result |
|---|---|
| 1. controls | 4/4 in both passes |
| 2. A vs B | agreement 0.960; κ 0.579 NOT judged (only 3 consensus in-scope rows, below the pre-registered 10): PASS as pre-registered |
| 3. owner spot-check | only 8 rows were available (3 consensus in, 5 out); not yet run |
| 4. presence | 73 of 96 rows disagree with the student |

**Consensus `in_scope` per stratum:**

| stratum | in scope | pool | predicted |
|---|---|---|---|
| `retrieved_hi` | **2/48** | 752 | 25–50% |
| `retrieved_lo` | **0/20** | 1,248 | 0–15% |
| `random_pass` | **1/28** | 13,024 | 0–10% |

**Retrieval gives no measurable lift** (2/48 against 1/28; the intervals overlap completely).

**Every row any judge called in (7):**
- **Both passes in (3):**
  - grandparents in a joint family teaching a 4-year-old
  - lifelong neighbourhood friends meeting around a table
  - a Greek village celebrating a birth
- **Split (4):**
  - a youth association cleaning its health centre
  - the Boti community keeping its forest
  - a Turkish village that rejects smoking
  - a Montana tribe welcoming children's remains home from Carlisle

**Reading** (Claude's):
- **The pilot shows rarity, not a judge defect.**
  - The judges' out verdicts on the retrieved rows read as right: official ribbon-cuttings, grants, NGO founders,
    research, harm.
  - The owner agreed with this judge setup 7/0/3 in pilot v2.
- **Claude's title-based predictions have now been too high three times running** (15–35%, 25–50%, 25–50%). Titles
  overstate belonging. Only full-text judging measures it.
- **The in-scope boundary is where the judges diverge:** 4 of 7 in-calls split. The out side is stable.
- **Lived belonging, as the owner ruled it, is ~2–4% of what the student passes.** The point estimates are 1/28 and
  2/48; the intervals are wide.
  - That is roughly 10–20 articles a day out of ~500 passers. This is a guess built on n=76.
- **The training problem:** positives cannot be found by e5 similarity, and sampling yields ~3 per 100 judged.
  Hundreds of positives would need thousands of full-text judgements.

## Review corrections (2026-10-02, session close)

Three reviewers ran: claims-vs-files, adversarial methodology, and code correctness. Their findings were verified
by recomputation. These corrections supersede the sections above.

1. **Pilot v2's item 3 is a FAIL.**
   - The owner agreed on 7 of 10, against a bar of ≥ 9/10; under pilot v3's own rule, "unsure" counts as not
     agreeing.
   - "0 disagreements" is true. "**The line is aligned**" overstated it; read it as "no disagreement, bar not met".
2. **Pilot v3's bar is NOT met.**
   - Item 2 is **NOT EVALUATED**, not PASS. Its "below 10 consensus-in" exemption was added after v2's κ failure,
     and its reachability check assumed a 25% prevalence, which was Claude's overshooting prediction.
     `analyse_pilot_v3.py` now prints NOT EVALUATED and exits 1; `pilot_v3_result.txt` was regenerated.
   - Item 3 (the owner check) never ran.
3. **"Lived belonging is ~2–4% of passers" is superseded.** The supportable statement is a judge-relative rate under
   rubric **v2.0**.
   - **Measured:** random passers **1/58 = 1.7% [0.3%, 9.1%]**, pooling pilot v2's `prod` (0/30) and pilot v3's
     `random_pass` (1/28).
   - **The population excludes** off-lens sources, Google News, rows under 300 characters, and the reader, pilot
     and test ids.
   - **2/48 is the retrieved stratum's rate,** not a rate among passers.
   - **v2.1 widened the line,** so the rate under v2.1 is unmeasured.
   - "~500 passers a day" comes from the reader snapshot (`../2026-10-02-belonging-reader-snapshot/README.md`).
4. **The retrieval claim, scoped:** the retrieved rate's 95% upper bound is **~14%**. That refutes the 25–50%
   prediction. It does NOT exclude a 3–4× lift: one method and one seed set were tested, and the seeds were mostly
   exemplars.
5. **"Not a judge defect"** (the reading after pilot v3) is contradicted by the calibration, which found a wrong
   judge label: the DIY classes, overridden by the owner.
6. **Exclusions for every future draw** (phase 3/4 builders must RAISE on overlap, not only on exemplars):
   - `key.jsonl`, `key_v2.jsonl` and `key_v3.jsonl` (all three pilots)
   - `calib_key.jsonl`
   - both exemplar lists
   - the v2 test set, the 150-row held-out sample, the 49 probe rows, and the 200-row reader sample
7. **Field-name caveat:**
   - `key_v3.jsonl`'s `oracle_in` holds the STUDENT's raw ≥ 4.0, not an oracle verdict.
   - `key_v2.jsonl` dropped the v1 `split` column, so the count of pilot rows from v1's test split must be recovered
     from the b650 splits before the phase-6 gate.
8. **Truncation:** pilot v3's judges and the calibration oracles read content cut at 4,000 characters. A production
   oracle sees the full text.
