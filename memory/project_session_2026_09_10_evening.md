# Session 2026-09-10 (evening) — a vendor swapped our oracle, a detector shipped, and the review found five blockers in it

**Spend: < $0.01** (six DeepSeek probe calls). No oracle scoring runs. **Nothing deployed was touched; no filter package changed; NexusMind PR #474 is a DRAFT, not merged.**

## 1. DeepSeek V4.1 landed and the guard against it had already stopped working

Read the second announcement email (Pro shutdown postponed to **04:00 UTC 2026-09-14**; we never call Pro, so it moves nothing of ours). Rates confirmed on the vendor page, so the email-only caveat in `memory/oracle-pricing-scheduling.md` is discharged.

**Six live probe calls settled `#157`, and both of its proposed fixes are dead:**

- `GET /models` now returns **`deepseek-flash`** and **`deepseek-v4-pro`**. `deepseek-v4-flash` and `-vision-exp` are **gone from the listing** (the former still resolves).
- The response `model` field reads `deepseek-flash` **whatever you send** — alias, new literal, retired literal. No header carries a version.
- ⛔ **The served version is NOT OBSERVABLE through this API.** So "stamp the served model" records the **tier**, not the version, and would not have distinguished V4 from V4.1. And there is **no versioned flash id to pin**.
- The reasoning-mode trap survived. ⚠️ **Its symptom changed and the new one does not raise**: at `max_tokens=16` the literal id returns empty `content` (the 2026-08-14 break); at the production `max_tokens=4096` with `response_format=json_object` it returns **correct JSON** and bills **208 completion tokens against the alias's 6** (n=1, one trivial prompt — direction only). A run on the literal id looks healthy and quietly costs ~35×.

**The live defect:** `score_ollama_oracle.py` guarded the trap with `startswith("deepseek-v4")` — a **denylist of the ids that existed when it was written**. `deepseek-flash` does not match it, and it is now the only flash id advertised. The other two entry points had **no guard at all**. Replaced with an allowlist (`ground_truth/deepseek_models.py`), endpoint-aware, wired into three scripts, subprocess-tested; 2 mutations killed.

⛔ **Review then refuted my own scoping**: there are **six** DeepSeek call sites, not three. `filters/common/violence_promotion/v1/oracle.py` takes the model as a **constructor argument** and is unguarded; `relabel_deepseek.py` and `scripts/analysis/valence_bakeoff.py` hardcode the alias. And the host check is bypassable by a **root-anchored FQDN** (`api.deepseek.com.`) — verified live against DeepSeek's own 401. **Not fixed. → carry into the next session.**

## 2. `EXP-037` — the free harm-detector arm, and the shipped v1 package

Pre-registered before the first run. **$0.** Splits rebuilt to a **new** directory (`human_thriving_v8_scoped`, seed 42, `1,011/105/137` — the old dir is what every v8 gate number is measured against and was not touched).

**Primary: 2.0 of the 9 both-judge-flagged panel rows** (band 0–3, 5 seeds) at the pre-registered threshold rule, against a shuffled-label null of **0.0** firing at twice the rate. Decision rule's **2–4 bucket** → *stamp anyway; the $3.2–3.6 pool spend becomes a ranked option, not the only route.* Not upgraded on the post-hoc 0.50.

Two properties checked **before** training (the `#142` trap): **0 of 137 panel ids in the training corpus**, and **9/9** locally archived panel bodies byte-identical to what the judges read.

Shipped `filters/common/harm_detector/v1/` — a **5-seed ensemble**, **no threshold**, stamp-only. CPU vs CUDA: **0 verdict flips** at four gates (max |Δ| 7.15e-07). ⛔ **Do not generalise that** — the Gemma student's CPU→CUDA term is **0.1956**; a floor belongs to a population and a mechanism.

## 3. The review — four lenses, and what they found

⛔⛔ **THE KEEPER — I published a null-arm reading where the null could not have said yes.** The `EXP-037` README's sweep concluded *"and the null is still 0.0."* The null's **flag count** (omitted from that table) is **0.0 of 137 at thresholds ≥0.65 in all five seeds**, so its catch of zero is **arithmetically forced**. At 0.30 the null fires **more** than the real arm (22.4 vs 10.6), so *"it fires at twice the rate"* holds only at the pre-registered rule. **RETRACTED.** The PRIMARY is unaffected. ⭐ **This is the instrument rule — which this repo has in `CLAUDE.md` — violated in the document where I was congratulating myself on having a control.**

