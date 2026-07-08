# nature_recovery v4 — Implementation Plan

*Drafted 2026-07-08 after the v3→v4 pivot + oracle-labeling audit. Not executed — for a fresh session to pick up. nature_recovery v4 is intended to become the project's new **canonical reference filter** (superseding cultural_discovery v5): first with a trained multilingual screening probe, DeepSeek single-oracle + positive-mining, protection-as-recovery scope, and the agreement-gate discipline.*

---

## ⚠️ 0. Plan-review corrections — READ FIRST (4-model review, 2026-07-08)

**CRITICAL — settle before spending any money:**

- **C1. The runtime `recovery_evidence` gatekeeper defeats the #70 protection goal by construction.** `base_scorer.py:46-48` sets `GATEKEEPER_DIMENSION="recovery_evidence", MIN=3.0, CAP=3.5`, applied **at inference** (`filter_base_scorer.py:257-259`). A delivered-protection article with no measured recovery has recovery_evidence 0–2 → capped at **3.5 < 4.0 surfacing threshold** → can never surface, so §E acceptance fails no matter how the prompt scores it. **Decide first:** (a) exempt a `delivered_protection` content-type from the gatekeeper, or (b) redefine `recovery_evidence` so *documented pressure-removal / enacted enforcement* counts as ≥3 (makes protection a legit recovery-evidence path; likely moots the "independent dimension" fight in §A.1). Everything downstream is wasted until this is resolved.
- **C2. A prompt tweak will NOT break the halo.** The current prompt *already* says "rate the six dimensions COMPLETELY INDEPENDENTLY" and still produced PC1=91%. Make §A.5 a **falsification test with a numeric abort**: on the pilot, measure `protection_durability↔recovery_evidence` correlation under the new prompt; if it stays >~0.8, decoupling failed → pivot to C1(b), do **not** re-label 300–400 articles.
- **C3. Commit now — nothing is committed.** `git log main..HEAD` is empty; the plan, the v4 scaffold, and the scorer change are untracked on one disk. The ~$4 DeepSeek labels are gitignored on that same disk → **back them up out-of-tree** (`tar` `datasets/scored/nr_v4_*` + `datasets/gate/nr_v4_*`).
- **C4. DEPLOY = NO this session.** v4 has no model/calibration/gate; prompt is verbatim v2; §E/§F block deploy; the `.githooks/commit-msg` hook (#44) fails `verify_filter_package --check-hub` on any deploy-worded commit touching `filters/*/v*/`. "Commit/push/deploy" = commit scaffold+plan+scorer with a **non-deploy-worded** message, push the branch, **defer deploy to Phase 7**.

**HIGH — fix the plan before executing:**

- **H1. Partial re-label = two-rubric label schism (ADR-010).** Converting `conservation_appeal` to a soft-penalty shifts the per-dim distribution of *every* conservation-appeal article, not a pre-identifiable subset. Re-label the **full corpus** under the final prompt (DeepSeek auto-cache makes a 2nd pass far cheaper than the first $4), OR prove via a random control that unflagged labels don't move.
- **H2. Reorder: train the probe LAST.** §7 currently trains the probe before the re-label that changes labels → it would screen out the protection articles Stage-2 promotes. Correct order: strip prefilter → prompt revision + **full** re-label → assemble final corpus → **then** train probe → train student.
- **H3. The e5 probe must be a recall-first classifier, not L1 regression on 96%-floor labels** (which collapses to floor and re-creates the recall bug). Train on the MEDIUM+ label with class weighting/balanced sampling; set threshold from the val **recall curve**; validate against the 129 known-blocked positives.
- **H4. 36 high-band anchors can't train *or* calibrate the top; per-band isotonic on 3–4 val points is worse than global.** Upweighting/averaging add no signal density. Use **ADR-005 active-learning** (probe-seeded mining of more high-band), retain Gemini high-band as supplementary anchors, or **clip/ceiling** the top tier instead of isotonic-extrapolating.
- **H5. Fix the merge + §2/§C wording.** The 831 set (448 pos + 383 negs) is NOT "the re-labeled protection subset." Write `merge_nr_v4_final.py` **modeled on `scripts/merge_cd_v5_deepseek_final.py`** (prefer later-scored on id overlap; 0/831 overlap confirmed) → ONE final training file; the re-label is a patch-by-id.

**MEDIUM — corrections:**

- **M1. Belonging borrowing was mis-described.** The force-pass is **BasePreFilter's `POSITIVE_PATTERNS`/`POSITIVE_THRESHOLD`** (`base_prefilter.py:365-382`) — belonging keeps `POSITIVE_THRESHOLD=0` and renamed its list to avoid base's slot. Copy **base's ADR-018 mechanism**, not "belonging wholesale." Base's bypass overrides only *pattern* exclusions, not domain/source/length.
- **M2. Scaffold config cleanups** (do with §A's config revision): strip `tiers:` (ADR-016); `oracle: recommended` gemini-flash → deepseek; drop/refit `score_scale_factor: 1.3708` (stale; ADR-014 supersedes); `normalization.json` is v2's verbatim → carry as bootstrap, refit post-production; convert `conservation_appeal` in config `content_type_caps` **in tandem with the prompt**.
- **M3. Gate specifics.** `scripts/gate/agreement_gate.py` is greenfield (write per NM#229's 4 metrics). Get the **v2 student** from HF Hub (`jeergrvgreg/nature-recovery-filter-v2`) — not on disk. A local two-package comparison does NOT need NexusMind artifact-retention.
- **M4. Resume prereqs.** Re-verify DeepSeek balance (the $0.51 drifts) — top up **$10 not $5**; back up labels first; `huggingface_token` is empty (fill before Phase 7); cold-shell `ssh-add` may need `eval $(ssh-agent)` first. `filter_version:"3.0-deepseek"` is stamped in all 4,472 records — benign, note.
- **Verified correct:** soft-penalty mechanism/values match cd v5 exactly; hard-constraint conformance (§C/§D); issue dispositions; `--input`/`--output-dir`; belonging is the only filter shipping a committed probe `.pkl`.

---

## 1. How we got here

- Started as **v3**: retrain to stop decline/threat framing scoring as recovery (lld#60 + #56).
- **Pivoted to v4** (#70): the oracle exercise showed DeepSeek correctly demotes protection *announcements* the editorial gate publishes; product decision = **delivered protection wins (MPAs / protected acreage) should surface as recovery**. That's a prompt change, so it supersedes the verbatim-prompt v3.
- A **4-model label audit** (Opus/Sonnet/Fable/Haiku over the DeepSeek scores) surfaced 5 design learnings (§4).

## 2. Current state — DONE this session, do NOT redo (expensive)

**DeepSeek balance is ~$0.51** — the labels below cost ~$4 and can't be cheaply regenerated. All data is gitignored but on the workstation disk:

| Artifact | Path | Contents |
|---|---|---|
| Full re-score | `datasets/scored/nature_recovery_v4_deepseek.jsonl` | 3,641 (3,424 corpus + 217 decline negs), DeepSeek labels |
| Positive labels | `datasets/scored/nr_v4_positives_deepseek.jsonl` | 831 editorial-publish → 448 confirmed positives (high-band 3→36) + 383 boundary negs |
| Gemini corpus | `datasets/scored/nr_v2_corpus_full.jsonl` | 3,517 with original Gemini labels (for oracle comparison) |
| Batch inputs | `datasets/scored/nr_v4_batch_input.jsonl`, `nr_v4_positive_input.jsonl` | carry `_group`, `_gate_ct`, `_v2_wa` |
| Gate snapshot | `datasets/gate/nr_v4_heldout_probes.jsonl` (42), `nr_v4_heldout_ids.txt`, `nr_v4_sourceA_reference.jsonl` (154), `nr_v4_oos_trainpool.jsonl` (217), `nr_v4_named_probes.jsonl` | frozen pre-augmentation; disjoint from training |

Also done:
- **v4 package scaffolded**: `filters/nature_recovery/v4/` (config `version 4.0`, prefilter class `NatureRecoveryPreFilterV4`, prompt still = **verbatim v2** — not yet revised).
- **Scorer generalized**: `scripts/score_deepseek_production.py` now takes `--config`/`--prompt` (`load_filter_spec` derives dims + analysis field). Back-compatible with cd v5.
- **Branch**: `nature-recovery-v3` (rename to `nature-recovery-v4` on resume).
- **Issues filed**: llm-distillery **#70** (v4 protection scope), ovr.news **#262** (data-archiving loss — why the rotted articles were unrecoverable).
- **Validation**: spot-check + full run confirmed DeepSeek demotes decline (mean 1.5), preserves genuine recovery, and *correctly* demotes Gemini/editorial-gate over-labels (tourism, symbolic gestures, individual-animal, how-tos).

## 3. Locked decisions

1. **Oracle**: DeepSeek, single-oracle full re-score (validated; conservative-correct per [[feedback-conservative-oracle-better]]).
2. **Positive enrichment**: mined 831 editorial-`publish` articles → 448 DeepSeek-confirmed positives added (fixes high-band sparsity). The 383 DeepSeek-declined = boundary negs, kept with their DeepSeek labels.
3. **Weighting**: **UPWEIGHT positives** — `sample_weight_scale ≥ 2.0` (v2's value). Data-confirmed (86.6% floor, ~36 high-band). *This reverses an earlier mid-session "disable" call, which mischaracterized the knob — it's the needle-in-haystack lever, and we need it.*
4. **Protection (#70)**: admit **delivered** structural wins (enacted MPAs/protected acreage) as recovery-in-progress; **pledges/announcements stay capped**. Placement = Recovery (flag possible Solutions #43 overlap).
5. **Gate**: manual agreement-gate (NM#229 / vmodel held-out recipe); held-out frozen pre-augmentation (done). Harmonize on genuine recovery (Source-A), *require* divergence on the mis-lensed bug.

## 4. The v4 work (execute fresh)

### A. Prompt revision (#70 + audit) — the crux
The prompt is no longer verbatim. Changes:
1. **Delivered-protection path** — score enacted protection as recovery-in-progress (moderate ~5). **Critical (Opus audit): a weight bump is inert** — the 6 dims are collinear (PC1=91%, halo effect), so protection collapses into `recovery_evidence`. The *prompt* must instruct scoring protection **independently from explicit legal-designation/enforcement quotes**, decoupled from whether recovery is yet measured. Distinguish **delivered** (enacted, pressure removed) from **pledge** (will/target/draft — stays capped).
2. **conservation_appeal cap → soft-penalty** (ADR-015). Audit: 69% of conservation_appeal articles naturally score *above* the 2.0 cap → real MAE cliff. **Take cd v5's exact mechanism** (config changelog): hard caps clamp *all* dims to one value (destroys gradient → cliff labels, thriving v1 @ 0.94); the soft penalty instead **subtracts a penalty from each dim, floored at 0**, preserving dim-to-dim ranking while lowering the weighted average. cd v5's calibrated values (F/G/K=2.5, H=3.5, I=2.0) and multi-flag rule ("apply max_score clamp first, then subtract highest penalty"). Convert only conservation_appeal; leave truly-OOS caps (climate_tech) hard — cd v5 also kept its A–E hard and only softened F–K. **⚠️ Calibrate the penalty value on DeepSeek, not cd v5's Gemini numbers** — cd v5's 3-way validation found soft-penalty *firing rates differ 2.3×* between oracles (Gemini 60% vs DeepSeek 26% on the same prompt); DeepSeek under-fires (conservative), so a Gemini-tuned penalty will be wrong.
3. **Individual-animal contrastive example** — captive birth / IVF / single rescue-and-release vs wild-population recovery (lld#56 cat 4; ~61 now labeled, inconsistently scored 0–3.9).
4. *(optional)* tighten `measurable_outcomes` rubric to countable anchors (noisiest dim, oracle MAE 0.67); add a HERITAGE_ALIVE / nature-tourism line to the NOISE checklist.
5. **Calibration pass** (cd v5 playbook): ~20–30 stratified articles (delivered MPAs, pledges, measured outcomes, decline negs, conservation appeals) to verify boundaries hold before batch.
6. **Targeted re-label** under the new prompt: only the policy/protection/conservation-flagged articles change (~300–400). **~$0.40 — needs a DeepSeek top-up** (~$5 for margin).

### B. Prefilter overhaul — multilingual screening (fixes 21.6% recall bug)
Root cause: the keyword prefilter does topic-inclusion (`_is_nature_related`, English-only) + decline-detection (`disaster_no_recovery`, 43% precision) — both English-only, both the model's job. Verified: **blocks 129/598 genuine positives (21.6%)**, mostly non-English (~34% of NR is es/pt/fr/de/it/nl/id/vi…; 20+ languages in production).
**Adopt belonging v1's full recipe wholesale** — it already solved multilingual screening (it's the only filter with both a probe *and* multilingual prefilter patterns). nature_recovery's prefilter is currently the sparsest of all filters (only EXCLUSION/EXCEPTION/source_filter — it lacks OVERRIDE_KEYWORDS, POSITIVE_PATTERNS, POSITIVE_THRESHOLD, obit_signal that belonging/cd v5 have).
1. **Strip the topic/decline keyword gates** (`_is_nature_related`/`not_nature_topic`, `disaster_no_recovery`) — English-only, the model's job. Keep base commerce/domain exclusion (ADR-004). Update the self-test.
2. **Add a multilingual force-pass via BasePreFilter's `POSITIVE_PATTERNS` + `POSITIVE_THRESHOLD`** (`base_prefilter.py:365-382` — the ADR-018 mechanism; see §0/M1 — belonging feeds *per-category* thresholds instead, so borrow the *base* mechanism, not belonging's class). Populate multilingual recovery signals (NL/DE/ES/PT/IT/FR/… — "se recupera", "wordt hersteld", "rewilding", species-return verbs) so strong positives bypass **pattern** exclusions (note: base bypass does not override domain/source/length blocks). Belt-and-suspenders alongside the probe.
3. **Train a `multilingual-e5-small` probe** on the v4 corpus (same recipe as belonging v1 / uplifting v7; frozen embeddings + MLP). e5 is multilingual → screens by meaning in any language. Data is ready (4,472 labeled, 18+ languages).
4. **Calibrate the Stage-1 threshold** on the v4 val set to a target FN rate on MEDIUM+ (uplifting hit 0.9% at threshold 1.00) → replaces the stale `0.75 # TODO`. Final architecture: **commerce exclusion + multilingual POSITIVE_PATTERNS force-pass → multilingual e5 probe → student.**

### C. Assemble training set + train (gpu-server)
- Final corpus = re-scored 3,641 + 831 (re-labeled protection subset) = ~4,472; **upweight positives (`sample_weight_scale ≥ 2.0`)**; consider **multi-run averaging on the ~36 high-band** labels (cheap, single-oracle) to stabilize the sparse top.
- `prepare_data.py --filter filters/nature_recovery/v4 --input <final_scored> --output-dir datasets/training/nature_recovery_v4` (args are `--input`/`--output-dir`, not `--data-source`). scp to gpu-server (`export PYTHONPATH=…; HF_HUB_OFFLINE=1`).
- Train Gemma-3-1B + LoRA, v2 hyperparams. `load_base_model_for_seq_cls()`; **OLD PEFT key format; never `resave_adapter.py`**. Report **band-stratified MAE** (aggregate hides the sparse high-band).

### D. Calibration
- Isotonic per-dim; **inspect the curve** — only ~36 high anchors, risk of violent extrapolation. Consider per-band. Commit `calibration.json`.

### E. Agreement-gate (Phase 6 — blocks deploy)
- `scripts/gate/agreement_gate.py`: vendor NexusMind `display_ranking.calculate_display_rank` (point-in-time copy; freeze `now` at snapshot time). Dual-score v2 student vs v4 student on the frozen snapshot.
- **Probe-demotion**: decline probes (42 held-out + named) fall below surfacing band (Wilson CI).
- **Over-demotion guard**: `high_band_shift ≤ 0.05` on Source-A (154, independent genuine-recovery).
- **Protection acceptance (#70)**: delivered-protection probes now *surface* (≥ threshold); pledges stay capped.
- Agreement/Spearman on Source-A only, excluding mis-lensed. Commit the gate report + post to NM#229.

### F. Deploy (Phase 7 — only if gate passes)
- Doc standard: build cd v5's file set (`STATUS.md`, `__init__.py`, `calibration_report.md`, `dimension_analysis/` are missing from the v2-based scaffold) — belonging v1 is the doc template.
- Hub upload `jeergrvgreg/nature-recovery-filter-v4`; `deploy_to_nexusmind.sh` (fix its hardcoded `C:/local_dev` roots for Linux) → sadalsuud → gpu-server + **manual `scp` of `model/`** (deploy_filters.sh excludes it on first deploy, #67). Verify probes on gpu-server. Don't remove v2 until v4 verified.
- Close #60; #56 → PARTIAL (single-animal covered, crime/tourism partial, doom-with-growth thin); update #70.

## 5. Cross-cutting / canonical (separate tracking — don't bloat v4)

- **Multilingual prefilter bug is project-wide**: 13 prefilters use the English keyword-gate; only belonging v1 has a probe. → **File a cross-filter issue**: strip keyword gates to commerce-only + train e5 probes per filter. nature_recovery v4 is the reference implementation.
- **Dimension redundancy** (6 dims ≈ 1 axis, PC1=91%): compelling but rewrites the filter's structure/lineage. → **File a separate experiment issue** (collapse to ~2 latent axes); do NOT do it inside v4.
- **Canonical-reference update**: once v4 ships, update `memory/cd-v5-reference-status.md` → nature_recovery v4 is the new exemplar (multilingual screening + oracle+positive-mining + protection scope + gate). belonging v1 stays the *doc* template.
- **ovr.news editorial gate over-publishes** for Recovery (HERITAGE_ALIVE 85% declined; gestures/appeals/individual-animals) — signal for the ovr.news side (relates to #262).

## 6. Prereqs for the fresh session

- **DeepSeek top-up (~$5)** — balance $0.51; needed for the protection re-label + calibration passes.
- **gpu-server SSH** — reload the key into the forced agent socket: `SSH_AUTH_SOCK=/run/user/1000/openssh_agent ssh-add ~/.ssh/id_ed25519` (config pins `IdentityAgent` there; the key has a passphrase).
- **secrets.ini** — present at `config/credentials/secrets.ini` with `deepseek_api_key`; add `huggingface_token` for Hub.
- **Preserve the datasets/** artifacts (§2) — gitignored, on disk; regenerating costs money.

## 7. First steps on resume (corrected order — see §0)
0. **Resolve C1 (gatekeeper vs protection)** — this gates the whole pivot; decide the exemption/redefinition before anything else.
1. Back up the gitignored labels; re-verify DeepSeek balance + top up ($10); fill `huggingface_token`; reload gpu-server SSH (`eval $(ssh-agent)` if cold); rename branch → `nature-recovery-v4`.
2. **Strip prefilter** to commerce-only + base `POSITIVE_PATTERNS`/`POSITIVE_THRESHOLD` force-pass (M1). Self-test that the 129 positives are recovered. *(Don't train the probe yet — H2.)*
3. **Prompt + config revision** (#70 delivered-protection *reconciled with C1* + conservation_appeal soft-penalty in prompt **and** config + individual-animal example; config cleanups M2) → §A.5 falsification pilot (C2) → **full** re-label under final prompt (H1) → `merge_nr_v4_final.py` (H5).
4. **Now train the e5 probe** on the final corpus as a recall-first classifier (H3) + calibrate threshold vs the 129 blocked positives.
5. Assemble final training set (upweight positives) → train (band-stratified MAE; high-band per H4) → calibrate (no per-band isotonic on 3–4 points).
6. Agreement-gate (write `agreement_gate.py`; v2 student from Hub — M3) → **only if it passes**, deploy (Phase 7).
7. File the two cross-cutting issues (multilingual prefilter recall bug; dimension-collapse experiment).

## References
- llm-distillery #70 (v4 protection), #60/#56 (v3 decline fix, folded in), #67 (deploy model/ exclude); ovr.news #262 (archiving)
- ADR-004 (commerce = only universal prefilter), ADR-006 (hybrid), ADR-010 (oracle consistency), ADR-011 (embedding screener), ADR-015 (soft penalties / lens overlap)
- Templates: cultural_discovery v5 (retrain playbook), belonging v1 (docs + e5 probe)
