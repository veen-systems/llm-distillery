"""Near-duplicate leakage of evaluation rows into training rows (#176). See PREREGISTRATION.md.

    python near_dup_leakage.py ARM QUERY.jsonl REF.jsonl OUT_PREFIX [--drop id,id,...]

Prints the controls, the counts at 0.90/0.93/0.95 with the query-set size, and the median max
cosine; writes OUT_PREFIX.pairs.tsv (every query row >= 0.90: cosine, ids, both titles).
Text geometry is scripts/screening/near_dup_filter.py's text_of, imported, not copied.
"""
import argparse, json, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "screening"))
from near_dup_filter import text_of  # noqa: E402

THRESHOLDS = (0.90, 0.93, 0.95)
N_CONTROL = 5


def load(p, drop=()):
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r["id"] not in drop]
    bad = [r.get("id") for r in rows if not (r.get("title") or r.get("content"))]
    if bad:
        raise SystemExit(f"FATAL: {len(bad)} rows with neither title nor content, e.g. {bad[:3]}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arm"); ap.add_argument("query"); ap.add_argument("ref"); ap.add_argument("out")
    ap.add_argument("--drop", default="")
    a = ap.parse_args()
    import numpy as np
    from sentence_transformers import SentenceTransformer

    q = load(a.query, set(filter(None, a.drop.split(","))))
    ref = load(a.ref)
    ref_ids = {r["id"] for r in ref}
    # Controls: exact copies and rewritten copies of 5 reference rows, under new ids.
    step = max(1, len(ref) // N_CONTROL)
    picks = [ref[i * step] for i in range(N_CONTROL)]
    exact = [dict(r, id=f"__ctl_exact_{i}") for i, r in enumerate(picks)]
    rewr = [dict(r, id=f"__ctl_rewrite_{i}", title="Local report",
                 content=(r.get("content") or "")[300:]) for i, r in enumerate(picks)]

    model = SentenceTransformer("intfloat/multilingual-e5-small")
    enc = lambda rows: model.encode([text_of(r) for r in rows], batch_size=256,
                                    normalize_embeddings=True, show_progress_bar=False)
    R = enc(ref)
    Q = enc(q + exact + rewr)
    S = Q @ R.T
    best = S.argmax(1); mx = S.max(1)

    n = len(q)
    ctl_exact = [float(x) for x in mx[n:n + N_CONTROL]]
    ctl_rewr = [float(x) for x in mx[n + N_CONTROL:]]
    print(f"[{a.arm}] query {a.query} n={n}   reference {a.ref} n={len(ref)}")
    print(f"  control exact   (must be >= 0.99): {['%.4f' % x for x in ctl_exact]}")
    print(f"  control rewrite (reported):        {['%.4f' % x for x in ctl_rewr]}")
    if min(ctl_exact) < 0.99:
        raise SystemExit("FATAL: presence control failed; no count is read")
    shared_ids = sum(1 for r in q if r["id"] in ref_ids)
    print(f"  query ids also in reference (exact id leak): {shared_ids}/{n}")
    real = mx[:n]
    for t in THRESHOLDS:
        k = int((real >= t).sum())
        print(f"  max cosine >= {t:.2f}: {k}/{n} = {100 * k / n:.2f}%")
    print(f"  median max cosine: {statistics.median(float(x) for x in real):.4f}")
    order = sorted(range(n), key=lambda i: -real[i])
    with open(a.out + ".pairs.tsv", "w", encoding="utf-8") as f:
        f.write("cosine\tquery_id\tref_id\tquery_title\tref_title\n")
        for i in order:
            if real[i] < THRESHOLDS[0]:
                break
            r = ref[best[i]]
            f.write(f"{real[i]:.4f}\t{q[i]['id']}\t{r['id']}\t{(q[i].get('title') or '')[:120]}\t"
                    f"{(r.get('title') or '')[:120]}\n")
    print(f"  wrote {a.out}.pairs.tsv")


if __name__ == "__main__":
    main()
