# Cross-family panel for human_thriving (#177 step 6, the accuracy anchor) — pre-registration

**Written and committed 2026-10-21, after the owner's rulings below and BEFORE any panel call.** Design source: `docs/proposals/oracle-canary-177.md`
§ *The two jobs* and step 6; the ruling behind it is veen-systems/pipeline-atlas#169 (2026-10-15).

## Question

The canary catches the oracle **changing**. This panel asks whether the oracle is **wrong**: on the human_thriving
prompt (`c4705408c477`, DeepSeek `deepseek-chat`, served `deepseek-flash`), how often does the oracle's pass/block
call at the 4.5 op-point disagree with a panel of other model families? And do those families agree with each
other well enough for their majority to be worth comparing against?

## Set: the existing canary set, $0

This is `config/canary/human_thriving.json`, set sha256 `f6b06de160e7…`: 100 production articles that touch no
training row (by id, url, or e5 ≥ 0.93), stratified 30 / 30 / 40 by the student's score. The ruling says the same
set serves both jobs.

Per EXP-052's baseline, 30 of the 100 are at or above 4.5. So any recall figure here rests on about 30 positives,
and its interval will be wide. The plan says that up front.

## Oracle labels: $0

The oracle's labels are the committed 6-run baseline mean (`config/canary/human_thriving.baseline.json` `items`),
so no new DeepSeek calls are needed.

## Panel (open decision D2)

Every member scores the same 100 items, with the oracle's own prompt and scoring spec, through the deploy gate's
own weighted-average arithmetic (`ground_truth_gate.py` `load_scoring_spec` + `_wa`). Changing the prompt per
member would measure the prompt, not the family.

| id | model | family | where | cost |
|---|---|---|---|---|
| L1 | `qwen3.8:27b` | Qwen (Alibaba) | b650 Ollama, daytime | $0 |
| L2 | `gemma3:27b` | Gemma (Google) | b650 Ollama, daytime | $0 |
| L3 | `mistral-small3.2:24b` | Mistral | b650 Ollama, daytime | $0 |
| P1 | `gemini-2.5-flash` | Gemini (Google) | API, existing key | measured on a 10-item pilot first |
| P2 | a Claude model | Claude (Anthropic) | API credit, first credit ~10-26 | only with the owner's per-experiment approval, and only after #174's terms are read |

- L2 and P1 are both Google models, so they are not independent. They are reported as one family as well as two
  members.
- b650 runs in the daytime only: infra's SovereignStack holds b650 from 00:00 to 07:00. Before each run,
  `curl localhost:11434/api/ps` must show no model we did not load.

## Measures (fixed before looking)

1. **Panel agreement:**
   - Krippendorff's alpha across the members on pass/block at 4.5 (nominal) and on the weighted average
     (interval), plus AC1 per pair (`ground_truth/agreement.py`).
   - Each is reported with the oracle in and out of the panel.
2. **Oracle against the panel majority** (leave-the-oracle-out majority, ties counted as their own row): the
   oracle's **specificity and recall** (ADR-023), each with the panel's positive rate. A 95% item-bootstrap
   interval is reported, never MAE.
3. **Instrument controls:**
   - Each member's parse rate must be ≥ 95%, and its own pass rate is printed. A member that passes or blocks
     nearly everything (≥ 95 of 100) cannot disagree, so it is reported and left out of the majority.
   - Each local member runs twice. A member whose own two runs flip more often than the canary's noise bar
     (7 flips) is too noisy to judge with, and is reported as such.

## Predictions (stated before any panel call)

- Cloud members agree with each other better than local ones do.
- Alpha on pass/block among the non-oracle members falls between 0.4 and 0.75. A figure above 0.9 would point to
  shared prompt artefacts, not shared judgment, and gets checked before it is believed.
- Against the panel majority, the oracle's specificity is ≥ 0.85. Its recall is not predicted: about 30
  positives is too few.

## Out of scope

- The owner's ~30-item hand-label slice. It comes after this, as the reference.
- Other filters.
- Any change to the oracle, to the canary, or to a training set. Panel outputs never become training labels.

## Owner rulings (2026-10-21)

