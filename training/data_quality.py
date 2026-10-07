"""Training-data quality checks that need more than the splits themselves: a production sample, the filter's
scoring constants, the collector's language stamps. The failure modes they guard are listed in
docs/checklists/training-data-fmea.md; `training/validate_training_data.py` runs them (RUNBOOK § Prepare data).

Born in the belonging retrain (2026-10-07), where two of them were found only because the owner asked:
training text unlike production text (pre-enrichment snippets vs enriched articles), and a text cut that replaced
the ending a head+tail model reads."""
import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SHINGLE = 8


def _words(text, lo=0, hi=None):
    return re.findall(r"\w+", (text or "").lower())[lo:hi]


def shingles(text):
    """8-word runs from words 10..160: alignment-free, so a differing dateline or prefix does not hide a twin."""
    w = _words(text, 10, 160)
    return {tuple(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1)}


def _nu(u):
    u = re.sub(r"^https?://(www\.)?", "", (u or "").strip().lower()).split("#")[0]
    base, _, q = u.partition("?")
    keep = sorted(x for x in q.split("&") if x and not re.match(r"(utm_[a-z]+|fbclid|gclid|mc_[a-z]+|ref)=", x))
    return base.rstrip("/") + ("?" + "&".join(keep) if keep else "")


def _nt(t):
    t = re.sub(r"[\W_]+", "", (t or "").lower())
    return t if len(t) >= 20 else None


def scoring_constants(filter_dir):
    """DIMENSION_WEIGHTS, the gatekeeper and the MEDIUM threshold, read from the package's base_scorer.py as source.
    Raises if any is missing: a plausible default here decides which rows count as positives."""
    src = (Path(filter_dir) / "base_scorer.py").read_text()
    want = ("DIMENSION_WEIGHTS", "GATEKEEPER_DIMENSION", "GATEKEEPER_MIN", "GATEKEEPER_CAP", "TIER_THRESHOLDS")
    c = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Assign)
         and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in want}
    if "DIMENSION_WEIGHTS" not in c or "TIER_THRESHOLDS" not in c:
        raise SystemExit(f"{filter_dir}/base_scorer.py: no DIMENSION_WEIGHTS / TIER_THRESHOLDS")
    medium = [t[1] for t in c["TIER_THRESHOLDS"] if t[0] == "medium"]
    if len(medium) != 1:
        raise SystemExit(f"{filter_dir}/base_scorer.py: no single 'medium' tier")
    c["MEDIUM"] = float(medium[0])
    return c


def label_wa(c, names, labels):
    """The label's weighted average with the filter's weights AND gatekeeper, as its scorer computes it."""
    sc = dict(zip(names, labels))
    w = sum(c["DIMENSION_WEIGHTS"][d] * sc[d] for d in c["DIMENSION_WEIGHTS"])
    g = c.get("GATEKEEPER_DIMENSION")
    if g is not None and sc[g] < c["GATEKEEPER_MIN"]:
        w = min(w, c["GATEKEEPER_CAP"])
    return w


def cross_split_twins(splits, hits=20):
    """FM-D1. Rows in val/test that are the same story as a train row: same normalised url or title, or >= `hits`
    distinctive shared 8-word runs (a run counts only if it occurs in <= 3 rows overall; site boilerplate otherwise
    matches unrelated stories). Returns [(split, id, by, train_id)]; the caller drops or refuses."""
    train = splits["train"]
    keys = defaultdict(set)
    for r in train:
        for k in (("url", _nu(r.get("url"))), ("title", _nt(r.get("title")))):
            if k[1]:
                keys[k].add(r["id"])
    sh = {r["id"]: shingles(r.get("content")) for s in splits for r in splits[s]}
    df = Counter(x for v in sh.values() for x in v)
    index = defaultdict(set)
    for r in train:
        for x in sh[r["id"]]:
            if df[x] <= 3:
                index[x].add(r["id"])
    out = []
    for s in ("val", "test"):
        for r in splits[s]:
            hit = next(((k[0], sorted(keys[k])[0]) for k in (("url", _nu(r.get("url"))), ("title", _nt(r.get("title"))))
                        if k[1] and keys.get(k)), None)
            if not hit:
                c = Counter(t for x in sh[r["id"]] if df[x] <= 3 for t in index.get(x, ()))
                best = c.most_common(1)
                if best and best[0][1] >= hits:
                    hit = ("content", best[0][0])
            if hit:
                out.append((s, r["id"], hit[0], hit[1]))
    return out


