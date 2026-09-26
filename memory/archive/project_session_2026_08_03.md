---
name: project_session_2026_08_03
description: "Session 2026-08-03 — #93 length-floor split shipped + synced to NexusMind; #95 found and quantified (batch-shape score noise flips 7-9% of near-boundary surfacing decisions); investment_risk LD↔NM drift resolved"
metadata: 
  node_type: memory
  type: project
  originSessionId: 34137b07-48ad-4310-8209-0ff8bc8e6728
  modified: 2026-08-03T14:25:20.252Z
---

# Session 2026-08-03

Two shipped, one found. The found one is the bigger deal.

## 1. #93 — the length floor is no longer a gate

`4d17e75` + `23732c3` (LD), synced to NexusMind in `c932065`/`c1df13c`.

Split three ways per ADR-022: the 300-char floor is a **labelling-time**
precondition in `make_oracle_prefilter()` (framework leakage is a property of
the oracle *prompt*; the student sees none), content length is **stamped** on
every scoring result, and there is **one** config-gated `short_content.cap` —
set on no filter, because #92's solutions DiD is still confounded.

Verified by A/B over 2,917 production rows: oracle verdicts **byte-identical**
for five of six filters. The zeros are structural — every rule ANDs into the
verdict, so hoisting one out can move the reason string but not the boolean.

