# How wide is the v8.1 §2 fix? — measured on the Phase B labels

**2026-09-03. $0** — no oracle calls. Reads `labels_k3.jsonl` (`EXP-010`) only.
Reproduce: `PYTHONPATH=. python3 docs/evidence/2026-09-03-v8-1-qualifier-blast-radius/blast_radius.py datasets/scored/human_thriving_v8/labels_k3.jsonl`

Owner ruled 2026-09-03 that the nursery row **stays adverse** and the v8.1 fix is on
**commencement** (a policy change that has not yet taken effect is an announcement),
not on prominence. This measures what that clause would touch before it is written.

⚠️ **What this source excludes.** `labels_k3.jsonl` holds **6,586** rows, not the 6,590
drawn — four scrape-junk skips. It holds **zero** adverse and **zero** no-regression rows
(asserted by the script, which exits non-zero otherwise; 22 guard ids declared). **The
nursery row is not in this population**, so its 4.400 is not comparable to any figure here.

---

## 1. ⭐⭐ The leak cannot reach a reader — it costs criterion 1, not reader trust

| | |
|---|---|
| verdict-flipped rows | **1,011 = 15.35%** |
| their **max** `weighted_mean_all` | **4.3667** |
| of them above the 4.5 op-point under `all` | **0** |
| above it under `majority` | 35 |
| in the 3.85–4.5 band (fail criterion 1, invisible in production) | **4** |

Under the adopted `--aggregate all`, **no row whose three runs disagreed on the scope
verdict reaches the op-point.** One run capped at 0–2 pulls the plain mean under the line.

⛔ **Empirical, not mathematical.** One capped run (≤2.0) with two at 10.0 gives 7.33 under
`all`, so nothing *forbids* a flipped row from crossing — this corpus simply contains none,
and the nursery row's own 4.400 sits **above** the corpus maximum. Treat 4.3667 as a
measured ceiling for this corpus, not a property of the aggregation rule.

✅ **Cross-check:** the 35-above-under-`majority` figure independently reproduces the
2026-09-02 label review's §4 count of 35, from a separately written instrument.

## 2. Scoping A — the clause bounded inside §2 (post-harm responses only)

The nursery shape is machine-selectable without a lexicon: runs that split between
`in_scope` and `response_to_harm`.

| | |
|---|---|
| nursery-shape rows | **67 = 1.02%** |
| above the op-point under `all` | **0** |
| above it under `majority` | 13 |
| showing not-yet-commenced language in the occasion | **~4–8** (window-sensitive: 4 @800, 6 @1200, 7 @1500, 8 @2500 chars) |

⚠️ **Tense is not the dominant mechanism of the 67** — roughly one row in ten. Read, the
rest are §2's *other* bullets: a demand (*"Oposición y ONG piden liberar a todos los presos
políticos"*), a plea, a municipal condemnation (*"Wrocław adopts resolution condemning
violence against Ukrainians"*), aid dispatched, a pledge with a date
(*"DPR pledges Asset Forfeiture Bill passage by Dec. 15"*). **The commencement clause fixes
the nursery row and leaves ~60 of the 67 exactly where they are.** That is not an argument
against it — criterion 1 is judged on 9 adverse rows, not on the corpus — but the fix should
not be described as general.

## 3. Scoping B — the clause extended globally into §1's money-committed family

| | |
|---|---|
| above-op rows | **456 = 6.92%** |
| showing not-yet-commenced language | **25 = 5.5%** |
| all above-op verdicts unanimous | **yes** |

⛔ **Recommend against.** The generator's top hits are rows a global clause would demote and
that look correct where they are: *California passes toughest wildfire rules* (5.43),
*France's constitutional authority strikes down social media ban for under-15s* (4.85),
*Hong Kong unveils its first dedicated psychiatric facility for under-18s* (4.98),
*Vietnam mulls scrapping death penalty* (4.83). A law passed with a commencement date is
what §1 already distinguishes *from* money committed — extending the money rule over it
collapses a distinction the prompt makes on purpose.

⛔ **My own framing was wrong here and it was in the option text the owner chose from.** I
described the tense fix as *"extends §1's existing money-committed rule"*. Measured, that
scoping is ~4× wider than the §2-bounded one and demotes rows that read as legitimate
positives. **The clause belongs inside §2**, where it only fires on a response to a harm.
The ruling's direction is unaffected; its placement is now decided by data rather than by
my sentence.

## 4. What this does not answer

- **Whether the clause actually fixes the nursery row.** That is ~6 calls, k=3 under both
  wordings, and it is not run here.
- **Whether the 67 are correctly labelled.** They are below the op-point, so they are cheap
  errors under ADR-023 — but "invisible" is not "right".
- **Anything about production.** These are oracle labels over the drawn corpus. The student
  has not been trained, and the gate applies to student scores over a different distribution.
