# Session 2026-09-27 (afternoon) — ADR-024 step 3: manifest-driven detector deploy, built, reviewed, merged

**Opening ask:** "pls continue" = `docs/TODO.md` ▶ NEXT SESSION item 0 (ADR-024 order step 3).
**Later asks:** push the commits and tell the NexusMind session; (owner) wait for NexusMind's signal, then a PR;
wrap up, curate, commit.

## Threads
| thread | state |
|---|---|
| ADR-024 step 3 code (`deploy_detectors.py`, deploy script 0.7/2a/2b, sidecars committed) | ✅ closed — `6c16056`, `44b703d` |
| Review before any real deploy (TODO required adversarial + reachability) | ✅ closed — 3 rounds (the cap) |
| Push + tell NexusMind (`nexusmind-b2`) | ✅ closed |
| First real deploy | ✅ merged as NexusMind PR #550 (`dafbbc9`, 13:47Z) after NexusMind's two-lens review |
| Production outcome (`H-DP3`) | ⏳ partial — due at the ~16:10 CEST cycle; check is TODO item 0 |
| ADR-024 steps 4–5 | not ours (NexusMind); step 4's start is the owner's call |

## What was built
- **Step 0.7** (before step 1): `deploy_detectors.py stage` fetches every file each committed `MANIFEST.json` lists
  (hub files at the pinned revision; git files from this repo), verifies sha256 + size. Refuses: manifest or git-origin
  file not committed as-is, unpinned `hub`, sidecar not carrying its pickle's manifest digest (or pickle unlisted),
  `.nexusmind-owns` entry inside a packaged dir, unsafe paths.
- **Step 2a**: `place` writes, prunes ONLY previous-manifest − new-manifest, writes `MANIFEST.json` last and only on
  success, re-hashes the target. `--dry-run` = `--plan`. No write/delete through a symlink at any site.
- **Step 2b**: old runtime copy minus packaged dirs (`common_runtime_files.py --unpackaged`, 101 → 35 files).
- 10 `.sha256` sidecars committed (byte-equal to the manifest entries); obituary `.gitignore` negation.

## Evidence
- Predicted by `--plan`, then measured through the SHIPPED script on throwaway clones (3 times, after each fix round)
  and on the PR branch: harm/commerce 0 existing bytes written, obituary v5 / violence v1 only `training_config.json`
  (#158 block, owner-ruled), 4 `MANIFEST.json`, nothing pruned; `verify --all --strict` OK; second run a no-op.
- Clean `main` `a8835c0` before: obituary v5 + violence v1 MISMATCH, harm OK, commerce MISSING (gitignored model).
- Suite `.venv/bin/python -m pytest tests/ -q`: 1096 passed, 25 skipped (tree held only this change).
- Mutants: 49 over three rounds; 48 killed, 1 equivalent (`cat-file` vs `ls-files` when `diff HEAD` also runs).

## Review
- Round 1 (6 lenses): the "committed" check was `git ls-files` (passes staged-only) in code AND test — 3 lenses;
  symlink dir escape; prune-before-manifest ordering; malformed previous manifest crash; relative TMPDIR; stale docs.
- Round 2: `.deploy-tmp` symlink bypass; two non-converging re-run cases.
- Round 3 (class recurred): symlinked package/detector dir; file↔dir layout change tracebacks; symlink loop.
- Measured limits (step 5, NexusMind's): `*.safetensors` gitignored there, so commerce's verified model never travels;
  `deploy_filters.sh` does not `--delete` under `models/`.

## Mine (errors)
- Fixed the symlink class one site per round instead of enumerating it (gotcha 2026-09-27).
- Shipped the `ls-files` idiom in the check AND its test (gotcha 2026-09-27; Mechanized row proposed).
- PR #550's "before" claim measured on a clone of the wrong branch; caught by re-measuring on `origin/main` before
  messaging, corrected with `gh pr edit` (gotcha 2026-09-27).

## Owner rulings this session
- Wait for NexusMind's signal, then deliver the first deploy as a PR (not a direct commit). Then: "they will do it"
  (NexusMind merges, not me).

▶ **NEXT:** `docs/TODO.md` ▶ NEXT SESSION item 0 — close `H-DP3` on sadalsuud.
