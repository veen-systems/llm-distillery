# Session 2026-09-07 — human_thriving v8 deployed, enabled, and the deploy that called nothing

**Spend $0.** No oracle calls, no training. One ~95-min-equivalent of GPU time: none — all
inference was existing dumps plus a handful of production scoring requests.

**Commits (llm-distillery):** `006b87d`, `893ec5f`, `62d2089`, plus this session's curate commit.
**Commits (NexusMind):** `a5aab4e` → PR #452 (`e0f0af9`), `718b4e1` → PR #453 (`9245f2c`).
**Issues filed:** #150 (junk-gate layer), #151 (cutover scope). **Commented:** #147.
**Experiment:** EXP-028. **Hypothesis:** H-V8-26.

## What shipped

`human_thriving v8` is deployed AND enabled. Route: adapter b650 → Situla → gpu-server, sha256
`074209ff…` read back at all three hops, 0 of 3 differed. Hub backup
`jeergrvgreg/human-thriving-filter-v8` (private), `--selected-epoch 5` so the card carries epoch
5's metrics and not `training_history[-1]`'s epoch 6. `inference_hub.py` written fresh and
`NO_HUB` deleted in one commit — the parked scratchpad copy from a previous session was gone,
which cost nothing because the module needed re-verification in the tree either way.

Verified by execution at every step that mattered: adapter key format (364 OLD-format
`.lora_A/B.weight`, 0 `.default.`, ADR-007), `verify_filter_package.py --check-hub` 9/9, the Hub
path scoring a real article, and finally `POST /filter/human_thriving/score` on gpu-server.

## ⛔⛔ THE KEEPER — I deployed a filter that nothing called

PR #452 passed every gate and I published "live in production". `human_thriving` was never added
to `pipeline.enabled_filters` — the list `scripts/main.py:2569` iterates — so no 4h cycle would
have touched it, `data/filtered/human_thriving/` would have stayed empty **forever**, and Phase E
normalization (which fits its CDF from that directory) could never have run.

⭐ **I tested the callee and inferred the caller.** The outcome check I ran deliberately, to
satisfy the working rule, answered "can it score when asked?" — not "does anything ask it?".

⭐⭐ **What found it was not a check but writing an unrelated fixture.** Adding the missing smoke
row forced a read of `deploy_filters.sh`'s fixture-name alignment gate, which requires every
fixture's filter to be in `enabled_filters`. **The gap was invisible to everything green**: the
post-deploy smoke suite passed through the entire deploy having never loaded v8, because it had
no fixture for it. ⚠️ A NEW filter has an enablement step a version upgrade does not, and every
guard in the chain was built for the upgrade case. 21st occurrence in `working-rules.md`.

## EXP-028 — precision under the production mix

The gate's precision 0.550 is the PANEL's, on a 25.1× design-weighted draw (positive rate
5.3030% unweighted vs 3.1638% weighted). Horvitz-Thompson weighted the shipped calibrated arm
reads **precision 0.6073** (band [0.5524, 0.8159]), **specificity 0.9941**, recall 0.2779 — the
weighting was expected to HURT precision and helped it, because the FP rate falls 1.44% → 0.59%
and that more than cancels the lower base rate. ⚠️ The bands overlap, so this is not a
distinguishable difference; what it establishes is that the reader-facing number does not get
worse off the panel. `H-V8-26`, REFUTED as stated.

⭐ Second result: under that mix the calibrated arm's specificity beats raw's with **disjoint**
bands (0.9941 [0.9933,0.9974] vs 0.9898 [0.9865,0.9915]) while their precision bands overlap —
an argument for calibration on ADR-023's own criterion, invisible to `calibration_report.md`
whose verdict is stated in MAE.

⭐ The control is the point: the script computes the UNWEIGHTED arm through the same join and
refuses to publish unless it reproduces `ground_truth_gate.json` cell-for-cell.

## Corrections made to already-published numbers

- `CLAUDE.md`'s ADR-023 bullet still published v8's **superseded epoch-4** gate (0.343/0.992).
  Corrected to 0.314/0.9856.
- "the #95 band on specificity is 3 to 8 false positives" in `memory/MEMORY.md` and the 09-06
  session file was the epoch-4 arm's band (fp 5, −2/+3). Epoch 5 is fp 9, −4/+1 → **5 to 10**.
- `check_claim_shapes.py` rejected this session's own README: "calibrated beats raw on BOTH
  criteria" ordered two measured quantities with no band. With bands only the specificity
  ordering survives. **A guard caught my overclaim before commit.**
- I told the NexusMind peer that ovr.news names `uplifting` in 8 files; it is **12**. My grep's
  `--include` dropped `.astro` and `head -15` cut three more. The peer was right.

## Cross-session work

Messaged `nexusmind-0a` (running 21h) about the deploy and the `app.yaml` change. It replied
that it had recorded *"do not flip `enabled_filters`"* in its own `memory/decisions.md` BEFORE my
message — which would have told the next session to block PR #453, the additive change v8 needed
to score at all. It corrected the row and added a probe that fails if `enabled_filters` ever
loses `uplifting`. ⭐ **The coordination caught a defect neither session's own checks would
have.** It also flagged a possible stale CI base on #453; checked and refuted — all six of its
dependency merges are ancestors of my base `e0f0af9`, and the CI run's headSha equals the PR head.

## Open, for the next session

1. ⛔ **Unconfirmed: no production cycle had run.** Deploy ~09:50 CEST, next `fluxus-collection`
   12:04. Check `data/filtered/human_thriving/` FIRST. **Do not treat the config key as the
   answer — that is exactly what went wrong today.**
2. Phase E normalization once ≥200 rows sit above 4.5.
3. The ~50-article production hand-audit — the only precision measurement on the population that
   matters, and the requirements-gathering for #150.
4. #151 — the cutover, blocked on 12 ovr.news files, a fitted CDF and an owner ruling
   (Jaccard 0.246: v7 and v8 do not share a positive class).
