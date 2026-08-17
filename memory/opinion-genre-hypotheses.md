# Opinion / editorial as a genre signal — llm-distillery#121

**Status 2026-08-16: measured once, at scale, and the motivating hypothesis is
REFUTED where it is measurable.** No stamp built, none justified yet. This file
exists so the next session does not re-run the confounded version.

⛔ **Read the two traps before quoting any number from #121's issue body.**

---

## Traps

1. ⛔ **#121's first-look table measures `solutions` at op-point 4.0. It is 2.25.**
   Runtime source, `NexusMind/filters/solutions/v6/base_scorer.py`,
   `("medium", 2.25, "Concrete pilot or early-stage solution")`. The issue's
   `solutions` row (`0/33` vs `11/2232`) is therefore 1.8 points above where that
   lens surfaces, and **that manufactured zero is one of the two the issue's
   "this contradicts my motivation" paragraph rests on.** At 2.25 the non-opinion
   arm is **8,809/229,582 = 3.84%**, not 0.5%. Corrected in a comment on the
   issue, not in its body — refuting in place beats deleting.
   *(The other five were verified correct against the same source: `uplifting`
   4.5, `investment_risk` 4.25, `belonging` 4.0, `cultural_discovery` 4.0,
   `nature_recovery` 3.75.)*

2. ⛔ **A substring detector builds the hand-built population this issue warns
   about.** Every token below was excluded because it fires on a *publisher
   name* or an unrelated genre, with the count that motivated it:
   - `*_tribune` — `express_tribune`, `qatar_tribune`, `texas_tribune`,
     `la_tribune`: **57 rows**. Same for `village_voice_news`, `global_voices`,
     `scotusblog`, `aws_ml_blog`. The source arm therefore matches a **trailing
     token only** (`_opinion`, `_meinung`, `_opinie`, `_editorial`), which is why
     it fires on 120 rows, all `spanish_elpais_opinion` + `swiss_nzz_meinung`.
   - `live-blog` / `liveblog` / `live-blog-update` — **52 rows**, breaking news.
   - url `blog` / `blogs` — **16 rows**, publisher blogs.
   - tag `analysis` — **125 rows**, dominated by `fundamental-analysis` /
     `market-analysis` (finance genre) and `thought-leadership` (marketing).
     Also dropped `tribunal*`, `religious leaders`, `polls and public opinion`.

3. ⚠️ **`nature_recovery`'s null carries no information and must not be quoted as
   one.** 68 of 92 within-source strata are tied at **0 vs 0**, because the lens
   surfaces 365 of 229,588 rows (**0.16%**) corpus-wide, so at n≈10–30 per
   stratum most strata cannot produce a positive in *either* arm. The instrument
   could not have said yes. See CLAUDE.md's working rule and
   `memory/working-rules.md`.

---

## Population (pipeline-computed, not hand-built)

Every row NexusMind persisted to `data/filtered/<lens>/filtered_*.jsonl`,
**2026-08-02 → 2026-08-16, 85 cycles, deduped by `id`**: **233,338 rows**
(169,922 for `investment_risk`, which excludes more source types), of which
**3,750 = 1.61%** flagged opinion. Dedup removed only 700 rows (0.3%), i.e. each
cycle persists near-entirely new articles.

⚠️ **Known exclusions, applying to BOTH arms:** these files are written under
`if result["passed_prefilter"]`, so they are 100% prefilter passers by
construction, and source-type-excluded rows never reach them. Within-source both
arms lose the same rows. See `memory/nexusmind-data-sources.md`.

---

## Result — rate above op-point, naive vs within-source

Strata = source, included when a source has ≥10 rows in **both** arms. `MH OR` is
the Mantel–Haenszel common odds ratio; `hi/lo/tie` counts sources by direction.

| lens | op | naive ratio | **MH OR (within-source)** | hi/lo/tie | reading |
|---|---:|---:|---:|:--:|---|
| `belonging` | 4.0 | 1.57× | **0.98** | 29/53/10 | **gone** |
| `uplifting` | 4.5 | 1.15× | 0.89 | 34/52/6 | **gone** |
| `nature_recovery` | 3.75 | 0.67× | 0.97 | 3/21/**68** | ⛔ uninformative |
| `cultural_discovery` | 4.0 | 1.30× | 1.27 | 29/40/23 | weak, split |
| `solutions` | **2.25** | 0.58× | **0.50** | 18/**66**/8 | **reversed** |
| `investment_risk` | 4.25 | 1.80× | **2.05** | **66/23/0** | **survives** |

