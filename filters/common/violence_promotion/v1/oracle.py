"""
Violence Promotion Oracle — DeepSeek labeler for calibration + training corpus.

Uses DeepSeek API (deepseek-chat, OpenAI-compatible endpoint) to score articles
on a 0–10 violence-promotion scale following the rubric in prompt.md. Chosen
over Gemini because:

- DeepSeek credits are owner-funded and independent of the podcast-reserved
  Gemini budget (same logic as obituary relabel_deepseek.py).
- ~100× cheaper than Gemini for this workload: ~2k articles ≈ $0.45 total.
- Temp=0, JSON response format, resumable batch scoring with ThreadPoolExecutor.

Score → label mapping for the trainer:
    score ≥ 7  → label="positive" (violence promotion)
    score ≤ 3  → label="negative" (not violence promotion)
    3 < score < 7 → discarded (ambiguous middle)

Violence is definitionally not constructive. This oracle answers: "does this
article promote, normalize, or present as desirable any form of mass violence?"

Usage:
    from filters.common.violence_promotion.v1.oracle import ViolencePromotionOracle

    oracle = ViolencePromotionOracle()
    result = oracle.score_article(article)
    # {"violence_score": 8, "reasoning": "...", "key_signals": [...]}

    # Batch (resumable)
    oracle.score_batch(articles, output_path="calibration_sample.jsonl")
"""

import configparser
import json
import os
import re
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional


def _load_api_key() -> Optional[str]:
    """Load DeepSeek API key from env or llm-distillery credential store."""
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    # llm-distillery credential store (Linux path; Windows path as fallback)
    candidates = [
        Path(__file__).parent.parent.parent.parent.parent / "config" / "credentials" / "secrets.ini",
        Path("C:/local_dev/llm-distillery/config/credentials/secrets.ini"),
    ]
    for secrets_path in candidates:
        if secrets_path.exists():
            cp = configparser.ConfigParser()
            cp.read(str(secrets_path), encoding="utf-8")
            if cp.has_option("api_keys", "deepseek_api_key"):
                key = cp.get("api_keys", "deepseek_api_key").strip()
                if key:
                    return key
    return None


DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


