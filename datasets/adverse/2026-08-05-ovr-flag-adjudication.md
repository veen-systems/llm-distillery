# Adjudication notes — ovr.news reader flags, 2026-08-04/05

Five candidate rows were staged from `scripts/flag-evidence.ts --days 2`. **Four are in the
JSONL; one was deliberately excluded.** This note records the exclusion, because a row that is
simply absent looks like an oversight and the reasoning is the part worth keeping.

## Excluded: `south_american_brasil_de_fato_42843d936b64`

> *Unifesp identifica resíduo compatível com sangue no antigo DOI-Codi/SP*
> `cultural_discovery`, raw 6.1084, batch p99 4.9118 (`filtered_20260804_045930`)
> Reader-flagged 2026-08-04T04:21:37Z: **"Not constructieve i tbink?"**

Forensic identification of blood residue at a former Brazilian dictatorship torture site.
Adjudicated **not adverse** — it belongs in the lens.

**Why.** Every other ovr.news lens requires a *process going well*. In the three
`cultural_discovery` rows that were kept, the actors are long dead and the finding is inert:
nothing is happening now. Here a living federal university is doing forensic work on state
crime today. That is an ongoing process, it is working, and it is the correction for
presentism in its purest form — the past is demonstrably not sealed off.

**What decided it was the consequence, not the article.** Labelling this adverse teaches the
scorer to suppress a category: truth commissions, mass-grave identification, war-crimes
forensics, transitional justice generally. Those are stories a constructive outlet should
want. ADR-042 ("editorial uncertainty resolves toward exclusion") governs uncertainty about
one article; it should not be used to define a category away on the strength of a single
example.

**The reader was not wrong to hesitate, and the fault looks like ours.** The ovr.news summary
title was *"Researchers find blood traces at former São Paulo dictatorship site"* — leading
with the residue and burying the accountability. That is a summarization framing problem, not
a lens-fit problem, and filing this as adverse would have fixed the wrong layer while making
the scorer worse. Tracked at ducroq/ovr.news#298.

**Boundary now recorded** in ovr.news `docs/BRAND.md` § What makes a finding constructive,
which had been left explicitly open pending this call.

## Note on the kept rows

- The two smallpox rows (`german_spiegel_wissenschaft_…`, `spanish_la_vanguardia_…`) are the
  **same study** in two languages, published to the same feed the same day. Treat as a pair.
  Their co-occurrence is also evidence for the cross-language dedup gap (NexusMind#291/#295).
- The `nature_recovery` row carries a **scale caveat** in its `why_adverse`. The label holds;
  the magnitude does not, because that batch's raw distribution is collapsed (median 0.2383)
  and the normalization producing its p99 is itself under investigation in #75/#76. Do not
  quote its "3.4× p99" as a clean figure.
- ~~`heritage_significance` is **7.10 on all four** `cultural_discovery` cases, identically.~~
  **Wrong — corrected 2026-08-06.** Atapuerca is **6.40**; the other three are 7.10. See the
  second-batch section below for the accurate version and why the observation still stands.

## Second batch, same day (`--days 1`, four flags)

Four more flags arrived later on 2026-08-05. Two were accepted (`cultural_discovery` Kixikila,
`solutions` Hong Kong drones) and are described in the README's 2026-08-05 section. Two were
image-pipeline failures — a Times of India default share image (`msid-47529300.cms`) served as
the hero on four articles — and are **not** lens adverse examples; they belong to ovr.news.

Three things from this batch that outlive the rows:

- **`heritage_significance` = 7.10 on FOUR of five `cultural_discovery` cases — and the
  "all four" claim in the section above was wrong when it was written.** Actual values:
  Atapuerca **6.40**, smallpox DE 7.10, smallpox ES 7.10, Inca 7.10, Kixikila 7.10. So it was
  three of four then, four of five now. Corrected here rather than silently, because the wrong
  version was the basis for the #87 suggestion and anyone re-deriving it would not reproduce it.

  What survives the correction is the part that matters. The three earlier 7.10s share a subject
  cluster (ancient remains, archaeological science), so their agreement could be coincidence.
  Kixikila shares nothing with them — it is a living financial practice in Angola — and lands on
  the identical 7.0999999. That is the observation worth probing in #87: the dimension may be
  near-constant for anything the scorer recognises as heritage at all, in which case it carries
  no discriminative signal and its weight is doing harm. Atapuerca at 6.40 does not refute this;
  it just means the constant is not universal.
- **The draft `filter` from `flag-evidence.ts` cannot be trusted.** It reads ovr.news
  `articles.filter` (last-writer-wins at ingestion), not the published lens. Kixikila was
  drafted as a `belonging` adverse row when belonging is the lens it *should* have published
  under; it lost to `cultural_discovery` by 0.043 normalized. Appending that draft unedited
  would have taught belonging to reject a correct belonging article — a sign-flipped label,
  which is worse than a missing one. Cross-check `published_observations.lens` and
  `article_filter_scores` before accepting any draft.
- **A near-miss on scoping.** Both accepted rows are the kind that generalise badly if the
  rationale is dropped: one is about a non-Western cultural practice, the other about
  workplace-safety enforcement after a fatal fire. Each carries an explicit "do not learn
  this" paragraph in `why_adverse`. If these rows are ever reduced to (text, label) pairs for
  training, that scoping is lost and both become harmful. They are gate probes first.

## Provenance

Rationales were operator-drafted and owner-confirmed on 2026-08-05; `labelled_by` on each row
says so. They are editorial judgement, not oracle scores — `max_acceptable_wa` is an
upper-bound assertion. The second-batch rationales were drafted from a joint operator/owner
triage of the four flags on 2026-08-05 and follow the same rule: the observed block is
mechanical, `why_adverse` and `misleading_features` are judgement.
