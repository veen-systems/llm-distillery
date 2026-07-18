"""
Unit tests for ground_truth.text_cleaning.is_scrape_junk().

Guards the ingestion check added after Solutions v4 calibration (DeepSeek
defect 3: a scraped cookie-consent page was scored from its headline). The
check must (a) catch boilerplate scrape artifacts and (b) never drop a genuine
article that merely mentions cookies/JS in passing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ground_truth.text_cleaning import is_scrape_junk


class TestJunkIsCaught:
    def test_cookie_consent_wall(self):
        art = {
            "title": "Cookie notice",
            "content": "We and our partners use cookies to store and access "
                       "information on your device. Accept all cookies to continue. "
                       "Manage your preferences in the cookie settings.",
        }
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is True
        assert reason.startswith("scrape_junk:")

    def test_javascript_required(self):
        art = {"title": "Loading", "content": "Please enable JavaScript to view this page."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_error_page(self):
        art = {"title": "404", "content": "404 - Page not found. The page you requested does not exist."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_paywall_stub(self):
        art = {"title": "Members only", "content": "Subscribe to continue reading this article."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_bot_check(self):
        art = {"title": "", "content": "Checking your browser before accessing the site. Verify you are human."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_empty_content(self):
        art = {"title": "Some headline", "content": ""}
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is True
        assert reason == "empty_or_stub_content"

    def test_near_empty_content(self):
        art = {"title": "Solar policy passes", "content": "Read more."}
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is True
        assert reason == "empty_or_stub_content"

    def test_junk_detected_from_title_field(self):
        # Body is short boilerplate; title carries the signature.
        art = {"title": "Enable cookies and reload the page", "content": "Loading content now please wait a moment."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True


class TestRealContentPasses:
    def test_long_article_mentioning_cookies_passes(self):
        # A genuine article about cookie regulation — long body, must NOT be dropped.
        body = " ".join(
            ["The European Parliament passed a binding reform of the ePrivacy "
             "directive requiring websites to obtain explicit consent before "
             "setting cookies, with a named enforcement agency and a two-year "
             "compliance timeline funded at fifty million euros."] * 6
        )
        art = {"title": "EU passes cookie-consent reform", "content": body}
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is False, reason

    def test_normal_solution_article_passes(self):
        body = " ".join(
            ["Costa Rica's payment-for-ecosystem-services program, funded by a "
             "fuel tax, now covers 1.3 million hectares and forest cover has "
             "risen from 26 percent to over 57 percent according to national "
             "land-survey data verified by the FAO."] * 5
        )
        art = {"title": "Costa Rica forest program", "content": body}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is False

    def test_short_real_brief_without_junk_signature_passes(self):
        # Short, but no boilerplate signature -> not junk (oracle will Step-1 it if needed).
        art = {
            "title": "Congestion charge cuts traffic",
            "content": "The city congestion charge cut traffic by 22 percent over "
                       "five years and revenue now funds public transit expansion.",
        }
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is False
