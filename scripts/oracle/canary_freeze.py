"""Freeze an oracle canary set (#177) from canary_draw.py's candidates. Step 2 of 2 (needs sentence-transformers).

    python canary_freeze.py --candidates candidates.jsonl --reference a.jsonl b.jsonl ... \
        --out datasets/canary/human_thriving/set.jsonl --manifest config/canary/human_thriving.json

Drops a candidate that matches ANY reference row (every training split the filter has used) by id, by url, or at
e5-small cosine >= 0.93 (EXP-051's instrument, `near_dup_filter.text_of`), and any candidate within 0.93 of an
EARLIER-ranked kept candidate (near-twins inside the set waste canary items). Then keeps, per stratum, the first
TARGET by `draw_rank`. Raises if a stratum cannot be filled.

Outputs: the set (article text; lives under datasets/, which is gitignored: the repo is public and the text is
publishers') and a MANIFEST that IS committed: per item id, stratum, student score and the sha256 of
title + "\\n" + content, plus the set's own sha256. canary.py refuses a set whose bytes do not match the manifest.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "screening"))
from near_dup_filter import text_of  # noqa: E402

TARGET = {"hi": 30, "near": 30, "lo": 40}
COS = 0.93


def item_sha(r):
    return hashlib.sha256(((r.get("title") or "") + "\n" + (r.get("content") or "")).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--reference", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--filter", required=True)
    a = ap.parse_args()
    from sentence_transformers import SentenceTransformer

    cand = [json.loads(l) for l in open(a.candidates, encoding="utf-8") if l.strip()]
    ref = {}
    for p in a.reference:
        for l in open(p, encoding="utf-8"):
            if l.strip():
                r = json.loads(l); ref[r["id"]] = r
    ref = list(ref.values())
    ref_ids, ref_urls = {r["id"] for r in ref}, {r.get("url") for r in ref} - {None, ""}
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    enc = lambda rows: model.encode([text_of(r) for r in rows], batch_size=256, normalize_embeddings=True,
                                    show_progress_bar=False)
    C, R = enc(cand), enc(ref)
    to_ref = (C @ R.T).max(1)
    drop = {"id": 0, "url": 0, "cos_ref": 0, "cos_self": 0}
    kept, kept_idx = {k: [] for k in TARGET}, []
    order = sorted(range(len(cand)), key=lambda i: (cand[i]["stratum"], cand[i]["draw_rank"]))
    for i in order:
        r = cand[i]
        if len(kept[r["stratum"]]) >= TARGET[r["stratum"]]:
            continue
        if r["id"] in ref_ids:
            drop["id"] += 1; continue
        if r.get("url") in ref_urls:
            drop["url"] += 1; continue
        if to_ref[i] >= COS:
            drop["cos_ref"] += 1; continue
        if kept_idx and float((C[kept_idx] @ C[i]).max()) >= COS:
            drop["cos_self"] += 1; continue
        kept[r["stratum"]].append(r); kept_idx.append(i)
    for k, n in TARGET.items():
        if len(kept[k]) < n:
            raise SystemExit(f"FATAL: stratum {k} filled {len(kept[k])}/{n} after exclusion {drop}")
    items = [r for k in ("hi", "near", "lo") for r in kept[k]]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps({k: r[k] for k in ("id", "title", "content", "url", "source", "published_date",
                                                  "language")}, ensure_ascii=False) + "\n" for r in items)
    Path(a.out).write_text(body, encoding="utf-8")
    man = {"filter": a.filter, "set_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(), "n": len(items),
           "exclusion": {"cosine": COS, "reference_rows": len(ref), "dropped": drop},
           "items": [{"id": r["id"], "stratum": r["stratum"], "student_raw": r["student_raw"],
                      "student_version": r["student_version"], "item_sha256": item_sha(r)} for r in items]}
    Path(a.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(a.manifest).write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"kept {len(items)} {{{', '.join(f'{k}: {len(v)}' for k, v in kept.items())}}}; dropped {drop}; "
          f"reference rows {len(ref)}; set sha256 {man['set_sha256']}")


if __name__ == "__main__":
    main()
