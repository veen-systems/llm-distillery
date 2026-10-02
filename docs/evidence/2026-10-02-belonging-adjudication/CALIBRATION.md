# Belonging scope-oracle calibration: Gemini vs DeepSeek vs Claude (2026-10-02)

**The question.** Pilot v3 showed that lived belonging is ~2–4% of what the student passes, and that e5 retrieval
does not concentrate it. The training positives have to come from a cheaper reader, scanning many rows. **Can an
LLM oracle, given rubric v2, separate in from out the way the judges and the owner do?**

The owner chose this route (option A, with hard negatives alongside) on 2026-10-02 and asked for all three vendors to
be compared and every step documented.

## Step 1: the calibration set (`calibrate_scope_oracles.py build`)

**Contents:** every row judged under the APPROVED rubric v2 (`rubric_belonging_v2.md`), 242 rows in all.

| source | rows | label | label source |
|---|---|---|---|
| pilot v2 (`key_v2.jsonl`) | 100 | consensus of judge passes A and B | Claude Opus 5.5 subagents, blind (`judge_instructions_v2.md`) |
| pilot v3 (`key_v3.jsonl`) | 100 | the same | the same |
| `exemplars_v2.tsv` without B | 42 | 13 in, 29 out | Claude's reading against the owner's ruled lines |

**What it excludes:**
- **Pilot 1:** judged under the failed rubric v1.
- **The exemplar B rows.**
- **The pilots' 4 controls:** each is also an exemplar row, so each is kept once. The first build counted them twice
  (250 rows) and was rebuilt.

**Totals:** 220 out, 17 in, 5 split (one pass in, one out, reported apart).
- Only 4 of the 17 in-rows come from the pilots.
- 13 are exemplars, which Claude labelled, and which are exactly the rows the rubric's rulings were written about.
  ⚠️ **Recall on exemplars is easier than recall on unseen production rows.** It is reported separately as
  "pilots only".

**Text:** every oracle reads exactly the text the judges read: the same title, source and content.
- Pilot v3 rows carry content cut at 4,000 characters (`extract_corpus_v3.py`).
- Others carry full content (median 3,100 characters, max 17,727).
- `calib_key.jsonl` (committed) holds ids and labels. The text is in gitignored `datasets/belonging_adjudication/calib/`.

## Step 2: the prompt (`oracle_scope_prompt.md`)

**Identical for all three oracles:**
1. a short task header
2. **`rubric_belonging_v2.md` verbatim**
3. the verdict list and the "remove the relationship" rule, as in the judge instructions
4. a JSON answer shape
5. the article

The prompt carries **no examples beyond the rubric's own wording**, which is the v2 test-set leakage lesson.
⚠️ The rubric names ruled shapes generically (a seniors' club, a family craft). Two of those shapes are exemplars in
the set.

## Step 3: the calls (`calibrate_scope_oracles.py run --oracle X`)

| oracle | model requested → served | settings | JSON |
|---|---|---|---|
| Gemini | `gemini-2.5-flash` → `gemini-2.5-flash` | temperature 0, thinking budget 0 (as `batch_scorer` runs it), max 1,024 out | `response_mime_type=application/json` |
| DeepSeek | `deepseek-chat` (the alias) → **`deepseek-flash`** | temperature 0, max 1,024 out; called off-peak, Fri 2026-10-02 ~17:55 UTC | `response_format=json_object` |
| Claude | `claude-opus-5-5` | effort `low` (thinking cannot be disabled on Opus 5.5; there is no temperature parameter), max 4,000 out | `output_config.format` json_schema with the verdict enum |

**Common to all three:**
- 8 parallel workers.
- Each row's verdict, quote, reason, served model, token usage and latency are recorded.
- A reply that is not a valid verdict is recorded as an error, never guessed. A rerun retries only the errors.

**The model is the defaults' choice, not a tuned one.** Claude Opus 5.5 is the claude-api skill's default, and the
owner asked for "Claude" without naming a model.

⚠️ **The judges that produced the labels are also Claude Opus 5.5**, reading the same rubric. Claude's agreement with
the labels is therefore inflated by shared bias. Only the owner's spot-checks are independent.

## Step 4: results (`calibrate_scope_oracles.py analyse`)

Smoke test first: 2 rows per oracle, all valid. Then full runs. Gemini and DeepSeek: 242/242 judged, 0 errors.

| oracle | specificity (220 out) | recall (17 in) | recall, pilots only (4 in) | the 5 split rows: says in | tokens in / out | cost, 242 rows |
|---|---|---|---|---|---|---|
| Gemini 2.5 Flash | **0.950** [0.913, 0.972] | **0.882** [0.657, 0.967] | 4/4 | 5/5 | 574,241 / 25,869 | $0.237 |
| DeepSeek (`deepseek-flash`) | **0.986** [0.961, 0.995] | **0.529** [0.310, 0.738] | 2/4 | 2/5 | 566,465 / 18,793 | $0.096 |
| Claude Opus 5.5 | *pending: no Anthropic API credential on this machine* | | | | | |

**The intervals** are Wilson 95%.

**The costs** are list price × the token counts each API returned:
- Gemini realtime: $0.30 / $2.50 per M tokens.
- DeepSeek V4.1 Flash off-peak: $0.15 / $0.60, cache-miss, with 0 cache hits recorded.
- Per 1,000 articles **on THIS prompt** (rubric v2 + article): Gemini $0.98, DeepSeek $0.40.
- ⏳ **Billing confirmation pending.**

**Gemini and DeepSeek agree on the binary call for 225 of 242 rows.**

**Errors:**

| | Gemini | DeepSeek |
|---|---|---|
| false in | 11 | 3 |
| missed in | 2 | 8 |

- **2 false ins are shared by both:** a BBC NI row and a Spinoff row.
- **1 false in is an exemplar shared by both:** the young ag networking group, which the rubric puts out as
  professional networking.
- **The 2 misses shared by both are both exemplars:** the hospital clean-up and the kauri planting.

**Reading** (Claude's; the Claude oracle is not in yet):
- **DeepSeek is the stricter reader.** It is near the judges on specificity and misses about half the positives.
- **Gemini is the better screen.** It catches ~88% of positives, and at a 2–4% base rate ~5% of rows are false ins.
  A Gemini screen would therefore send ~7–9% of rows to the Claude judges, a ~10× enrichment over random.
  This is an estimate from these rates, not measured on production.
- **Small n:** n=17 in-rows, 13 of them exemplars. The recall intervals are wide.
