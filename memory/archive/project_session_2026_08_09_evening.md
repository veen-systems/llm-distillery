# Session 2026-08-09 (evening) — llm-distillery

**Sent to fix a calibration defect. There wasn't one.** 15 commits, all pushed.
**Nothing deployed, and nothing needs to be.**

## The headline

The owner opened with *"the mutual calibration of the lenses seems not to
work"* and a 173× surfacing spread. **Mostly genuine base-rate difference.**

160 production articles, stratified by the student's own score band, graded by
DeepSeek (`nature_recovery`'s own oracle, $0.21, 160/160 parsed):

| band (student) | population/6cyc | n | oracle ≥3.75 |
|---|---|---|---|
| A ≥3.75 (surfacing) | 30 | 30 | **26/30 = 87%** |
| B 2.00–3.75 | 50 | 40 | 12/40 |
| C 1.00–2.00 | 353 | 40 | 1/40 |
| D+E <1.00 (**96.7% of corpus**) | 12,709 | 50 | **0/50**, oracle max 1.05 |

Precision at the gate **0.87** (recorded 0.848); ~8 oracle-positives/cycle vs ~5
surfaced → recall ~0.6 (recorded 0.65). **"3 of 2,152" is not a defect — there
are only about 8 of 2,190.** The outlier in that table is `investment_risk` at
24.2%, not `nature_recovery` at 0.14%.

## Two of my own headlines retracted, same day

1. **Isotonic crush.** Real and measured — `recovery_evidence` jumps **+2.47
   over a 0.06 student step**, >52% of the student's range maps to calibrated
   ≤1.33 against a 3.75 gate. Worth **~3 articles/cycle**. Not the lever.
2. **Six-filter MAE ranking + "calibration is a net negative".** Invalid: six
   populations, one number. Owner: *"beware of what you call error! we are
   doing needle-in-haystack filtering."* → **ADR-023**.

Both are Dead Ends in `memory/calibration-history.md`.

## ADR-023 — a false positive costs a reader, a false negative costs nothing visible

Owner: *"letting junk through is way worse than not catching positives. Junk
kills readers; positives they don't know about don't hurt them"*, then *"that
always was the target, but apparently not clear enough. ADR? put it into your
genes."* Written, and promoted into **CLAUDE.md Hard Constraints**.

Optimise specificity; recall is a floor; **never rank filters on MAE**. Only
recall and specificity are comparable across splits — precision is base-rate
dependent too. Active-learning batches sample **above** the op-point. Explicitly
**exempts the Stage-1 e5 probe**, which is a recall-safe screen by design.

| filter | positive rate | recall | specificity | FPR on true negatives |
|---|---|---|---|---|
| uplifting v7 | 32.7% | 0.7361 | 0.9189 | **8.1%** |
| solutions v6 | 16.2% | 0.6707 | 0.9723 | 2.8% |
| nature_recovery v4 | 15.3% | 0.6500 | 0.9789 | 2.1% |

Careful: composition explains only **+0.0919 of the 0.3435** MAE gap (~27%), so
the residual may be real — it is simply not the objective.

## One irreversible risk closed

**`uplifting v7`'s adapter existed on a single disk** — NO_HUB (its
`training_metadata.json` was never produced, so the Hub uploader can't build a
card) and gitignored by `filters/**/model/`. Now on four machines, all
`eb0bf8416206b841`: gpu-server, workstation, b650, **sadaltager**.
*(A storagebox copy was made and then removed at the owner's request — it was
their backup infrastructure and I should have asked first.)*

**Three production probe pickles existed only on gpu-server** (cd v5, ir v6,
uplifting v7) — `.nexusmind-owns` is empty and the deploy script overwrites, so
the next sync would have deleted them. Recovered, md5-verified, committed.
Cause: the `.gitignore` negation `!filters/*/v*/probe/*.pkl` carried a trailing
same-line comment and was inert until **2026-07-10** (`f910032`). Everything
deployed before that date is missing; everything after is present.

## Audit: all six scorers

**Stage 1 is uncalibrated on five of six** — only `solutions v6` runs its
probe's own threshold. The other four carry no threshold at all, just `val_mae`.
Refitted all four on b650: **every deployed threshold sits at val FN 0.000**, so
this is efficiency headroom, not a recall bug — and the calibrated thresholds
trade recall for speed, the wrong direction under ADR-023. Not deployed.

Corpus decided by the probe alone: ir 8.8% · nr 11.5% · upl 12.4% · bel 14.9% ·
**cd 53.7%** · **solutions 67.2%**.

**Clean:** 35 of 36 shared files byte-identical repo ↔ gpu-server; all six
normalization anchors correct; `surfacing AND stage1_low` = **0 across all six
lenses / 13,142 articles**.

## First active-learning batch + reader flags

Sampled **above** the op-point per ADR-023 (170 rows, gemini-flash, 144 graded):
**~50 of ~199 articles/cycle reaching readers are off-lens (~25%)**, precision
1.000 / 0.705 / **0.571** by band. 21 of 34 candidates are `solutions_story`.

Pulled all 89 ovr.news reader flags. 15 are off-lens complaints; 12 matched a
production row; **only 5 were new** — 6 already filed, 1 already rejected.
Owner adjudicated: **3 accepted** (belonging 1→2, uplifting 2→4), 1 rejected,
1 open.

**The finding that matters most:** the oracle graded uplifting's ≥5.5 band
**29/29 perfect** while readers flagged articles at 6.85 / 6.49 / 6.09 in it. An
oracle that defines the editorial line the student was trained on is blind to a
blind spot it shares. **5 hand-checked reader flags yielded 3 adverse rows; 34
oracle candidates yielded none.**

## Also

- **`uplifting v7` has its first accuracy record ever** —
  `filters/uplifting/v7/ground_truth_gate.json`.
- **#81 repointed**: sklearn is now 1.8.0 on both boxes. The live mismatch is
  **ST 5.6.0 (sadalsuud) vs 5.2.2 (gpu-server)** on the mpnet + sklearn-MLP
  detectors, where the |0.16| skew was measured. **Obituary enforces at 0.85
  with a 0.0012 margin. Unmeasured.**
- **|0.16| cross-box skew SCOPED**: does not apply to the e5 + torch MLP path
  (max |Δ| **4.2e-6**, zero flips). b650 cleared for probe training.
- `requirements.txt`: two provable defects fixed — `google-genai` undeclared,
  and `transformers<5.0.0` excluded the 5.0.0 production serves.
- Issues **#81 #90 #91 #96** updated with measurements; **#102** filed.
- Framework **v1.18.0, no drift**. One unpushed badge-fix commit sits in the
  owner's `agent-ready-projects` checkout.

## Owner-facing note

Mid-session: *"i have no idea, what now?"* — the answers had drifted into
jargon. Recovery was a plain-language summary and a small set of concrete
options. `CLAUDE.md` § How To Write Answers Here exists for exactly this, and
was not being followed.

## Next

1. **#102** — `uplifting v7` specificity; ADR-021 gate on a 4.5 op-point.
2. **Adjudicate the 21 `solutions_story` candidates** — ADR-015 says lenses
   overlap by design, so this decides most of the batch. Owner call.
3. One reader flag open: the Global Voices Assyrian-erasure essay, belonging 7.67.
4. Three filters still have no ground-truth gate: belonging v1, cd v5, ir v6.
