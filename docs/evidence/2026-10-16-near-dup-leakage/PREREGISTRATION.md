# Near-duplicate leakage into gate and test sets (#176) — pre-registration

Written 2026-10-16, **before any embedding was computed or any pair read.** $0 (e5 on b650).

## Question

Do the evaluation sets of the two most recently gated live filters contain near-duplicates of
their own training rows? If they do, the published recall/specificity are measured on leaked
data (#176). `prepare_data.py` removes exact duplicate ids only; `near_dup_filter.py` compares
a pool against a calibration file, never pool rows against each other. belonging's gate
(`gate3.py`) already refuses LEXICAL twins (id, url, title, a content window) — this measures
what it cannot see: translations and rewritten copies.

## Populations (query set vs reference = the package's training rows)

| arm | query set | reference (train) | why |
|---|---|---|---|
| A1 | `datasets/training/human_thriving_v8/test.jsonl` (660) | `datasets/training/human_thriving_v8_adj3/train.jsonl` (5,768) | v9's deploy gate ran on v8's 660 test ids; v9 = `adj3` (counts match `training_metadata.json`) |
| A2 | `human_thriving_v8_adj3/test.jsonl` (723) | same | the split prepare_data made |
| B1 | `datasets/belonging_heldout3/heldout3_rows.jsonl` minus Amendment 1's 3 drops (2,397) | `datasets/training/belonging_c2b/train.jsonl` (6,331) | belonging v3's gate (held-out set 3); v3 = `c2b` per its STATUS.md |
| B2 | `belonging_c2b/test.jsonl` (780) | same | the split prepare_data made |

## Instrument

`intfloat/multilingual-e5-small`, normalized, text = `scripts/screening/near_dup_filter.py`
`text_of` (`query: {title}. {content[:1024]}`) — the repo's existing near-duplicate geometry.
Per query row: max cosine to any reference row, and that reference row's id. Report counts at
**≥ 0.90 / 0.93 / 0.95** with the query-set size beside each, and the median max-cosine.

**Controls (in the same run, printed by the script):**
1. *Presence:* 5 reference rows copied into the query set under new ids → each must score ≥ 0.99.
   If not, the instrument is broken and no count is read.
2. *Rewrite:* the same 5 with the title replaced and the first 300 content chars dropped → their
   cosines are reported, so we know whether 0.93 can see a re-edited syndicated copy.

## Predictions (stated before running)

- A1, A2, B2: **0.5–5%** of query rows at ≥ 0.93 (news syndication; nothing dedups within a pool).
- B1: **0–1%** (the lexical guard and Amendment 1 already removed the obvious twins).
- An implausibly high count (> 15%) is an instrument signal, not a result: check the text field first.

## Reading the pairs, and what is decided

Every ≥ 0.93 pair in A1 and B1 (the GATE sets) is read and classed: (a) same text, (b) same
article, other outlet or translation, (c) same event, different article, (d) different event.
**(a) and (b) are leaks**; (c) is reported, not counted as a leak (the model may have learned the
event, but a different article is a fair test); (d) is an instrument false positive.

- **0 leaks in A1 and B1** → the two gates are not inflated by near-duplicate leakage at this
  instrument; #176 step 2 is not needed for them. Step 3 (prevent by construction) is then a
  cost/benefit call for the owner, informed by the A2/B2 counts.
- **≥ 1 leak** → recompute that gate's numbers with the leaked rows excluded, from the stored
  per-row gate outputs (no re-scoring), and report the change against the noise floor, as the
  VERDICT FLIP count at the op-point, not max |Δ| (#95).
