# Session 2026-08-09 (night) — the prerequisite, not the task

Sent to start **#102** (`uplifting v7` specificity: 8.1% FPR vs 2–3% elsewhere;
candidate op-point move 4.0 → 4.5). **#102 was not started.** The owner opened by
asking me to explain two traps from the previous session rather than act on them,
and one of the two turned out to be **wrong**. That is the shape of the session:
it removed a confound sitting under #102 instead of executing #102.

**Nothing deployed. Nothing needed deploying.** No filter package, prompt,
threshold, config or model artefact changed. Everything committed is evidence,
tooling, memory or docs.

## 1. The headline: b650 is cleared at 4.0, NOT at 4.5

`filters/uplifting/v7/ground_truth_gate.json` recorded honestly that it was
measured on b650, *not* the serving box, and flagged "unquantified cross-box
uncertainty". Since **spec 0.9189 is the entire premise of #102**, that had to be
quantified first.

Re-scored the same 660 rows on gpu-server's **serving venv**, with adapter
weights, tokenizer, `inference.py`, `base_scorer.py`, `config.yaml`,
`calibration.json`, all three `filters/common/*` modules and the split **verified
md5-identical on both boxes** — and this repo's `fit_calibration.py` copied to
both so the inference code is provably the same object.

| | gpu-server serving venv | b650 |
|---|---|---|
| tp/fn/fp/tn @4.0 | 159/57/36/408 | **159/57/36/408** |
| recall / spec @4.0 | 0.7361 / 0.9189 | **0.7361 / 0.9189** |
| flips @4.0 | — | **0 of 660** |
| flips @4.5 | — | **3 of 660** |
| spec @4.5 | **0.9730** | 0.9662 |

- bit-identical rows: **15/660 (2.3%)**
- calibrated weighted \|Δ\|: p50 **0.0000**, p90 0.0345, p99 0.1198, **max 0.2008**
- **1 row exceeds the #95 0.16 floor**; signed mean **+0.00018** → noise, not a shift

**The rule this establishes: a box is cleared AT A THRESHOLD, never in general.**
The e5 probe's 4.2e-6 parity does **not** transfer to the Gemma student. And the
p50 of exactly 0.0000 is a trap — raw logits are bf16-quantised (~0.03 steps), so
most disagreements are hidden rather than absent.

Still unmeasured for the student: **CPU vs CUDA**. Today isolated the *library
stack*, on CPU both sides; production serves on GPU. The 5.4e-6 CPU-vs-CUDA
figure in [[b650-gpu]] is the **probe's**.

Harness now exists and is committed: `scripts/verification/box_parity.py` +
`diff_box_parity.py`. Before this, `memory/b650-gpu.md` instructed sessions to
"re-run the parity harness" and **no such harness existed** — a pointer to
nothing, which is the same failure class as [[feedback-enumeration-is-not-inventory]].

## 2. #102 pre-work: the sweep, on production predictions

On-lens fixed at oracle ≥ 4.0; only the student's bar moves.

| student thr | recall | spec | **FPR** | fp |
|---|---|---|---|---|
| **4.00** (now) | 0.7361 | 0.9189 | **8.11%** | 36 |
| 4.25 | 0.6667 | 0.9459 | 5.41% | 24 |
| **4.50** | 0.6111 | 0.9730 | **2.70%** | 12 |
| 4.75 | 0.5602 | 0.9842 | 1.58% | 7 |
| 5.00 | 0.4769 | 0.9887 | 1.13% | 5 |

4.5 lands between `solutions v6` (2.8%) and `nature_recovery v4` (2.1%) — exactly
#102's hypothesis. Trades 24 fewer FPs for 27 more FNs: right direction under
ADR-023. **Not a decision** — no #95 band applied, `ground_truth_gate.py` not
used, split is 32.7% enriched.

Note there are two defensible definitions of the positive class and they answer
different questions: fixing on-lens at 4.0 (used above) vs letting truth follow
the student's bar (which changes the positive set 216 → 193 between 4.0 and 4.5,
so its recall is not comparable across rows of the table). `diff_box_parity.py`
takes a flag; the default is the fixed cut, which is the ADR-023 question.

## 3. A prior diagnosis of mine was wrong

**b650 "cannot run Gemma on GPU because gcc cannot link `libcuda.so.1`" is
false.** Reproduced it: triton's helper compile dies on
`cuda_utils.c:9:10: fatal error: Python.h: No such file or directory`.
**`python3.12-dev` is not installed.** `libcuda.so.1` *and* the dev symlink are
present, in `ldconfig -p`, and `gcc` links them with triton's exact flags at exit
0. The wrong reading came from the **tail of a `CalledProcessError`**, which
prints the failing command line — ending in `-l:libcuda.so.1`. gcc's real error
is further up the traceback.

**Generalisable trap: a subprocess exception's rendered command line is not its
error message.** Fix (untried, needs sudo): `sudo apt install python3.12-dev`,
then `ssh b650-gpu '~/llm-distillery/venv/bin/python /tmp/tk.py'` (repro left in
place). Related [[feedback-claim-requires-verify]].

Timing correction too: the 660-row split is **~16 min on b650**, **~30 min on
gpu-server CPU** — not the "~7 min" recorded yesterday.

