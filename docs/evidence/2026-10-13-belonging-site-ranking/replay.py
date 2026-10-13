"""Replay candidate ranking formulas on real ovr.news pages (asked by the ovr.news session for the owner, 2026-10-13).

Formulas, as specified by ovr.news (s = normalized weighted_average, age_h = hours since publication at build):
  control  s x 0.85^(age_h/24) x 1.3 if age_h < 24     (live; reproduces the pages, see site_rank.py)
  A        s x 0.5^(age_h/48)                          (half-life 2 days, no cliff)
  B        s x 0.5^(age_h/72)                          (half-life 3 days, no cliff)
  C        band (0: < 72 h, 1: 72 h-7 d, 2: older) ascending, then s descending
  H        hybrid (ovr.news, later the same day): slots 1-5 = the 5 highest-s cards under 24 h old; then every other
           card in C order. Fewer than 5 under 24 h: the remaining slots go to C order.

Populations:
  10-13, all five lenses: exactly the cards each live page shows (built 2026-10-13T06:55:18Z), so the editor's,
    canonical-lens and dedup removals are already applied. Inputs: lenses_20261013/<lens>.json.
  10-12, Belonging: the owner-labelled page, rebuilt at 14:30Z (site_rank.py) from pop_window_20261012.json. Rows
    the 10-13 06:43 build population held but its page did not show are dropped as removed. ASSUMPTION: a removal
    is sticky across one day. Rows published before 10-03 have unknown removal status, so they are flagged.

Labels (Belonging only): the owner's labels (with the owner's pos-25 correction, so 10 personal) for the 30 rows of the 10-12 page (tags.tsv); otherwise qwen3.8:27b
tags from the 10-12 runs (a FLOOR: qwen undercounts personal, 7 vs the owner's 10 on the same 30); otherwise
untagged. Counts are reported per source and never merged into one number.

    python3 docs/evidence/2026-10-13-belonging-site-ranking/replay.py > .../replay_result.txt
"""
import csv, json, os
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser()
QWEN = [LAB / "experiments/2026-10-12-belonging-c2c/focus-tag/out.jsonl",
        LAB / "experiments/2026-10-12-belonging-c2c/focus-tag-comp/out.jsonl"]
TAGS = HERE.parent / "2026-10-12-belonging-personal-tag" / "tags.tsv"
N = 30
# tags.tsv keeps the pre-registered labels (rule 3); the owner's later corrections live beside it as DATA, and every
# consumer loads them (gotcha 2026-10-13: a correction kept only in prose was missed).
_CORR = Path(__file__).resolve().parent.parent / "2026-10-12-belonging-personal-tag" / "owner_corrections.tsv"
OWNER_CORRECTIONS = {row["id"]: row["owner"] for row in csv.DictReader(_CORR.open(encoding="utf-8"), delimiter="\t")}


