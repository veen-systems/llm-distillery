---
name: obituary-v4-hypotheses
description: Hypotheses confirmed and learned from the obituary detector v4 corrective retrain
metadata:
  type: project
---

# Obituary Detector v4 — Hypotheses from Corrective Retrain

**Date:** 2026-07-28 (v5 production-FN addenda 2026-07-31, 2026-08-02)

## Confirmed

1. **Small-N hard negatives shift MLP boundaries effectively.** 12 hard negatives against 11,295 rows (0.1%) was enough to fix all 12 known FPs. The frozen embedder means the MLP only needs to learn a better separating hyperplane, not a new representation — so small targeted corrections work.

2. **Panel ground truth beats oracle labels for FP measurement.** The heldout showed 7 "FPs" at 0.95 against oracle labels, but the 4-model panel found only 4 actual FPs among the top scorers. Measuring FP fixes against oracle labels alone overstates the regression and understates the improvement.

3. ~~**Precision/recall tradeoff is real but acceptable for prefilter classifiers.**~~ **FALSIFIED 2026-07-30.** The original claim ("FNs just waste 5ms of lens scoring") confused a *blocking* prefilter with a *routing* one: once enforcement flips, an FN is an obituary on the site — the exact failure the owner keeps flagging (Farouq Hilal tribute, 2026-07-29: v3 0.977, v4 0.937 → v4@0.95 would miss it). Resolution: op-point moved to 0.90, where v4's heldout FP set is identical to 0.95 (zero precision cost) and recall recovers to 0.683. For blocking classifiers, sweep the op-point on both error directions against the product metric; never accept a recall drop on "FNs are cheap" grounds. See LD#83.

## Learned

4. **FP class matters for correction difficulty.** Legacy/tribute pieces (Greek/Spanish/Chinese historical profiles) dropped from >0.97 to <0.15 — easy to fix. Crime/accident reports dropped from >0.92 to <0.15 — also easy, once explicitly added. But one Spanish photographer profile (Belita Gracia) only dropped from 0.87 to 0.65 — the model still sees obituary-like structure in it. Some FP classes need more examples than others.

5. **OOF metrics overstate the tradeoff.** OOF recall dropped from 0.681 to 0.703 (actually improved), while heldout recall dropped from 0.744 to 0.608. The OOF numbers are on a clean train/test split of 11K rows; the heldout is 1,562 rows with different label noise characteristics. The heldout gap suggests the hard negatives shifted the boundary into a region where oracle labels were already noisy.

6. **Belita Gracia at 0.65 is the residual uncertainty.** The model isn't confident enough to call it an obituary (below 0.95) but isn't confident it's clean either (above 0.10). This is a legitimate ambiguous case — a profile of a deceased photographer published posthumously. The labeling rule says KEEP (legacy tribute), but the text has genuine obituary-like structure. Worth watching in production shadow.

## v5 production-FN addendum (2026-07-31, owner obit sighting on ovr.news)

7. **Open question 1 ANSWERED: yes, the recall loss appears in production, and it is structured, not noise.** Two live obituaries on ovr.news are true v5 FNs (rescored on gpu-server with the exact production text format `title + " " + content`; the rescore reproduces the production v4 stamp to 4 decimals — 0.4376 vs stamped 0.4375612):
   - **Community-mourning class — MONOTONE REGRESSION across versions.** "Namur mourns Yves Devos, captain of stilt walkers": v3 **0.682** → v4 **0.438** → v5 **0.122**. Each round of hard negatives (v4's legacy tributes, then v5's mix) pulled the community/festival-mourning style further from the obituary region. The correction mechanism from hypothesis 1 cuts both ways: small-N hard negatives shift the boundary effectively — including *over* genuine positives that share surface structure with the negatives. Under the owner's grief-vs-news rule this class is unambiguously BLOCK.
   - **Biography-rich obit class — STABLE BLIND SPOT, not a regression.** "Muere Teresa Alonso, la 'niña de Rusia'… dies at 101": v3 0.284 / v4 0.195 / v5 **0.277** — every version misses it. The article is dominated by decades of biography (Civil War evacuation, Leningrad siege), so it embeds as a history piece; the death-announcement frame is a small fraction of the text. Threshold changes cannot reach it (all versions <0.30); this class needs training examples (or title-weighted features — the title alone says "Muere…").
   Evidence for LD#85 when reactivated; both articles left on site per owner washout decision ("it is what it is").

