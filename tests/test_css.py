"""Tests for static/css/custom.css."""

import os
import re
import unittest

from helpers import PROJECT_ROOT, build_site

CUSTOM_CSS = os.path.join(PROJECT_ROOT, "static", "css", "custom.css")


def parse_rules(css):
    """Maps each selector to its declarations, e.g. {".caption + h4": {"padding-top": "25px"}}."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules = {}
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        declarations = {}
        for declaration in body.split(";"):
            if ":" in declaration:
                name, _, value = declaration.partition(":")
                declarations[name.strip()] = value.strip()
        for selector in selectors.split(","):
            rules.setdefault(" ".join(selector.split()), {}).update(declarations)
    return rules


class CustomCssTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CUSTOM_CSS, encoding="utf-8") as f:
            cls.css = f.read()
        cls.rules = parse_rules(cls.css)

    def assertRule(self, selector, **declarations):
        self.assertIn(selector, self.rules, "missing rule for " + selector)
        for name, value in declarations.items():
            self.assertEqual(self.rules[selector].get(name.replace("_", "-")), value, selector)

    def test_braces_are_balanced(self):
        depth = 0
        for char in self.css:
            depth += {"{": 1, "}": -1}.get(char, 0)
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)

    def test_every_rule_has_declarations(self):
        for selector, declarations in self.rules.items():
            with self.subTest(selector=selector):
                self.assertTrue(declarations, "empty rule")

    def test_build_serves_project_css_instead_of_theme_css(self):
        # The theme ships its own css/custom.css; the project's copy must take precedence.
        self.assertEqual(build_site().read("css", "custom.css"), self.css)

    # Regression tests for specific fixes

    def test_scrollable_gist_has_max_height(self):
        self.assertRule(".scrollable-gist .gist-data", max_height="400px", overflow_y="auto")

    def test_h4_after_caption_has_gap(self):
        self.assertRule(".caption + h4", padding_top="25px")

    def test_list_items_are_spaced(self):
        self.assertRule("article li:not(:last-child)", margin_bottom="8px")

    def test_gist_snippets_have_border_and_background(self):
        self.assertRule(".gist .gist-file .gist-data", background_color="#fbfbfb", box_shadow="inset 0 0 0 1px #eee")
        self.assertRule(".gist .gist-data .highlight", background_color="transparent")

    def test_figures_and_captions(self):
        self.assertRule("div.figure", text_align="center")
        self.assertRule(".caption", font_size="smaller")

    def test_article_header_color(self):
        self.assertRule(".article-header", color="#29abe2")
        self.assertRule("div.article-header h1 a", color="#29abe2")
        self.assertRule("div.article-header h1 a:visited", color="#29abe2")


if __name__ == "__main__":
    unittest.main()
