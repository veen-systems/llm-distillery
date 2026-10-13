"""Step 6 of PREREGISTRATION.md: per build, the qwen `personal` count in the first 30 v3 rows (a FLOOR), plus, for
10-12 only, the owner's labels on the rows they cover (pre-registered + the owner's corrections, as data).

    python3 docs/evidence/2026-10-13-belonging-daily-baseline/count.py > .../count_result.txt

Reads selection.json and the lab file tag/out.jsonl (cited in MANIFEST.json).
"""
import csv, json, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser()
TAGS = LAB / "experiments/2026-10-13-belonging-daily-baseline/tag/out.jsonl"
PT = HERE.parent / "2026-10-12-belonging-personal-tag"

qwen = {}
for line in TAGS.read_text(encoding="utf-8").splitlines():
    if line.strip():
        o = json.loads(line)
        qwen[o["id"]] = o["focus"]
owner = {t["id"]: t["owner"] for t in csv.DictReader((PT / "tags.tsv").open(encoding="utf-8"), delimiter="\t")}
owner.update({t["id"]: t["owner"] for t in csv.DictReader((PT / "owner_corrections.tsv").open(encoding="utf-8"),
                                                          delimiter="\t")})
sel = json.loads((HERE / "selection.json").read_text())
counts = []
print("build               N  in_range  qwen_personal  qwen_group  unparsed  | owner (labelled rows only)")
for build, s in sel.items():
    ids = s["top30_v3"]
    missing = [i for i in ids if i not in qwen]
    assert not missing, f"{build}: {len(missing)} rows untagged"
    p = sum(qwen[i] == "personal" for i in ids)
    g = sum(qwen[i] == "group" for i in ids)
    o_n = sum(i in owner for i in ids)
    o_p = sum(owner.get(i) == "personal" for i in ids)
    qo = sum(qwen[i] == "personal" for i in ids if i in owner)
    print(f"{build:18} {s['n']:2}  {str(s['in_range']):8}  {p:13}  {g:10}  {len(ids) - p - g:8}  | "
          f"owner {o_p} personal of {o_n} labelled (qwen says {qo} personal on those {o_n})")
    if s["in_range"]:
        counts.append(p)
print(f"\nin-range builds {len(counts)}: qwen personal min {min(counts)}, max {max(counts)}, range {max(counts) - min(counts)}")
