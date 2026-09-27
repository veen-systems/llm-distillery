# Session — 2026-09-05: the device timings get an experiment, and the experiment gets a review

**Spend $0.** No oracle calls. Nothing deployed — **deploy N/A, not skipped** (verified:
`ls NexusMind/filters/` on sadalsuud has no `human_thriving`; v8's weights are gitignored,
#97, and live only on `b650-gpu`; phases 8 and 9 have not run).

Commits `b94fa01` (EXP-022) and this session's follow-up (EXP-023). Continues
`project_session_2026_09_04_late.md`.

---

## What was asked

> *"have you also logged the experiments on cpu/gpu usage for the scorers?"*

**Answer: the numbers were logged; the experiment was not.** `EXP-019` carried five device
metrics, but the script was cited by no registry entry, wrote no output, recorded
host/device/batch only in a docstring, and ran **n=1 per arm**. The figures survived as prose
in a markdown file — which is how they passed the registry's greppable-metric check.

Then: *"wrap up, clean up the repo, update docs, then curate and commit… update hypotheses,
todo's and GH issues. Also merge, push and deploy if that is applicable."*

## The measurements (`EXP-023`, superseding `EXP-022`)

`b650-gpu`, 660-row v8 test split, batch 64, load excluded, **one arm per process**, device
read back off the object **and asserted**:

| arm | ms/article | n | spread |
|---|---|---|---|
| e5-small probe, GPU | **2.345** | 15 | 1.13% |
| e5-large **full probe**, GPU | **16.417** | 5 | 0.72% |
| e5-large encoder-only, GPU | 16.514 | 5 | 0.45% |
| student, GPU | **24.740** | 3 | 0.01% |
| e5-small probe, CPU | **42.541** | 3 | 0.12% |

student ÷ probe **10.55×**; break-even **56.9%**; two-stage saving at the adopted 89% routing
**1.52%**. **EXP-018/019/020's conclusions are unchanged.**

## ⛔⛔ THE KEEPER — I searched where the artifact could not be, and published the negative

I wrote *"the e5-large probe was never retained"* in four places and substituted an
encoder-only measurement. **It was at `b650-gpu:/tmp/probe_e5large.pkl` the whole time** — and
**eleven** probes were in that `/tmp`, including both EXP-019 regression heads and the
seed-42/seed-7 pair from the reproducibility work. My `find` was rooted at `/home/jeroen`,
which cannot reach `/tmp`. ⭐ **The instrument could not have said yes** — this repo's first
working rule, broken inside a document written about instruments that cannot say what they
claim. **36 days of uptime: one reboot from gone.** Rescued to
`~/llm-distillery/rescued_probes/`, manifest committed. ⚠️ Not in git — owner decision.

⭐⭐ **And the substitution was numerically harmless** — full probe 16.417 against encoder-only
16.514, the MLP head is free. **A harmless-looking substitution is exactly what stops anyone
re-checking the premise.**

## ⛔ The first re-run reported CUDA as CPU

e5-small "CPU" read **2.37 ms** against GPU's **2.34**. `EmbeddingStage` caches models keyed on
the **model name alone** (`embedding_stage.py:112`, read at `:214`), so `device` is ignored on
a cache hit while `self.device` still reads `"cpu"` — and `self.device` *is* honoured at `:195`
and `:284`, so half the object obeys the flag and nothing raises. True CPU is **42.5 ms, 18×
slower**. Filed **#146**. ⚠️ Latent, not live — but **on the `(name, device)` axis**, not the
name axis: fourteen filter configs share `multilingual-e5-small` and none passes `device`.

⛔ **"The only tell was that the two numbers agreed" was false.** `EXP-019` already recorded
**47.2 ms** for that arm — a 20× disagreement, written down in the very registry this work was
repairing. Honest form: *the only tell I used*.

## ⭐⭐ The variance is arm-specific, not a session effect

Three runs of `e5small-probe-gpu`, same box, same day: **2.332 / 4.746 / 2.345** — 2.04× apart
— while `student, GPU` and `e5-small probe, CPU` reproduced to **0.03%** and **0.31%**. The
unstable one is the **short** arm (~1.5 s of work); run 2 coincided with a review agent
benchmarking the same GPU, making contention the leading candidate. ⛔ **Not established** —
registered as **H-V8-21** with a method and a stated falsifier.

⚠️ The *"within-run spread 0.03–0.61%"* I published was a property of four quiet processes, not
of the arms: spreads of **32%** and **111%** appeared on the same arms later.

## ⛔⛔ VERIFICATION IS NOT REVIEW — fifth consecutive session

667 tests, refcheck, the registry checker, both budget guards, 21/21 verify annotations and the
structural check: **green throughout, and they found none of the six defects.**
`/review-changes` (4 lenses) found them all. **Four of six came from a reviewer going and
looking on the machine** rather than reading code.

Beyond the two above: the encoder arm truncated 27.7% of the corpus; the student's "unknown
provenance" was two commands away on the box; `device_verified` was **recorded and never
asserted**, so an all-arms wrapper would have re-created #146 and exited 0; `--gpu-repeats` /
`--cpu-repeats` were inert for two arms — the *"flag that parsed and did nothing"* shape,
shipped one commit after logging it.

⭐ **And a guard refused work I was confident about**: rewriting the write-up made **nine** of
`EXP-022`'s metrics untraceable. The registry's append-only rule protects the *entry*; an entry
is a pointer, and rewriting what it points at destroys the evidence while leaving the claim.
§7 of the write-up now carries the superseded figures verbatim.

## Also this session

- **Issues**: filed **#146**; commented **#104** (the device-label hazard, and the enumeration
  that clears this issue's CPU measurements), **#81** (a pinned venv did not make a timing
  reproducible), **#146** again (the two corrections above).
- **Working rule** *establish what a source excludes* → **20th occurrence**; the `pgrep` rule
  → **7th** (a wait-loop matched itself again, exit 143, inside this very work).
- **CLAUDE.md**: the `pgrep` bullet's ordinal removed and pointed at `working-rules.md`, per
  #133 — a count in the always-loaded file can only go stale, and that one had.

## Next session

**Phase 8 is unchanged and still next: the op-point, on the calibrated scale, with the owner.**
Nothing here moves it, and the cost measurements confirm there is still no Stage-2 cost
constraint. ⚠️ **One decision is owed**: whether the eleven rescued probes go into git.
