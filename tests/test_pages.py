"""Tests for layouts/index.html, layouts/_default/single.html, and layouts/_default/list.html."""

import unittest

from helpers import BASE_URL, build_site, published_posts


def summaries(document):
    """(title, permalink, meta text) for each post summary on a listing page."""
    results = []
    for summary in document.find_all("div", cls="summary"):
        link = summary.find("h2").find("a")
        results.append((link.clean_text(), link.attrs["href"], summary.find("div", cls="meta").clean_text()))
    return results


class HomePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = build_site()
        cls.home = cls.site.html("index.html")
        cls.posts = published_posts()

    def test_heading(self):
        main = self.home.find("main", id="index")
        self.assertEqual(main.find("div", cls="article-header").clean_text(), "Recent Articles")

    def test_lists_published_posts_newest_first(self):
        self.assertEqual(
            summaries(self.home),
            [(post.title, post.permalink, post.display_date) for post in self.posts[:10]],
        )

    def test_no_posts_are_marked_as_drafts(self):
        self.assertNotIn(":: DRAFT", self.home.text())

    def test_pagination_nav_is_present(self):
        self.assertIsNotNone(self.home.find("nav"))

    def test_first_paginator_page_redirects_home(self):
        self.assertIn(BASE_URL, self.site.read("page", "1", "index.html"))


class PostListTests(unittest.TestCase):
    """The /post/ section page rendered by list.html."""

    @classmethod
    def setUpClass(cls):
        cls.document = build_site().html("post", "index.html")

    def test_heading_is_hashtag_section_title(self):
        main = self.document.find("main", id="list")
        self.assertEqual(main.find("div", cls="article-header").clean_text(), "#Posts")

    def test_lists_every_published_post_newest_first(self):
        self.assertEqual(
            summaries(self.document),
            [(post.title, post.permalink, post.display_date) for post in published_posts()],
        )


class SinglePostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = build_site()
        cls.posts = published_posts()

    def document(self, post):
        return self.site.html(post.slug, "index.html")

    def test_heading_title_and_date(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                header = self.document(post).find("main", id="single").find("div", cls="article-header")
                link = header.find("h1").find("a")
                self.assertEqual(link.clean_text(), post.title)
                self.assertEqual(link.attrs["href"], ".")
                self.assertEqual(header.find("div", cls="meta").clean_text(), post.display_date)

    def test_content_is_rendered_inside_article(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                article = self.document(post).find("article")
                self.assertGreater(len(article.clean_text()), 200)
                self.assertNotRegex(article.text(), r"(?m)^#{1,6} ", "unrendered Markdown heading")

    def test_previous_and_next_links_follow_date_order(self):
        for index, post in enumerate(self.posts):
            with self.subTest(post=post.filename):
                nav = self.document(post).find("nav", cls="pagination-single")
                newer = self.posts[index - 1] if index > 0 else None
                older = self.posts[index + 1] if index + 1 < len(self.posts) else None
                for cls, rel, expected in [("previous", "prev", newer), ("next", "next", older)]:
                    span = nav.find("span", cls=cls)
                    if expected is None:
                        self.assertIsNone(span, "unexpected '{}' link".format(cls))
                        continue
                    link = span.find("a")
                    self.assertEqual(link.attrs["href"], expected.permalink)
                    self.assertEqual(link.attrs["rel"], rel)
                    self.assertEqual(link.clean_text(), expected.title)

    def test_comments_and_share_buttons_are_disabled(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                document = self.document(post)
                self.assertIsNone(document.find("div", id="disqus_thread"))
                self.assertIsNone(document.find("div", id="share-this"))


if __name__ == "__main__":
    unittest.main()
