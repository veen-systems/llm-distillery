"""Validate experiments/registry.jsonl: schema, id order, artifact existence, and -- the point
of the file -- that every number an entry states is TRACEABLE to an artifact it cites.

⛔ Why the traceability check exists rather than a "please keep numbers in sync" note: augur's
own EXP-031 was an audit that found 19 registry numbers untraceable to any artifact. A registry
whose numbers drift is worse than no registry, because it reads authoritative.

A metric value passes if its string form appears VERBATIM in at least one cited artifact (or in
the commit message of a cited commit). `null` always passes -- an unrecoverable number should be
null with an explanation in `notes`, never invented.

Exit 0 = all checks pass. Exit 1 = at least one FAIL.
"""
import json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG = REPO / "experiments" / "registry.jsonl"
REQUIRED = ["id", "date", "title", "hypothesis", "subject", "oracle", "branch", "commits",
            "spend_usd", "population", "metrics", "decision", "decision_rationale",
            "artifacts", "references", "review"]
DECISIONS = {"kept", "parked", "rejected", "rolled_back", "superseded"}
ID_RE = re.compile(r"^EXP-\d{3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def artifact_text(entry, cache={}):
    """Every byte the entry points at: the artifact files, plus the commit messages."""
    key = tuple(entry["artifacts"]) + tuple(entry["commits"])
    if key in cache:
        return cache[key]
    blobs = []
    for a in entry["artifacts"]:
        p = REPO / a
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in (".md", ".txt", ".json", ".py", ".jsonl"):
                    blobs.append(f.read_text(encoding="utf-8", errors="replace"))
        elif p.is_file():
            blobs.append(p.read_text(encoding="utf-8", errors="replace"))
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
    for f in sorted(forms):
        if f and f in text:
            return True, f
    return False, str(value)


def main():
    if not REG.exists():
        print(f"FAIL: {REG} does not exist")
        return 1
    fails, entries = [], []
    for n, line in enumerate(REG.read_text(encoding="utf-8").splitlines(), 1):
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
    print(f"spend recorded: ${sum(e.get('spend_usd') or 0 for e in entries):.4f}")
    for f in fails:
        print(f"  FAIL  {f}")
    print("PASS" if not fails else f"{len(fails)} FAILURE(S)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
