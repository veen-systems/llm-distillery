---
name: review-changes
description: Diff-driven pre-commit review — picks review lenses based on what changed, from single-pass adversarial to full multi-model battery
disable-model-invocation: false
---

Pre-commit review of pending changes. Scope and depth are driven by what changed,
not a fixed checklist.

Adapted from agent-ready-projects v1.12.0, **re-mapped rather than copied**. The
framework template's tiers key on its own paths (`templates/*`, `docs/GUIDE.md`,
`tests/lint/*`), none of which exist here; installed verbatim, every change in
this repo would fall through to LOW and the skill would quietly do nothing —
which is this repo's own signature defect (NM#284, LD#94, NM#281). Tiers below
key on what llm-distillery actually ships.

**This file is deliberately PROJECT-LOCAL.** Until 2026-08-06 a
`~/.claude/skills/review-changes` symlink pointed at the *personal notes* repo and
**won over this file** — `/review-changes` here ran a checklist tiered on
`Nieuw huis/` and `modellen/*.py`. The symlink is gone; if a global of this name
ever reappears, this adaptation is silently shadowed again. Check the "Base
directory" line the invocation prints. See `memory/gotcha-log.md` (2026-08-06).

Four items were ported on 2026-08-06 from that divergent copy before its symlink
was removed, and from a parallel harvest in ovr.news: the untracked-file scan, two
adversarial questions, the re-derive-every-number rule, and the read-the-whole-
section rule.

## Step 1 — Diff and classify

**First resolve a baseline.** A branch that is committed AND pushed has an empty
`git diff`, an empty `--cached`, and an empty `@{u}` — the last one *precisely
because* the upstream exists and is current. Taken literally that reports
"nothing to review" on a whole open PR, which is the commonest state in which
anyone wants a pre-merge review. (Ported ahead of release from
agent-ready-projects `e824212`, on the unmerged branch `fix/review-changes-scope`
— **there is no v1.26.1**; latest upstream release is v1.26.0, confirmed
2026-08-15. An adopter hit this on a real PR where a widened review found
**4 blockers**.
This session hit the same defect on 2026-08-13 and worked around it by hand
without recognising it — the workaround is what the fix now prescribes.)

```bash
BASE=""
for c in origin/HEAD origin/main origin/master main master; do
  if git rev-parse --verify -q "$c" >/dev/null; then BASE=$(git rev-parse --abbrev-ref "$c" 2>/dev/null || echo "$c"); break; fi
done
# On the default branch itself, HEAD...HEAD is empty — fall back to the upstream.
if [ -n "$BASE" ] && [ "$(git rev-parse --verify -q HEAD)" = "$(git rev-parse --verify -q "$BASE")" ]; then
  BASE=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
fi
[ -n "$BASE" ] || echo "SCOPE NOT ESTABLISHED — no baseline resolved; do NOT report a clean diff"
echo "baseline: ${BASE:-<none>}"
```

`origin/HEAD` is unset in many clones, so the loop is load-bearing rather than
defensive. If none resolves, say the scope could not be established — never
report a clean diff.

Then run `git diff --stat`, `git diff --cached --stat`, `git diff --stat "${BASE:?}"...HEAD`,
**and `git status -s` for untracked files**. Untracked files show in no diff, and they are usually brand-new
code rather than an edit to already-reviewed code — so they are the *highest*-risk
part of a change, not the lowest. A new `scripts/diagnostics/*.py` or a new
`filters/*/v*/` package is exactly what a diff-only scan walks past.

Classify each changed file:

