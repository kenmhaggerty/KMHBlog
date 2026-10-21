"""Tests for posts in content/post/ and the assets they reference."""

import os
import re
import unittest
from urllib.parse import unquote, urlparse

from helpers import BASE_URL, PROJECT_ROOT, build_site, load_posts, published_posts

REQUIRED_FIELDS = ["title", "date", "description", "draft"]


class FrontMatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.posts = load_posts()

    def test_required_fields_are_present_and_non_empty(self):
        for post in self.posts:
            for field in REQUIRED_FIELDS:
                with self.subTest(post=post.filename, field=field):
                    self.assertIn(field, post.front_matter)
                    self.assertNotEqual(post.front_matter[field], "")

    def test_dates_include_a_timezone(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                self.assertIsNotNone(post.date.tzinfo, "date should include a UTC offset")

    def test_titles_are_unique(self):
        titles = [post.title for post in self.posts]
        self.assertEqual(len(titles), len(set(titles)))

    def test_hero_images_exist(self):
        for post in self.posts:
            image = post.front_matter.get("image")
            if not image:
                continue
            with self.subTest(post=post.filename):
                self.assertTrue(os.path.isfile(os.path.join(PROJECT_ROOT, "static", "images", image)), image)

    def test_filenames_are_url_friendly_slugs(self):
        for post in self.posts:
            with self.subTest(post=post.filename):
                self.assertRegex(post.slug, r"^[a-z0-9]+(-[a-z0-9]+)*$")


class RenderedContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = build_site()

    def resolve_local(self, page, url):
        """Maps a URL found on `page` to a path in the build, or None if it is external."""
        parsed = urlparse(url)
        if parsed.scheme in ("mailto", "tel", "javascript", "data"):
            return None
        if parsed.netloc:
            if not url.startswith(BASE_URL):
                return None
            path = parsed.path[len("/blog/"):]
        elif parsed.path.startswith("/"):
            if not parsed.path.startswith("/blog/"):
                return "outside-blog:" + parsed.path
            path = parsed.path[len("/blog/"):]
        else:
            path = os.path.normpath(os.path.join(os.path.dirname(page), parsed.path))
        path = unquote(path)
        if path in ("", ".") or path.endswith("/"):
            path = os.path.join(path, "index.html")
        elif os.path.isdir(self.site.path(path)):
            path = os.path.join(path, "index.html")
        return path

    def test_local_links_and_assets_resolve(self):
        for page in self.site.html_files():
            document = self.site.html(page)
            for node in document.iter():
                for attr in ("href", "src"):
                    url = node.attrs.get(attr)
                    if not url or url.startswith("#"):
                        continue
                    path = self.resolve_local(page, url)
                    if path is None:
                        continue
                    with self.subTest(page=page, url=url):
                        self.assertFalse(path.startswith("outside-blog:"), "root-relative URL escapes /blog/")
                        self.assertTrue(self.site.exists(path), "broken reference")

    def test_images_in_posts_have_files_in_static(self):
        for post in load_posts():
            for src in re.findall(r'<img[^>]+src="(/blog/images/[^"]+)"', post.body):
                with self.subTest(post=post.filename, src=src):
                    self.assertTrue(os.path.isfile(os.path.join(PROJECT_ROOT, "static", src[len("/blog/"):])))

    def test_article_links_use_https(self):
        for post in published_posts():
            article = self.site.html(post.slug, "index.html").find("article")
            for link in article.find_all("a"):
                href = link.attrs.get("href", "")
                with self.subTest(post=post.filename, href=href):
                    self.assertFalse(href.startswith("http://"))

    def test_embedded_scripts_and_images_use_https(self):
        # Mixed content is blocked by browsers on an HTTPS page.
        for post in published_posts():
            article = self.site.html(post.slug, "index.html").find("article")
            for node in article.find_all("script") + article.find_all("img") + article.find_all("iframe"):
                src = node.attrs.get("src", "")
                with self.subTest(post=post.filename, src=src):
                    self.assertFalse(src.startswith("http://"))

    def test_raw_html_is_rendered_unescaped(self):
        # config.toml sets markup.goldmark.renderer.unsafe = true, which posts rely on for captions and figures.
        for post in published_posts():
            if '<span class="caption">' not in post.body:
                continue
            with self.subTest(post=post.filename):
                html = self.site.read(post.slug, "index.html")
                self.assertIn('<span class="caption">', html)
                self.assertNotIn("&lt;span class=&quot;caption", html)

    def test_captions_start_with_bold_position_label(self):
        for post in published_posts():
            article = self.site.html(post.slug, "index.html").find("article")
            for caption in article.find_all("span", cls="caption"):
                with self.subTest(post=post.filename, caption=caption.clean_text()[:40]):
                    label = caption.children[0] if caption.children else None
                    self.assertEqual(getattr(label, "tag", None), "b", "caption should start with e.g. <b>Above</b>")
                    self.assertIn(label.clean_text().lower(), {"above", "below", "left", "right"})


class UsingClaudePostTests(unittest.TestCase):
    """Regression tests for markup that custom.css targets in using-claude.md."""

    @classmethod
    def setUpClass(cls):
        cls.article = build_site().html("using-claude", "index.html").find("article")

    def test_gist_is_wrapped_in_scrollable_container(self):
        container = self.article.find("div", cls="scrollable-gist")
        self.assertIsNotNone(container)
        script = container.find("script")
        self.assertRegex(script.attrs["src"], r"^https://gist\.github\.com/kenmhaggerty/[0-9a-f]+\.js$")

    def test_h4_directly_follows_caption(self):
        # `.caption + h4` only applies when the heading is the caption's next sibling.
        followers = [caption.next_element() for caption in self.article.find_all("span", cls="caption")]
        self.assertIn("h4", [node.tag for node in followers if node is not None])


if __name__ == "__main__":
    unittest.main()
