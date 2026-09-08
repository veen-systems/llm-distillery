# The Thriving harm panel — would a reader be harmed seeing this here? (2026-09-08)

⛔ **Headline: my pre-registered prediction was REFUTED under both judges. `human_thriving v8`
is NOT safer per article than `uplifting v7` on harm-subject content.** It is substantially
better at delivering the tab's promise, and the absolute harm reaching readers falls after a
cutover — but that falls out of **volume**, not from v8 being a safer scorer.

⭐ **The mechanism finding is judge-independent and is the useful result:** on three articles
v8's **own oracle** fires its scope gate at wa 0.80–0.90 and the **student returns 4.66–4.85**,
just above the 4.50 operating point. A binary gate is a step function; a regression head
interpolates across it. Written up as
`docs/decisions/2026-09-08-scope-gate-two-head.md`, evidence for #150.

Pre-registration (written and committed **before any judge call**): `PREREGISTRATION.md`, commit
`c54f595`. Reproduce: `python3 docs/evidence/2026-09-08-thriving-harm-panel/analyze.py`
(committed output `analyze.txt`).

## Design

- **Population: display-eligible rows** — what would actually reach a reader.
  `ovr.news/src/lib/data/pipeline.ts:83` → `getArticlesForBuild(filter, 4.5, …)` filters on
  `afs.weighted_average >= 4.5` (`db-articles.ts:290`, threshold `config.ts:477`). Over the same
  four cycles / 15,372 articles as `EXP-030`: **v7-only 523 · both 131 · v8-only 37**.
- **n=137**, seeded: 60 v7-only, 40 both, **all 37** v8-only (a census of that stratum).
- **Blind.** The judge sees title and body only — never the stratum, never either lens's score.
- **The rubric belongs to neither lens.** Built from the reader-facing tab copy in
  `ovr.news/src/i18n/translations.ts` — *"Health improving, rights advancing, lives getting
  better."* Grading v7 on v8's rubric is the confound the NexusMind session hit and flagged.
- **Both oracle families judge, because each lens has one.** `uplifting v7`'s oracle is
  **Gemini Flash**, `human_thriving v8`'s is **DeepSeek**, so each lens's conservative number is
  the *opposing* family's verdict.

## Results

| judge | | v7-only | both | v8-only |
|---|---|---|---|---|
| **DeepSeek** k=3 | `harmful` | 3.3% | 7.5% | **10.8%** |
| | `misleading` | 63.3% | 30.0% | 21.6% |
| | on-promise (`fits`+`weak`) | 33.3% | 62.5% | **67.6%** |
| **Gemini** k=1 | `harmful` | 23.3% | 20.0% | **27.0%** |
| | `misleading` | 48.3% | 22.5% | 21.6% |
| | on-promise | 28.3% | 57.5% | **51.4%** |

**The #91 rate — `harmful`, v7-only vs v8-only:** Fisher two-sided **p = 0.198** (DeepSeek),
**p = 0.809** (Gemini). Under neither judge is v8 safer; under DeepSeek the point estimate is
three times worse.

**What v8 wins, under both judges:** `misleading` — nothing has actually improved yet — is
**21.6%** for v8-only against 63.3% / 48.3% for v7-only (**p = 0.0001 / 0.0101**). That is #125's
research-abstract finding, reproduced by a different instrument on a different population.

## Absolute harm reaching the tab, per 4 cycles

A rate on 37 rows and a rate on 523 are not the same reader experience:

| | articles | DeepSeek | Gemini |
|---|---|---|---|
| **today** (both + v7-only) | 654 | ~27 [8, 85] | ~148 [89, 231] |
| **after cutover** (both + v8-only) | 168 | ~14 [5, 35] | ~36 [19, 61] |
| | | **2.0× fewer** | **4.1× fewer** |

⚠️ **The bands overlap and the direction comes from volume, not per-article safety.** Both
judges agree on the direction; neither establishes the magnitude.

## Controls (they assert in `analyze.py`)

1. Both judged sets are **set-identical to the frame**; 0 ERROR majorities.
2. Strata match the pre-registered draw exactly (60 / 40 / 37).
3. ⭐ **The two judges are different objects** — they disagree on **61 of 137** rows, Cohen
   **κ = 0.375**. A zero-disagreement result would be reported as a *failed* control, because it
   would mean the cross-family design proved nothing.
4. **43.1% of DeepSeek's articles had a split k=3 vote.** A majority is not a settled verdict.
   Gemini ran k=1, where unanimity is vacuous — the script says so rather than printing 0%.

## What this does NOT establish

- **Absolute harm levels.** The judges differ by a factor of ~3–7 on the same articles
  (κ 0.375). Read the *within-judge* comparisons; the levels are not trustworthy.
- **What either lens MISSES.** The panel is drawn from what each lens surfaces, so every
  quantity here is precision-shaped.
- **That the gate leak explains the harm rate.** Three articles carry the ~4-point gap. The
  other flagged rows are genuine definition disagreements between v8's oracle and a
  reader-facing harm rubric — prompt questions (#153, #143), not architecture.
- Both judges are from the two families that trained these lenses. An authorship-independent
  judge is still blocked (`openai_api_key` → HTTP 401).
- Four cycles in an 11h38m window; c1 is the backlog cycle.

## Files

`PREREGISTRATION.md` · `panel_frame.jsonl` (137 rows, both lenses' scores, stratum) ·
`judge.py` · `judge_deepseek_k3.json` · `judge_gemini_k1.json` · `analyze.py` / `analyze.txt` ·
`oracle_recheck_input.jsonl` and `oracle_recheck_run{1,2,3}.jsonl` (v8's own oracle, k=3, on the
nine articles either judge called harmful).
