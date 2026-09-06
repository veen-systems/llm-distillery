#!/usr/bin/env python3
"""Four claim-SHAPE checks over the evidence and decision records.

⛔ WHY THESE EXIST. On 2026-09-05 the whole mechanical battery — experiment
registry, both budget guards, `check_doc_claims.py`, 21/21 verify annotations,
667 unit tests — went green on `docs/evidence/2026-09-05-adr023-op-point-table/`
and caught **none** of the four defects a four-lens `/review-changes` then found
(`EXP-024`; `agent-ready-projects#127` for the upstream framing,
`agent-ready-projects#126` for what that review round cost: 557,442 tokens, 148
tool calls). Four of those five defects have a mechanical SHAPE, and this file is
that shape written down:

  (a) `no-difference-range`   a "no difference at all X" claim must publish the
                              range over which it COULD have differed
  (b) `zero-width-interval`   a published interval of [x, x] is a defect signal
                              (one exemption, printed not silent: a null control,
                              where zero width is what PASS looks like)
  (c) `ordering-needs-band`   a quantified comparative ordering needs a paired
                              band or p-value
  (d) `design-weights-read`   an analysis that reads a design-weighted population
                              and never reads the weights must say so out loud

⚠️ WHAT THIS IS NOT, and the limit is the same one `check_doc_claims.py` carries.
None of these checks knows whether a claim is TRUE. Each converts "nobody thought
to ask" into "the file has to answer" — which is the whole claim being made for
it, and is much less than review.

⚠️ AND THE HONEST PART: **mechanising this is not claimed to reduce the cost of a
future review round.** That is an expectation, and it is the thing to instrument
(`docs/TODO.md`). What is claimed is narrower: these four defect shapes were in
the tree, green, until a human-directed adversarial lens looked.

⭐ MEASURED LIMITS, from the four-lens review of THIS file (2026-09-05). Every one
was demonstrated, not argued, and none is fixed by the current design:

  1. **The prose checks ask whether SOME qualifier sits in the paragraph, never
     whether it is the qualifier for THIS sentence.** A markdown table with a
     `spread` column header satisfies (c) for an ordering row elsewhere in the
     table; an unrelated bullet saying "the 3 flips seen in August" satisfies (a)
     for a different bullet. Trigger is sentence-scoped, qualifier is
     paragraph-scoped, and the gap between them is real.
  2. **(d)'s trigger is a MENTION test while its exculpation is a USE test.** A
     script that reads the population through an argparse default built in
     another module is still invisible; a script that only names the path in a
     usage example is still a site. ⭐ **Narrowed 2026-09-05 after review**: the
     registry was two literal corpus paths, so five analyses reading
     `test.jsonl` — the 660 design-weighted rows every v8 number is computed on —
     were not sites at all. The three splits are registered now, and `CODE_ROOTS`
     covers `training/`, `ground_truth/` and the rest of `scripts/` rather than
     the three directories that happened to hold an offender that day.
  3. **A rewrap can move a claim out of a trigger.** Sentence-scoping (2026-09-05,
     after a review found exactly this: a fix rewrapped a line so the ordering
     verb and its two numbers no longer shared a physical line, and the site
     vanished rather than being qualified) makes this much harder, not
     impossible.
  4. **`_reads_field` false-FAILs on a field name held in a variable** — an
     imported constant, an attribute access (`df.inclusion_probability`), a
     concatenated key. That direction is safe: it demands a declaration for a
     script that is in fact correct, and the declaration is one line.

⭐ MUTATION RECORD, on the REAL tree — not on fixtures, because fixtures are where
a claim-shape check is easiest to fool. Re-run after each revision:

  M1 delete EXP-024 §4's reachability bound            -> no-difference-range KILLED
  M2 collapse a real `recall_band` to zero width       -> zero-width-interval KILLED
  M3 delete every band word in the checkpoint bullet   -> ordering-needs-band  KILLED
  M4 drop a `# design-weights:` declaration            -> design-weights-read  KILLED
  M5 repoint phase_c_outcome.py's ONLY weight read at
     a non-existent key, leaving the field's name in
     an error string and a JSON label                  -> design-weights-read  KILLED
  M6 add a [0.0, 0.0] interval to a registry row       -> zero-width-interval  KILLED
  M7 delete the weight join from a split-reading arm   -> design-weights-read  KILLED

⛔ **M5 SURVIVED in the first version of this file, and it is the most important
line here.** `_reads_field` then accepted any non-docstring string constant, so
deleting the only real read from `phase_c_outcome.py` still passed — while this
docstring claimed *mention is not use* was fixed and a unit test claimed to pin
it. The fix covered docstrings and comments and stopped there. `_reads_field` now
requires a subscript key or a direct call argument.

⚠️ TWO EARLIER MUTATIONS SURVIVED AND WERE CORRECT TO. Removing only the DASH
before EXP-024's bound left the bound in the paragraph; removing only "not
distinguishable" from the checkpoint bullet left "run variance" and "noise floor"
two bullets down. Both survivals are the check behaving correctly. They mark
limit 1 above, and they are why M1/M3 are stated as deleting the whole qualifier.

    python3 scripts/verification/check_claim_shapes.py
    python3 scripts/verification/check_claim_shapes.py --check zero-width-interval

Exit 0 when every selected check passes, 1 otherwise. ⛔ A check that examined NO
candidate site reports CANNOT VERIFY and exits 1, and each scan root is checked
SEPARATELY: a review demonstrated that removing three evidence directories took
(d) from 7 sites to 1 and still printed PASS, because the emptiness test was
aggregate. This repo's signature defect is a guard that reports success because it
looked at nothing, and a guard that looked at a tenth of something is the same
defect with better camouflage.
"""
import ast
import io
import json
import os
import re
import sys
import tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Scan roots, relative to ROOT. ⚠️ These are part of every check's meaning: a
# claim outside them is unchecked, and moving a directory silently narrows the
# instrument. Each is required to be non-empty (see `_walk`).
# ⛔ `filters` ADDED 2026-09-06, and the old comment below predicted exactly why.
# It read: *"`filters/` is deliberately NOT here (167 files): it is production
# scoring code ... If an analysis ever lands there, this list is wrong."* Phase 9
# landed `filters/human_thriving/v8/README.md` and `DEEP_ROOTS.md`, which publish
# rates over the 25.1x design-weighted test split, so the condition was met and the
# list was wrong. What widening bought, counted before and after: quantified
# orderings 5 -> 10 sites over 110 -> 273 files, intervals 115 -> 172 over 140 ->
# 494. It found 6 unbanded orderings (five of them pre-existing, two of which were
# cross-filter MAE rankings ADR-023 forbids) and 3 artifacts that were not valid
# UTF-8, one of them also truncated.
DOC_ROOTS = ("docs/evidence", "docs/decisions", "filters")
# ⛔ WIDENED 2026-09-05 AFTER REVIEW. The first three roots were the ones that
# happened to contain an offender on the day this was written, which is a
# hand-built population — this project's most reliable source of measurement
# error. An unweighted rate published from `training/`, `ground_truth/` or any
# other `scripts/` directory was unchecked. The added roots contribute 0 sites
# today; that is the point of adding them before one appears.
# ⚠️ `filters/` is deliberately NOT in CODE_ROOTS: it is production scoring code,
# which consumes an article and emits a score, and publishes no rate over a drawn
# population. (Its DOCS are a different matter — see DOC_ROOTS above, widened
# 2026-09-06.) If an analysis script ever lands under `filters/`, this list is wrong.
CODE_ROOTS = ("docs/evidence", "scripts/analysis", "scripts/diagnostics",
              "scripts/corpus", "scripts/gate", "scripts/calibration",
              "scripts/normalization", "training", "ground_truth")