def parity(rows, production, is_pos):
    """FM-T1. Text length of training rows vs a uniform production sample, and the positive share per length bin.
    A label that rises with length while production is all long is a shortcut the student can learn."""
    def q(xs):
        xs = sorted(xs)
        return {p: xs[int(p / 100 * (len(xs) - 1))] for p in (10, 50, 90)} if xs else {}
    out = dict(train_len=q([len(r.get("content") or "") for r in rows]),
               production_len=q([len(r.get("content") or "") for r in production]), positive_share_by_len={})
    for lo, hi in ((0, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 10 ** 9)):
        g = [is_pos(r) for r in rows if lo <= len(r.get("content") or "") < hi]
        out["positive_share_by_len"][f"{lo}-{hi if hi < 10 ** 9 else 'inf'}"] = dict(
            n=len(g), share=round(sum(g) / max(1, len(g)), 3))
    return out


def load_language(path):
    """id -> the `language` FluxusSource's collector stamped (langdetect). Recovered from its collection archives
    (`~/local_dev/FluxusSource/data/archived/collection_*.tar.gz`): never improvise a detector, production already has
    one. A row without a stamp is reported as `unstamped`, never guessed."""
    return json.load(open(path)) if path else {}


def mix(rows, production, is_pos, lang):
    """FM-D2. Language (the collector's stamp) and source of training positives / negatives vs production. Report."""
    def src(r):
        return r["id"].rsplit("_", 1)[0]

    def share(rs, f, n=8):
        c = Counter(f(r) for r in rs)
        return {k: round(v / max(1, len(rs)), 3) for k, v in c.most_common(n)}
    pos = [r for r in rows if is_pos(r)]
    neg = [r for r in rows if not is_pos(r)]
    lg = lambda r: lang.get(r["id"]) or "unstamped"  # noqa: E731
    return dict(language=dict(train_pos=share(pos, lg), train_neg=share(neg, lg), production=share(production, lg)),
                top_sources_train_pos=share(pos, src),
                top_source_share_pos=round(max(Counter(map(src, pos)).values()) / len(pos), 3) if pos else None,
                n=dict(train_pos=len(pos), train_neg=len(neg), production=len(production)))


BOILER = re.compile(r"cookie|subscribe|newsletter|all rights reserved|enable javascript|sign up for|advertisement"
                    r"|lees ook|lire aussi|leer más|mehr zum thema|related articles?", re.IGNORECASE)


def boilerplate(rows, group=lambda r: r.get("origin", "all")):
    """FM-D3. Share of rows with a site-furniture marker, and of rows whose text is mostly runs shared with >= 10
    other rows. Report, by group."""
    sh = {r["id"]: shingles(r.get("content")) for r in rows}
    df = Counter(x for v in sh.values() for x in v)
    by = defaultdict(Counter)
    for r in rows:
        g = group(r)
        by[g]["n"] += 1
        by[g]["marker"] += bool(BOILER.search(r.get("content") or ""))
        s = sh[r["id"]]
        by[g]["mostly_shared"] += bool(s) and sum(df[x] >= 10 for x in s) / len(s) > 0.5
    return {g: dict(n=c["n"], marker_share=round(c["marker"] / c["n"], 3),
                    mostly_shared_share=round(c["mostly_shared"] / c["n"], 3)) for g, c in by.items()}
