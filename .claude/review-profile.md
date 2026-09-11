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
that: 78 "failures" that were the wrong interpreter).

**Measured 2026-09-11: `822 passed, 25 skipped` in 125s.** Re-measure rather than trust
this line; a stale baseline is how a real regression reads as pre-existing.

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

## Project lenses — ⛔ NOT READ BY THE SKILL

⛔ **The v1.40.0 skill's Step 2 lens list is CLOSED. Nothing below fires automatically.**
These three lenses lived in the pre-v1.40.0 local fork and have no slot in the profile
contract. Upstream **`ducroq/agent-ready-projects#166`** (filed 2026-09-11) is exactly this
gap. They are kept here so the split does not silently delete them — **not** because
anything runs them.

**Until #166 lands, invoke these by hand** when the tier calls for them: paste the prompt
into a review subagent alongside the skill's own lenses. A lens you believe is running and
is not is this repo's signature defect; that is why this heading says so twice.

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