# ⛔ `experiments/registry.jsonl` IS JSON-LINES AND WAS SILENTLY UNSCANNED. The
# first version put "experiments" in the JSON scan roots with an `endswith(".json")`
# filter — and `".jsonl".endswith((".json",))` is False, so the root contributed
# zero files and the `.jsonl` guard beneath it was unreachable dead code. The
# registry is where an experiment's headline numbers live; it is now read
# line-by-line, explicitly.
JSONL_FILES = ("experiments/registry.jsonl",)

# ─────────────────────────────────────────────────────────────────────────────
# (a) "no difference at all X" — the FORCED NEGATIVE shape.
#
# The instance: *"the gate buys nothing — B and C give identical TP at all eight
# k"*. B and C can only differ once a screened row outranks the k-th stage-2
# score; the smallest k at which that is possible is 140 and the grid stops at
# 60. The comparison could not have come out any other way, so the negative
# carried no information — the working rule *before believing a negative, prove
# the instrument could have said yes*, in its 21st recorded occurrence.
#
# TRIGGER = a sameness word quantified over a grid, WITHIN ONE SENTENCE.
# Deliberately narrow: a universal claim that is not about SAMENESS ("every one
# of the six dimensions is 0-2") is a property claim, not a no-difference claim,
# and firing on it would bury the check in noise until someone turned it off.
SAMENESS = (r"(?:identical|indistinguishable|no difference|no change|"
            r"zero difference|unchanged|exactly the same|makes no difference)")
# ⚠️ THE QUANTIFIER MUST NAME ITS GRID. `\b(?:at|across|for|in) (?:all|every|each)\b`
# alone matches the bare idiom — *"reaching for the prefix at all"* was reported as a
# no-difference claim — so a following word is required, and it may not be punctuation.
NO_DIFF_RE = re.compile(SAMENESS + r".{0,80}?\b(?:at|across|for|in|on) "
                        r"(?:all|every|each)\s+(?![,.;:!?)\u2014\u2013-])\S", re.I)

