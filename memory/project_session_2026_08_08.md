---
name: project_session_2026_08_08
description: 2026-08-08 — LD#101 confirmed by outcome and committed out of one-box drift; the deadline gate closed by a parallel session; NM#300 diagnosed as two drops in series; the contracts met production for the first time and failed; three of my own instruments broke.
metadata:
  type: project
---

# 2026-08-08 — the checks failed, the analysis didn't

## Headline

**Three of my measurement instruments broke and zero of my conclusions did.**
That is the session in one line, and it is the thing to carry forward. Details in
the assistant memory entry `feedback-check-must-be-specific`.

## What shipped

| What | Where | State |
|---|---|---|
| **LD#101 confirmed live and CLOSED** | — | `eval_aggregator` rows in each filter's output **21 → 0**, all six, with the control that the same cycle's input carried **22** |
| eval exclusion committed out of drift | `ducroq/NexusMind@9fb441a` | It was running as **uncommitted working-tree edits on sadalsuud**; nothing in the repo referenced `eval_aggregator` |
| 4 published eval articles suppressed | `ovr.news@75bde57` | Config kill switch, **not** a DB edit; proven by executing the rule with negative controls |
| **NM#300 fixed — two drops in series** | `ducroq/NexusMind@410f630` | Deployed both halves; **unproven until the 12:00 cycle** |
| **Stamp census** | `ducroq/NexusMind@e64a45f` | `scripts/stamp_census.py`; see `stamp-contract-integrity.md` |
| **Contract B 1.15.0** | `ducroq/NexusMind@3030e35` | First-ever production validation: **908 violations → 1** |
| Filed | NM#303, FS#138 | Production contract validation; a `null` inside `tags` |

## LD#101 — and the check that would have called it broken

Verified by **outcome**: 21 → 0 across all six filters, with an input control of
22 eval articles in the same cycle.

**The check I pre-registered would have reported FAILURE.** It was "the
`source_filter excluded N articles` line must exceed the 121 baseline". It came
in at **86** — lower — because that count aggregates all excluded types and
swings with corpus composition (69 → 121 → 86 across one day; investment_risk
519 → 545 → 946). I replaced it because I wanted something more direct, **not**
because I had spotted it was invalid.

**The drift was the bigger find.** The fix was live only as uncommitted edits on
one box. A `git checkout` there, or a fresh copy from the repo, would have
reverted a reader-visible fix leaving no diff behind. All six configs were
md5-verified identical to llm-distillery's before committing, and the six `.bak`
files were verified byte-identical to `e63202b` before deletion.

## The 30 published rows were NOT a cleanup job

Enumerating them changed the recommendation. All 30 sat inside the 10-day window
(`maxAgeDays: 10`) and **age out on their own between 08-09 and 08-14**, and most
are good, on-lens global-south coverage — pine-tree smallholders in Iringa and
Njombe, Tanzania's science-policy overhaul, a tree-kangaroo conservation deed,
Els Xiquets de Tarragona, Zimbabwe's wildlife-ranger law. Bulk deletion would
have destroyed exactly the population Chain 14 protects.

**Four were actually defective** and were suppressed via
`data/chief_editor_config.json` `manual_suppression` (operator kill switch,
config not DB — and the rule's own docstring notes the live site builds from the
R2 copy, so a DB edit would not have worked anyway): two Taiwanese stories under
a **Madagascar** query (one scoring **9.51 uplifting** for new traffic fines), a
Zimbabwe funeral/murder story at belonging 7.89, and a China–Kazakhstan business
piece under a **Chad** query.

**Not yet verified:** the site build. Recorded before/after — all three URLs
returned **200** pre-build; the two suppressed must go 404 and the control
(`newsdata_eval_bi_1c78d8e397b7`) must stay 200. **If all three 404, the list is
over-matching.**

**Loose thread:** eval-arm articles cluster at **9.4–9.99** on uplifting and
solutions. Either that stream was unusually good or the scorers over-reward it —
worth checking against LD#91 and NM#289.

## NM#300 — the issue's own caveat was the answer

Two loss points, **in series**, so fixing either alone changes nothing:

1. `deploy/gpu-server/main.py` — `FilterScoreResult` is a Pydantic allowlist
   built field-by-field. **This one kills it first**, which the issue ranked as
   less likely while stating the caveat that made it decisive.
2. `scripts/main.py` — the `analysis` allowlist drops it again.

No third: `analysis` is attached whole and written with `json.dumps(article)`.

**Deploy was free** — the scorer was already down with ollama holding the GPU, so
no restart and ollama untouched. The gpu-server half was **proven on the box** by
`ast`-extracting the two model classes verbatim from the deployed file and
executing them in the scorer venv (no GPU touched): `content_length` crosses the
wire; an old-build control still returns `None`.

## The contracts had never met a production row

`tests/unit/test_contracts.py` validates **fixtures**. First run against 2,400
live rows: **908 violations**. `image_analysis.image_confidence` declared `0..1`
is a **raw logit** (−12.330..6.365, median −2.696, 68.4% outside). The producer
was right; the contract was wrong from the day it was written, and fixtures could
never have caught it because `url_pattern` emits 1.0 and `domain_duplicate` 0.9.
**908 → 1** after the fix, and that last one is real (a `null` in `tags`) and
left failing. Full detail: `memory/stamp-contract-integrity.md`.

## Board

**196** — LD 36 · NM 43 · ovr 89 · FS 13 · ps 12 · atlas 3. Sediment **74**
(cutoff 2026-07-09; quote the cutoff, it moves on its own).

It went **198 → 199 → 195 → 196** in one day and every move was ours.

**Chain 8 (Google News) is CLOSED — by a parallel session, not by me.**
`ListAgents` showed **three** peers live, one 12 hours into FluxusSource. It
wrote `ADR-007` at 08:54:31 and closed FS#120 at 08:54:57; **I commented on that
issue at 09:24 calling for a decision taken 30 minutes earlier**, from a board
state read at 08:05. Same finding as theirs, worse disposition — they used the
`gn_chad` contamination (2 on-topic items in 462) as *H1 confirmed by a sharper
test*; I called it a threat to validity. Corrected in-thread.
**Re-query issue state immediately before commenting or closing.**

**So the board now has no calendar-bound item at all.**

## NEXT SESSION

1. **Read `/tmp/.../tasks/bnsfc8dn8.output`** — the NM#300 outcome check on the
   12:00 cycle. `content_length` must be non-null on new rows (was 0 of 50,605).
   If it is still 0, suspect a *third* drop, not the two fixed.
2. **Re-check the three ovr.news URLs** after the next site build: two suppressed
   → 404, `newsdata_eval_bi_1c78d8e397b7` → still 200.
3. **Run the stamp census** on post-fix cycles and decide whether
   `content_length` can be promoted to `required` in Contract B.
4. Then the RoI order: **cd v6 cutover** (blocked on a Hub repo that does not
   exist + a normalization fit from a historical rescore) → **LD#93 step 4** →
   **LD#88 item 1** (`stage_used`, which the census surfaced unprompted).
5. Re-measure corroboration precision on the **capped** system ~08-18.
