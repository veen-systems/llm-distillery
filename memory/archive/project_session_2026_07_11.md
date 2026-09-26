# Session 2026-07-11 — "ovr shows no new nature articles" → normalization cold-start (diagnosis + doc gap closed)

Diagnostic session. User reported ovr.news hadn't shown new nature articles since the
nature_recovery v4 deploy (2026-07-10). Traced end-to-end; **nothing was broken** — the
finding reframed the premise and exposed a real process gap. No filter code/config/model
changed; doc-only. Branch `nature-recovery-v4`.

## What was actually happening (the reframe)

1. **Scoring side healthy.** Scorer resting cleanly (`Result=success`, `NRestarts=0`),
   pipeline running every ~4h, v4.0 producing MEDIUM+ output (~3–4 genuine raw≥4.5/batch).

2. **v2's "fuller" feed was ~90% inflation.** v2 shipped a fitted percentile
   `normalization.json`; that CDF mapped raw≈2.0 (tier=**low**, no recovery evidence) up to
   normalized 5–7, padding the ovr Recovery tab with ~10–17/batch. v2's *genuinely-strong*
   articles (raw≥4.5) were only **0–2/batch** — fewer than v4's 3–4. So v4 surfaces MORE real
   recovery signal; the tab only *looks* emptier because the padding is gone.

3. **Why "no NEW articles" specifically.** ovr `article_filter_scores` still holds v2 rows
   (articles scored once at harvest) on the inflated scale; v4 rows are on the raw scale.
   ovr ranks the shared feed by `weighted_average` (`ranking.ts`), so still-in-window inflated
   v2 rows **out-rank** fresh v4 rows → new v4 articles buried, not absent.

4. **Self-corrects, no action.** Age-out is on `published_date`, 10-day window
   (`db-articles.ts:250`, `maxAgeDays:10`). Last v2 batch Jul 9 → inflated rows drain by
   **~Jul 19**; decay (`0.95^age`) + fresh-article recency boost tip it toward v4 daily.
   Destination = honest v4 steady state (~3–4/batch). Fuller tab = v5 recall lever (#71),
   NOT a normalization fix.

## The mechanism (root cause)

A fresh version correctly ships **no `normalization.json`** (ADR-014 forbids reusing the old
CDF). So `production_scorer.py` emits RAW `weighted_average` while every OTHER lens emits
*normalized* scores. Two ovr mechanisms then mis-handle the raw filter:
- cross-lens assignment (`canonical-lens.ts` — highest `weighted_average` across scorers wins the lens),
- uniform display gate (`ranking.displayScoreThreshold: 4.5`, calibrated for normalized scores).
Both under-rank / under-show the raw filter until ≥200 production MEDIUM+ accrue — **weeks** for
a needle (nature ≈ 0.3% MEDIUM+).

Attempted "fit now": blocked by design. `production_scorer.py`'s `MIN_NORMALIZATION_ARTICLES=200`
guard silently rejects thin fits (only 33 v4 MEDIUM+ prod articles exist; a 33-article CDF over-
inflates by construction — the exact v2 bug). Fitting on raw≥1.5 to game the count would recreate
the inflation. Removed the inert 33-article file I generated.

## The process gap (user's insight — correct)

We have the data to fit normalization **at deploy time** by rescoring a *production-representative
historical* corpus (FluxusSource `~/local_dev/FluxusSource/data` 1.2 GB; 100K+ NexusMind filtered
articles) — no weeks-long wait. It wasn't in the runbook because the playbook conflated "don't use
*enriched* training/val data" (true, §2) with "wait for ≥200 *live production* articles" (unnecessary);
nobody drew the "historical production data is fine and available now" path. Caveat: must be at the
production base rate (~145K articles for 200 MEDIUM+), NOT the enriched set.

## Docs changed (this session, uncommitted at write time)

- `docs/FILTER_PLAYBOOK.md` §6 — new cold-start pit + deploy-time historical-rescore fix; §8 line 83
  + checklist item 7 cross-reference the deploy-time option.
- `docs/RUNBOOK.md` — new "Fit normalization" operational subsection (command + `MIN_200` /
  base-rate guards) + lifecycle Phase 9 note.
- `memory/gotcha-log.md` — "Fresh-version normalization cold-start starves the ovr feed (2026-07-11)".

## Also noted (not actioned)

- Deploy scripts (`deploy_to_nexusmind.{sh,ps1}`) still carry stale `C:/local_dev/` Windows paths;
  user confirmed all machines (situla/sadalsuud/gpu-server) are Linux now. Porting still pending
  (already tracked in playbook §8 line 85).
- Normalization buys cross-lens *fairness*, not volume — worth fitting for nature v4 via historical
  rescore when desired (user chose "doc the gap only" for now).

## Open follow-ups (unchanged + one new)

- **#72** — v4 normalization: now has a faster path (deploy-time/anytime historical rescore) instead
  of waiting ~2 weeks for 200 live MEDIUM+. Fit on `--min-score 3.75 --filter-version 4.0`.
- **#71** — v5 recall (the actual lever if the Nature tab should be fuller).
- **solutions v4** (#43) prompt drafting — unchanged primary.
