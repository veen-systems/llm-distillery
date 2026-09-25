# adj3 below its op-point — junk rate per cut-off in [3.5, 4.5), written BEFORE any band article is judged

**2026-09-25.** Owner: *"I would hope we could balance that a bit better, so increase adj3"*; approved
this measurement. The design is the **assistant's proposal**. This is a MEASUREMENT for the owner to
choose a cut-off from, not a pass/fail gate.

## Population
The live audit's week and exclusions, unchanged (`../2026-09-25-v8-adj3-live-audit/groups.json`:
123,374 audit ids). adj3 calibrated scores from the same b650 dumps, weighted by the gate's own
`load_scores(spec=...)`. Band = adj3 in **[3.5, 4.5)**: **937** articles, in four sub-bands:

| sub-band | N (counted before this was written) | drawn |
|---|---|---|
| [4.25, 4.5) | 182 | 40 |
| [4.0, 4.25) | 197 | 40 |
| [3.75, 4.0) | 245 | 40 |
| [3.5, 3.75) | 313 | 40 |

Uniform within each sub-band, seed 20260926. A row judged in the live audit may be drawn again and
is judged again, blind; the earlier verdicts are not reused (they covered only rows v8 also passed).

## Judging — identical to the live audit
Same `judge_instructions.md` (copied here, plus ONE added rule: each judge keeps any helper file
under its own `/tmp/judge_<batch>/`, because on 2026-09-25 one judge re-ran another's script and
rewrote its output). The 4 pilot controls are hidden in pass A: **4/4 or STOP**. Pass B is a seeded
20% re-judged in a different shuffle: **agreement < 0.90 → STOP**; an A/B split counts as not in scope.
**Owner check:** 20 drawn uniformly from the 160, blind. **≥ 18/20** → reported as a measurement;
below that, the result is withheld until the disagreements are ruled on, as in the live audit.

## What is reported
For each candidate cut c ∈ {4.5, 4.25, 4.0, 3.75, 3.5}, the junk share of everything adj3 would publish:

    junk(c) = (N_≥4.5 · j_≥4.5 + Σ_{sub-bands ≥ c} N_s · j_s) / (N_≥4.5 + Σ N_s)

with j_≥4.5 = adj3's live-audit estimate (groups A and B, re-weighted by N, as in `analyse.py`),
per-cycle volume (N/42), and a 95% bootstrap CI (resampling within every judged group, 10,000 draws,
seed 20260926).

**Guardrail, stated now:** a cut whose junk-share CI upper bound reaches **v8's point estimate
(0.338)** is reported as **"not shown to be better than v8"**, and the assistant will not recommend
it. The choice among the rest is the owner's (ADR-023: specificity first; volume is never a target).

## Limits
Same judge, same rubric, same week, one seed as the live audit. The sub-band N are counted on the
audit population, not the whole feed.
