# Session 2026-07-14 — "is nature_recovery running as planned?" → five dead controls

Started as a health check. Ended as an audit of controls that existed but had never fired.

## What triggered it

nature_recovery v4 was healthy: output every ~4h, all 10,625 articles/24h at `version 4.0`, the 3.75 op-point genuinely live (an article at raw 3.86 tiered `medium`, which is the band that ran inert at 4.0 before 2026-07-10). Two articles looked wrong — Spanish conservation stories flattened to 2.0 by `cap_applied: ['climate_doom']`:

| raw | article | why the cap fired |
|-----|---------|-------------------|
| 3.79 | Chile: seed-banking the last wild *Dendroseris neriifolia* | `extinción` in the lede — inside *"para evitar su extinción"* (to **prevent** it) |
| 4.28 | Ecuador: buying habitat for the vizcacha | `extinción` in the lede — the **IUCN Critically Endangered label**, boilerplate in every species story |

Neither is doom. Both had their recovery signals (`restauración`, `reintroducciones`) at char 2551+, outside the 500-char scan window.

## The finding that reframes #161

**#161 was never a model failure.** The five articles that motivated the 2026-05-08 `climate_doom` slice were scored **2.2–3.3 by v2's model** — correctly low. `normalization.json`, fitted at `raw >= 1.5` (fit-set median 2.19), mapped them to **5.2–8.3**, putting sparrow-population-decline on the Recovery lens at **8.34/10 "high"**. Replaying all five raw scores through v2's `normalization.json` reproduces production **exactly, 5/5**. The cap was a keyword band-aid over a threshold error.

Rescoring those five against the **v4** model (gpu-server CPU, scorer left at rest):

| article | v2 raw | v2 displayed | v4 raw |
|---|---|---|---|
| sparrows (ES) | 3.30 | **8.34 "high"** | **1.60** |
| peach trees | 2.38 | 6.14 | **0.36** |
| deforestation | 2.33 | 5.93 | **0.95** |
| cyclone Gabrielle | 2.32 | 5.90 | **0.56** |
| controlled burns | 2.23 | 5.16 | **1.89** |

**0/5 surface.** All below the 3.75 op-point *and* below the cap's own 2.0 ceiling — the cap cannot act on them at all. Under v4 it is a dormant safety net; in 24h its entire effect was 165 triggers → 163 no-ops → 2 bites, **both wrong**.

Conditionality confirmed by simulation: fit at 3.75 → all five clip to ~0.56 (cap moot). Fit at v2's 1.5 → `burns` re-inflates to **5.32** and the cap becomes load-bearing again. So the cap's redundancy depends entirely on fitting at the op-point.

## Five controls found dead

Each added in good faith. None had ever been watched fire.

1. **`.githooks/commit-msg`** (the #44 deploy-claim gate) — committed mode **100644**; git silently ignores non-executable hooks. Every clone that followed CLAUDE.md's setup step got a no-op. Also invoked bare `python` (only `python3` exists), so even once executable it could never *pass* — which trains `--no-verify`.
2. **`deploy_filters.sh` freshness gate** — the deploy *hash* covers `src/scoring/`; the origin/auto-pull gate only diffed `filters/` + `src/filters/`. A scoring-only commit skipped the pull, hashed the stale checkout, matched gpu-server's stale revision, printed *"already in sync"*, exited 0. **Reproduced live** against this session's own fix.
3. **`content_type_caps.*.exceptions:`** — documented in config ("Doom framing followed by documented recovery outcome"; the Chile article hits it exactly), never compiled into `cap_triggers.py`.
4. **`config.yaml scoring.tiers`** — read by nothing. Still live in **sustech v3**: config `3.0`, code `4.0`.
5. **Three `MEMORY.md` verify assertions** — reported FAIL on claims that were all **true**.

## What shipped

**llm-distillery** (`nature-recovery-v4`):
- `33fba44` — `fit_normalization.py` derives `--min-score` from the op-point (AST-parsed from `TIER_THRESHOLDS`, lowest non-zero, name-independent) and **refuses** below it. 22 new tests; mutation-tested.
- `9b6126d` — commit-msg hook made executable + interpreter resolved. Verified blocks/passes/scopes correctly.
- `7be2368` — verify assertions rewritten: claim decides PASS/FAIL, transport/deps surface ERROR. Each state verified to fire.
- `fe07211` → `4254487` → `7f59d4d` — gpu-server access note (three corrections; see below).

**NexusMind** (`main`, pushed):
- `8681efa` — overrides scan full body, triggers stay lede-bound. A/B over 10,625 articles: 33 change state, only **2** above the 2.0 ceiling — exactly the two false positives. Nothing else moves.
- `4e25934` — `SCORER_PATHS=(filters/ src/filters/ src/scoring/)` so the gate covers what the hash covers.

## Deploy posture

`nexusmind.service` runs `deploy_filters.sh` as **ExecStartPre** and `scorer-stop.sh` as **ExecStartPost** — that wiring *is* the always-rest rule. So the deploy was pushed, not hand-run: forcing it would start the scorer outside a scoring run and starve ollama of the 16GB GPU. sadalsuud needed one manual `git pull --ff-only` to bootstrap (the gate fix can't deliver itself — `scripts/` isn't in `SCORER_PATHS`).

## Where I was wrong (engineer caught all three)

1. **"No gpu-server key from situla, must hop via sadalsuud"** — false. The link works; `id_ed25519` was just locked. **The hop worked**, so the wrong model kept getting confirmed. An error whose workaround produces green results never falsifies itself.
2. **First gpu-server note documented the wrong agent** — said gcr; gpu-server pins `openssh_agent`. `ssh-add -l` reads gcr and lists `situla@veen` even when openssh_agent is empty — a false-positive diagnostic.
3. **Second note asserted the two-agent split was deliberate** — the engineer doesn't recall creating it. Invented intent. Testing then killed my follow-up hypothesis too: forcing gpu-server through gcr **hangs** (gcr advertises keys it hasn't unlocked and prompts on use), so the passphrase gate is real, not illusory.

