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

---

## ⛔⛔ ADDENDUM — the enablement took the pipeline down (written after the sections above)

Everything above was written before the first post-enable cycle produced numbers. It did, and
they were bad.

**The 12:10 cycle ran the SHARED preprocessing stages 7–10× over normal** — og:image backfill
21,245 pages against a 2.6k–3.1k baseline, hero image extraction **41,435** against 3.3k–4.0k,
ML candidates 18,206 against a 3,000 cap. It hit the og:image stage's own 3,600s budget (dropping
5,203) and was on course to exceed `TimeoutStartSec=4h` **before scoring started**: a SIGKILL
with zero filtered output for **all six filters**, not just the new one.

**Cause — a cold start, not the prefilter.** NexusMind skips articles listed in
`data/raw/.processed_ids_<filter>.json` (`scripts/main.py:1565`). A new filter has no such file,
so it loads every article inside `max_article_age_days: 3` — ~18 collection cycles, ~41,400
against the observed 41,435. Private to the new filter, except dedup and image analysis run once
on the **union** of every enabled filter's pool (`:3555-3567`).

⛔ **And it does not self-heal.** `_save_processed_ids` is at `:2141`, after the per-filter
scoring loop. A kill before scoring leaves the file unwritten and the next cycle rebuilds the
identical pool — a kill loop every 4h until someone intervenes.

⭐⭐ **The keeper, from the `nexusmind-0a` session: THE COST AND THE THING THAT WOULD END IT ARE
ON OPPOSITE SIDES OF THE SAME TIMEOUT.** Generalised: *a one-time cost whose receipt is written
only on success is not one-time — it is a loop.* Look for it wherever a first run is expensive
and its completion marker is written at the end.

⭐ **Two mechanisms fitted the same 10×; only one survived reading the code.** The peer's leading
hypothesis was that v8's ABSENT PREFILTER widened the candidate set — it fits the magnitude just
as well and is wrong: that path consults no prefilter. Registered as `H-V8-27` with the rival kept
in the row, because the refuted one is the instructive half.

**Mitigation (peer session, owner-authorised, 15:27–15:28, NOT me):** stop the unit, copy
`.processed_ids_uplifting.json` → `.processed_ids_human_thriving.json`, `reset-failed`. ⭐ **My
contribution was the one detail that changed their command**: copy WHOLESALE. The `versions`
sidecar is `{id, content_hash, collected_date}`, the superseded-rows mechanism (#119), and it is
filter-agnostic corpus data — copying only `ids` would have silently disabled change detection
for v8 across the whole 3-day window. ⚠️ **That seeded file is the mitigation, not a stray
artifact: deleting it restores the outage.**

**I stood down** and did not touch sadalsuud once my user said the peer was handling it — two
sessions acting on one production host is its own failure mode.

## ⛔ THE ACCEPTANCE TEST IS UNREAD — first action next session

At 15:41 the unit was `inactive dead` and the next collection was 16:04, so no post-mitigation
cycle had run. **The diagnosis is consistent with the evidence and not yet confirmed by it.**

```bash
ssh sadalsuud 'cd ~/local_dev/NexusMind && \
  grep -E "og:image backfill: fetching|Hero image extraction:" logs/nexusmind.log | tail -2; \
  cat data/filtered/human_thriving/*.jsonl 2>/dev/null | wc -l'
```

PASS: og:image **2.6k–3.1k**, hero **3.3k–4.0k**, and `human_thriving` rows appearing.
⛔ **FAIL on either ⇒ the cold start is not the whole story**: back `human_thriving` out of
`pipeline.enabled_filters` and redeploy (that is llm-distillery's path, i.e. mine), and
re-diagnose rather than guessing a third mechanism.

## What today's two misses have in common

**I verified the thing I changed, not the system around it — twice, one layer apart.** First:
the package deployed and the scorer could score, but nothing called it (`enabled_filters`).
Then: the filter was enabled and would score, but I never asked what its FIRST cycle would cost.
Both passed every gate that existed. `working-rules.md` 21st occurrence covers the first; the
second is now `docs/RUNBOOK.md` § 4b and **#152**.

⚠️ **v8 has still never scored a production article.**
