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
| Claude | `claude-opus-5-5`, **run as Claude Code subagents** (see below) | the session's model and settings | the subagent writes JSON lines |

**Common to all three:**
- 8 parallel workers.
- Each row's verdict, quote, reason, served model, token usage and latency are recorded.
- A reply that is not a valid verdict is recorded as an error, never guessed. A rerun retries only the errors.

**How Claude was run.** This machine has no Anthropic API key: `secrets.ini` is empty and `ant` is not installed.
The owner ruled "run it as a subagent", so `calibrate_scope_oracles.py` keeps an API path (`call()`) that has never
run.
- **Instead:** the 242 rows were shuffled (seed 31) and split into 5 blind batches, `calib/claude_subagent/C1..C5`
  (48–49 rows each).
- **Opaque ids:** each row's calibration id was replaced by an opaque hash, so a subagent cannot tell an exemplar from
  a pilot row. `id_map.json` maps them back.
- **The instruction:** each subagent was told to behave exactly as if it had received `oracle_scope_prompt.md` with
  the rubric and that article filled in, and to read no other repository file.
- **Import:** `calibrate_scope_oracles.py import-subagents` checks ids and order, then writes `claude.jsonl`.
- ⚠️ **Not identical to the API oracles:** a subagent reads all ~49 articles in one context, while the API oracles
  saw one article per call. It also ran at the session's settings, not at effort `low`.
- **Cost:** 534,506 subagent tokens in total (104,871 / 108,988 / 108,598 / 102,848 / 109,201). There is no API
  bill; it ran on the Claude Code plan.

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
| Claude Opus 5.5 (subagents) | **0.982** [0.954, 0.993] | **0.765** [0.527, 0.904] | 4/4 | 5/5 | n/a | 534,506 subagent tokens |

**The intervals** are Wilson 95%.

**The costs** are list price × the token counts each API returned:
- Gemini realtime: $0.30 / $2.50 per M tokens.
- DeepSeek V4.1 Flash off-peak: $0.15 / $0.60, cache-miss, with 0 cache hits recorded.
- Per 1,000 articles **on THIS prompt** (rubric v2 + article): Gemini $0.98, DeepSeek $0.40.
- ⏳ **Billing confirmation pending.**

**Binary agreement on 242 rows:** Gemini–DeepSeek 225, Gemini–Claude 227, DeepSeek–Claude 230. Full output is in
`calibration_result.txt`.

**Errors:**

| | Gemini | DeepSeek |
|---|---|---|
| false in | 11 | 3 |
| missed in | 2 | 8 |

- **2 false ins are shared by both:** a BBC NI row and a Spinoff row.
- **1 false in is an exemplar shared by both:** the young ag networking group, which the rubric puts out as
  professional networking.
- **The 2 misses shared by both are both exemplars:** the hospital clean-up and the kauri planting.

**Where all three oracles disagree with the labels** (Claude's read of their reasons; the owner has not checked
these). These look like LABEL or RUBRIC problems, not oracle problems:
1. **The DIY classes for women** (`pilot3:british_irish_bbc_northern_ireland_dc99721a35e2`).
   - All three say **in**: named women keep returning to a shared shed, and they build and care for each other.
   - Both pilot-v3 judge passes said out ("charity-run courses").
   - **The judge label is probably wrong.**
2. **The hospital clean-up and the kauri planting**, two of Claude's P exemplars. All three say **out**: a one-day
   clean-up event, and a conservation project.
   - The rubric pulls two ways here: "community events where people take part" (in) against "ongoing or shared, not
     a one-off moment".
   - **The owner needs to rule** whether a one-day community action counts.
3. **The prison theatre and the women's music programme**, ruled IN by the owner under Q3.
   - DeepSeek and Claude say **out**: "the bonds between participants are not shown", "a staff-delivered therapy
     programme". Gemini says in.
   - Q3's line ("participants build something together") is not getting through as written. **It needs a sharper
     sentence** in the rubric.

4. **The festival listing and the band's 45th year**, out-exemplars from the owner's Q1 OUT list. Claude says **in**
   on both.
   - `rubric_belonging_v2.md` kept the Q1 rule ("traditions the people themselves carry") but not its OUT examples,
     so the rubric no longer says that a listing or an anniversary is out.
   - **A drift between the ruling and the rubric text.** Restore the OUT examples.

**Reading** (Claude's):
- **Gemini has the best recall: 0.88, missing only the two exemplars in item 2.** It has the most false ins:
  11 of 220.
- **Claude is in between:** specificity 0.98, recall 0.77. All four of its misses are exemplars from items 2 and 3.
- **DeepSeek is the strictest:** specificity 0.99, recall 0.53.
- **On the 4 pilot positives (unseen rows)**, Gemini and Claude both score 4/4 and DeepSeek 2/4.
- ⚠️ **Claude's figures are inflated by shared bias:** the labels came from Claude Opus 5.5 judges reading the same
  rubric.
- **For a SCREEN** (find candidates, then confirm with judges and the owner), recall is what matters. **Gemini is the
  candidate**, at ~$1 per 1,000 articles on this prompt.
  - The confirmation step absorbs its ~5% false ins.
  - DeepSeek would lose about half the positives before anyone sees them.
- **Before scaling,** fix items 1–4 with the owner; they are a rubric problem. The recall intervals stay wide: n=17,
  13 of them exemplars.
