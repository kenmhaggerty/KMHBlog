# KMHBlog

Personal blog of Ken M. Haggerty.

## Tests

The tests build the site with Hugo into a temporary directory and check the generated HTML, CSS, RSS feed, and sitemap. They need only `hugo` (with the `angels-ladder` theme in `themes/`) and Python 3.

```sh
python3 -m unittest discover -s tests -v
```

## Linting and Formatting

Posts and `README.md` are checked with [markdownlint](https://github.com/DavidAnson/markdownlint-cli2) (`.markdownlint-cli2.jsonc`), and `static/css/custom.css` with [Stylelint](https://stylelint.io) (`.stylelintrc.json`) and [Prettier](https://prettier.io). Install the tools once with Node.js:

```sh
npm install
npm run lint     # check everything
npm run format   # auto-fix what can be fixed
```

## Pre-commit Hook

To lint and run the tests automatically before every commit (and block commits when either fails), enable the repo's hooks once per clone:

```sh
git config core.hooksPath .githooks
```

Use `git commit --no-verify` to skip the hook for a single commit.
