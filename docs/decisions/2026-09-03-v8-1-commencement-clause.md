# The nursery row stays adverse, and the v8.1 fix is on **commencement**

**2026-09-03. Owner ruling.** Closes the question left open by
`docs/decisions/2026-09-01-v8-oracle-ruling.md` §3 and
`docs/evidence/2026-09-01-classA-full-read/` §1.

⛔ **No oracle spend.** The blast radius below is read off labels already paid for
(`EXP-010`); the clause itself is **not yet written and not yet tested**.

---

## 1. The question that was put

Acceptance criterion 1 (**BLOCKING**) requires all nine class-A adverse rows to score below
**3.85**. Eight do. *"Parents of baby girl killed at nursery fear unsafe sleeping 'rife' in
sector across England"* scores **4.400** (DeepSeek k=3) and **5.133** (Gemini k=3), and on
both oracles it is a coin toss — each returns the right verdict on exactly one run of three.

The article is two things at once: a nine-month-old suffocating at nursery and four
custodial sentences, then a national regulation won by the parents' campaign — a cot-only
sleeping rule, Ofsted tripling unannounced inspections, 3,000 extra visits a year, £8m.

§2 of `prompt-candidate-tail.md` scores 0–2 for *"a policy change… made after the fact,
**especially as a trailing sentence**"*. The qualifier was written for a throwaway mention;
here the policy change is about a third of the body, funded and causally attributed, so the
clause invites the exception the oracle keeps taking. #107 narrows the lens to *"a process
going well **for people**, now"* — and a bereaved family securing a funded national
regulation is a process going well for people on most readings. **The clause boundary and
the lens boundary were doing the same work in two places.** That is why this was an owner
question and not a wording bug.

## 2. Ruled

**The row stays adverse, and the fix is on COMMENCEMENT, not on prominence.**

A policy change that has **not yet taken effect** is an announcement, however prominent in
the article, however well funded, and however clearly caused by the events reported.

⭐ **The article supports the ruling on its own text**, which was not noticed until
2026-09-03: every verb in its good half is future — *"will be banned from September"*,
*"will triple"*, *"will state"*, *"will scrutinise"*. Published 9 August, nothing had
commenced. §1 already draws exactly this line for money (*"money committed is not a
protection established… a facility operating, a **law enacted**, a service running is a
different thing"*); the oracle read an announced-with-a-date regulation as an enacted one.

⛔ **Rejected: the prominence fix** (strike *"especially as a trailing sentence"* so any
after-the-fact policy change scores 0–2 however much of the article it occupies). It would
also demote policy changes that **have** commenced, which §1 deliberately scores normally.

## 3. Placement — inside §2, decided by measurement

The clause fires **only inside §2** ("harm answered is not harm undone"), i.e. only where the
policy change is a response to the harm the article is about. It is **not** added to §1.

⛔ **This corrects the option text the ruling was chosen from**, which described the fix as
*"extends §1's existing money-committed rule"*. Measured, that scoping is ~4× wider and
demotes rows that read as correct today — *California passes toughest wildfire rules* (5.43),
*France's constitutional authority strikes down social media ban for under-15s* (4.85),
*Hong Kong unveils its first dedicated psychiatric facility for under-18s* (4.98). The
direction of the ruling is unaffected; its placement is now set by data.
Evidence: `docs/evidence/2026-09-03-v8-1-qualifier-blast-radius/`.

## 4. Blast radius, and what it means for the corpus

| scoping | rows touched | above the 4.5 op-point |
|---|---|---|
| **§2-bounded** (adopted) | **67** of 6,586 = 1.02% | **0** |
| §1-global (rejected) | 25 of 456 above-op rows = 5.5% | 25 |

⭐⭐ **Under `--aggregate all`, no verdict-flipped row in the corpus reaches the op-point** —
1,011 flipped rows, maximum **4.3667**. So the §2 leak, as it appears in this corpus, costs
**criterion 1**, not reader trust. ⛔ Empirical, not mathematical: one capped run with two at
10.0 gives 7.33, and the nursery row's own 4.400 is above the corpus maximum.

⚠️ **The clause is narrow, and should not be described as general.** Only ~4–8 of the 67
nursery-shape rows show not-yet-commenced language at all (window-sensitive). The rest are
§2's other bullets — a demand, a plea, a municipal condemnation, aid dispatched, a pledge
with a date. **The fix repairs the nursery row and leaves ~60 of the 67 where they are.**

## 5. ⛔ What is NOT decided, and must not be read as decided

- **The clause is unwritten and untested.** ~6 calls: re-score the nursery row k=3 under the
  current and amended §2, and re-score the Travelodge row as the negative control (its policy
  change genuinely is one trailing sentence and both oracles score it ~0.77 today — the fix
  must not move it).
- **No relabelling is authorised.** 6,586 labels stand at `prompt_hash 003cd35a5122`. Whether
  v8.1 ever re-scores the corpus is a separate decision, and §4 is the argument that it need
  not: the affected rows are all below the op-point.
- **Criterion 1 remains FAILING until the clause is written and measured.** It is not
  discharged by this ruling and must not be read later as passed.
