"""Tests for layouts/partials/footer.html, which every page includes."""

import unittest

from helpers import build_site, published_posts


class FooterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = build_site()
        cls.pages = [p for p in cls.site.html_files() if p != "page/1/index.html"]

    def test_copyright_uses_year_of_latest_post(self):
        latest_year = published_posts()[0].date.year
        for path in self.pages:
            with self.subTest(page=path):
                footer = self.site.html(path).find("footer", role="contentinfo")
                self.assertEqual(footer.clean_text(), f"Written by Ken M. Haggerty • {latest_year}")

    def test_highlight_js_is_loaded_and_initialized(self):
        for path in self.pages:
            with self.subTest(page=path):
                document = self.site.html(path)
                sources = [s.attrs.get("src") for s in document.find_all("script")]
                self.assertIn("/blog/js/highlight.pack.js", sources)
                self.assertIn("hljs.initHighlightingOnLoad();", self.site.read(path))

    def test_optional_integrations_are_disabled(self):
        html = self.site.read("index.html")
        self.assertNotIn("google-analytics.com", html)
        self.assertNotIn("disqus", html)
        self.assertNotIn('width="64" height="64"', html)  # profile image


if __name__ == "__main__":
    unittest.main()