Two numbers wrong, both flattering the artifact: *"single seeds bounced 0–3"* over the plateau (they span **2–4**, and at 0.30 **three seeds beat the ensemble's 3**; 0–3 belongs to the val-picked point), and *"three of five seeds under 2%"* (**two**). Corrected on every surface.

**NexusMind PR #474 → DRAFT. Five reproduced blockers**, all recorded on the PR:
1. `enabled: false` is **NexusMind-side only** — the gpu-server loads unconditionally, its guard checks an 807-byte JSON before loading 12 files, and `load()` is unwrapped inside the lifespan: any failure takes **the whole scorer** down, and the deploy stops the old one first.
2. `validate_production_contract.py`'s stamp list is a **twin of the one I updated** and was not; Contract A's root is `additionalProperties: false`, so every stamped row would report a violation **attributed to FluxusSource**. Reproduced on 200 real rows.
3. `r.get("score")` with no presence check → a server shape change becomes a **permanent silent zero-stamp no-op**. Reproduced: 250 rows, 0 stamped, clean exit.
4. `_ping_healthcheck` enumerates a **hardcoded tuple**; `harm_preprocessing` is absent, so a crash pings OK.
5. The rewrite **permanently deletes unparseable lines** from `data/raw`, invisible in every counter — and harm sits **between obituary's stamp and its enforcement**, refuting my own code comment.

Plus: cold start ≈ **34,661 articles / 347 chunks** against a 60-req/60-s shared rate limit, with 429 absent from the retry list; a VRAM leak (harm never unloaded, third mpnet copy); the local fallback arm untested and running sklearn 1.9.0 against 1.8.0 pickles with **nothing on the row saying which stack scored it** — the 0.2008 floor, mixed into one corpus.

## 4. Two process failures of my own

- ⛔ **I ran `git stash -- .`** — a git verb taking the whole tree, the shape the working rules prohibit because a parallel session may share the checkout. Caught immediately, popped, tree verified. The rule exists so I do not have to get lucky.
- ⛔ **Second occurrence: I read 78→9 test collection errors as "the environment"** when it was `python3` instead of `venv/bin/python`. With the project interpreter: 1,643 pass. **A dismissal is a claim.**

## 5. All of it fixed, same session — and three of the fixes had the same defect as the code

**Owner call: NexusMind consolidates into one GPU-hosted package in the near term.** So the
gpu-server endpoint was **scaffolding for a boundary that goes away**, and building it was
building a deletion. `NM#474` rewritten: **8,660 chars out of `deploy/gpu-server/main.py`, 3,894
out of `gpu_client.py`**, zero harm references left. ⭐ **Blockers 1 and 3 were DELETED, not
patched** — the unwrapped lifespan load and the `r.get("score")` silent no-op cannot exist without
an endpoint. Measured cost of staying in-process: **19.9 articles/s on CPU** (137 real articles),
~3 min/cycle on the 8-core pipeline host. Cold start bounded to 3,000/run, **newest files first**.

Blockers 2, 4, 5 fixed with a test each. `_harm_detector_stack` now on the row (the 0.2008 stack
floor must stay separable). llm-distillery side: the ensemble check made **bidirectional**, pickle
hashes **actually verified** (`SHA256SUMS.txt` was read by nothing), `sklearn_version` read,
`batch_score` raises instead of returning `[]`, `stamp()` prefixed, the FQDN bypass closed,
`load_split` verdicts **enumerated**, `band()` allowlisting scalars, `val_spec_target_met` read.

⛔⛔ **THREE OF MY OWN FIXES REPEATED THE SHAPE THEY WERE FIXING: cheap checks placed after
expensive work.** The scaler was unpickled **before** its hash was verified; the
`sentence_transformers` import sat **above** every integrity check, making them unreachable in a
checkout without it — which is where CI runs; the empty-ensemble guard ran **after** the embedding
pass. All three moved. ⭐ **Verify before you load, and refuse before you spend.**

⛔ **My count of the DeepSeek surface was wrong TWICE** — three, then six, then **eight** from a
test that greps the tree. ⭐ **Enumerate a surface from the code, never from a list**; a list is
what was wrong both times.

⛔ **One mutation SURVIVED**: deleting the per-article cap passed all 11 tests, because the only
cap test exercised *file-level* deferral. Fixed, and the new test kills it. **11 + 6 mutations
killed overall; 790 + 1,649 tests pass.**

## Next session

1. **`NM#474`: a REVIEW ROUND and a SMOKE TEST** (owner deferred both). It is a draft; the rewrite
   has not been reviewed. Then the merge and the enable are two separate owner calls.
2. **DeepSeek V4-vs-V4.1 parity**, ~$0.92, arm A **free and on disk** (6,130 rows carry k=3 V4
   votes under a prompt file still hashing to `003cd35a5122`).
3. **Three decisions still open**: the ovr.news ADR-045 recency axis vs `#85`'s adjudicated rule
   (⚠️ `#85` is already RULED — what is open is cross-repo governance and the relabel it implies);
   `H-DET5` (re-measure across the `EXP-033` seed set first — mine, not the owner's);
   `filters/resilience/v1` (delete vs index).
