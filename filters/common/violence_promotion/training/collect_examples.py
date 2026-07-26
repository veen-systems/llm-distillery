#!/usr/bin/env python3
"""
Collect calibration + training examples for violence_promotion binary prefilter.

Reads from NexusMind filtered JSONL files (on sadalsuud) to build a
representative sample spanning the full conflict-score spectrum:

  POSITIVES (violence promotion) — articles from:
    - Defense/military/war RSS feeds (breaking_defense, defense_one, etc.)
    - Weapons manufacturing, defense industry, military tech sources
    - Articles whose title/content promotes or normalises violence
    - Target: ~100 for calibration, ~500 for full training

  NEGATIVES (not violence promotion) — articles from:
    - investment_risk, resilience, nature_recovery filters (the boundary
      MUST hold — these are the consumer filters that keep violence articles)
    - General journalism across all sources
    - Recovery, peace, diplomacy, disarmament articles
    - Target: ~200 for calibration, ~1500 for full training

Output: JSONL with {id, title, content, source, source_type, published_date,
                  language, url, filter, weighted_average}

Usage (on sadalsuud):
    python3 collect_examples.py \
        --mode calibration \
        --nexusmind-dir ~/local_dev/NexusMind/data/filtered \
        --out data/calibration_sample.jsonl

    python3 collect_examples.py \
        --mode training \
        --nexusmind-dir ~/local_dev/NexusMind/data/filtered \
        --out data/training_corpus.jsonl
"""

import argparse
import json
import random
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Cookie-wall / consent interstitial detection
# ---------------------------------------------------------------------------

# Patterns that identify Google GDPR consent pages and similar interstitials
# that replace actual article content in RSS feeds.
COOKIE_WALL_PATTERNS = [
    re.compile(r"Before you continue to Google", re.IGNORECASE),
    re.compile(r"We use cookies and data to", re.IGNORECASE),
    re.compile(r"Google uses cookies and data to", re.IGNORECASE),
    re.compile(r"To continue,? please agree to", re.IGNORECASE),
    re.compile(r"Please confirm that you are not a robot", re.IGNORECASE),
    re.compile(r"Accept (all|our) cookies to (continue|view)", re.IGNORECASE),
    re.compile(r"This site uses cookies to (ensure|provide|improve|deliver)", re.IGNORECASE),
]


def _is_cookie_wall(content: str) -> bool:
    """Detect Google GDPR consent interstitials and similar cookie walls.

    These replace actual article content in RSS feeds. Scoring from a
    cookie wall would train the model on titles alone — guaranteed noise.
    """
    if not content or len(content) < 100:
        return True  # too short to be real content
    # Check first 500 chars — cookie walls announce themselves early
    head = content[:500]
    for pattern in COOKIE_WALL_PATTERNS:
        if pattern.search(head):
            return True
    return False


# ---------------------------------------------------------------------------
# Source lists
# ---------------------------------------------------------------------------

# Feeds likely to carry violence-promoting content (active combat, weapons
# manufacturing, military tech, defense industry, arms trade)
VIOLENCE_SOURCES = {
    # Defense / military news wires
    "aerospace_defense_breaking_defense",
    "aerospace_defense_space_news",
    "disaster_alerts_defense_one",
    # Weapons industry / military tech
    "aerospace_defense_defense_news",
    "aerospace_defense_janes",
    "aerospace_defense_flight_global",
    # Middle East — combat + weapons industry reporting
    "middle_eastern_al_jazeera",
    "middle_eastern_times_of_israel",
    "middle_eastern_haaretz",
    "middle_eastern_jerusalem_post",
    # Wire services that carry war/weapons reporting
    "british_irish_reuters",
    "british_irish_bbc_news",
    "us_media_associated_press",
    "us_media_cnn",
    "us_media_npr",
    "us_media_new_york_times",
    "us_media_washington_post",
    "us_media_wall_street_journal",
    # International wire services
    "french_afp",
    "german_dw",
    "russian_tass",
    "ukrainian_ukrinform",
    "ukrainian_pravda",
    # Arms trade / defense business
    "professional_business_forbes_innovation",
    # South Asian — regional conflict zones
    "south_asian_the_hindu",
    "south_asian_dawn",
    "south_asian_times_of_india",
}

