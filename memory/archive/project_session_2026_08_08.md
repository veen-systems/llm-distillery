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

---

# 2026-08-08 (afternoon) — proven by outcome, and a self-inflicted outage

## Headline

**The morning's "fixed" was wrong, and only the outcome check found it.** NM#300
was diagnosed as two allowlists, both fixed and deployed — and the next cycle
read **0 of 2,170** with both fixes provably loaded (service start times
verified, md5 parity both boxes). There are **five** allowlists in series. The
three missed ones all sit on the *response → result-object* boundary in
`gpu_client.py` and `main.py`'s dict conversion. The morning's "verified there is
no third" checked the *article → disk* seam — a true statement about the wrong
seam.

Generalisable: **when a value crosses a process boundary, patching the sender
proves nothing unless the receiver's parser is checked — and here the receiver
was an allowlist twice over.**

## Verified (17:10 cycle)

`content_length` and `stage_used` / `stage1_estimate` **100% populated, all six
filters**. NM#300 and LD#88 both **closed**.

**Unasked result:** no surfacing article is ever probe-scored. `stage1_low` rows
peak at raw **0.75–1.50** against op-points of 2.25/4.0, so
`surfacing AND stage1_low` is **0** in every filter. That is the hybrid design's
core safety claim, assumed since 2026-02, measured for the first time. It also
means surfacing-score analysis measures **student output only** — which
retroactively validates the LD#93 step 4 work.

## I took the pipeline down

`nexusmind.service` FAILED 16:07, would have failed every 4h. The fail-closed
deploy gate did its job: `src/scoring/gpu_client.py.bak_nm300third_20260808` was
untracked under a guarded path. **Not a slip — a decision.** I said, ~20 minutes
earlier, that I was keeping the `.bak` files as a rollback for an unverified fix.
The commits were already pushed; git *was* the rollback. Recovered 16:23, 16:07
collection reprocessed, no data lost, one cycle delayed, alert email had fired.
Gotcha `0c14de4`.

## LD#93 step 4 — sized, then withdrawn, twice

**Verdict: do not set the cap.** A cap ≥ the op-point removes **zero** false
positives (visibility keys on raw), and nothing short reaches `medium_high`
(max 4.93). Two corrections, both from the FluxusSource session:

1. Residual understated **3×** — ADR-007 retires the 59 `gn_*` country proxies,
   not the 243 publisher-named GN feeds. Post-ADR-007 is **8.0/cycle**, not 2.6.
2. My "topic feeds emit solution vocabulary" mechanism **refuted** —
   `google_news_uplifting` is 80 short rows, **0** surfacing. It is one feed ×
   one lens: `energy_storage` on solutions at 56.8%, 0% on the other five.

**A mechanism that explains the observation is not evidence for it.** The
cheapest kill was naming the case the hypothesis most strongly predicted and
looking.

## Shipped alongside

NM#303 production contract validation → **NM#304** (Contract A had never met
production either; 4 defects). Census check A hardened — it false-positived on
`enriched`/`enriched_at`, rare-but-working. `commit-msg` hook fixed (false-failed
on private Hub repos). Framework → **v1.17.0**. **agent-ready-projects#33**:
`install-global-skills.sh` installs from the working tree, so an adopter can
receive unreleased, later-reverted content — observed for ~42 minutes today.

## Three instrument failures, all mine

1. The pre-registered NM#300 check would have passed a *broken* fix as fine had
   the third drop not existed — and my `stage_used` criterion ("a nonzero
   minority, 17–32%") **fails on a working fix**: solutions is 64.6%. The
   baseline came from journal lines whose filter I never identified.
2. My watcher fired **falsely** — `/tmp` was cleaned, and the loop treated any
   non-`NOT-YET` output as success, so an error message read as a result.
3. My census patch referenced a variable that does not exist; `py_compile` was
   green and only executing it caught the `NameError`.

**Third instance today of comparing a per-filter quantity against an
unattributed aggregate**, after `source_filter excluded N` and the GN split.

## NEXT SESSION

All of the morning's items are done. Nothing is calendar-bound before 08-10.

1. **cd v6 cutover — the top item, and the only one needing a deploy window.**
   The package is ready and proven (Hub repo live, `normalization.json` n=3,680,
   `--check-hub` 9/9, loaded end-to-end and scored). Deferred by owner decision
   so it would not share a cycle with NM#300. **This makes cd screening
   reader-visible for the first time** — unlike the rule prefilter (NM#284), a
   probe actually executes. After cutover: refit `normalization.json` from real
   `filter_version=6.0` rows once ≥200 surfacing rows accumulate, then **#87**.
2. **NM#304** — 4 Contract A defects, none decided. Two (`priority` ceiling,
   `eval_query`) need a FluxusSource answer; two are schema edits. The baseline
   file is empty **on purpose** — do not widen the schema to go green.
3. **~08-10: the GN natural experiment.** FluxusSource will ping. Six feeds moved
   from GN redirects to canonical publisher URLs — same publishers either side,
   so it isolates the redirect as the cause of **0 of 14,198** GN rows ever
   enriching. Compare their rescue rate against the ~62% general rate *and*
   their own pre-migration 0%. Their first steady-state day is 08-09, so measure
   on 08-10, not before.
4. **~08-18: re-measure corroboration precision on the CAPPED system.**
5. Watch, don't act: `content_length` → `required` in Contract B only after
   several clean cycles; LD#93 re-measure gated on **measured GN-URL share per
   cycle**, not on FluxusSource's migration being "done" (there is no near-term
   done).

**Standing cautions that earned their place today:** re-query issue state
immediately before commenting or closing (a peer closed Chain 8 30 minutes ahead
of me). Scrutinise the check as hard as the claim — three of my instruments broke
and none of my conclusions did. And **never leave scratch files inside a repo a
service deploys from**; write them to the scratchpad instead.
