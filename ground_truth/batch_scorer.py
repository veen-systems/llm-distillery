"""
Generic batch scoring using Claude/Gemini API for ground truth generation.

Produces dimensional regression ground truth (continuous scores 0-10) not classification labels.

Fully filter-agnostic - works with ANY semantic filter package.
No hardcoded filter logic - all filtering handled by filter packages.
No post-processing - outputs raw oracle dimensional scores for regression training.

Usage:
    python -m ground_truth.batch_scorer \
        --filter filters/<filter_name>/v<N> \
        --source datasets/raw/historical_dataset.jsonl \
        --output-dir datasets/scored/<filter_name>_v<N> \
        --target-scored 2500 \
        --llm gemini-flash \
        --batch-size 50
"""

# Standard library imports
import glob
import importlib.util
import json
import logging
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Third-party imports
# Cloud-provider SDKs (anthropic, google-genai) are imported LAZILY at their
# client-factory / call sites below, so this module loads without them
# installed — only the selected provider's SDK is needed at runtime (same
# pattern as the openai path). The old google.generativeai import was unused
# and has been removed.

# Local imports
from . import analysis_field_name
from .secrets_manager import get_secrets_manager
from .text_cleaning import clean_article as clean_article_comprehensive, sanitize_text_comprehensive


def load_filter_package(filter_path: Path) -> Tuple[Optional[object], Path, Dict]:
    """
    Load filter package components from a filter directory.

    A filter package follows the structure:
        filters/<name>/v<N>/
        ├── prefilter.py      # Optional: PreFilter class for early filtering
        ├── prompt.md         # Required: LLM prompt template
        ├── prompt-compressed.md  # Optional: Compressed version (preferred)
        └── config.yaml       # Optional: Filter configuration

    Args:
        filter_path: Path to filter directory (e.g., Path("filters/uplifting/v5"))

    Returns:
        Tuple of (prefilter_instance, prompt_path, config_dict):
        - prefilter_instance: Instantiated PreFilter class, or None if not found
        - prompt_path: Path to prompt file (compressed preferred)
        - config_dict: Loaded config.yaml contents, or {} if not found

    Raises:
        FileNotFoundError: If no prompt file exists in the filter directory

    Example:
        >>> prefilter, prompt_path, config = load_filter_package(
        ...     Path("filters/uplifting/v5")
        ... )
        >>> if prefilter:
        ...     passed, reason = prefilter.apply_filter(article)
    """
    print(f"Loading filter package: {filter_path}")

    # Validate filter path resolves inside filters/ directory
    resolved = filter_path.resolve()
    project_root = Path(__file__).resolve().parent.parent
    filters_root = project_root / "filters"
    try:
        resolved.relative_to(filters_root.resolve())
    except ValueError:
        raise ValueError(
            f"Filter path must be inside filters/ directory, got: {filter_path}"
        )

    # Load prefilter
    prefilter_module_path = filter_path / "prefilter.py"
    prefilter = None

    if prefilter_module_path.exists():
        spec = importlib.util.spec_from_file_location("prefilter", prefilter_module_path)
        prefilter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefilter_module)

        # Get the prefilter class (defined in this module, not imported)
        prefilter_classes = [
            obj for name, obj in vars(prefilter_module).items()
            if isinstance(obj, type) and 'PreFilter' in name
            and obj.__module__ == prefilter_module.__name__  # Exclude imported classes
        ]

        if prefilter_classes:
            prefilter_class = prefilter_classes[0]
            prefilter = prefilter_class()
            print(f"  Loaded: {prefilter_class.__name__} v{prefilter.VERSION}")

    # Find prompt file (try compressed first, then regular)
    prompt_path = filter_path / "prompt-compressed.md"
    if not prompt_path.exists():
        prompt_path = filter_path / "prompt.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"No prompt file found in {filter_path}")

    print(f"  Prompt: {prompt_path.name}")

    # Load config (for reference)
    config_path = filter_path / "config.yaml"
    config_dict = {}
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        except ImportError:
            print("  Warning: PyYAML not installed, skipping config load")

    return prefilter, prompt_path, config_dict


class ErrorType(Enum):
    """Classification of errors during distillation."""
    TIMEOUT = "timeout"
    JSON_PARSE_ERROR = "json_parse_error"
    JSON_EXTRACTION_FAILED = "json_extraction_failed"
    LLM_API_ERROR = "llm_api_error"
    EMPTY_RESPONSE = "empty_response"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    UNKNOWN = "unknown"


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    def __init__(self, message: str, error_type: ErrorType, retryable: bool = True):
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable


class LLMTimeoutError(LLMError):
    """LLM call timed out."""
    def __init__(self, message: str, timeout_seconds: int):
        super().__init__(message, ErrorType.TIMEOUT, retryable=True)
        self.timeout_seconds = timeout_seconds


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, ErrorType.RATE_LIMIT, retryable=True)
        self.retry_after = retry_after


class LLMAuthError(LLMError):
    """Authentication/authorization error."""
    def __init__(self, message: str):
        super().__init__(message, ErrorType.AUTH_ERROR, retryable=False)


class LLMResponseError(LLMError):
    """Error in LLM response (empty, invalid, etc.)."""
    def __init__(self, message: str, error_type: ErrorType):
        super().__init__(message, error_type, retryable=True)


@dataclass
class RetryState:
    """Tracks state across retry attempts for an article analysis."""
    article_id: str
    start_time: float = field(default_factory=time.time)
    current_attempt: int = 0
    max_attempts: int = 3
    json_repaired: bool = False
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None

    def increment_attempt(self) -> int:
        """Increment and return current attempt number (1-indexed for display)."""
        self.current_attempt += 1
        return self.current_attempt

    def has_retries_left(self) -> bool:
        """Check if more retry attempts are available."""
        return self.current_attempt < self.max_attempts

    def get_backoff_seconds(self) -> float:
        """Get exponential backoff delay for current attempt."""
        return 2 ** (self.current_attempt - 1)  # 1s, 2s, 4s

    def elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return time.time() - self.start_time

    def set_error(self, error_type: ErrorType, message: str):
        """Record error details."""
        self.error_type = error_type
        self.error_message = message


