---
name: project_session_2026_09_22_harm_live
description: "Session 2026-09-22 — the harm detector went LIVE in production (stamp-only), its contracts were declared and twice reviewed, and ADR-022 turned out to say the opposite of what four documents cited it for"
metadata:
  type: project
---

# Session — 2026-09-22: the harm stamp is live, and the ADR it cited forbids it

**$0 of oracle spend.** No oracle calls, no judge calls, no GPU. **Deploy: PARTIAL and
deliberately so** — `pipeline.harm_detector.enabled: true` is merged AND on sadalsuud
(`NM#519`, `1d4dc40`); everything after that is committed on NexusMind `main` and **NOT
pushed**. No filter package, model, calibration, normalization or threshold changed.

## What the owner asked

*"if want the harm detector in operation"*, then `go` three times, then *"pls do"* on an
ADR draft, then the session close.

## 1. The harm detector is LIVE (`#156` step 1, `NM#519`)

⛔ **Stamp-only.** No threshold ships, no filter config reads the fields, nothing is gated.
Rollback is one line back to `false`.

**Outcome-proven before it shipped**, not predicate-proven: the stage ran through its real
caller (`NexusMindPipeline._run_harm_preprocessing`) over 3,004 real `data/raw` rows and
stamped 3,000, where the same call returns `{"skipped": "disabled"}` beforehand. First
production cycle 20:08, `Result=success`, 3,000 stamped, `device: cpu`, stack id identical
to the offline smoke.

⚠️ **Host preconditions were checked, not assumed** — the five classifier pickles are on
sadalsuud, the mpnet embedder is in its HF cache, and its venv imports the same four library
versions, so the first cycle downloaded nothing.

⭐ **Both contract checkers already carried `_harm_` in their stamp-prefix tuples**, so
neither newly flagged our own fields. That mattered: `nexusmind-output-contract-check.service`
treats new violations as a unit failure.

## 2. ⛔ THE COLD START CANNOT CONVERGE, AND I QUOTED THE ESTIMATE THAT SAYS IT CAN (`H-HD13`, `NM#522`)

`config/app.yaml` said *"at 3000/run the backlog needs ~12 cycles, i.e. ~2 days"*. That is a
fixed backlog divided by the cap **with no intake term**. Measured 24h in: **48,676** rows
inside the 3-day window, **11,982** stamped, **36,694** unstamped, against intake of **3,072**
and **3,650** per cycle versus a **3,000** cap. Newest-first puts the entire shortfall in the
**oldest** rows — a population skew, not random missingness.

⭐ **The keeper is how it survived: a closed-form number reads as measured.** The same file
says *"Derived, not timed in production"* two keys down about a different number, and I read
past it, then repeated the estimate to the owner and into `#156` before checking it.

**Decision: cap NOT raised** — it buys a corpus-wide rate nothing needs and costs a fixed
per-cycle addition to `NM#517`'s unexplained duration trend, at a throughput only ever timed
AT this cap. ⚠️ Revisit after **2026-10-15**, when GN retirement drops intake.

✅ One thing gained: the stage is now **timed** here — 13.1 and 12.2 rows/s.

## 3. Contracts declared, and reviewed twice (`73ad620`, peer's `a0736c6`)

Contract B **1.19.0 → 1.20.0** (three top-level properties), article-record **0.6.0 → 0.7.0**
(`nexusmind.signals.harm_is_subject` = `{score, model, stack}`), `record_path` on the three
status entries, and the three `meaning:` blocks removed because
`article_record_register.py:389` lets `meaning` win over a contract description.

⛔ **Round 1 found three blockers, all in things I wrote:**
1. The promoted description said the model version is *"read off the loaded artifact"*.
   `harm.py:207` stamps a class constant; the artifact path `HarmDetectorV1.stamp()` has
   **no callers** (`NM#520`). Deleting the `meaning:` copy would have turned a doc defect
   into a contract defect.
2. ⭐ **My four mutants all moved the `record_path` AWAY from anything declared** — three
   that stay INSIDE the declared set survived, worst being score↔stack transposed, which is
   type-impossible and green.
