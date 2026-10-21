"""Shared helpers for the blog's build tests.

Each test module builds the site with Hugo into a temporary directory (once per
test run) and asserts against the generated HTML, CSS, and XML. Only the Python
standard library and the `hugo` binary are required.
"""

import atexit
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://www.kenmhaggerty.com/blog/"
SITE_TITLE = "Blog • Ken M. Haggerty"
POSTS_DIR = os.path.join(PROJECT_ROOT, "content", "post")

_temp_dirs = []
_build_cache = {}


@atexit.register
def _cleanup():
    for path in _temp_dirs:
        shutil.rmtree(path, ignore_errors=True)


def make_temp_dir(prefix):
    path = tempfile.mkdtemp(prefix=prefix)
    _temp_dirs.append(path)
    return path


# Building
# --------------------------------------------------

class Build:
    """The output of a single `hugo` build."""

    def __init__(self, source, destination, log):
        self.source = source
        self.destination = destination
        self.log = log

    def path(self, *parts):
        return os.path.join(self.destination, *parts)

    def exists(self, *parts):
        return os.path.exists(self.path(*parts))

    def read(self, *parts):
        with open(self.path(*parts), encoding="utf-8") as f:
            return f.read()

    def html(self, *parts):
        return parse_html(self.read(*parts))

    def html_files(self):
        pattern = os.path.join(self.destination, "**", "*.html")
        return sorted(os.path.relpath(p, self.destination) for p in glob.glob(pattern, recursive=True))


def run_hugo(source, destination, *args):
    result = subprocess.run(
        ["hugo", "--source", source, "--destination", destination, "--cleanDestinationDir", "--logLevel", "warn", *args],
        capture_output=True,
        text=True,
    )
    log = result.stdout + result.stderr
    if result.returncode != 0:
        raise AssertionError("hugo build failed:\n" + log)
    return Build(source, destination, log)


def build_site():
    """Builds the real site exactly as it would be deployed (cached per test run)."""
    if "site" not in _build_cache:
        _build_cache["site"] = run_hugo(PROJECT_ROOT, make_temp_dir("kmhblog-site-"))
    return _build_cache["site"]


def copy_project(prefix):
    """Copies the project (including the local theme) so tests can add fixture content."""
    destination = os.path.join(make_temp_dir(prefix), "site")
    shutil.copytree(
        PROJECT_ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "public", "resources", "tests", ".hugo_build.lock", ".DS_Store"),
    )
    return destination


def write_post(source, filename, front_matter, body):
    lines = ["+++"]
    for key, value in front_matter.items():
        lines.append("{} = {}".format(key, json.dumps(value)))
    lines += ["+++", "", body, ""]
    with open(os.path.join(source, "content", "post", filename), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# Content
# --------------------------------------------------

class Post:
    def __init__(self, filename, front_matter, body):
        self.filename = filename
        self.slug = os.path.splitext(filename)[0]
        self.front_matter = front_matter
        self.body = body

    @property
    def title(self):
        return self.front_matter.get("title")

    @property
    def date(self):
        return datetime.datetime.fromisoformat(self.front_matter["date"])

    @property
    def draft(self):
        return self.front_matter.get("draft", False)

    @property
    def permalink(self):
        return BASE_URL + self.slug + "/"

    @property
    def display_date(self):
        # Matches the Go layout "Jan 2, 2006" used by the templates.
        return "{} {}, {}".format(self.date.strftime("%b"), self.date.day, self.date.year)


def parse_front_matter(text):
    """Parses the flat `key = value` TOML front matter used by this blog's posts."""
    match = re.match(r"\+\+\+\n(.*?)\n\+\+\+\n?(.*)", text, re.S)
    if not match:
        raise ValueError("missing +++ TOML front matter")
    front_matter = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if value in ("true", "false"):
            front_matter[key.strip()] = value == "true"
        else:
            front_matter[key.strip()] = json.loads(value)
    return front_matter, match.group(2)


def load_posts(posts_dir=POSTS_DIR):
    posts = []
    for path in sorted(glob.glob(os.path.join(posts_dir, "*.md"))):
        with open(path, encoding="utf-8") as f:
            front_matter, body = parse_front_matter(f.read())
        posts.append(Post(os.path.basename(path), front_matter, body))
    return posts


def published_posts(posts=None):
    """Published posts, newest first (the order Hugo lists them in)."""
    posts = load_posts() if posts is None else posts
    return sorted((p for p in posts if not p.draft), key=lambda p: p.date, reverse=True)


# HTML parsing
# --------------------------------------------------

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []

    @property
    def classes(self):
        return self.attrs.get("class", "").split()

    def text(self):
        parts = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return "".join(parts)

    def clean_text(self):
        return " ".join(self.text().split())

    def iter(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.iter()

    def find_all(self, tag=None, cls=None, **attrs):
        results = []
        for node in self.iter():
            if tag and node.tag != tag:
                continue
            if cls and cls not in node.classes:
                continue
            if any(node.attrs.get(k.rstrip("_")) != v for k, v in attrs.items()):
                continue
            results.append(node)
        return results

    def find(self, tag=None, cls=None, **attrs):
        results = self.find_all(tag, cls, **attrs)
        return results[0] if results else None

    def next_element(self):
        """The next sibling element, skipping whitespace-only text."""
        siblings = self.parent.children
        for sibling in siblings[siblings.index(self) + 1:]:
            if isinstance(sibling, Node):
                return sibling
            if sibling.strip():
                return None
        return None


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {})
        self.current = self.root
        self.doctype = None
        self.unmatched_end_tags = []

    def handle_decl(self, decl):
        self.doctype = decl

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.current)
        self.current.children.append(node)
        if tag not in VOID_TAGS:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.current)
        self.current.children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is self.root:
            self.unmatched_end_tags.append(tag)
            return
        self.current = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse_html(text):
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    document = builder.root
    document.doctype = builder.doctype
    document.unmatched_end_tags = builder.unmatched_end_tags
    return document
