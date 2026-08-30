# Experiment Registry

An append-only, machine-readable index of experiments run in this repo: what was asked, what was
decided, what it cost, and where the real evidence lives.

**Adapted from `veen-systems/augur`'s `experiments/README.md`** — the schema, the `EXP-NNN` id
space, the decision vocabulary and the append-only correction rule are theirs. Three deliberate
differences are noted under *Adaptations*.

## What this is NOT

⛔ **Not a place numbers live.** Every figure in an entry must appear **verbatim** in one of the
files the entry's `artifacts` list, or be `null`. A registry that restates numbers becomes a
fourth hand-maintained copy of them, and this project's rule is that two copies disagree the
moment one is updated. Enforced by `scripts/verification/check_experiment_registry.py`.

It is also not a replacement for the two surfaces that already exist and go deeper:

| surface | what it holds | why it stays |
|---|---|---|
| `memory/hypothesis-ledger.md` | open positions, the falsification **Method** pinned before the data lands, revisit triggers | this is where a hypothesis lives while it is *unanswered* |
| `docs/evidence/<date>-<name>/` | pre-registration, the analysis script, its committed output, figures | the actual evidence; entries here point at it and never duplicate it |

The registry answers a question neither of those can: **"across everything, what did we decide,
and what did it cost?"** — in one `grep`.

## Format

`registry.jsonl` — one JSON object per line, sorted by `id` ascending. UTF-8, no BOM.

```bash
tail -1 experiments/registry.jsonl | python3 -m json.tool
grep '"decision": "rejected"' experiments/registry.jsonl | python3 -m json.tool -
python3 -c "import json;print(sum(json.loads(l)['spend_usd'] or 0 for l in open('experiments/registry.jsonl')))"
python3 scripts/verification/check_experiment_registry.py      # schema + number traceability
```

## Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | `EXP-NNN`, zero-padded, monotonic, never reused |
| `date` | string | yes | ISO date the experiment was **concluded** |
| `title` | string | yes | One line, human-readable |
| `hypothesis` | string | yes | What was asked, and why it mattered |
| `subject` | string | yes | What was under test — a prompt, a corpus, a model, a script |
| `oracle` | string \| null | yes | Which judge produced the labels, or `null` if none |
| `branch` | string | yes | Where it landed |
| `commits` | array<string> | yes | 7-char hashes |
| `spend_usd` | number \| null | yes | **Oracle spend. `0` means zero calls and is a checkable claim.** |
| `population` | object | yes | What was measured over: rows, window, exclusions. `{}` if N/A |
| `metrics` | object | yes | Headline figures. ⛔ Each value must be greppable **verbatim** in an artifact, or `null` |
| `decision` | string | yes | `kept` · `parked` · `rejected` · `rolled_back` · `superseded` |
| `decision_rationale` | string | yes | 1–2 sentences |
| `artifacts` | array<string> | yes | Repo paths holding the evidence |
| `references` | array<string> | yes | Ledger ids, issues, ADRs, gotcha entries |
| `review` | string \| null | yes | Which review lenses ran, and what they found. `null` if none ran |
| `notes` | string | no | Caveats, confounds, environment |

### Decision values

`kept` in production or adopted · `parked` works, not adopted · `rejected` does not work ·
`rolled_back` was live, then reverted · `superseded` replaced by a later approach

## Adaptations from augur

1. **`spend_usd` added.** Augur's experiments are free; these are not, and every session record
   here states spend already. A `0` is a claim the reader can check.
2. **`features` / `hyperparameters` replaced by `subject` / `oracle` / `population`.** The axes
   that vary here are prompts, corpora and judges, not model hyperparameters.
3. **`review` added, and number-traceability is enforced rather than requested.** Augur's own
   `EXP-031` was an audit that found **19 registry numbers untraceable to any artifact**; its fix
   was to automate the check. Adopting the registry without that check would be adopting the
   defect and waiting for the audit.

## Adding an entry

1. Next id: `tail -1 registry.jsonl | python3 -c "import json,sys;print(json.loads(sys.stdin.read())['id'])"`
2. Append one line. Then **run the checker** — it validates the schema, the id order, that every
   artifact path exists, and that every metric is greppable.
3. Commit naming the experiment: `experiments: add EXP-006 <title>`.

⛔ **Entries are append-only.** To correct one, append a follow-up that references it. Editing in
place destroys the record that the earlier reading was ever believed — which is usually the most
useful thing in the file.