3. *"No verdict member, which makes the rule structural"* was **FALSE** — adding a `verdict`
   and an `_is_harm` both left the suite green.

⚠️ And *"it creates no obligation on a reader"* was false while two greps agreed it was true.

## 4. ⭐⭐ ADR-022 SAYS THE OPPOSITE OF WHAT FOUR DOCUMENTS CITED IT FOR (`#161`)

ADR-022 requires the stamp triple **including `_is_<detector>`**, requires ONE central
enforcement point (*"never a consumer-side drop"*), and calls stamps *"observability/audit
fields, not routing fields"*. Harm omits the bool, plans N per-lens points, and exists to be
routed on.

⭐ **The design survives; the citation was wrong.** Clause 1 specifies *"bool at the deployed
op-point"* and harm ships no op-point ⇒ **INAPPLICABLE, not unmet**. And the ADR already
prescribed the remedy nobody used — *Revisit If*: an exception is justified *"as an explicit
exception recorded here"*. **The defect was the missing record.**

⛔ **A DRAFT amendment is in `docs/adr/022-stamp-always-single-gate.md` and is NOT RULED.**

## ⛔ My errors this session

1. **Chain 7.5/7.6.** I built a contract paragraph and a cross-repo instruction on it. That
   file has **zero** hits for `harm_is_subject`/`#156`/`_harm_`. ⭐ **I opened the file and
   quoted the rows accurately — the error was confirming the QUOTE and not the REFERENT**,
   which is the harder half, because having read the source is what stops you re-checking.
2. **Repeated the `~12 cycles` estimate twice** before measuring it (§2).
3. **The two arguments merged.** The 6-of-9 carriage figure argues for ONE SHARED DETECTOR;
   *stamp-don't-block* rests on the lens-promise argument. A reviewer made the identical
   collapse independently, so the pairing invites it.
4. **"One of which enforces at 0.85"** — both obituary and violence enforce. Raised in review
   round 1, carried into `NM#521` anyway, where it then read as reviewed.

## Numbers

NexusMind unit suite **1647 → 1648** (mine) and **1710** (peer's, after the contract pass).
`validate_status` 0 errors, seeded red two ways. **6 mutations killed** on the record_path
assertion after the fix, **13 mutants / 10 killed / 3 negative controls** on the peer's
replacement. Four issues filed: `NM#520`, `NM#521`, `NM#522`, `#161`.

## ⛔ OWED — deploy is incomplete on purpose

- **NexusMind `main` is 7 commits ahead of origin and NOT pushed**, and sadalsuud stays on
  `1d4dc40`. The host therefore has the ENABLED flag but **not** the corrected cap comment.
  The peer session (`nexusmind-0f`) was still working and asked to hold; it owns the push.
  ⚠️ **If its handoff does not claim this, it is the first action next session** — a step both
  sessions think the other owns is the shape that gets skipped.
  ✅ **DISCHARGED 2026-09-22, and VERIFIED HERE rather than taken**: the peer's close message
  claimed it, and `git rev-parse origin/main` (NexusMind clone) and `ssh sadalsuud ... git
  rev-parse HEAD` both read **`8c54bef`**, clean tree. Its handoff does claim it from that
  side, so the both-sessions-think-the-other shape did not occur.
- ⚠️ **After that push, pull sadalsuud but do NOT run `deploy/install.sh`.** `34fab3e`
  touches `deploy/systemd/`, whose files are installed as root-owned copies a pull does not
  update. Owner ruled: bundle the install into the next real deploy. The unit headers stay
  stale on the host **deliberately**.
- The `record_path` → record-schema declarations are done; `NM#521`'s missing RULE is not.
  ✅ **Now done too, NexusMind-side at `007be0a` (Contract B 1.21.0), verified here by reading
  that commit.** 8 routable stamps declared, 3 bookkeeping ones declared-OMITTED with reasons.
  ⚠️ The check was shown red against the **8**, not against the 11 this repo's queue named —
  consistent, because the criterion makes the 3 omitted-with-reason ones passing, not missing.