## 4. Five interpreters, five stacks — root cause is `requirements.txt`

| | gpu-server serving (**prod**) | sadalsuud | b650 | situla `.venv` | gpu-server system |
|---|---|---|---|---|---|
| torch | **2.11.0+cu130** | 2.12.1+cpu | 2.13.0+cu130 | 2.13.0+cu130 | 2.5.1+cu124 |
| transformers | **5.0.0** | 5.12.1 | 5.14.1 | **4.57.6** | — |
| peft | **0.18.1** | 0.19.1 | 0.19.1 | 0.19.1 | *missing* |
| sentence-transformers | **5.2.2** | 5.6.0 | 5.6.1 | *missing* | 5.2.3 |
| sklearn | **1.8.0** | 1.8.0 | 1.8.0 | **1.9.0** | — |

All five satisfy `requirements.txt`, because it declares **ranges**. A range file
cannot reproduce production. Production is now frozen in
**`constraints/production-gpu-server.txt`** (91 packages, diffed against a fresh
`pip freeze` to prove nothing was lost). **`torch==2.11.0` there is really
`2.11.0+cu130`** — pip freeze strips the CUDA local-version tag, so a reinstall
from PyPI defaults gives a different build under the same version number.

**Direction is one-way: dev boxes move to production, never the reverse.**
Changing torch/transformers under the student changes scores, and the change
cannot be distinguished from the #95 band without a full ADR-021 gate run per
filter — a large job that buys nothing.

Two live hazards on situla, unfixed: **sklearn 1.9.0** vs 1.8.0 everywhere else
(b650 was deliberately pinned to 1.8.0 to match the obituary pickles), and **no
`sentence-transformers` at all**, so the e5 probe path cannot run locally.

## 5. A fourth box: `sadaltager`

RTX 5060 Ti 16 GB (Blackwell **sm_120**), driver 610.43.02, 12 cores / 14 GB RAM,
425 GB free, on the home LAN (192.168.1.63). Only venv `~/torch-test`: **torch
2.11.0+cu128 and nothing else**. Because it is empty it is the cheapest box to
build *from the lockfile*, and its torch already matches production's version.
**Unverified prediction: no `python3-dev` either → same triton failure as b650 on
first GPU JIT.** If it ever becomes a scoring box, sm_120 vs the 4080's sm_89 is
a *second* skew axis on top of the library one.

## 6. Two emails, both live

- **DeepSeek API price rise announced 2026-08-06** — "significant increase", no
  numbers, no date; continued use counts as acceptance. **The number that decides
  it is +64%**: DeepSeek off-peak $0.0011/article vs Gemini Batch ~$0.0018. Above
  that, Gemini Batch is cheapest and the cd v5 DeepSeek-as-default precedent is
  void. DeepSeek **peak** ($0.0022) is *already* dearer than Gemini Batch. Whole
  decision ≈ $5–6 per 8K-article retrain — it changes which oracle we default to,
  not whether we can afford to retrain. Banner added to
  [[oracle-pricing-scheduling]], whose opening line ("a scheduling lever, not a
  price hike") is now false going forward. **Not affected: #102** (Gemini Flash).
- **Odido maintenance Tue 11 Aug, 01:00–07:00.** Verified rather than assumed:
  situla (…100), sadalsuud (…101) and sadaltager (…63) all route via
  **192.168.1.1** — one uplink, so all three drop together with Tailscale reach
  to gpu-server/b650. **The 04:00 cycle is lost.** `Persistent=true` will *not*
  catch it: the host stays powered and the timer fires, it just fails; Persistent
  only replays runs that never fired. 08:00 recovers. **Expect a failed cycle in
  Tuesday's logs and do not diagnose it as a regression** — that phantom-outage
  chase already cost a session on 2026-07-31.

## Traps hit or avoided this session

- **`git check-ignore -v` prints the last matching pattern *including negations*,
  so its output looks like "ignored" when the file is not.** I misread it and
  briefly concluded my `.gitignore` negation had failed. `git add --dry-run` is
  the check that answers the question. (`datasets/*` would otherwise have
  silently swallowed the parity dumps — same shape as the `datasets/adverse/`
  negation block already there.)
- **A stale progress line is not a stalled job.** gpu-server sat at "160/660" for
  ~10 minutes because its stderr buffers when redirected. The reliable check was
  the CPU-time delta from `/proc/<pid>/stat` fields 14+15 twice, 15 s apart
  (9,275 ticks / 15 s ≈ 618% CPU). I published a "~5 minutes" ETA off the stale
  line and had to correct it.
- **`sensors` was not installed on b650**, so the first temperature reading I got
  back was `acpitz 16 °C` — a junk zone. Real value came from
  `/sys/class/hwmon/*/temp*_input` → `k10temp 76 °C` under load, well inside a
  ~95 °C throttle point.

## Next session

See `docs/TODO.md` top block. Short version: **#102 step 2 can run immediately** —
the production-venv predictions are committed at
`datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl`,
so `scripts/gate/ground_truth_gate.py` needs no re-scoring. **Adjudicate the 21
`solutions_story` candidates before any threshold move** (ADR-015: they may
belong in both lenses).
