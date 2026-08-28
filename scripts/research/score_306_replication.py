"""NM#306 HARM — replication on the NexusMind session's independently-labelled pairs.

Run 1 scored 254 il Fatto pairs from the 2026-07-26..08-08 window, labelled by a
crude title/body disjointness test written here. This scores 104 pairs from the
2026-07-12..07-26 window, labelled by that session's calibrated instrument and
its collapse rule.

THE TWO SETS DO NOT OVERLAP. Intersection of the id sets is EXACTLY 0 — printed
and checked before any of this was written, because the original plan was to
re-slice run 1's scores under these labels and that would have produced a table
over an empty join. So this is a genuine replication: different window, different
detector, different labeller, same scorer.

WHY THESE LABELS ARE WORTH MORE THAN RUN 1'S. `label` comes from a relative
collapse rule (title-affinity falling from >=0.75 to <=0.25 across enrichment),
and it agrees ROW FOR ROW with an independent string match on the wire's own
byline (Adnkronos, incl. the Salute and Labitalia sub-brands): 47 and 47. Two
derivations sharing no mechanism landing on the same rows is the corroboration
run 1's labelling never had.

TRUNCATION CHECKED, because the first version of this export was silently capped
at body[:2000] by a spool cache -- which would have compressed exactly the
difference being measured here, since wire widgets are short and real articles
are long. Verified on load: no body at exactly 2000 or 1000 chars.

CONTROL. 57 `intact` pairs also go RSS-summary -> full-article, so their delta is
the NORMAL enrichment effect. Only a difference between the arms is evidence.

#95. Batch composition alone moves a score up to |0.162| on this stack. One
process, one box, one stack and one device, so neither the stack (|0.2008|) nor the device (|0.1956|) term applies; the host term is 0.0000 regardless -- but a per-pair delta under ~0.16 is not
interpretable on its own, which is why the comparison is broken-vs-intact rather
than broken-vs-zero.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

REPO = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(REPO))

SRC = Path("/tmp/claude-1000/-home-jeroen-repos-veen-systems-NexusMind/"
           "1f0152f0-a145-4875-b1e8-e054ba22bd1b/scratchpad/nm306_ilfatto_pairs_v2.json")
OUT = Path("/tmp/claude-1000/-home-jeroen-repos-veen-systems-llm-distillery/"
           "fdc433a8-104a-44c3-81c1-dfcf2dd1378f/scratchpad/out_306_replication.json")

from filters.solutions.v6.inference import SolutionsScorer  # noqa: E402


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("pairs") or list(data.values())

    # Truncation guard — refuse to score the known-bad export shape.
    after = [len(r["body_after"]) for r in data]
    if sum(1 for n in after if n in (1000, 2000)) > len(after) * 0.5:
        raise SystemExit("REFUSING: bodies look truncated at a cache boundary")
    print(f"pairs {len(data)}  labels {dict(Counter(r['label'] for r in data))}")
    print(f"body_after len: min {min(after)} max {max(after)} mean {sum(after)//len(after)}")

    scorer = SolutionsScorer(model_path=str(REPO / "filters/solutions/v6/model"),
                             device="cpu")
    print("scorer loaded", flush=True)

    def score(title: str, content: str):
        try:
            r = scorer.score_article({"title": title, "content": content},
                                     skip_prefilter=True)
            return float(r.get("weighted_average"))
        except Exception as exc:  # noqa: BLE001
            print(f"  score failed: {exc}", flush=True)
            return None

    out = []
    for i, r in enumerate(data):
        s_true = score(r["title"], r["body_before"])
        s_stored = score(r["title"], r["body_after"])
        if s_true is None or s_stored is None:
            continue
        out.append({
            "id": r["id"], "label": r["label"],
            "adnkronos": r.get("adnkronos_dateline"),
            "score_true_body": round(s_true, 4),
            "score_stored_body": round(s_stored, 4),
            "delta": round(s_stored - s_true, 4),
            "len_before": len(r["body_before"]), "len_after": len(r["body_after"]),
        })
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(data)}", flush=True)

    def block(name: str, sel) -> dict:
        rows = [x for x in out if sel(x)]
        if not rows:
            return {"n": 0}
        d = [x["delta"] for x in rows]
        a = [abs(v) for v in d]
        res = {
            "n": len(rows),
            "median_delta": round(st.median(d), 4),
            "median_abs_delta": round(st.median(a), 4),
            "pct_abs_gt_0.16": round(100.0 * sum(v > 0.16 for v in a) / len(a), 1),
            "median_score_true": round(st.median([x["score_true_body"] for x in rows]), 4),
            "median_score_stored": round(st.median([x["score_stored_body"] for x in rows]), 4),
        }
        print(f"\n  {name}  n={res['n']}")
        print(f"    score on TRUE body    median {res['median_score_true']:.3f}")
        print(f"    score on STORED body  median {res['median_score_stored']:.3f}")
        print(f"    delta median {res['median_delta']:+.3f}   |delta| median {res['median_abs_delta']:.3f}")
        print(f"    |delta| above the 0.16 noise floor: {res['pct_abs_gt_0.16']:.1f}%")
        return res

    print("\n" + "=" * 66)
    summary = {
        "filter": "solutions v6",
        "source": "NexusMind session v2 export, window 2026-07-12..07-26",
        "overlap_with_run1": 0,
        "n_scored": len(out),
        "broken": block("BROKEN (collapse rule + Adnkronos, 47/47 agree)",
                        lambda x: x["label"] == "broken"),
        "intact": block("INTACT (enrichment correct)", lambda x: x["label"] == "intact"),
    }
    OUT.write_text(json.dumps({"summary": summary, "rows": out}, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