def pdate(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def age_h(r, now):
    return max(0.0, (now - pdate(r["published_date"])).total_seconds() / 3600)


FORMULAS = {
    "control": lambda r, now: (-(r["weighted_average"] * 0.85 ** (age_h(r, now) / 24)
                                 * (1.3 if age_h(r, now) < 24 else 1.0)),),
    "A hl=2d": lambda r, now: (-(r["weighted_average"] * 0.5 ** (age_h(r, now) / 48)),),
    "B hl=3d": lambda r, now: (-(r["weighted_average"] * 0.5 ** (age_h(r, now) / 72)),),
    "C bands": lambda r, now: (0 if age_h(r, now) < 72 else 1 if age_h(r, now) < 168 else 2,
                               -r["weighted_average"]),
}


def order(name, rows, now):
    if name != "H hybrid":
        return sorted(rows, key=lambda r: FORMULAS[name](r, now))
    fresh = sorted((r for r in rows if age_h(r, now) < 24), key=lambda r: -r["weighted_average"])[:5]
    ids = {r["id"] for r in fresh}
    return fresh + [r for r in sorted(rows, key=lambda r: FORMULAS["C bands"](r, now)) if r["id"] not in ids]


def labels():
    owner = {t["id"]: t["owner"] for t in csv.DictReader(TAGS.open(encoding="utf-8"), delimiter="\t")}
    owner.update(OWNER_CORRECTIONS)
    qwen = {}
    for f in QWEN:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                o = json.loads(line)
                if o.get("focus") in ("personal", "group"):
                    qwen.setdefault(o["id"], o["focus"])
    return owner, qwen


def report(name, rows, now, control_top, lab=None, flag=frozenset()):
    top = order(name, rows, now)[:N]
    ids = [r["id"] for r in top]
    ages = [age_h(r, now) for r in top]
    low = min(top, key=lambda r: r["weighted_average"])
    line = (f"  {name:8} in control top {N}: {len(set(ids) & set(control_top)):2}/{N} | age <24h {sum(a < 24 for a in ages):2}"
            f" 1-3d {sum(24 <= a < 72 for a in ages):2} older {sum(a >= 72 for a in ages):2} | lowest s "
            f"{low['weighted_average']:.2f} (raw {float('nan') if low.get('raw_weighted_average') is None else low['raw_weighted_average']:.2f}) | "
            f"upper-median s {sorted(r['weighted_average'] for r in top)[N // 2]:.2f}")
    if lab:
        owner, qwen = lab
        o_p = sum(owner.get(i) == "personal" for i in ids)
        o_n = sum(i in owner for i in ids)
        q_ids = [i for i in ids if i not in owner]
        q_p = sum(qwen.get(i) == "personal" for i in q_ids)
        q_n = sum(i in qwen for i in q_ids)
        line += (f"\n           personal: owner {o_p} of {o_n} labelled; qwen {q_p} of {q_n} more tagged (floor); "
                 f"untagged {N - o_n - q_n}")
    if flag:
        line += f"; removal status unknown {len(set(ids) & flag)}"
    print(line)
    return ids


def main():
    lab = labels()
    print(f"== 10-13 build 06:55:18Z, all five lenses (population = the page's own cards)")
    for lens in ("belonging", "thriving", "solutions", "discovery", "recovery"):
        d = json.loads((HERE / "lenses_20261013" / f"{lens}.json").read_text())
        now, rows = pdate(d["built"]), d["page_order"]
        print(f"{lens} ({d['filter']}): {len(rows)} cards, {sum(age_h(r, now) < 24 for r in rows)} under 24 h")
        control = [r["id"] for r in rows][:N]
        assert [r["id"] for r in sorted(rows, key=lambda r: FORMULAS["control"](r, now))][:N] == control, lens
        for name in [*FORMULAS, "H hybrid"]:
            report(name, rows, now, control, lab if lens == "belonging" else None)
        c = [r["id"] for r in order("C bands", rows, now)]
        h = [r["id"] for r in order("H hybrid", rows, now)]
        print(f"  H vs C: same top-{N} set {set(c[:N]) == set(h[:N])}; C positions of H's slots 1-5 "
              f"{[c.index(i) + 1 for i in h[:5]]}; top-{N} positions that differ {sum(a != b for a, b in zip(c[:N], h[:N]))}")

    print("\n== 10-12 Belonging, the owner-labelled page, rebuilt at 14:30Z")
    now = datetime(2026, 10, 12, 14, 30, tzinfo=timezone.utc)
    pop = [r for r in json.loads((HERE / "pop_window_20261012.json").read_text())
           if pdate(r["s_created"]) <= now and pdate(r["published_date"]) <= now]
    b13 = {r["id"] for r in json.loads((HERE / "build_pop_20261013.json").read_text())}
    p13 = {l.strip() for l in (HERE / "page_ids_20261013.txt").read_text().splitlines() if l.strip()}
    removed = b13 - p13
    rows = [r for r in pop if r["id"] not in removed]
    unknown = frozenset(r["id"] for r in rows if r["id"] not in b13)
    page30 = [t["id"] for t in csv.DictReader(TAGS.open(encoding="utf-8"), delimiter="\t")]
    print(f"population {len(pop)}, dropped as removed {len(pop) - len(rows)}, removal status unknown {len(unknown)}")
    got = [r["id"] for r in sorted(rows, key=lambda r: FORMULAS["control"](r, now))][:N]
    print(f"control reproduces the labelled page: {sum(a == b for a, b in zip(got, page30))}/{N} positions")
    for name in [*FORMULAS, "H hybrid"]:
        report(name, rows, now, page30, lab, unknown)


if __name__ == "__main__":
    main()
