import json, sys
from pathlib import Path
SCRATCH = Path("/tmp/claude-1000/-home-jeroen-repos-veen-systems-llm-distillery/96c7f831-6b9e-443a-a955-658f6c98dec6/scratchpad")
IDS = sys.argv[1:]
cohort = {json.loads(l)["id"]: json.loads(l) for l in open(SCRATCH / "phaseA_cohort200.jsonl")}
rows = {}
for arm in ("A", "B"):
    for run in (1, 2, 3):
        for line in open(SCRATCH / f"phaseA_{arm}{run}.jsonl"):
            r = json.loads(line)
            if r["id"] in IDS:
                rows[(r["id"], arm, run)] = r["uplifting_analysis"]
for i in IDS:
    c = cohort[i]
    print("=" * 100)
    print(f"{i}  [{c['stratum']}] {c['language']}  src={c['source']}  {len(c['content'])} chars  v7={c['v7_raw_weighted_average']:.2f}")
    print(f"TITLE: {c['title']}")
    print(f"URL:   {c['url']}")
    print("-" * 100)
    print("CONTENT:")
    print(c["content"])
    print("-" * 100)
    for arm in ("A", "B"):
        for run in (1, 2, 3):
            a = rows[(i, arm, run)]
            print(f"[{arm}{run}] subj={a.get('dominant_subject')!r} verdict={a.get('scope_verdict')}")
            if run == 1:
                # ⛔ The first version of this script hand-listed six dimension names and THREE of
                # them do not exist in this filter (`environmental_stewardship`, `solution_quality`,
                # `narrative_constructiveness`). The `if d in a` guard turned that into a silent
                # under-display -- three real dimensions never printed, no error. The scores in the
                # write-up were never affected (they come from wavg over the imported
                # DIMENSION_NAMES), but a hand-built list of field names is the same defect class
                # as a hand-built population. Import it.
                import sys as _sys
                from pathlib import Path as _P
                _sys.path.insert(0, str(_P(__file__).resolve().parents[3]))
                from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as _S
                for d in _S.DIMENSION_NAMES:
                    if d in a:
                        print(f"      {d}: {a[d]['score']}  | {str(a[d].get('evidence',''))[:220]}")
    print()
