"""Where does production scoring wall-time actually go — sadalsuud, the wire, or the GPU?

Asked because the owner believes the e5 probes may be running on sadalsuud and wearing it
out. This splits the pipeline's blocking wall time into measurable layers:

    sadalsuud `[timing] <filter> score`      — what the pipeline blocks for
      >= gpu-server `POST /filter/*/score`   — what the server's own handler took
        >= `Hybrid batch scored N in Ts`     — what the model actually computed

The difference between adjacent layers is the overhead attributable to that layer.

⚠️ NexusMind's `scoring:` config (`require_gpu: true`, `cpu_fallback.enabled: false`,
`host: gpu-server`) says the FILTER path has no CPU branch. ⛔ That is a config read and is
NOT a runtime proof, and it is specifically not a statement about the host: those keys sit
under `scoring:`, and story dedup is a PREPROCESSING stage that never consults them. The
runtime evidence is the layer split below plus the dedup device line — not the config.

⛔ THE TRAPS THIS SCRIPT EXISTS TO PREVENT. Each is a defect that was actually made here, in
this order, and each is now a guard rather than a caveat:

  1. TWO WINDOWS. A first pass compared sadalsuud's `score` total from a THREE-CYCLE window
     (1209.1s / 15 calls) against gpu-server's totals from a TWENTY-HOUR window (1656.8s /
     941 batches) and reported "~62 ms/article of overhead, a 4x multiplier". Matched, the
     multiplier is 1.18x. The per-call rates AGREED across the two windows (80.6 vs 77.5
     s/call), which is exactly why the mismatch was invisible: every check on the pieces
     passed and only the denominators were incomparable.
  2. PARTIAL COVERAGE, which reproduces (1) silently. Filtering gpu lines to `[lo, hi]`
     excludes over-coverage but not UNDER-coverage: if gpu-server's journal begins after
     `lo` (rotation, restart, shorter retention), sadalsuud's totals span the window and
     gpu's span a subset, inflating "client + network" in the same direction as (1) with
     every per-call rate still agreeing. `assert_covers()` below is the guard. Measured
     2026-09-04 on a synthetic pair: 4.80x reported against a true 2.40x.
  3. AN UNGUARDED REGEX. `BATCH` and `TIMING` failures raise; a `RESPONSE` failure used not
     to, so an access-log format change (`[200] 5.900s` instead of `5900.0ms`) gave
     `http = 0` and republished conclusion (1) — the whole of `wall` attributed to the
     client — while exiting 0. Guarded, and the layer nesting is now ASSERTED.
  4. TWO POPULATIONS IN ONE RATIO. `wall` is sadalsuud's; `n` is gpu-server's, and counts
     EVERY caller. A second client on the scorer pushed `http/wall` to 147.5% and the
     multiplier below 1.0 without complaint. The nesting assert catches it.
  5. UNEQUAL DENOMINATORS. Story dedup runs BEFORE the per-filter loop, so the first
     cycle's dedup line precedes the first `[timing]` line and falls outside a window
     anchored on `[timing]`. Comparing 8 cycles of scoring against 7 of dedup is (1) again
     in miniature. Cycles are therefore delimited BY THE DEDUP LINE, so both series share a
     denominator by construction, and unmatched cycles are dropped and reported.

⚠️ WHAT `embed_seconds` IS NOT. The `Centroid migration (#195/#243/#275) … embed_seconds=`
field times ONLY the re-embedding of cluster centroids being drift-checked
(`story_dedup.py::_migrate_drifted_seeds_with_stats`). The run's ARTICLE embedding pass is
untimed and unlogged on the sadalsuud side. So dedup's wall time MINUS `embed_seconds` is
NOT "clustering on sadalsuud CPU" — it still contains the article pass's blocking HTTP wait.
That pass is measured here from the GPU side instead (`POST /embeddings/encode`), which is
the only surface that sees it.

⚠️ Two hosts, two clocks: gpu-server runs UTC, sadalsuud UTC+2. `-o short-iso` on both is
load-bearing — systemd's default `Sep 04 13:27:52` carries no offset, and comparing those
bare local times shifts the window two hours with no error. Needs Python >= 3.11 for
`fromisoformat` on a colonless offset.

    python docs/evidence/2026-09-04-scoring-overhead/measure_scoring_overhead.py \
        --since '36 hours ago' --out overhead.json | tee overhead.txt
"""

import argparse
import collections
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

