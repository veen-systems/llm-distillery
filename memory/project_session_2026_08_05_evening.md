---
name: project_session_2026_08_05_evening
description: Cross-repo board refresh, then the legal/compliance arc — five owner decisions recorded, AI Act art. 50 disclosure completed across all surfaces, EMFA art. 6 ownership published
metadata:
  type: project
---

# Session 2026-08-05 (evening) — board refresh, then the legal arc

Almost all execution landed in **ovr.news**, not here. This repo contributed one
decision record and the memory updates. Nothing was committed in either repo.

## 1. Cross-repo board refresh

Re-queried GitHub because the board had not been read since 2026-08-03. It was wrong
in two places.

**Counts, measured 2026-08-05:** llm-distillery **36** · NexusMind **40** · ovr.news
**90** (63 engineering) · FluxusSource **13** · persuasion-scorer **12** = **191**
(was 177). All growth is downstream.

**Two banded entries were already closed:** ovr#285 (P0, orphan reclamation NULLing
`raw_weighted_average` — so ovr#283's publication-floor decision is unblocked) and
NM#290 (P1, hero chrome). Also closed: NM#293, NM#295, FS#121, LD#64. ovr#299 was
filed *and* closed COMPLETED on 08-05.

**New Chain 15 — lens commensurability.** LD#96 and ovr#296 were filed independently
the same day and are the same defect from both ends: ovr#296's case is *Kixikila lost
Belonging to Discovery by 0.043*, which sits inside LD#95's measured 0.16 noise floor.
The placement was decided by noise. **The unmeasured quantity that sets its urgency —
what share of lens placements is settled by a margin under 0.16 — is nobody's issue
yet**; added as Batch F item 5.

**Batch C became a real compliance programme** headed by ovr#292 (333 of 1,357 source
domains signal an AI opt-out), which **LD#28 inherits**.

Also grouped this repo's own 36 issues in the prioritization memo, because no view of
"what is open here" existed — the P-bands interleave five repos. **14 of the 36 have
not been touched in 30+ days**; the live backlog is ~22.

## 2. The legal arc — five decisions, all owner calls

| # | Question | Decision |
|---|---|---|
| 1 | Oracle sends full article text to Gemini/DeepSeek | **Risk knowingly accepted.** *"This is the only way I can do this, so if someone objects in future, let's see then."* |
| 2 | Do AI-crawler opt-outs bind our fetcher? | **No** — ovr.news ADR-043 |
| 3 | Is training TDM? | **"Not mining, modelling"** — recorded here, in the form that survives scrutiny |
| 4 | Social cards / search snippets | **Disclose**, text marker not badge |
| 5 | Who publishes ovr.news? | **Veen Systems**, publishing under the Busara.eu name |

### What shipped in ovr.news

- **AI Act art. 50 disclosure completed.** `aiGenerated` opt-in prop on `Layout.astro`;
  marker on `<meta name="description">`, `og:description`, `twitter:description`.
  `src` variant covers the summary only (the headline there is the publisher's).
  Verified in a 8,741-page build; 1,103 tests pass.
- **EU icon set committed** (`public/eu-ai-icons/`) and `og-image-article.png` built —
  branded card + AI GENERATED pill, used by 42 of 2,894 articles, zero other pages.
- **EMFA art. 6 ownership disclosure published** at `/accountability#ownership`, and
  `/accountability` added to the footer (it carried the AI Act disclosure too and was
  reachable only from in-page links).
- **GDPR art. 33(5) incident record** for the Comscore beacon.
- New: ADR-043, ADR-044, `docs/compliance-register.md`,
  `docs/security/incident-2026-08-01-comscore-beacon.md`.
- The missing **Recovery** lens added to `og-image.svg` and both cards re-rendered.

### The two findings that changed the work

**The EMFA micro-enterprise exemption does not exist.** Secondary sources said art. 6
exempts micro enterprises; the adopted regulation contains the phrase **zero times**.
So ovr.news is *probably in scope*, and has been since 8 August 2025. It also had
**"Data controller: Busara.eu"** published — an entity the owner confirms does not
exist. Both now read Veen Systems, from one constant.

**The Code of Practice is real** — published 2026-06-10, Commission-endorsed
2026-07-08, obligations live since 2026-08-02. It prescribes **no single marking
technique**, which confirms rather than supersedes ADR-003's IPTC marking, and kills
"wait for a standard" as an option.

## 3. This repo's own change

`docs/decisions/2026-08-05-tdm-opt-out-training-data.md` — the LD#28 position.
Grounds, strongest first: the directives name other parties' crawlers; **the student
model has a regression head and cannot emit text at all**, so no output can substitute
for a publisher's work; and the use is referral, not substitution.

**Recorded against itself:** "modelling is not mining" is *not* a distinction the DSM
Directive draws — its TDM definition is broad enough to cover fitting a model to text.
The position rests on the **reservation** question and on harm, not on being outside
the definition. Two carve-outs stay open: the oracle transfer (decided above, recorded
in ovr.news) and **the seven already-trained deployed filters**, which nobody has
assessed.

## Open

- **FS#120** — still the only calendar-bound item, ~2026-08-14.
- EMFA: confirm `Veen Systems` matches the KvK trade name; no beneficial owner is
  named (deliberate, dated gap — a foundation would close it without exposing anyone).
- `/accountability` source-opt-out copy is now a *knowing* omission: it does not
  mention that 333 carried domains signal an opt-out we decided to keep. Flagged, not
  rewritten.
- Nothing committed in either repo. `data/chief_editor_config.json` was already dirty
  in ovr.news; two `datasets/adverse/*.jsonl` rows appeared in llm-distillery during
  the session and are not mine.

## Related

- [[cross-repo-prioritization]] — refreshed this session, incl. Chain 15
- [[project_session_2026_08_05]] — the morning half (LD#92 identified, GN evidence)
- [[prefilter-length-floor-hypotheses]] · [[score-batch-shape-noise]]
