# Review Profile — llm-distillery

<!-- Read by the user-global `review-changes` skill at Step 1 (agent-ready-projects
     v1.40.0). This file is this repo's half of that skill; the skill body is generic,
     ships identically to every project, and is re-copied on each framework release.
     Everything here is ours and never travels. -->

⛔ **If this file is lost, `review-changes` STOPS at Step 1.** The template is
`templates/review-profile.md` in the framework clone at `~/repos/agent-ready-projects`
(`git show v1.40.0:templates/review-profile.md`) — this repo ships no `templates/`.

Adopted 2026-09-11 from `agent-ready-projects` v1.40.0, which split `review-changes` into
a user-global skill plus a per-repo profile. The content below was **extracted from this
repo's previous 546-line project-local fork** (adapted from v1.12.0, re-mapped rather than
copied) rather than written fresh — the fork is in git history at `93e2bcf`.

## Risk tiers

| Tier | File patterns | Depth |
|------|-------------|-------|
| **HIGH** | `filters/common/*.py` · `filters/*/v*/config.yaml` · `filters/*/v*/{calibration,normalization,ground_truth_gate}.json` · `filters/*/v*/prefilter.py` · `filters/*/v*/base_scorer.py` · `filters/*/v*/inference*.py` · `filters/*/v*/model/**` · `ground_truth/batch_scorer.py` · `scripts/{gate,normalization,calibration,deployment}/*` · `scripts/deploy_to_nexusmind.sh` · `scripts/**/*.sh` · `tests/**/*.sh` · `docs/evidence/**/*.py` · `tests/unit/test_normalization_{invariant,op_point}.py` · `.githooks/*` | Full battery: guarantee-preservation + adversarial + doc-accuracy, plus shell-correctness when a shell file changed (**3–4 lenses — the skill ships four, not the fork's six**) |
| **MEDIUM** | `CLAUDE.md` · `ground_truth/*` · `training/*` · `scripts/**` (other) · `tests/**` · `docs/adr/**` · `docs/FILTER_PLAYBOOK.md` · `docs/NORMALIZATION_METHOD.md` · `docs/RUNBOOK.md` · `docs/ARCHITECTURE.md` · `docs/decisions/**` · `docs/evidence/**` (non-`.py`) · `.claude/**` · **anything matching no tier** | Adversarial + doc-accuracy |
| **LOW** | `memory/*` · `docs/TODO.md` · `docs/ROADMAP.md` · session files | Adversarial |

**Unmatched files are MEDIUM, not LOW** — silence must never read as safe. Name every
unmatched file in the report's Unclassified section **even when a HIGH file in the same diff
makes the tier moot**. Pick the **highest** tier that applies.

⚠️ **If an unmatched file is EXECUTABLE, or is copied into NexusMind, escalate it to HIGH**
rather than leaving it at MEDIUM — MEDIUM omits guarantee-preservation and sync-safety,
which are the two lenses shipped and propagated content most needs.

⚠️ **`.claude/**` tiers MEDIUM, but the skill's own carve-outs still apply and this
profile CANNOT remove them** — a non-frontmatter edit to a reference install under
`.claude/skills/**`, a frontmatter edit to one, and any diff that deletes a guard are each
**always full depth**, whatever this row says. Tier picks the lenses; the carve-out sets the
depth. What MEDIUM buys is that HIGH's guarantee-preservation and sync-safety lenses — about
shipped filter math and the NexusMind copy — are not bolted onto a skill edit they have
nothing to say about.

## Guarantee surfaces

⚠️ Every path here must sit in the **HIGH** row above. The guarantee lens is HIGH-gated, so
a guarantee on a lower-tiered path can never fire — and the report renders that as a clean
pass. Check it in this direction: read each entry here, then find its tier above.

- `filters/common/model_loading.py`: `load_base_model_for_seq_cls()` stays the only entry
  point. `AutoModelForSequenceClassification` must NEVER be used directly — Gemma-3-1B's
  `gemma3_text` config is not in the Auto mapping.
- `scripts/deployment/*` — PEFT key format: OLD only (`.lora_A.weight` / `score.weight`,
  NOT `.lora_A.default.weight`); `resave_adapter.py` must never run before Hub upload, it
  breaks `PeftModel.from_pretrained()`. ⛔ **Review CANNOT enforce this on the adapter files
  themselves and must not pretend to.** `.gitignore:65` is `filters/**/model/` and the only
  re-include is `!filters/**/training_*.json`, which does not cover `adapter_config.json`.
  **Every current production filter has 0 tracked files under `model/`** — measured
  2026-09-11 over human_thriving v8, uplifting v7, cultural_discovery v5, belonging v1,
  nature_recovery v4, solutions v6. The 32 tracked `*/model/` paths all belong to DEAD
  filters (`investment_risk/v2_*`, `investment_risk/v4`, `uplifting/v4*`,
  `commerce_prefilter/v1`) and predate that rule. The enforceable surface is therefore the
  **upload/deploy code**, which a diff can contain; the adapters are enforced by the deploy
  gate and the Hub upload path, not by review. `filters/*/v*/model/**` stays in the HIGH row
  for those legacy files only.
- `filters/common/filter_base_scorer.py`: `_apply_short_content_cap` is the ONE place the
  #93 short-content rule is decided, reading the stamp on `result`, not the article. A
  second inline copy is the ADR-022 second-drop-point defect.
- `filters/*/v*/prefilter.py`: no `apply_filter()` on a SCORING path may check content
  length (#93). The floor is labelling-time only, in
  `ground_truth.batch_scorer.make_oracle_prefilter`. Adding `check_content_length` to a
  prefilter re-creates what #93 removed. (`validate_article` rejecting EMPTY content is
  separate and legitimate.)
- `scripts/gate/*`, `filters/*/v*/config.yaml`: ADR-022 "stamp always, decide once" — gate
  modules stamp score+flag+model version unconditionally; exactly ONE config-gated drop
  point per concern; every enforcement decision is a config flip, never a code revert.
- `ground_truth/batch_scorer.py`: ADR-001/016 — the oracle outputs dimensional scores
  (0-10) only, never tiers or stages. Changing a threshold must never require re-labelling.
- `filters/*/v*/normalization.json`, `scripts/normalization/*`,
  `tests/unit/test_normalization_invariant.py`: ADR-014 / `docs/NORMALIZATION_METHOD.md` —
  fit at `raw >= the filter's tier threshold`. Both NM#161 and NM#205 were `raw_min`
  drifting off that threshold.
- `filters/*/v*/calibration.json`: refit after every training run, committed with the
  filter package.
- `filters/*/v*/prefilter.py`: ADR-004 — commerce is the only universal prefilter.

## Test baseline

```bash
.venv/bin/python -m pytest tests/ -q
```

⚠️ **Name the interpreter.** Bare `python3` is `/usr/bin/python3` here and lacks the deps —
it produces a phantom failure baseline that gets believed (this project has done exactly
that: 78 "failures" that were the wrong interpreter). ⛔ **SECOND OCCURRENCE 2026-09-17, by an
agent that had not opened this file**: `python3 -m pytest` reported **13 failed, 6 errors** on the
#158 change and they were reported to the owner as "environmental, pre-existing" before
`.venv/bin/python` returned **0 failures**. ⭐ The diagnosis was right and still useless — a
phantom baseline is not made harmless by being explained, because the explanation is what makes it
believed. **Run `.venv/bin/python -m pytest` and say which interpreter produced the number.**

**Measured 2026-09-22: `932 passed, 25 skipped` in 123s** — `.venv/bin/python3 -m pytest tests/ -q`,
**on a clean tree, alone on the machine**. ⚠️ Both qualifiers are load-bearing and were learned
the hard way in the same session: an earlier line said `926 passed` and was true when taken, then
went stale twice — once because more tests were added, once because a `timeout`-killed run left
`experiments/registry.jsonl` corrupted (llm-distillery#162) and three reviewers each measured a
different failing count on the same code. **If you cannot produce a green line alone on a quiet
tree, do not write the number.**
The +10 over 2026-09-17's 922 decomposes as: **5** new llm-distillery#154 gap-guard tests in
`tests/unit/test_normalization_invariant.py` (the regression case plus all three directions the
rule moved in — stricter below op-point 4.0, identical at 4.0, looser above), **4** in the new
`tests/unit/test_fit_normalization_guard.py` (the deploy-path guard, run end-to-end through the
real CLI), and **1** new parametrization — `human_thriving-v8` joined
`test_normalization_fitted_at_the_tier_threshold` the moment Phase E wrote its
`normalization.json`, which is a test count moving because DATA changed, not code.
*Prior: 2026-09-17 (final): `922 passed, 25 skipped` in 118s* (was `912`, then `894 passed,
25 skipped` earlier the same day, and `848` before that; the +46 were the #134 step-2 docs
tier — `tests/unit/test_refcheck_docs_tier.py` 37 and `tests/unit/test_refcheck_tier_reparse.py`
6 — plus 3 seeding the `suite-baseline` claim check that guards THIS line, and the latest +18
were `tests/unit/test_detector_metric_bands.py` (llm-distillery#158) and the latest +10 are
`tests/unit/test_gate_device_stamp.py`, llm-distillery#104). Re-measure rather than trust this line — a stale baseline is how a
real regression reads as pre-existing. ⚠️ **This line is the ONLY live copy of the number
and is meant to be**; the 2026-09-11 change that added tests left it stale, and the
2026-09-17 draft that fixed it wrote 834 and was falsified by its own next commit. ⛔ **Occurrence three was caught by review, not by anyone re-reading this line**: the #134 step-2 record wrote its own copy of the count while quoting this rule. The
history file deliberately records the COMMAND and no number.

## Always-full-depth carve-outs (project additions)

The skill's own carve-outs (`.gitignore`, renames, mode changes, binaries, submodules)
always apply and cannot be removed here. Project additions:

- `CLAUDE.md`: always-loaded, and a wrong line there is wrong in every future session. A
  one-line edit is not a small change. Its own stamp row asserted a stale upstream version
  for eleven releases, inside the paragraph written to correct the previous stale version
  claim — no review caught it; `/update-drift` did.
- `.githooks/*`: a broken hook fails open and silently stops gating commits.
- `filters/common/*.py`: HIGH regardless of how small the diff looks — it is shared math
  that `deploy_to_nexusmind.sh` OVERWRITES into NexusMind, where `.nexusmind-owns` is empty.
- `filters/*/v*/config.yaml` op-point keys: an operating point lives in FOUR places and
  `config.yaml` is **not** the runtime one. A config-only change is a no-op in production.
- `.claude/review-profile.md` (this file): a tier silently narrowed here disables a lens
  everywhere, and the report renders that as a clean pass.

⚠️ **A `.claude/**` diff carries one question the lenses do not ask: is this file still an
adaptation, or has it drifted from what it was adopted from?** That question belongs to
`/update-drift`; a reviewer's job is to notice it is owed, not to answer it in the review.

## Project lenses

**Read by the skill — Step 1 (`SKILL.md:83`) and Step 2 (`SKILL.md:300`), which name this
section by the heading `Project lenses`. Keep the heading undecorated.** Upstream
**`ducroq/agent-ready-projects#166`** (filed 2026-09-11) landed in **v1.43.0** — it adds three
optional profile sections, of which this repo uses one.

⚠️ **Undecorated for a reason that is NOT a string match.** Nothing greps this file: the
skill instructs an *agent* to read it, so the old heading (`## Project lenses — ⛔ NOT READ BY
THE SKILL`) would still have been found. What suppressed these lenses was the decoration's
**instruction** — *"Nothing below fires automatically … invoke these by hand"* — which a
reader obeys. Do not restate this as a matcher; there is no matcher.

⚠️ **A dated claim about a file OUTSIDE this repo, which no commit here can hold still.**
The annotation this paragraph replaced was **true when written on 2026-09-11** and false six
days later, upstream having shipped **six** releases (v1.41.0…v1.45.1) in between. Do not
hardcode a tag here — the probe derives it from the stamp:

```bash
bash scripts/verification/check_framework_stamp.sh    # 0 verified · 1 drift · 2 undecided
```

These three lenses **add** to the shipped set (`guarantee-preservation`, `adversarial`,
`doc-accuracy`, `shell-correctness`); a project lens never replaces a shipped one, and no
shipped lens asks what these ask. ⛔ **Naming the caller is not sufficient proof here either
— the outcome proof is a `/review-changes` report that NAMES these three lenses.** If a
report does not name them, they did not run, whatever this heading says.

### Lens: reachability (HIGH and MEDIUM — this repo's signature defect)

```
This repo's recurring failure is a mechanism that is present, configured, and
CANNOT FIRE. Four instances: per-filter prefilters never ran in production for
six months (NM#284); solutions v6's concreteness_gatekeeper binds 0 times in
191,616 articles (LD#94); a violence gate wired so it could never fire (NM#281);
a shadow loader arming a dead branch.

For every gate, cap, threshold, flag or config key touched:
1. Trace the CALL PATH. Is it reached in the production scoring path, the
   oracle/labelling path, both, or neither? Name the caller.
2. Does its INPUT exist at that point in the flow? (The GPU scorer reconstructs
   an Article of {title, content} only — rules reading url/source/source_type/
   description are inert in-path.)
3. Could the condition ever be true on real data? If it declares a rate or
   threshold, what does production actually show?
4. If it is a config key: does any runtime code read it, or does it only LOOK
   like an enforcement point?

Do NOT infer runtime behaviour from the presence of a config key. Do NOT check
prefilter state from data/filtered/*/filtered_*.jsonl — that file is 100%
passers by construction AND drops source-type-excluded rows.

Report: REACHABLE (with the call path) or UNREACHABLE/INERT (with why).
```

### Lens: claim-verification (any tier, when the diff asserts measured numbers)

```
The diff asserts measured numbers. For each one: what produced it, and can the
command be re-run? A number with no command behind it is a claim, not a
measurement. Check that the population and the window are named — a count
without its denominator, or a rate without its span, is not a result. Flag any
figure restated in a second place, since two hand-maintained copies of a number
disagree the moment one is updated.

Report: VERIFIED (with the command) or UNVERIFIED (with what is missing).
```

### Lens: sync-safety (HIGH only, when filters/common/ or a deployed filter changed)

```
This change may propagate to NexusMind via deploy_to_nexusmind.sh, which
OVERWRITES and whose .nexusmind-owns manifest is EMPTY — so any drift on the
NexusMind side is deleted silently. That has nearly cost three production source
blocks, and investment_risk v6 carried arxiv/mastodon_/bluesky blocks in
NexusMind that never existed upstream.

1. Does the NexusMind copy of each changed file differ today? Diff before
   concluding.
2. Would a blind LD -> NM copy DELETE anything NexusMind added? If so, port it
   back to llm-distillery first rather than overwriting.
3. Is the change pure shared math (safe to sync) or does it encode a
   production-runtime concern that belongs in NexusMind's production_scorer.py?

Report: SYNC SAFE or SYNC WOULD DROP <files/blocks>.
```
