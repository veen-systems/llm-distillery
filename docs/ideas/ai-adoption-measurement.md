# Measuring "true AI adoption" in SMEs and larger companies

**Status:** PARKED 2026-08-11 by Jeroen ("interesting, park it as an idea").
Nothing built, nothing measured, no spend.
**Origin:** owner side question — *"people wonder about true AI adoption among
SMEs (and larger companies). Could we find answers using our pipelines?"*

## The answer in one line

**Not the question as asked.** Our corpus is articles; adoption happens at firms.
The pipeline can measure AI-adoption **discourse** rigorously, actual adoption
barely at all — and there is one input change (job postings) that would get close
to the literal question.

## Why the literal question does not fit the corpus

This is the same population error as #108, where a clean corpus-level result died
once length turned out to be near-collinear with outlet. Here the mismatch is
more basic: **the unit of the corpus is an article, and the unit of the question
is a firm.**

- **SMEs are ~99% of firms and close to 0% of coverage.** A plumbing firm using
  an LLM to draft quotes is never written about. Any SME-specific number from a
  news corpus describes the atypical SME that attracted a journalist — a
  selection effect the size of the finding.
- **A quarter of the input cannot support content judgment at all.** Google News
  is **25.7% of the production corpus and 100.0% sub-300-char headline echoes**
  (measured, NM#310, `memory/google-news-corpus-hypotheses.md`).
- **Coverage volume tracks the hype cycle, not deployment.** Announcements,
  funding rounds and backlash all generate articles. A working deployment nobody
  publicises generates none.
- **No firm-level ground truth exists to validate against.** Oracle scores are
  labels, not truth ([[feedback-oracle-not-ground-truth]]), and here there would
  be nothing to check them against.
- **Source composition would drive the answer.** Country and sector coverage skew
  is exactly the confound #108 documents.

Publishing "AI adoption among SMEs is X%" off a news corpus would be measuring
journalism. Say so plainly if anyone proposes it.

## What the pipeline WOULD answer well

Reframed to what the corpus actually contains:

> Of AI-adoption claims in the press, what share are **concrete deployments**
> versus announcements, pilots or vendor marketing? Is that ratio moving over
> time? Does it differ by company size, sector and country?

That is a defensible measurement of whether the discourse is maturing, and it is
a shape this repo already implements. `solutions v6` scores
`solution_concreteness` and `evidence_strength`, and its oracle prompt already
makes the needed discrimination — the tech/governance/hybrid tiebreak separates
"a subsidy that *enabled* a deployment" from "a redesigned subsidy", which is the
same judgment as "announced AI" versus "running AI".

Candidate dimensions: deployment concreteness · organisation size · business
function · evidence strength · **reversibility** (was it reported switched off —
the abandonment signal nobody tracks).

Fits the standalone oracle-only outlet direction rather than an ovr.news lens
([[project-standalone-outlets-direction]], `re-enchantment-outlets.md`).

## The input change that gets close to the literal question

**Job postings.** A vacancy is firm-level, carries company size and sector, exists
for SMEs as well as enterprises, and publishes continuously. Training a scorer on
*"does this posting indicate operational AI use, versus AI-adjacent buzzwords"* is
precisely what this machinery does, and AI-skill demand in vacancies is a
respected adoption proxy in the economics literature.

If FluxusSource can ingest a vacancies feed, the rest of the stack is unchanged.
**This is the highest-leverage move if the goal is adoption rather than
discourse.** For large firms, earnings-call transcripts are the other firm-level
text source — but they measure what executives claim, which is its own bias.

## Cheap first probe — do this BEFORE designing anything

**Base-rate screen over the existing corpus: how much AI-adoption content is in
there at all, and how does company size distribute?** No oracle spend, roughly an
hour.

**Kill criterion:** if AI-adoption content is a fraction of a percent, or if
SME-attributable items are near zero, **stop — no filter fixes a corpus that does
not contain the material.** Today's `solutions v6` result is the precedent: its
`community_practice_strength` dimension is fine and its labels are sound; it has
41 positives in the test split because the corpus genuinely lacks that content.
That was a sourcing problem wearing a modelling costume
(`memory/solutions-v6-dimension-hypotheses.md`).

## Costs, if it were ever resumed

Oracle for an 8K-article training set is ~$9 off-peak (DeepSeek) or ~$14 (Gemini
Batch) — see `memory/oracle-pricing-scheduling.md`, and re-check it first, a
DeepSeek price rise is announced (#103). The build is cheap and the playbook
exists; **validity is the hard part, not cost.**

## What is measured vs. reasoned here

**Measured:** the Google News share and stub rate; `solutions v6`'s dimensions and
its 41-positive shortfall; oracle per-article pricing; the #108 collinearity.
**Reasoned, not measured:** everything about how much AI-adoption content our
corpus holds, and the SME coverage rate. The probe above exists to convert that
into numbers before anyone commits.