# Sources whose articles about conflict might frame it constructively —
# these test the boundary (recovery/peace framing of conflict zones)
BOUNDARY_SOURCES = {
    "positive_news_mongabay",
    "positive_news_positive_news",
    "positive_news_good_news_network",
    "positive_news_reasons_to_be_cheerful",
}

# Filters whose high-tier articles must NOT be false-positive (the boundary)
BOUNDARY_FILTERS = {
    "investment_risk",
    "resilience",
    "nature_recovery",
}

# ---------------------------------------------------------------------------
# Combat keyword patterns (used as a rough pre-filter for candidate hunting)
# ---------------------------------------------------------------------------

STRONG_VIOLENCE_RE = re.compile(
    r"\b("
    # Active combat
    r"air[\s-]?strike|missile\s(strike|attack)|drone\sstrike|"
    r"shelling|bombardment|artillery\sbarrage|"
    r"killed\s(in|by)\s(a|an)\s|casualties\s(from|in)\s|"
    r"died\s(in|during)\s(the|a)\s(strike|attack|bombing)|"
    r"troops?\s(killed|died|wounded)|"
    r"launched\s(an?\s)?offensive|"
    r"captured\s(the|a)\s(town|city|village|base)|"
    r"war\s(crimes?|tribunal)|genocide|"
    # Weapons manufacturing / industry (when framed as progress)
    r"weapons?\s(production|manufacturing|factory|plant)|"
    r"arms?\s(production|manufacturing|industry|trade|deal|export)|"
    r"munitions?\s(factory|plant|production)|"
    r"defense\s(contractor|manufacturing|industrial\sbase)|"
    r"missile\s(production|factory|program)|"
    r"combat\s(drone|aircraft|vehicle|system)\s(unveiled|completed|tested)|"
    r"domestically[\s-]produced\s(bomb|weapon|missile|munition)|"
    r"military\s(build[\s-]?up|expansion|moderni[sz]ation|procurement\sdeal)|"
    r"naval\s(fleet\sexpand|commission|warship\slaunch)|"
    r"fighter\sjet\s(unveiled|delivered|ordered|program)|"
    # Recovery/peace (to find boundary cases — these LOWER the score)
    r"ceasefire|peace\s(deal|talks|negotiations?|agreement)|"
    r"disarmament|demining|de-mining|"
    r"post[\s-]?conflict\sreconstruction|"
    r"refugees?\s(return|flee|resettle)"
    r")\b",
    re.IGNORECASE,
)

