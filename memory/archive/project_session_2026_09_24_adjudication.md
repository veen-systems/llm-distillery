# Session — 2026-09-24 (evening) → 09-25 morning: read-surface retirement, EXP-042, Thriving adjudication, more positives

*Written 2026-09-25 by `/curate` from the commits (`652dcf7` … `1bf1fc6`), `docs/TODO.md` item −2/−1 and
the evidence READMEs, because this run left no session record and the index stopped at 2026-09-22.
Every number below is quoted from those sources, not re-measured. Open the source before using one.*

**Spend: $0.17 (EXP-042) + $0.24 (more-positives oracle step) + $0.37 (hard negatives) = $0.78.**
GPU: none — b650 was held at 05:07 on 09-25 (`gemma3:27b`), so the retrain did not start.
Deploy: N/A — `uplifting v7` still serves Thriving and `human_thriving v8` is unchanged.

## 1. Read surface (`#163`, retire steps 1–2)
- `docs/TODO.md` 548,758 → 59,911 B: 57 closed sections moved verbatim to `docs/TODO-archive.md`.
- `memory/gotcha-log.md` 715,877 → 256,970 B: pre-2026-09-01 entries moved verbatim to
  `memory/gotcha-log-archive.md`.
- One check mechanized: `check_doc_claims.py --check gate-share-sample` (`652dcf7`).
- Owner, on the mechanize-only result: *"i do not really think we achieved something?"* — then
  approved the retire steps. Next retire target is **not chosen** (TODO item −1 lists candidates).

## 2. EXP-042 — the v8-5 prompt edit FAILS its pre-registered bar (`db135f0`)
Widening §5 ("nothing has taken effect yet") credited **0 of 4** targeted flips. The V4 → V4.1
oracle swap (`#157`) moved more than the edit did. Evidence: `docs/evidence/2026-09-24-v8-5-gate/`.

## 3. Three Thriving scope rulings (`e836738`)
Court rulings are in scope; laws passed but not yet in force are out; petitions are out.
`docs/decisions/2026-09-24-thriving-scope-rulings.md`.

## 4. Claude adjudication of every v8 label ≥ 3.5 (`2614550`, `f7119a6`, `0d13fb8`)
- Pilot: owner-checked 10/10. Full run: **878** rows, drift check A vs B **0.946** (stop < 0.90).
- **553 moved out**, every one from in to out: 112 of 316 (35.4%) at ≥ 4.5, 441 of 562 at [3.5, 4.5).
- Training rule for moved-out rows, **the assistant's call (owner: "no idea")**: cap all six
  dimensions at 2.0. Data: `datasets/training/human_thriving_v8_adj1/` (gitignored), v8's split ids.
- ⚠️ This is Claude's judgment under a written rubric, **not independent human truth**. The
  shares are over the 25.1× design-weighted v8 draw — sample quantities, not production rates
  (`merge.py` did not declare this until `/curate` added the line on 2026-09-25).

## 5. More positives (`b2fc09e` … `1bf1fc6`)
- 637 production passers adjudicated → **198 in scope** (drift 0.921). Only **23 of 200 (11.5%)**
  of the `uplifting_only` stratum are Thriving: direct evidence for "the thriving lens is a firehose"
  (#151, the cutover). Per-stratum shares only; the README forbids pooling them.
- Oracle step ($0.24): 186 kept; the V4 → V4.1 control median Δ **−0.267** (|d| ≤ 0.30 → mix).
- 439 production hard negatives added, capped at 2.0 ($0.37). The oracle calls 28% of them in scope.
- Training dirs: `adj1` (adjudicated only), `adj2` (+ new positives), `adj3` (+ hard negatives).

## Open at close
- **TODO −2: retrain adj1 + adj3 on b650**, compare on v8's 660 test ids against both label sets,
  specificity first (ADR-023). Check the GPU first; it was held at 05:07.
- **Owner question, not started:** adjudicate the ~720-article ≥ 7 pool (est. $0.10–0.20).
