# The §5b no-regression set, assembled — and the free local judge fails it

**2026-08-23. No spend, nothing deployed, no model trained.** Two results, one of which
retracts the framing of a claim I made earlier the same session.

---

## 1. The set existed only as prose, and it is 3 articles, not 4

`docs/HUMAN_THRIVING_V8_PLAN.md` §5b is referenced by **three** gates — step A5's calibration
sample, Gate B-C, and acceptance **criterion 2, marked BLOCKING**. It existed as a
four-row markdown table and nothing else. No file in `datasets/adverse/` held it; the
directory README does not mention it. **The plan's only blocking control against
over-suppression was unexecutable.**

Now assembled as **`datasets/adverse/uplifting_no_regression.jsonl`**, full text, no excerpts
(§5b's own method rule: three of five drafts reversed on reading the full article).

⛔ **It is THREE articles.** The fourth table row — *Namibian child-welfare /
gender-equality policy items* — has no article behind it. Its only concrete instance,
`south_african_namibian_6ec2eb173e48`, is one of the **18 accepted adverse rows** (class B,
raw 5.1166), carrying a *scope warning*: "the boundary is announcement vs outcome, not
'policy is adverse'". A labelling caveat on an adverse row is not a row that must score above
the op-point — which is why its "reader's real objection" cell is `—`.

⚠️ **The three carry different assertions; only two are op-point assertions.**

| guards | article | assertion | baseline |
|---|---|---|---|
| recovery narratives | Rappler, "The silent crisis on our plates" (13,107 ch) | raw > 4.5 | observed **6.4864** |
| transitional justice | Unifesp / DOI-Codi forensics (4,761 ch) | `evidence_level` not forced to 0–2 | **6.11 on `cultural_discovery`** — never scored by uplifting, so "above the uplifting op-point" is not a claim its history supports |
| lens overlap (ADR-015) | Rwanda–EU $46M agri financing (1,896 ch) | raw > 4.5 | ⚠️ **none** — it was *rejected* as adverse, so no `observed` block was ever written |

### Provenance, and one trap

Two of the three had **aged out of every JSONL on sadalsuud** — `data/filtered/`, `data/raw/`,
everything. They survive in **`ovr.news/data/ovr.db`'s `articles` table**, the superset
`memory/nexusmind-data-sources.md` points at. Rappler came back at **13,107 chars, matching
its recorded `content_original_length` exactly** — an integrity check, not a coincidence.

⛔ **`grep -rl` on an article id returned three files that do not contain the article.** The
Rappler id appears inside a *different* row's `nexus_mind_attributes` — the Express Tribune
"Poison on our plates" — as a cluster co-member. Two articles with near-identical titles,
co-clustered: the centroid-inheritance shape of the 79.3% sub-threshold merge artefact
(NM#188/#228/#278). **A grep for a string is not a grep for a row**; parse and compare the
`id` field.

---

## 2. ⛔ The free local judge cannot arbitrate Phase A — and this retracts my earlier framing

**What I claimed earlier today**, in the commit for the generalized harness: a 2-row smoke
test where `qwen3:14b`, on v7's *unchanged* prompt, scored two class-A rows **0.0 and 1.0**
against production's 6.846 and 5.976 — reported as *"consistent with the step 1 finding"* that
v7's scope check already covers class A.

**That framing does not survive its own control.** Same judge, same unchanged prompt, k=3,
on the three no-regression rows:

| article | run scores | mean | spread | above 4.5 |
|---|---|---|---|---|
| Rappler (recovery) | 2.300 / 5.250 / 3.650 | **3.733** | 2.950 | **1 of 3 runs** |
| Unifesp (transitional justice) | 0.000 / 1.150 / 1.150 | **0.767** | 1.150 | 0 of 3 |
| Rwanda (lens overlap) | 1.000 / 2.000 / 1.000 | **1.333** | 1.000 | 0 of 3 |

**The judge that zeroed the class-A rows zeroes the true positives too.** Getting class A
"right" costs it nothing, because it puts nearly everything in the 0–2 band. A verdict from an
instrument that cannot say *yes* to a known positive carries no information about class A —
the positive-control half of the standing rule, and I ran the negative arm first and read it
as a result.

⚠️ **Second, independent problem: the spread.** Mean **1.700**, max **2.950** across k=3 —
roughly **2× the recorded oracle run-to-run floor** (0.82 mean / 2.25 max) and ~10× the #95
batch band (0.16). The Rappler row swings **2.300 → 5.250**, crossing the op-point *inside its
own spread*: its verdict is indeterminate at this k, whatever the mean says.

### What this does and does not mean

- ⛔ **It does not mean the Phase A drafts are wrong.** Nothing here tests them; both runs used
  v7's unchanged prompt.
- ⛔ **It does not vindicate v7's prompt either.** That was the reading I published and it is
  withdrawn.
- ✅ **It means the $0 path I recommended cannot decide Gate A as proposed.** A judge must
  clear the no-regression set *before* its verdict on the adverse set means anything.
- ✅ **The no-regression set has already paid for itself** — it killed a wrong conclusion of
  mine within an hour of existing, which is what a blocking control is for.

---

## 3. The model control: it is `qwen3:14b`, not local 14B judges

Same prompt, same rows, same k=3, `qwen2.5:14b`:

| article | qwen3:14b mean (spread) | **qwen2.5:14b mean (spread)** | assertion |
|---|---|---|---|
| Rappler (recovery) | 3.733 (2.950), 1/3 above 4.5 | **5.533 (0.450), 3/3 above 4.5** | ✅ **passes** |
| Rwanda (lens overlap) | 1.333 (1.000), 0/3 | **4.467 (0.650), 2/3 above 4.5** | ⚠️ straddles the op-point |
| Unifesp (transitional justice) | 0.767 (1.150) | **1.883 (0.050)** | see §4 — assertion was wrong |

⭐ **The instrument problem is model-specific, and the run-to-run spread is the tell.**
`qwen2.5:14b` averages **0.383** spread (max 0.650) against `qwen3:14b`'s **1.700** (max
2.950) — **4.4× tighter**, and *below* the recorded oracle floor of 0.82/2.25 rather than
double it. It is also **2.8× faster** (9.2s vs 26.2s per article). ⚠️ Likely the
reasoning-mode interaction already recorded for the `deepseek-v4-flash` alias in
`memory/gotcha-log.md` (2026-08-14) — **not established here**, and worth one experiment
before any judge selection is settled.

**So a $0 local instrument does exist** — it is just not the one §1f's bake-off reached for.
⛔ But `qwen2.5:14b` clears only **one** assertion outright; Rwanda straddles. Do not promote
it to "the Phase A instrument" on n=3.

---

## 4. ⛔ Correcting one of my own assertions, one hour after writing it

I gave the Unifesp row the assertion *"`evidence_level` not forced to the 0–2 band"*. **That
is mis-specified.** The article was scored by `cultural_discovery` (raw 6.11) and **never by
`uplifting`**, so its absolute standing under the uplifting prompt was never established or
endorsed by anyone. Measured under v7's *unchanged* uplifting prompt it already sits in the
0–2 band on **both** judges — so the bar fails **v7**, and a v8 measured against it would be
scored against a baseline nobody ever accepted.

**Corrected to a DELTA:** v8 must not score it *lower than v7* under the same prompt family
and the same judge. What §5b guards is that the v8 **rule** does not suppress transitional
justice — a before/after question, not an absolute band. The v7 baselines are now stored on
the row (`baseline_v7_uplifting_prompt`).

⚠️ **General form, worth carrying:** *an absolute bar on a row whose baseline was never
established cannot confirm anything* — it measures the prompt family, not your change. Check
which of the remaining assertions in this repo have that shape.

---

## Next

1. If `qwen2.5:14b` is to be the Gate A instrument, **widen the control set first** — n=3 with
   one straddler is not a qualified instrument. And test the reasoning-mode hypothesis in §3.
2. Otherwise Phase A's calibration needs the **real oracle** — Gemini Batch at
   ~$0.0018/article, so the ~30-article sample is **cents**, not a budget question
   (`memory/oracle-pricing-scheduling.md`).
3. **Establish the Rwanda row's op-point baseline** properly; today it has only these two
   local-judge readings and no production `observed` block.
4. ⚠️ **k=1 is not usable here whatever the instrument.** Report the per-article spread beside
   every verdict; the harness prints it.
