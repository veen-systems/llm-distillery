# v8.1 measured against Gate B-A — and criterion 1 was never stably failing

**2026-09-03. Spend $0.17** (balance 7.40 → 7.23; the script's peak estimate said $0.16, so its
estimate is a *lower* bound). 54 runs, **0 errors**. Run 06:58–07:2x UTC, i.e. **inside the
06:00–10:00 peak window** — deliberately, because 39 calls at a ~$0.01 surcharge gated everything
downstream. DeepSeek balance probed **before** the first call (the 2026-09-01 omission).

Reproduce: `PYTHONPATH=. python3 docs/evidence/2026-09-03-v8-1-gate/analyse.py <arm>`

---

## ⛔⛔ THE KEEPER — the blocking gate was failing on a coin flip, at k=3

Everything today started from *"acceptance criterion 1 is FAILING: the nursery row scores 4.400
against a 3.85 bar."* That figure is a **k=3 mean on a bimodal row**, measured 2026-09-01.

Measured at **k=6** under the *unchanged* v8 prompt:

| | mean | sd | runs | verdicts | vs bar 3.85 |
|---|---|---|---|---|---|
| nursery row, v8, **k=3** (09-01) | **4.400** | — | 6.10 / 0.90 / 6.20 | 2 in_scope, 1 off | **FAIL** |
| nursery row, v8, **k=6** (today) | **3.608** | **2.560** | 6.30 / 1.05 / 6.00 / 6.20 / 1.05 / 1.05 | **3 in_scope, 3 off** | **PASS** |

**It is a 50/50 coin toss, and the k=3 mean is a coin flip about the bar.** With sd 2.560 the
standard error at k=3 is **1.48**; the distance from 4.400 to 3.85 is **0.55**. The plan's own
Gate B-A rule says *"the margin must clear the band"* — nobody computed the band for this row,
and it does not clear it at any k we have run.

⚠️ **This does not retire the owner's ruling.** The editorial question — is a bereaved family's
not-yet-commenced national regulation *"a process going well for people, now"* — was worth
answering and is answered (`docs/decisions/2026-09-03-v8-1-commencement-clause.md`). What it
retires is the **urgency**: criterion 1 was not stably failing, so v8.1 is a **label-quality**
change, not an unblocking fix.

⭐ **And the reframe makes the clause MORE valuable, not less.** Under `--aggregate all` a
coin-toss row's label is noise. B_commence takes the nursery row from **3.608 ± 2.560** to
**1.017 ± 0.055** — it does not move a failing row below a bar, it **removes a coin toss**.

## What the four clauses actually do — single-clause ablation, k=6, one judge, one session

Each arm is the v8 base with **exactly one** clause applied, lifted verbatim from v8.1b.

### The #91 origin row — *"Celebrated at birth, pushed into sex work"*

| arm | mean | sd | off-scope | verdicts |
|---|---|---|---|---|
| **v8 (baseline)** | **0.900** | **0.000** | 6/6 | harm_is_subject ×6 |
| **A — §1 not-about-money** | **2.583** | **2.381** | 4/6 | harm_is_subject ×4, **in_scope ×2** |
| B — §2 commencement | 0.917 | 0.037 | 6/6 | harm_is_subject ×5, response_to_harm ×1 |
| C — §3 jurisdiction | 0.900 | 0.000 | 6/6 | harm_is_subject ×6 |
| D — §5 judicial relief | 0.900 | 0.000 | 6/6 | harm_is_subject ×6 |
| v8.1b (all four) | 2.567 | 2.357 | 4/6 | harm_is_subject ×4, in_scope ×2 |

⛔ **Clause A alone reproduces the entire regression** (2.583/2.381 against the four-clause
2.567/2.357). B, C and D leave the row exactly where v8 pins it. **v8 holds this row at 0.900
with zero decoder spread over six runs; A turns it into a 1-in-3 chance of ~5.7 `in_scope`.**

⚠️ A is the clause the owner *approved* (decision 3, the legislative-proposal rule). The most
likely mechanism is A's own **CONTRAST example** — *"Lebanon abolishes death penalty — enacted"*
— which tells the model that an ended harmful practice scores normally; the origin article
closes on a youth committee that **stopped** the practice. ⚠️ **Untested**: that is a hypothesis
from reading, not a measurement.

