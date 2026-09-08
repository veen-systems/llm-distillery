# human_thriving v8 — the first live-output audit (2026-09-08)

⛔ **Headline: v8 faithfully implements its oracle. The oracle PROMPT is what diverges from the
documented lens — on 18% of live output, in three categories `STATUS.md` already names as owed.**

Reproduce every number here: `PYTHONPATH=. python3 docs/evidence/2026-09-08-v8-live-panel/decompose.py`
(committed output: `decompose.txt`). The script recomputes from the artifacts and **asserts** that
the shipped `ground_truth_gate.py::_wa` still reproduces NexusMind's deployed
`raw_weighted_average` — if either repo's aggregation drifts, it fails rather than reports.

## Population

`data/filtered/human_thriving/filtered_20260907_180414.jsonl` on sadalsuud — **v8's first
cycle that actually scored** (the 12:10 cycle died in image enrichment; see the incident in
`docs/RUNBOOK.md` §4b and #152). 6,210 articles scored, **63 above the 4.50 op-point**.

⚠️ **That cycle was 2.45× normal size**, draining backlog from the incident. Rates hold;
absolute counts do not. Normal cycles since: 45, 26, 34 passers.

**Panel n=62.** One row dropped, excluded twice over: `gn_asia_gn_uzbekistan_0eb9a39780bf`,
`content_length` 97 — under `make_oracle_prefilter`'s 300-char labelling floor (#93) **and** a
Google News row, which this repo forbids oracle-re-scoring (sub-300-char headline echoes).
⚠️ Its raw is **5.022**, i.e. not a marginal passer — the one row the oracle instrument cannot
see is one the gate would expect to be right.

## Arms

All DeepSeek `deepseek-chat` via `scripts/score_deepseek_production.py`; v8's oracle family.

| arm | prompt | text | k | in_scope | Wilson 95% |
|---|---|---|---|---|---|
| **A** | `prompt-v8-4.md` (44.7 KB, `c4705408c477`) | full | 6 | **60/62 = 0.968** | [0.890, 0.991] |
| **B** | NexusMind's README-derived rubric (~250 tok) | full | 1 | **49/62 = 0.790** | [0.674, 0.873] |
| **C** | same rubric | 4000 chars | 1 | **49/62 = 0.790** | [0.674, 0.873] |

Against the ADR-021 deploy gate neither arm is distinguishable: scope **Newcombe [-0.007, +0.329]**,
score **Newcombe [-0.001, +0.449]** — both point estimates above the gate's.

Arm A also gives **score precision 48/62 = 0.774** [0.656, 0.860] (k=6 mean oracle weighted
average ≥ 4.50). Of its 14 misses, **12 are `in_scope` boundary disagreements** (oracle 3.03–4.46,
8 of them within 0.5 of the line) and only **2 are genuinely off-lens**.

## The decomposition

The DeepSeek(A) − Gemini gap of +0.1423 splits cleanly:

```
PROMPT      A vs B  paired McNemar b=12 c=1   exact p = 0.0034   +0.1774
TRUNCATION  B vs C  paired McNemar b= 3 c=3   exact p = 1.0000   +0.0000
FAMILY      C vs Gemini, rubric+truncation fixed              −0.0323   n.s.
```

⭐ **Prompt more than accounts for the whole gap.** Not a k artifact: arm A's k=1-equivalent
(mean per-row vote share) is **0.9677**, identical to its k=6 majority.

⛔ **Every null here is a RATE-null with case-level churn — report "the rates are
indistinguishable", never "it doesn't matter".**

| contrast | rate | cases |
|---|---|---|
| truncation | 0.000 | **6 of 62 articles changed verdict** (b=3, c=3) |
| family (DeepSeek vs Gemini) | −0.032 | **8 of 62 disagree**, Cohen's κ **0.587**, 5-way agreement 50/62 |
| prompt | **+0.177** | **12 one way, 1 the other** — large *and* directional |

⚠️ **κ = 0.587 bounds what this evidence can carry:** no single article below is *proven*
mis-scored. The finding is the **pattern**, not any row.

## ⭐ The 12 prompt flips are `STATUS.md`'s owed v8.1 gaps

Same family, same articles, **only the prompt changes**: 5 `out_of_scope`, 5 `response_to_harm`,
2 `no_person_benefits`. Set against `filters/human_thriving/v8/STATUS.md`:

| STATUS.md, owed and unimplemented | live rows that flip |
|---|---|
| §2 **commencement** — *"a policy change that has not taken effect is an announcement"* (fix RULED 2026-09-03, unwritten) | Houston rental air-conditioning law **5.544** (benefit not delivered until December); Hong Kong schools "brace for" **5.075** |
| §1's announcement rule is written in terms of **money**, so a **legislative proposal has no rule pointing at it** — *"six above-op rows … score 4.55–6.33 anyway"* | water systems "to be built" **4.888**; Mentawai forest petition **4.655**; Madras HC reconstruction permission **4.554** |
| ⛔ **clause D (§5 judicial relief) is DROPPED** — the convict-relief ruling stands unexecuted (#143) | Bombay HC custody ruling **6.110** (2nd-highest in the panel); the Madras HC row |

⭐ **My five `out_of_scope` flips span 4.554–5.544, against STATUS.md's independently-derived
4.55–6.33.** A production panel rediscovered all three gaps by a route that never read the prompt.

## The band finding — the only thing that replicates

| band | n | share | scope precision (this arm) |
|---|---|---|---|
| **[4.5, 5.0)** | 37 | **58.7%** | 0.946 (score 0.676) |
| [5.0, 5.591] | 20 | 31.7% | 1.000 (score 0.900) |
| (5.591, 6.129] | 5 | 7.9% | 1.000 (score 1.000) |

Both off-lens articles are in `[4.5, 5.0)`; so are 7 of the 12 prompt flips, 8 of Gemini's 11
failures, 15 of Claude's 22, and all three of the deploy gate's off-lens false positives.
**Five measurements, three model families, two populations, one half-point of score range.**

⛔ **This does NOT license raising the op-point to 5.0, and the recommendation is the opposite.**
7 of 12 flips there are a *known prompt* problem with a fix already owed. A prompt fix keeps the
volume; a threshold move discards 58.7% of it. **Sequence the prompt work first, re-measure after.**
What a 5.0 gate would *lose* is unmeasurable from a panel selected on passing.

## What this does not establish

- **Not lens transfer.** DeepSeek is v8's own teacher; arm A measures distillation fidelity and
  structurally cannot detect the written definition failing to transfer.
- **No single-judge precision number is trustworthy to better than ±16 points.** Three judges on
  this panel span **0.651 to 0.968** (Claude 41/63, Gemini 51/62, DeepSeek 60/62).
- **No authorship-independent judge exists**: `openai_api_key` returns HTTP 401, and DeepSeek,
  Gemini and Anthropic are all already in the set.
- **One cycle**, and an atypical one. `[4.5,5.0)`'s 58.7% share did **not** replicate: the
  00:07 cycle gave **30.8% (8/26)**, outside a 46–70% interval predicted from this cycle.
  ⚠️ That prediction and the 58.7% share it came from **share one contaminated denominator** —
  the 2.45× backlog cycle.

## Cross-repo

NexusMind ran the complementary blind-adjudication arm (independent families, controls,
pre-registered decision rules, three amendments all made before any verdict was read):
**PR #461**, **issue #462**, commits `4c6fc9f` / `94ff14e` / `cdcf4ea`.

## Spend

**$0.16** — 6 oracle passes at k=6 ($0.14, 85%→99.5% cache), two rubric arms (~$0.01), pilot ($0.01).
