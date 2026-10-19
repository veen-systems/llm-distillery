"""Chance-corrected agreement between judges (#179): Krippendorff's alpha, Gwet's AC1, Cohen's kappa.

Raw agreement alone validates nothing when one class is rare: two judges who both say "out" to almost
everything agree ~95% by base rate alone. Report raw agreement only BESIDE a chance-corrected statistic
and each judge's positive rate — `agreement_report` returns all of them together for that reason.

Which statistic:
  - Krippendorff's alpha: any number of judges, missing values, nominal / ordinal / interval data
    (0-10 dimension scores are interval). The default to quote.
  - Gwet's AC1: two judges, categories, and ONE CLASS RARE. Kappa and alpha collapse there (the
    prevalence paradox: high raw agreement, kappa near 0); AC1 does not. Quote it beside alpha, never
    instead of it.
  - Cohen's kappa: kept so older evidence (six scripts under docs/evidence/) can be compared.

An undefined statistic RAISES (fewer than two pairable values, a single category in play): a `None`
or a 1.0 there reads as perfect agreement.
"""
from collections import Counter, defaultdict
from itertools import permutations

LEVELS = ("nominal", "ordinal", "interval")


def raw_agreement(a, b):
    _check_pairs(a, b)
    return sum(x == y for x, y in zip(a, b)) / len(a)


def cohen_kappa(a, b):
    _check_pairs(a, b)
    n = len(a)
    po = raw_agreement(a, b)
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1:
        raise ValueError("kappa undefined: both judges used a single, identical category")
    return (po - pe) / (1 - pe)


def gwet_ac1(a, b, categories=None):
    """Two judges, nominal. `categories`: the full category set (default: those observed). Pass it when
    a category exists but neither judge used it -- Q enters the chance term."""
    _check_pairs(a, b)
    n = len(a)
    cats = set(categories) if categories is not None else set(a) | set(b)
    if not set(a) | set(b) <= cats:
        raise ValueError(f"values outside categories: {sorted(set(a) | set(b) - cats, key=str)}")
    if len(cats) < 2:
        raise ValueError("AC1 undefined with fewer than two categories")
    counts = Counter(a) + Counter(b)
    pe = sum((counts[q] / (2 * n)) * (1 - counts[q] / (2 * n)) for q in cats) / (len(cats) - 1)
    return (raw_agreement(a, b) - pe) / (1 - pe)


def krippendorff_alpha(units, level="nominal"):
    """units: one sequence per unit (article), one value per judge, None where that judge gave none.
    Units with fewer than two values are not pairable and drop out, as the method prescribes."""
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, not {level!r}")
    o = defaultdict(float)                         # coincidence matrix o[(c, k)]
    for unit in units:
        vals = [v for v in unit if v is not None]
        m = len(vals)
        if m < 2:
            continue
        for c, k in permutations(vals, 2):
            o[(c, k)] += 1 / (m - 1)
    if not o:
        raise ValueError("alpha undefined: no unit carries two values")
    n_c = defaultdict(float)
    for (c, _), w in o.items():
        n_c[c] += w
    n = sum(n_c.values())
    values = sorted(n_c)
    if len(values) < 2:
        raise ValueError("alpha undefined: every pairable value is the same")

    if level == "nominal":
        def d2(c, k):
            return 0.0 if c == k else 1.0
    elif level == "interval":
        def d2(c, k):
            return float(c - k) ** 2
    else:
        rank = {v: i for i, v in enumerate(values)}

        def d2(c, k):
            lo, hi = sorted((rank[c], rank[k]))
            return (sum(n_c[values[g]] for g in range(lo, hi + 1)) - (n_c[c] + n_c[k]) / 2) ** 2

    d_obs = sum(w * d2(c, k) for (c, k), w in o.items()) / n
    d_exp = sum(n_c[c] * n_c[k] * d2(c, k) for c in values for k in values) / (n * (n - 1))
    return 1 - d_obs / d_exp


def agreement_report(a, b, positive=None, categories=None):
    """Everything to quote together for two judges. `positive`: the rare/positive category, whose rate
    per judge is the prevalence the raw figure must be read against (#179)."""
    _check_pairs(a, b)
    out = {"n": len(a), "raw": raw_agreement(a, b),
           "alpha_nominal": krippendorff_alpha(list(zip(a, b)), "nominal"),
           "ac1": gwet_ac1(a, b, categories), "kappa": cohen_kappa(a, b)}
    if positive is not None:
        out["positive_rate"] = (sum(x == positive for x in a) / len(a), sum(y == positive for y in b) / len(b))
    return out


def _check_pairs(a, b):
    if len(a) != len(b):
        raise ValueError(f"judges rated different numbers of items: {len(a)} vs {len(b)}")
    if not a:
        raise ValueError("no items")
    if any(v is None for v in a) or any(v is None for v in b):
        raise ValueError("a missing rating: use krippendorff_alpha, which handles missing values")
