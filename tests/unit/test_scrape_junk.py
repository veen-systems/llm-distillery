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


class TestNonEnglishJunkIsCaught:
    # Solutions v4: production is ~29% non-English; the English-only list let
    # non-English consent/JS walls reach the oracle (nature_recovery gate in
    # embedding form). STRONG shims fire on a single hit; WEAK need >=2 or a stub.
    def test_javascript_disabled_german(self):
        art = {"title": "Fehler", "content": "Bitte aktivieren Sie JavaScript, um diese Seite anzuzeigen."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_javascript_disabled_french(self):
        art = {"title": "", "content": "Veuillez activer le JavaScript pour afficher ce contenu."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_javascript_disabled_spanish(self):
        art = {"title": "", "content": "JavaScript está desactivado en tu navegador."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_google_consent_wall_german(self):
        # The exact Solutions v4 consent-wall poison, in German — STRONG.
        art = {"title": "Google", "content": "Bevor Sie zu Google weitergehen. Wir verwenden Cookies."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_google_consent_wall_french(self):
        art = {"title": "Google", "content": "Avant d'accéder à Google, acceptez les cookies."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_cookie_wall_two_weak_spanish(self):
        # Two distinct weak Spanish signatures -> boilerplate-dominated -> junk.
        art = {
            "title": "Aviso",
            "content": "Usamos cookies para mejorar tu experiencia. "
                       "Acepta todas las cookies para continuar navegando.",
        }
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is True, reason
        assert "scrape_junk" in reason

    def test_paywall_stub_french(self):
        # Single weak signature but body-less stub (<= 8 words) -> junk.
        art = {"title": "Réservé aux abonnés", "content": "Abonnez-vous pour lire la suite."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True

    def test_page_not_found_italian(self):
        # "pagina non trovata" (weak) + English "404 ... error" (weak) = 2 hits.
        art = {"title": "404", "content": "Errore 404 - Pagina non trovata sul server."}
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is True


class TestNonEnglishRealContentPasses:
    def test_short_spanish_brief_single_weak_passes(self):
        # A genuine short Spanish brief mentioning cookie law ONCE must survive.
        art = {
            "title": "España adopta reglas de cookies",
            "content": "El gobierno español aprobó el martes una nueva política "
                       "de cookies que exige consentimiento explícito de los "
                       "usuarios en todos los sitios web, según anunció el ministerio.",
        }
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is False, reason

    def test_long_german_article_mentioning_cookies_passes(self):
        body = " ".join(
            ["Das Europäische Parlament verabschiedete eine verbindliche Reform "
             "der ePrivacy-Richtlinie, die von Webseiten eine ausdrückliche "
             "Einwilligung vor dem Setzen von Cookies verlangt, mit einer "
             "benannten Aufsichtsbehörde und einer zweijährigen Frist."] * 6
        )
        art = {"title": "EU verabschiedet Cookie-Reform", "content": body}
        is_junk, reason = is_scrape_junk(art)
        assert is_junk is False, reason

    def test_normal_french_solution_brief_passes(self):
        art = {
            "title": "Paris étend le budget participatif",
            "content": "La ville de Paris a étendu son budget participatif à "
                       "cent millions d'euros, permettant aux habitants de voter "
                       "directement sur les projets de quartier chaque année.",
        }
        is_junk, _ = is_scrape_junk(art)
        assert is_junk is False


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
