"""Shared-text share of every A1 pair at cosine >= 0.93 (#176), on the FULL text.

    .venv/bin/python classify_pairs.py LAB_DIR > classify_pairs.txt

share = |8-word shingles of the query that also occur in its train twin| / |query shingles|. A first-600-chars
comparison missed a leak (ScienceDaily's Date/Source/Summary header pushed the shared body out of the window;
review 2026-10-16), so the WHOLE text is compared. LEAK iff share >= 0.5: copy, not shared quotes (the highest
non-copy pair in the review read 0.19). The cut is post hoc — the pre-registration classed pairs by reading; this
replaces the eye with a number and prints every share so the cut can be judged.
"""
import json, re, sys
from pathlib import Path

LAB = Path(sys.argv[1])
CUT, N = 0.5, 8


def shingles(t):
    w = re.findall(r"\w+", (t or "").lower())
    return {tuple(w[i:i + N]) for i in range(max(0, len(w) - N + 1))}


q = {r["id"]: r for r in map(json.loads, open(LAB / "ht_v8_test.jsonl"))}
ref = {r["id"]: r for r in map(json.loads, open(LAB / "ht_adj3_train.jsonl"))}
leaks = []
for line in list(open(LAB / "A1.pairs.tsv"))[1:]:
    cos, qi, ri, *_ = line.rstrip("\n").split("\t")
    if float(cos) < 0.93:
        break
    a, b = shingles(q[qi].get("content")), shingles(ref[ri].get("content"))
    share = len(a & b) / len(a) if a else 0.0
    tag = "LEAK" if share >= CUT else "-"
    if tag == "LEAK":
        leaks.append(qi)
    print(f"{cos}\tshare {share:.2f}\t{tag}\t{qi}\t{ri}")
print(f"leaks (share >= {CUT}): {len(leaks)} of the >= 0.93 pairs")
print("LEAK_IDS " + ",".join(leaks))
