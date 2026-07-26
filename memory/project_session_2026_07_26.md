# Session 2026-07-26 — Multi-repo triage, wrap-up, curate

**Branch:** main (clean). **Spend: ~$0** (review/triage only).

## What happened

Session was a multi-repo review and triage pass. No code changes — this was a planning/prioritization
session surveying the full issue landscape across llm-distillery, NexusMind, ovr.news, and FluxusSource.

### Context carried from July 22 evening

Two post-wrap-up doc corrections landed on 2026-07-22:
- `0a12d9e` — solutions v4 VERIFIED live (9,334 scored, sane multi-tier dist), ADR-020 clear to Accept
- `1c6101f` — corrected: LIVENESS only verified, content-quality NOT validated

These correctly qualified the verification: the structural/liveness check passed, but title-eyeball
flagged quality issues (policy/regulation bleed, branded bleed, belonging/uplifting drift). ADR-020
remains Provisional — content-quality gate is owed before Accept.

### Issue landscape triage

Reviewed the full cross-repo issue board. Key conclusions:

**Cross-repo dependency chains:**
- armed_conflict (LD#73 → NM#274): NM blocked until LD classifier exists
- obituary detector (LD#51/#77 → NM#185 → ovr#204): chained, ovr removes hardcoded only after NM ships
- normalization refits (LD#72/#64 ↔ NM#205/#167): same raw_min-drift root cause as #161 & #205
- source classification (FS source_class → NM#253): state-media/bias consumed downstream
- solutions lens (LD#43 / shipped v4 → NM#204): v4 likely lets NM#204 close as superseded

**Priority ranking confirmed:**

| Pri | Items |
|-----|-------|
| P0 | #76 calibration audit, #75 nr raw-scale collapse, #74 belonging boundary, NM#276 consent/paywall, #72 cross-filter scale, NM#206 filter timeout |
| P1 | NM#96 GPU migration, NM#221 VRAM mgmt, NM#244 422s, NM#220 Ollama contention, ovr#262 data archiving, ops catch-up budget |
| P2 | ovr#270 summarizer swap, ovr#235 held-out validation, obituary chain, armed_conflict, NM#275 cross-lang dedup, ovr#214 summarizer lang, LD#23 cd evidence_quality, LD#71/#70 nr v5, ovr#255/#256 academic/abbreviations, NM#231 uplifting non-English |
| P3 | FS#11 config refactor, FS#107/#103/#114 measurement/dead-feeds/il-Fatto, LD#52/#66 prefilter harmonization, NM#196/#82/#23 simplify/dockerize/decouple, ovr#63/#55/#19 E2E/lighthouse/integration-tests, FS#105+ovr#254 systemd versioning |
| P4 | LD#38/#40 Breakthroughs/Resilience, LD#43 broaden Solutions, ovr#232/#223 Pagefind/places, ovr#211/#213 PWA/WebPush, ovr#242/#133 continuation/map, LD#24 energy-efficient inference |

### FluxusSource quick checks (3 items for operator)

1. Verify global broadening feeds are yielding — check feed-health-report for zero-yield/stale feeds
2. 71 DEAD disable candidates from 07-26 triage — decide: apply now or wait for more brotli-fixed cycles
3. Check OVER_POLLED class after frequency bumps — did 172 bumps clear it, or need second pass

### ovr.news next-session pickups confirmed

1. Summarizer quality sweep (#270 model swap + word-count, test together not serially, use #235 gate)
2. Solutions lens upstream recheck (ovr.db COUNT solutions rows)
3. #235 residual (ratify 39 provisional golden rows)
4. Obituary detector over-flags (LD#77 → ground truth → retrain)
5. armed_conflict detector (LD#73 classifier → NM#274 shadow wiring, biggest build, lowest urgency)

## Framework check

- **agent-ready-projects**: pinned `v1.10.6` = latest ✅
- **agent-ready-papers**: not formally pinned in this project (cross-repo concern)
- **CLAUDE.md**: 14,665 bytes, well under 35k budget, no footer bloat

## Curate findings

- All 10 locally-runnable `<!-- verify: -->` assertions: PASS
- 1 dead-reference false positive (FluxusSource cross-repo pointer, not a local path)
- 3 stale memory files flagged (calibration-history 51d, gemma3-model 57d, thriving-v1-scoring 98d — parked)
- No unresolved gotchas, no hypothesis log, no ground truth drift
- No new gotchas to add (no code work this session)
- CLAUDE.md `Last updated` bumped to 2026-07-26

## Next session pickup (priority order)

1. **① SOLUTIONS v4 QUALITY GATE** — full-content read + oracle re-score sample + dimensional check before ADR-020 Accept. File: `filtered/solutions/filtered_20260722_210402.jsonl`. Policy/regulation bleed in high tier, belonging/uplifting drift in medium, ≥1 branded bleed.
2. **② COMMERCE v2 REGRESSION (#80)** — decide: rollback to v1 (BLOCKED on weight backup) or retrain v2 on representative multilingual traffic. Back up v1 weights to HF Hub regardless.
3. **③ CALIBRATION AUDIT (#76)** — umbrella for #74/#75/#72. Likely ONE raw_min-drift root cause. Start at #76, cross-ref calibration-history Dead Ends.
4. **④ nr v4 NORMALIZATION (#72)** — confirmed running raw-passthrough (31,852 records under-ranked). Fit normalization.json.
5. **⑤ obituary detector v4** — retrain on collected false-negatives (reader flags KV + phase1 labels)
6. **ovr.news #270** — swap summarizer gpt-oss:20b, test with #235 gate
7. **FluxusSource triage** — feed-health check, DEAD disable decision, OVER_POLLED audit

**Quick:** sync `filters/common/score_normalization.py` (44-line divergence with NexusMind); ~2026-08-01 delete retired sustech/foresight dirs post-drain.

**Your calls (parked):** NM#91 sadalsuud healthcheck drift; uplifting v7 NO_HUB backup; cd v5 config-schema exemptions.
