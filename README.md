# KMHBlog
Personal blog of Ken M. Haggerty.

## Tests

The tests build the site with Hugo into a temporary directory and check the generated HTML, CSS, RSS feed, and sitemap. They need only `hugo` (with the `angels-ladder` theme in `themes/`) and Python 3.

```sh
python3 -m unittest discover -s tests -v
```

To run the tests automatically before every commit (and block commits when they fail), enable the repo's hooks once per clone:

```sh
git config core.hooksPath .githooks
```

Use `git commit --no-verify` to skip the hook for a single commit.