**CONFIRMED — the source confound was the entire effect for `belonging`.** Its
headline 5.9× at n=33 becomes OR 0.98 at n=3,750; pooled rates 4.0% vs 3.9%.
`uplifting` likewise. Caveat 2 of the original issue was correct and dissolved
its own headline.

**CONFIRMED — `investment_risk` is a genuine within-publisher effect, and it is
not The Hill.** 66 of 89 sources same direction, zero ties, and it reproduces on
each detector arm independently — arms with different false-positive profiles:

| arm | strata | opinion n | opinion rate | other rate | MH OR | hi/lo |
|---|---:|---:|---:|---:|---:|:--:|
| url path | 64 | 2,329 | 40.2% | 21.5% | **2.23** | 49/15 |
| tag | 52 | 1,503 | 39.1% | 20.5% | **2.15** | 39/13 |
| title prefix | 6 | 79 | 31.6% | 17.1% | 1.83 | 4/2 |

`us_news_the_hill` is one stratum of 89 (119 opinion rows); the effect holds at
Globe & Mail, Japan Times, Børsen, Süddeutsche, Al Jazeera, FD, El País alike.
Stage composition is near-identical between arms here (8.1% vs 7.6% `stage1_low`),
so it is not a probe artefact.

**REFUTED — the lens-fidelity motivation.** The argument for caring was that
evidence-of-implementation lenses should be the polluted ones. Measured at its
**correct** op-point and at n=3,750, `solutions` runs the other way: **MH OR
0.50, 66 of 92 sources negative** — an opinion piece is about *half* as likely to
clear `solutions`' bar as a non-opinion piece from the same publisher. The lens
already discriminates against advocacy. `nature_recovery` cannot be measured.
**Refuted where measurable, not merely unsupported.**

---

## Open

- ⚠️ **A topic confound survives inside each source and MH cannot remove it.**
  Eyeballing 25 flagged `investment_risk` rows above op-point, they are
  overwhelmingly geopolitical/policy op-eds — *"How to end the 'Hormuz war'"*,
  *"Stablecoin is the wrong weapon in U.S.-China fight"*, *"Hamas disarmament
  cannot wait … - editorial"*. **Hormuz is investment risk.** Opinion sections
  skew geopolitical and this lens scores geopolitics highly. **Nothing here
  establishes that the surfaced opinion is WRONG**, which is the question a stamp
  would have to answer. Needs a topic control or oracle adjudication.
- The remaining question for `investment_risk` is a **lens-definition** question,
  not a detector question, and belongs with the owner (cf. #107 for `uplifting`,
  where a scorer was faithfully serving a definition its consumer had not
  published).
- `cultural_discovery`'s 1.27 with a 29/40/23 split is too weak to act on and too
  non-zero to close. Note its stage composition **does** differ sharply between
  arms (29% vs 55% `stage1_low`), unlike `investment_risk`.
- The detector remains a **floor** — URL/tag/title/source only. Misses land in
  the "other" column and bias every contrast toward null, so the five nulls are
  weak-but-real and the 2.05 is a lower bound.

## Reproducing

Population is on sadalsuud; nothing is committed here (full article text — #97).

<!-- verify: P=memory/opinion-genre-hypotheses.md; M=""; for v in 2.25 233,338 2.05; do grep -qF "$v" "$P" || M="$M $v"; done; if [ -z "$M" ]; then echo "PASS op-point 2.25 + n=233,338 + MH OR 2.05 all present"; else echo "FAIL dropped from the record:$M"; exit 1; fi -->

```bash
# op-points, from the RUNTIME source — never from config.yaml, never from #121's body
ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && \
  for f in uplifting/v7 investment_risk/v6 cultural_discovery/v5 \
           belonging/v1 nature_recovery/v4 solutions/v6; do \
    echo "=== $f"; grep -A6 "TIER_THRESHOLDS = \[" filters/$f/base_scorer.py; done'

# the population, and its span — print the span, a window is part of a source
ssh sadalsuud 'ls /home/jeroen/local_dev/NexusMind/data/filtered/belonging/ | head -1; \
               ls /home/jeroen/local_dev/NexusMind/data/filtered/belonging/ | tail -1'
```

Related: `memory/filter-status.md` (op-points and accuracy),
`memory/nexusmind-data-sources.md` (what the population excludes),
`memory/working-rules.md` (the instrument rule that made `nature_recovery`'s null
readable as empty rather than as a result). Issue: llm-distillery#121.
