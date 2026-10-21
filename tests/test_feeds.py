"""Tests for the RSS feed and sitemap."""

import unittest
import xml.etree.ElementTree as ElementTree

from helpers import BASE_URL, SITE_TITLE, build_site, published_posts

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class RssFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.channel = ElementTree.fromstring(build_site().read("index.xml")).find("channel")

    def test_channel_metadata(self):
        self.assertEqual(self.channel.findtext("title"), SITE_TITLE)
        self.assertEqual(self.channel.findtext("link"), BASE_URL)

    def test_items_are_published_posts_newest_first(self):
        items = [(item.findtext("title"), item.findtext("link")) for item in self.channel.findall("item")]
        self.assertEqual(items, [(post.title, post.permalink) for post in published_posts()])

    def test_item_descriptions_are_present(self):
        for item in self.channel.findall("item"):
            with self.subTest(item=item.findtext("title")):
                self.assertTrue(item.findtext("description").strip())


class SitemapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = ElementTree.fromstring(build_site().read("sitemap.xml"))
        cls.locations = [loc.text for loc in root.findall("sm:url/sm:loc", SITEMAP_NS)]

    def test_includes_home_and_every_published_post(self):
        self.assertIn(BASE_URL, self.locations)
        for post in published_posts():
            with self.subTest(post=post.filename):
                self.assertIn(post.permalink, self.locations)

    def test_urls_are_https_under_blog(self):
        for location in self.locations:
            with self.subTest(location=location):
                self.assertTrue(location.startswith(BASE_URL))


if __name__ == "__main__":
    unittest.main()