TIMING = re.compile(r"\[timing\] (\S+) (\S+) ([\d.]+)s")
BATCH = re.compile(
    r"Hybrid batch scored (\d+) articles in ([\d.]+)s: "
    r"prefilter_blocked=(\d+), stage1_low=(\d+), stage2=(\d+)"
)
RESPONSE = re.compile(r"POST (/\S+) \[(\d+)\] ([\d.]+)ms")
SCORE_EP = re.compile(r"^/filter/\S+/score$")
DEDUP = re.compile(r"Story dedup: (\d+) removed \((\d+) clusters, ([\d.]+)s\)")
# ⚠️ Anchored to the migration line, not applied to every record: unanchored, an unrelated
# `embed_seconds=` elsewhere in the journal folded into dedup's total and produced a 120%
# embedding share with a NEGATIVE remainder, exit 0.
DEDUP_MIGRATE = re.compile(r"Centroid migration .*?embed_seconds=([\d.]+)\)")
DEDUP_STORE = re.compile(r"Loaded (\d+) saved clusters for cross-run dedup")
# ⛔ Matches the GPU branch ONLY. The CPU branches log "gpu-server not healthy, will try CPU
# embeddings" / "will use CPU embeddings", neither of which contains "using". So this
# instrument CANNOT say "CPU": a CPU-fallback run reports NOT LOGGED, which reads as "no
# information" and not as a negative. Every device conclusion below states the line COUNT
# against the run count for that reason.
DEDUP_DEVICE = re.compile(r"Story dedup: using (.+?)\s*$")
ISO = re.compile(r"^\d{4}-\d\d-\d\dT")


def journal(host: str, unit: str, since: str, until: str | None) -> list[str]:
    """One unit's journal from one host, as offset-aware ISO lines, deduplicated.

    `-q` suppresses the "not seeing messages from other users" hint, which otherwise lands
    on stdout and is counted as log content. Duplicate records (syslog forwarding, or a
    merged persistent+volatile journal) would double every count and HALVE ms/article
    without any other symptom, so identical lines are collapsed.
    """
    cmd = f"journalctl -u {unit} --since '{since}'"
    if until:
        cmd += f" --until '{until}'"
    cmd += " --no-pager -q -o short-iso"
    try:
        p = subprocess.run(["ssh", "-o", "BatchMode=yes", host, cmd],
                           capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"{host}/{unit}: journalctl did not return within 300 s — "
                         f"--since {since!r} is almost certainly too wide (a broad one "
                         f"streams the whole retained journal over ssh).")
    if p.returncode != 0:
        raise SystemExit(f"{host}: journalctl failed ({p.returncode}): {p.stderr.strip()[:400]}")
    lines = list(dict.fromkeys(l for l in p.stdout.splitlines() if ISO.match(l)))
    if not lines:
        # An empty read and a quiet system are different results, and only one of them
        # means "no overhead". Refuse rather than report zero.
        raise SystemExit(f"{host}/{unit}: no timestamped lines since {since!r} — "
                         f"nothing was measured, which is not the same as nothing happened")
    return lines


def stamp(line: str) -> dt.datetime:
    return dt.datetime.fromisoformat(line.split(" ", 1)[0]).astimezone(dt.timezone.utc)


