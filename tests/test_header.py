"""Tests for layouts/partials/header.html, which every page includes."""

import re
import time
import unittest

from helpers import BASE_URL, SITE_TITLE, build_site, published_posts

STYLESHEETS = ["sanitize.css", "responsive.css", "highlight_monokai.css", "theme.css", "custom.css"]
SLIDER_STYLESHEET = "https://cdn.jsdelivr.net/npm/img-comparison-slider@8/dist/styles.css"
DEFAULT_COVER = BASE_URL + "images/hero.png"


def meta_content(document, **attrs):
    node = document.find("meta", **attrs)
    return node.attrs.get("content") if node else None


class HeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = build_site()
        cls.home = cls.site.html("index.html")
        cls.posts = published_posts()
        cls.pages = [p for p in cls.site.html_files() if p != "page/1/index.html"]

    # Basic page structure

    def test_html_lang_matches_site_locale(self):
        for path in self.pages:
            with self.subTest(page=path):
                self.assertEqual(self.site.html(path).find("html").attrs.get("lang"), "en-us")

    def test_charset_and_viewport(self):
        for path in self.pages:
            with self.subTest(page=path):
                document = self.site.html(path)
                self.assertEqual(document.find("meta", charset="UTF-8").attrs["charset"], "UTF-8")
                self.assertEqual(
                    meta_content(document, name="viewport"),
                    "width=device-width,user-scalable=no,maximum-scale=1,initial-scale=1",
                )

    # Titles

    def test_home_title_is_site_title_only(self):
        self.assertEqual(self.home.find("title").clean_text(), SITE_TITLE)

    def test_post_title_is_suffixed_with_site_title(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                document = self.site.html(post.slug, "index.html")
                expected = f"{post.title} | {SITE_TITLE}"
                self.assertEqual(document.find("title").clean_text(), expected)
                self.assertEqual(meta_content(document, name="twitter:title"), expected)

    # Canonical URL

    def test_canonical_url_is_https_permalink(self):
        self.assertEqual(self.home.find("link", rel="canonical").attrs["href"], BASE_URL)
        for post in self.posts:
            with self.subTest(post=post.filename):
                document = self.site.html(post.slug, "index.html")
                self.assertEqual(document.find("link", rel="canonical").attrs["href"], post.permalink)

    # Stylesheets

    def test_stylesheets_are_absolute_and_in_cascade_order(self):
        for path in self.pages:
            with self.subTest(page=path):
                links = self.site.html(path).find_all("link", rel="stylesheet")
                hrefs = [link.attrs["href"].split("?")[0] for link in links]
                expected = [BASE_URL + "css/" + name for name in STYLESHEETS]
                expected.insert(-1, SLIDER_STYLESHEET)
                self.assertEqual(hrefs, expected)

    def test_custom_css_has_cache_busting_version(self):
        versions = set()
        for path in self.pages:
            with self.subTest(page=path):
                href = self.site.html(path).find_all("link", rel="stylesheet")[-1].attrs["href"]
                match = re.fullmatch(re.escape(BASE_URL + "css/custom.css") + r"\?v=(\d+)", href)
                self.assertIsNotNone(match, "custom.css is missing its ?v= cache buster: " + href)
                versions.add(int(match.group(1)))
        self.assertEqual(len(versions), 1, "every page in a build should share one version")
        self.assertLess(abs(versions.pop() - time.time()), 24 * 60 * 60, "version should be the build time")

    # RSS

    def test_rss_alternate_and_feed_links(self):
        for rel in ["alternate", "feed"]:
            with self.subTest(rel=rel):
                link = self.home.find("link", rel=rel)
                self.assertEqual(link.attrs["href"], BASE_URL + "index.xml")
                self.assertEqual(link.attrs["type"], "application/rss+xml")
                self.assertEqual(link.attrs["title"], SITE_TITLE)

    # Open Graph and Twitter Card

    def test_post_images_use_front_matter_image_or_default_cover(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                document = self.site.html(post.slug, "index.html")
                image = post.front_matter.get("image")
                expected = BASE_URL + "images/" + image if image else DEFAULT_COVER
                self.assertEqual(meta_content(document, property="og:image"), expected)
                self.assertEqual(meta_content(document, name="twitter:image"), expected)
                self.assertEqual(meta_content(document, name="twitter:card"), "summary_large_image")

    def test_home_uses_default_cover_image(self):
        self.assertEqual(meta_content(self.home, property="og:image"), DEFAULT_COVER)

    def test_post_descriptions(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                document = self.site.html(post.slug, "index.html")
                self.assertEqual(meta_content(document, property="og:description"), post.front_matter["description"])
                self.assertEqual(meta_content(document, name="twitter:description"), post.front_matter["description"])

    def test_og_description_omitted_without_description(self):
        self.assertIsNone(self.home.find("meta", property="og:description"))

    def test_twitter_site_and_creator(self):
        for name in ["twitter:site", "twitter:creator"]:
            with self.subTest(name=name):
                self.assertEqual(meta_content(self.home, name=name), "@kenmhaggerty")

    def test_share_this_is_disabled(self):
        self.assertNotIn("sharethis", self.site.read("index.html").lower())

    # Site header

    def test_site_title_links_to_blog_home(self):
        link = self.home.find("div", id="site-title").find("a")
        self.assertEqual(link.attrs["href"], BASE_URL)
        self.assertEqual(link.clean_text(), SITE_TITLE)

    def test_social_links(self):
        links = self.home.find("div", id="social").find_all("a")
        self.assertEqual(
            [(link.clean_text(), link.attrs["href"]) for link in links],
            [
                ("Home", "https://www.kenmhaggerty.com"),
                ("Twitter", "https://twitter.com/kenmhaggerty"),
                ("GitHub", "https://github.com/kenmhaggerty"),
                ("RSS", BASE_URL + "index.xml"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
