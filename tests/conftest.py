"""
Shared pytest fixtures for llm-distillery tests.

Provides common test data and mock objects used across test modules.
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, List


# =============================================================================
# Sample Article Fixtures
# =============================================================================

@pytest.fixture
def valid_article() -> Dict:
    """A valid article with all required fields."""
    return {
        "id": "test-article-001",
        "title": "Community Solar Project Brings Clean Energy to Rural Town",
        "content": """
        A new community solar project in rural Vermont has connected 500 households
        to clean energy for the first time. The 2 MW installation, funded through
        a combination of federal grants and local investment, will reduce carbon
        emissions by an estimated 3,000 tons annually. Local residents have already
        seen their electricity bills drop by 15-20%. The project also created 25
        permanent jobs in the community.
        """,
        "url": "https://example.com/solar-project",
        "source": "Green Energy News",
        "published_date": "2024-01-15"
    }


@pytest.fixture
def minimal_article() -> Dict:
    """Article with only required fields (title and content)."""
    return {
        "title": "Test Article",
        "content": "This is the article content with enough text to pass length checks." * 10
    }


@pytest.fixture
def article_missing_title() -> Dict:
    """Article missing the title field."""
    return {
        "content": "Some content here"
    }


@pytest.fixture
def article_missing_content() -> Dict:
    """Article missing both content and text fields."""
    return {
        "title": "A Title"
    }


@pytest.fixture
def article_empty_content() -> Dict:
    """Article with empty content."""
    return {
        "title": "A Title",
        "content": ""
    }


@pytest.fixture
def article_with_text_field() -> Dict:
    """Article using 'text' instead of 'content' field."""
    return {
        "title": "Test Article",
        "text": "This is article text content that is long enough." * 10
    }


@pytest.fixture
def short_article() -> Dict:
    """Article with content too short (under 300 chars)."""
    return {
        "title": "Short Article",
        "content": "This is too short."
    }


# =============================================================================
# Oracle Analysis Fixtures
# =============================================================================

@pytest.fixture
def sample_oracle_analysis() -> Dict:
    """Sample oracle analysis with nested dimension format.

    Note: calculate_overall_score looks for dimensions directly in the dict,
    not inside a 'dimensions' key. The 'dimensions' key format is used in
    the full article structure, not in the raw analysis dict.
    """
    return {
        "human_wellbeing_impact": {"score": 7, "reasoning": "Direct health benefits"},
        "social_cohesion_impact": {"score": 6, "reasoning": "Community cooperation"},
        "justice_rights_impact": {"score": 5, "reasoning": "Equal access"},
        "evidence_level": {"score": 8, "reasoning": "Verified data"},
        "benefit_distribution": {"score": 6, "reasoning": "Wide distribution"},
        "change_durability": {"score": 7, "reasoning": "Permanent installation"},
        "overall_score": 6.5
    }


@pytest.fixture
def sample_oracle_analysis_flat() -> Dict:
    """Sample oracle analysis with flat dimension format."""
    return {
        "human_wellbeing_impact": 7,
        "social_cohesion_impact": 6,
        "justice_rights_impact": 5,
        "evidence_level": 8,
        "benefit_distribution": 6,
        "change_durability": 7,
        "overall_score": 6.5
    }


@pytest.fixture
def labeled_articles(valid_article, sample_oracle_analysis) -> List[Dict]:
    """List of labeled articles for testing data preparation."""
    articles = []
    scores = [
        (8.5, "high"),    # Gold tier
        (7.0, "high"),    # Gold tier
        (6.5, "medium"),  # Silver tier
        (5.5, "medium"),  # Silver tier
        (4.0, "low"),     # Bronze tier
        (3.0, "low"),     # Bronze tier
        (2.0, "low"),     # Low tier
        (1.5, "low"),     # Low tier
    ]

    for i, (score, _tier) in enumerate(scores):
        article = valid_article.copy()
        article["id"] = f"article-{i:03d}"
        article["uplifting_analysis"] = {
            "dimensions": {
                "human_wellbeing_impact": {"score": score, "reasoning": "test"},
                "social_cohesion_impact": {"score": score - 0.5, "reasoning": "test"},
                "justice_rights_impact": {"score": score - 1.0, "reasoning": "test"},
                "evidence_level": {"score": score, "reasoning": "test"},
                "benefit_distribution": {"score": score - 0.5, "reasoning": "test"},
                "change_durability": {"score": score, "reasoning": "test"}
            },
            "overall_score": score
        }
        articles.append(article)

    return articles


# =============================================================================
# Temporary Directory Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_jsonl_file(temp_dir, labeled_articles) -> Path:
    """Create a temporary JSONL file with labeled articles."""
    file_path = temp_dir / "test_articles.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        for article in labeled_articles:
            f.write(json.dumps(article) + '\n')
    return file_path


# =============================================================================
# Filter Configuration Fixtures
# =============================================================================

@pytest.fixture
def uplifting_dimension_names() -> List[str]:
    """Dimension names for uplifting filter."""
    return [
        "human_wellbeing_impact",
        "social_cohesion_impact",
        "justice_rights_impact",
        "evidence_level",
        "benefit_distribution",
        "change_durability"
    ]


@pytest.fixture
def uplifting_tier_boundaries() -> Dict[str, float]:
    """Tier boundaries for uplifting filter."""
    return {
        "high_impact": 7.0,
        "moderate_uplift": 4.0,
        "not_uplifting": 0.0
    }


@pytest.fixture
def investment_risk_dimension_names() -> List[str]:
    """Dimension names for investment_risk filter."""
    return [
        "risk_domain_type",
        "severity_magnitude",
        "materialization_timeline",
        "evidence_quality",
        "impact_breadth",
        "retail_actionability"
    ]


# =============================================================================
# The wrong-interpreter banner (memory/gotcha-log.md, "I EXPLAINED 78 TEST FAILURES AS
# 'THE ENVIRONMENT' AND IT WAS THE WRONG INTERPRETER", 5 occurrences through 2026-10-12)
# =============================================================================
# Under system `python3` the suite reports ModuleNotFoundError (transformers, peft, ...) and
# those rows have been explained away as "pre-existing environment noise" five times. The
# fix was always "run .venv/bin/python"; prose never stopped it, so the suite says it itself.

import sys as _sys

_REPO = Path(__file__).resolve().parents[1]


def wrong_interpreter_hint(failure_texts, executable, repo=_REPO):
    """The banner lines, or [] when there is nothing to say."""
    n = sum(1 for t in failure_texts if "ModuleNotFoundError" in t)
    venv = repo / ".venv"
    try:
        inside = Path(executable).resolve().is_relative_to(venv.resolve())
    except OSError:
        inside = False
    if not n or inside or not venv.is_dir():
        return []
    return [f"WRONG INTERPRETER? {n} failure(s)/error(s) are ModuleNotFoundError under "
            f"{executable}. This repo's suite runs under {venv}/bin/python -- re-run there "
            f"before calling any of them pre-existing or environmental."]


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    texts = [str(getattr(r, "longrepr", "") or "")
             for key in ("failed", "error")
             for r in terminalreporter.stats.get(key, [])]
    for line in wrong_interpreter_hint(texts, _sys.executable):
        terminalreporter.write_sep("!", line, red=True, bold=True)