def assert_covers(label: str, lines: list[str], lo: dt.datetime, hi: dt.datetime) -> tuple:
    """Trap 2. Filtering to a window is not the same as the window being covered."""
    a, b = stamp(lines[0]), stamp(lines[-1])
    if a > lo or b < hi:
        raise SystemExit(
            f"{label} journal covers {a:%Y-%m-%d %H:%M:%S}..{b:%Y-%m-%d %H:%M:%S} UTC but "
            f"the window is {lo:%Y-%m-%d %H:%M:%S}..{hi:%Y-%m-%d %H:%M:%S}. Totals from a "
            f"journal that does not span the window are not comparable with ones that do — "
            f"this is the two-window defect the whole script exists to prevent. Narrow "
            f"--since/--until to what BOTH journals retain.")
    return a, b


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="36 hours ago",
                    help="passed to journalctl on BOTH hosts; the reported window is then "
                         "narrowed to the cycles the pipeline side actually covers")
    ap.add_argument("--until", default=None,
                    help="pin the far edge so a committed run can be re-derived later")
    ap.add_argument("--pipeline-host", default="sadalsuud")
    ap.add_argument("--pipeline-unit", default="nexusmind.service")
    ap.add_argument("--gpu-host", default="gpu-server")
    ap.add_argument("--gpu-unit", default="nexusmind-scorer.service")
    ap.add_argument("--out", type=Path, default=None,
                    help="write the JSON record. WITHOUT THIS NOTHING IS SAVED.")
    args = ap.parse_args()

    pipe = journal(args.pipeline_host, args.pipeline_unit, args.since, args.until)
    gpu = journal(args.gpu_host, args.gpu_unit, args.since, args.until)

    # --- cycles are delimited by the DEDUP line (trap 5) -------------------------------
    dedup_at = [(stamp(l), DEDUP.search(l)) for l in pipe if DEDUP.search(l)]
    timed = [(stamp(l), m) for l in pipe if (m := TIMING.search(l))]
    if not timed:
        raise SystemExit(f"{args.pipeline_host}: no [timing] lines — the pipeline did not "
                         f"run in this window, so there is no wall time to attribute")
    if not dedup_at:
        raise SystemExit(f"{args.pipeline_host}: no 'Story dedup: N removed' lines, so "
                         f"cycles cannot be delimited. Widen --since, or note that shared "
                         f"dedup is skipped when only one filter is enabled.")

    lo = dedup_at[0][0]
    hi = timed[-1][0]
    if hi <= lo:
        raise SystemExit("the last [timing] line precedes the first dedup line — no "
                         "complete cycle in this window")

    gpu_span = assert_covers("gpu-server", gpu, lo, hi)
    pipe_span = assert_covers(args.pipeline_host, pipe, lo, hi)

    stages: dict[str, list] = collections.defaultdict(lambda: [0.0, 0])
    per_filter: dict[str, float] = collections.defaultdict(float)
    for t, m in timed:
        if not (lo <= t <= hi):
            continue
        name, stage, secs = m.group(1), m.group(2), float(m.group(3))
        stages[stage][0] += secs
        stages[stage][1] += 1
        if stage == "score":
            per_filter[name] += secs

    dd = dict(runs=0, seconds=0.0, removed=0, run_clusters=0,
              migrate_embed_seconds=0.0, migrate_runs=0,
              store_loads=0, store_clusters_max=0, device_lines=0)
    devices: set[str] = set()
    for line in pipe:
        t = stamp(line)
        if not (lo <= t <= hi):
            continue
        if (m := DEDUP.search(line)):
            dd["runs"] += 1
            dd["removed"] += int(m.group(1))
            dd["run_clusters"] += int(m.group(2))
            dd["seconds"] += float(m.group(3))
        if (m := DEDUP_MIGRATE.search(line)):
            dd["migrate_runs"] += 1
            dd["migrate_embed_seconds"] += float(m.group(1))
        if (m := DEDUP_STORE.search(line)):
            dd["store_loads"] += 1
            dd["store_clusters_max"] = max(dd["store_clusters_max"], int(m.group(1)))
        if (m := DEDUP_DEVICE.search(line)):
            dd["device_lines"] += 1
            devices.add(m.group(1).strip())

    # --- the inner layers, over the SAME window ----------------------------------------
    g = dict(batches=0, articles=0, compute=0.0, blocked=0, stage1_low=0, stage2=0,
             score_responses=0, score_ms=0.0, non200=0,
             embedding_loads=0, filter_unloads=0, gpu_frees=0)
    other_ep: dict[str, list] = collections.defaultdict(lambda: [0, 0.0])
    slowest = (0.0, "")
    for line in gpu:
        if not (lo <= stamp(line) <= hi):
            continue
        if (m := BATCH.search(line)):
            g["batches"] += 1
            g["articles"] += int(m.group(1))
            g["compute"] += float(m.group(2))
            g["blocked"] += int(m.group(3))
            g["stage1_low"] += int(m.group(4))
            g["stage2"] += int(m.group(5))
        if (m := RESPONSE.search(line)):
            ep, code, ms = m.group(1), m.group(2), float(m.group(3))
            if SCORE_EP.match(ep):
                if code == "200":
                    g["score_responses"] += 1
                    g["score_ms"] += ms
                else:
                    g["non200"] += 1
                if ms > slowest[0]:
                    slowest = (ms, ep)
            else:
                other_ep[ep][0] += 1
                other_ep[ep][1] += ms
        g["embedding_loads"] += "Embedding model loaded:" in line
        g["filter_unloads"] += "Unloaded filter:" in line
        g["gpu_frees"] += "GPU memory freed" in line

    if not g["articles"]:
        raise SystemExit(
            "gpu-server logged no scored articles inside the window. Coverage was already "
            "asserted, so this is NOT a clock problem: either --gpu-unit is wrong, the "
            "scorer was down, or every cycle here scored zero articles (which still emits "
            "[timing] lines).")
    if not g["score_responses"]:
        raise SystemExit(
            "no `POST /filter/*/score [200] <n>ms` lines matched, though batches were "
            "scored — the access-log format has changed. Without this the whole of `wall` "
            "is attributed to the client, which is exactly the retracted conclusion.")

    n = g["articles"]
    wall = stages["score"][0]
    http = g["score_ms"] / 1000
    compute = g["compute"]
    span = (hi - lo).total_seconds()

    # Trap 4: the layers must nest. `wall` is sadalsuud's population, `http`/`compute` are
    # gpu-server's and count every caller, so this is not an identity — it is a test.
    if not (compute <= http <= wall):
        raise SystemExit(
            f"the layers do not nest: compute {compute:.1f}s <= http {http:.1f}s <= wall "
            f"{wall:.1f}s is false. Something other than this pipeline is using the "
            f"scorer, or a regex is matching the wrong lines. Every derived figure below "
            f"would be meaningless.")

    cycles = dd["runs"]
    n_filters = len(per_filter)
    score_cycles = stages["score"][1] / n_filters if n_filters else 0

    print(f"window  {lo:%Y-%m-%d %H:%M:%S} -> {hi:%Y-%m-%d %H:%M:%S} UTC   {span/3600:.2f} h")
    print(f"  delimited by the dedup line, so `score` and dedup share a denominator")
    print(f"  {args.pipeline_host} journal {pipe_span[0]:%m-%d %H:%M} .. "
          f"{pipe_span[1]:%m-%d %H:%M}   gpu-server {gpu_span[0]:%m-%d %H:%M} .. "
          f"{gpu_span[1]:%m-%d %H:%M}  (both cover it)")
    print(f"  {cycles} dedup-delimited cycles, {stages['score'][1]} score calls over "
          f"{n_filters} filters = {score_cycles:.2f} score cycles\n")

    print("WHERE THE SCORING WALL TIME GOES")
    print(f"  {'sadalsuud blocks on score':<34} {wall:9.1f}s  {wall/n*1000:7.2f} ms/article")
    print(f"  {'gpu-server HTTP handler':<34} {http:9.1f}s  {http/n*1000:7.2f} ms/article"
          f"   ({http/wall:.1%} of it)")
    print(f"  {'model compute (hybrid batch)':<34} {compute:9.1f}s  "
          f"{compute/n*1000:7.2f} ms/article   ({compute/wall:.1%} of it)")
    print(f"  {'-> client + network':<34} {wall-http:9.1f}s  "
          f"{(wall-http)/n*1000:7.2f} ms/article")
    print(f"  {'-> in-server, non-compute':<34} {http-compute:9.1f}s  "
          f"{(http-compute)/n*1000:7.2f} ms/article")
    print(f"  multiplier sadalsuud-wall / compute = {wall/compute:.2f}x\n")

    print(f"THROUGHPUT   {n:,} articles, {g['batches']} batches, {g['score_responses']} 200s"
          + (f", {g['non200']} non-200" if g["non200"] else ", 0 non-200"))
    print(f"  prefilter_blocked {g['blocked']:>6,} ({g['blocked']/n:6.2%})")
    print(f"  stage1_low        {g['stage1_low']:>6,} ({g['stage1_low']/n:6.2%})   "
          f"<- the DEPLOYED FLEET's screens, not any one filter's")
    print(f"  stage2            {g['stage2']:>6,} ({g['stage2']/n:6.2%})\n")

    print("CHURN — the model is not held resident between filters")
    print(f"  embedding-model loads {g['embedding_loads']}, filter unloads "
          f"{g['filter_unloads']}, GPU memory frees {g['gpu_frees']}")
    print(f"  slowest single /filter/*/score response: {slowest[0]:.1f}ms ({slowest[1]})")

    # --- every OTHER consumer of the same GPU, named rather than left out --------------
    print("\nOTHER CONSUMERS OF gpu-server IN THIS WINDOW — not part of `score` above")
    if other_ep:
        for ep, (cnt, ms) in sorted(other_ep.items(), key=lambda kv: -kv[1][1]):
            print(f"  {ep:<28} {cnt:5d} calls {ms/1000:9.1f}s")
    else:
        print("  none logged")

    print("\nTHE OTHER CONSUMER ON sadalsuud — story dedup, same window, same cycles")
    emb = dd["migrate_embed_seconds"]
    print(f"  {'story dedup wall':<34} {dd['seconds']:9.1f}s over {dd['runs']} runs"
          f"  = {dd['seconds']/dd['runs']:.1f}s/cycle")
    print(f"  {'  centroid re-embedding':<34} {emb:9.1f}s  ({emb/dd['seconds']:.1%})"
          f"  <- goes to gpu-server")
    print(f"  {'  everything else':<34} {dd['seconds']-emb:9.1f}s  "
          f"({1-emb/dd['seconds']:.1%})")
    print(f"  ⛔ 'everything else' is NOT all sadalsuud CPU. The ARTICLE embedding pass is")
    print(f"     untimed on this side; it appears above as POST /embeddings/encode. Subtract")
    print(f"     that before calling any remainder clustering.")
    print(f"  embedding device: {', '.join(sorted(devices)) or 'NOT LOGGED'} "
          f"({dd['device_lines']} device lines over {dd['runs']} runs"
          + ("; every run stated it" if dd["device_lines"] >= dd["runs"]
             else " — NOT every run stated it, so this is not an every-run claim") + ")")
    print(f"  cross-run store: {dd['store_clusters_max']:,} saved clusters (max over "
          f"{dd['store_loads']} loads); {dd['run_clusters']:,} clusters formed in-run")
    if dd["migrate_runs"] != dd["runs"]:
        print(f"  ⚠️ {dd['migrate_runs']} centroid-migration lines against {dd['runs']} "
              f"dedup runs — the embedding share is over an unmatched denominator")

    # --- the derived block, PRINTED rather than hand-computed in prose ------------------
    other_s = sum(v[0] for k, v in stages.items() if k != "score")
    total = wall + dd["seconds"] + other_s
    print("\nDERIVED — printed here so no document has to recompute it by hand")
    print(f"  pipeline blocking total   {total:9.1f}s = score {wall:.1f} + dedup "
          f"{dd['seconds']:.1f} + other stages {other_s:.1f}")
    print(f"  duty cycle over the window {total/span:8.2%}")
    print(f"  shares: score {wall/total:.1%}  dedup {dd['seconds']/total:.1%}  "
          f"other {other_s/total:.1%}")
    print(f"  score {wall/60:.1f} min/window; floor if ALL in-server non-compute vanished "
          f"{(compute+(wall-http))/60:.1f} min (saving {(http-compute)/60:.1f} min)")
    print(f"  per cycle: score {wall/cycles:.1f}s  dedup {dd['seconds']/cycles:.1f}s  "
          f"ratio {wall/dd['seconds']:.2f}x")
    print("\n  other stages, in full (a stage reading 0.0s is rounded, not proven zero):")
    for k, (secs, cnt) in sorted(stages.items(), key=lambda kv: -kv[1][0]):
        if k != "score":
            print(f"    {k:<16} {secs:8.1f}s  n={cnt}")

    print("\n  per-filter share of sadalsuud's blocking score time:")
    for name, secs in sorted(per_filter.items(), key=lambda kv: -kv[1]):
        print(f"    {name:<24} {secs:8.1f}s  {secs/wall:6.1%}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "window_utc": [lo.isoformat(), hi.isoformat()], "span_hours": span / 3600,
            "since_arg": args.since, "until_arg": args.until,
            "journal_coverage": {"pipeline": [pipe_span[0].isoformat(), pipe_span[1].isoformat()],
                                 "gpu": [gpu_span[0].isoformat(), gpu_span[1].isoformat()]},
            "cycles": cycles, "score_calls": stages["score"][1], "filters": n_filters,
            "pipeline": {"stages": {k: {"seconds": v[0], "n": v[1]} for k, v in stages.items()},
                         "score_by_filter": dict(per_filter)},
            "gpu": g,
            "gpu_other_endpoints": {k: {"calls": v[0], "seconds": v[1] / 1000}
                                    for k, v in other_ep.items()},
            "story_dedup": {**dd, "devices_logged": sorted(devices)},
            "derived": {"wall_s": wall, "http_s": http, "compute_s": compute,
                        "other_stages_s": other_s, "pipeline_total_s": total,
                        "duty_cycle": total / span,
                        "share_score": wall / total, "share_dedup": dd["seconds"] / total,
                        "share_other": other_s / total,
                        "ms_per_article": {"wall": wall / n * 1000, "http": http / n * 1000,
                                           "compute": compute / n * 1000},
                        "multiplier_wall_over_compute": wall / compute,
                        "score_over_dedup": wall / dd["seconds"]},
        }, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())
