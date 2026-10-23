# Mistral Large 4 as an oracle on belonging v3: label parity against the Gemini baseline — pre-registration

**Written and committed 2026-10-23, BEFORE any Mistral call in this experiment.** It fixes what EXP-054 lacked: EXP-054
ran before a pre-registration, so it could only describe.

Asked by infra (cross-session, 2026-10-23) as an offer. The owner said go in this session on 2026-10-23 ("yes, spend
it"), which also covers the open carve-out in `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` (oracle ships
article text to the vendor; Mistral keeps API input 30 days, training toggle OFF per the owner 10-21).

## Question

Does `mistral-large-4-0` score belonging v3's frozen canary set the way belonging's labelling oracle does?
The labelling oracle is `batch_scorer|gemini-flash` (served `gemini-2.5-flash`, thinking off). Its billing key
returned HTTP 402 "prepayment credits are depleted" on a check call on 2026-10-23, so a Mistral path matters for
belonging now, and as an EU fallback generally.

## Set and baseline: committed, $0

- Set: `datasets/canary/belonging/set.jsonl`, sha256 `a44d8f07d2ee…` (`config/canary/belonging.json`), 100 items.
- Baseline: `config/canary/belonging.baseline.json`, the per-item mean of 6 Gemini runs. Op-point 4.0. 47 of the 100
  baseline means are at or above 4.0.
- Noise bar (Gemini against itself): k=1 F=3 S=0.0467; k=3 F=2 S=0.0496. The canary's margins are fixed in
  `ground_truth/oracle_canary.py`: FLIP_MARGIN 1, SHIFT_MARGIN 0.15.

## Request (fixed)

- Prompt bytes: built by `ground_truth.batch_scorer.GenericBatchScorer.build_prompt` itself (the stripped template,
  same sanitising and 800-word compression), so the prompt is the one the baseline was scored with. The run script
  refuses unless the template's digest equals the baseline's `prompt_sha256_stripped`.
- One user message, `temperature` 0.3 (the oracle path's), JSON mode, `max_tokens` 8192.
- Scores go through the canary's own arithmetic (`oracle_canary.run_scores` → the deploy gate's `_wa`).

## Probe: 3 calls, before any full run

1. Article 1, vendor default (reasoning as served).
2. Article 1 again with a reasoning-off request (`reasoning_effort: "none"`).
3. Article 2 with the setting chosen by the rule below.

**Rule for reasoning:** the baseline runs with thinking off. If call 2 is accepted (HTTP 200) AND returns no thinking
content, the full runs use reasoning off. Otherwise they use the vendor default, and the README says so as a
difference from the baseline.

**Rule for cost:** project 3 full runs (300 calls) from the probe's per-call tokens at Mistral's list price as found
by infra (web aggregators, unverified: $1.36/M in, $4.18/M out), ×1.25 for retries. If the projection exceeds €18,
stop and go back to the owner. The bill is read off Mistral's usage page afterwards; the projection is not the bill.

## Full runs

k = 3 runs, M1–M3, concurrency 4, each resumed (by id) at most 4 passes until all 100 items are scored. Any run with
items still missing after that: **NO-VERDICT**, reported as such.

## Decision rule (fixed before looking)

- **Primary:** the mean of M1–M3 against the baseline, at the k=3 bar. **FAIL** if flips > 2 + 1 = 3 or
  |shift| > 0.0496 + 0.15 = 0.1996; otherwise **PASS** (the bar `canary.py evaluate` applies at k=3).
- **Secondary:** each of M1–M3 alone at the k=1 bar (flips > 4 or |shift| > 0.1967 fails).
- **Mistral's own noise:** each run against the mean of the other two (flips, shift). If Mistral's own flips exceed
  Gemini's k=1 F (3), the README says the Mistral instrument is noisier than the baseline it is judged against.

**What a PASS would mean:** Mistral agrees with this oracle on this set as closely as the oracle agrees with itself.
It does NOT make Mistral a drop-in. Switching would be a new oracle key, with every canary baseline rebuilt on it
(`canary.py` refuses another oracle by design). One filter, one set.

## Also reported

- Parse rate, `finish_reason` counts, empty-content count (EXP-054's Medium 3.5 returned `{}` on 80 of 172 calls).
- Tokens per call (in / out), and the projected € per article at the unverified price, so the owner can compare
  the €25.50/month allowance with a 5–10K-article labelling run.
- Served `model` per response (#157).

## Predictions (stated before any call)

- Shift is positive (Mistral more generous than Gemini Flash). EXP-054's Medium 3.5 was +0.51 on human_thriving;
  that was a different prompt, a smaller model and a DeepSeek baseline.
- Primary verdict: FAIL, on flips (predicted 5–12).
- With reasoning on, output is 1,000–3,000 tokens per call; with it off, under 600.

## Data

Raw rows go to lab `experiments/2026-10-23-mistral-large4-belonging-parity/raw/` (written on situla directly, no
host copy), cited with `lab.py cite`. Registry id: **EXP-060**, if still free when this concludes.