- **D1:** human_thriving first.
- **D2:** panel = L1, L2 and L3 (b650) + P1 (Gemini 2.5 Flash). P2 (Claude) is a possible later round. It is NOT
  approved by this ruling: it needs its own per-experiment approval for the API credit, and #174's terms read first.
- **D3:** hard cap of $2 total on paid calls. The 10-item P1 pilot measures tokens on this prompt. If the full run
  projects past the cap, it stops and goes back to the owner.

## Run notes (fixed)

- **P1** runs through the ORACLE's own scorer, `scripts/score_deepseek_production.py`, pointed at Gemini:
  `--base-url https://generativelanguage.googleapis.com/v1beta/openai/chat/completions --key-name gemini_api_key
  --model gemini-2.5-flash`, with the baseline's `--config` and `--prompt`, and `--skip-canary "cross-family panel
  EXP-055 (#177): evaluation only"` (the gate refuses any other oracle; the reason is stamped on every row).
  That makes the prompt text, the request body and the temperature (0.3) identical to the oracle's; only the model
  differs. (Amended before any call, 2026-10-21: the first draft named `batch_scorer`, which builds the request
  differently.)
- **Cost check:** the pilot's measured tokens are priced at $0.30/M input and $2.50/M output, Gemini 2.5 Flash's
  paid realtime card as recalled. Before the full run, the operator re-checks that card at the vendor page.
- **L1, L2 and L3** run through `scripts/score_ollama_oracle.py --provider ollama`, k = 2 each.
- Pull everything back with `lab.py pull`; cite with `lab.py cite`.
- **Registry id: EXP-055**, if it is still free when the run starts.

## Amendment 2026-10-21 (evening): P2, Claude Sonnet 5.5. Committed BEFORE any P2 call

**Owner approval, 2026-10-21:** "Yes, Sonnet Batch, $5 cap", against the Anthropic promo credit (expires
2026-10-28). Infra was sent the estimate in advance. P2 is EVALUATION ONLY: its outputs never become labels.

**How P2 is scored:** `score_claude_batch.py` in this dir.
- **Request:** the oracle's prompt template and `build_prompt` (`score_deepseek_production.py`), unchanged.
  `claude-sonnet-5-5` via the Message Batches API, `max_tokens` 4096.
- **Thinking:** `{"type": "between_tools"}`, which is Sonnet 5.5's thinking-off mode. The oracle (DeepSeek chat)
  does not think either.
- **Parsing:** the reply goes through the oracle's own `parse_response`, wrapped in the same envelope, so the
  parse, the dims and the provenance checks are identical. The ONE difference: a reply wrapped in a ```json code
  fence has the fence stripped first.
- **Deviation: temperature.** Sonnet 5.5 rejects any non-default temperature (400). P2 therefore runs at the API
  default, not the oracle's 0.3. The run-to-run noise of P2 is therefore NOT measured (k = 1).

**Cost guard:**
- The price was checked at the source on 2026-10-21: Batch, $1/M input and $5/M output.
- Input tokens are counted with `count_tokens` on 3 items. The projection, at 100 × (counted input + 4,096 output
  as the worst case), must be ≤ $5 or nothing is submitted.

**Analysis:** P2 joins `analyse.py` as a fifth member under the same eligibility rules. The parse bar for a k = 1
member is the share of items scored. It is reported both inside and outside the panel majority.

## Amendment 2 (2026-10-21 evening): P2 at k = 2. Committed BEFORE the second P2 call

**Owner, 2026-10-21:** "Sonnet run 2", with llm-distillery's promo-credit cap raised to **$12 total**.

- **What changes:** a second, identical Batch pass of P2 (same script, same parameters, a separate work dir).
- **Why:** it measures P2's own run-to-run noise. At the API's default temperature that noise is unmeasured, and
  the local members already get 2 runs.
- **The same rules as the local members:**
  - P2's self-flips between the two runs must stay within the canary's noise bar (7), or P2 is reported as too noisy
    to judge with;
  - P2's score is the mean of its two runs;
  - its parse rate is the share of items scored in BOTH runs.
- **Analysis:** `analyse.py` gains multi-file members (`--member P2=run1.jsonl,run2.jsonl`). A file is one run.
  This is an amendment to the committed script, made before either P2 file is read.
