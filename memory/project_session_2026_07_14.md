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
