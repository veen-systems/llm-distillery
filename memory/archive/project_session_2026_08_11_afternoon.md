# Session record — 2026-08-11, afternoon

Follows `project_session_2026_08_11_midday.md`. Four threads: the op-point
verification that was the session's stated first task, framework drift, #105, and
a long cross-session exchange with the NexusMind and FluxusSource peers that
produced three retractions — two mine, one theirs.

---

## 1. The op-point cycle — VERIFIED, and #102 closed

**Both filters read ZERO on the pre-registered criterion.** The 12:02 cycle of
2026-08-11.

| filter | band | rows still tiered `medium` | baseline | verdict |
|---|---|---|---|---|
| `uplifting v7` | [4.0, 4.5) | **0** — all 50 band rows now `low` | 81 | PASS |
| `investment_risk v6` | [4.0, 4.25) | **0** — all 49 band rows now `low` | 82 | PASS |

Batches `filtered_20260811_123954` (1,720 rows) and `filtered_20260811_124058`
(1,210 rows). **Both confirmed fully written before reading** — size stable across
a 3-second gap, per-row counts summing exactly to line counts. Pre-cycle,
`TIER_THRESHOLDS` was read from **NexusMind's checkout on sadalsuud**, the runtime
source, not from `config.yaml`.

**The secondary `medium`-count expectation was NOT met, and that is correct.**
Predicted ≈152 and ≈318; observed **58** and **224**. The batches were far smaller
than the baseline's (1,720 vs 4,676; 1,210 vs 1,928), so **the absolute counts are
not comparable quantities**. By share: `uplifting` 3.37% observed vs 3.25%
predicted (matches); `investment_risk` 18.51% vs 16.49% (runs high — the
pre-registered `proxy_aggregator` caveat). **Do not re-derive this as a failure.**

Record: `docs/evidence/2026-08-10-uplifting-v7-op-point-4.5-VERIFIED.md` (renamed
off `-PREPARED`; five references updated).

**#102 closed** with step 1 recorded as NOT RUN rather than silently dropped — no
second oracle batch was collected, and its second half ("reach the sub-300 rows")
is now refused by the do-not-oracle-score-short-content rule.

## 2. Framework drift closed — stamped v1.20.0

`/update-drift` over v1.19.0 + v1.20.0: **4 adopted, 1 declined, 3 n/a, 6 already
in force.** Full record now in `docs/decisions/framework-adoption-history.md`.

The adopted Step 1.5 structural pre-check was **verified by execution** over 382
tracked `.md` files — 2 violations, 0 false positives, both genuine data loss. It
has run on every commit since.

## 3. #105 answered — and it split into #108

**Method: zero oracle spend.** Every refused row already carries the label it was
trained on, so comparing refused-vs-passed label distributions settles "are the
labels wrong or did the rule tighten?" for free, and never runs the oracle outside
its validated range. `scripts/research/gate_refused_label_audit.py`.

**`cultural_discovery v5` — the RULE tightened, the labels are fine.**
Lens-refused rows: mean label **1.102**, **2.4%** at/above the 4.0 op-point.
Passed: **2.214**, **16.1%**. The gate strips tech/commerce domains hardest — off
lens for a culture filter, working as designed. **Consequence #105 did not
state**: dropping 4,458 rows that are 97.6% negative roughly **doubles the positive
rate, 9.0% → 16.2%**, so any across-retrain comparison is non-comparable per
ADR-023.

**`investment_risk v6` — neither. My first reading was REFUTED and is now #108.**
The corpus numbers looked like #92 short-stub inflation (refused mean 2.633 /
19.6% at-or-above vs passed 2.245 / 8.3%). Killed by two checks:

1. **Length is almost perfectly collinear with source** — elpais 97.8% short,
   spiegel 99.5%, nu.nl 96.1%, nrc 93.4%, exame 99.0%, aljazeera 100.0%. The one
   domain with both sides usable (`ad.nl`) runs the **opposite** way: short
   2.086/9.7%, long 2.502/19.4%.
2. **The floor is not at the discontinuity.** By length bucket, % at/above 4.25:
   0–100 27.2%, 100–200 18.6%, 200–300 18.6%, **300–600 18.1%** (this bucket
   *passes* the gate), 600–1200 2.2%, 1200+ 6.4%. The break is near **600**, not
   300.

**So: a retrain removes El País, Spiegel, NU.nl, NRC, Exame and Al Jazeera at
93–100% each** — a language and geography shift, not a volume reduction. Lands on
NM#292.

**#109** designs the instrument that would settle label *correctness* for both.
Two arms, because measuring the populations showed only one needs a judge panel:
`cultural_discovery v5`'s refused rows are **99.9% full-length** (6 of 4,464
sub-300, 0 Google News) so a cross-oracle re-score is in range; `investment_risk
v6`'s are **99.1% sub-300**. **Unapproved, nothing run, no spend.**

## 4. The peer exchange — three retractions

Delegated FS#145/#157 to the FluxusSource session and NM#314 to NexusMind. Both
came back with corrections; the record improved in every case.

- **FS#145 is an ENABLER, not a root cause.** It harvests the publisher *host*,
  not the article URL, so it does not make GN items enrichable and **the GN share
  does not fall when it lands**. Do not schedule anything on that assumption.
- **NM#314 is BUILT** (PR #317). The gate is merge + deploy, not implementation.
- **The singleton claim, retracted by NM.** They said the wrong-but-plausible
  singleton pairing was "most of the population by count"; I committed it. The
  measurement says **~7.5% — a tail**. Corrected in `cross-repo-prioritization.md`
  after **verifying against their source rather than their report**, which
  surfaced two exclusions their message had not carried (only-stored-rows, and
  65% of bad rows from three sources). The residual is **unquantified, not
  large** — and "not large" is not "small". **NM#322** now sizes it; n=300 is the
  first size whose ceiling falls under the measured 1.76% base rate, and n=150
  settles nothing.