### The nursery row — criterion 1's blocker

| arm | mean | sd | verdicts |
|---|---|---|---|
| v8 (baseline, k=6) | 3.608 | 2.560 | in_scope ×3, response_to_harm ×3 |
| A — §1 not-about-money | 1.058 | 0.249 | response_to_harm ×6 |
| **B — §2 commencement** | **1.017** | **0.055** | **response_to_harm ×6** |
| C — §3 jurisdiction | 1.875 | 2.047 | response_to_harm ×5, in_scope ×1 |
| D — §5 judicial relief | 0.975 | 0.075 | response_to_harm ×6 |

⚠️ **Every arm moves it, including C and D, which have nothing to do with policy commencement.**
The row is knife-edge, and adding *any* out-of-scope material to STEP 1 appears to tip it. B is
the intended mechanism and the most stable (sd 0.055); C is the weakest and still leaves 1 in 6
`in_scope`. **Do not read "D fixes the nursery row" as D doing the work the ruling described.**

## Gate B-A and the negative control, k=3

| | Gate B-A | class-A verdicts |
|---|---|---|
| v8 | 8/9 | — |
| v8.1 | 9/9 | in_scope ×1 leaked |
| **v8.1b** | **9/9** | **19 harm_is_subject / 5 response_to_harm / 3 no_person_benefits, zero in_scope** |

**No-regression set under v8.1b — 4/4 hold**: silent-crisis **4.967**, ULEZ **6.233**, Dutch
air-pollution **5.650**, Unifesp **4.750** (= v8 exactly, **+1.850 over v7's 2.900**, so the
DELTA assertion holds). ⚠️ At k=3 all four appeared to drift **down** (4/4 same sign); **paired
at k=6 in one session that dissolves** — 2 down, 2 up, one exactly 0.000, mean **−0.077**. The
apparent drift was cross-day noise between a 08-31 baseline and a 09-03 treatment.

## ⛔ Mine

1. **I wrote commencement as a NECESSARY condition when the ruling made it SUFFICIENT.** v8.1's
   §2 bullet read as one conditional ending *"a policy change that has not yet taken effect is
   an announcement"*, so a response that **had** taken effect escaped §2 entirely. Fixed in
   v8.1b by splitting the base rule from the additional trigger and stating *"commencement is
   NOT a way out of this bullet."*
2. ⛔ **I declared that fix successful from a k=3 draw.** v8.1b's gate run showed the origin row
   back at 0.900 harm_is_subject 3/3, and I reported the regression fixed. At k=6 it is
   **2.567 ± 2.357** — statistically identical to v8.1. **The k=3 run had drawn three stable
   runs out of a 2-in-6 bimodal distribution.** Same instrument error as the keeper above,
   committed by me, one hour after measuring it in someone else's number.
3. **I read 4/4-same-sign on the controls as a systematic effect** and said so before pairing
   the arms. It was noise.

⭐ The single lesson under all three: **on a bimodal row, a k=3 mean is not a measurement — it
is a sample of a coin flip.** #135 already says the scope gate is a step function that `1/√k`
does not describe. This is that, demonstrated on the blocking gate itself.

## Recommendation

- **Adopt B (§2 commencement), C (§3 jurisdiction) and D (§5 judicial relief).** All three are
  stable, none moves the no-regression set, and B removes a coin toss on the criterion-1 row.
- ⛔ **Do NOT adopt A (§1 not-about-money) as written.** It is the sole cause of the origin-row
  regression. Either drop it, or rewrite it without the *"Lebanon abolishes death penalty"*
  contrast example and re-run this ablation — ~$0.01.
- **Re-derive Gate B-A's k.** At k=3 this gate cannot distinguish 3.608 from 4.400 on its own
  worst row. Either raise k for bimodal rows or report the band and refuse a verdict when the
  margin does not clear it.

## What is NOT claimed

- **No corpus row was re-scored.** The 50 staged above-op rows are untouched pending a prompt.
- **No label was edited**, and no training data changed.
- **The A-clause mechanism is a hypothesis.** The ablation proves A is the cause; it does not
  prove the contrast example is the part of A responsible.