**cultural_discovery is the intended sixth.** Its custom `apply_filter` never
called `check_content_length` (a v3→v4 regression in its own docstring), so cd
was the only filter whose *labelling* path had no floor. Hoisting restores one:
190/474 ≈ 40% of what cd would have sent to the oracle, on a corpus deliberately
skewed short (66% sub-300). Production-realistic share is lower and
**unmeasured**. Pinned by a test. **Re-measure before the next cd oracle run
(#87).**

## 2. #95 — a score is not a function of the article alone

Found while smoke-testing #93 on gpu-server; **not caused by #93** (measured
with every #93 line inert). See [[score-batch-shape-noise]].

Same article, same weights, same process — only `batch_size` differs:

| filter | op-point | in ±0.30 band | flipped | share |
|---|---|---|---|---|
| solutions v6 | 2.252 | 28 | 2 | **7.1%** |
| uplifting v7 | 4.0 | 33 | 3 | **9.1%** |

Max |Δ| 0.162, mean 0.004. Under ADR-022 visibility is `raw >= op-point`, so
these are **surfacing** flips. Aggregates (MAE, DiD, calibration) are safe;
threshold tests are not. **The queued #92 second-op-point re-run is directly
exposed** — pin `batch_size` for it.

## 3. investment_risk LD↔NM drift, resolved the right way

`e51309d`. NexusMind blocked `arxiv`/`mastodon_`/`bluesky` since 2026-05-18;
llm-distillery never did. So the oracle labelled a population production never
scores. A blind LD→NM sync would have **deleted** all three — found only by
diffing first. Ported back to LD instead.

**Rule: diff both copies before every sync.** `.nexusmind-owns` is empty, so
nothing else compares them.

Also corrected a NexusMind MEMORY.md row claiming `filter_base_scorer.py` +
`hybrid_scorer.py` are "NexusMind-owned — do NOT sync", which contradicted LD's
CLAUDE.md and was contradicted by the files: byte-identical before the sync, so
the rule had protected nothing.

## 4. Reader-reported defects — one complaint, three repos, none of them ovr.news

The owner reported four bad articles on ovr.news. Investigation split them into
three defects, each filed where the fix lands. **This is the concrete instance
of the owner's own observation that "a bug is often better fixed from the
original repo".**

- **NexusMind#290** — hero extraction publishes a *Google Play badge* as the
  article image. **Reproduces on current code with NM#287 in place**; nothing
  rejects an image from a foreign host. Compounded by `hero_validation_cap: 200`
  vs ~968 heroes/run → ~79% unvalidated, so the same defect shows a badge on one
  article and nothing on another. Visibility is a lottery; the defect is not.
- **NexusMind#291** — cross-source dedup threshold **0.88** vs **0.8355**
  measured for a confirmed same-story RU/ES pair (`multilingual-e5-large`,
  title-only, `"query: "` prefix). Then: the Egyptian-princess repeat the owner
  remembered is real — **four** articles over ten days, including **two with
  byte-identical titles from different sources**, which cannot fail a 0.88 bar.
  So dedup has a fault that is *not* the threshold. Left explicitly unresolved.
- **FluxusSource#124** — UTF-8→MacRoman mojibake at collection. **463/9,343
  articles (5.0%)** in one day, concentrated in `baltic_lrt`/`spanish_*`/
  `vietnamese_*`/`german_*`; English essentially unaffected, so English-only
  spot checks never see it.

**Two of my hypotheses were measured and refuted in this investigation** — see
the gotcha entries. Ordering note recorded on ovr#287: re-extracting the
already-published wrong images would faithfully reproduce them until #290 lands.

## Process notes

- **Two sessions wrote to the NexusMind tree at once.** `c932065` — message
  "docs: correct NM#287 status" — swept in my seven-file filter sync via
  `git add -A`, and was pushed before I could describe it. Content correct,
  attribution wrong; recorded in `c1df13c` rather than rebased, since it was
  already public. **When a parallel session may be active, stage explicitly.**
- **A stubbed smoke test is worth running, and worth not trusting too far.**
  The workstation run (transformer stubbed, no weights in cache) passed 20/20
  and caught nothing. The gpu-server run with real weights failed one check —
  which turned out to be #95, not a #93 defect. Real weights earn their cost.
- **My failing test was asserting something the platform doesn't provide**
  (single-vs-batch numerical identity at 1e-6, against 8.6e-3 of real noise).
  Fixed by checking each path against its own baseline.

## Next session

1. ~~Deploy filters to gpu-server~~ **DONE 2026-08-03 ~15:45 CEST** via
   `scripts/remote_deploy.sh`. Revision hash matched local↔remote
   (`2d5c54aa…`), scorer healthy, 6/6 smoke tests in range, push completeness
   verified. **Verified at n=1 per filter** — the real check is the next cycle.
   <!-- verify: N=$(ssh -o BatchMode=yes -o ConnectTimeout=10 gpu-server 'grep -c _apply_short_content_cap ~/NexusMind/filters/common/hybrid_scorer.py' 2>/dev/null) || { echo "CANNOT VERIFY: gpu-server unreachable"; exit 0; }; if [ "$N" = 1 ]; then echo "PASS: _apply_short_content_cap occurs $N time"; else echo "count is $N, expected 1"; exit 1; fi -->
2. **Re-run the NM#284 shadow on a real cycle** — pass rates finally describe
   lens behaviour, not a length floor (LD#90 item 2). **Rates measured before
   2026-08-03 are not comparable to ones after.** First cycle carrying this
   code: 16:10 CEST 2026-08-03.
   Also confirm the 6 filters score normally at full batch size, not just at
   the n=1 smoke.
3. **#95: pin `batch_size` in the production scorer**, then record the noise
   floor in the ground-truth gate and NORMALIZATION_METHOD.
4. #92 second op-point (with batch_size pinned) → only then fit a solutions cap.
5. cd labelling-floor decision before the next cd oracle run (#87).
6. ~~NM#287 hero fix unobserved~~ **OBSERVED** — 12:48 cycle logged
   `by source: data-original=4, data-src=44, src=920`. 48 lazy-loaded heroes
   recovered that the pre-fix code could not find. The fix works; NM#290 is a
   *different* defect in the same subsystem.
7. **NM#290 before any ovr#287 backfill** — re-extracting now would faithfully
   reproduce the wrong images.
8. **NM#291: settle the identical-title pair first.** If those two clustered,
   the threshold work stands; if they did not, the threshold is the wrong thing
   to tune. Needs the post-dedup artifact — `filtered_*.jsonl` has
   `cluster_id: null` for every row by construction.
9. **Issue hygiene**: ovr.news engineering view is now
   `-label:positioning -label:outreach -label:community -label:content` (55, not
   81). NexusMind (25 stale) and llm-distillery (15 stale) have **not** had the
   same pass — and being engineering-only repos, they will not split the same
   way.

## Related

- [[project_session_2026_08_02]] — the session whose queue this one worked
- [[score-batch-shape-noise]] — #95 in detail
- [[prefilter-length-floor-hypotheses]] — updated with what shipped

---

# Evening session (same day, separate context)

Full detail in the repo: `memory/project_session_2026_08_03_evening.md`.

**Four shipped, two deployed.** Commerce provenance fix (NexusMind `c696ea3` —
86.4% of corpus rows had a verdict with no model version, guard keyed on
`_commerce_score` alone); seeded per-run shuffle (NexusMind `f7fef85` — cycles
are now replayable via `NEXUSMIND_RUN_SEED`); #95 noise floor recorded
(LD `efab69d`); sustech v3 + foresight v1 packages removed (LD `289bda1`,
archive on sadalsuud). NM#292 filed, LD#64 closed.

**All three junk gates verified against the running box, not config.** Obituary
enforcing — max score among 14,572 survivors is 0.8488, zero at or above 0.85.
Commerce enforcing, LD#80 `v1` pin intact. Violence inert by design.

**Corrected mid-session:** I recommended pinning the batch size; it was already
pinned (`DEFAULT_BATCH_SIZE = 16`). The real variable was an unseeded
`random.shuffle` in NexusMind's `scripts/main.py`. Seeding buys **replay, not
stability**.

**#90 not ready.** Both `nature_recovery v4` and `solutions v6` already passed
ground-truth gates (F1 0.736 / 0.739), so "do they work?" is answered. Open
question is which template elements are load-bearing — #94 and #92 say at least
two of the six #90 proposes copying do nothing.

**Owner feedback:** chat answers were too dense. Rules now in the repo's
CLAUDE.md ("How To Write Answers Here"); see [[feedback-plain-answers]].
