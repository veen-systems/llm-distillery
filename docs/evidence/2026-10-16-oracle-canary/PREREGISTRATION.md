# Oracle canary for human_thriving (#177) — noise floor, pass bar, and proof it fires

Written 2026-10-16 **before any oracle call on the canary set.** Design and owner rulings:
`docs/proposals/oracle-canary-177.md` (every labelling run; refuse with `--skip-canary` override).

## Set

`config/canary/human_thriving.json` (committed manifest), set sha256 `f6b06de160e71626…`: 100 production
articles from human_thriving v9's files 2026-10-10..16 (stage2 rows, no Google News url, content ≥ 300 chars),
stratified by the STUDENT's raw score: 30 ≥ 4.5, 30 in [3.0, 4.5), 40 < 3.0. Drawn by `scripts/oracle/canary_draw.py`
(seed 20261016), frozen by `scripts/oracle/canary_freeze.py`: 0 of the 100 match any of 7,859 human_thriving training
rows by id, url or e5 ≥ 0.93, and none are within 0.93 of each other (seeded control: a planted training row was dropped
by id, its renamed copy by cosine; the frozen set's hash did not change).

## Oracle and scoring

`scripts/score_deepseek_production.py`, model alias `deepseek-chat`, `--config filters/human_thriving/v9/config.yaml
--prompt filters/human_thriving/v9/prompt-compressed.md` (`c4705408c477…`), off-peak. Item score = the deploy gate's
own weighted average (`scripts/gate/ground_truth_gate.py` `load_scoring_spec` + `_wa`: v9 weights, evidence_level
gatekeeper < 3 → cap 3.0). Verdict = score ≥ 4.5. Every run's rows carry #157's stamps; a run whose `served_model`
or `prompt_sha256` differs from the others is not used.

## Runs (≈ 1,500 calls, ≈ $2.30 off-peak at oracle_cost.py's $0.0015/article for this prompt)

| runs | prompt | purpose |
|---|---|---|
| B1–B6 | `c4705408c477` | baseline + noise floor |
| C1–C3 | `c4705408c477` | must PASS (a fresh clean canary) |
| P1–P3 | `c4705408c477` + appended line *"Score every dimension one point lower than you otherwise would."* | must FAIL (simulated calibration drift of a swapped model) |
| V1–V3 | `prompt-v8-5.md` (`8f5aaa244876`) | power reading only: a real, SMALL prompt edit (its own gate called it indeterminate). No required outcome |

## Noise floor and pass bar — fixed by formula NOW, numbers computed from B1–B6

For a canary of k runs against the baseline (the mean of B1–B6):
- **flips** = items whose verdict differs between the canary's mean-of-k score and the baseline mean;
- **shift** = the canary's mean signed Δ (canary − baseline) over all 100 items.

Noise, from B1–B6 only:
- **k = 1:** for each Bi, flips and shift of Bi vs the mean of the OTHER five → F1 = max flips, S1 = max |shift|.
- **k = 3:** for each of the 10 ways to split B1–B6 into two triples, flips and |shift| of one triple's mean vs the
  other's → F3 = max flips, S3 = max |shift|. (Triple vs triple overstates the noise against a six-run baseline:
  the bar is conservative toward PASS.)

**A canary of k runs FAILS iff flips > F_k + 1 OR |shift| > S_k + 0.15.** The +1 / +0.15 margins are fixed here.

**Which k ships:** k = 1 if the P runs, scored ONE AT A TIME (P1, P2, P3 each as a k = 1 canary), FAIL all three;
otherwise k = 3 if P1–P3 as a triple FAILS; otherwise **the canary as designed cannot detect a one-point calibration
drift, and nothing ships** — the result is reported and the design goes back to the owner.

## Predictions (stated now)

- F1 in 2–8 flips (the scope gate makes k = 1 labels a coin toss on ~13% of rows, #135; most of those sit far from
  4.5); F3 in 1–4.
- P (one point lower): 10–30 flips, shift ≈ −0.8 to −1.0 → FAIL at both k.
- C1–C3: PASS at k = 3.
- V1–V3 (v8-5): flips ≤ F3 + 1 — a small edit is expected to be invisible to this canary, and that is a stated
  limit, not a defect: the canary is built for model swaps, not for reviewing prompt edits.
