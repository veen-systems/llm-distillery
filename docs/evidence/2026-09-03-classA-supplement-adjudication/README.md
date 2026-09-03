# The 47-row class-A supplement, adjudicated — and what the labels say about themselves

**2026-09-03. $0** — no oracle calls. Reads `EXP-010`'s labels only.
Reproduce: `PYTHONPATH=. python3 docs/evidence/2026-09-03-classA-supplement-adjudication/adjudicate.py`

Discharges the `tp_fp_status: adjudication-pending` item carried since the 2026-08-29 draw
(`docs/evidence/2026-08-29-v8-corpus-draw/corpus_manifest.json`) and named as still-open in
`docs/decisions/2026-09-01-v8-oracle-ruling.md` §4.

⚠️ **What this source excludes.** 6,586 labelled against 6,590 drawn (four scrape-junk skips).
The supplement is the **47** class-A rows in the two above-op design cells; the other **35**
class-A rows sit below the op-point and are **neither TP nor FP** under the 2026-08-30 ruling.

---

## 1. v8 demotes 68% of the rows v7 got wrong

| | |
|---|---|
| supplement rows (v7 ≥ 4.5, harm title, stage 2) | **47** |
| v8 **demotes** below the op-point | **32 = 68.1%** |
| v8 keeps above it | **15 = 31.9%** |
| verdict-flipped | 14 = 29.8% (corpus: 15.35%) |
| verdicts | `in_scope` 21, `out_of_scope` 10, `response_to_harm` 9, `harm_is_subject` 7 |

**That is the headline: two thirds of v7's harm-title false positives are gone at the label
level.** The 29.8% flip rate confirms the slice is genuinely harder than the corpus — the
manifest's warning was right.

## 2. ⛔ The 15 survivors are **11 events**, and one event is **9 rows corpus-wide**

Reading 15 rows as 15 independent judgements overstates the evidence by ~40%. Seven of the 15
are the same news event — the US removing Syria from its state-sponsors-of-terrorism list — and
two more are one Indian court case reported twice.

⛔ **Corpus-wide the Syria cluster is 15 rows, 9 of them above the op-point** — 2.0% of the
entire visible set, one event. ⚠️ **My first count said 14 / 8.** It matched English titles,
so it missed `47年続くシリアの「テロ支援国家」指定を解除` (ja, 4.80). ⭐ **The oracle's
`dominant_subject` is written in English whatever the article's language, which makes it a
language-independent matching surface that a title regex is not.** Seventeenth occurrence of
*establish what a source excludes*, and the smallest yet — off by one in both numbers.

✅ **Near-duplication is NOT systemic.** Corpus-wide: 0 exact content duplicates, 19
near-duplicate title clusters covering 49 rows = **0.74%**, and only **1.3%** of above-op rows.
The Syria cluster is an outlier, not a symptom. (That scan is title-Jaccard, so it is a **lower
bound** — it too missed the Japanese row.)

✅ **And within the cluster the oracle discriminates rather than drifting**: substantive
reports of the removal score 4.25–5.67, while reaction pieces — *"Jordan welcomes…"*,
*"Arab countries applaud…"*, *"Türkiye hails…"* — score 1.57–3.40. **The 4.1-point spread
across one event is signal, not noise**, and it is the prompt's occasion rule working.

## 3. ⭐⭐ A label-quality instrument that needs no lexicon: the oracle contradicting itself

Read the oracle's own `dominant_subject` against the oracle's own score. A hit is one JSON
object disagreeing with itself — no article text, no keyword list over content, and it works
across languages because `dominant_subject` is always English.

Over all **456** above-op rows:

| family named in `dominant_subject` | rows | share |
|---|---|---|
| proposal / not yet enacted | 3 | **3 = 0.7%** |
| announcement / pledge / plan | 12 | 2.6% |
| funding committed | 3 | 0.7% |
| call for / demand / appeal | **0** | 0.0% |
| harm as the subject | 10 | 2.2% |
| benefit reaches no person (§3) | 7 | **7 = 1.5%** |

⚠️ **"Harm as the subject" is mostly the guard WORKING**, not a defect family: the murder-rate
decline (6.95), Lebanon abolishing the death penalty (6.67), NYC's Cure Violence programme
(6.47) are harm-as-setting with an outcome as the occasion, which §1 explicitly protects. **Do
not read that row of the table as 10 errors.**

## 4. Candidates I would put to the owner, in priority order

**A. Self-contradiction — the oracle named the disqualifier and scored it high anyway.**
Under ADR-023 these are the expensive errors: all are above the op-point, where a false
positive reaches a reader.

| score | article | why |
|---|---|---|
| 6.33 | *What could change for U.S. teens on Instagram and Facebook* | *"Meta's **proposed settlement**"* — nothing delivered |
| 6.00 | *Zelensky announces preparations for next prisoner exchange* | *"**preparations for** next prisoner exchange"* — not an exchange |
| 5.10 | *Spain plans transfer of 500 migrant children from Ceuta* | *"Spain's **plan** to transfer"* |
| 4.83 | *Vietnam mulls scrapping death penalty* | *"legislative **proposal**"*; draft laws scheduled for discussion |
| 4.68 | *Tamil Nadu CM announces full waiver on farm loans* | *"farm loan waiver **announcement**"* — §1's money-committed family verbatim |
| 4.55 | *California Legislature passes balcony solar bill* | a bill passed, not enacted — weaker than the others |

⭐ **These fall through a real gap: §1's announcement rule is written in terms of MONEY**
(*"funding secured, mobilised, pledged or allocated"*). A **legislative** proposal has no rule
pointing at it. That is a v8.1 candidate **distinct from** the commencement clause ruled today
(`docs/decisions/2026-09-03-v8-1-commencement-clause.md`) — *proposed but not enacted* is a
weaker state than *enacted but not commenced*, and only the second was ruled on.

**B. §3 — does the benefit reach a person?** An owner question, not a defect claim.

- The **Syria cluster** (9 rows above op). §3 excludes *"an outcome delivered to… a
  jurisdiction's reputation"*, and the article's own forward-looking clause is *"will help
  foster additional investment"*. Against that: sanctions relief plausibly reaches people.
- *Health insurance outpaces traditional medical aid* (4.80), *battery storage systems
  reshaping Australia's electricity market* (4.77), *Heat-pump water heaters keep getting
  better* (4.57) — all three name a **market** as the beneficiary.

**C. Judicial relief to convicted offenders.** Three rows: a 105-year-old murder convict
granted Supreme Court relief (5.37, reported twice) and the Bombay High Court freeing a 2006
kidnap-murder convict on good conduct (4.73). A delivered outcome to an identifiable person —
and the person is a convicted offender. Same family as the nursery row: the lens boundary,
not a wording bug.

## 5. What is NOT claimed

- **No label was edited.** Editing labels by hand is how a corpus stops being reproducible
  (2026-09-02 review §5). Every row above is a candidate for a **v8.1 prompt** pass.
- **These are my readings, not rulings.** Group A is close to self-proving; groups B and C are
  editorial and belong to the owner.
- **No production claim.** These are oracle labels over the drawn corpus, not student scores.
