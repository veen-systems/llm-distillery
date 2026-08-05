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
- `heritage_significance` is **7.10 on all four** `cultural_discovery` cases, identically.
  Possible saturation, worth checking independently of these rows (#87).

## Provenance

Rationales were operator-drafted and owner-confirmed on 2026-08-05; `labelled_by` on each row
says so. They are editorial judgement, not oracle scores — `max_acceptable_wa` is an
upper-bound assertion.
