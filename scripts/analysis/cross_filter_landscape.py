"""Cross-filter landscape analysis: dedup scenarios for ovr.news tabs.

Tab names are English per ADR-013 (renamed 2026-10-07, LD#160; the old names are mapped in ADR-009's note):
Thriving (scored by uplifting), Solutions (sustainability_technology), Discovery (cultural-discovery).
"""
import json
import numpy as np
from collections import defaultdict

THRESHOLD = 4.0

def load_training_scores(base_dir):
    scores = {}
    for split in ['train.jsonl', 'val.jsonl', 'test.jsonl']:
        try:
            with open(f'{base_dir}/{split}', encoding='utf-8') as f:
                for line in f:
                    a = json.loads(line)
                    url = a.get('url', '')
                    if url:
                        scores[url] = float(np.mean(a['labels']))
        except FileNotFoundError:
            pass
    return scores

def load_belonging():
    dims = ['intergenerational_bonds', 'community_fabric', 'reciprocal_care',
            'rootedness', 'purpose_beyond_self', 'slow_presence']
    weights = [0.25, 0.25, 0.10, 0.15, 0.15, 0.10]
    scores = {}
    with open('datasets/belonging/belonging_all_scored.jsonl', encoding='utf-8') as f:
        for line in f:
            a = json.loads(line)
            url = a.get('url', a.get('link', ''))
            if not url:
                continue
            ba = a['belonging_analysis']
            vals = [ba[d]['score'] for d in dims]
            scores[url] = float(np.dot(vals, weights))
    return scores

def get_passing(url, filter_dict):
    passing = {}
    for name, scores in filter_dict.items():
        if url in scores and scores[url] >= THRESHOLD:
            passing[name] = scores[url]
    return passing

def vol_ratio(vals):
    return max(vals) / max(min(vals), 1)

