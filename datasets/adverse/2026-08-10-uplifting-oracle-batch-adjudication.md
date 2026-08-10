# Adjudication — the 21 `solutions_story` candidates, uplifting v7

**2026-08-10. Adjudicator: Claude Opus 5, editorial judgement, open to owner override.**
Source: [`candidates/2026-08-09-uplifting-oracle-batch.jsonl`](candidates/2026-08-09-uplifting-oracle-batch.jsonl)
(34 rows), companion note [`2026-08-09-uplifting-oracle-batch.md`](2026-08-09-uplifting-oracle-batch.md).

**Outcome: 7 accepted, 3 rejected, 11 held.** The 7 are appended to
[`uplifting.jsonl`](uplifting.jsonl), which goes from 4 rows to 11.

---

## First, the framing was wrong — and it changes what this batch means

The 2026-08-09 note said:

> The dominant failure is not randomness — **uplifting is absorbing solutions-lens
> material**, which has its own filter.

and `docs/TODO.md` carried that forward as *"under ADR-015 they may legitimately
belong in both lenses, so this decides most of the batch."*

**It decides two rows, not twenty-one.** `content_type` is not a lens-routing
signal. Read `filters/uplifting/v7/prompt-compressed.md` §4 (lines 225–245): the
oracle is asked to run five checks — `corporate_finance` (cap 2.0),
`military_security` (4.0), `speculation` (3.0), `doom_framed` (4.0),
`individual_crime` (3.0). **`solutions_story` is not one of the checks.** It is a
value in the output enum with no rule attached, i.e. the residual bucket for
"none of the five penalty flags applied."

And it is the tag the prompt puts on its own *good* examples: the **7.3/10 HIGH
SCORE** agroforestry example (line 300) and the **5.8/10 MEDIUM** food-bank
example (line 331) are both `"content_type": "solutions_story"`.

So `solutions_story` on an off-lens row means "the oracle applied no cap", which
is what you would expect of *any* article that is merely bland rather than
disqualified. Reading it as "this belongs to the solutions lens" inverted the
field's meaning. The ADR-015 overlap defence applies to the two rows that are
actually solutions stories (Rwanda–EU agricultural financing; arguably the
Namibian child-welfare item), and to nothing else.

**What the 21 actually are**, by reading them:

**These labels OVERLAP — this is a description, not a partition, and the column
does not sum to 21.** Sylvia Earle is listed under both "general news" and
"body-extraction defect" (short body, judged genuine); the Namibian minister
under both "general news" and "genuine solutions story". Two rows are described
elsewhere rather than here: the coffee frog (Q2, adjacent-lens) and the celebrity
protein diet (Rejected). Distinct rows covered below: **19 of 21**. The outcome
counts that matter — 7 accepted + 3 rejected + 11 held = 21 — are a partition and
are verified against the file.

| shape | n | rows |
|---|---|---|
| academic abstract / preprint (OpenAlex, MDPI, PLOS, bioengineer) | **9** | papaya oil, rodent LCA, GIS flooding, nomadic tents, nanovesicles, Moringa yogurt, AI-in-fashion, JESIP report, PLOS trust-IRT |
| general news & features (essay, heritage, profile, sport, speech, regulator) | 7 | FAZ punctuation, estancia, Sylvia Earle, CAN féminine, Namibian minister, EBA dashboard, AI olympiad |
| body-extraction defect (not the article) | 3 | Post-Courier paywall stub, Japan Today photo caption, *(Sylvia Earle blurb — judged genuine, see below)* |
| genuine solutions story | 2 | Rwanda–EU agri financing, Namibian child welfare |

**The dominant failure class among the 21 is academic-abstract register**
— 9 of 21, 43% — not lens overlap. Abstract prose supplies benefit vocabulary
("promising", "sustainable", "improvement", "enrichment") and a high
`evidence_level` from study-design words, with no beneficiary anywhere in the
text. That is a different fix from lens de-confliction and it should be tracked
as its own thing.

---

## The three tests each row had to pass

Promotion to `uplifting.jsonl` asserts, permanently, that **`predicted_wa ≤
3.85`**. That is a strong claim, so:

**1. Decidability (#95).** The observed prediction must sit more than the 0.16
batch-composition noise floor above the bar, or the probe flaps between runs and
tests nothing. **The general rule is `raw ≥ max_acceptable_wa + 0.16`**; for
*this file* that is `raw ≥ 4.01`, because uplifting's bar is 3.85. **The 4.01 does
not travel** — other filters' bars are far lower (`nature_recovery` 0.6414,
`solutions` 1.0918–1.13, `belonging` 1.6446, `cultural_discovery` 1.6154–2.1867),
so applying 4.01 to them would reject maximally-decidable candidates. Nothing
enforces either form in code: `grep -r 'assertion_margin\|max_acceptable_wa'`
over `*.py` returns **zero hits**, so `assertion_margin` is a stored derived
number with no checker, and it goes stale silently if `max_acceptable_wa` ever
changes. Treat it as documentation of the check that was made, not as the check.

**2. Oracle confidence.** The batch selected rows the oracle put below 4.0, but
an `oracle_wa` of 3.95 is not a negative — it is a coin flip against a 4.0 cut on
a half-point scale where one increment on `human_wellbeing_impact` (weight 0.30)
moves the average 0.15. Rows with `3.5 < oracle_wa < 4.0` are **held**, not
labelled. *(0.5 is a judgement, not a measurement: it is roughly what two or
three single-increment disagreements would cost.)*

**3. Failure layer.** Is the lens boundary what failed, or something else? A
truncated body is an extraction defect; a good article sitting in the wrong lens
is a routing question. Neither belongs in a lens probe suite.

---

## Accepted (7)

Ordered by observed raw score. Every `observed` block was read from the NexusMind
filtered batch the article actually went through, per this directory's README —
not from a rescore.

| raw | margin over 3.85 | oracle | row |
|---|---|---|---|
| 5.1166 | +1.267 | 3.30 | Namibian minister — "boys must not be left behind" |
| 4.9392 | +1.089 | 2.55 | Sylvia Earle career profile (PRX *The World*) |
| 4.7162 | +0.866 | 3.10 | Engineered nanovesicles / METTL3 neuroinflammation |
| 4.3703 | +0.520 | 2.15 | Banana-pseudostem rodent enrichment LCA (MDPI) |
| 4.2899 | +0.440 | 2.70 | EBA ESG risk dashboard |
| 4.1300 | +0.280 | 3.05 | FAZ first-person essay on punctuation |
| 4.0570 | +0.207 | 2.05 | Papaya seed oil solvent screening (OpenAlex) |

Four of the seven carry an explicit **scope warning** in `why_adverse`, following
the Kixikila / Hong-Kong-drones precedent — because each one names a boundary
that is easy to over-generalise:

- **nanovesicles** — the boundary is *preclinical vs delivered*, not biology vs
  not-biology. Medical research with an outcome that reached people still scores.
- **Namibian minister** — the boundary is *announcement vs outcome*. This must
  not teach that gender-equality or child-welfare policy is adverse.
- **rodent LCA** — animal welfare is not out of scope; a laboratory-scale
  prototype LCA read as a delivered collective benefit is.
- **Sylvia Earle** — not a claim that profiles of scientists, or of women in
  science, are adverse; a biography is not a delivered wellbeing outcome.

Two of the seven also document **oracle-prompt gaps**, which is why they are
worth more than their score:

- **EBA dashboard.** The `corporate_finance` cap (max 2.0) enumerates stock
  prices, earnings, funding rounds, valuations, M&A, IPO. **Prudential regulation
  is none of those**, so no cap fired. `justice_rights_impact` came back 5.00 on
  an article containing no rights claim.
- **Namibian minister.** Check C (PURE SPECULATION, cap 3.0) should arguably have
  fired on a "could have consequences" aspiration with no programme behind it,
  and did not. `social_cohesion_impact` 6.38 was earned by the fact that a
  meeting happened.

---

## Rejected (3) — with reasons, because a missing row looks like an oversight

**`pacific_post_courier_png_56ffbe255efb`** — "National Cancer team assesses
Simbu's capacity…", raw 4.240. The stored body is one sentence followed by *"To
access this post, you must purchase Web, Web – One-Day, Web – 14-Day…"*. **This
is a paywall stub, not an article.** The lens judgement cannot be made on a body
that is not the article, and the real story — a national cancer programme
reaching a highland province — is plausibly *on*-lens. Labelling it adverse would
assert the article does not belong when what failed was the fetch.
→ Route to ducroq/NexusMind#306 (enrichment storing a wrong/partial body).

