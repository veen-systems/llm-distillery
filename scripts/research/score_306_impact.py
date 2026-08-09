"""NM#306 IMPACT — how much does a corrupted body move a lens score?

NM#306 establishes the RATE at which enrichment replaces a correct article body
with unrelated wire/widget content. This measures the HARM, which is the other
half of the launch decision: rate x impact. It belongs in llm-distillery because
this repo owns the scorers.

DESIGN. For each il Fatto article we hold two bodies for the SAME title:
    pre  = the RSS summary as collected (pre-enrichment, verified correct)
    post = whatever enrichment stored (what production actually scored)
Score both and compare.

THE CONTROL IS BUILT IN AND IS THE POINT. 208 of the 254 pairs are articles where
enrichment worked correctly. Those also go short-summary -> long-article, so their
delta is the NORMAL enrichment effect. The 46 disjoint pairs go short-summary ->
WRONG article. If both groups move by the same amount, this measures nothing and
the detector is mislabelling. Only a difference between the groups is evidence.

WHAT THIS IS NOT. It is not a claim about the corpus. il Fatto is one outlet,
Latin-script, chosen because the disjointness detector is valid there. The corpus
rate is NM#306's deliverable, not this one.

#95 NOISE FLOOR, and why the control matters more than the floor here. Batch
composition alone moves a score up to |0.162| on this stack. Everything is scored
in ONE process on ONE box, so cross-box skew (also |0.16|) does not apply, but
batch position still does. A per-pair delta smaller than ~0.16 is therefore not
interpretable on its own -- which is exactly why the comparison is
disjoint-vs-control rather than disjoint-vs-zero.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

REPO = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(REPO))

PAIRS = Path("/tmp/claude-1000/-home-jeroen-repos-veen-systems-llm-distillery/fdc433a8-104a-44c3-81c1-dfcf2dd1378f/scratchpad/fatto_pairs.jsonl")
OUT = Path("/tmp/claude-1000/-home-jeroen-repos-veen-systems-llm-distillery/fdc433a8-104a-44c3-81c1-dfcf2dd1378f/scratchpad/out_306_impact.json")
FILTER_DIR = REPO / "filters/solutions/v6"

from filters.solutions.v6.inference import SolutionsScorer  # noqa: E402


def main() -> None:
    rows = [json.loads(l) for l in PAIRS.open(encoding="utf-8") if l.strip()]
    print(f"pairs: {len(rows)}  (disjoint {sum(r['disjoint'] for r in rows)}, "
          f"control {sum(not r['disjoint'] for r in rows)})")

    scorer = SolutionsScorer(model_path=str(FILTER_DIR / "model"), device="cpu")
    print("scorer loaded")

    def score(title: str, content: str) -> float | None:
        try:
            # skip_prefilter=True mirrors production: the GPU scorer builds every
            # scorer with use_prefilter=False and calls score_batch(skip_prefilter=True).
            r = scorer.score_article({"title": title, "content": content},
                                     skip_prefilter=True)
            return float(r.get("weighted_average"))
        except Exception as exc:  # noqa: BLE001
            print(f"  score failed: {exc}")
            return None

    out = []
    for i, r in enumerate(rows):
        s_pre = score(r["title"], r["pre"])
        s_post = score(r["title"], r["post"])
        if s_pre is None or s_post is None:
            continue
        out.append({
            "id": r["id"], "disjoint": r["disjoint"],
            "title": r["title"][:90],
            "score_true_body": round(s_pre, 4),
            "score_stored_body": round(s_post, 4),
            "delta": round(s_post - s_pre, 4),
            "len_pre": len(r["pre"]), "len_post": len(r["post"]),
        })
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(rows)}")

    def block(name: str, sel) -> dict:
        d = [x["delta"] for x in out if sel(x)]
        a = [abs(v) for v in d]
        tb = [x["score_true_body"] for x in out if sel(x)]
        sb = [x["score_stored_body"] for x in out if sel(x)]
        if not d:
            return {"n": 0}
        res = {
            "n": len(d),
            "median_delta": round(st.median(d), 4),
            "mean_delta": round(st.fmean(d), 4),
            "median_abs_delta": round(st.median(a), 4),
            "pct_abs_gt_noise_floor": round(100.0 * sum(v > 0.16 for v in a) / len(a), 1),
            "median_score_true_body": round(st.median(tb), 4),
            "median_score_stored_body": round(st.median(sb), 4),
        }
        print(f"\n  {name}  n={res['n']}")
        print(f"    score on TRUE body    median {res['median_score_true_body']:.3f}")
        print(f"    score on STORED body  median {res['median_score_stored_body']:.3f}")
        print(f"    delta                 median {res['median_delta']:+.3f}   "
              f"median |delta| {res['median_abs_delta']:.3f}")
        print(f"    |delta| above the 0.16 noise floor: {res['pct_abs_gt_noise_floor']:.1f}%")
        return res

    print("\n" + "=" * 66)
    summary = {
        "filter": "solutions v6",
        "n_scored": len(out),
        "corrupted": block("CORRUPTED (title/body disjoint)", lambda x: x["disjoint"]),
        "control": block("CONTROL (enrichment correct)", lambda x: not x["disjoint"]),
        "caveats": [
            "One outlet (il Fatto), Latin-script. Corpus rate is NM#306's deliverable.",
            "Control is short-summary -> correct-long-article, i.e. the NORMAL "
            "enrichment effect; only a DIFFERENCE between groups is evidence.",
            "#95: batch composition alone moves a score up to |0.162|, so a "
            "per-pair delta under ~0.16 is not interpretable on its own.",
            "Pre-enrichment body is an RSS summary, so it is shorter by design; "
            "length differs in BOTH groups, which is why the control exists.",
        ],
    }
    OUT.write_text(json.dumps({"summary": summary, "rows": out}, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