| Tier | File patterns | Depth |
|------|-------------|-------|
| **HIGH** | `filters/common/*.py` · `filters/*/v*/config.yaml` · `filters/*/v*/{calibration,normalization,ground_truth_gate}.json` · `filters/*/v*/prefilter.py` · `filters/*/v*/base_scorer.py` · `ground_truth/batch_scorer.py` · `scripts/{gate,normalization,calibration,deployment}/*` · `tests/unit/test_normalization_invariant.py` · `.githooks/*` | Full battery (4–5 lenses) |
| **MEDIUM** | `CLAUDE.md` · `ground_truth/*` · `training/*` · `scripts/**` (other) · `tests/**` · `docs/adr/**` · `docs/FILTER_PLAYBOOK.md` · `docs/NORMALIZATION_METHOD.md` · `docs/RUNBOOK.md` · `docs/ARCHITECTURE.md` · **anything matching no tier** | Adversarial + doc-accuracy (+ claim-verification if numbers changed) |
| **LOW** | `memory/*` · `docs/TODO.md` · `docs/ROADMAP.md` · session files | Adversarial (+ claim-verification if numbers changed) |

Pick the **highest** tier that applies. **Unmatched files are MEDIUM, not LOW** —
silence must never read as safe. **Name every unmatched file in the report under
"Unclassified", even when a HIGH file in the same diff makes the tier moot.** The
naming is the point: an unrecognized path is usually new shipped content whose
tier nobody has decided yet, and it keeps arriving un-triaged until someone adds a
row. Do not silently drop it, and do not default it to LOW. **If it is executable
or is copied into NexusMind, escalate it to HIGH rather than leaving it at
MEDIUM** — MEDIUM omits the guarantee-preservation and sync-safety lenses, which
are exactly the two that shipped filter content needs.

`filters/common/*.py` is HIGH regardless of how small the diff looks: it is pure
shared math synced verbatim into NexusMind, and `.nexusmind-owns` is empty, so a
mistake here reaches production scoring on the next deploy.

**Every file named in the guarantee-preservation lens must sit in the HIGH row.**
That lens is HIGH-gated, so a guarantee defined for a file that tiers lower can
*never* be checked, and the report renders it as a clean pass. This is why
`tests/unit/test_normalization_invariant.py` is listed in HIGH rather than falling
under `tests/**`: it is the pin the normalization guarantee names, both NM#161 and
NM#205 were that pin's subject, and a change weakening the pin itself would
otherwise tier MEDIUM and skip the lens that exists to catch it. Re-check this
invariant whenever either the tier table or the lens changes.

If no files changed, report "nothing to review" and stop.

## Step 1.5 — Structural pre-check

Runs at **every tier and every magnitude**, before any lens, on every changed
markdown file. It is deterministic, costs nothing, and needs no model to
evaluate — which is why it is a step and not a lens.

Every lens below reads *content*. None asks whether the file is still **valid
markdown** after the edit. That gap matters disproportionately here, because this
repo's memory and docs layer is predominantly wide tables — the filter table, the
lens→tab mapping, the occurrence catalogue — where a row is one very long line. A
`|` added inside a cell (a regex like `'recordfail|initrdfail'`, an `||` in a
shell fragment, an alternation in a note) pushes cells past the end of the table
and **GFM drops the excess silently**. It reads fine as prose in the diff and is
wrong only when rendered, so a human reviewer and the adversarial lens both pass
it.

