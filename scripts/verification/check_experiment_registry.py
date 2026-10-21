"""Validate experiments/registry.jsonl: schema, id order, artifact existence, and -- the point
of the file -- that every number an entry states is TRACEABLE to an artifact it cites.

⛔ Why the traceability check exists rather than a "please keep numbers in sync" note: augur's
own EXP-031 was an audit that found 19 registry numbers untraceable to any artifact. A registry
whose numbers drift is worse than no registry, because it reads authoritative.

A metric value passes if its string form appears VERBATIM, as a token of its own (dates and times removed
first; #171/#175), in at least one git-TRACKED cited artifact (or in the commit message of a cited commit). `null` always passes -- an unrecoverable number should be
null with an explanation in `notes`, never invented.

Exit 0 = all checks pass. Exit 1 = at least one FAIL.

Optional `lab`: a list of lab paths (relative to ~/lab/llm-distillery on situla) holding the run's data --
each must sit under `experiments/` or `datasets/` (never `inbox/`, whose items have no home yet)
and, where a lab root exists, must exist. Without a lab root only the shape is checked, and the
output says so (`lab paths ... SKIPPED`).

`--registry PATH` checks another file (tests plant defects in a temp copy, never in the tracked
one -- llm-distillery#162). Artifact paths and commits still resolve against the repo.
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG = REPO / "experiments" / "registry.jsonl"
REQUIRED = ["id", "date", "title", "hypothesis", "subject", "oracle", "branch", "commits",
            "spend_usd", "population", "metrics", "decision", "decision_rationale",
            "artifacts", "references", "review"]
DECISIONS = {"kept", "parked", "rejected", "rolled_back", "superseded"}
ID_RE = re.compile(r"^EXP-\d{3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LAB_RE = re.compile(r"^(experiments|datasets)/[^/]")


TEXT_SUFFIXES = (".md", ".txt", ".json", ".py", ".jsonl", ".csv", ".tsv")


def tracked(a):
    """The git-tracked files an artifact path names: itself, or (a folder) every tracked file under it. #171/#175:
    `exists()` passed a gitignored file on the one machine that had it."""
    r = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--", a], capture_output=True, text=True)
    return sorted(x for x in r.stdout.split("\0") if x) if r.returncode == 0 else []


def artifact_text(entry, cache={}):
    """Every byte the entry points at: the TRACKED artifact files, plus the commit messages."""
    key = tuple(entry["artifacts"]) + tuple(entry["commits"])
    if key in cache:
        return cache[key]
    blobs = []
    for a in entry["artifacts"]:
        for f in tracked(a):
            fp = REPO / f
            if fp.suffix in TEXT_SUFFIXES and fp.is_file() and not fp.is_symlink():
                blobs.append(fp.read_text(encoding="utf-8", errors="replace"))
    for c in entry["commits"]:
        r = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%B", c],
                           capture_output=True, text=True)
        if r.returncode == 0:
            blobs.append(r.stdout)
    cache[key] = "\n".join(blobs)
    return cache[key]


def traceable(value, text):
    """A number is traceable if its string form is in the cited evidence. Tries the value as
    written and, for floats, a couple of equivalent renderings -- but NEVER a re-derived one:
    the entry must quote what the artifact says."""
    if value is None:
        return True, "null"
    forms = {str(value)}
    if isinstance(value, float):
        forms |= {f"{value:g}", f"{value:.1f}", f"{value:.2f}", f"{value:.3f}", f"{value:.4f}"}
        forms |= {f"{value:,}"}
    elif isinstance(value, int):
        forms |= {f"{value:,}"}
    text = _strip_dates(text)
    for f in sorted(forms):
        # #171/#175: the number must stand ALONE. Nothing that makes it part of a larger token may touch it: no
        # digit, letter, `#`, `.`, `/`, `:` or `_` before it, and no id's `-` (EXP-041, v8-4); no digit, `.digit`,
        # `:` or `/` after it. A trailing UNIT letter is allowed (26.46ms, 3.82x). So `4` no longer matches inside
        # "#41", "EXP-041", "v4", "1.40" or "4:14", and dates are removed first.
        if f and re.search(rf"(?<![0-9A-Za-z#./:_]){_lead(f)}{re.escape(f)}(?![0-9:/]|\.[0-9])", text):
            return True, f
    num = value if isinstance(value, float) else (float(value) if isinstance(value, str)
                                                    and re.fullmatch(r"-?\d+\.\d+", value) else None)
    if num is not None and _sig(str(value)) >= 4:
        # A rounded quote of a longer float in the evidence (0.5715 of 0.5715025663...), only at >= 4 significant
        # digits: at two, a JSON full of floats would round to almost anything (EXP-015's 0.65 matched 0.6541...).
        d = len(str(value).split(".")[1]) if "." in str(value) else 0
        for m in re.finditer(r"(?<![0-9A-Za-z#./:_-])-?\d+\.\d{%d,}(?![0-9])" % (d + 1), text):
            if round(float(m.group()), d) == num:
                return True, m.group()
    return False, str(value)


def _sig(s):
    digits = s.lstrip("-").replace(".", "").lstrip("0")
    return len(digits)


def _lead(f):
    """A non-negative value must not be the tail of an id like `EXP-041` / `v8-4`: a `-` preceded by a letter or digit."""
    return "" if f.startswith("-") else r"(?<![0-9A-Za-z]-)"


# Dates and timestamps only; a bare H:MM is kept (it can be a duration, EXP-018's 4:14), and `:` blocks a match.
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?Z?)?\b|\b\d{8}T\d{4,6}Z?\b")


def _strip_dates(text, cache={}):
    k = id(text)
    if k not in cache:
        cache[k] = _DATE.sub(" ", text)
    return cache[k]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--registry", type=Path, default=REG,
                    help="registry file to check (default: the tracked experiments/registry.jsonl)")
    ap.add_argument("--lab-root", type=Path,
                    default=Path(os.environ.get("LD_LAB", Path.home() / "lab" / "llm-distillery")).expanduser(),
                    help="lab root for the optional `lab` field (default $LD_LAB, else ~/lab/llm-distillery)")
    args = ap.parse_args(argv)
    reg, lab_root = args.registry, args.lab_root
    if not reg.exists():
        print(f"FAIL: {reg} does not exist")
        return 1
    fails, entries, lab_paths = [], [], 0
    for n, line in enumerate(reg.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except Exception as ex:
            fails.append(f"line {n}: not valid JSON ({ex})")
            continue
        entries.append(e)
        for f in REQUIRED:
            if f not in e:
                fails.append(f"{e.get('id', f'line {n}')}: missing required field `{f}`")
        if "id" in e and not ID_RE.match(e["id"]):
            fails.append(f"{e['id']}: id is not EXP-NNN")
        if "date" in e and not DATE_RE.match(e["date"]):
            fails.append(f"{e.get('id')}: date is not ISO")
        if e.get("decision") not in DECISIONS:
            fails.append(f"{e.get('id')}: decision {e.get('decision')!r} not in {sorted(DECISIONS)}")
        for a in e.get("artifacts", []):
            if not (REPO / a).exists():
                fails.append(f"{e.get('id')}: artifact does not exist: {a}")
            elif Path(a).is_absolute() or ".." in Path(a).parts or a.strip("/") in ("", "."):
                fails.append(f"{e.get('id')}: artifact path {a!r} is absolute, escapes the repo, or names the root")
            elif not tracked(a):
                fails.append(f"{e.get('id')}: artifact is not tracked by git (it would be missing in a clone): {a}")
        lab = e.get("lab", [])
        if not isinstance(lab, list) or not all(isinstance(x, str) for x in lab):
            fails.append(f"{e.get('id')}: `lab` must be a list of lab paths")
            lab = []
        for x in lab:
            lab_paths += 1
            if not LAB_RE.match(x) or ".." in x.split("/"):
                fails.append(f"{e.get('id')}: lab path {x!r} is not under experiments/ or datasets/")
            elif lab_root.is_dir() and not (lab_root / x).exists():
                fails.append(f"{e.get('id')}: lab path does not exist under {lab_root}: {x}")
    ids = [e["id"] for e in entries if "id" in e]
    if ids != sorted(ids):
        fails.append("ids are not in ascending order")
    if len(set(ids)) != len(ids):
        fails.append("duplicate ids")

    checked = untraceable = 0
    for e in entries:
        text = artifact_text(e)
        for k, v in (e.get("metrics") or {}).items():
            checked += 1
            ok, form = traceable(v, text)
            if not ok:
                untraceable += 1
                fails.append(f"{e['id']}: metric `{k}` = {form} is NOT traceable to any cited "
                             f"artifact or commit message")
    print(f"entries {len(entries)}   metrics checked {checked}   untraceable {untraceable}")
    print(f"lab paths {lab_paths}" + ("" if lab_root.is_dir() else
          f" (existence SKIPPED: no lab root at {lab_root}; shape checked)"))
    print(f"spend recorded: ${sum(e.get('spend_usd') or 0 for e in entries):.4f}")
    for f in fails:
        print(f"  FAIL  {f}")
    print("PASS" if not fails else f"{len(fails)} FAILURE(S)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
