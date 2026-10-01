---
name: project-session-2026-09-29-cloud-pilots
description: Session 2026-09-29 — Claude Code cloud pilots (#162, #136, #134 step 3 → PRs #166/#167/#168 merged), stopped by owner; gpu-server outage, sadaltager woken + checked, NM#395 migration handed to nexusmind-44
metadata:
  type: project
---

# Session 2026-09-29 — cloud pilots, then the gpu-server outage

**Ask:** "update cross-repo-prioritization with the cloud angle ($100 cloud budget)", then run pilots, then
"stop testing and focus on the migration", then close ("wrap up… prune, thin, mechanize, retire").
Cloud model cost **$6.89 measured** (pilot 3 not read); no oracle, no GPU training. Deploy: **N/A** — no
filter package changed; the `.githooks/commit-msg` change is live in every checkout with
`core.hooksPath=.githooks` the moment it merged.

| thread | state |
|---|---|
| #162 registry test writes the tracked file | ✅ PR #166 merged `1624c62` |
| #136 deploy guard can't read negation | ✅ PR #167 merged `4ec7850` — 3 review rounds; round 1 and 2 each found a fail-open bypass (`No regressions deployed v7`, `Errors during deploy: none` committed unverified) |
| #134 step 3 marking pass | 🔶 PR #168 merged `30e668d` (+ review fix `d489c7c`): live tier **277 → 227 in place**. Open: owner (a) `docs/TODO-archive.md` edit or leave counted; (c) ADR templates code-span vs links; ~82 decidable only on this machine; `phaseA_cohort200.jsonl` <!-- placeholder --> disposition (`docs/evidence/2026-08-29-v8-phase-a-k3/`) |
| cloud pilots | ⛔ STOPPED by owner. Standing rules in `cross-repo-prioritization.md` § *The cloud angle* |
| gpu-server outage | offline since ~2026-09-28 21:20; last scored cycle 09-28 16:08 (NM#395 comment 06:25; `tailscale status` 16:32 "last seen 19h ago") |
| sadaltager | woken 16:34:46 (WoL from situla, up at +85 s); GPU + torch OK, outbound OK, no Docker, no scorer stack — posted to NM#395. **Left ON at owner's request**; `nexusmind-44` builds the scorer image there (NM#395 step 1) and runs parity |
| parity reading rules | sent to `nexusmind-44` as a file (`scratchpad/nm395-parity-reading-rules.md` <!-- placeholder -->, session-temporary): flips split at 0.16 from the op-point; condition on `stage_used`; op-points confirmed for all six live filters |
| NM#395 parity (measured by nexusmind-44, read by our rules) | 0 flips beyond 0.16 of the op-point over 18,466 rows; 6/99 = 6.1% inside the band; 0 `stage_used` mismatches; same-order rerun bit-identical. **Shuffled control still running at close**; go/no-go is the owner's + nexusmind-44's |

**Lessons (promoted where they belong, not here):**
- A cloud PR is a draft — 2 of 3 carried a defect only local review found (the 3rd: a suite count from the local tree, not the branch). Two independent sessions wrote the
  same #136 reader blind spot, so it is the test-writer's blind spot, not one session's.
- `--teleport` is not a view. Cross-session messages to a session in another permission mode expire unless
  approved in its terminal; a file the owner pastes (`Read <path> and do what it says`) is reliable.
- My own `83805b3` added a default-refcheck finding (`MEMORY_FIXTURE.md`); fixed `d3eaf69`. The default run on
  `main` still shows 5 findings from the 2026-09-27 curate (`memory/gotcha-log.md`).

## Retired verbatim

*From `memory/cross-repo-prioritization.md` § "The cloud angle", 2026-09-29 close (read-surface thinning, #163).
Moved byte-for-byte; the source keeps a compact standing section.*


**Owner, 2026-09-29: $100 of Claude Code cloud budget; which part of the backlog can be fixed from there?**
⚠️ A SNAPSHOT: issue sets from the `gh` loop at **2026-09-29 08:31 +02:00** (≈410 open, 6 repos),
triaged mostly **from titles** — read each issue before dispatching it. Two rows spot-checked in code
(LD#145 `prepare_data.py:183` still an unweighted mean; LD#144 `train.py:1116` still strict `<`).

**What a cloud session cannot reach** (docs, via claude-code-guide, 2026-09-29 — code.claude.com
`claude-code-on-the-web`, `costs`): Anthropic-managed VM, GitHub repos only (several per session; private
via the GitHub App), push + PR yes, network default *Trusted* allowlist. **Not documented, so assume NO:
Tailscale, SSH to sadalsuud/gpu-server/b650, any GPU.** Measured from this checkout: `datasets/*`,
`data/`, `filters/**/model/` are gitignored — **no oracle-scored data, no training splits, no student
weights** in a clone (probe `.pkl`s are tracked). Also missing in cloud: the USER-GLOBAL skills
(`/review-changes`, `/curate`, `/audit-context`) and the auto-memory `feedback-*` rules in `~/.claude` —
a cloud session reads `CLAUDE.md` and repo `memory/` only.

**So the working rule decides the split: a cloud session can prove the PREDICATE (a test), almost never
the OUTCOME** (a production cycle, a flip count, a recall figure). Three classes:

| class | what it means | ship as |
|---|---|---|
| **C — closes in cloud** | inputs in git, done = a test or a static check | PR; merge after a local read |
| **D — draft in cloud, prove locally** | the code change is self-contained, the outcome needs a cycle or data | PR + an outcome line written into the PR body; the local session runs it |
| **L — local only** | GPU, oracle spend, production data, a deploy, or an owner ruling | not dispatched |

**C — candidates (read the issue first):**
- **llm-distillery**: #162 (registry test writes into the tracked registry), #144 (checkpoint ties),
  #146 (EmbeddingStage cache key lacks device), #115 (merge-script date sort), #136 (commit-msg guard
  can't read negation), #134 (refcheck skips `docs/`), #160 (ADR-013 Dutch-name sweep), #140 (two stale
  guides), #117 (license NOASSERTION), #118 (dependabot half only — the lockfile half needs the prod
  venv, #81). TODO item 2 (cd v5 `raw_min` 4.0006 vs 4.0) if the answer is "record the tolerance".
- **FluxusSource**: FS#240 (caption becomes summary), FS#239 (tag twins), FS#243 (comments feed picked),
  FS#200 (notes silently replaced), FS#179 (CEST → LMT offset), FS#198 (two ticked-but-absent tests),
  FS#168 (requests charset), FS#170 (mojibake conjunction detector — detector only, never a repair run).
- **ovr.news**: ovr#354 (mobile nav), ovr#320 (`startsWith` on compound names), ovr#297 (size-suffixed
  logos), ovr#289 (COALESCE vs `'{}'`), ovr#243 (safeId allowlist), ovr#362 (voice-ab REGISTER_CURRENT),
  ovr#369 (Gemini fallback docs), ovr#19 / ovr#63 / ovr#55 (tests + CI).
- **persuasion-scorer** doc/process rows: #23, #21, #18, #16, #11, #7.
- **pipeline-atlas**: #58 (SVG note wrap), #56, #12, #4, #85 (estate page deleted by render).

**D — draft in cloud, prove locally:** LD#145 (weighted overall_score — changes every future training
split; needs an owner nod), LD#165 / NM#556 (detector manifest + sha256 — weights live on the Hub, needs
an HF token in the cloud env), **TODO item 1b (execute decision 0: delete per-lens prefilters)** — the
deletion is repo-local, the "batch_scorer passes the rows it used to drop" proof needs data. NexusMind
code bugs with a production outcome: NM#506, NM#524, NM#526, NM#472, NM#525, NM#532, NM#487, NM#466,
NM#465, NM#459, NM#399, NM#355, NM#352, NM#350, NM#344, NM#362, NM#302, NM#518. ovr.news: ovr#376,
ovr#342, ovr#341, ovr#361. ⛔ Anything that syncs into NexusMind still goes through the diff-first rule
(`deploy_to_nexusmind.sh --dry-run`) locally.