**`east_asian_japan_today_4be8af016f51`** — "Teamwork", raw 4.087. The article is
a 56-character photo caption (*"Garbage men are hard at work on a street in
Tokyo's Chuo Ward"*); the remaining ~600 characters of the scored body are the
reader comment thread and site chrome. Same layer as above, with an extra trap:
`content_length` 653 makes it clear the #93 300-char labelling floor, which
counts the comments, and the article proper is ~60 characters.
→ Route to NM#306 / comment stripping.

**`south_asian_indian_express_da18dde9d2ac`** — celebrity protein diet, raw
**4.004**. Genuinely off-lens, and **rejected anyway**: the assertion `≤ 3.85`
needs a 0.154 move, which is **inside the #95 |0.16| floor**. It is not a
testable assertion — batch composition alone can satisfy or violate it. An
adverse probe whose margin is smaller than the noise floor is a coin flip
dressed as a gate. If this shape matters, it belongs in oracle training data, not
in the probe suite.

*(That third rejection generalises: **`raw ≥ 4.01` is now the admission bar for
this file**, and every accepted row records its `assertion_margin` so the
property is checkable rather than remembered.)*

---

## Held (11) — two questions for the owner, not eleven

### Q1. Oracle-margin rows (6) — mechanical, no editorial call needed

`3.5 < oracle_wa < 4.0`, so the oracle did not put them clearly off-lens:

| oracle | raw | row |
|---|---|---|
| 3.95 | 5.414 | Moldovan schoolchildren, AI olympiad medals (Astana) |
| 3.95 | 4.424 | Moringa-enriched functional yogurt, diabetic rats (MDPI) |
| 3.85 | 4.433 | JESIP emergency-services interoperability report (OpenAlex) |
| 3.80 | 4.530 | Rwanda–EU, $46M agricultural resilience financing |
| 3.75 | 4.982 | CAN 2026 féminine — Algeria beat Côte d'Ivoire |
| 3.60 | 4.317 | Reconfiguring Fashion through AI (Zenodo) |

Resolution is a second oracle pass, not a decision. Two are worth flagging
regardless: **Rwanda–EU is the one genuine ADR-015 case in the batch** — a real
solutions story that may legitimately be uplifting too — and the **Moringa
yogurt** row got `human_wellbeing_impact` **7.5** and `evidence_level` **7.0**
from the oracle **for a study in rats**, which is an oracle defect worth its own
look even though the row is held.

### Q2. Adjacent-lens placement (3) — this one is a line call, and it is yours

| oracle | raw | row | plausible home |
|---|---|---|---|
| 2.85 | 4.044 | New "coffee frog" species found on Costa Rican plantations (n-tv) | cultural_discovery / nature_recovery |
| 2.95 | 4.430 | Estancia Los Remedios still standing in Buenos Aires (La Nación) | cultural_discovery / belonging |
| 3.05 | 4.908 | Nomadic tent traditions as heritage, Antalya (MDPI) | cultural_discovery |

All three are good articles in the wrong lens. Under ADR-015 lenses overlap by
design, so **"delight/discovery is not uplifting" is an editorial line, not a
fact** — and it is exactly the line the Kixikila adjudication warned about
crossing carelessly. One ruling covers all three and probably a recurring class.
Held rather than guessed.

### Q3. Held for curation, not for evidence (2) — the third slice of the 11

`science_plos_one_acf925e84260` (measuring trust in public health authorities,
IRT — raw 4.356, oracle 3.00) and `science_mdpi_sustainability_b578b7a29fa9`
(GIS 3D flooding model, Ho Chi Minh City — raw 4.910, oracle 2.90) both pass all
three tests and would be valid accepts. They were left out to keep one register
from taking 5 of 11 rows in the probe file. Promote them if the abstract class
turns out to need more coverage; the ids are here so nothing has to be
rediscovered.

---

## Two side observations, filed here so they are not lost

**Every accepted row has `tier: medium`** (the `gatekeeper_applied: false` seen in
the source batches is NOT carried into `uplifting.jsonl` — do not look for it
there). The
raw score put all seven above the 4.0 op-point — they surfaced — while
percentile normalization mapped them as low as **0.287** (papaya oil). That is
ADR-014/ADR-022 working as designed (visibility is raw, tier is rank), and it is
the "ranking illusion" this directory's README already warns about: do not
dismiss any of these on the strength of a low normalized number.

**OpenAlex rows carry a broken date.** `OpenAlex_e41a191391ca` has
`"publication_year": 2050` and `"original_published_date": "2050-01-01"`. Not
this batch's problem, but if anything downstream sorts or windows on those
fields, it is wrong now.
