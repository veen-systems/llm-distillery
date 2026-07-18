"""
Unit tests for ground_truth.text_cleaning.is_scrape_junk().

Guards the ingestion check added after Solutions v4 calibration (DeepSeek
defect 3: a scraped cookie-consent page was scored from its headline). The
check must (a) catch boilerplate scrape artifacts and (b) never drop a genuine
article — including short in-lens briefs that merely mention a topical phrase,
and non-space-delimited (CJK/Thai) content. Regression cases from the
2026-07-18 multi-model review are marked inline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ground_truth.text_cleaning import is_scrape_junk


class TestJunkIsCaught:
    def test_cookie_consent_wall(self):
        # >=2 distinct weak signatures -> boilerplate-dominated -> junk.
        art = {
            "title": "Cookie notice",
            "content": "We and our partners use cookies to store and access "
                       "information on your device. Accept all cookies to continue. "
                       "Manage your preferences in the cookie settings.",
        }
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is True
        assert "scrape_junk" in reason

    def test_javascript_required(self):
        # STRONG signature -> single hit suffices.
        art = {"title": "Loading", "content": "Please enable JavaScript to view this page."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_error_page(self):
        # Two weak hits ("404 ... not found" + "page not found").
        art = {"title": "404", "content": "404 - Page not found. The page you requested does not exist."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_paywall_stub(self):
        # Single weak signature but body-less stub (<= 8 words) -> junk.
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
        # Body is short boilerplate; title carries a STRONG signature.
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

    def test_short_governance_brief_single_weak_signature_passes(self):
        # REGRESSION (review MED): a genuine short in-lens brief that mentions ONE
        # topical phrase ("cookie consent") must survive — one weak hit is not junk.
        art = {
            "title": "EU adopts cookie-consent rules",
            "content": "The European Union adopted new cookie consent rules on "
                       "Tuesday requiring explicit user opt-in across all member "
                       "states, the parliament announced after a final vote.",
        }
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is False, reason

    def test_cjk_short_article_passes(self):
        # REGRESSION (review HIGH): non-space-delimited languages collapse under
        # split(); a genuine short Chinese article must NOT read as empty.
        art = {
            "title": "太阳能政策",
            "content": "中国政府本周宣布了一项新的太阳能补贴计划，"
                       "覆盖超过一万户低收入家庭，首批八百户已完成安装。",
        }
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
        art = {
            "title": "Congestion charge cuts traffic",
            "content": "The city congestion charge cut traffic by 22 percent over "
                       "five years and revenue now funds public transit expansion.",
        }
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is False