class ViolencePromotionOracle:
    """
    Oracle for classifying violence-promoting content using DeepSeek API.

    Outputs a 0–10 violence_score following the rubric in prompt.md:
      0–2  No Violence Promotion
      3–4  Peripheral
      5–6  Mixed/Ambiguous
      7–8  Mostly Violence Promotion
      9–10 Violence Promotion

    Violence is definitionally not constructive. The decisive test: does this
    article, as a whole, make violence or instruments of violence seem normal,
    acceptable, desirable, or a source of progress?

    Attributes:
        model: DeepSeek model identifier
        prompt_template: Loaded prompt.md content
        api_key: DeepSeek API key
    """

    def __init__(self, model: str = DEEPSEEK_MODEL):
        self.model = model
        self.api_key = _load_api_key()
        if not self.api_key:
            raise SystemExit(
                "DEEPSEEK_API_KEY not found in env or "
                "llm-distillery config/credentials/secrets.ini [api_keys]"
            )

        # Load the oracle prompt
        prompt_path = Path(__file__).parent / "prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Oracle prompt not found: {prompt_path}")
        self.prompt_template = prompt_path.read_text(encoding="utf-8")

        # Build the user-message template: append the JSON output instruction
        # and the placeholder for article data.
        self._user_template = (
            self.prompt_template
            + "\n\n---\n\n"
            + "**Article to classify:**\n\n"
            + "TITLE: {title}\n\n"
            + "CONTENT:\n{content}\n\n"
            + "---\n\n"
            + "Reply ONLY as JSON: "
            + '{{"violence_score":<0-10 integer>,"reasoning":"one short sentence",'
            + '"key_signals":["exact quote or \\"No evidence in article\\""]}}'
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_article(self, article: Dict) -> Dict:
        """
        Score a single article for violence promotion content.

        Args:
            article: Dict with 'title' and 'content' (or 'text') fields.

        Returns:
            Dict with:
                violence_score: int 0–10, or -1 on error
                reasoning: str
                key_signals: list[str]
                error: str or None
        """
        title = article.get("title") or ""
        content = article.get("content") or article.get("text") or ""
        prompt = self._user_template.format(
            title=title,
            content=content[:3000],
        )
        try:
            raw = self._call_api(prompt)
            return self._parse_response(raw)
        except RuntimeError:
            raise
        except Exception as e:
            return {
                "violence_score": -1,
                "reasoning": f"ERROR: {str(e)}",
                "key_signals": [],
                "error": str(e),
            }

    def score_batch(
        self,
        articles: List[Dict],
        output_path: str,
        workers: int = 8,
        limit: int = 0,
    ) -> List[Dict]:
        """
        Score a batch of articles with resumable output.

        Already-scored article IDs in *output_path* are skipped — safe to
        re-run after a halt (402 balance, network blip, etc.).

        Args:
            articles: List of article dicts with 'id', 'title', 'content'.
            output_path: JSONL file to append results to (resume-safe).
            workers: Number of ThreadPoolExecutor workers.
            limit: If >0, only score the first N unlabeled articles (debug).

        Returns:
            List of scored article dicts (only newly-scored; does NOT
            re-read previously scored from disk).
        """
        if limit:
            articles = articles[:limit]

        # Resume: collect already-scored IDs
        done_ids: set = set()
        out_path = Path(output_path)
        if out_path.exists():
            for line in out_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        done_ids.add(json.loads(line)["id"])
                    except Exception:
                        pass

        todo = [a for a in articles if a.get("id") not in done_ids]
        print(
            f"candidates={len(articles)}  already_labeled={len(done_ids)}  "
            f"to_label={len(todo)}"
        )

        if not todo:
            print("Nothing to do.")
            return []

        new_results: List[Dict] = []
        lock = threading.Lock()
        done = [0]  # mutable container for thread-safe increment
        halted = [False]

        def _work(article: Dict):
            with lock:
                if halted[0]:
                    return None
            try:
                result = self.score_article(article)
            except RuntimeError as e:
                with lock:
                    halted[0] = True
                print(f"\n!! {e}")
                return None
            article["violence_score"] = result["violence_score"]
            article["reasoning"] = result["reasoning"]
            article["key_signals"] = result.get("key_signals", [])
            article["label"] = self._binarize(result["violence_score"])
            with lock:
                done[0] += 1
                current = done[0]
            if current % 100 == 0:
                print(f"  {current}/{len(todo)}")
            return article

        try:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                for scored in ex.map(_work, todo):
                    if scored is not None:
                        new_results.append(scored)
        finally:
            # Flush all buffered results to disk on any exit path
            if new_results:
                with out_path.open("a", encoding="utf-8") as out_fh:
                    for scored in new_results:
                        out_fh.write(json.dumps(scored, ensure_ascii=False) + "\n")

        # Tally over the full output file
        self._print_tally(out_path, halted[0])
        return new_results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_api(self, prompt: str, timeout: int = 90) -> str:
        """Call DeepSeek chat/completions with per-status-code retry logic.

        - 429 (rate limit): exponential backoff, read Retry-After header if present.
        - 5xx (server error): retry with backoff.
        - 402 (balance): halt immediately — the run is resumable.
        - 401, 400, 403 (client error): fail fast — retrying won't help.
        """
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_tokens": 150,
        }
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    DEEPSEEK_URL,
                    data=json.dumps(body).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )
                resp = urllib.request.urlopen(req, timeout=timeout)
                data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                status = e.code
                if status == 402:
                    raise RuntimeError(
                        "DeepSeek 402 insufficient balance — top up and re-run (resumable)"
                    )
                if status == 429:
                    # Rate limited — use Retry-After header or exponential backoff
                    retry_after = e.headers.get("Retry-After", "")
                    try:
                        delay = int(retry_after)
                    except (ValueError, TypeError):
                        delay = min(2 ** (attempt + 2), 60)
                    if attempt == 4:
                        raise RuntimeError(
                            f"DeepSeek 429 rate-limited after 5 attempts "
                            f"(last Retry-After: {retry_after})"
                        )
                    print(f"  rate-limited (429), waiting {delay}s...")
                    time.sleep(delay)
                    continue
                if status in (400, 401, 403):
                    # Client errors — not retriable
                    body_text = e.read().decode(errors="replace")[:500] if e.fp else ""
                    raise RuntimeError(
                        f"DeepSeek HTTP {status} (non-retriable): {body_text}"
                    )
                if status >= 500:
                    # Server errors — retriable
                    if attempt == 4:
                        raise RuntimeError(
                            f"DeepSeek HTTP {status} after 5 attempts"
                        )
                    time.sleep(2 * (2**attempt))
                    continue
                raise  # unexpected 4xx
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                # Network-level errors — retriable
                if attempt == 4:
                    raise RuntimeError(
                        f"DeepSeek network error after 5 attempts: {e}"
                    )
                time.sleep(2 * (2**attempt))
                continue

    @staticmethod
    def _parse_response(raw: str) -> Dict:
        """Parse the JSON response from DeepSeek."""
        try:
            # Extract JSON object from response (may have markdown fences)
            text = raw
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError(f"No JSON object found in: {text[:200]}")
            obj = json.loads(match.group(0))
            score = int(obj.get("violence_score", -1))
            # Clamp to valid range
            if score < 0:
                score = 0
            if score > 10:
                score = 10
            return {
                "violence_score": score,
                "reasoning": str(obj.get("reasoning", ""))[:200],
                "key_signals": obj.get("key_signals", []),
                "error": None,
            }
        except Exception as e:
            return {
                "violence_score": -1,
                "reasoning": f"Parse error: {str(e)}",
                "key_signals": [],
                "error": str(e),
            }

    @staticmethod
    def _binarize(score: int) -> str:
        """Convert 0–10 score to positive/negative/discard label."""
        if score < 0:
            return "error"
        if score >= 7:
            return "positive"
        if score <= 3:
            return "negative"
        return "discard"  # ambiguous middle (4–6)

    @staticmethod
    def _print_tally(output_path: Path, halted: bool) -> None:
        """Print verdict distribution over the output file."""
        import collections

        scores = collections.Counter()
        labels = collections.Counter()
        errors = 0
        for line in output_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            vs = row.get("violence_score", -1)
            if vs < 0:
                errors += 1
            else:
                scores[vs] += 1
            labels[row.get("label", "unknown")] += 1

        print("\n=== Score distribution (full out file) ===")
        for s in range(11):
            if scores.get(s, 0) > 0:
                bar = "█" * scores[s]
                print(f"  {s:>2}: {scores[s]:>4} {bar}")
        print(f"  errors: {errors}")
        print(f"\n=== Label distribution ===")
        for k, n in labels.most_common():
            print(f"  {k:<12} {n}")
        pos = labels.get("positive", 0)
        neg = labels.get("negative", 0)
        total = pos + neg
        if total > 0:
            print(f"\n  positive rate: {pos}/{total} = {pos/total*100:.1f}%")
        if halted:
            print("RUN HALTED (balance/error) — re-run the same command to resume.")


