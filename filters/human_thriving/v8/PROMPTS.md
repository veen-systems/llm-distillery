# Which prompt is which — v8 prompt lineage

⛔ **`prompt-v8-4.md` is the current prompt** (`sha256 c4705408c477…`). Everything else in this
directory is superseded.

⛔ **Do not tidy the superseded files away, and do not move them.** Every run under
`docs/evidence/2026-09-03-v8-1-gate/runs/` stamps both a `prompt_hash` **and a `prompt_file`
path**, so relocating a rejected draft turns a stamped provenance field into a dead reference —
the same trap that stops `prompt-candidate-tail.md` being renamed to `prompt-compressed.md`.
Their being clutter is the price of the evidence being reproducible.

⚠️ **None of these is named `prompt-compressed.md`**, which is what `load_filter_spec` derives
from `config.yaml`. Every run so far passed `--prompt` explicitly. Resolve at phase 9 **by
copying, never renaming**: 6,586 labels record `prompt-candidate-tail.md` as provenance and a
rename breaks that pointer.

| file | sha256 (12) | status | what it is |
|---|---|---|---|
| `prompt-candidate.md` | — | superseded | the first v8 rewrite, article at the **front** |
| `prompt-candidate-tail.md` | `003cd35a5122` | **the labelling prompt** | article moved to the **end**; ADOPTED 2026-08-30 on H-V8-9's label argument. **The 6,586 Phase B labels are stamped with this hash** and 6,130 of them still are |
| `prompt-v8-1.md` | `32bbbdb68f38` | ⛔ rejected | first v8.1 draft, four clauses. Its §2 wording made commencement a **necessary** condition when the ruling made it **sufficient**, so a response that HAD taken effect escaped §2 |
| `prompt-v8-1b.md` | `9b71ba58e0c0` | ⛔ rejected | fixes that necessary/sufficient bug. Still carried clause D |
| `prompt-v8-2.md` | `4942ca92dc33` | ⛔⛔ rejected | all four clauses. Scored the #91 origin row **5.921 with 12/12 `in_scope`** where the labelling prompt pins it at 0.900 sd 0.000 — a **B×D interaction**, worse than any single clause |
| **`prompt-v8-4.md`** | **`c4705408c477`** | ✅ **CURRENT** | **B + C + A3, clause D dropped.** Gate B-A **9/9** at k=12, worst class-A sd **2.250 → 0.205**, `in_scope` runs on class A **3 of 108 → 0**, no-regression **4/4**. Used for the 456 above-op re-label |

There is no `prompt-v8-3.md` in this directory: that candidate (D with its licensing sentence
removed) lives in the evidence dir as `ablate_v83.md` because it was rejected before promotion.

## The clauses, and which survived

| clause | where | verdict |
|---|---|---|
| **B** — commencement: a policy change not yet in effect is an announcement; the *"especially as a trailing sentence"* qualifier is retired | §2 | ✅ in v8.4 |
| **C** — a delisting / sanctions move / grey-list exit reaches a jurisdiction, not a person | §3 | ✅ in v8.4 |
| **A3** — nothing has taken effect yet: proposal, draft law, plan, preparations | §5 list | ✅ in v8.4 |
| **A / A2** — the same rule as a **test inside §1** | §1 | ⛔ destabilises the #91 origin row |
| **D** — judicial relief whose only beneficiary is a convicted offender | §5 | ⛔ dropped: harmless alone, breaks the origin row together with B |

⭐ **A and A3 carry the same rule and behave differently.** A rule stated as a **test** inside a
reasoning step becomes a question the model asks of every article; the same rule as a
**category** in an exclusion list does not. A placebo of +996 chars of §1 restatement left the
origin row unmoved, so this is not about length or location — it is about what the text *does*.

Full measurements, the seven-arm ablation and the leave-one-out:
`docs/evidence/2026-09-03-v8-1-gate/`.
