# Session 2026-09-06 (second) — phase 9: the doc set, and a retrain instead of an exception

**$0 spend, no oracle calls.** One ~95-minute GPU run on b650. Commits `64b469d`, `c0127d4`,
`0d7115a`, `67c6f59` (+ this one). **EXP-027.** Issues **#148** and **#149** filed; **#144**
and **#104** commented.

## What the owner ruled

Three decisions, put as questions before any production action:

1. **The dangling checkpoint: RETRAIN, not an exception.** Verbatim: *"no exception, i want
   this system to be harmonized"*, and then *"it is very sloppy that we need to redo this"* —
   which is fair, and the root cause is named below.
2. **Transport: rsync AND publish** `jeergrvgreg/human-thriving-filter-v8` private, as an
   off-machine backup.
3. **Phase E: proceed as normal**, accepting NM#319 (~40% of surfaced articles fall below the
   4.0 enrichment gate once a CDF exists).

## ⛔ Why the retrain was needed, and what it actually cost

`human_thriving v8`'s adapter was built by the tree that became `1878e7b` via
`git commit --amend`, orphaning the producing sha (`0697f5a`). Nothing caught it because
`training_metadata.json` recorded **no commit at all**.

⭐ **And it was worse than "unrecorded": `b650-gpu:~/llm-distillery` was a partial rsync, not a
checkout, and its `training/train.py` was the PRE-FIX version missing the 176 lines of
checkpoint-selection machinery `main` says trained the artifact.** The box did not hold the code
the record named. 12 tracked files had drifted; `uplifting v7`'s `config.yaml` /
`normalization.json` / `base_scorer.py` differed from what sadalsuud serves, and `main` was
byte-identical to sadalsuud — so making b650 a real checkout moved it **toward** production.
Pre-checkout copies and per-file diffs: `b650:~/b650-pre-checkout-2026-09-06/`.

**The retrained model is NOT the same model.** `recall_medium` **saturated** in EXP-015 (0.5806
across epochs 4/5/6, tie-break kept the earliest) and did **not** saturate here, so selection
chose **epoch 5** outright — a bigger change than run-to-run noise.

| | epoch 5 (ships) | epoch 4 (superseded) |
|---|---|---|
| recall / precision / specificity | 0.314 / 0.550 / 0.9856 | 0.343 / 0.706 / 0.9920 |
| surfaced / FP | 20 / 9 | 17 / 5 |

⛔ **All four #95 bands overlap → NOT DISTINGUISHABLE.** Every point estimate moves adversely;
that is a direction, not an effect.

⭐ **THE KEEPER FOR THE OWNER'S QUESTION.** Asked whether precision matters more than
specificity, the answer turned out to need a third quantity. Classifying every false positive by
the oracle's own `scope_verdict` — a field on all 6,586 labelled rows:

| | epoch 5 | epoch 4 |
|---|---|---|
| `in_scope` (oracle calls it on-lens, scored just under 4.5) | **6** | 3 |
| genuinely off-lens | 3 of 20 → **0.850** | 2 of 17 → 0.882 |
| **`harm_is_subject`** (the category error) | **1** | **1** |

**The plain FP count moved 5× more than the reader-facing quantity did, and the two models have
identical category-error counts.** Specificity 0.9856 and "9 of 20 surfaced are wrong" are the
same model; the #95 band on specificity is **5 to 10 false positives** (⚠️ **corrected 2026-09-07**: this
line published **3 to 8**, which is the SUPERSEDED epoch-4 arm's band — fp 5, −2/+3. Epoch 5
is fp 9, −4/+1), a 2× range inside one
"not distinguishable" verdict. Registered as `H-V8-25` / #149. ⚠️ n=17 and 20; "1 versus 1"
compares two single articles.

## ⛔⛔ VERIFICATION IS NOT REVIEW — 7th consecutive session, and the worst margin yet

**746 tests, five guards, all green — a six-lens `/review-changes` returned NINE BLOCKERS, all
in code and docs written that same day.** Three of them were the new guard failing at exactly
the thing it was built to catch:

1. **The refusal could not fire.** `git branch --contains` emits `* (HEAD detached from …)`,
   truthy after `lstrip("* ")`, so "commit on no branch" never triggered. **My own test did
   `git checkout main` first** — the state that hides it.
