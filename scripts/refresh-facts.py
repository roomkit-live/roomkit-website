#!/usr/bin/env python3
"""Refresh build-time facts on the homepage from the roomkit checkout.

Run from the website repo root (``make gather`` does). Updates, in index.html:

  - every element carrying ``data-fact="..."``:
      version        latest git tag of ../roomkit (fallback: _version.py)
      channel-types  members of ChannelType in models/enums.py
      hook-triggers  members of HookTrigger in models/enums.py
      tests          count of test functions under ../roomkit/tests
  - the cards between ``<!-- latest-posts:start -->`` and
    ``<!-- latest-posts:end -->``, taken from blog/index.html (newest first).

Missing sources degrade to warnings so the site still builds.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOMKIT = ROOT.parent / "roomkit"
INDEX = ROOT / "index.html"
LATEST_COUNT = 3

CARD_TEMPLATE = """                <div class="blog-card">
                    <h2><a href="/blog/{slug}/">{title}</a></h2>
                    <div class="blog-meta">
                        <span>{date}</span>
                        <span>&middot;</span>
                        <span>{mins}</span>
                    </div>
                    <a href="/blog/{slug}/" class="blog-read-more">Read more</a>
                </div>"""


def latest_version() -> str:
    try:
        tag = subprocess.run(
            ["git", "-C", str(ROOMKIT), "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if tag:
            return tag.lstrip("v")
    except (OSError, subprocess.CalledProcessError):
        pass
    m = re.search(
        r'__version__\s*=\s*"([^"]+)"',
        (ROOMKIT / "src/roomkit/_version.py").read_text(),
    )
    return m.group(1)


def enum_count(name: str) -> int:
    src = (ROOMKIT / "src/roomkit/models/enums.py").read_text()
    block = re.search(rf"class {name}.*?(?=\nclass |\Z)", src, re.S).group(0)
    return len(re.findall(r"^\s+[A-Z_]+\s*=", block, re.M))


def test_count() -> int:
    total = 0
    for path in (ROOMKIT / "tests").rglob("*.py"):
        total += len(re.findall(r"^\s*(?:async )?def test_", path.read_text(), re.M))
    return total


def set_fact(html: str, key: str, value: str) -> str:
    pattern = rf'(<[^>]*data-fact="{key}"[^>]*>)[^<]*(</)'
    new, n = re.subn(pattern, rf"\g<1>{value}\g<2>", html)
    if n == 0:
        print(f'warning: no data-fact="{key}" element in index.html', file=sys.stderr)
    return new


def latest_post_cards() -> str | None:
    blog = (ROOT / "blog/index.html").read_text()
    posts = re.findall(
        r'<h2><a href="/blog/([^"]+)/">([^<]+)</a></h2>\s*'
        r'<div class="blog-meta">\s*<span>([^<]+)</span>\s*'
        r"<span>&middot;</span>\s*<span>([^<]+)</span>",
        blog,
    )
    if len(posts) < LATEST_COUNT:
        print("warning: fewer than 3 posts found in blog/index.html", file=sys.stderr)
        return None
    return "\n".join(
        CARD_TEMPLATE.format(slug=slug, title=title, date=date, mins=mins)
        for slug, title, date, mins in posts[:LATEST_COUNT]
    )


def main() -> int:
    html = INDEX.read_text()

    if ROOMKIT.is_dir():
        html = set_fact(html, "version", latest_version())
        html = set_fact(html, "channel-types", str(enum_count("ChannelType")))
        html = set_fact(html, "hook-triggers", str(enum_count("HookTrigger")))
        html = set_fact(html, "tests", f"{test_count():,}")
    else:
        print(f"warning: {ROOMKIT} not found, facts left as-is", file=sys.stderr)

    cards = latest_post_cards()
    if cards is not None:
        html = re.sub(
            r"(<!-- latest-posts:start -->\n).*?(\n\s*<!-- latest-posts:end -->)",
            rf"\g<1>{cards}\g<2>",
            html,
            flags=re.S,
        )

    INDEX.write_text(html)
    print("index.html facts refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
