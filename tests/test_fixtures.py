"""Tests that build a copy of the site with fixture posts to cover template branches real posts don't use.

Covers tags (list.html and tag links), drafts, future posts, pagination, posts without a hero image or
description, the Markdown extras enabled in config.toml, and the default archetype.
"""

import os
import subprocess
import unittest

from helpers import (
    BASE_URL,
    copy_project,
    load_posts,
    make_temp_dir,
    parse_front_matter,
    published_posts,
    run_hugo,
    write_post,
)

PAGE_SIZE = 10


def summary_titles(document):
    return [summary.find("h2").find("a").clean_text() for summary in document.find_all("div", cls="summary")]


class FixtureSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = copy_project("kmhblog-fixtures-")
        write_post(
            cls.source,
            "fixture-tagged.md",
            {"date": "2010-01-03T12:00:00-05:00", "draft": False, "title": "Fixture Tagged", "tags": ["Swift UI", "iOS", "firebase"]},
            "Markdown extras: ==marked== ~~deleted~~ H~2~O x^2^.\n\n#### Fixture Heading\n\nBody text.",
        )
        write_post(
            cls.source,
            "fixture-plain-1.md",
            {"date": "2010-01-02T12:00:00-05:00", "draft": False, "title": "Fixture Plain One"},
            "Body text.",
        )
        write_post(
            cls.source,
            "fixture-plain-2.md",
            {"date": "2010-01-01T12:00:00-05:00", "draft": False, "title": "Fixture Plain Two"},
            "Body text.",
        )
        write_post(
            cls.source,
            "fixture-draft.md",
            {"date": "2010-01-04T12:00:00-05:00", "draft": True, "title": "Fixture Draft"},
            "Body text.",
        )
        write_post(
            cls.source,
            "fixture-future.md",
            {"date": "2999-01-01T12:00:00-05:00", "draft": False, "title": "Fixture Future"},
            "Body text.",
        )
        cls.site = run_hugo(cls.source, make_temp_dir("kmhblog-fixtures-out-"))
        cls.drafts_site = run_hugo(cls.source, make_temp_dir("kmhblog-fixtures-drafts-"), "--buildDrafts")
        cls.posts = published_posts(load_posts(os.path.join(cls.source, "content", "post")))
        cls.visible_posts = [p for p in cls.posts if p.slug != "fixture-future"]

    # Drafts and future posts

    def test_drafts_are_not_published(self):
        self.assertFalse(self.site.exists("fixture-draft", "index.html"))
        self.assertNotIn("Fixture Draft", self.site.read("index.xml"))

    def test_drafts_are_labeled_when_built_with_drafts(self):
        self.assertTrue(self.drafts_site.exists("fixture-draft", "index.html"))
        listing = self.drafts_site.html("post", "index.html")
        self.assertIn("Fixture Draft :: DRAFT", summary_titles(listing))

    def test_future_posts_are_not_published(self):
        self.assertFalse(self.site.exists("fixture-future", "index.html"))

    def test_future_posts_do_not_change_copyright_year(self):
        footer = self.site.html("index.html").find("footer", role="contentinfo")
        self.assertIn(str(self.visible_posts[0].date.year), footer.clean_text())

    # Pagination (index.html)

    def test_home_page_is_paginated(self):
        first_page = summary_titles(self.site.html("index.html"))
        second_page = summary_titles(self.site.html("page", "2", "index.html"))
        titles = [post.title for post in self.visible_posts]
        self.assertEqual(first_page, titles[:PAGE_SIZE])
        self.assertEqual(second_page, titles[PAGE_SIZE:2 * PAGE_SIZE])

    def test_pagination_links_between_pages(self):
        first_nav = self.site.html("index.html").find("nav")
        hrefs = [link.attrs.get("href") for link in first_nav.find_all("a")]
        self.assertIn("/blog/page/2/", hrefs)
        second_nav = self.site.html("page", "2", "index.html").find("nav")
        self.assertIn("/blog/", [link.attrs.get("href") for link in second_nav.find_all("a")])

    # Tags (list.html and the tag links on index.html and single.html)

    def test_tag_links_on_post_page(self):
        meta = self.site.html("fixture-tagged", "index.html").find("div", cls="meta")
        links = [(link.clean_text(), link.attrs["href"]) for link in meta.find_all("a")]
        self.assertEqual(
            links,
            [("Swift UI", "/blog/tags/swift-ui"), ("iOS", "/blog/tags/ios"), ("firebase", "/blog/tags/firebase")],
        )
        self.assertIn("#Swift UI", meta.clean_text())

    def test_tag_links_on_listing_pages(self):
        for path in [("index.html",), ("page", "2", "index.html"), ("post", "index.html")]:
            document = self.site.html(*path)
            for summary in document.find_all("div", cls="summary"):
                if summary.find("h2").clean_text() != "Fixture Tagged":
                    continue
                with self.subTest(page="/".join(path)):
                    hrefs = [link.attrs["href"] for link in summary.find("div", cls="meta").find_all("a")]
                    self.assertEqual(hrefs, ["/blog/tags/swift-ui", "/blog/tags/ios", "/blog/tags/firebase"])

    def test_tag_pages_list_tagged_posts_and_keep_tag_casing(self):
        # config.toml sets capitalizeListTitles = false so tags like "iOS" aren't shown as "IOS".
        for slug, title in [("swift-ui", "#Swift UI"), ("ios", "#iOS"), ("firebase", "#firebase")]:
            with self.subTest(tag=slug):
                document = self.site.html("tags", slug, "index.html")
                self.assertEqual(document.find("div", cls="article-header").clean_text(), title)
                self.assertEqual(summary_titles(document), ["Fixture Tagged"])

    def test_tag_page_titles(self):
        document = self.site.html("tags", "ios", "index.html")
        self.assertEqual(document.find("title").clean_text(), "iOS | Blog • Ken M. Haggerty")

    # Posts without a hero image or description (header.html fallbacks)

    def test_post_without_image_uses_default_cover(self):
        document = self.site.html("fixture-plain-1", "index.html")
        self.assertEqual(document.find("meta", property="og:image").attrs["content"], BASE_URL + "images/hero.png")

    def test_post_without_description_omits_og_description(self):
        document = self.site.html("fixture-plain-1", "index.html")
        self.assertIsNone(document.find("meta", property="og:description"))

    # Markdown extras enabled in config.toml

    def test_markdown_extras_are_rendered(self):
        article = self.site.html("fixture-tagged", "index.html").find("article")
        for tag, text in [("mark", "marked"), ("del", "deleted"), ("sub", "2"), ("sup", "2")]:
            with self.subTest(tag=tag):
                node = article.find(tag)
                self.assertIsNotNone(node, "<{}> was not rendered".format(tag))
                self.assertEqual(node.clean_text(), text)

    def test_single_tildes_are_subscript_not_strikethrough(self):
        # Goldmark's strikethrough extension (disabled in config.toml) would render H~2~O as H<del>2</del>O.
        article = self.site.html("fixture-tagged", "index.html").find("article")
        self.assertIn("H<sub>2</sub>O", self.site.read("fixture-tagged", "index.html"))
        self.assertEqual([node.clean_text() for node in article.find_all("del")], ["deleted"])

    def test_markdown_headings_get_ids(self):
        heading = self.site.html("fixture-tagged", "index.html").find("h4")
        self.assertEqual(heading.attrs.get("id"), "fixture-heading")


class ArchetypeTests(unittest.TestCase):
    def test_new_posts_start_as_drafts(self):
        source = copy_project("kmhblog-archetype-")
        result = subprocess.run(
            ["hugo", "new", "--source", source, "post/archetype-check.md"], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(os.path.join(source, "content", "post", "archetype-check.md"), encoding="utf-8") as f:
            front_matter, body = parse_front_matter(f.read())
        self.assertIs(front_matter["draft"], True)
        self.assertEqual(front_matter["image"], "")
        self.assertEqual(front_matter["description"], "")
        self.assertEqual(body.strip(), "Hello World!")


if __name__ == "__main__":
    unittest.main()