# What counts as publishing the range. Two families, because two honest answers
# exist: state the bound explicitly, or point at a configuration where the same
# comparison DID differ (the cross-box parity record does the latter — "0 flips
# at every threshold" is safe next to "the 3 flips at 4.5 were the library
# stack", which proves difference was reachable by this instrument).
REACHABILITY_RE = re.compile(
    r"could (?:not )?have (?:differed|come out|been|said)|smallest k\b|"
    r"range over which|would have (?:required|had to|needed)|forced\b|"
    r"carried no information|reachab|power to detect|detectab|"
    # "3 verdict flips" and "15 rows differ" both count; a leading 0 does not.
    r"\b[1-9]\d*(?:\s+[a-z]+){0,2}\s+flips?\b|\b[1-9]\d*(?:\s+[a-z]+){0,2}\s+rows? differ",
    re.I)

# (c) ordering + a paired band. TRIGGER = an ordering verb in the same SENTENCE
# as TWO metric-shaped numbers, i.e. an ordering that is quantified and therefore
# invites "by how much, and could it have been the other way?".
ORDERING_RE = re.compile(
    r"\b(?:beats|outperforms|out-performs|leads|wins|better than|worse than|"
    r"superior to|ranks above|would have picked|picks the wrong|dominates|"
    r"higher than|lower than)\b", re.I)
TWO_METRICS_RE = re.compile(r"\d+\.\d{2,}.*?\d+\.\d{2,}")
BAND_RE = re.compile(
    r"\bCIs?\b|confidence interval|±|\bp\s*=|\bP\s*=|p-value|bootstrap|"
    r"\bband\b|not distinguishable|indistinguishable|noise floor|"
    r"run variance|\bvariance\b|\bspread\b|overlap", re.I)

# Sentence split: whitespace after . ! ? — a decimal is safe because it is never
# followed by whitespace. ⚠️ A COLON IS NOT A SENTENCE END HERE. Splitting on it cut
# "AUC would have picked the wrong arm: 0.9035 vs 0.9021" into a verb with no numbers
# and numbers with no verb, so the check's own seeded true positive stopped firing.
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# (b) zero-width intervals in JSON. Two shapes are used in this repo: a
# two-element list under a `*_band` / `*_ci` key, and sibling low/high numbers.
# ⛔ `("min", "max")` WAS IN THIS LIST AND IS NOT AN INTERVAL SHAPE. It matched
# six score RANGES in `adr023_op_point_table.json`, two of which already read
# `min: 0.0`; a genuinely constant column would have been reported with the wrong
# diagnosis, and the six inflated the site count the liveness argument rests on.
INTERVAL_KEY_RE = re.compile(r"(?:^|_)(?:ci|band|interval)(?:_|$)", re.I)
LOW_HIGH = (("ci_low", "ci_high"), ("lo", "hi"), ("low", "high"),
            ("lower", "upper"))
# ⛔ THE ONE LEGITIMATE ZERO WIDTH, and it is the working rule *a failing check
# may be the CONTROL WORKING* pointed at this file. `adr023_op_point_table.py`
# runs an arm against ITSELF and REQUIRES [0,0]; a defect there would be a
# NON-zero width. The exemption matches the LEAF key only — as an ancestor match
# it silenced every interval nested under one badly-named parent, demonstrated in
# review — and it prints as a NOTE on every run, because a silent carve-out is
# how the next real [0,0] gets through.
NULL_CONTROL_RE = re.compile(r"null_control|null_arm|self_control", re.I)

# ⛔ THE SECOND LEGITIMATE ZERO WIDTH, and it is a DATA property, not a carve-out
# for a name. `ground_truth_gate.py` builds a metric's #95 band by flipping the
# rows that sit within the noise floor of the threshold — the ones it counts in
# `indeterminate_by_cell`. A metric whose confusion cells contain NO indeterminate
# row therefore has a band of exactly zero width, and that is the correct answer:
# nothing near the bar could move it. `belonging v1` is the live case (fp 0, tn 0
# → `specificity_band` a point, while `recall_band` is wide because tp 5 / fn 2).
# ⚠️ The exemption is checked against the SIBLING COUNTS in the same object, so a
# genuinely frozen instrument (indeterminate rows present, band still zero) still
# FAILS. It prints as a NOTE on every run — a silent carve-out is how the next
# real [0, 0] gets through.
BAND_CELLS = {
    "recall": ("tp", "fn"),
    "specificity": ("tn", "fp"),
    "precision": ("tp", "fp"),
    "f1": ("tp", "fp", "fn"),
}


def _saturated_band(parent, key):
    """(exempt, reason) for a zero-width `<metric>_band` given its own object."""
    if not isinstance(parent, dict) or not key.endswith("_band"):
        return False, ""
    cells = BAND_CELLS.get(key[:-len("_band")])
    if cells is None:
        return False, ""
    ind = parent.get("indeterminate_by_cell")
    if not isinstance(ind, dict):
        return False, ""
    missing = [c for c in cells if c not in ind]
    if missing:
        return False, ""
    if any(ind[c] for c in cells):
        return False, ""
    return True, ("no row in " + "/".join(cells) + " is within the noise floor "
                  "of the threshold, so this band could not have any width")

