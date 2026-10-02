"""Raw-score bands and language mix of the belonging passers, from bel_month.py's per-row output.

    python3 passer_bands.py bel_month.tsv > passer_bands.txt

bel_month.tsv (written to /tmp on sadalsuud) is NOT committed: it carries urls and titles of 14,850 rows.
Column 5 = language, column 6 = raw_weighted_average (stage2, raw >= 4.0, one row per distinct id).
"""
import sys, collections
rows = [l.rstrip('\n').split('\t') for l in open(sys.argv[1])]
raw = [float(r[5]) for r in rows]
print(f'rows {len(rows)}')
bands = [(4, 4.5), (4.5, 5), (5, 5.5), (5.5, 5.77), (5.77, 6), (6, 7), (7, 8), (8, 11)]
for a, b in bands:
    n = sum(a <= x < b for x in raw)
    print(f'raw {a}-{b}\t{n}\t{n/len(raw):.1%}')
for t in (5.5, 5.77, 7):
    n = sum(x < t for x in raw)
    print(f'raw < {t}\t{n}\t{n/len(raw):.1%}')
c = collections.Counter(r[4] for r in rows)
print(f'languages {len(c)}')
for k, n in c.most_common(10):
    print(f'lang {k}\t{n}\t{n/len(rows):.1%}')
