"""
nature_recovery v4 prefilter recall self-test (#70).

Reproduces the 21.6%-recall bug and verifies the v4 pass-through prefilter
recovers the blocked genuine positives.

Method: over the full DeepSeek-labeled corpus, compute each article's v4
weighted-average and call MEDIUM+ (>= 4.0) a "genuine positive". Then count
how many genuine positives the OLD v2 prefilter logic blocks vs the NEW v4
prefilter. Old should block a large chunk (the recall bug); new should block
~0 (only structural content_too_short).

Run: PYTHONPATH=. python scripts/nr_v4_prefilter_recall_check.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from filters.nature_recovery.v4.prefilter import NatureRecoveryPreFilterV4

ROOT = Path(__file__).resolve().parent.parent
LABEL_FILES = [
    ROOT / "datasets/scored/nature_recovery_v4_deepseek.jsonl",
    ROOT / "datasets/scored/nr_v4_positives_deepseek.jsonl",
]

DIMENSION_WEIGHTS = {
    "recovery_evidence": 0.25,
    "measurable_outcomes": 0.20,
    "ecological_significance": 0.20,
    "restoration_scale": 0.15,
    "human_agency": 0.10,
    "protection_durability": 0.10,
}
MEDIUM_THRESHOLD = 4.0


# --- OLD v2 prefilter logic (verbatim, for the before/after comparison) ---
_NATURE_KEYWORDS = [
    'ecosystem', 'biodiversity', 'habitat', 'deforestation', 'reforestation',
    'coral', 'reef', 'ocean', 'marine', 'wildlife', 'species', 'extinction',
    'pollution', 'air quality', 'water quality', 'environment', 'climate',
    'carbon', 'wetland', 'mangrove', 'conservation', 'restoration', 'recovery',
    'rewilding', 'endangered', 'protected area', 'national park', 'nature reserve',
    'emission', 'ozone', 'afforestation', 'fish stock',
]
_DISASTER = re.compile(
    r'\b(extinction|collapse|dying|destroyed|devastating|catastroph|irreversible)\b',
    re.IGNORECASE)
_RECOVERY_EXC = re.compile(
    r'\b(recover|restor|rebound|return|improv|increas|grow|thriv|heal|reintroduc|rewild)\b',
    re.IGNORECASE)


def old_v2_apply_filter(article):
    title = article.get('title', '')
    content = article.get('content', '') or article.get('text', '')
    text_lower = (title + ' ' + content[:2000]).lower()
    if not any(kw in text_lower for kw in _NATURE_KEYWORDS):
        return (False, "not_nature_topic")
    if _DISASTER.search(text_lower) and not _RECOVERY_EXC.search(text_lower):
        return (False, "disaster_no_recovery")
    return (True, "passed")


GATEKEEPER_MIN = 3.0   # recovery_evidence gatekeeper (base_scorer.py)
GATEKEEPER_CAP = 3.5


def weighted_avg(rec):
    """Weighted average WITH the recovery_evidence gatekeeper applied, matching
    how the scorer defines a surfacing score (base_scorer.py). Applying the
    gatekeeper here makes the 'genuine positive' count (598) consistent with
    prefilter.py's quoted figure; without it, 12 gatekeeper-capped articles
    are over-counted (610)."""
    a = rec["nature_recovery_analysis"]
    wa = sum(a[d]["score"] * w for d, w in DIMENSION_WEIGHTS.items())
    if a["recovery_evidence"]["score"] < GATEKEEPER_MIN and wa > GATEKEEPER_CAP:
        wa = GATEKEEPER_CAP
    return wa


def main():
    records = []
    for fn in LABEL_FILES:
        with open(fn, encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
    print(f"Loaded {len(records)} labeled articles")

    positives = [r for r in records if weighted_avg(r) >= MEDIUM_THRESHOLD]
    print(f"Genuine positives (weighted_avg >= {MEDIUM_THRESHOLD}): {len(positives)}")

    new_pf = NatureRecoveryPreFilterV4()

    def summarize(name, apply_fn):
        blocked, reasons = [], {}
        for r in positives:
            ok, reason = apply_fn({"title": r["title"], "content": r["content"]})
            if not ok:
                blocked.append(r)
                reasons[reason] = reasons.get(reason, 0) + 1
        n = len(blocked)
        pct = 100 * n / len(positives) if positives else 0
        print(f"\n{name}: blocks {n}/{len(positives)} positives ({pct:.1f}%)")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason}: {count}")
        return n

    old_blocked = summarize("OLD v2 prefilter", old_v2_apply_filter)
    new_blocked = summarize("NEW v4 prefilter", new_pf.apply_filter)

    recovered = old_blocked - new_blocked
    print("\n" + "=" * 60)
    print(f"RECOVERED by v4: {recovered} previously-blocked positives "
          f"(old {old_blocked} -> new {new_blocked})")
    # New should only ever block on structural grounds.
    assert new_blocked <= old_blocked, "v4 prefilter blocks MORE than v2 — regression"
    print("OK" if recovered > 0 else "WARNING: no recall gain measured")


if __name__ == "__main__":
    main()