def safe_print(msg: str):
    """
    Print message with fallback for systems that don't support Unicode.
    Handles Windows console encoding issues (cp1252).
    """
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback: encode as ASCII, replacing unsupported characters
        print(msg.encode('ascii', errors='replace').decode('ascii'))


def extract_json_from_response(response_text: str) -> str:
    """
    Robustly extract JSON from LLM response that may contain markdown or extra text.

    Handles:
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - Extra text before/after JSON
    - Multiple whitespace/newlines

    Returns:
        Extracted JSON string (still needs parsing)
    """
    if not response_text:
        return ""

    # Try to extract JSON from markdown code fence using regex
    # Pattern: ```json (optional) followed by JSON, then closing ```
    markdown_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(markdown_pattern, response_text, re.DOTALL)

    if match:
        response_text = match.group(1).strip()
    else:
        # No markdown fence, try to find JSON object boundaries
        # Look for first { and last }
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]

    return response_text.strip()


def repair_json(json_str: str) -> str:
    """
    Attempt to repair common JSON syntax issues.

    Fixes:
    - Trailing commas before closing braces/brackets
    - Unescaped newlines in string values
    - Invalid escape sequences (e.g., \theta, \alpha from LaTeX)
    - Common patterns that cause parse errors

    Returns:
        Repaired JSON string
    """
    # Remove trailing commas before closing braces or brackets
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # Remove comments (// or /* */ style)
    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

    # Fix invalid escape sequences (preserve valid JSON escapes: \n \t \r \" \\ \/ \b \f)
    # This regex finds backslashes followed by characters that aren't valid JSON escapes
    # and escapes them properly
    def fix_escapes(match):
        text = match.group(0)
        # Replace backslash with double backslash for invalid escapes
        # Valid JSON escapes: n, t, r, ", \, /, b, f, u (unicode)
        text = re.sub(r'\\(?![ntr"\\/bfu])', r'\\\\', text)
        return text

    # Apply to string values only (between quotes)
    json_str = re.sub(r'"[^"]*"', fix_escapes, json_str)

    return json_str.strip()


def setup_logging(output_dir: Path, filter_name: str) -> Tuple[logging.Logger, Path]:
    """
    Set up logging infrastructure for the distillation process.

    Creates:
    - Main log file: distillation.log (human-readable)
    - Metrics log file: metrics.jsonl (structured, machine-readable)

    Returns:
        Tuple of (logger, metrics_log_path)
    """
    log_dir = output_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # Main logger for human-readable logs
    logger = logging.getLogger(f'distillery.{filter_name}')
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler - detailed logs
    log_file = log_dir / 'distillation.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler - important messages only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Metrics log path (JSONL format for structured analysis)
    metrics_log = log_dir / 'metrics.jsonl'

    logger.info(f"Logging initialized - Log file: {log_file}")
    logger.info(f"Metrics tracking - Metrics file: {metrics_log}")

    return logger, metrics_log