2. **`git -C` walks up**, so a copy nested in another repo stamped the enclosing HEAD.
   **My test used `tmp_path`, outside any repo** — the population guaranteed the pass.
3. **The blast-radius mutation survived**: deleting `**git_provenance` from the metadata dict
   passed all 746 tests. The producing half was untested.

Also: nothing *invoked* the checker (no hook, no CI, no `verify:` row — the delete-it mutation
survived); `UNSTAMPED_BASELINE` could **grow** to silence a real failure with every test
passing; and the exemption I added could not distinguish a saturated band from
`--noise-floor 0`. All fixed, with tests that kill each mutation. 762 tests now.

⭐ **The generalisable half: two of the three were found by mutating the WORLD the guard runs in
— a detached HEAD, a nested directory — not the guard's own lines.** Mutating what you wrote
tests your intent. Mutating the environment tests the premise.

## ⚠️ Stale numbers, and the surfaces a package edit does not reach

Doc-accuracy found the superseded **0.343 / 0.992** still published as v8's gate result on four
fleet surfaces the session never opened — `CLAUDE.md:70` (**always-loaded**),
`memory/filter-status.md`, `docs/FILTER_PLAYBOOK.md`, `docs/adr/023`. Plus "right about 70%"
(epoch 4's precision) left in `STATUS.md` three lines below text the same commit rewrote, and in
`DEEP_ROOTS.md` — a file written that day. ⭐ **Updating a filter package does not update the
fleet-level documents that quote it, and the commit message claimed it had.**

Claim-verification separately corrected a published number: **test MAE "0.5947 → 0.6066 (−2.0%)"
pairs an UNCLAMPED before with a clamped after.** `fit_calibration` keeps raw logits;
`dump_student_scores` clamps to [0, 10], which is what production does. On production's arm it
is **0.5855 → 0.6066 = −3.6%**. Direction and decision unchanged; the magnitude understated.

## ⚙️ Incidental, all fixed

- **`README_MODEL.md` was gitignored repo-wide** — five on disk, **none tracked**, for any
  filter, while the doc standard required it and parity checks counted it present. Un-ignored;
  six now committed (belonging v1's gap, open since 2026-08-21, closed in passing). The
  generator also read `training_history[-1]` (the *last* epoch, not the shipped one), could not
  resolve v8's oracle, and asserted a `quality_score >= 0.7` threshold that appears nowhere.
- **`filter_completeness.py`** — the parity tool's own filter list was hand-written and stale,
  naming `sustainability_technology v3`, **deleted 2026-08-03**. Now discovered from the
  filesystem: **4 of 29** packages meet the 6-file doc core, **14 of 29** carry neither
  `inference_hub.py` nor `NO_HUB`. ⛔ Its docstring claimed it was "the tool the package-parity
  gate invokes" — **nothing invokes it**; mention-as-use, inside the file about stale
  hand-maintained state.
- **Three obituary-validation artifacts were not valid UTF-8** — `open(path,"w")` with no
  `encoding=`, the NM#338 class. Two re-encoded with content proven identical; one is truncated
  mid-write and keeps its bytes under `.truncated`. ⚠️ **No script in the tree writes two of the
  three**, so hardening the writers cannot have fixed them — recorded rather than papered over.
- **`check_claim_shapes` DOC_ROOTS widened to `filters/`**, which its own comment predicted.
  Orderings 5 → 10 sites over 110 → 273 files; intervals 115 → 172 over 140 → 494. Found six
  unbanded orderings, two of them cross-filter MAE rankings ADR-023 forbids.

## ▶ NEXT: the weights have not moved

Everything before the deploy is done. Remaining, in order: the 82 MB adapter to **gpu-server**
(the serving box — `deploy_filters.sh` excludes `model/`, so weights go out-of-band and a
weightless highest version stops the scorer starting, #67); the Hub publish; then land
`inference_hub.py` and **delete `NO_HUB` in the same commit** (the verifier refuses the pair);
then `deploy_to_nexusmind.sh --dry-run`, a `chore/` branch and PR, `remote_deploy.sh`; then
Phase E. Full handoff: `docs/TODO.md` § *NEXT SESSION STARTS HERE*.
