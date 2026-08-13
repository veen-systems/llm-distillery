"""Recompute the NM#284 observed-vs-declared pass rate, without the scorer's log.

Valid population argument: the per-lens prefilter has never run in production, so
every row in data/filtered/ reached scoring regardless of what the lens rules would
have said. Asking "what WOULD these rules have blocked?" over that population is
exactly the shadow question. Caveat stated in the output: filtered files also drop
source-type-excluded rows, so the population is "scored AND not source-excluded".
"""
import json, glob, importlib.util, sys, yaml
from pathlib import Path

REPO = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(REPO))
LIVE = [("solutions","v6"),("uplifting","v7"),("cultural_discovery","v5"),
        ("cultural_discovery","v6"),("investment_risk","v6"),("belonging","v1"),
        ("nature_recovery","v4")]

def load_pf(name, ver):
    p = REPO/"filters"/name/ver/"prefilter.py"
    if not p.exists(): return None
    spec = importlib.util.spec_from_file_location(f"pf_{name}_{ver}", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    cls = [o for n,o in vars(m).items()
           if isinstance(o,type) and "PreFilter" in n and o.__module__==m.__name__]
    return cls[0]() if cls else None

def declared(name, ver):
    c = yaml.safe_load(open(REPO/"filters"/name/ver/"config.yaml", encoding="utf-8"))
    v = (c.get("prefilter") or {}).get("expected_pass_rate")
    if v is None: return None
    try: return float(v)
    except (TypeError, ValueError): return ("UNPARSEABLE", v)

import argparse
_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--population", default="/tmp/shadow_articles.json",
                 help="JSON list of {id,title,content}, extracted from a cycle's filtered file")
_args = _ap.parse_args()
ART = json.load(open(_args.population))
print(f"population: {len(ART)} articles from the most recent cycle's filtered files\n")
print(f"{'filter':24} {'declared':>9} {'observed':>9} {'delta':>8}  {'blocked':>7}  top reason")
print("-"*88)
rows=[]
for name, ver in LIVE:
    pf = load_pf(name, ver)
    if pf is None:
        print(f"{name+'/'+ver:24} {'—':>9} {'NO PREFILTER':>9}"); continue
    passed=0; reasons={}
    for a in ART:
        try: ok, why = pf.apply_filter(a)
        except Exception as e: ok, why = None, f"error:{type(e).__name__}"
        if ok: passed+=1
        else: reasons[why]=reasons.get(why,0)+1
    obs = passed/len(ART)
    dec = declared(name, ver)
    top = max(reasons.items(), key=lambda kv: kv[1])[0] if reasons else "—"
    if isinstance(dec, tuple):
        d, ds, dec = "n/a", f"str:{str(dec[1])[:12]}", None
    elif dec is None:
        d, ds = "n/a", "absent"
    else:
        d, ds = f"{obs-dec:+.3f}", f"{dec:.2f}"
    print(f"{name+'/'+ver:24} {ds:>9} {obs:>9.4f} {d:>8}  {len(ART)-passed:>7}  {top}")
    rows.append({"filter":f"{name}/{ver}","declared":dec,"observed":round(obs,4),
                 "blocked":len(ART)-passed,"reasons":reasons})
json.dump(rows, open("/tmp/shadow_result.json","w"), indent=1)
print("\nCAVEAT: filtered files also drop source-type-excluded rows, so this population")
print("is 'scored AND not source-excluded', not 'everything collected'.")