Three plausible claims, none checked before being written down — the same defect as the code this session fixed, applied to memory.

## The lesson

Not "add more checks." Every one of these **was** a check. The distinguishing property of a real control is that **someone has watched it fail**. Today's fixes only count because the new tests were run against the *old* code and observed failing — that is the only reason they're known to test anything.


## Coda — the cap was retired the same day (17:00)

The override-window fix deployed at **12:11** and worked: the deployed detector on
gpu-server releases both Spanish articles. But the **16:40** batch surfaced a third
false positive the fix cannot touch:

> **"Ecuador's Amazon coffee farmers get ahead of Europe's deforestation rules"** —
> raw **4.66**, capped to 2.0. Trips on `deforestation` inside **`deforestation-free`**
> (`\b` matches across the hyphen). Zero recovery vocabulary in 12,627 chars, so no
> override could rescue it. Scores were a coherent conservation story:
> recovery_evidence 4.58, human_agency 6.91, 400 producers, 5,000 hectares.

All three bites share one shape — the trigger word in a **non-doom construction**
(`evitar su extinción`, `en peligro crítico de extinción`, `deforestation-free`).
The regex is polarity-blind; patching each is whack-a-mole across five languages.

**Final scoreboard: 3 bites, 3 false positives, 0 saves.** Retired in NexusMind
`1dd5e49`. The principled reason: the `recovery_evidence` gatekeeper (`<3 → cap 3.5`,
below the 3.75 op-point) already does this semantically — doom scores
recovery_evidence 0.07–1.08, the coffee FP scored 4.58. The cap was a regex
overriding the model's *correct* judgement, costing exactly the recall #71 chases.

I had recommended keeping it as defence-in-depth six hours earlier. That was wrong;
the evidence since was one-directional.

**The gate fix proved itself**: `1dd5e49` touches only `src/scoring/`, the exact case
the old freshness gate missed. Verified on sadalsuud — old gate MISSES, new gate
detects and auto-pulls. No manual bootstrap needed this time.

Deploy queued for the 20:00 cycle; expect `CODE_REVISION` `29d3e3a0…` (was `3bbfcf93…`).

---

## Part 2 (evening) — two review rounds, and what they cost

**Round 1** (`2598ffa..1dd5e49` / `ffe4172..bef87d4`): 10 confirmed. Its **top finding was wrong** — it claimed the normalization guard "mixes scales" and would collapse recall. I amplified it into a plan and a quantified table ("2,776 hidden articles across 5 lenses"), and framed linear `score_scale_factor` as the healthy baseline.

The engineer stopped it with a question, not a check: *"Can it be that you are not understanding the normalization procedure? … I think not the linear scaling?"*

ADR-014 specifies the pipeline as "…normalize → **reassign tier on normalized** → display_rank". `production_scorer.py`'s docstring says it 250 lines above the line I'd read. So `raw >= threshold` + `tier: low` is **correct by design**. And foresight uses `scale_factor` only because its fit was REJECTED by `MAX_NORMALIZATION_RAW_MIN` (#205) — the opposite of healthy.

The evidence that settles it, and which nobody had ever written down:

| filter | raw_min | |
|---|---|---|
| belonging, cd v4/v5, invR v6, sustech v3, uplifting v6/v7 | **4.00** | == tier threshold |
| foresight v1 | 5.01 | drifted HIGH → #205 |
| nature_recovery v1 / v2 | 1.51 / 1.50 | drifted LOW → **#161** |

7 of 9 comply. The 3 that don't are the only 2 normalization incidents this project has ever had. **One assertion catches both** — now `tests/unit/test_normalization_invariant.py`.

**Round 2** (`1dd5e49..ba827e4` / `bef87d4..a608da0`): 8 distinct, **4 of them inside round 1's fixes**:

- The dirty-check premise I wrote in a comment and never ran. `git diff --quiet <paths>` is worktree-vs-**INDEX**; `git add` defeats it. Verified: a staged edit passed while the hash named a blob without it and rsync shipped the worktree.
- My invariant test was **too strict** — `raw_min` is the smallest score *observed*, not the fit threshold. It passed only because the files are dense (invR 4.0003, cd v5 4.0006) and the tolerance absorbed it by luck. Now a range: `[op_point, 4.5]`.
- My invariant test **re-implemented its own subject**, and the copy drifted within the same commit.
- The #205 mirror gated on `args.min_score` instead of the written `stats.raw_min`; `--filter-version` fell back to the directory name; `--allow-thin-fit` clobbered the package it says never to deploy to.

## Deployed and verified 20:08

`d3c2f8d8` live on gpu-server; registry empty; `cap_applied` permanently `null`. The log line that matters:

> `Local main is 4 commit(s) behind origin/main on filters/ src/filters/ src/scoring/ (clean fast-forward) — auto-pulling`

That is the `src/scoring`-only case the old gate missed. **The morning's gate fix proved itself in production the same day it was written.** Also checked, not assumed: three of those commits modify `deploy_filters.sh` *while bash executes it* — git writes-and-renames, the running shell holds the old inode, old content runs to completion.

## The scorecard

Five of the day's corrections came from adversarial review. **The two most consequential came from the engineer** — "go read the design" killed a false narrative already baked into a plan, and "I don't remember the intent" sent me to an ADR that said the opposite of my conclusion.

Reviews catch what I can't see in myself. They do not catch what the reviews and I both get wrong — and today that was the single most expensive error.