# markdown: `CI [x, y]`, `95% CI of (x, y)`, `confidence interval [x, y]`.
# ⚠️ Numbers are compared as FLOATS: a lexical test passed `CI [0.0, 0.00]`.
MD_CI_RE = re.compile(
    r"(?:\bCIs?\b|confidence interval)\s*(?:of|=|is|:)?\s*"
    r"[\[\(]\s*([+\-−]?\d+(?:\.\d+)?)\s*,\s*([+\-−]?\d+(?:\.\d+)?)\s*[\]\)]",
    re.I)
MD_NULL_CONTROL_RE = re.compile(r"null control|null arm|against itself", re.I)

# (d) The design-weighted populations, and the field that carries the weight.
# ⚠️ THIS IS A HAND-MAINTAINED REGISTRY, which is the thing this project keeps
# getting wrong — so it is not trusted on its own word: `check_design_weights`
# reads the DRAW MANIFEST and fails as CANNOT VERIFY if the manifest no longer
# describes a weighted design. The registry says WHICH file; the manifest says
# THAT it is weighted.
_HT_MANIFEST = "docs/evidence/2026-08-29-v8-corpus-draw/corpus_manifest.json"
DESIGN_WEIGHTED = {
    "datasets/scored/human_thriving_v8/corpus.jsonl": {
        "field": "inclusion_probability", "manifest": _HT_MANIFEST},
    # The same file, under the name it has on b650-gpu where the GPU-side
    # scripts run. A path alias is still the same population.
    "datasets/ht_v8_corpus.jsonl": {
        "field": "inclusion_probability", "manifest": _HT_MANIFEST},
    # ⛔ THE SPLITS ARE THE SAME DRAWN SAMPLE, AND THEY WERE INVISIBLE. Review
    # finding: the trigger matched two literal corpus paths, so five analyses
    # reading `test.jsonl` — the 660 design-weighted rows every v8 number is
    # computed on — were not sites at all. ⚠️ The weight does NOT live in the
    # split file; it lives in `corpus.jsonl`, so "reads the weights" here means
    # the script performs the join. That is exactly what `adr023_op_point_table.py`
    # and `phase_c_outcome.py` do, and what the others do not.
    "datasets/training/human_thriving_v8/test.jsonl": {
        "field": "inclusion_probability", "manifest": _HT_MANIFEST},
    "datasets/training/human_thriving_v8/val.jsonl": {
        "field": "inclusion_probability", "manifest": _HT_MANIFEST},
    "datasets/training/human_thriving_v8/train.jsonl": {
        "field": "inclusion_probability", "manifest": _HT_MANIFEST},
}
# The opt-out. ⛔ IT MUST BE A REAL COMMENT, found by `tokenize` — an unanchored
# regex over the file text exempted a declaration sitting inside a string literal
# and one buried mid-line in unrelated prose, and printed the garbage it captured
# as though it were a reason.
DECL_RE = re.compile(r"^#\s*design-weights:\s*(\S.*)")


def _reads_field(text, field):
    """Does this file USE `field` as a key, as opposed to mentioning it?

    ⛔ THIS WAS A SUBSTRING TEST, THEN AN ANY-STRING-CONSTANT TEST, AND BOTH
    PASSED THE WRONG FILE. The first `# design-weights:` declaration written
    under this check explained the gap by NAMING `inclusion_probability`, so the
    check read the confession as compliance. Excluding docstrings fixed that and
    not the general case: a review then deleted the ONLY real read from
    `phase_c_outcome.py` and the check still passed, because the field's name
    survived in an error message and a JSON label. *Mention is not use*, twice.

    A read is now one of three concrete shapes:
      * `obj["field"]`            — a Subscript with a constant string key
      * `obj.get("field", ...)`   — a constant string argument to any call
      * `getattr(obj, "field")`   — the same shape

    An f-string is a `JoinedStr`, not a `Constant`, so an interpolated error
    message no longer counts even when it is a call argument.

    ⚠️ DISCLOSED, and the direction is safe: a field name held in a variable
    (`from x import FIELD; r[FIELD]`) or read as an attribute (`df.field`)
    false-FAILs. That demands a one-line declaration from a correct script; the
    opposite error would pass a wrong one.

    Returns (reads, unparsed). ⛔ `unparsed` is a FAILURE, not a fallback: the
    first version fell back to the substring test, which re-opened the exact hole
    this function exists to close — a file with a syntax error and the field in a
    comment was exempted.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False, True

    def is_field(node):
        return (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and field in node.value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and is_field(node.slice):
            return True, False
        if isinstance(node, ast.Call):
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                if is_field(arg):
                    return True, False
    return False, False


def _declaration(text):
    """The `# design-weights:` opt-out, as a real comment, with its whole reason.

    Two review findings, both demonstrated: the regex was unanchored and file-wide
    (a match inside a string literal exempted the file), and the printed reason
    was truncated at the first newline and again at 120 chars — so the defence
    the docstring claimed, *the reason is printed on every passing run*, showed a
    mid-sentence fragment nobody could re-read.

    So: tokenize, take COMMENT tokens only, and when one opens a declaration
    absorb the contiguous comment lines that follow it as its continuation.
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    comments = [(t.start[0], t.string.strip()) for t in toks
                if t.type == tokenize.COMMENT]
    for idx, (lineno, body) in enumerate(comments):
        m = DECL_RE.match(body)
        if not m:
            continue
        parts, prev = [m.group(1).strip()], lineno
        for nline, nbody in comments[idx + 1:]:
            if nline != prev + 1 or DECL_RE.match(nbody):
                break
            parts.append(nbody.lstrip("#").strip())
            prev = nline
        return " ".join(p for p in parts if p)
    return None


