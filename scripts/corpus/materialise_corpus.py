"""Join full article text back onto a corpus drawn from a REDUCED pool file.

The draw runs where the repo is (so the op-point is imported from the scorer, never copied);
the archive lives on the collection host. This step runs THERE, and it is deliberately paranoid
about one thing: an id is not proof that you rejoined the same article. Every row carries a
`content_sha256` taken at reduction time, and a mismatch is fatal, not a warning — the archive
rolls, and a rewritten row with the same id is exactly the case that would otherwise pass.

Usage:
  python3 materialise_corpus.py --corpus corpus.jsonl --archive DIR --out corpus_full.jsonl
"""
import argparse, glob, hashlib, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="corpus.jsonl from a --pool draw")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-missing", type=int, default=0,
                    help="tolerate at most N ids that are no longer in the window (default 0). "
                         "A rolled-off row is a REAL event; make it a decision, not a default.")
    args = ap.parse_args()

    want = {}
    for line in open(args.corpus, encoding="utf-8"):
        r = json.loads(line)
        if "content" in r and r["content"]:
            raise SystemExit("FATAL: this corpus already carries article text — it was drawn "
                             "from an archive, not from a reduced pool. Nothing to materialise.")
        want[r["id"]] = r

    files = sorted(glob.glob(os.path.join(args.archive, "filtered_*.jsonl")))
    if not files:
        raise SystemExit(f"FATAL: no filtered_*.jsonl under {args.archive}")

    found, mismatched = {}, []
    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            aid = r.get("id")
            if aid not in want or aid in found:
                continue
            content = r.get("content") or ""
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
            if sha != want[aid]["content_sha256"]:
                mismatched.append(aid)
                continue
            row = dict(want[aid])
            row["content"] = content
            found[aid] = row

    missing = [i for i in want if i not in found]
    print(f"corpus rows {len(want):,}   materialised {len(found):,}   "
          f"missing {len(missing):,}   sha-mismatched {len(mismatched):,}")
    if mismatched:
        raise SystemExit(
            f"FATAL: {len(mismatched)} rows matched by id but their text has CHANGED since the "
            f"draw (first: {mismatched[:3]}). The archive rewrote them; re-reduce and re-draw "
            f"rather than labelling text the manifest does not describe.")
    if len(missing) > args.allow_missing:
        raise SystemExit(
            f"FATAL: {len(missing)} ids are no longer in this window (allowed "
            f"{args.allow_missing}). The archive rolls; re-reduce and re-draw, or pass "
            f"--allow-missing deliberately and record it. First: {missing[:3]}")

    with open(args.out, "w", encoding="utf-8") as f:
        for aid in want:                       # preserve the drawn order
            if aid in found:
                f.write(json.dumps(found[aid], ensure_ascii=False) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
