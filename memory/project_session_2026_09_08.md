# Session 2026-09-08 — v8's first live-output audit: the student is faithful, the PROMPT is not

**Spend: $0.16** (6 DeepSeek oracle passes $0.14, two rubric arms ~$0.01, pilot $0.01).
Registry **EXP-029**. Evidence `docs/evidence/2026-09-08-v8-live-panel/`. New issue **#153**.
Ran alongside a NexusMind peer session throughout; its half is NM **#461** / **#462**.

## The question

Owner: *"is the scorer any good in practice? could we test its performance — training vs test vs
deploy, to 'prove' generalization?"*

**Answered: not as posed, because the third leg does not exist.** train/val/test are 5,268/658/660,
ONE stratified split (seed 42) of one 6,586-row corpus, so the ADR-021 gate measures generalization to
held-out rows of the **labelling corpus**. Production carries no labels, and the populations
demonstrably differ — the eval mix predicts **120–192** passers/cycle against **63** observed.
Recall and specificity in production need labels on non-passers at a ~1% base rate: thousands of
calls, not funded. **The affordable half is precision on live output, and that is what ran.**

## What was measured

62 of the 63 passers from `filtered_20260907_180414.jsonl` — v8's first cycle that actually scored.
One row dropped twice over: `gn_asia_gn_uzbekistan_0eb9a39780bf`, 97 chars, under the 300-char oracle
floor (#93) **and** a Google News row, which this repo forbids oracle-re-scoring.

| arm | prompt | text | k | in_scope |
|---|---|---|---|---|
| A | `prompt-v8-4.md` (`c4705408c477`) | full | 6 | **60/62 = 0.968** [0.890, 0.991] |
| B | NexusMind's README rubric | full | 1 | **49/62 = 0.790** |
| C | same rubric | 4000 chars | 1 | **49/62 = 0.790** |

Against the deploy gate: scope Newcombe **[-0.007, +0.329]**, score **[-0.001, +0.449]** — both
above it, neither distinguishable. Only **2 of 62** genuinely off-lens.

## ⭐ The finding

```
PROMPT      A vs B  paired McNemar b=12 c=1   exact p = 0.0034   +0.1774
TRUNCATION  B vs C  paired McNemar b= 3 c=3   exact p = 1.0000   +0.0000
FAMILY      C vs Gemini, rubric+truncation fixed              −0.0323   n.s.
```

**Prompt more than accounts for the whole gap** (not a k artifact: A's k=1-equivalent is 0.9677,
identical to its k=6 majority). And the 12 flips are `STATUS.md`'s three **owed** v8.1 gaps —
commencement (Houston **5.544**, Hong Kong **5.075**), the money-worded announcement rule that leaves
legislative proposals unaddressed (**4.888 / 4.655 / 4.554**), and dropped clause D on judicial relief
(#143 — Bombay HC **6.110**). The five `out_of_scope` flips span **4.554–5.544** against STATUS.md's
independently-derived **4.55–6.33**. ⭐ **A production panel rediscovered all three by a route that
never read the prompt.**

⚠️ **Pattern-level evidence, not per-row proof** — κ 0.587 between judges.

## The band, and why it does NOT mean raise the op-point

`[4.5, 5.0)` holds **58.7%** of shipped volume, both off-lens articles, 7 of 12 prompt flips, 8 of
Gemini's 11 failures, 15 of Claude's 22 and all 3 of the gate's off-lens FPs — **five measurements,
three families, two populations**, and the only result that replicates. ⛔ But 7 of the 12 are a
*known prompt* problem with a fix already owed; a prompt fix keeps the volume, a threshold move
discards it, and **a panel selected on passing structurally cannot measure what a higher bar would
lose**. Prompt first, re-measure after (#150).

## Controls that fired, and three findings that died

- ⭐ **`_wa(dims)` reproduces NexusMind's deployed `raw_weighted_average` to 0.000000 on 62/62.** Two
  independently-written codebases, one arithmetic — a load-bearing assumption under every band number,
  now asserted in `decompose.py` rather than assumed. **Not yet in the test suite** (carried).
- ⛔ **The sub-300-char stub finding was an artifact** — the export carried the pre-enrichment RSS
  teaser. Retracted in full; gotcha log 2026-09-08.
- ⛔ **"63 is below the 89 that eval's FPR alone predicts"** dissolved under the floor's own band
  [50, 99].
- ⛔ **A registered acceptance rule where "supports (a)" was unreachable** — a perfect 63/63 has
  Wilson lower 0.9425 against a comparator upper 0.9476.
- ⛔ **My band-share prediction FAILED**: predicted 46–70%, observed **30.8% (8/26)**. It and the
  58.7% it came from **share one contaminated denominator**, the 2.45× backlog cycle.

## Cross-session

Five corrections went each way with the peer. Theirs that landed on me: the snippet export, the
1,400-vs-4,000 truncation (their Amendment 1 changed two parameters and communicated one), the
cumulative Phase E bar, and a superlative (Bombay HC 6.110 is the panel's **second**-highest; max is
6.129). ⭐ **The two-instrument design found something neither half could — but what made it work was
that every number crossed a repo boundary before it was believed.**

## State at close

- ⛔ **Phase E is 168/200 CUMULATIVE — ~0.9 cycles. Do not disable v8.**
- ⭐ **The v7-vs-v8 same-articles comparison is FREE and has never been run.** Both lenses already
  score every article every cycle. Everything measured today asks whether v8 is *correct*; only that
  asks whether it is *better than what ships*, and only the second gates #151.
- **Carried:** CHECK 2 as a standing control; an authorship-independent judge is **BLOCKED**
  (`openai_api_key` → HTTP 401, and DeepSeek/Gemini/Anthropic are all already in the set).
