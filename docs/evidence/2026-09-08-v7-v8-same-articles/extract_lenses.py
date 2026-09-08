"""Per-cycle surfacing (the pipeline's OWN tier field) for the other production lenses."""
import glob, json, os, sys
BASE = "/home/jeroen/local_dev/NexusMind/data/filtered"
# cycle -> filename timestamp prefix to match (date + hour of THIS cycle's run)
CYCLES = {"c1": ("20260907_17", "20260907_18"),
          "c2": ("20260907_21",),
          "c3": ("20260908_01",),
          "c4": ("20260908_05",)}
# ⛔ A HAND-BUILT POPULATION, and it is asserted against the directory rather than trusted.
# A newly enabled lens that is missing from this list is invisible, and its absence INFLATES the
# "carried by no other lens" share §4 is quoted for. `investment_risk` is PAUSED (2026-08-25) and
# writes no new files, so it is expected-present-on-disk but absent from these cycles.
FILTERS = ["nature_recovery", "solutions", "cultural_discovery", "belonging"]
PAUSED = ["investment_risk", "uplifting", "human_thriving"]  # uplifting/human_thriving are the
# two lenses UNDER TEST and are read by extract.py, not here.

on_disk = {d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d))}
expected = set(FILTERS) | set(PAUSED)
if on_disk != expected:
    raise RuntimeError(
        f"the lens set on disk is not the one this script was written for: "
        f"unexpected {sorted(on_disk - expected)}, missing {sorted(expected - on_disk)}. "
        f"A lens missing from FILTERS inflates the 'carried by no other lens' share.")

out = open(sys.argv[1], "w")
for filt in FILTERS:
    d = os.path.join(BASE, filt)
    if not os.path.isdir(d):
        print(f"SKIP {filt}: no directory", file=sys.stderr); continue
    for cycle, prefixes in CYCLES.items():
        hits = sorted(p for p in glob.glob(os.path.join(d, "filtered_*.jsonl"))
                      if any(os.path.basename(p).startswith("filtered_" + pre) for pre in prefixes))
        if len(hits) != 1:
            raise RuntimeError(f"{filt} {cycle}: expected exactly 1 file, got {hits}")
        n = surf = 0
        with open(hits[0]) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                a = r["nexus_mind_attributes"][filt]
                n += 1
                if a["tier"] != "low":
                    surf += 1
                    out.write(json.dumps({"cycle": cycle, "filter": filt, "id": r["id"],
                                          "raw": a["raw_weighted_average"],
                                          "tier": a["tier"]}) + "\n")
        print(f"{filt}\t{cycle}\t{os.path.basename(hits[0])}\tn={n}\tsurfaced={surf}", file=sys.stderr)
out.close()