def _walk(roots, exts):
    """Files under `roots` with one of `exts`, ROOT-relative, plus the per-root
    counts — a caller that cannot see an EMPTY root cannot tell a narrowed
    instrument from a clean one."""
    found, per_root = [], {}
    for rel in roots:
        base = os.path.join(ROOT, rel)
        here, seen = [], set()
        # ⚠️ `followlinks=True` because `os.walk`'s default silently contributes
        # ZERO files for a symlinked evidence directory — a narrowed instrument
        # with no signal, which is this file's whole subject. The realpath guard
        # is what keeps that from looping.
        for dirpath, dirnames, filenames in os.walk(base, followlinks=True):
            real = os.path.realpath(dirpath)
            if real in seen:
                dirnames[:] = []
                continue
            seen.add(real)
            dirnames[:] = [d for d in dirnames
                           if d not in ("__pycache__", ".ipynb_checkpoints")]
            for fn in filenames:
                if fn.endswith(exts):
                    here.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
        per_root[rel] = len(set(here))
        found.extend(here)
    return sorted(set(found)), per_root


class Undecodable(Exception):
    """A file this check cannot read as UTF-8.

    ⛔ IT USED TO BE `errors="replace"`, WHICH IS A SILENT WRONG ANSWER. `±` is a
    `BAND_RE` token; a latin-1 markdown file loses it to a replacement character
    and a properly-qualified ordering is reported as unqualified. A file the
    instrument cannot read is CANNOT VERIFY, never a FAIL and never a PASS.
    """


