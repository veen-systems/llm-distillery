"""Restore FULL article text to an adverse/no-regression set whose rows are 300-char excerpts.

Why this exists
---------------
`datasets/adverse/uplifting.jsonl` ships 18 rows with `content_excerpt: true` and content
truncated to exactly 300 characters, against originals of 620-28,905. The repo's own rule
(`datasets/adverse/2026-08-09-reader-flags.md`) is that **excerpts are not sufficient -- three
of five drafts reversed on a full read** -- and Gate B-A of the v8 plan is BLOCKING and judged
on this file. Meanwhile nothing on the scoring path stops a paid run against a 300-char row:
`is_scrape_junk` floors at 25 characters, and the 300-char oracle floor lives only in
`ground_truth.batch_scorer.make_oracle_prefilter`, which the DeepSeek path does not use.

Where the text actually is
--------------------------
⛔ NOT in the FluxusSource archive. Those tarballs hold PRODUCER bytes: three rows whose
enriched originals are 14,546 / 2,917 / 3,652 characters appear there at 447 / 133 / 441. The
long text is NexusMind's enrichment, so the source is NexusMind -- first the live
`data/filtered/` window (~14 days), then the MONTHLY archives
`data/archived/nexusmind_YYYY-MM.tar.gz`, which run 2025-10 .. current. Their member layout is
`nexusmind_YYYY-MM/<lens>/scored.jsonl` -- one per lens, inside the tarball, resolving to no
path on disk. This script reads EVERY lens member, not just the set's own: an adverse row is
archived under whichever lens scored it, and the set spans filters. (Measured 2026-09-01: 15
of the 18 uplifting-set rows came out of the BELONGING member.)

⭐ Those monthly archives are why "the window has rolled, so it is unrecoverable" is wrong.
That premise appears in llm-distillery#127's comment thread and in the 2026-08-30 rulings.

The join is verified, not assumed
---------------------------------
An id is not proof you rejoined the same article -- ids are reused when a source rewrites a
URL, and the archive spans months. Every recovered row must match the excerpt's recorded
`content_original_length` EXACTLY, and must still start with the 300 characters the excerpt
kept. A mismatch is fatal, never a warning.

Run it on the host that holds the archive (sadalsuud):
    python3 rehydrate_adverse.py --in adverse.jsonl --out adverse_full.jsonl [--allow-missing N]
"""
import argparse, glob, json, os, sys, tarfile


def _norm(s):
    """Whitespace-collapsed text, for comparing an excerpt against its source.

    Only ever used for the prefix CHECK — never for what gets written back, which is the
    source text byte-for-byte.
    """
    return " ".join(s.split())


def candidate_lines(filtered_root, archive_root, wanted, log):
    """Yield (source_label, line) from the cheapest source first.

    Live window before archives: it is smaller, uncompressed, and if a row is still live the
    archive scan can be skipped entirely for it.
    """
    files = sorted(glob.glob(os.path.join(filtered_root, "*", "filtered_*.jsonl")))
    log(f"live window: {len(files)} cycle file(s)")
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    yield f"live:{os.path.basename(f)}", line
        except OSError:
            continue

    tars = sorted(glob.glob(os.path.join(archive_root, "nexusmind_*.tar.gz")), reverse=True)
    log(f"monthly archives: {len(tars)} tarball(s)"
        + (f", newest {os.path.basename(tars[0])}" if tars else ""))
    for t in tars:
        try:
            with tarfile.open(t, "r:gz") as tf:
                for m in tf:
                    # every lens, not just the set's own -- an adverse row can be archived
                    # under whichever lens scored it, and the set spans filters
                    if not (m.isfile() and m.name.endswith("scored.jsonl")):
                        continue
                    fh = tf.extractfile(m)
                    if fh is None:
                        continue
                    label = f"{os.path.basename(t)}:{m.name}"
                    for raw in fh:
                        yield label, raw.decode("utf-8", "replace")
        except (tarfile.TarError, OSError) as e:
            log(f"  WARN unreadable {os.path.basename(t)}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--filtered-root", default="/home/jeroen/local_dev/NexusMind/data/filtered")
    ap.add_argument("--archive-root", default="/home/jeroen/local_dev/NexusMind/data/archived")
    ap.add_argument("--allow-missing", type=int, default=0,
                    help="tolerate at most N rows left as excerpts. A row that cannot be "
                         "rehydrated is a REAL event; make it a decision, not a default.")
    args = ap.parse_args()

    def log(m):
        print(m, file=sys.stderr, flush=True)

    rows = [json.loads(l) for l in open(args.inp, encoding="utf-8")]
    excerpts = {r["id"]: r for r in rows if r.get("content_excerpt") is True}
    log(f"{len(rows)} row(s), {len(excerpts)} carrying content_excerpt: true")
    if not excerpts:
        raise SystemExit("FATAL: no row is marked content_excerpt: true. Nothing to rehydrate, "
                         "and a silent no-op here would read as success.")
    for r in excerpts.values():
        if not r.get("content_original_length"):
            raise SystemExit(f"FATAL: {r['id']} is an excerpt with no content_original_length — "
                             "there is nothing to verify a rejoin against. Refusing.")

    found, mismatched = {}, []
    wanted = set(excerpts)
    for label, line in candidate_lines(args.filtered_root, args.archive_root, wanted, log):
        if not wanted:
            break
        # cheap reject before the JSON parse: these files are millions of lines
        hit = next((w for w in wanted if w in line), None)
        if hit is None:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("id") != hit:
            continue                                   # the id appeared in some other field
        content = rec.get("content") or ""
        want_len = int(excerpts[hit]["content_original_length"])
        if len(content) != want_len:
            mismatched.append((hit, label, len(content), want_len))
            continue                                   # keep looking: an older copy may match
        # ⚠️ The prefix comparison is WHITESPACE-NORMALISED on both sides, and that is not
        # laxity. Excerpting collapsed newlines to spaces: `north_african_tsa_algerie_…`
        # stores `"Canada. Cette"` where the live row has `"Canada.\nCette"`, and a strict
        # `startswith` rejected the correct article six times over. (That row is also the
        # only excerpt that is not exactly 300 characters — it is 355.) The LENGTH check is
        # the strong constraint and is deliberately left exact: it is computed on the
        # original, so it still catches a rewritten article reusing an id.
        prefix = _norm((excerpts[hit].get("content") or "")[:300])
        if prefix and not _norm(content).startswith(prefix):
            mismatched.append((hit, label, "prefix-mismatch", want_len))
            continue
        found[hit] = (content, label)
        wanted.discard(hit)
        log(f"  recovered {hit[:46]:48} {len(content):>7} chars  {label}")

    log("")
    for i, label, got, want in mismatched:
        log(f"  REJECTED {i[:46]:48} {got} != content_original_length {want}  ({label})")
    log(f"recovered {len(found)} of {len(excerpts)}; still excerpts: {len(wanted)}")
    for w in sorted(wanted):
        log(f"  MISSING {w}")

    if len(wanted) > args.allow_missing:
        raise SystemExit(f"FATAL: {len(wanted)} row(s) could not be rehydrated and "
                         f"--allow-missing is {args.allow_missing}. No output written.")

    out = []
    for r in rows:
        if r["id"] in found:
            content, label = found[r["id"]]
            r = dict(r)
            r["content"] = content
            r["content_excerpt"] = False
            r["content_rehydrated_from"] = label
        out.append(r)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"wrote {args.out}")
    print(json.dumps({"rows": len(out), "rehydrated": len(found),
                      "still_excerpt": sorted(wanted), "rejected": len(mismatched)}))


if __name__ == "__main__":
    main()