class GenericBatchScorer:
    """
    Generic batch scorer for LLM-based oracle labeling.

    This is the core component for generating ground truth training data.
    It sends articles to an LLM with a scoring prompt and collects the
    dimensional scores for training smaller models via knowledge distillation.

    Features:
    - Multi-provider support: Claude, Gemini (Flash/Pro), GPT-4
    - Robust error handling with typed exceptions
    - Automatic retry with exponential backoff
    - JSON repair for malformed LLM responses
    - Progress checkpointing for resumable batches
    - Structured metrics logging

    Workflow:
        1. Load articles from source JSONL files
        2. Optional prefiltering (skip obviously off-topic content)
        3. Send to LLM with scoring prompt
        4. Parse JSON response (with repair if needed)
        5. Save scored articles to output JSONL
        6. Track progress for resumability

    Example:
        >>> scorer = GenericBatchScorer(
        ...     prompt_path="filters/uplifting/v5/prompt.md",
        ...     llm_provider="gemini-flash",
        ...     output_dir="datasets/scored/uplifting",
        ... )
        >>> scorer.run(
        ...     source_files=["datasets/raw/articles.jsonl"],
        ...     target_scored=1000,
        ...     batch_size=50
        ... )
    """

    def __init__(
        self,
        prompt_path: str,
        llm_provider: str = "claude",
        api_key: Optional[str] = None,
        output_dir: str = "datasets",
        filter_name: Optional[str] = None,
        filter_version: Optional[str] = None,
        thinking_budget: int = 0
    ):
        """
        Initialize the batch scorer.

        Args:
            prompt_path: Path to prompt markdown file containing the scoring
                        instructions for the LLM. Typically located at
                        filters/<name>/v<N>/prompt.md or prompt-compressed.md
            llm_provider: LLM provider to use. Options:
                        - "claude": Claude 3.7 Sonnet
                        - "gemini" or "gemini-pro": Gemini 2.5 Pro
                        - "gemini-flash": Gemini 2.5 Flash (fastest/cheapest)
                        - "gpt4": GPT-4 Turbo
            api_key: API key for the provider. If None, reads from environment
                    variables or config/credentials/secrets.ini
            output_dir: Directory to save scored articles and logs
            filter_name: Name of the filter (e.g., "uplifting"). If None,
                        auto-detected from prompt_path directory structure.
            filter_version: Version of the filter (e.g., "7.0"). If None,
                        auto-detected from config.yaml or directory name.
            thinking_budget: Token budget for Gemini "thinking" mode (0-24576).
                        Default 0 disables thinking to reduce costs by ~80%.
                        Set higher (e.g., 1024-8192) for complex reasoning tasks.
                        Only applies to gemini providers.
        """
        self.prompt_path = Path(prompt_path)
        self.llm_provider = llm_provider.lower()
        self.thinking_budget = thinking_budget

        # Auto-detect filter name from prompt filename
        if filter_name is None:
            self.filter_name = self.prompt_path.stem  # e.g., "sustainability" from "sustainability.md"
        else:
            self.filter_name = filter_name

        # Store filter version for scoring metadata
        self.filter_version = filter_version

        # Load prompt template
        self.prompt_template = self._load_prompt_template()

        # Compute prompt hash for reproducibility tracking
        import hashlib
        self.prompt_hash = hashlib.sha256(self.prompt_template.encode('utf-8')).hexdigest()[:12]

        # Initialize LLM client
        self.llm_client = self._init_llm_client(api_key)

        # Setup output directory
        self.output_dir = Path(output_dir) / self.filter_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger, self.metrics_log_path = setup_logging(self.output_dir, self.filter_name)

        # Load state
        self.state_file = self.output_dir / '.scored_ids.json'
        self.state = self._load_state()

        # Session statistics
        self.session_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'articles_attempted': 0,
            'articles_succeeded': 0,
            'articles_failed': 0,
            'total_retries': 0,
            'errors_by_type': {},
            'total_processing_time': 0.0
        }

    def _load_prompt_template(self) -> str:
        """
        Load prompt template from markdown file.

        Supports two formats:
        1. Legacy format: Extracts content from ## PROMPT TEMPLATE section
        2. Modern format: Uses entire file as-is (truly prompt-agnostic)

        The modern format allows filters to use any prompt structure without
        requiring boilerplate wrapper sections.
        """
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

        with open(self.prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try legacy format first (backward compatibility)
        prompt_section_marker = "## PROMPT TEMPLATE"

        if prompt_section_marker in content:
            # Legacy format: Extract from structured section
            end_marker = "DO NOT include any text outside the JSON object.\n```"

            prompt_section_idx = content.find(prompt_section_marker)
            start_idx = content.find("\n```\n", prompt_section_idx)

            if start_idx == -1:
                raise ValueError(f"Could not find opening ``` in PROMPT TEMPLATE section of {self.prompt_path}")

            end_idx = content.find(end_marker, start_idx)
            if end_idx == -1:
                raise ValueError(
                    f"Could not find closing marker in {self.prompt_path}\n"
                    f"Expected: 'DO NOT include any text outside the JSON object.\\n```'"
                )

            # Extract prompt (skip the opening ``` and newline, exclude closing marker)
            prompt = content[start_idx + 5:end_idx + len(end_marker) - 4]
            self.is_modern_format = False
            return prompt.strip()

        else:
            # Modern format: Use entire file (truly prompt-agnostic)
            # Supports LCSA framework, custom structures, etc.
            print(f"  Using modern prompt format (entire file)")
            self.is_modern_format = True
            return content.strip()

    def _init_llm_client(self, api_key: Optional[str]):
        """Initialize LLM client based on provider."""
        # Use SecretsManager if no API key provided
        if api_key is None:
            secrets = get_secrets_manager()
            api_key = secrets.get_llm_key(self.llm_provider)

        if self.llm_provider == "claude":
            if not api_key:
                raise ValueError(
                    "Claude API key not found. Set ANTHROPIC_API_KEY in environment or secrets.ini"
                )
            import anthropic
            return anthropic.Anthropic(api_key=api_key)

        elif self.llm_provider in ("gemini", "gemini-flash"):
            if not api_key:
                raise ValueError(
                    "Gemini API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY in environment or secrets.ini"
                )
            # Use new SDK with thinking disabled to reduce costs
            # Thinking tokens were adding ~80% to output token costs
            self._gemini_model = 'gemini-2.5-flash'
            from google import genai as genai_new
            return genai_new.Client(api_key=api_key)

        elif self.llm_provider == "gemini-pro":
            if not api_key:
                raise ValueError(
                    "Gemini API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY in environment or secrets.ini"
                )
            # Use new SDK with thinking disabled
            self._gemini_model = 'gemini-2.5-pro'
            from google import genai as genai_new
            return genai_new.Client(api_key=api_key)

        elif self.llm_provider == "gpt4":
            import openai
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY in environment or secrets.ini"
                )
            return openai.OpenAI(api_key=api_key)

        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def _load_state(self) -> Dict:
        """Load processing state for resume capability."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'processed': [],
            'total_scored': 0,
            'batches_completed': 0,
            'last_updated': None,
            'filter_name': self.filter_name,
            'llm_provider': self.llm_provider
        }

    def _save_state(self):
        """Save processing state."""
        self.state['last_updated'] = datetime.utcnow().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    # DEPRECATED: Post-processing removed from ground truth generation
    # Post-classification (caps, gatekeeper, tiers) should happen at inference time,
    # not during training data creation. Training targets should be raw oracle scores.
    #
    # All filter-specific logic has been removed from batch_scorer.py
    # The scorer now outputs raw oracle scores only.

    def _smart_compress_content(self, content: str, max_words: int = 800) -> str:
        """
        Intelligently compress long articles while preserving key information.

        Strategy:
        - Keep full content if short enough
        - For long articles: Keep beginning (context) + end (conclusions/impact)
        - Preserve structure for uplifting detection

        Args:
            content: Article text
            max_words: Target maximum word count (default 800 ≈ 3000 tokens)

        Returns:
            Compressed content
        """
        words = content.split()
        word_count = len(words)

        # Short enough - keep as is
        if word_count <= max_words:
            return content

        # Long article - intelligent sampling
        # Strategy: 70% from beginning (context), 30% from end (conclusions)
        start_words = int(max_words * 0.7)
        end_words = int(max_words * 0.3)

        beginning = ' '.join(words[:start_words])
        ending = ' '.join(words[-end_words:])

        # Add marker to indicate compression
        compressed = f"{beginning}\n\n[...content compressed...]\n\n{ending}"

        return compressed

    def _sanitize_unicode(self, text: str) -> str:
        """
        Comprehensively clean text for LLM processing.

        Removes:
        - Invalid Unicode (surrogates)
        - HTML entities and tags
        - Zero-width characters (invisible text)
        - Bidirectional marks (security issue)
        - Normalizes whitespace

        Prevents encoding and processing errors when sending to LLM APIs.
        """
        return sanitize_text_comprehensive(text) if isinstance(text, str) else str(text)

    def _sanitize_article(self, obj):
        """
        Recursively clean all text fields in an object (dict/list/str).

        Applies comprehensive cleaning:
        - Invalid Unicode removal
        - HTML cleaning
        - Invisible character removal
        - Security (BiDi marks)
        - Whitespace normalization

        Uses prefilter's clean_article() if available (single source of truth),
        otherwise uses comprehensive cleaning from text_cleaning module.
        """
        # Try to use prefilter's cleaning method if available
        if hasattr(self, 'pre_filter') and self.pre_filter:
            if hasattr(self.pre_filter, 'prefilter_obj'):
                prefilter_obj = self.pre_filter.prefilter_obj
                if hasattr(prefilter_obj, 'clean_article'):
                    return prefilter_obj.clean_article(obj)

        # Use comprehensive cleaning from text_cleaning module
        return clean_article_comprehensive(obj)

    def build_prompt(self, article: Dict) -> str:
        """
        Build prompt by filling in article data with smart content compression.

        Uses intelligent compression for long articles to:
        - Stay within context window limits
        - Preserve key information (beginning + ending)
        - Prepare for future small-model compatibility

        Supports two prompt formats:
        - Legacy: Uses .format() with {title}, {source}, {published_date}, {text} placeholders
        - Modern: Replaces [Paste the summary of the article here] with article text
        """
        # CRITICAL: Sanitize article FIRST to prevent encoding errors when sending to API
        # This removes surrogates, HTML, BiDi marks, etc. before any processing
        article = self._sanitize_article(article)

        content = article.get('content', '')

        # Smart compression (targets ~800 words ≈ 3000 tokens)
        compressed_content = self._smart_compress_content(content, max_words=800)

        # Build prompt based on format type
        if hasattr(self, 'is_modern_format') and self.is_modern_format:
            # Modern format: Replace placeholder text with article summary
            title = self._sanitize_unicode(article.get('title', 'N/A'))
            source = self._sanitize_unicode(article.get('source', 'N/A'))
            published_date = self._sanitize_unicode(article.get('published_date', 'N/A'))
            text = self._sanitize_unicode(compressed_content)

            # Build article summary
            article_summary = f"Title: {title}\nSource: {source}\nPublished: {published_date}\n\n{text}"

            # Replace placeholder text
            return self.prompt_template.replace('[Paste the summary of the article here]', article_summary)
        else:
            # Legacy format: Use .format() with placeholders
            return self.prompt_template.format(
                title=self._sanitize_unicode(article.get('title', 'N/A')),
                source=self._sanitize_unicode(article.get('source', 'N/A')),
                published_date=self._sanitize_unicode(article.get('published_date', 'N/A')),
                text=self._sanitize_unicode(compressed_content)
            )

    def _call_llm_with_timeout(
        self,
        prompt: str,
        timeout_seconds: int
    ) -> str:
        """
        Call LLM provider with timeout protection.

        Args:
            prompt: The prompt to send
            timeout_seconds: Maximum time to wait

        Returns:
            Response text from LLM

        Raises:
            LLMTimeoutError: If call times out
            LLMRateLimitError: If rate limited
            LLMAuthError: If authentication fails
            LLMError: For other LLM errors
        """
        result = [None]  # Mutable container for thread result
        exception = [None]  # Mutable container for exceptions

        def call_llm():
            try:
                if self.llm_provider == "claude":
                    message = self.llm_client.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=4096,
                        temperature=0.3,
                        system="You are an expert analyst. You respond only with valid JSON following the exact format specified. DO NOT include any text outside the JSON object.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result[0] = message.content[0].text.strip()

                elif self.llm_provider in ["gemini", "gemini-pro", "gemini-flash"]:
                    from google.genai import types as genai_types
                    # Use new SDK with configurable thinking budget
                    # thinking_budget=0 (default) eliminates ~80% of output tokens
                    # Set higher (1024-8192) for complex reasoning if needed
                    response = self.llm_client.models.generate_content(
                        model=self._gemini_model,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=4096,
                            thinking_config=genai_types.ThinkingConfig(
                                thinking_budget=self.thinking_budget
                            )
                        )
                    )
                    result[0] = response.text.strip()

                elif self.llm_provider == "gpt4":
                    response = self.llm_client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=4096,
                    )
                    result[0] = response.choices[0].message.content.strip()
            except Exception as e:
                exception[0] = e

        # Run LLM call in thread with timeout
        thread = threading.Thread(target=call_llm)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            raise LLMTimeoutError(
                f"LLM call timed out after {timeout_seconds}s",
                timeout_seconds
            )

        if exception[0]:
            self._classify_and_raise_exception(exception[0])

        if not result[0]:
            raise LLMResponseError("Empty response from LLM", ErrorType.EMPTY_RESPONSE)

        return result[0]

    def _classify_and_raise_exception(self, exc: Exception):
        """
        Classify an exception from LLM provider and raise appropriate LLMError.

        Args:
            exc: The original exception

        Raises:
            LLMRateLimitError: For rate limit errors
            LLMAuthError: For authentication errors
            LLMError: For other errors
        """
        error_str = str(exc).lower()
        error_type_str = type(exc).__name__.lower()

        # Check for rate limiting
        if any(term in error_str for term in ['rate limit', 'ratelimit', 'quota', '429', 'too many requests']):
            # Try to extract retry-after if available
            retry_after = None
            if hasattr(exc, 'retry_after'):
                retry_after = exc.retry_after
            raise LLMRateLimitError(str(exc), retry_after)

        # Check for authentication errors
        if any(term in error_str for term in ['auth', 'unauthorized', '401', '403', 'invalid key', 'api key']):
            raise LLMAuthError(str(exc))

        # Generic LLM error
        raise LLMError(str(exc), ErrorType.LLM_API_ERROR, retryable=True)

    def _parse_json_response(self, response_text: str, state: RetryState) -> Optional[Dict]:
        """
        Extract and parse JSON from LLM response with repair fallback.

        Args:
            response_text: Raw response from LLM
            state: Current retry state (updated if repair succeeds)

        Returns:
            Parsed JSON dict or None if parsing failed

        Raises:
            LLMResponseError: If JSON extraction or parsing fails
        """
        # Extract JSON from response
        json_str = extract_json_from_response(response_text)

        if not json_str:
            self._log_failed_response(state.article_id, response_text, "No JSON found", state.current_attempt)
            raise LLMResponseError(
                "Could not extract JSON from response",
                ErrorType.JSON_EXTRACTION_FAILED
            )

        # Try parsing JSON with repair fallback
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try repair
            try:
                repaired_json = repair_json(json_str)
                result = json.loads(repaired_json)
                state.json_repaired = True
                safe_print(f"  INFO: JSON repair successful for article {state.article_id}")
                return result
            except json.JSONDecodeError as e2:
                self._log_failed_response(state.article_id, response_text, str(e2), state.current_attempt)
                raise LLMResponseError(str(e2), ErrorType.JSON_PARSE_ERROR)

    def analyze_article(
        self,
        article: Dict,
        timeout_seconds: int = 60,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Analyze a single article using LLM with timeout protection and retry logic.

        Args:
            article: Article to analyze
            timeout_seconds: Timeout for LLM call
            max_retries: Maximum number of retry attempts for failed JSON parsing

        Returns:
            Analysis dict or None if all retries failed
        """
        prompt = self.build_prompt(article)
        article_id = article.get('id', 'unknown')

        # Initialize retry state
        state = RetryState(article_id=article_id, max_attempts=max_retries)

        # Ensure error log directory exists
        error_log_dir = self.output_dir / 'error_logs'
        error_log_dir.mkdir(exist_ok=True)

        while state.has_retries_left():
            attempt_num = state.increment_attempt()

            try:
                # Call LLM with timeout
                response_text = self._call_llm_with_timeout(prompt, timeout_seconds)

                # Parse JSON response
                analysis = self._parse_json_response(response_text, state)

                # Success! Add metadata
                analysis['analyzed_at'] = datetime.utcnow().isoformat() + 'Z'
                analysis['analyzed_by'] = f'{self.llm_provider}-api-batch'
                analysis['filter_name'] = self.filter_name
                if self.filter_version:
                    analysis['filter_version'] = self.filter_version
                analysis['prompt_hash'] = self.prompt_hash

                # Log success metrics
                self._log_metrics(
                    article_id, True, None, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, None
                )
                return analysis

            except LLMAuthError as e:
                # Auth errors are not retryable
                state.set_error(e.error_type, str(e))
                safe_print(f"  AUTH ERROR for article {article_id}: {e}")
                self._log_metrics(
                    article_id, False, state.error_type, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, state.error_message
                )
                return None

            except LLMRateLimitError as e:
                state.set_error(e.error_type, str(e))
                backoff = e.retry_after if e.retry_after else state.get_backoff_seconds() * 2
                safe_print(f"  RATE LIMITED for article {article_id}, waiting {backoff}s...")
                if state.has_retries_left():
                    time.sleep(backoff)
                    continue
                self._log_metrics(
                    article_id, False, state.error_type, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, state.error_message
                )
                return None

            except LLMTimeoutError as e:
                state.set_error(e.error_type, str(e))
                safe_print(f"  TIMEOUT after {e.timeout_seconds}s for article {article_id} (attempt {attempt_num}/{max_retries})")
                if state.has_retries_left():
                    time.sleep(state.get_backoff_seconds())
                    continue
                self._log_metrics(
                    article_id, False, state.error_type, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, state.error_message
                )
                return None

            except LLMResponseError as e:
                state.set_error(e.error_type, str(e))
                safe_print(f"  {e.error_type.value.upper()} for article {article_id} (attempt {attempt_num}/{max_retries}): {e}")
                if state.has_retries_left():
                    time.sleep(state.get_backoff_seconds())
                    continue
                safe_print(f"  ERROR: Failed for article {article_id} after {max_retries} attempts")
                self._log_metrics(
                    article_id, False, state.error_type, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, state.error_message
                )
                return None

            except LLMError as e:
                state.set_error(e.error_type, str(e))
                safe_print(f"  LLM ERROR for article {article_id} (attempt {attempt_num}/{max_retries}): {e}")
                if e.retryable and state.has_retries_left():
                    time.sleep(state.get_backoff_seconds())
                    continue
                self._log_metrics(
                    article_id, False, state.error_type, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, state.error_message
                )
                return None

            except Exception as e:
                # Unexpected error - classify and handle
                state.set_error(ErrorType.UNKNOWN, str(e))
                safe_print(f"  UNEXPECTED ERROR for article {article_id} (attempt {attempt_num}/{max_retries}): {type(e).__name__}: {e}")
                if state.has_retries_left():
                    time.sleep(state.get_backoff_seconds())
                    continue
                self._log_metrics(
                    article_id, False, state.error_type, state.current_attempt,
                    state.elapsed_time(), state.json_repaired, state.error_message
                )
                return None

        # Should not reach here, but safety fallback
        self._log_metrics(
            article_id, False, ErrorType.UNKNOWN, state.current_attempt,
            state.elapsed_time(), False, "Exhausted retries"
        )
        return None

    def _log_failed_response(self, article_id: str, response_text: str, error: str, attempt: int):
        """Log full response from failed JSON parse for debugging."""
        error_log_dir = self.output_dir / 'error_logs'
        error_log_dir.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_id = re.sub(r'[^\w\-]', '_', str(article_id))[:64]
        log_file = error_log_dir / f'{safe_id}_attempt{attempt}_{timestamp}.txt'

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Article ID: {article_id}\n")
            f.write(f"Attempt: {attempt}\n")
            f.write(f"Error: {error}\n")
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}\n")
            f.write(f"\n{'='*60}\n")
            f.write(f"Full Response:\n")
            f.write(f"{'='*60}\n")
            f.write(response_text)

    def _log_metrics(
        self,
        article_id: str,
        success: bool,
        error_type: Optional[ErrorType] = None,
        attempts_made: int = 1,
        time_taken: float = 0.0,
        json_repaired: bool = False,
        error_message: Optional[str] = None
    ):
        """
        Log structured metrics for analysis and optimization.

        Args:
            article_id: Article identifier
            success: Whether analysis succeeded
            error_type: Type of error if failed
            attempts_made: Number of retry attempts needed
            time_taken: Time in seconds for analysis
            json_repaired: Whether JSON repair was needed
            error_message: Detailed error message
        """
        metric = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'article_id': article_id,
            'filter_name': self.filter_name,
            'llm_provider': self.llm_provider,
            'success': success,
            'attempts_made': attempts_made,
            'time_taken_seconds': round(time_taken, 2),
            'json_repaired': json_repaired
        }

        if not success and error_type:
            metric['error_type'] = error_type.value
            metric['error_message'] = error_message

        # Write to metrics log (JSONL format)
        with open(self.metrics_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metric, ensure_ascii=False) + '\n')

        # Update session statistics
        self.session_stats['articles_attempted'] += 1
        self.session_stats['total_processing_time'] += time_taken
        if success:
            self.session_stats['articles_succeeded'] += 1
        else:
            self.session_stats['articles_failed'] += 1
            error_key = error_type.value if error_type else 'unknown'
            self.session_stats['errors_by_type'][error_key] = \
                self.session_stats['errors_by_type'].get(error_key, 0) + 1

        if attempts_made > 1:
            self.session_stats['total_retries'] += (attempts_made - 1)

        # Log to human-readable log
        if success:
            self.logger.info(
                f"SUCCESS | {article_id} | attempts={attempts_made} | "
                f"time={time_taken:.2f}s | repaired={json_repaired}"
            )
        else:
            self.logger.warning(
                f"FAILED  | {article_id} | error={error_type.value if error_type else 'unknown'} | "
                f"attempts={attempts_made} | time={time_taken:.2f}s"
            )

    def _write_summary_report(self):
        """Write a summary report of the session statistics."""
        self.session_stats['ended_at'] = datetime.utcnow().isoformat()
        self.session_stats['duration_seconds'] = round(
            (datetime.fromisoformat(self.session_stats['ended_at']) -
             datetime.fromisoformat(self.session_stats['started_at'])).total_seconds(),
            2
        )

        # Calculate success rate
        total = self.session_stats['articles_attempted']
        success_rate = (self.session_stats['articles_succeeded'] / total * 100) if total > 0 else 0

        # Calculate average processing time
        avg_time = (self.session_stats['total_processing_time'] / total) if total > 0 else 0

        summary_file = self.output_dir / 'session_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_stats, f, indent=2)

        # Log summary
        self.logger.info("="*60)
        self.logger.info("SESSION SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Articles attempted: {total}")
        self.logger.info(f"Articles succeeded: {self.session_stats['articles_succeeded']}")
        self.logger.info(f"Articles failed: {self.session_stats['articles_failed']}")
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info(f"Total retries: {self.session_stats['total_retries']}")
        self.logger.info(f"Average processing time: {avg_time:.2f}s per article")

        if self.session_stats['errors_by_type']:
            self.logger.info(f"Errors by type:")
            for error_type, count in self.session_stats['errors_by_type'].items():
                self.logger.info(f"  - {error_type}: {count}")

        self.logger.info(f"Summary saved to: {summary_file}")
        self.logger.info("="*60)

    def process_batch(self, articles: List[Dict], batch_num: int) -> Dict:
        """Process a batch of articles.

        Each article is written to disk immediately after scoring to prevent
        data loss from rate limits, crashes, or interruptions.
        """
        output_file = self.output_dir / f'scored_batch_{batch_num:03d}.jsonl'
        num_scored = 0
        num_failed = 0

        self.logger.info("="*60)
        self.logger.info(f"Processing batch {batch_num} ({len(articles)} articles)")
        self.logger.info("="*60)
        print(f"\n{'='*60}")
        print(f"Processing batch {batch_num} ({len(articles)} articles)")
        print(f"{'='*60}")

        for i, article in enumerate(articles, 1):
            article_id = article.get('id')

            # Skip if already processed
            if article_id in self.state['processed']:
                print(f"  [{i}/{len(articles)}] SKIP Skipping {article_id} (already processed)")
                continue

            print(f"  [{i}/{len(articles)}] Analyzing {article_id}...")

            analysis = self.analyze_article(article)

            if analysis:
                # Add analysis to article
                article[analysis_field_name(self.filter_name)] = analysis

                # Write immediately to disk (append mode)
                clean_article = self._sanitize_article(article)
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(clean_article, ensure_ascii=False, separators=(',', ':')) + '\n')

                # Update state immediately so resumes skip this article
                self.state['processed'].append(article_id)
                self.state['total_scored'] += 1
                self._save_state()

                num_scored += 1

                # Rate limiting based on provider
                if self.llm_provider == "claude":
                    time.sleep(1.5)  # 50 RPM limit → ~40 req/min to be safe
                elif self.llm_provider in ["gemini", "gemini-pro", "gemini-flash"]:
                    time.sleep(0.5)  # 150 RPM limit → ~120 req/min to avoid 429 errors
                elif self.llm_provider == "gpt4":
                    time.sleep(1.0)  # Vary based on tier

                print(f"     SUCCESS")
            else:
                num_failed += 1
                print(f"     FAILED to analyze")

        if num_scored > 0:
            print(f"\nSAVED {num_scored} scored articles to {output_file.name}")

        self.state['batches_completed'] += 1
        self._save_state()

        return {
            'batch_num': batch_num,
            'articles_processed': num_scored,
            'articles_failed': num_failed,
        }

    def load_unscored_articles(
        self,
        source_files: List[str],
        batch_size: int = 50,
        pre_filter: Optional[callable] = None
    ) -> List[Dict]:
        """
        Load unscored articles from source files.

        Args:
            source_files: List of paths to JSONL files with articles
            batch_size: Number of articles to load
            pre_filter: Optional function to pre-filter articles
                       Should return True to include article, False to skip
        """
        articles = []
        processed_ids = set(self.state['processed'])

        # Iterate through all source files
        for source_file in source_files:
            if len(articles) >= batch_size:
                break

            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(articles) >= batch_size:
                            break

                        try:
                            article = json.loads(line.strip())
                            article_id = article.get('id')

                            # Skip if already processed
                            if article_id in processed_ids:
                                continue

                            # Apply pre-filter if provided
                            if pre_filter and not pre_filter(article):
                                continue

                            articles.append(article)
                        except json.JSONDecodeError:
                            # Skip malformed JSON lines
                            continue
            except FileNotFoundError:
                print(f"Warning: Source file not found: {source_file}")
                continue

        return articles

    def load_all_articles(
        self,
        source_files: List[str],
        pre_filter: Optional[callable] = None
    ) -> List[Dict]:
        """
        Load ALL articles from source files (for random sampling).

        Args:
            source_files: List of paths to JSONL files with articles
            pre_filter: Optional function to pre-filter articles

        Returns:
            List of all unprocessed articles that pass the prefilter
        """
        all_articles = []
        processed_ids = set(self.state['processed'])
        total_read = 0
        total_skipped_processed = 0
        total_skipped_prefilter = 0

        print(f"Loading all articles from {len(source_files)} source file(s)...")

        for source_file in source_files:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        total_read += 1

                        try:
                            article = json.loads(line.strip())
                            article_id = article.get('id')

                            # Skip if already processed
                            if article_id in processed_ids:
                                total_skipped_processed += 1
                                continue

                            # Apply pre-filter if provided
                            if pre_filter and not pre_filter(article):
                                total_skipped_prefilter += 1
                                continue

                            all_articles.append(article)
                        except json.JSONDecodeError:
                            # Skip malformed JSON lines
                            continue
            except FileNotFoundError:
                print(f"Warning: Source file not found: {source_file}")
                continue

        print(f"\nArticle loading statistics:")
        print(f"  Total articles read: {total_read}")
        print(f"  Already processed: {total_skipped_processed}")
        print(f"  Blocked by prefilter: {total_skipped_prefilter}")
        print(f"  Available for scoring: {len(all_articles)}")
        print()

        return all_articles

    def run(
        self,
        source_files: List[str],
        max_batches: Optional[int] = None,
        target_count: Optional[int] = None,
        batch_size: int = 50,
        pre_filter: Optional[callable] = None,
        random_sample: bool = False,
        random_seed: int = 42
    ):
        """
        Run batch scoring process.

        Args:
            source_files: List of paths to JSONL files with articles
            max_batches: Maximum number of batches to process (None = unlimited)
            target_count: Target number of scored articles to produce (None = unlimited)
            batch_size: Articles per batch
            pre_filter: Optional function to pre-filter articles before scoring
            random_sample: If True, load all articles and sample randomly
            random_seed: Seed for random number generator (for reproducibility)
        """
        # Store pre_filter for use by _sanitize_article
        self.pre_filter = pre_filter

        # Format source files for display
        source_display = ', '.join(source_files) if len(source_files) <= 3 else f"{len(source_files)} files"

        print(f"\nLLM Distillery - Batch Scoring")
        print(f"{'='*60}")
        print(f"Filter: {self.filter_name}")
        print(f"Prompt: {self.prompt_path}")
        print(f"LLM: {self.llm_provider}")
        print(f"Source: {source_display}")
        print(f"Output: {self.output_dir}")
        print(f"Batch size: {batch_size}")
        print(f"Max batches: {max_batches or 'unlimited'}")
        print(f"Target count: {target_count or 'unlimited'}")
        print(f"Sampling mode: {'RANDOM' if random_sample else 'SEQUENTIAL'}")
        if random_sample:
            print(f"Random seed: {random_seed}")
        print(f"Already processed: {len(self.state['processed'])} articles")
        print(f"{'='*60}\n")

        # Random sampling mode: Load all articles, shuffle, process in batches
        if random_sample:
            # Set random seed for reproducibility
            random.seed(random_seed)

            # Load all articles at once
            all_articles = self.load_all_articles(source_files, pre_filter)

            if not all_articles:
                print("No articles available for scoring.")
                return

            # Shuffle articles
            random.shuffle(all_articles)
            print(f"Shuffled {len(all_articles)} articles (seed={random_seed})\n")

            # Limit to target_count if specified
            if target_count:
                articles_to_process = all_articles[:target_count]
                print(f"Selected first {len(articles_to_process)} articles for scoring\n")
            else:
                articles_to_process = all_articles

            # Process in batches
            batch_num = self.state['batches_completed'] + 1
            total_processed = 0
            total_failed = 0

            for i in range(0, len(articles_to_process), batch_size):
                batch = articles_to_process[i:i+batch_size]

                # Process batch
                result = self.process_batch(batch, batch_num)
                total_processed += result['articles_processed']
                total_failed += result['articles_failed']

                print(f"\nBatch {batch_num} Summary:")
                print(f"   Processed: {result['articles_processed']}")
                print(f"   Failed: {result['articles_failed']}")
                print(f"   Total scored so far: {self.state['total_scored']}/{len(articles_to_process)}")

                batch_num += 1

        # Sequential mode: Original behavior
        else:
            batch_num = self.state['batches_completed'] + 1
            total_processed = 0
            total_failed = 0
            batches_this_run = 0

            while True:
                # Check if we've hit max batches
                if max_batches and batches_this_run >= max_batches:
                    print(f"\nReached max batches ({max_batches})")
                    break

                # Check if we've hit target count
                if target_count and self.state['total_scored'] >= target_count:
                    print(f"\nReached target count ({target_count} scored articles)")
                    break

                # Load next batch
                articles = self.load_unscored_articles(source_files, batch_size, pre_filter)

                if not articles:
                    print(f"\nDONE - No more unscored articles found")
                    break

                # Process batch
                result = self.process_batch(articles, batch_num)
                total_processed += result['articles_processed']
                total_failed += result['articles_failed']

                print(f"\nBatch {batch_num} Summary:")
                print(f"   Processed: {result['articles_processed']}")
                print(f"   Failed: {result['articles_failed']}")
                if target_count:
                    print(f"   Total scored so far: {self.state['total_scored']}/{target_count}")

                batch_num += 1
                batches_this_run += 1

        # Final summary
        print(f"\n{'='*60}")
        print(f"Batch Scoring Complete!")
        print(f"{'='*60}")
        print(f"Articles scored this run: {total_processed}")
        print(f"Articles failed this run: {total_failed}")
        print(f"Total articles scored: {self.state['total_scored']}")
        print(f"Total batches completed: {self.state['batches_completed']}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}\n")

        # Write summary report
        self._write_summary_report()