def _lines(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            return fh.read().split("\n")
    except UnicodeDecodeError as exc:
        raise Undecodable(f"{rel} is not valid UTF-8 ({exc}) — a lossy read here "
                          f"would drop band and reachability tokens silently") from exc


def _paragraphs(lines):
    """(start_line_1indexed, text) for each block of contiguous non-blank lines.

    ⛔ THE UNIT WAS ±6 LINES, THEN THE PARAGRAPH, AND THE STEP MATTERED. Under
    ±6 both prose mutations SURVIVED on the real tree: these documents are dense
    enough in caveat vocabulary that something always sat within six lines.
    Tightening to the paragraph killed both and immediately surfaced a real
    defect the ±6 version had passed.

    ⚠️ A markdown table, a bullet and its continuation, and a blockquote all read
    as ONE paragraph. That is the unit a caveat usually attaches to and is not
    the unit it always attaches to — see limit 1 in the module docstring.
    """
    out, buf, start = [], [], None
    for i, line in enumerate(lines, 1):
        if line.strip():
            if start is None:
                start = i
            buf.append(line)
        elif buf:
            out.append((start, "\n".join(buf)))
            buf, start = [], None
    if buf:
        out.append((start, "\n".join(buf)))
    return out


def _flat(para):
    """A paragraph with its line breaks removed.

    ⛔ THE QUALIFIER SEARCH MUST RUN ON THIS, NOT ON THE RAW PARAGRAPH. A clause
    reading "could not have\ncome out any other way" failed `REACHABILITY_RE`
    purely because the wrap fell between "have" and "come" — i.e. the check's
    verdict depended on where a text editor broke the line, which is the same
    defect as the per-line trigger it replaced.
    """
    return re.sub(r"\s+", " ", para).strip()


def _sentences(para):
    """Sentences of a paragraph, newlines flattened.

    ⛔ THE TRIGGER WAS PER-LINE UNTIL A REVIEW SHOWED A REWRAP ERASING A SITE.
    The first fix made under this check moved an ordering verb onto a different
    physical line from its two numbers; the site stopped existing rather than
    being qualified, which is this repo's signature defect committed by the fix
    for it.
    """
    units, buf = [], []

    def flush():
        if buf:
            units.append(" ".join(buf))
            del buf[:]

    for line in para.split("\n"):
        # ⛔ A LIST ITEM AND A TABLE ROW ARE THEIR OWN UNIT. Bullets carry no
        # terminal punctuation, so joining them made two adjacent bullets one
        # "sentence" and reported `- Val MAE 0.654 (8% better than v1)` /
        # `- Test MAE 0.717` as a single quantified ordering. It is two claims.
        if re.match(r"\s*(?:[-*+]\s|\d+[.)]\s|\|)", line):
            flush()
            units.append(line)
        else:
            buf.append(line)
    flush()
    out = []
    for unit in units:
        # ⚠️ Strip emphasis and code markers BEFORE splitting: `stable.**` put a
        # `*` between the period and the space, so the sentence never ended and
        # an ordering in one sentence borrowed the numbers from the next.
        flat = re.sub(r"[*`_]", "", re.sub(r"\s+", " ", unit)).strip()
        out.extend(x for x in SENTENCE_RE.split(flat) if x)
    return out


def _verdict(name, rc, out, sites, files, noun, roots, per_root):
    """Shared tail. ⛔ `sites == 0` and any EMPTY ROOT are CANNOT VERIFY, never
    PASS — see the module docstring."""
    empty = [r for r in roots if not per_root.get(r)]
    if empty:
        return 1, [f"CANNOT VERIFY {name}: scan root(s) {', '.join(empty)} "
                   f"contain no files of the type this check reads — the "
                   f"instrument is narrower than it looks, or the roots moved"]
    if files == 0:
        return 1, [f"CANNOT VERIFY {name}: scanned 0 files under "
                   f"{', '.join(roots)} — the scan roots moved"]
    if sites == 0:
        return 1, [f"CANNOT VERIFY {name}: read {files} files and found 0 {noun} "
                   f"to examine — the trigger pattern no longer matches anything, "
                   f"so a pass here would mean nothing"]
    if not rc:
        out.append(f"PASS {name}: {sites} {noun} examined over {files} files, "
                   f"all qualified")
    return rc, out


def check_no_difference_range():
    """A *no difference at all X* claim must publish the range over which it
    COULD have differed.

    ⚠️ DISCLOSED LIMIT. This checks that reachability language is PRESENT in the
    same paragraph, not that the bound is right or that it belongs to this
    comparison. A doc can satisfy it with the word "forced" and still be wrong.
    It stops the claim being published with nothing beside it at all, which is
    the state EXP-024 shipped in and which four green guards did not notice.
    """
    files, per_root = _walk(DOC_ROOTS, (".md",))
    out, rc, sites = [], 0, 0
    for rel in files:
        try:
            lines = _lines(rel)
        except Undecodable as exc:
            rc = 1
            out.append(f"CANNOT VERIFY no-difference-range: {exc}")
            continue
        for start, para in _paragraphs(lines):
            hits = [s for s in _sentences(para) if NO_DIFF_RE.search(s)]
            if not hits:
                continue
            sites += len(hits)
            if not REACHABILITY_RE.search(_flat(para)):
                rc = 1
                out.append(
                    f"FAIL no-difference-range: {rel}:{start} claims sameness "
                    f"over a grid and nothing in its paragraph publishes the "
                    f"range over which it could have differed — "
                    f"{hits[0][:110]!r}")
    return _verdict("no-difference-range", rc, out, sites, len(files),
                    "no-difference claim(s)", DOC_ROOTS, per_root)


def check_zero_width_interval():
    """A published interval of [x, x] is a defect signal.

    The instance: EXP-024's first paired bootstrap froze the top-k masks, so two
    arms with no discordant rows produced a 95% CI of exactly zero width, which
    was published as though it were a precise result. A zero-width interval is
    almost never a measurement — it is usually an instrument that could not vary.

    ⚠️ NOT "always", which the first version of this file asserted twice and then
    contradicted 130 lines lower with the null-control exemption. A saturated
    statistic can legitimately have zero width; the claim is that it needs
    saying, not that it is impossible.
    """
    jsons, per_root = _walk(DOC_ROOTS, (".json",))
    mds, md_roots = _walk(DOC_ROOTS, (".md",))
    for rel in jsons:
        pass
    out, rc, sites = [], 0, 0

    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def leaf(path):
        return path.rsplit(".", 1)[-1]

    def visit(obj, path, rel, parent=None, key=""):
        nonlocal rc, sites
        if isinstance(obj, dict):
            for a, b in LOW_HIGH:
                if a in obj and b in obj and num(obj[a]) and num(obj[b]):
                    sites += 1
                    if obj[a] == obj[b]:
                        if NULL_CONTROL_RE.search(leaf(path)):
                            out.append(
                                f"NOTE zero-width-interval: {rel} {path}.{a}/{b} = "
                                f"{obj[a]} — exempt as a declared null control, "
                                f"where zero width is the PASS condition")
                        else:
                            rc = 1
                            out.append(
                                f"FAIL zero-width-interval: {rel} {path}.{a}/{b} = "
                                f"{obj[a]} — a zero-width interval is an "
                                f"instrument that could not vary, not a result")
            for k, v in obj.items():
                visit(v, f"{path}.{k}", rel, parent=obj, key=k)
        elif isinstance(obj, list):
            key = key or leaf(path)
            if len(obj) == 2 and all(num(x) for x in obj) \
                    and INTERVAL_KEY_RE.search(key):
                sites += 1
                if obj[0] == obj[1]:
                    saturated, why = _saturated_band(parent, key)
                    if NULL_CONTROL_RE.search(key):
                        out.append(
                            f"NOTE zero-width-interval: {rel} {path} = {obj} — "
                            f"exempt as a declared null control, where zero width "
                            f"is the PASS condition")
                    elif saturated:
                        out.append(
                            f"NOTE zero-width-interval: {rel} {path} = {obj} — "
                            f"exempt as a SATURATED band: {why} "
                            f"(indeterminate_by_cell={parent['indeterminate_by_cell']})")
                    else:
                        rc = 1
                        out.append(
                            f"FAIL zero-width-interval: {rel} {path} = {obj} — "
                            f"a zero-width interval is an instrument that could "
                            f"not vary, not a result")
            for i, v in enumerate(obj):
                visit(v, f"{path}[{i}]", rel)   # elements have no band semantics

    n_files = 0
    for rel in jsons:
        n_files += 1
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                doc = json.load(fh)
        except (ValueError, OSError) as exc:
            rc = 1
            out.append(f"CANNOT VERIFY zero-width-interval: {rel} is not "
                       f"readable JSON ({exc}) — fix the file or narrow "
                       f"the scan, do not leave it unscanned")
            continue
        visit(doc, "", rel)

    # JSON-LINES artifacts, named explicitly — see JSONL_FILES.
    for rel in JSONL_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            rc = 1
            out.append(f"CANNOT VERIFY zero-width-interval: {rel} is named in "
                       f"JSONL_FILES and does not exist — the scan is narrower "
                       f"than it claims")
            continue
        n_files += 1
        with open(path, encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                except ValueError as exc:
                    rc = 1
                    out.append(f"CANNOT VERIFY zero-width-interval: {rel}:{ln} "
                               f"is not readable JSON ({exc})")
                    continue
                visit(doc, "", f"{rel}:{ln}")

    for rel in mds:
        n_files += 1
        try:
            md_lines = _lines(rel)
        except Undecodable as exc:
            rc = 1
            out.append(f"CANNOT VERIFY zero-width-interval: {exc}")
            continue
        for i, line in enumerate(md_lines):
            for lo, hi in MD_CI_RE.findall(line):
                sites += 1
                try:
                    same = float(lo.replace("−", "-")) == float(hi.replace("−", "-"))
                except ValueError:
                    continue
                if not same:
                    continue
                if MD_NULL_CONTROL_RE.search(line):
                    out.append(
                        f"NOTE zero-width-interval: {rel}:{i + 1} publishes "
                        f"CI [{lo}, {hi}] and names it a null control — exempt")
                else:
                    rc = 1
                    out.append(
                        f"FAIL zero-width-interval: {rel}:{i + 1} publishes "
                        f"CI [{lo}, {hi}] — zero width; the instrument "
                        f"could not vary")
    merged = {r: per_root.get(r, 0) + md_roots.get(r, 0) for r in DOC_ROOTS}
    return _verdict("zero-width-interval", rc, out, sites, n_files,
                    "interval(s)", DOC_ROOTS, merged)


def check_ordering_needs_band():
    """A quantified comparative ordering needs a paired band or a p-value.

    The instance: *"AUC would have picked the wrong arm"* was published as an
    ordering and was a coin flip — Δ = +0.0014, 95% CI [−0.0448, +0.0476],
    P = 0.523.

    ⚠️ DISCLOSED LIMIT. The band only has to be in the same paragraph; nothing
    here checks that it is the band FOR this comparison. A review demonstrated a
    table whose `spread` column header qualified an ordering in a different row.
    """
    files, per_root = _walk(DOC_ROOTS, (".md",))
    out, rc, sites = [], 0, 0
    for rel in files:
        try:
            lines = _lines(rel)
        except Undecodable as exc:
            rc = 1
            out.append(f"CANNOT VERIFY ordering-needs-band: {exc}")
            continue
        for start, para in _paragraphs(lines):
            hits = [s for s in _sentences(para)
                    if ORDERING_RE.search(s) and TWO_METRICS_RE.search(s)]
            if not hits:
                continue
            sites += len(hits)
            if not BAND_RE.search(_flat(para)):
                rc = 1
                out.append(
                    f"FAIL ordering-needs-band: {rel}:{start} orders two "
                    f"measured quantities with no band or p-value in its "
                    f"paragraph — {hits[0][:110]!r}")
    return _verdict("ordering-needs-band", rc, out, sites, len(files),
                    "quantified ordering(s)", DOC_ROOTS, per_root)


def check_design_weights():
    """If the population file carries design weights and the analysis never
    reads them, flag.

    The instance: the v8 test split is drawn under a 25.1× design and
    `corpus.jsonl` carries `inclusion_probability` for all 660 rows. EXP-024's
    first version used none, and the weighted arm does not say the same thing as
    the unweighted one (positive rate 5.3030% → 3.1638%).

    A script may opt out, but only in writing: a `# design-weights: <reason>`
    comment, whose text this check PRINTS in full on every passing run.

    ⚠️ DISCLOSED, from review: one declaration exempts EVERY registered
    population in that file, and a declaration can be contradicted by the file's
    own stdout. This check reads source, never output. It makes the omission
    visible; it does not adjudicate the reason.
    """
    out, rc, sites = [], 0, 0
    # The registry is not trusted on its own word — the draw manifest has to
    # still describe a weighted design.
    for pop, spec in DESIGN_WEIGHTED.items():
        mpath = os.path.join(ROOT, spec["manifest"])
        if not os.path.isfile(mpath):
            return 1, [f"CANNOT VERIFY design-weights-read: the draw manifest "
                       f"{spec['manifest']} for {pop} is missing — the "
                       f"registry's claim that this population is weighted is "
                       f"unbacked"]
        try:
            with open(mpath, encoding="utf-8") as fh:
                man = json.load(fh)
        except (ValueError, OSError) as exc:
            return 1, [f"CANNOT VERIFY design-weights-read: {spec['manifest']} "
                       f"unreadable ({exc})"]
        if not man.get("design_cells"):
            return 1, [f"CANNOT VERIFY design-weights-read: {spec['manifest']} "
                       f"no longer declares `design_cells`, so this check can no "
                       f"longer establish that {pop} is design-weighted"]

    files, per_root = _walk(CODE_ROOTS, (".py",))
    # ⛔ EMPTINESS IS CHECKED BEFORE ANYTHING ELSE. The stale-registry branch below
    # returns early, so an empty root reached it first and was reported as a stale
    # registry — a true CANNOT VERIFY with the wrong cause, which sends the reader to
    # the wrong file.
    empty = [r for r in CODE_ROOTS if not per_root.get(r)]
    if empty:
        return 1, [f"CANNOT VERIFY design-weights-read: scan root(s) "
                   f"{', '.join(empty)} contain no python files — the instrument is "
                   f"narrower than it looks, or the roots moved"]
    for rel in files:
        try:
            text = "\n".join(_lines(rel))
        except Undecodable as exc:
            rc = 1
            out.append(f"CANNOT VERIFY design-weights-read: {exc}")
            continue
        for pop, spec in DESIGN_WEIGHTED.items():
            if pop not in text:
                continue
            sites += 1
            uses, unparsed = _reads_field(text, spec["field"])
            if unparsed:
                rc = 1
                out.append(f"CANNOT VERIFY design-weights-read: {rel} does not "
                           f"parse as python, so whether it READS "
                           f"`{spec['field']}` cannot be established — fix the "
                           f"file; a substring fallback here is the hole this "
                           f"check was written to close")
                continue
            if uses:
                continue
            decl = _declaration(text)
            if decl:
                out.append(f"NOTE design-weights-read: {rel} reads {pop} "
                           f"unweighted, declared: {decl}")
                continue
            rc = 1
            out.append(
                f"FAIL design-weights-read: {rel} reads {pop}, which carries "
                f"`{spec['field']}` under a stratified draw, and never reads the "
                f"weights — every rate it publishes describes the sample, "
                f"not the population. Read the weights, or declare "
                f"`# design-weights: <why not>`")
    if files and sites == 0:
        return 1, [f"CANNOT VERIFY design-weights-read: read {len(files)} python "
                   f"files and none references any registered design-weighted "
                   f"population — the paths in DESIGN_WEIGHTED are stale"]
    return _verdict("design-weights-read", rc, out, sites, len(files),
                    "read(s) of a weighted population", CODE_ROOTS, per_root)


CHECKS = {
    "no-difference-range": check_no_difference_range,
    "zero-width-interval": check_zero_width_interval,
    "ordering-needs-band": check_ordering_needs_band,
    "design-weights-read": check_design_weights,
}


def main(argv=None):
    """`argv` is a PARAMETER, not `sys.argv` — an imported caller (the
    tests) would otherwise be handed pytest's arguments. Same defect as
    `check_index_budget.py` shipped for ten minutes on 2026-08-26."""
    if argv is None:
        argv = []
    names = list(CHECKS)
    if argv:
        if argv[0] == "--check" and len(argv) > 1:
            sel = argv[1]
        elif argv[0].startswith("--check="):
            sel = argv[0].split("=", 1)[1]
        else:
            print(f"CANNOT VERIFY: unknown argument {argv[0]!r}; expected "
                  f"--check {'|'.join(list(CHECKS) + ['all'])}")
            return 1
        if sel != "all":
            if sel not in CHECKS:
                print(f"CANNOT VERIFY: unknown check {sel!r}; expected one of "
                      f"{', '.join(list(CHECKS) + ['all'])}")
                return 1
            names = [sel]

    rc, lines = 0, []
    for name in names:
        code, out = CHECKS[name]()
        rc = rc or code
        lines.extend(out)
    # Failures first, summary last — `run_verify_annotations.py` anchors on
    # a line-initial FAIL/CANNOT VERIFY and reports the LAST line otherwise.
    lines.sort(key=lambda l: 0 if l.startswith(("FAIL", "CANNOT VERIFY")) else 1)
    bad = sum(1 for l in lines if l.startswith(("FAIL", "CANNOT VERIFY")))
    for l in lines:
        print(l)
    verdict = "FAIL" if bad else "PASS"
    print(f"{verdict} {len(lines) - bad}/{len(lines)} claim-shape checks clean, "
          f"over {len(names)} check(s): {', '.join(names)}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