```bash
{ git -c core.quotePath=false diff --name-only
  git -c core.quotePath=false diff --cached --name-only
  git -c core.quotePath=false diff --name-only "${BASE:?baseline unresolved - see Step 1}"...HEAD 2>/dev/null
  git -c core.quotePath=false ls-files --others --exclude-standard; } |
  sort -u | grep '\.md$' | while IFS= read -r f; do
  [ -f "$f" ] || continue
  awk -v F="$f" '
    # `$(0)`, never a bare dollar-zero: skill ARGUMENTS are substituted into the
    # skill BODY, so a bare one arrives as the FIRST ARGUMENT WORD and this program
    # then examines a constant instead of the record — silently, printing exactly
    # what a clean run prints. Upstream #77 (agent-ready-projects v1.27.0).
    # This copy is RE-MAPPED: patch it surgically, never re-copy — upstream #94.
    function cells(s,   t, n) {
      t = s; gsub(/\\\|/, "", t)
      sub(/^[ \t]+/, "", t); sub(/[ \t]+$/, "", t)
      sub(/^\|/, "", t); sub(/\|$/, "", t)
      n = gsub(/\|/, "|", t); return n + 1
    }
    function isdelim(s,   t) {
      t = s; gsub(/\\\|/, "", t); gsub(/[ \t]/, "", t)
      return (t ~ /-/ && t ~ /^[|:-]+$/)
    }
    { sub(/\r$/, "") }               # CRLF: strip before anything reads the line,
                                     # or isdelim() never matches and no table in
                                     # the file is examined. See #52 (framework).
    {
      bare = $(0); sub(/^ ? ? ?/, "", bare)
      if (bare ~ /^```/ || bare ~ /^~~~/) {
        c = substr(bare, 1, 1); n = 0
        while (substr(bare, n + 1, 1) == c) n++
        if (fch == "") { if (n >= 3) { fch = c; flen = n } }
        else if (c == fch && n >= flen) fch = ""
        intbl = 0; prev = ""; next
      }
      if (fch != "") next
      if (isdelim($(0)) && prev != "" && (index($(0), "|") || index(prev, "|"))) {
        base = cells($(0)); intbl = 1
        if (cells(prev) != base)
          printf "%s:%d: header has %d cells, delimiter row defines %d — not a valid table\n", F, NR-1, cells(prev), base
        prev = $(0); next
      }
      if (intbl) {
        if ($(0) ~ /^[ \t]*$/) intbl = 0
        else if (index($(0), "|") && cells($(0)) > base)
          printf "%s:%d: row has %d cells, table defines %d — the excess is dropped when rendered\n", F, NR, cells($(0)), base
      }
      prev = $(0)
    }
    END { if (fch != "") printf "%s: unclosed %s code fence\n", F, fch }
  ' "$f"
done
```

The file list is the union of unstaged, staged, unpushed, and **untracked** —
`git diff` in any form never lists a file git has not seen, and a brand-new
document is where fresh corruption is likeliest. `core.quotePath=false` is
load-bearing: git otherwise renders a non-ASCII path as `"caf\303\251.md"`, which
does not end in `.md`, so the file drops out of both the check and the count with
no error.

Only the **lossy** direction is reported. A row with *fewer* cells than the header
is spec-legal in GFM — empty cells are inserted, and a `| **PART ONE** |` divider
row inside a wide table is idiomatic — so flagging it produces noise, not
findings. Report the count of files in scope (not files edited) in Step 4, so a
check that scanned nothing is distinguishable from one that found nothing.

Fix real hits before committing: escape the offending pipe as `\|`, or restructure
the row. **A hit is worth opening — it is not yet proof of loss.** When this was
first run over this repo it found a caveat in
`memory/cross-repo-prioritization.md` that renders nowhere, which is the case it
exists for. But two classes report without losing anything, both reproduced
against *this* copy of the check on 2026-08-15: excess cells that are **empty**
(`| 1 | 2 | |` against a two-column delimiter reports and discards nothing), and
lines that are **not a table at all** — `isdelim()` accepts a bare `---`, and its
guard is satisfied by a pipe in the *previous* line, so YAML frontmatter closing
after a piped `description:` and a spaced `- - -` break each report. (Upstream
also lists setext headings; that one did **not** reproduce here — the guard needs
a pipe the fixture lacked.) Look before you edit.

**Known blind spots, so a clean result is not read as more than it is**: tables
inside blockquotes are not examined, nor is a table whose delimiter row is itself
missing. This finds lossy rows in well-formed tables; it is not a markdown
validator. **CRLF was one of these until the `sub(/\r$/, "")` rule above** —
`isdelim()` strips spaces and tabs but not `\r`, so on a CRLF checkout no table
was entered and a file whose defect was in a table printed exactly what a clean
file prints. Only the fence check survived, anchored at line start where a
trailing `\r` cannot reach. `core.autocrlf=true` — the Git-for-Windows installer
default, and this repo is driven from Git Bash (`docs/RUNBOOK.md`, and the
`MSYS_NO_PATHCONV=1` in CLAUDE.md's normalization command) — is what puts CRLF in
the working tree. **Lone CR is still a blind spot** and a worse-behaved one: awk
sees the whole file as one record, so no table is examined and the fence check
misreports — a lone-CR file whose fence is correctly *closed* is reported as
unclosed.

## Step 2 — Execute review lenses

Spawn a subagent per lens, concurrently. (Running them inline is acceptable if
subagents are unavailable; the lens prompts are unchanged either way.)

### Lens: guarantee-preservation (HIGH only)

```
You are reviewing changes to surfaces that carry hard invariants in
llm-distillery. For each changed file, check the guarantees it carries:

