# The ≥ 7 pool — plan (written before any adjudication or oracle call)

**2026-09-26.** Owner, in session: *"Yes, run it"* (option text written by the assistant: blind
adjudication of ~720 high-scoring articles, then k=3 oracle, est. $0.10–0.20). The question it was
proposed for (TODO-archive, *OPEN OWNER QUESTION — the ≥ 7 pool*): add Thriving positives as the
volume lever the owner chose for v9 instead of a lower cut-off, and test whether the empty top
(0 labels ≥ 8, 3 at 7–8 of 6,772) is the oracle's SCALE or missing data.

## Pool (`build_pool.py`, run read-only on sadalsuud; `pool.jsonl`)
Production articles scored **raw ≥ 7 at stage 2** by `uplifting`, `belonging`, `solutions` or
`human_thriving`, files dated 2026-09-02 → 09-24. Excluded as in the more-positives run:
`news.google.com` urls, content < 300 chars, duplicate content hash, and **any id already in the v8
corpus, the adj3 training dir, or an earlier adjudication input** (8,285 ids).

| filter set that scored it ≥ 7 | rows |
|---|---|
| uplifting only | 192 |
| belonging only | 450 |
| belonging + uplifting | 14 |
| **kept** | **656** (57 excluded as already labelled; 0 GN, 0 short, 0 duplicate) |

⚠️ **Design-weighted, like every pool before it**: this is active learning toward positives
(ADR-005). Yields are reported **per filter set**; no production rate may be derived from them.

## Step 1 — blind Claude adjudication ($0)
Same rubric, verdict set, blinding and instructions as the band-audit re-run; the only change is
ruling 6 (`judge_instructions.md`, diffed against its parent). Shuffled with seed 20260926 into 11
batches of ≤ 60 (`input_A*.jsonl`, one blind subagent each). **Pass B** (drift check): a seeded 20%
(131 rows, seed 20260927, `input_B*.jsonl`), judged blind again by different subagents.
- **Stop rule:** A-vs-B binary (in_scope vs not) agreement below **0.90** → the run is NOT used; the
  result is reported, not repaired.
- **Tie rule:** an A/B split is **not in scope** (ADR-023).
- Each output is checked against its input: ids, order, verdict set, and quote-in-article.

**Predicted in-scope yield (guesses, before running):** uplifting only **15–35%**, belonging only
**10–30%**, both **20–50%** (n = 14, too small to read). Anchors: the more-positives run's
uplifting_only 11.5% and belonging_no_v8 19.0% at the op-point; a ≥ 7 score should raise both.

## Step 2 — oracle (≈ $0.10–0.20, the owner's yes above covers it), rules fixed now
- **Prompt `filters/human_thriving/v8/prompt-v8-4.md`** (sha256[:12] `c4705408c477`, the prompt of
  every v9 label), k=3, DeepSeek `deepseek-chat`, via the same scorer invocation as the
  more-positives `runs/new_*.log`.
- **Alias control (#157: the alias can change model unmeasured):** re-score 50 seeded rows of the
  more-positives `new_labels.jsonl` (V4.1 labels, same prompt). `d` = median(new − old) on the
  weighted average. **|d| ≤ 0.30 → the new rows are mixed 80/10/10; |d| > 0.30 → TEST ONLY.**
- **Oracle disagrees with Claude** (k=3 majority verdict on a Claude-`in_scope` row is not
  `in_scope`): excluded and counted, not relabelled.
- **The scale question is answered from the kept rows**: count weighted ≥ 7 and ≥ 8, and per
  dimension ≥ 8. If still ~0 ≥ 8 among articles Claude calls in scope AND production scored ≥ 7,
  that points at the oracle's SCALE, not missing data.

## Not decided here
Whether the not-in-scope rows are added as capped hard negatives (the adj3 precedent) — that adds
oracle cost and changes the negative mix; it goes to the owner with step 1's numbers. Any retrain
(v10 candidate) is a separate, gated step (ADR-021).

## Hard negatives — APPROVED by the owner 2026-09-26 ("Yes, add them"), rule fixed before any call
The **473** pool rows NOT judged in scope (356 out_of_scope, 78 harm_is_subject, 21
no_person_benefits, 8 response_to_harm, 10 A/B splits) are oracle-scored k=3 with `prompt-v8-4.md`
and **every dimension is capped at 2.0, whatever the oracle's verdict** — the adj3 rule. How often
the oracle's k=3 majority calls one `in_scope`, and how many have an uncapped weighted ≥ 4.5, is
counted and reported (the oracle's own leak rate on production ≥ 7 mistakes). Estimate ~$0.70
(scaled from this pool's measured $0.36; an estimate). Any rows that never score after retries
are excluded and counted.
