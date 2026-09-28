"""Pull the hand-check list for H-HD17: every human_thriving v9 row and 50 random belonging rows
at harm >= 0.5 above the lens op-point, last 12 filtered files per lens (run on sadalsuud).
Seeded PER LENS (random.Random(lens)) so the draw does not depend on argument order — the
2026-09-28 gotcha. Writes TSV to stdout; the committed file IS the output that was read."""
import json, glob, os, random
OP = {'human_thriving': 4.5, 'belonging': 4.0}
N = {'human_thriving': None, 'belonging': 50}
base = os.path.expanduser('~/local_dev/NexusMind/data/filtered')
print('lens\tharm\traw\tsource\ttitle\turl\tverdict(junk/fits)')
for lens, op in OP.items():
    rows = {}
    files = sorted(glob.glob(f'{base}/{lens}/filtered_*.jsonl'))[-12:]
    for f in files:
        for line in open(f):
            try: r = json.loads(line)
            except Exception: continue
            a = r.get('nexus_mind_attributes', {}).get(lens) or {}
            raw = a.get('raw_weighted_average')
            if raw is None or raw < op or a.get('stage_used') == 'stage1_low': continue
            h = r.get('_harm_is_subject_score')
            if h is not None and h >= 0.5:
                t = (r.get('title') or '').replace('\t', ' ').replace('\n', ' ')
                rows[r['id']] = (h, raw, r.get('source', ''), t, r.get('url', ''))
    pick = sorted(rows.values())
    if N[lens] is not None and len(pick) > N[lens]:
        pick = random.Random(lens).sample(pick, N[lens])
    print(f'# {lens}: {len(rows)} rows at harm>=0.5 above {op}; listed {len(pick)}; window '
          f'{os.path.basename(files[0])}..{os.path.basename(files[-1])}')
    for h, raw, src, t, u in sorted(pick, reverse=True):
        print(f'{lens}\t{h:.2f}\t{raw:.2f}\t{src}\t{t}\t{u}\t')