- filters/common/model_loading.py: load_base_model_for_seq_cls() stays the only
  entry point. AutoModelForSequenceClassification must NEVER be used directly —
  Gemma-3-1B's gemma3_text config is not in the Auto mapping.
- PEFT adapters: OLD key format only (.lora_A.weight / score.weight, NOT
  .lora_A.default.weight). resave_adapter.py must never run before Hub upload —
  it breaks PeftModel.from_pretrained().
- filters/common/filter_base_scorer.py: _apply_short_content_cap is the ONE
  place the #93 short-content rule is decided, reading the stamp on `result`,
  not the article. A second inline copy is the ADR-022 second-drop-point defect.
- No apply_filter() on a SCORING path may check content length (#93). The floor
  is labelling-time only, in ground_truth.batch_scorer.make_oracle_prefilter.
  Adding check_content_length to a prefilter re-creates what #93 removed.
  (validate_article rejecting EMPTY content is separate and legitimate.)
- ADR-022 "stamp always, decide once": gate modules stamp score+flag+model
  version unconditionally; exactly ONE config-gated drop point per concern;
  every enforcement decision is a config flip, never a code revert.
- ADR-001/016: the oracle outputs dimensional scores (0-10) only, never tiers or
  stages. Changing a threshold must never require re-labelling.
- Normalization (ADR-014, docs/NORMALIZATION_METHOD.md): fit at
  `raw >= the filter's tier threshold`. Pinned by
  tests/unit/test_normalization_invariant.py. Both #161 and #205 were raw_min
  drifting off that threshold.
- calibration.json is refit after every training run and committed with the
  filter package.
- ADR-004: commerce is the only universal prefilter.

For each guarantee touched: does the change preserve it? Flag any weakening.
Then ask: is the change broader than its stated intent?

Report: GUARANTEE OK or GUARANTEE WEAKENED per surface.
```

### Lens: reachability (HIGH and MEDIUM — this repo's signature defect)

```
This repo's recurring failure is a mechanism that is present, configured, and
CANNOT FIRE. Four instances: per-filter prefilters never ran in production for
six months (NM#284); solutions v6's concreteness_gatekeeper binds 0 times in
191,616 articles (LD#94); a violence gate wired so it could never fire (NM#281);
a shadow loader arming a dead branch.

For every gate, cap, threshold, flag or config key touched:
1. Trace the CALL PATH. Is it reached in the production scoring path, the
   oracle/labelling path, both, or neither? Name the caller.
2. Does its INPUT exist at that point in the flow? (The GPU scorer reconstructs
   an Article of {title, content} only — rules reading url/source/source_type/
   description are inert in-path.)
3. Could the condition ever be true on real data? If it declares a rate or
   threshold, what does production actually show?
4. If it is a config key: does any runtime code read it, or does it only LOOK
   like an enforcement point?

Do NOT infer runtime behaviour from the presence of a config key. Do NOT check
prefilter state from data/filtered/*/filtered_*.jsonl — that file is 100%
passers by construction AND drops source-type-excluded rows.

Report: REACHABLE (with the call path) or UNREACHABLE/INERT (with why).
```

### Lens: claim-verification (any tier, when the diff asserts measured numbers)

```
You are checking measured claims added or changed in this diff — in docs,
memory files, ADRs, issue text or commit messages.

For each numeric or empirical claim:
1. Is it labelled MEASURED, or is it an inference presented as measurement?
   This repo's stated failure mode is a confident claim nobody verified.
2. Is the denominator stated, and is the source's EXCLUSIONS established?
   (filtered_*.jsonl = passers only + source-type drops; data/raw/ is
   pre-enrichment.)
3. If it is a difference near an operating point: is it above the #95 noise
   floor? A run-to-run delta below ~0.1 near an op-point is indistinguishable
   from batch-composition noise (measured |delta| <= 0.16) and must NOT be
   reported as an effect. Scores from different machines must never be compared
   (cross-box skew |0.16|).
4. If it is a difference-of-differences or similar comparison, does it carry:
   a permutation (or cluster-aware) test, multiplicity correction, source
   clustering, AND an explicit statement of whether selection into the sample
   depends on the quantity being compared?
5. Does the claim carry a verification command, so it can decay loudly?
6. **Re-derive every number from the tool that produced it — never carry one
   across from adjacent prose, including prose already committed here.** On
   2026-08-06 a review found `GPTBot 401 domains` published in a public ADR and
   two other files: it exceeded the 333 total stated four lines above it, and was
   a count of matching *lines*, not domains. A figure that is a subset of a stated
   total must be checked against that total before it ships.

Report: CLAIM SUPPORTED or CLAIM UNSUPPORTED, naming the missing evidence.
```

### Lens: adversarial (all tiers)

```
You are an adversarial reviewer. Refute the changes — find what breaks, what
edge cases fail, what assumptions do not hold.

For each changed file:
1. What is the change trying to accomplish?
2. What could go wrong? Find at least one concrete failure scenario.
3. Are there SILENT failure modes — things that pass but are wrong?
4. If this is a test change: what real failure does the weaker test now pass?
5. If this touches filters/common/: what breaks in NexusMind on the next sync?
6. If this touches a skill, agent, template or ADR: what would a future session
   break by following the new version? These are read by someone who was not here.
7. If this writes a field consumed downstream (a score, a flag, a label, a tier):
   could it be confidently WRONG rather than merely absent? A wrong score that
   looks plausible outranks a missing one — see LD#91, ovr#296.
8. If this touches a threshold, weight or op-point: what is the recall cost, and
   was it measured or assumed?

Default stance: refuted=true. Mark NOT REFUTED only after a thorough attempt.

**A claim that needs a measurement gets one, gets hedged, or is not ready.**
Two shapes need one. They are the same failure from two sides:

- **Negatives.** "0 rows", "never called", "nothing reads it", "no other
  callers", "all clean" — a negative cannot tell a real absence from a broken
  instrument, an empty sample or the wrong population. Report the claim, the
  command that produced it, and **what a non-empty result would have looked
  like**. If you cannot state the shape of a positive, the claim is not ready.
  Where a negative *licenses a loosening* — "no false positives", "nothing was
  affected" — seed a positive first: a run that finds nothing cannot tell a
  fixed check from a disabled one.
- **Absolutes in descriptions.** *every, all, always, never, none, zero, cannot,
  impossible, no … can, guaranteed* — in a claim about how something
  **behaves**. An absolute in an *instruction* is a decision and is fine
  ("never edit the NexusMind copy" prescribes). An absolute in a *description*
  is a measurement, and it ships unmeasured by default. Each needs a measurement
  with its scope, a citation, or a hedge — or it is not ready.

**Name the population, not just the number.** The absolute that cost most here
was scoped to one fetcher and stated of a URL scheme; it propagated into another
repo as a premise and nearly retired working code. "35,229 of 35,229" was right;
"so no fetcher change moves it" was the unmeasured half.

This is the sentence to write, not a step to perform — a separate "verify your
claims" step is skippable in exactly the cases where it matters. In this repo the
failure has a name and a catalogue: `filtered_*.jsonl` is 100% passers by
construction, `data/raw/` is pre-enrichment, a host is a source with an exclusion
list too, and `docs/adr/` exists in more than one repo. Every one produced a
clean-looking negative. **Every one was a hand-built population** — prefer one
the pipeline already computes.

**A claim whose measurement cannot be taken yet is a finding in its own right.**
Report it as one, at the moment you make it — not in the write-up afterwards,
which is where it gets reconstructed from memory. Do not register it here: this
lens reports, it does not write, and a hypothesis needs a Method and a Revisit
trigger a diff reviewer is not placed to supply. The home is the relevant
`memory/*-hypotheses.md` topic file, written during `/curate`.

Report: REFUTED (with failure scenario) or NOT REFUTED. Every negative carries
its command and the shape of a positive; every absolute about behaviour carries
its measurement, its citation, or its hedge.
```

### Lens: doc-accuracy (MEDIUM and HIGH)

```
Review documentation changes for accuracy against disk state.

1. **Re-read the whole section, not the diff.** The diff shows what changed and
   never what the change contradicted. On 2026-08-06 three of four blockers were
   stale sentences sitting a few paragraphs from correct new text, inside files
   the same commit had edited.
2. Does every file path mentioned actually exist? (Filter versions are removed
   over time — sustainability_technology v3 and foresight v1 are gone.)
3. Does every command use correct flags and syntax? Do the PYTHONPATH= and
   MSYS_NO_PATHCONV= prefixes match the documented ones?
4. Do version numbers, MAE figures, dates and issue references match what is
   actually shipped? Cross-check the CLAUDE.md filter table against
   filters/*/v*/ on disk.
5. Is an issue number expanded on first use, per CLAUDE.md "How To Write
   Answers Here"?
6. Internal inconsistencies between two places in the same doc set?

Report: ACCURATE or INACCURATE, with the specific mismatch.
```

### Lens: sync-safety (HIGH only, when filters/common/ or a deployed filter changed)

```
This change may propagate to NexusMind via deploy_to_nexusmind.sh, which
OVERWRITES and whose .nexusmind-owns manifest is EMPTY — so any drift on the
NexusMind side is deleted silently. That has nearly cost three production source
blocks, and investment_risk v6 carried arxiv/mastodon_/bluesky blocks in
NexusMind that never existed upstream.

1. Does the NexusMind copy of each changed file differ today? Diff before
   concluding.
2. Would a blind LD -> NM copy DELETE anything NexusMind added? If so, port it
   back to llm-distillery first rather than overwriting.
3. Is the change pure shared math (safe to sync) or does it encode a
   production-runtime concern that belongs in NexusMind's production_scorer.py?

Report: SYNC SAFE or SYNC WOULD DROP <files/blocks>.
```

## Step 3 — Synthesize

Combine all lens reports. For each finding:
- **Severity**: BLOCKER (fix before commit) / WARNING (should fix) / NOTE (consider)
- **Lens**, **File**, **Finding**, **Fix**

An UNREACHABLE verdict on a newly-added gate is a BLOCKER, not a NOTE — shipping
an inert enforcement point is how NM#284 and LD#94 happened.

## Step 4 — Report

```
## Review: [N] files changed, [tier] risk, [M] lenses

### Findings

| # | Severity | Lens | File | Finding |
|---|----------|------|------|---------|
| 1 | BLOCKER | reachability | ... | ... |

### Unclassified

[Files matching no tier row, or "none". NEVER omit this section.]

### Summary

- **Structural pre-check**: [N] markdown files in scope, [M] violations
- **Lenses run**: [list]
- **Blockers**: [N] · **Warnings**: [N] · **Notes**: [N]
- **Verdict**: [READY TO COMMIT | FIX BLOCKERS FIRST | REVIEW WARNINGS]
```

**Never omit the Unclassified section.** An empty one is evidence the check ran; a
missing one is indistinguishable from a check that was skipped — which is the
failure class the rule exists to prevent. Same reasoning for the structural
pre-check count line.

Report findings faithfully: if a lens found nothing, say so; do not pad. If a
lens could not run (missing data, unreachable host), say that rather than
letting its silence read as a pass.
