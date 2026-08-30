import json, glob, os
BASE = os.path.expanduser("~/local_dev/NexusMind/data/filtered")
IDS = {"dutch_news_welingelichtekringen_760a0a956413",
       "industry_intelligence_fast_company_5510f1117e34",
       "austrian_die_presse_politik_90fe990b80ef",
       "vietnamese_vnexpress_vn_c293336fd7bd"}
out = {}
for lens in ("uplifting", "solutions", "nature_recovery", "cultural_discovery", "belonging"):
    for fp in sorted(glob.glob(os.path.join(BASE, lens, "filtered_*.jsonl"))):
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                if not any(i in line for i in IDS):
                    continue
                d = json.loads(line)
                if d.get("id") not in IDS:
                    continue
                a = (d.get("nexus_mind_attributes") or {}).get(lens, {})
                r = out.setdefault(d["id"], {
                    "title": d.get("title"), "url": d.get("url"), "lang": d.get("language"),
                    "source": d.get("source"), "pub": d.get("published_date"),
                    "content_len": len(d.get("content") or ""),
                    "native": a.get("original_content_length") if a.get("pre_enriched") else a.get("content_length"),
                    "pre_enriched": a.get("pre_enriched"),
                    "flags": {"obit": d.get("_is_obituary"), "viol": d.get("_is_violence_promotion"),
                              "comm": d.get("_is_commerce"), "quality": (d.get("content_quality") or {}).get("pass")},
                    "content": (d.get("content") or "")[:1100], "lenses": {}})
                r["lenses"][lens] = {"raw": round(a.get("raw_weighted_average", -1), 4),
                                     "norm": a.get("weighted_average"), "tier": a.get("tier"),
                                     "stage": a.get("stage_used"), "cycle": os.path.basename(fp),
                                     "version": a.get("version")}
for k, v in out.items():
    print("=" * 100)
    print(k)
    print(" ", v["title"], "|", v["lang"], "|", v["source"])
    print("  native", v["native"], "enriched", v["content_len"], "pre_enriched", v["pre_enriched"], "flags", v["flags"])
    print("  pub", v["pub"], "url", v["url"])
    for L, s in v["lenses"].items():
        print(f"   {L:20s} v{s['version']:4s} raw {s['raw']:8.4f} norm {s['norm']} tier {s['tier']:14s} {s['stage']} {s['cycle']}")
    print("  CONTENT:", v["content"].replace("\n", " | ")[:1100])
