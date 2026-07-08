"""Assemble the nature_recovery v4 re-label input (H5 deliverable).

This is the reproducible record of how the final training pool was assembled
BEFORE oracle scoring. Because the whole pool is scored in ONE pass under one
prompt version (-> datasets/scored/nature_recovery_v4_final_deepseek.jsonl),
there is no cd-v5-style post-hoc merge of two scoring vintages to reconcile;
H5's "merge_nr_v4_final.py" collapses to this single pre-scoring build. (Verified
by review: single uniform filter_version across all output rows.)

Pool = corpus (nature_recovery_v4_deepseek.jsonl, 3641) + mined positives
(nr_v4_positives_deepseek.jsonl, 831), MINUS:
  - content < MIN_CONTENT_LENGTH chars (v4 prefilter blocks these in production;
    labelling them risks framework-leakage garbage and mismatches production)
  - named gate probes (kept out of training so the agreement gate stays honest)

Fixes over the first-cut scratchpad version (review findings, both were dormant
because actual overlap==0 and only 1 probe was in-pool, but now enforced):
  - dedup PREFERS the mined-positive label on any id collision (positives first)
  - the excluded named-probe id set is DERIVED from the gate file, not hardcoded

Run: python scripts/nr_v4_build_relabel_input.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "datasets"
CORPUS = D / "scored/nature_recovery_v4_deepseek.jsonl"
POSITIVES = D / "scored/nr_v4_positives_deepseek.jsonl"
NAMED_PROBES = D / "gate/nr_v4_named_probes.jsonl"
HELDOUT_IDS = D / "gate/nr_v4_heldout_ids.txt"
OUT = D / "scored/nr_v4_relabel_input.jsonl"
MIN_CONTENT_LENGTH = 300  # matches BasePreFilter.MIN_CONTENT_LENGTH


def recs(p):
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                pass


def gate_probe_ids():
    """Named gate probes actually present in the DB (found_in_db=true)."""
    if not NAMED_PROBES.exists():
        return set()
    out = set()
    for r in recs(NAMED_PROBES):
        if r.get("found_in_db") and r.get("id"):
            out.add(r["id"])
    return out


def main():
    corpus = list(recs(CORPUS))
    positives = list(recs(POSITIVES))
    c_ids = {r["id"] for r in corpus if r.get("id")}
    p_ids = {r["id"] for r in positives if r.get("id")}
    overlap = c_ids & p_ids
    print(f"corpus={len(c_ids)} positives={len(p_ids)} overlap={len(overlap)}")

    exclude_probes = gate_probe_ids()
    print(f"named gate probes to exclude (derived from {NAMED_PROBES.name}): "
          f"{len(exclude_probes)} -> {sorted(exclude_probes)}")

    # positives FIRST so first-seen (kept) prefers the mined-positive label on
    # any id collision (dedup precedence fix).
    seen = set()
    out = []
    n_short = n_probe = n_dup = 0
    for r in positives + corpus:
        rid = r.get("id")
        if not rid:
            continue
        if rid in seen:
            n_dup += 1
            continue
        seen.add(rid)
        if rid in exclude_probes:
            n_probe += 1
            continue
        content = r.get("content") or ""
        if len(content) < MIN_CONTENT_LENGTH:
            n_short += 1
            continue
        out.append({"id": rid, "title": r.get("title", ""), "content": content,
                    "url": r.get("url", ""), "source": r.get("source", ""),
                    "published_date": r.get("published_date", "")})

    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out)} to {OUT} | excluded short={n_short} probe={n_probe} dup={n_dup}")

    # --- hard verification ---
    out_ids = {r["id"] for r in out}
    heldout = {l.strip() for l in open(HELDOUT_IDS) if l.strip()} if HELDOUT_IDS.exists() else set()
    errs = []
    if any(len(r["content"]) < MIN_CONTENT_LENGTH for r in out):
        errs.append("short article present")
    if out_ids & exclude_probes:
        errs.append("named probe present")
    if out_ids & heldout:
        errs.append(f"{len(out_ids & heldout)} held-out gate probes present")
    if any(not r["title"].strip() or not r["content"].strip() for r in out):
        errs.append("empty title/content")
    print(f"held-out gate probes in output: {len(out_ids & heldout)} (must be 0)")
    if errs:
        print("VERIFICATION FAILED:", errs)
        sys.exit(1)
    print("VERIFICATION PASSED.")


if __name__ == "__main__":
    main()
