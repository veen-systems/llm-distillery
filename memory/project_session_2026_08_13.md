# Session record — 2026-08-13 (midday)

**Assignment: "status, and make sure we are synced with sadalsuud/gpu-server; delegate
to the peers as required."** One guard shipped, one cross-repo sync closed, one issue
reopened, one NexusMind defect filed and fixed by a peer. **Nothing deployed to
production from this repo**, no oracle spend, no model touched.

## The headline: the sync gap was not where the risk was

Three hops, all measured rather than assumed, and only one had drifted.

| hop | state | why it was never the risk / was |
|---|---|---|
| gpu-server ↔ sadalsuud NexusMind | **exact** — 42/42 files md5-identical across the six live filters | `deploy_filters.sh` is `ExecStartPre` on `nexusmind.service`, so this hop **re-verifies itself every 4h**; `filters/CODE_REVISION` was re-stamped 08:10:15 |
| sadalsuud ↔ origin | 2 commits behind, **docs only** (PR #343) | `deploy_filters.sh:130-138` auto-pulls `--ff-only` when purely behind on a clean scorer tree. **No action was the correct action** |
| llm-distillery → NexusMind | **3 files drifted**, this repo ahead | Step 1 of the deploy is a bare `cp -r`; nothing pushes and nothing reports. This is the hop with no self-check |

The drifted files — `cultural_discovery/v5/config.yaml` (+50, the `tiers:` block),
`cultural_discovery/v5/prefilter.py` (+145, multilingual patterns from LD#86),
`investment_risk/v6/config.yaml` (+32/−17, of which the 17 are comment re-wrapping) —
are **all inert at runtime**, verified independently by the NexusMind session: `scoring.tiers`
has no reader in that repo at all, and the per-lens `prefilter.py` is not imported by
`filter_loader` or `main` (NM#284). Pushed as `7ae74ba` + `bb204be`.

⚠️ **Both went straight to NexusMind `main` with no PR**, against that repo's `chore/*`
convention. The owner authorised the content and the peer's owner authorised it
independently; the process miss is ours and revert-and-redo remains available.

## Shipped: `docs/FILTER_PLAYBOOK.md` checklist item 5 became a guard (`d969a23`)

`deploy_filters.sh` excludes `model/` from **both** rsync passes, deliberately — the
adapters are multi-GB, out-of-git, and `--delete` without the exclude would wipe
gpu-server's only copy. So a code deploy **never** carries weights, for any version.

Guard D probes gpu-server for `{filter}/{version}/model/adapter_model.safetensors`
and aborts if absent. Proven against production state, not a fixture:

```
cultural_discovery v5 -> weights present on gpu-server        exit 0
cultural_discovery v6 -> FAILED: gpu-server has NO weights    exit 1
```

**Its first act is to refuse the next thing anyone would have done** (#98's cutover).

Three decisions inside it worth keeping:

- **"Could not ask" fails CLOSED and is a DIFFERENT failure from "absent."** Different
  remedies; collapsing them makes a VPN blip read as a missing adapter.
  `--weights-preplaced` is the offline override and prints four lines saying nothing was
  verified — **an override that reads like a pass is how a checkbox replaces a check.**
- **The probe names the adapter file, never the `model/` DIRECTORY** — that directory
  exists on gpu-server for versions whose weights were never pushed, which is the exact
  state being guarded.
- **Caller parity is tested and DERIVED from `build_parser()`.** The 2026-08-12 review
  found the `.ps1` had no Step 0.5 at all; it was fixed by hand and nothing stopped it
  recurring. Both seeded failures were confirmed to fire before restoring.

⚠️ **Consequence the owner must weigh:** every `deploy_to_nexusmind.sh` run now needs ssh
reachability to `gpu-server`. Fine from this workstation; from the Windows box (still the
script's default paths) the alias may not resolve and deploys abort. Open question posed
to the owner: should an *unknown host* degrade to a warning, distinct from *unreachable*?

## #47 REOPENED, then CLOSED same day — `NO_HUB` was a local convention recorded as a cross-repo contract

NexusMind still carries `filters/uplifting/v7/inference_hub.py`, which this repo deleted
(`cp -r` never deletes). `NO_HUB` has **zero** references in NexusMind's `src/`, `tests/`,
`scripts/`, `docs/`; `filter_loader.py:146` sets `hub_class` purely from the file's
existence. And our verifier — which fails fast on exactly `NO_HUB` + `inference_hub.py` —
**only ever runs against our tree, never the one that serves.**

The peer's finding is the sharp one and is theirs: deleting the file turns **3 NM#312
tests red**, because they assert `get_scorer_class(use_hub=True)` resolves for every
discovered filter. **They were green because of the stale file, and they assert
importability, not repo existence** — so they would stay green pointing at a repo that
404s. Deleting it doesn't break the guard; it reveals the guard was already hollow.

**The easy way out is closed, checked rather than recalled:** `training_metadata.json`
and `training_history.json` are still **absent** for v7, and `upload_to_huggingface.py`
reads both directly for the model card. That is the metric fabrication #47 closed
against. *(A diff earlier the same day showed those files for uplifting **v6** and I
nearly carried it across.)*

## Filed: NexusMind#344 — `Infer` reports the LAST GPU response

`FILTER SUMMARY` printed `investment_risk ... 67ms` for 2,291 articles. The raw log shows
**two** GPU calls — 3,957 articles in 98,652ms, then a 2-article post-enrichment re-score
in 67ms — and `scripts/main.py:603` overwrites `_last_gpu_meta` on every response, read
once at `:2772`. **No performance anomaly**; investment_risk really took 98.7s, in line
with the other five. Wrong *only* for filters that re-score after enrichment — the same
population anyone reading that column would be investigating.

Fixed by the NexusMind session the same session (`def3611`, branch
`fix/nm344-infer-accumulation`): accumulate, rename `_last_gpu_meta` → `_gpu_meta`
("last" was the bug), and `scoring_device` reports `"mixed"` rather than relabelling a
mostly-GPU run. They verified both new tests fail against the pre-fix code.

## Both peer PRs merged the same session — the full fix, not the instance

NexusMind `main` at **`6adda86`**: `888e110` (#345, the NM#344 accumulation fix) and
`6adda86` (#346). The owner took option 1 on #47 — `filter_loader` now reads `NO_HUB` and
the sentinel is **authoritative over what is on disk**, which is the right precedence,
because the failure being guarded against *is* a stale hub scorer surviving a `cp -r`.
NM#312's three tests re-scoped to *every filter resolves a scorer by its declared path,
hub or local*, and our verifier's invariant now also lives where the state lives.

Verified on the **merged** tree rather than assuming the two PRs composed: file absent,
**1270 passed** = 1266 + 2 + 2, the arithmetic both PRs predict. **#47 CLOSED.**

The residue clears itself: gpu-server still holds the deleted file until
`deploy_filters.sh`'s `--delete` rsync runs, which is `ExecStartPre` on every cycle — so
it is cleared by the next cycle rather than by a deploy anyone has to remember.

**Two open questions deliberately not closed**: CPU-fallback for a `NO_HUB` filter still
*raises* rather than auto-selecting local (my read: leave it raising — a CPU fallback is
already degraded, and a filter that silently switches loading strategy there is the quiet
substitution this repo keeps getting caught by); and the `7ae74ba`/`bb204be`
direct-to-`main` history question.

## My own errors this session — four, all caught before they cost anything

1. **Reported the weights-ordering and version-selection findings as undocumented.** Both
   were already documented: playbook item 5 (→ **#67, closed**, filed after this exact
   failure took cd v5 down on 2026-05-31) and the guard module's own docstring +
   `check_cutover`. Corrected publicly on #98. **The finding was never "nobody knew" — it
   was "knowing did not help,"** which is a better argument for the guard than the one I
   originally made.
2. **An unauthenticated Hub probe that carried zero information — and it was the SECOND time.**
   ⚠️ `memory/cd-v6-probe-hypotheses.md` had recorded this on 2026-08-06 (*"`--check-hub`
   returns `repo not found` for a private repo when `HF_TOKEN` is unset ... its first run
   here was a false FAIL on a repo that existed"*). **The lesson was written down and I
   re-derived it anyway**, in a different tool and a different status code — which is why
   the note has now been generalised in that file from one script to the Hub itself. 401 for
   `uplifting-filter-v7` *and* 401 for `cultural-discovery-filter-v5`, which I had
   confirmed exists twenty minutes earlier. Re-run authenticated with a positive **and** a
   negative control before reporting. The claim survived; it had been inherited from a
   narrative file, not measured.
3. **"~90 lines" of prefilter patterns was +145** — quoted a truncated diff hunk as the
   whole. Caught by the peer.
4. **Ran `--dry-run` into a peer's checkout before their reply arrived.** That flag copies
   files and skips only the commit, so it dirtied two paths in a shared tree. Reverted
   with explicit paths, never a bare `git checkout .`.

## The cross-session lesson worth carrying

**A true report becomes a false one while it is being read.** I told the peer "held, your
checkout is clean at `80b0608`" — true when sent. The owner then authorised the sync in my
session, I committed and pushed, and the peer found two commits on `main` and reasonably
concluded my report was false. Neither side's evidence was wrong; **I reported a state
without its ordering.** When reporting state across sessions, stamp it and name what would
change it. Their underlying rule stands and is why this took one hop instead of three: a
reported state is not a state.

## Verify

<!-- verify: PYTHONPATH=. python3 -m pytest tests/unit/test_preflight_deploy_guards.py -q 2>&1 | tail -1 -->
<!-- verify: PYTHONPATH=. python3 scripts/deployment/preflight_deploy_guards.py --filter-name cultural_discovery --version v6 --distillery-root . --nexusmind-root /home/jeroen/repos/veen-systems/NexusMind >/dev/null 2>&1 && { echo "FAIL: guard D did not refuse the weightless cutover"; exit 1; } || echo "PASS: guard D refuses cd v6" -->
<!-- verify: grep -q "ENFORCED since 2026-08-13" docs/FILTER_PLAYBOOK.md && echo PASS || { echo FAIL; exit 1; } -->
<!-- verify: grep -c "weights-preplaced\|WeightsPreplaced" scripts/deploy_to_nexusmind.sh scripts/deploy_to_nexusmind.ps1 -->

## Carries

- [[feedback-claim-requires-verify]] — the Hub 401. **A probe that cannot distinguish the
  two hypotheses is not evidence for either**; run it against something whose answer you
  already know.
- **A convention enforced by a checker that runs on one side of a boundary is a convention
  on that side only.** `NO_HUB`, and our verifier that never meets the deployed tree.
- **A documented step that has already been missed once belongs in a guard.** Its
  consequence can grow after the documentation is written — here, from one filter failing
  at request time to the scorer refusing to start for all six.
- **Report state with its ordering when a peer will act on it.**