# DEPRECATED: All hardcoded pre-filter functions removed
# Pre-filtering is now handled by filter packages (filters/*/v*/prefilter.py)
# These legacy functions are no longer needed


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Generic batch scoring for ground truth generation'
    )

    # Support both --filter (new) and --prompt (legacy)
    filter_group = parser.add_mutually_exclusive_group(required=True)
    filter_group.add_argument(
        '--filter',
        help='Path to filter package directory (e.g., filters/uplifting/v1)'
    )
    filter_group.add_argument(
        '--prompt',
        help='Path to prompt markdown file [DEPRECATED: use --filter instead]'
    )

    parser.add_argument(
        '--source',
        required=True,
        help='Source JSONL file(s) with articles (supports glob patterns like "data/*.jsonl")'
    )
    parser.add_argument(
        '--output-dir',
        default='datasets',
        help='Output directory for scored data (default: datasets/)'
    )
    parser.add_argument(
        '--llm',
        default='claude',
        choices=['claude', 'gemini', 'gemini-pro', 'gemini-flash', 'gpt4'],
        help='LLM provider (default: claude)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Articles per batch (default: 50)'
    )
    parser.add_argument(
        '--max-batches',
        type=int,
        help='Maximum number of batches to process (default: unlimited)'
    )
    parser.add_argument(
        '--target-scored',
        type=int,
        help='Target number of scored articles to produce (stops when reached)'
    )
    parser.add_argument(
        '--random-sample',
        action='store_true',
        help='Randomly sample articles instead of sequential processing (STRONGLY RECOMMENDED for training data to avoid temporal/source bias)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--api-key',
        help='API key (or set via environment variable)'
    )
    parser.add_argument(
        '--thinking-budget',
        type=int,
        default=0,
        help='Token budget for Gemini 2.5 Flash thinking mode (0=disabled, max 24576). Default 0 to minimize costs.'
    )

    args = parser.parse_args()

    # Load filter package or use legacy mode
    prefilter = None
    prompt_path = None
    filter_name = None

    filter_version = None

    if args.filter:
        # New filter package mode
        filter_path = Path(args.filter)
        filter_name = filter_path.parent.name  # e.g., "uplifting" from "filters/uplifting/v1"
        prefilter_obj, prompt_path, config = load_filter_package(filter_path)

        # Extract filter version from config or directory name
        if config and 'filter' in config:
            filter_version = str(config['filter'].get('version', ''))
        if not filter_version:
            # Fallback: extract from directory name (e.g., "v7" -> "7")
            filter_version = filter_path.name.lstrip('v')

        # Wrap prefilter object to match batch_scorer interface
        # Filter packages return (bool, reason) but batch_scorer expects just bool
        if prefilter_obj:
            prefilter = lambda article: prefilter_obj.apply_filter(article)[0]
            # Store prefilter object for Unicode cleaning
            prefilter.prefilter_obj = prefilter_obj
        else:
            prefilter = None
        print()
    else:
        # Legacy --prompt mode (NO PREFILTER SUPPORT)
        prompt_path = Path(args.prompt)
        filter_name = prompt_path.stem
        print("WARNING: --prompt is deprecated. Use --filter for prefilter support.")
        print()

    # Expand glob patterns in source parameter
    source_files = glob.glob(args.source)
    if not source_files:
        # If glob returns nothing, treat as literal filename
        source_files = [args.source]

    # Sort files for consistent ordering
    source_files.sort()

    print(f"Found {len(source_files)} source file(s):")
    for f in source_files[:5]:  # Show first 5
        print(f"  - {f}")
    if len(source_files) > 5:
        print(f"  ... and {len(source_files) - 5} more")
    print()

    # Create scorer
    scorer = GenericBatchScorer(
        prompt_path=str(prompt_path),
        llm_provider=args.llm,
        api_key=args.api_key,
        output_dir=args.output_dir,
        filter_name=filter_name,
        filter_version=filter_version,
        thinking_budget=args.thinking_budget
    )

    # Run scoring
    scorer.run(
        source_files=source_files,
        max_batches=args.max_batches,
        target_count=args.target_scored,
        batch_size=args.batch_size,
        pre_filter=prefilter,
        random_sample=args.random_sample,
        random_seed=args.seed
    )