## v5 production-FN addendum 2 (2026-08-02, two more owner flags in 24h)

8. **The LD#85 reactivation condition has now fired twice in one day, and these two FNs sit far higher than addendum 7's cases — though the FN population as a whole sits *lower*, see the third bullet.** Two more obituaries reached ovr.news on 2026-08-01 and the owner flagged both ("this is an obituary" / "Obituary"). Scores are the **production stamps** read straight out of the NexusMind filtered batches — no rescore, so no reproduction step is needed:

   | Article | Lang | v5 stamp | Lens published | Batch |
   | --- | --- | --- | --- | --- |
   | "'A person of faith and courage': Carol Lynn Pearson's legacy of compassion" (Deseret) | en | **0.6866** | belonging, raw 6.93 → norm 9.49, tier high | `belonging/filtered_20260801_085409.jsonl` |
   | "Simone Forti's Dance of Life" (Hyperallergic) | en | **0.5783** | cultural_discovery, raw 5.41 → norm 7.81, tier high | `cultural_discovery/filtered_20260801_004817.jsonl` |

   Threshold at the time: **0.85, `enforce: true`, v5** (NexusMind `config/app.yaml`).

   Four things follow, and the second overturns the option this addendum was originally written to recommend:

   - **These two are threshold-reachable, unlike the addendum-7 cases** — but see the sweep below before concluding anything from that. Yves Devos (0.122) and Teresa Alonso (0.277) are unreachable by any usable op-point; these two sit at 0.58–0.69.
   - **The op-point sweep was run the same day and it KILLED the threshold option.** `config/app.yaml`'s claim — "Lower thresholds add FPs with almost no recall" — was derived from the heldout, and the obvious objection was that two production FNs sit in exactly the band it writes off. Measured on production stamps over 7 days (113,998 articles, 2026-07-26 → 08-02): 692 articles sit in [0.55, 0.85), of which **23 actually reached the site**. Hand-labelled: **3 true obituaries, 6 death-centred memorial/repatriation pieces, 14 clean articles** — a botanist's forest regeneration, a stroke rescue where the patient lived, an art retrospective, an archaeological tombstone find. So moving the op-point to 0.55 buys 3 obituaries a week and costs 14 good articles. **The config note's conclusion stands; only its reasoning was incomplete.** The band is not enriched for obituaries — the score is close to uninformative between 0.55 and 0.85.
   - **Worse, the errors are not near the boundary at all.** Of 38 obituary-shaped articles live on ovr.news on 2026-08-02, 19 scored ≥0.85 (shadow-era carryovers, would block today) and 19 below. Of those 19, seven are under 0.32 — including **"Israeli IVF pioneer professor Shlomo Meshiah dies at 89" at 0.0001** and **"Anti-apartheid activist Shanthie Naidoo dies at 91" at 0.0000**. The classifier is not hesitant on these, it is confidently wrong on the canonical shape. No op-point reaches an article scored at zero.
   - **Title-weighted features would not have helped here** — the addendum-7 suggestion is class-specific. Neither source title announces a death: "…Pearson's *legacy of compassion*" and "Simone Forti's *Dance of Life*". Both are euphemistic-legacy headlines over a plain death announcement in the lede. (Notably ovr.news's own summarizer read it correctly from the body — its generated titles are "Carol Lynn Pearson dies after…" and "Simone Forti, pioneering performance artist, dies at 91" — so the signal is in the text the detector already sees.)

   The Hyperallergic case carries a second defect worth separating out: the source is a **newsletter roundup**, obituary in the lede followed by unrelated art-world items (a statue regilding, UNESCO listings, museum appointments). Same dilution mechanism as Teresa Alonso — death frame as a small fraction of the embedded text — but the diluent is *other articles*, not biography. If roundups are a recurring source shape, dilution is a structural FN cause and not a labeling gap.

   Both articles were also scored at the very top of their lens (each above its batch p99), so the lens scorers did not compensate. Not filed as lens adverse examples, per the #62 decision that the death/grief shape is owned by this detector.

9. **The consumer solved it downstream, and that relocates the problem rather than closing it.** ovr.news now drops articles whose *own generated summary* announces a death (`src/lib/data/editor/rules/obituary-summary.ts`, live 2026-08-02). It catches every case above — including Yves Devos and Teresa Alonso, which this detector cannot reach at any threshold — at a measured **0.79% decision rate over 3,658 build-eligible lens-rows** (29 matches), hand-checked. 27 of the 29 are on the `belonging` lens — 3.2% of it, against 0.1% everywhere else.

   Two measurement traps were hit and are worth carrying across repos: the first rate was quoted from a *stale local mirror* that did not contain one of the obituaries it claimed to catch, and from the wrong *population* (a 14-day display view rather than the 10-day per-lens build query). Both produced plausible numbers. Neither was the rate the rule applies.

   Why it works is the useful part for v6: **the summarizer reads the article and states plainly that someone died, while the embedding classifier reads source text where a euphemistic headline ("…legacy of compassion", "…Dance of Life") and paragraphs of biography dilute the death frame.** The signal was never missing; it was being destroyed by whole-document embedding. That is a representation problem, and it predicts the failure class precisely: FNs are exactly the articles where the death announcement is a small fraction of the text (biography-rich, newsletter roundups, community-mourning features).

   Consequences for LD#85 if it reactivates:
   - **Do not spend the budget on a threshold sweep or on more hard negatives at the document level.** Both are answered: the sweep is above, and addendum 7 shows hard negatives interfering with genuine positives.
   - **Try a lede/title-weighted representation** — embed the first sentence separately, or score `title + first_sentence` as its own feature alongside the document embedding. The downstream rule is evidence that this window carries the signal.
   - **Keep this detector regardless.** The downstream rule only sees articles that were summarized; blocking upstream still saves the scoring and summarization spend on ~957 obituaries a week.

## Open questions for v5+

- ~~Does the recall loss on the heldout appear in production, or was it concentrated in noisily-labeled regions?~~ **Answered 2026-07-31 — see addendum 7.**
- Is Belita Gracia a one-off or a whole class of Spanish-language legacy profiles that need dedicated hard negatives?
- Would the same fix work for a different architecture (e.g., fine-tuning the embedder instead of a frozen MLP)?
- ~~What is the real FP cost of an op-point at 0.55–0.70, measured on production stamps?~~ **Answered 2026-08-02 — 3 obituaries per 14 clean articles. Threshold tuning is closed; see addendum 8.**
- **NEW (addendum 8/9): does a lede- or title-weighted representation fix the dilution class?** The downstream ovr.news rule reads the first sentence of a generated summary and catches every known FN, including the two no threshold can reach. That is evidence the signal survives in a short window and is lost in the document embedding.
- **NEW (addendum 8): are newsletter/roundup sources a structural FN class?** Obituary in the lede plus unrelated items dilutes the death frame in the embedding the same way biography does.
- **NEW: does the hard-negative↔positive interference (addendum 7) mean v6 needs paired examples** — for every hard-negative class added, a matched hard-positive set from the same surface style (memorial-events-blocked vs festivals-kept now inverts under the grief-vs-news rule anyway)?
