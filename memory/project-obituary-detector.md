---
name: project-obituary-detector
description: Obituary detector — ENFORCEMENT LIVE v5@0.85 (recall-first), carryover washout ~Aug 13, v6 relabel parked (LD#85); architecture, key numbers, validation harness
metadata:
  type: project
---

## Status

**ENFORCEMENT ON — v5 @ 0.85, owner-signed-off 2026-07-30 ~19:50 (NexusMind
`b904edc`, after the 0.92 shadow swap `89f3c58` same evening).** Owner
directive: RECALL-FIRST — "I don't mind stuff getting blocked that is not
strictly obituary… I just hate obits coming through." Over-blocking
death-adjacent news = accepted collateral; this supersedes the precision
framing of the review battery for OPERATING decisions (the adjudicated rule
still governs v6 LABELS, LD#85). 0.85 catches all 21 gate obits + Farouq;
drop happens in the dedup gate (`obituary_blocked`, after commerce, mirrors
it), config-gated: rollback = `pipeline.obituary_detector.enforce: false`.
Stamps always written. Lens scoring is NOT a backstop (verified: 102
obit-flagged rows passed lens thresholds in the 16:00 cycle, mostly
belonging). **VERIFIED LIVE 2026-07-30 20:12 cycle**: Loaded line shows **1158 obituary**
blocked (vs 5415 commerce); gpu-server health lists `obituary_detector_v5`
(hash gate passed). <!-- verify: ssh sadalsuud "journalctl -u nexusmind.service --since today --no-pager | grep -m1 ' obituary,'" -->
**Overnight sanity check PASSED 2026-07-31**: blocked count 1158 (20:12) →
1208 (00:17) → 1249 (04:14), ~40-50 new/cycle ≈1% of loaded; v5 hash-verified
each cycle; 26 new flags in `content_items_20260731_041042.jsonl` <!-- placeholder --> all stamped
`_obituary_model: "v5"`. Spot-read: high band = clear obits; 0.85–0.95 band =
death-as-news collateral (accepted per recall-first) + 2 alive-person
survival-story over-blocks (0.893, 0.937 — known v5 failure class, no owner
action per parked LD#85). ovr#204 handoff comment posted (issuecomment-5139810271).
<!-- verify: ssh sadalsuud "journalctl -u nexusmind.service --since '2026-07-31' --no-pager | grep -m1 ' obituary,'" -->
Note: gpu-server:8000 is DOWN between cycles by design (static unit, started
per cycle, ExecStopPost restarts ollama; gpu-server logs are UTC = local−2).

**Re-verified 2026-08-06** (first run of these assertions since 07-31; they had
slipped three curate passes). Blocked count still climbing monotonically:
1208 (Jul 31 00:17) → **2573** (Aug 6 08:18), 234 Loaded lines in the window,
no gap. Rescore reproduced the 07-31 numbers to 4 decimals on both articles —
Alonso v3 0.2838 / v4 0.1954 / v5 0.2766, Devos v3 0.6817 / v4 0.4376 /
v5 0.1218 — so the two live v5 FNs below are still exactly as characterised,
and the 0.4376 production stamp reproduces.

**2026-07-31 owner obit sighting on ovr.news — diagnosed, NOT an enforcement
failure.** Of 133 post-enforcement articles: zero obits (enforcement works).
But **47 obit-flagged shadow-era carryovers (all ≥0.85) are live on the site**
— shadow stamped, never dropped; the ovr `live_articles` view is **14 days by
published_date**, so washout runs to ~**Aug 13** (not Aug 6 / max_age 7d —
that governs only the NexusMind pipeline). ⚠️ **The washout date was derived
from the wrong object** (noted 2026-08-16): `live_articles` is legacy and off
the build path; the site's window is `ranking.maxAgeDays` via
`getArticlesForBuild`. Both were 14 days at the time, so the Aug 13 conclusion
is believed unaffected — **but it was never re-derived against the build query,
and the two windows are independent settings that can diverge.** Purge list posted on ovr#204
(issuecomment-5139853211). Plus **2 true v5 FNs live**: Teresa Alonso obit
(v3 .284/v4 .195/**v5 .277** — biography-rich obit reads as history) and Yves
Devos mourning piece (v3 .682/v4 .438/**v5 .122** — v5 REGRESSED on the
community-mourning class, likely v4 hard-negative legacy-tribute pull).
Rescore reproduced the production stamp exactly (0.4376). FN-class evidence
for LD#85 if the owner calls the sighting a reactivation trigger.
<!-- verify: manual — rerun the rescore on gpu-server with `~/gpu-server/nexusmind-scorer/venv/bin/python /tmp/rescore_obit.py`, inputs `/tmp/obit_recheck.jsonl`. Both live in /tmp and will not have survived; regenerate them first. Was silently ERRORing as an inline command because of the trailing parenthetical. -->

**Owner verdict on carryover (2026-07-31): "it is what it is" — no purge, no
LD#85 reactivation; let it wash out.** ovr-side session independently verified
enforcement AND measured the downstream effect: belonging death-pattern rate
**7.9% pre-enforcement (220/2769) → 2.9% post (1/35)** — first
past-the-boundary measurement (keyword proxy, so 2.9% is an upper bound).
ovr editorial gate retired entirely 2026-07-30 (permanent). ovr sentinel
re-derivation (~5%, not 2%) scheduled after Aug 6. Three washout windows —
QA sentinel (3d published) ~Aug 2-3; pipeline max_age (7d) ~Aug 6; site
live view (14d) ~Aug 13 — reconciled on ovr#204 (issuecomment-5139876852).
Transitional note: articles stamped during the 0.90/0.95 shadow eras keep
their old `_is_obituary` flags (preprocessor skips already-scored rows), so
the 0.85–0.90 band only blocks for newly scored articles; washes out within
max_age_days (7d). Next: ovr#204. **LD#85 (v6) PARKED indefinitely (owner 2026-07-30)** — reactivate on an owner obit-flag or visible over-blocking harm; nothing else.

**Owner adjudication 2026-07-30 (14/14 rows)**: boundary = grief/mourning
content (block: funerals any angle, memorial events, mourning tributes any
age) vs death-as-news (keep: accidents/crime/investigations — "none of those
are obituaries"; not the violence filter's job either — that's promotion/
glorification). Flips BOTH clauses of sharpened-broad. Worksheet with
verdicts: `adjudication_worksheet_2026-07-30.md`. Feeds LD#85 (v6 relabel).

**b650 training env READY** — see `memory/b650-gpu.md` (all machine facts + gotchas).

## History 2026-07-30

Superseded strata (v5@0.92 shadow era, June-increment panel pre-recall-first framing, v5 training/eval detail incl. corrected excl-24 table, v4@0.90 deploy, FN-delta gate failure) archived 2026-07-31 context audit → [[project_session_2026_07_30]] "Archived obituary history strata" section. Status above is current; v5 eval artifacts live in `filters/common/obituary_detector/validation/artifacts/`.

## What it is

Multilingual obituary/death-memorial classifier: frozen `paraphrase-multilingual-mpnet-base-v2` → StandardScaler → sklearn MLP(256,128) → predict_proba. Blocks obituaries upstream of lens scoring in NexusMind. Same architecture as commerce_prefilter v2.

## v3 key numbers

- **Training:** 11,295 rows (2,672 positive, 23.5%), DeepSeek oracle, sharpened-broad labeling rule
- **June holdout (temporally disjoint, leakage-free):** 0 FPs at ≥0.95 (0/58), precision 1.0 excl-split
- **Recommended op-point:** 0.95
- **Model artifacts:** gpu-server `~/llm-distillery/filters/common/obituary_detector/v3/models/` (mlp_classifier.pkl + scaler.pkl)

## ovr.news investigation (2026-07-27)

Scored 203 ovr.news Phase-1 borderlines with v3 MLP:
- **186/203 (91.6%) score <0.50** — model is confident these are NOT obituaries
- **3/203 (1.5%) at ≥0.95** — all false positives: historical legacy/tribute pieces in Greek/Spanish/Chinese
- **1/203 at ≥0.90** — Bharathiraja tribute (true positive, recent death June 2026)
- **Bottom line:** v3 generalizes well to ovr.news. The Phase-1 concern about over-blocking was driven by a different model (Claude screener), not the v3 MLP.

## Dependency chain

LD#51 (train v3) ✅ → LD#77 (ovr.news validation) ✅ → NM#185 (shadow deploy) ✅ → v4 retrain ✅ → v5 retrain + **ENFORCEMENT v5@0.85** ✅ 2026-07-30 (LD#83 CLOSED) → ovr#204 (ovr-side handled: hardcoded filter removal in progress, editorial gate retired) → **chain COMPLETE** — only LD#85 (v6 relabel) remains, parked.

## v4 corrective retrain (EXECUTED 2026-07-28)

12 hard negatives added to training (11,295 → 11,308 rows):
- 8 ovr.news production FPs (legacy/tribute pieces in Greek/Spanish/Chinese)
- 4 heldout panel-confirmed FPs (crime/accident reports)

**Results at threshold 0.95:**
- All 12 FPs score <0.65 (max 0.65, most <0.15)
- Heldout precision: **0.977** (v3: 0.973), FP count: **5** (v3: 7)
- Heldout recall: **0.608** (v3: 0.744) — tradeoff from added conservatism, not a concern for shadow mode
- Bharathiraja TP: **0.954** (v3: 0.913) — stronger

Artifacts: `filters/common/obituary_detector/v4/models/` (mlp_classifier.pkl + scaler.pkl). Same architecture, drop-in replacement for v3.

### Old v4 plan (pre-execution, kept for reference)

(Superseded — executed 2026-07-28, see above.)

## Production flag 2026-07-29 (v3 TP, v4 MISS at 0.95)

Owner flagged `arabic_thearabweekly_d056412bf8cf` ("Farouq Hilal, the last guardian of Iraq's musical taste") via ovr.news flag API — a memorial for a recently deceased person, i.e. a true obituary per the labeling rule.

- **v3: 0.977** → caught (shadow stamped `_is_obituary: True`; reached the site only because shadow mode doesn't drop)
- **v4: 0.937** → **below the 0.95 op-point — v4 would MISS it.** The recall tradeoff (0.744→0.608) biting on a real production case. (Verify: rescore the gitignored worksheet below with v3+v4 models on gpu-server — same embed+scale+predict_proba as `validation/score_borderlines.py`.)
- v4 OOF sweep (`v4/calibration_report.json`, threshold_sweep) says 0.90 threshold ≈ v3-level recall (0.749) at precision 0.916 (vs 0.927 at 0.95) — and 0.90 catches this article. But the OOF numbers are oracle-label-based; the heldout check at 0.90 came next (see Resolution below).

**Resolution (2026-07-30): v4 promoted at op-point 0.90.** Evidence:

- Heldout sweep (1,562 rows; verify: `ssh gpu-server "wc -l ~/llm-distillery/filters/common/obituary_detector/training/data/heldout_corpus.jsonl"`): v4's 5 FPs at 0.90 are the *identical set* as at 0.95 (all score ≥0.95) — the threshold drop costs zero heldout FPs and recovers recall 0.608 → 0.683. v4@0.90 beats v3@0.95 on precision (0.979 vs 0.973) at −6pt recall. Caveat: heldout labels are DeepSeek-oracle, and the 5 surviving FPs were never independently panel-checked (the panel budget went to the new 0.90–0.95 band).
- 4-model blind panel on the June-holdout marginal band [0.90, 0.95), n=37: **35/37 majority-obituary** (band precision ≈0.946). 1 FP (crime-report class), 1 split. phi4:14b dropped out mid-run (ollama down — pipeline had started on gpu-server); 3-lab majority for most rows.
- Artifacts: `validation/artifacts/v4_oppoint_check_2026-07-30.json`, `grades_panel_v4_band_2026-07-30.jsonl`. Farouq article (gitignored): `validation/artifacts/worksheet_ovrnews_flagged_2026-07-29_farouq.jsonl`.

NexusMind `02da4fe`: v3→v4 swap + threshold 0.90, still SHADOW, committed+pushed but not deployed (see Status). Sequence: deploy → smoke test → one shadow cycle → FN-delta check (owner gate, see Status) → owner sign-off → enforce → ovr#204.

The issue's original "FN just wastes 5ms" framing was wrong — an FN is an obituary on the site (that's what the owner keeps flagging); recall is the product metric, FP-precision is the safety constraint.

## Validation harness

All scripts in `filters/common/obituary_detector/validation/`:
- `score_borderlines.py` — score articles with v3 MLP (needs gpu-server for sentence-transformers)
- `panel_obit.py` — 4-model blind panel (gemini + gemma3:27b + qwen3:14b + phi4:14b)
- `panel_audit_deepseek.py` — 3-lab Ollama audit of DeepSeek oracle
- `rollup_obit.py` — panel-majority vs model, block precision
- `relabel_deepseek.py` — DeepSeek oracle labeling (resumable)

Key artifacts in `validation/artifacts/`:
- `v3_june_validation.json` — temporally-disjoint June holdout (0 FPs)
- `v3_heldout_validation.json` — in-corpus heldout (3 FPs at ≥0.95)
- `worksheet_ovrnews_scored_2026-07-27.jsonl` — 203 ovr.news borderlines with v3 scores (gitignored, content)
- `ovrnews_phase1_borderlines_2026-07-16.jsonl` — 203 borderlines with Claude model_verdict
- `grades_panel_ovrnews_2026-07-21.jsonl` — Claude 3-model panel on 66 borderlines

## NM#185 handoff

What NexusMind needs:
1. Copy v3 model artifacts from gpu-server
2. Wire into prefilter pipeline (same pattern as commerce_prefilter v2)
3. Shadow-deploy: stamp `_obituary_score` / `_is_obituary`, log would-block, drop nothing
4. Run for ≥1 production cycle, collect flagged articles
5. Report back: how many flagged, any obvious FP patterns beyond the 3 we know about

The commerce_prefilter v2 integration is the template — same artifact contract (mlp_classifier.pkl + scaler.pkl), same inference pattern.

## Labeling rule (owner-endorsed 2026-06-14)

- **Block (obituary):** fresh obituaries / death notices / mourning pieces whose PRIMARY purpose is to mark a specific person's recent death.
- **Keep (not_obituary):** memorial events, anniversary/commemoration pieces, legacy tributes, laws/programs prompted by a death, profiles of the living, any story that merely mentions death.