**L — never dispatch:** training/seeds (LD#85, #71, #98, #100, #158, #104), oracle spend (LD#156 adverse
pool, #124, persuasion #4), production reads (LD#141, #128, #135, #147, #153, harm hand check), owner
rulings (LD#130, #159, #116, H-HD17), deploys/cutovers (LD#151, NM#395), and **FS source-health rows
(FS#232, NM#509/#510)** — a cloud VM's IP is a different fetcher, so its 403s answer a different question.
LD#163 (the read surface) is text-only and fits the VM, but its method needs `/curate`'s rules and the
owner's keep-rule calls — pair it, don't dispatch it.

**Budget — nothing here is measured yet.** Cloud usage is metered like any Claude usage (`/usage` in the
session); the docs give no per-session figure. ⚠️ GUESS, not measured: a C-class fix with tests is a few
dollars, so $100 is on the order of 15–30 C rows. **First step: dispatch 2–3 C rows, read `/usage` per
session, then set the pace from those numbers** — and record them here with the date.

**Pilot 1 — #162 → PR #166 (2026-09-29). ⛔ NOT A CLOUD RUN.** Launched with `claude --cloud`, but a
`claude --teleport <session>` process started ~08:37 (pid 20998, `ps` etime) and the work ran in the
LOCAL main checkout (reflog: checkout to the fix branch 09:18, commit 09:25, back to `main` 09:26 — the
checkout another session was using). So the cloud environment (setup script, allowlist, no secrets) is
still **untested**; only the model cost carries over. ⛔ **Never run the `--teleport` line `--cloud`
prints** — it pulls the session onto this machine. Review (`/review-changes`, 4 lenses incl. reachability +
claim-verification): **0 blockers, 3 warnings**; the code held under 5 mutations re-run locally. Cost
(`/usage` in the cloud session, owner-pasted): **$2.13** — Opus 5.5, 17.9k output, 3.7M cache-read tokens,
3m21s API time over 3h44m wall (idle ~3h after the PR, which matches PR creation 09:25). ⚠️ `$` is the
API-equivalent figure; the same panel shows plan-limit bars (session 14%, week 22%), so whether this
drew on the $100 credit or on the subscription is **not established** — check the billing page.
The local `/review-changes` (4 subagents) is extra and was not metered here. On this one sample,
$100 ≈ 45 fixes of #162's size — one sample, a small and well-specified issue. ⚠️ **A fresh clone is NOT the local baseline**: measured on a clean
`origin/main` worktree (`9d7304e`, `.venv/bin/python -m pytest tests/ -q`) — **18 failed, 48 skipped**
vs the profile's 25 skipped. All 18 fail identically on `main` itself: missing gitignored API keys
(`secrets.ini`) and detector model files (`test_scorer_run_fatal` 7, `test_preflight_deploy_guards` 6,
`test_harm_detector_contract` 3, `test_deepseek_model_guard` 2). **Put this baseline in every cloud
prompt**, or a session either "fixes" environmental failures or reports a suite count it cannot have
produced — PR #166's `1104 passed, 25 skipped` came from the local tree (keys and models present), not the branch.

**Pilot 2 — #136 → PR #167, merged `4ec7850` (2026-09-29). ⛔ ALSO NOT A CLOUD RUN** — the owner ran
the `--teleport` line (read as "a view"; it is not) at ~13:05 (pid 97345), and it continued locally.
Cost (`/usage`, owner-pasted): **$4.76** — 66.2k output, 10.0M cache-read, 11m49s API, **including two
fix rounds**. ⭐ **Review was the value, not the first draft**: the PR arrived with 34 green tests, 13/13
mutations caught and a thorough body, and still let real claims through — round 1: any "no X" within
3 words of the deploy word passed (`No regressions deployed v7` landed unverified; found by all 4
reviewers, reproduced end-to-end); round 2: the fix's `deploy: none` rule was unanchored (`Errors during
deploy: none` landed). Round 3 (deterministic): 40 claims blocked, 6 real negations pass, 101 tests,
suite = the same 18 fresh-clone failures by name. Its own green tests could not find this because it
wrote them against its own reading of the rule. **So: price a cloud fix as draft + local review, and
never merge a cloud PR on its own evidence.** Relay worked through a file the owner pastes
(`Read <path> and do what it says`); a `SendMessage` to a teleported session waits for approval and expired once.
Running total, both pilots: **$6.89 model cost**, not counting the local reviews (6 + 4 subagents).

**Pilot 3 — #134 step 3 → PR #168, merged `30e668d` (2026-09-29). ✅ THE FIRST REAL CLOUD RUN.** Cost:
**not read** (no `/usage` pasted before the owner stopped the pilots). Cloud facts, measured by that run:
push works (branch `claude/…`); `gh` absent and the GitHub API 403s (so it could not read issue comments);
the **full test suite hung ~2 h** (locally ~80 s, cause unknown) — cloud prompts must name targeted tests
only; `refcheck.py` counts and `run.sh` sensitivity are **environment-dependent** (no sibling repos, no
auto-memory, checkout named `repo`): clone 409 → 359 vs in place **277 → 227**. The work was right (11 fixes
all correct, no prose deleted) but 4 of its placeholder marks were false claims only this machine could
see (auto-memory, NexusMind). A 4th data point for the rule: **a cloud PR is a draft; the review needs
this machine.** Separately, a 4th session (`nexusmind-44`) did #136 in the cloud and **could not push**
(reason not established) — it reproduced both #167 bypasses independently, so the blind spot is the
test-writer's, not one session's.

**PILOTS STOPPED 2026-09-29 by the owner — focus moved to the gpu-server → sadaltager migration
(NexusMind#395).** Resume from here: the C-class list above is still valid; put the fresh-clone baseline and
"targeted tests only" in every prompt, follow via the `View:` link, never `--teleport` mid-run.
