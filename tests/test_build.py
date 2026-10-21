import unittest

from helpers import build_site, published_posts


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = build_site()

    def test_build_has_no_warnings_or_errors(self):
        for line in self.site.log.splitlines():
            self.assertNotRegex(line, r"\b(WARN|ERROR)\b", "Hugo reported a problem:\n" + self.site.log)

    def test_expected_pages_are_generated(self):
        for path in ["index.html", "index.xml", "sitemap.xml", "post/index.html", "tags/index.html"]:
            with self.subTest(path=path):
                self.assertTrue(self.site.exists(path), path + " was not generated")

    def test_every_published_post_has_a_page_at_its_filename(self):
        for post in published_posts():
            with self.subTest(post=post.filename):
                self.assertTrue(self.site.exists(post.slug, "index.html"))

    def test_static_and_theme_assets_are_copied(self):
        for path in [
            "css/sanitize.css",
            "css/responsive.css",
            "css/highlight_monokai.css",
            "css/theme.css",
            "css/custom.css",
            "js/highlight.pack.js",
            "images/hero.png",
        ]:
            with self.subTest(path=path):
                self.assertTrue(self.site.exists(path), path + " is missing from the build")

    def test_pages_have_a_doctype_and_balanced_end_tags(self):
        for path in self.site.html_files():
            with self.subTest(page=path):
                document = self.site.html(path)
                if path == "page/1/index.html":
                    continue  # Hugo's redirect alias for the first paginator page.
                self.assertEqual(document.doctype.lower(), "doctype html")
                self.assertEqual(document.unmatched_end_tags, [], "unmatched closing tags")


if __name__ == "__main__":
    unittest.main()
