# Four v8 scope rulings, and what measurement did to them afterwards

**2026-09-03. Owner rulings.** Taken after the material in
`docs/evidence/2026-09-03-classA-supplement-adjudication/` and
`docs/evidence/2026-09-03-v8-1-qualifier-blast-radius/`. The commencement ruling from the same
day has its own record: `docs/decisions/2026-09-03-v8-1-commencement-clause.md`.

⛔ **Every ruling below was ADOPTED. Two of the four did not survive implementation intact, and
that is recorded here rather than in a commit message**, because a ruling nobody can find is a
ruling that gets re-litigated.

---

## 1. The Syria delisting cluster — **OUT OF SCOPE under §3**

**Ruled: out of scope.** An outcome delivered to a jurisdiction's designation and to an
investment climate does not reach people. §3 already names *"a jurisdiction's reputation"*; the
article's own claim for the action is that it *"will help foster additional investment in Syria
to promote political and economic stability."* No person in the article receives anything.

**Scope of the precedent:** delistings, grey-list exits, sanctions moves, trade normalisations.

**Against it, recorded:** sanctions are not reputation — they constrain banking, medicine and
goods for ~23M people, and lifting them is a material change during a post-war rebuild. The
ruling does not deny that; it says this lens is not where that story belongs (ADR-015: lenses
are perspectives, not partitions).

**Population:** 15 rows corpus-wide, **9 above the op-point**. ⚠️ The first count said 14/8 — an
English title regex missed a Japanese row. The oracle's own `dominant_subject` is written in
English whatever the article's language and is the reliable matching surface.

✅ **Implemented as clause C** (a §3 example). Measured: the §3 group went **5.05 → 2.89**,
4 demoted, 0 promoted.

## 2. Judicial relief to convicted offenders — **OUT, on §1's own headline rule**

**Ruled: out of scope.** The recipient is the offender; nobody harmed by the offence is better
off. §1 already says it — *"Length does not vote. A reader meets this article as its headline"* —
and the headline is *frees kidnap-murder convict*.

**The discriminator, which is a gloss on the ruling and not part of it:** §4's *"amnesty
delivered"* is untouched. Where the imprisonment **itself** was the injustice — political
prisoners freed, a wrongful conviction quashed — the release **is** the repair and scores
normally. **The test is whether the conviction is the harm or the response to a harm.** That
wording is the assistant's, offered to reconcile the ruling with §4, and the owner has not ruled
on it.

⛔⛔ **NOT IMPLEMENTED — the clause was written, measured, and DROPPED.** Alone it was inert
(origin row 0.900 sd 0.000, identical to v8). Combined with the commencement clause it produced
a **B×D interaction** that scored the #91 origin article **5.921 with 12/12 runs `in_scope`**,
where v8 pins it at 0.900 with zero spread. D held the only sentence among the four clauses that
**licenses** a positive — *"the release **is** the repair and **scores normally**"* — and
deleting that sentence helped (5.921 → 3.375) but was **not sufficient**.

**So this ruling stands unexecuted.** Three corpus rows keep their labels. Revisit at v9 with a
wording that adds an exclusion without licensing anything.
Evidence: `docs/evidence/2026-09-03-v8-1-gate/` PART 2.

## 3. The legislative-proposal clause — **WRITE IT**, and it moved to §5

**Ruled: write it.** §1's principle — *"money committed is not a protection established"* — is
correct but written in terms of **money**, so a proposal, a plan, a bill not yet enacted and
*preparations* fall through. Six above-op rows named exactly that in the oracle's own
`dominant_subject` and scored 4.55–6.33 anyway.

⚠️ **Placement changed under measurement, twice.** Stated as a **test inside §1** it destabilised
the #91 origin row (2.583, sd 2.381, 2/6 `in_scope`). Two hypotheses for why were **refuted**: a
contrast example (removing it changed 2/6 to 1/6, indistinguishable at n=6) and length/location
(a **placebo** of +996 chars of §1 restatement left the row at 0.883 ± 0.037). Moved to **§5's
plain exclusion list** it is inert on that row and 360 chars instead of 1,107.

⭐ **The generalisable finding: a rule stated as a TEST inside a reasoning step becomes a
question the model asks of every article; the same rule stated as a CATEGORY in an exclusion
list does not.** Prefer adding an exclusion to adding a test.

✅ **Implemented as clause A3.** Measured: the proposal/announcement group **4.76 → 3.53**,
8 demoted, 1 promoted. ⚠️ The promotion is a real defect — a Tamil Nadu fuel-price
**announcement** crossed upward, 2.98 → 4.73, from the same politician as a waiver row that
correctly went down.

## 4. Re-label scope — **the affected above-op rows, not the corpus**

**Ruled:** re-score Gate B-A plus the affected above-op rows; not the full 6,586.

⚠️ **The assistant then argued for a full k=9 re-label once cost stopped being a constraint, and
was wrong to.** The owner pushed back and the argument did not survive: the label noise a higher
k buys concentrates **below** the op-point (only **2.1%** of the ±1.0 band is verdict-flipped,
against 15.35% corpus-wide), where `--aggregate all` already suppresses it and ADR-023 calls the
errors cheap — and a fresh corpus would **invalidate** the label review, the class-A adjudication
and every population figure measured that day. **Scope creep dressed as thoroughness.**

✅ **Executed at the right size: all 456 above-op rows** — not the 50 the generators had flagged,
because a generator finds what it was written to find. **140 demoted (30.7%), and 115 of those
were rows no generator flagged**; sampling would have found 25.

**Written:** `labels_v84_merged.jsonl`, 6,586 rows with 456 replaced, per-row provenance
(`prompt_hash` 003cd35a5122 ×6130 / c4705408c477 ×456). `labels_k3.jsonl` untouched.

⛔ **Consequence for Phase C: the positive class shrank 456 → 316, a base rate of 6.92% → 4.80%**,
now **below** production's measured 7.74%. The probe objective must be set against 4.80%.

---

## What these rulings did NOT settle

- **The phase-3 mRNA row.** A Moderna/Merck personalised cancer vaccine result — patients,
  measured reduction in melanoma recurrence — demoted **5.13 → 0.52**. That is not the
  preclinical class-B shape. **Owner eye wanted; the assistant believes this label is wrong.**
- **The train/test overlap on the adverse suite.** Seven of the 18 adverse rows are designated
  hard negatives, i.e. intended training inputs, while Gate B-A judges against the same rows.
  Six new benchmark candidates were identified and **not promoted** for exactly this reason.
  `docs/evidence/2026-09-03-gate-executable/` §3.