WEAPON_VIOLENCE_RE = re.compile(
    r"\b("
    r"fighter\sjet|warplane|bomber\saircraft|combat\shelicopter|"
    r"tank\sdivision|armoured\svehicle|"
    r"surface[\s-]to[\s-]air\smissile|ballistic\smissile|"
    r"cruise\smissile|hypersonic|"
    r"naval\sfleet|warship|destroyer|frigate|"
    r"submarine\slaunched|nuclear\s(weapon|warhead|deterrent)|"
    r"combat\sdrone|loitering\smunition|"
    r"precision[\s-]guided\smunition|guided\sbomb|"
    r"howitzer|mortar\ssystem|multiple\slaunch\srocket"
    r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Article collection
# ---------------------------------------------------------------------------

def find_jsonl_files(nexusmind_dir: Path, max_age_days: int = 3) -> Dict[str, List[Path]]:
    """
    Find recent filtered JSONL files across all filter directories.

    Args:
        nexusmind_dir: Path to NexusMind data/filtered directory.
        max_age_days: Only include JSONL files from the last N days.

    Returns:
        Dict mapping filter_name -> list of Paths
    """
    nexusmind_dir = Path(nexusmind_dir)
    files_by_filter: Dict[str, List[Path]] = defaultdict(list)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

    for filter_dir in sorted(nexusmind_dir.iterdir()):
        if not filter_dir.is_dir():
            continue
        all_files = sorted(
            filter_dir.glob("filtered_*.jsonl"),
            reverse=True,
        )
        # Filter by filename timestamp: filtered_YYYYMMDD_HHMMSS.jsonl
        recent = []
        for fp in all_files:
            match = re.search(r"filtered_(\d{4})(\d{2})(\d{2})_", fp.name)
            if match:
                try:
                    file_date = datetime(
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                        tzinfo=timezone.utc,
                    )
                    if file_date >= cutoff:
                        recent.append(fp)
                except ValueError:
                    recent.append(fp)  # include if can't parse (fail open)
            else:
                recent.append(fp)  # include if can't parse (fail open)
        if recent:
            files_by_filter[filter_dir.name] = recent

    return files_by_filter


def read_articles(file_paths: List[Path], limit: int = 0) -> List[Dict]:
    """
    Read articles from JSONL files, deduplicating by id.

    Args:
        file_paths: JSONL files to read (newest first)
        limit: If >0, stop after collecting this many unique articles

    Returns:
        List of article dicts
    """
    seen: Set[str] = set()
    articles: List[Dict] = []

    for fp in file_paths:
        if not fp.exists():
            continue
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    article = json.loads(line)
                except json.JSONDecodeError:
                    continue
                aid = article.get("id")
                if not aid or aid in seen:
                    continue
                seen.add(aid)

                # Skip articles with no content
                content = article.get("content") or ""
                if len(content) < 300:
                    continue

                # Skip cookie-wall articles (Google consent interstitials
                # replace real content — scoring from titles alone is noise)
                if _is_cookie_wall(content):
                    continue

                articles.append(article)
                if limit and len(articles) >= limit:
                    return articles

    return articles


def is_potential_violence(article: Dict) -> bool:
    """
    Quick heuristic: could this article promote or normalize violence?

    Checks title + first 500 chars of content against violence/weapons
    keyword patterns. This is a BROAD pre-filter for candidate hunting —
    the oracle makes the final call.
    """
    title = (article.get("title") or "").lower()
    content_start = (article.get("content") or "")[:500].lower()
    combined = f"{title} {content_start}"
    return bool(STRONG_VIOLENCE_RE.search(combined) or WEAPON_VIOLENCE_RE.search(combined))


def collect_calibration(
    files_by_filter: Dict[str, List[Path]],
    limit_positives: int = 100,
    limit_negatives: int = 200,
    seed: int = 42,
) -> List[Dict]:
    """
    Collect a calibration sample (~300 articles).

    Positives: from defense/war sources + combat-keyword matches
    Negatives: from boundary filters (risk/resilience/recovery) + random general
    """
    rng = random.Random(seed)

    positives: List[Dict] = []
    negatives: List[Dict] = []
    pos_ids: Set[str] = set()
    neg_ids: Set[str] = set()

    # ----- Positives: conflict sources first, then keyword scan -----
    # Read from ALL filters (conflict articles could be in any filter's
    # sub-threshold output, or in uplifting/cultural_discovery)
    all_files = []
    for filter_name in sorted(files_by_filter):
        all_files.extend(files_by_filter[filter_name])

    # Shuffle to avoid source ordering bias
    rng.shuffle(all_files)

    print(f"Scanning {len(all_files)} JSONL files for calibration candidates...")
    articles_scanned = 0

    for fp in all_files:
        if not fp.exists():
            continue
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                articles_scanned += 1
                if articles_scanned % 50000 == 0:
                    print(f"  scanned {articles_scanned}... pos={len(positives)} neg={len(negatives)}")

                try:
                    article = json.loads(line)
                except json.JSONDecodeError:
                    continue

                aid = article.get("id")
                if not aid or aid in pos_ids or aid in neg_ids:
                    continue

                content = article.get("content") or ""
                if len(content) < 300:
                    continue
                if _is_cookie_wall(content):
                    continue

                source = (article.get("source") or "").lower()
                article_filter = (article.get("filter") or "").lower()

                # Positive candidate?
                if len(positives) < limit_positives:
                    is_pos = source in VIOLENCE_SOURCES or is_potential_violence(article)
                    if is_pos:
                        positives.append(article)
                        pos_ids.add(aid)
                        continue

                # Negative candidate?
                if len(negatives) < limit_negatives:
                    # Prioritize boundary filters
                    if article_filter in BOUNDARY_FILTERS and rng.random() < 0.3:
                        negatives.append(article)
                        neg_ids.add(aid)
                    elif rng.random() < 0.02:  # random general sample
                        negatives.append(article)
                        neg_ids.add(aid)

                if len(positives) >= limit_positives and len(negatives) >= limit_negatives:
                    break

        if len(positives) >= limit_positives and len(negatives) >= limit_negatives:
            break

    print(f"Scanned {articles_scanned} articles total")
    print(f"Positives: {len(positives)} (target {limit_positives})")
    print(f"Negatives: {len(negatives)} (target {limit_negatives})")

    # Merge and shuffle
    all_articles = positives + negatives
    rng.shuffle(all_articles)

    return all_articles


def collect_training(
    files_by_filter: Dict[str, List[Path]],
    limit_positives: int = 500,
    limit_negatives: int = 1500,
    seed: int = 42,
) -> List[Dict]:
    """
    Collect a full training corpus (~2000 articles).

    Same strategy as calibration but larger. After oracle labeling,
    articles scoring 4-6 (ambiguous middle) will be discarded.
    """
    # For now, same logic as calibration but with higher limits
    return collect_calibration(
        files_by_filter,
        limit_positives=limit_positives,
        limit_negatives=limit_negatives,
        seed=seed,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_articles(articles: List[Dict], output_path: Path) -> None:
    """Write collected articles as JSONL with only the needed fields."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kept_fields = {
        "id", "title", "content", "source", "source_type",
        "published_date", "language", "url", "filter", "weighted_average",
    }

    written = 0
    with output_path.open("w", encoding="utf-8") as f:
        for article in articles:
            slim = {k: article.get(k) for k in kept_fields if k in article}
            # Content length for quick filtering later
            slim["content_len"] = len(slim.get("content") or "")
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")
            written += 1

    print(f"\nWrote {written} articles to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Collect articles for armed_conflict detector training"
    )
    ap.add_argument(
        "--mode", choices=["calibration", "training"], default="calibration",
        help="Collection mode: calibration (~300) or training (~2000)",
    )
    ap.add_argument(
        "--nexusmind-dir", required=True,
        help="Path to NexusMind data/filtered directory (on sadalsuud)",
    )
    ap.add_argument("--out", required=True, help="Output JSONL path")
    ap.add_argument("--max-age-days", type=int, default=3,
                    help="Only use JSONL files from the last N days")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    nexusmind_dir = Path(args.nexusmind_dir).expanduser()
    if not nexusmind_dir.is_dir():
        raise SystemExit(f"Not a directory: {nexusmind_dir}")

    files_by_filter = find_jsonl_files(nexusmind_dir, max_age_days=args.max_age_days)
    total_files = sum(len(v) for v in files_by_filter.values())
    print(f"Found {total_files} JSONL files across {len(files_by_filter)} filters "
          f"(max {args.max_age_days}d age)")

    if args.mode == "calibration":
        articles = collect_calibration(files_by_filter, seed=args.seed)
    else:
        articles = collect_training(files_by_filter, seed=args.seed)

    write_articles(articles, Path(args.out).expanduser())

    # Print source/filter breakdown
    sources = defaultdict(int)
    filters = defaultdict(int)
    for a in articles:
        sources[a.get("source", "?")] += 1
        filters[a.get("filter", "?")] += 1

    print(f"\nTop sources:")
    for s, n in sorted(sources.items(), key=lambda x: -x[1])[:15]:
        print(f"  {s:<50s} {n}")
    print(f"\nTop filters:")
    for f, n in sorted(filters.items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:<30s} {n}")


if __name__ == "__main__":
    main()
