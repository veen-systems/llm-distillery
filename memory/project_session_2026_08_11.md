---
name: project_session_2026_08_11
description: "Two op-points moved and deployed (uplifting 4.5, investment_risk 4.25) but NOT yet verified; the fleet got its first complete ADR-021 numbers; a deploy blocker and an og:image misdiagnosis both fixed"
metadata:
  type: project
---

# 2026-08-11 — shipped two op-points; verification is the next session's first job

**DEPLOYED, NOT VERIFIED.** Both changes activate at the first NexusMind cycle
after 12:02. The session ended before that cycle ran.

## Read this before anything else

**The verification criterion in both deploy commit messages is WRONG.** They say
the next batch must contain no rows with raw in the old band. It will.
`filtered_*.jsonl` holds **every scored row** — the 09:03 batch has a minimum raw
of **0.8412** — so band rows do not disappear when the op-point moves. **Their
tier changes.**

Pre-change baseline, captured while the old op-points were still live and
**not recreatable**:

| filter | batch | tier `medium` in band | overall low / medium / high |
|---|---|---|---|
| uplifting v7 | `filtered_20260811_090307` | **81** in [4.0, 4.5) | 4363 / 233 / 80 |
| investment_risk v6 | `filtered_20260811_090540` | **82** in [4.0, 4.25) | 1360 / 400 / 168 |

Both must read **0** after the cycle; `medium` should fall to ~152 and ~318.
Command in `docs/evidence/2026-08-10-uplifting-v7-op-point-4.5-VERIFIED.md`.

## The near-miss worth carrying forward

**An op-point lives in four places and `config.yaml` is not the runtime one.**
`base_scorer.py TIER_THRESHOLDS` is what scores. I changed the config, ran the
refit, and `fit_normalization.py` refused to agree with itself:

> *Operating point drift: base_scorer.py TIER_THRESHOLDS says 4.0, config.yaml
> scoring.tiers says 4.5. TIER_THRESHOLDS is the runtime source and wins here —
> but fix the mismatch, one of them is a lie.*

It then fitted at the **old** anchor and had to be redone. Changing the config
alone would have been a no-op in production. **Caught by a tool arguing back, not
by review.** Now a hard constraint in CLAUDE.md.

## What was established

- **The fleet has ADR-021 numbers for the first time.** Three filters were live
  with none. Completing the set **confirmed** #102 rather than refuting it:
  uplifting was 1.79× the next worst. My "the comparison set is half-missing"
  objection resolved *against* me.
- **The cheaper alternative is refuted.** A register/source-type rule removes
  **2** false positives and costs **21** true ones. The adverse batch pointed the
  wrong way because it sampled a different population from the test split.
- **`investment_risk v6`'s case is weaker than uplifting's, and that is recorded
  in the shipped artifact.** Its false positives are near-misses (oracle median
  3.05) — geopolitical/macro risk a reader on an investment-risk feed would
  plausibly want. Shipped on the 17-for-6 trade; revert is one line plus a refit.

## Two defects found by using things

- **`deploy_to_nexusmind.sh` ran `--check-hub` with no token.** The Hub returns
  404 (not 401) for a private repo accessed anonymously, so it aborted on a
  healthy repo — and would have blocked **any** private-Hub filter deploy. The
  commit-msg hook already resolved the token from `secrets.ini`; the deploy
  script did not. They disagreed, and the one that disagreed gated deploys.
- **og:image's "85% failure" is mostly correct behaviour** (NexusMind#316).
  Measured n=200: **48% have no og:image tag**, **26% are arxiv** (whose og:image
  is its own logo), 22% succeed, 4.5% are HTTP errors. **The obvious fix would
  make it worse** — resolving the relative URLs would push ~1,200 arxiv logos per
  cycle into a pipeline that already struggles with logos. Concurrency was tested
  and refuted (18.3% at both 1 and 10 workers). The fix is the counter.

## Open for the owner

1. **The adjacent-lens ruling** — coffee frog, Buenos Aires estancia, Antalya
   nomadic tents. Does "delightful/interesting" count as uplifting, or must
   uplifting have a benefit that reached people? One ruling covers the class.
2. **#104** — every accuracy number is CPU-measured; production serves on GPU.
3. **gpu-server's disk ceiling** is host-side (LXC on a 207 G rootfs).

## Corrections I made to my own claims today

- The verification criterion (above).
- **The 04:00 cycle did not fail.** I inherited and repeated a warning that the
  Odido maintenance would kill it; it ran at 04:52 and completed cleanly.
- I was about to recommend `urljoin` for the og:image relative URLs as a 2.6×
  win. Checking the hosts first showed all 51 were arxiv logos.