# ------------------------------------------------------------------
# Quick smoke test
# ------------------------------------------------------------------
def main():
    """Smoke-test the oracle on key examples from prompt.md."""
    oracle = ViolencePromotionOracle()

    test_articles = [
        {
            "id": "test-conflict-1",
            "title": "Russian Missile Strike Kills 12 in Kharkiv Apartment Block",
            "content": (
                "A Russian S-300 missile struck a residential apartment block in "
                "Kharkiv early Tuesday, killing 12 civilians and wounding 25. "
                "Emergency services pulled bodies from the rubble throughout the "
                "morning as rescue workers searched for survivors."
            ),
        },
        {
            "id": "test-recovery-1",
            "title": "Kharkiv Residents Return to Rebuilt Apartment Block Two Years After Strike",
            "content": (
                "Families returned to their newly rebuilt apartment block in Kharkiv "
                "this week, two years after a missile strike destroyed their homes. "
                "The reconstruction, funded by international donors, features new "
                "windows, reinforced walls, and a reopened community center."
            ),
        },
        {
            "id": "test-weapons-progress-1",
            "title": "Israel Opens Domestically-Produced Bomb Line, Reducing Reliance on US Imports",
            "content": (
                "Israel has inaugurated a new production line for domestically-manufactured "
                "aerial bombs, a move defense officials say will reduce the country's "
                "strategic reliance on US imports. The facility, operated by a state-owned "
                "defense contractor, will produce precision-guided munitions at scale. "
                "'This is a milestone for our defense industrial base and our ability to "
                "operate independently,' the defense ministry said in a statement."
            ),
        },
    ]

    for article in test_articles:
        print(f"\n--- {article['title'][:70]}... ---")
        result = oracle.score_article(article)
        print(f"  Score: {result['violence_score']}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Signals: {result['key_signals']}")
        if result.get("error"):
            print(f"  ERROR: {result['error']}")


if __name__ == "__main__":
    main()