def main():
    upl = load_training_scores('datasets/training/uplifting_v6')
    sus = load_training_scores('datasets/training/sustainability_technology_v3')
    cul = load_training_scores('datasets/training/cultural-discovery_v4')
    bel = load_belonging()

    filters_3 = {'thriving': upl, 'solutions': sus, 'discovery': cul}
    filters_4 = {'thriving': upl, 'solutions': sus, 'discovery': cul, 'belonging': bel}
    all_urls = set(upl) | set(sus) | set(cul) | set(bel)

    w_total = sum(1 for s in upl.values() if s >= THRESHOLD)
    e_total = sum(1 for s in cul.values() if s >= THRESHOLD)
    v_total = sum(1 for s in sus.values() if s >= THRESHOLD)
    b_total = sum(1 for s in bel.values() if s >= THRESHOLD)

    # ============================================================
    print('=' * 70)
    print('CURRENT STATE (3 tabs, no dedup)')
    print('=' * 70)
    print()
    for tab in ['thriving', 'solutions', 'discovery']:
        f = filters_3[tab]
        mp = sum(1 for s in f.values() if s >= THRESHOLD)
        high = sum(1 for s in f.values() if s >= 7.0)
        print(f'  {tab:>12s}: {mp:>4d} MEDIUM+, {high:>3d} HIGH')

    print()
    print('Articles on multiple tabs:')
    multi = defaultdict(int)
    for url in all_urls:
        p = get_passing(url, filters_3)
        if len(p) > 1:
            key = ' + '.join(sorted(p.keys()))
            multi[key] += 1
    for combo, count in sorted(multi.items(), key=lambda x: -x[1]):
        print(f'  {combo}: {count}')

    # ============================================================
    print()
    print('=' * 70)
    print('SCENARIO 1: 3 tabs + dedup (suppress thriving duplicates)')
    print('=' * 70)
    print('Rule: if MEDIUM+ on thriving AND another tab, remove from thriving')
    print()

    s1_thriving = 0
    s1_moved = defaultdict(int)
    for url in all_urls:
        p = get_passing(url, filters_3)
        if 'thriving' in p:
            others = [t for t in p if t != 'thriving']
            if others:
                best = max(others, key=lambda t: p[t])
                s1_moved[best] += 1
            else:
                s1_thriving += 1

    print(f'  thriving: {w_total} -> {s1_thriving} (moved {w_total - s1_thriving})')
    for tab, count in sorted(s1_moved.items(), key=lambda x: -x[1]):
        print(f'    -> {tab}: +{count}')
    print(f'  discovery: {e_total} (unchanged)')
    print(f'  solutions: {v_total} (unchanged)')

    # ============================================================
    print()
    print('=' * 70)
    print('SCENARIO 2: 4 tabs + dedup (belonging added)')
    print('=' * 70)
    print('Rule: if MEDIUM+ on thriving AND any other tab, remove from thriving')
    print()

    s2_thriving = 0
    s2_moved = defaultdict(int)
    for url in all_urls:
        p = get_passing(url, filters_4)
        if 'thriving' in p:
            others = [t for t in p if t != 'thriving']
            if others:
                best = max(others, key=lambda t: p[t])
                s2_moved[best] += 1
            else:
                s2_thriving += 1

    bel_not_thriving = sum(
        1 for url in bel
        if bel[url] >= THRESHOLD and (url not in upl or upl[url] < THRESHOLD)
    )

    print(f'  thriving: {w_total} -> {s2_thriving} (moved {w_total - s2_thriving})')
    for tab, count in sorted(s2_moved.items(), key=lambda x: -x[1]):
        print(f'    -> {tab}: +{count}')
    print(f'  discovery: {e_total} (unchanged)')
    print(f'  solutions: {v_total} (unchanged)')
    print(f'  belonging: {b_total} total MEDIUM+')
    print(f'    of which NOT also thriving MEDIUM+: {bel_not_thriving}')

    # ============================================================
    print()
    print('=' * 70)
    print('VOLUME COMPARISON')
    print('=' * 70)
    print()
    fmt = '{:>40s}  {:>6s} {:>6s} {:>6s} {:>6s}  {:>6s}'
    print(fmt.format('Scenario', 'thrv', 'disc', 'solu', 'belo', 'ratio'))

    print(f'{"Current (3 tabs, no dedup)":>40s}  {w_total:>6d} {e_total:>6d} {v_total:>6d} {"--":>6s}  {vol_ratio([w_total,e_total,v_total]):>5.1f}x')
    print(f'{"3 tabs + dedup":>40s}  {s1_thriving:>6d} {e_total:>6d} {v_total:>6d} {"--":>6s}  {vol_ratio([s1_thriving,e_total,v_total]):>5.1f}x')
    print(f'{"4 tabs + dedup":>40s}  {s2_thriving:>6d} {e_total:>6d} {v_total:>6d} {b_total:>6d}  {vol_ratio([s2_thriving,e_total,v_total,b_total]):>5.1f}x')
    print()
    print('(ratio = max/min article count, lower = more balanced)')

    # ============================================================
    print()
    print('=' * 70)
    print('MEDIUM+ YIELD RATES')
    print('=' * 70)
    print()
    for name, f in [('thriving', upl), ('solutions', sus), ('discovery', cul), ('belonging', bel)]:
        total = len(f)
        mp = sum(1 for s in f.values() if s >= THRESHOLD)
        pct = 100 * mp / total if total > 0 else 0
        print(f'  {name:>12s}: {mp:>5d}/{total:>5d} = {pct:.1f}% MEDIUM+ rate')

    # ============================================================
    print()
    print('=' * 70)
    print('WHAT THRIVING BECOMES AFTER 4-TAB DEDUP')
    print('=' * 70)
    print()

    thriving_only_urls = set()
    thriving_shared_urls = set()
    for url in upl:
        if upl[url] < THRESHOLD:
            continue
        p = get_passing(url, filters_4)
        others = [t for t in p if t != 'thriving']
        if not others:
            thriving_only_urls.add(url)
        else:
            thriving_shared_urls.add(url)

    # Load dimension data
    thriving_dims = {}
    upl_dim_names = None
    for split in ['train.jsonl', 'val.jsonl', 'test.jsonl']:
        try:
            with open(f'datasets/training/uplifting_v6/{split}', encoding='utf-8') as f:
                for line in f:
                    a = json.loads(line)
                    url = a.get('url', '')
                    if url:
                        thriving_dims[url] = a['labels']
                        if upl_dim_names is None:
                            upl_dim_names = a['dimension_names']
        except FileNotFoundError:
            pass

    print(f'Thriving-only (stays): {len(thriving_only_urls)}')
    print(f'Thriving-shared (moved): {len(thriving_shared_urls)}')
    print()

    fmt2 = '{:>30s}  {:>6s}  {:>6s}  {:>6s}'
    print(fmt2.format('Uplifting dimension', 'Stays', 'Moved', 'Diff'))
    for i, dim in enumerate(upl_dim_names):
        only_vals = [thriving_dims[u][i] for u in thriving_only_urls if u in thriving_dims]
        shared_vals = [thriving_dims[u][i] for u in thriving_shared_urls if u in thriving_dims]
        o_mean = np.mean(only_vals) if only_vals else 0
        s_mean = np.mean(shared_vals) if shared_vals else 0
        diff = o_mean - s_mean
        marker = ' <--' if abs(diff) > 0.3 else ''
        print(f'{dim:>30s}  {o_mean:>6.2f}  {s_mean:>6.2f}  {diff:>+5.2f}{marker}')

    only_scores = [upl[u] for u in thriving_only_urls]
    shared_scores = [upl[u] for u in thriving_shared_urls]
    print()
    print('Score distribution:')
    print(f'  Stays:  mean={np.mean(only_scores):.2f}, median={np.median(only_scores):.2f}, HIGH(>=7): {sum(1 for s in only_scores if s >= 7.0)}')
    print(f'  Moved:  mean={np.mean(shared_scores):.2f}, median={np.median(shared_scores):.2f}, HIGH(>=7): {sum(1 for s in shared_scores if s >= 7.0)}')

if __name__ == '__main__':
    main()
