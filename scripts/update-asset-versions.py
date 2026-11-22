#!/usr/bin/env python3
"""Keep the ?v= cache-busting values in step with the files they point to.

nginx serves CSS and JS as immutable for a year, so every reference carries the first
12 hex digits of the file's SHA-256. Run this after changing one of those files:

    python3 scripts/update-asset-versions.py          # rewrite the references
    python3 scripts/update-asset-versions.py --check  # exit 1 if any is stale
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = [
    "css/shell.css", "css/site.css", "css/blog.css", "css/docs.css",
    "js/site.js", "js/home.js",
    "assistant/page.css", "assistant/page.js", "code/page.css",
]
PAGES = [*ROOT.glob("*.html"), *ROOT.glob("*/index.html"), *ROOT.glob("blog/*/index.html"),
         ROOT / "docs-theme" / "mkdocs.yml"]


def main() -> int:
    check = "--check" in sys.argv[1:]
    versions = {a: hashlib.sha256((ROOT / a).read_bytes()).hexdigest()[:12] for a in ASSETS}
    stale = []
    for page in PAGES:
        text = page.read_text()
        new = text
        for asset, version in versions.items():
            new = re.sub(rf"(/{re.escape(asset)})\?v=[0-9a-f]+", rf"\1?v={version}", new)
        if new != text:
            stale.append(page.relative_to(ROOT))
            if not check:
                page.write_text(new)
    for page in stale:
        print(("stale: " if check else "updated: ") + str(page))
    if check and stale:
        print("Run: python3 scripts/update-asset-versions.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
