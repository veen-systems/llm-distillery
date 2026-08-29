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
                for d in ("human_wellbeing_impact", "social_cohesion_impact", "environmental_stewardship",
                          "solution_quality", "evidence_level", "narrative_constructiveness"):
                    if d in a:
                        print(f"      {d}: {a[d]['score']}  | {str(a[d].get('evidence',''))[:220]}")
    print()