**A fifth home for the op-point constant**, from NM#319: NexusMind's
`pipeline.enrichment.min_score` gates *enrichment* at 4.0 and is not a tier
boundary. Moving an op-point does not move it. Now in `CLAUDE.md` Hard
Constraints.

---

## My own errors this session, both caught before anyone acted

1. **The `investment_risk` inflation reading** — plausible, corpus-level, and
   wrong. Caught by my own confound check, before publishing.
2. **The `else` misattribution** — `gate_refused_label_audit.py` attributed
   anything not blocked by the length floor to "lens rules" via `else`. Correct
   today (the gate has exactly two reasons) but a third would have been silently
   misreported, under numbers already published. Fixed to test every reason
   positively with a loud `refused_unattributed` remainder.
3. **The ablation that lied.** Testing that fix, I copied the script to a scratch
   dir, stubbed an arm, got exit 1 — from a `FileNotFoundError`, because `REPO`
   derives from `__file__`. **An ablation failing for an unrelated reason is
   indistinguishable from a working control if only the exit code is checked.**
   Redone with `REPO` pinned: 4,458 and 50 rows move into the bucket, exit 1, no
   traceback.

**All three were plausible-and-unchecked, not wrong-and-obvious.** That is the
shape to watch for, and it is why the new gotcha about confident recall matters.

---

## 5. The late half — two owner questions that found more than the day's analysis did

**"ovr.news cannot make a summary of 300 words if the input is less than that?"**
It can't, and it does anyway. Measured on `ovr.db`: articles under 200 chars
(n=40 published) get summaries averaging 1,165 chars — **8.87× expansion**, while
normal articles compress to 0.37×. **324 published summaries are longer than their
source.** Two verified fabrications: a 106-char Cambodia headline became 1,095 chars
asserting victims *"included both Cambodian citizens and foreign nationals"*
(invented); a 131-char Kačanik headline became 902 chars asserting *"The church had
been without a cross since 1999"* — the source says no **Serbs** since 1999, so the
date was moved onto a different, politically loaded fact. **Current, not historical**:
24 in 2026-08 at 9.2×. Filed ovr.news#311 (P1); it is the **mechanism behind
ovr.news#286**, a reader-reported backfill of 397 such summaries.

**Why nothing caught it**: `summary-overlap-audit.ts` tests for *copying* — the
opposite failure — so a 9× expansion passes cleanly; `OWN_WORDS_RULE` promises
"original … in new words", which fluent invention satisfies; and
`MIN_CONTENT_AFTER_ENRICHMENT = 100` is the **wrong shape, not the wrong value** —
both items cleared it by 6 and 31 chars. A floor cannot express "output must not
exceed input"; only a ratio can.

**"Is enrichment before or after scoring?"** Both, and there are **three passes**:
NexusMind `pre_enrich` (before scoring, short articles, no score gate),
NexusMind `enrich_articles` (after scoring, `min_score` 4.0), and **ovr.news**
(before summarising, `content < 500` **AND NOT** `wasEnrichedUpstream`). The third
exists because it is the only one that can resolve Google News links — **NexusMind
has no GN resolution at all** — and that resolver **fails every time**, which is
ovr.news#312: the unresolved branch returns before the fetch, before `SKIP_DOMAINS`
and before the `try/catch` that logs, emitting only an unpersisted debug line. Three
other early returns in that function share the shape.

**And the direction makes it moot**: FluxusSource's ADR-007 migration is *working*.
Six feeds migrated 2026-08-08 — median length **89 → 326**, sub-300 share **100% →
47%**, landing above the non-GN baseline. Two levers though: retiring the country
proxies closes **14.9 of 25.7 points (58%)**; population B (10.8% of corpus, same
defect) needs bulk repointing. So the enrichment workarounds are patches on a source
already being retired. **Note: "ADR-007" here is FluxusSource's, not this repo's
(ours is adapter-format-and-deployment) — same number, different subject.**

## My errors in the late half

**A third and fourth refuted conclusion**, both the same shape as the first two —
inferring a mechanism from a measurement instead of reading code:

3. **"ovr.news doesn't enrich, so gate upstream in NexusMind."** The 99.4%
   payload-identity measurement was right; the inference was wrong. ovr *does*
   enrich, narrowly gated, so most articles never enter the path — which makes
   "matches what NM sent" and "doesn't enrich" produce **the same number**. Only
   reading the code separated them. Retracted in `601e39d`.
4. **"NM#314 is a prerequisite for a precise short-content gate."** The owner's
   simplification killed it: *short is short, enriched or not* — enrichment can
   succeed and return a 60–100 char Google stub.

**All four were plausible-and-unchecked.** Two were caught by peers reading code I
had only measured; two by re-running. Re-running is the cheaper instrument.

## Next session

`docs/TODO.md` top block is current. **Nothing is blocked on a machine and nothing is
mid-flight.** Owner decisions: **#109** (approve/reject; arm A is cheap and closes
#105's remaining half alone), **#107** and **#106** (rulings), plus two that emerged
late — **confirm the withholding gate to NexusMind directly** (they correctly refuse
approval relayed through a peer) and **decide whether ovr.news should enrich at all**
(owner says it is NexusMind's job; ovr's CLAUDE.md documents the consolidation as
deliberate — two documented positions, genuinely in conflict).
