"""Live obituary-detector behaviour by SCRIPT, over production rows the pipeline already
stamped. Window 2026-08-26..2026-09-10, data/raw/content_items_*.jsonl (stamped in place by
ObituaryPreprocessor, which drops nothing -- so this is every loaded article, not survivors).

⚠️ THIS CANNOT PROVE A DEFECT. Flag rate confounds detector behaviour with the true
obituary base rate, which plausibly differs by region and source mix. The discriminator that
is NOT confounded that way is the upper tail: if the detector can see obituaries in a script
at all, SOME articles in it should score high. A script whose maximum score over thousands of
articles stays low is blind, not merely low-base-rate.
"""
import json, glob, os, re, collections

RANGES = [("Latin",(0x41,0x5A),(0x61,0x7A),(0xC0,0x24F)), ("Greek",(0x370,0x3FF),(0x1F00,0x1FFF)),
          ("Cyrillic",(0x400,0x4FF)), ("Hebrew",(0x590,0x5FF)), ("Arabic",(0x600,0x6FF),(0x750,0x77F)),
          ("Devanagari",(0x900,0x97F)), ("Hangul",(0xAC00,0xD7AF),(0x1100,0x11FF)),
          ("Kana",(0x3040,0x30FF)), ("Han",(0x4E00,0x9FFF)), ("Thai",(0xE00,0xE7F)),
          ("Armenian",(0x530,0x58F))]
def dom_script(t):
    c = collections.Counter()
    for ch in t[:400]:
        o = ord(ch)
        for row in RANGES:
            if any(a <= o <= b for a, b in row[1:]):
                c[row[0]] += 1; break
    return c.most_common(1)[0][0] if c else "NONE"

files = sorted(glob.glob(os.path.expanduser("~/local_dev/NexusMind/data/raw/content_items_*.jsonl")))
by = collections.defaultdict(list)
unstamped = 0
for f in files:
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        s = r.get("_obituary_score")
        if s is None: unstamped += 1; continue
        by[dom_script((r.get("title") or "") + " " + (r.get("content") or ""))].append(float(s))

def pct(sorted_v, q):
    if not sorted_v: return 0.0
    i = min(len(sorted_v)-1, max(0, int(round(q/100*(len(sorted_v)-1)))))
    return sorted_v[i]
def rate(v, th): return sum(1 for x in v if x >= th)/len(v) if v else 0.0

print(f"unstamped rows skipped: {unstamped}\n")
print(f"{'script':<12}{'n':>8}{'share':>8}{'flag@0.85':>11}{'>=0.5':>8}{'p50':>8}{'p90':>8}{'p99':>8}{'max':>8}")
tot = sum(len(v) for v in by.values())
for s, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
    a = sorted(v)
    print(f"{s:<12}{len(a):>8}{100*len(a)/tot:>7.2f}%{100*rate(a,0.85):>10.3f}%"
          f"{100*rate(a,0.5):>7.2f}%{pct(a,50):>8.4f}{pct(a,90):>8.4f}"
          f"{pct(a,99):>8.4f}{a[-1]:>8.4f}")
lat = sorted(by["Latin"]); non = sorted(x for k,v in by.items() if k not in ("Latin","NONE") for x in v)
print(f"\nLatin      n={len(lat):>7}  flag@0.85 {100*rate(lat,0.85):.3f}%  p99 {pct(lat,99):.4f}")
print(f"non-Latin  n={len(non):>7}  flag@0.85 {100*rate(non,0.85):.3f}%  p99 {pct(non,99):.4f}")
print(f"ratio of flag rates (Latin / non-Latin): {(rate(lat,0.85)/max(rate(non,0.85),1e-12)):.2f}x")
json.dump({s: {"n": len(v), "flag_rate": rate(sorted(v),0.85),
               "p99": pct(sorted(v),99), "max": max(v)} for s,v in by.items()},
          open(os.path.expanduser("~/obit_by_script.json"),"w"), indent=1)
