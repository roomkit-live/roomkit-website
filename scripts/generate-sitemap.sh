#!/usr/bin/env bash
# Generate sitemap.xml with auto-discovered blog posts.
# Called by `make gather` before copying files to .build/.
set -euo pipefail

SITE="https://www.roomkit.live"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
OUT="$ROOT/sitemap.xml"

cat > "$OUT" <<'HEADER'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.roomkit.live/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/features/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/mcp/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/ai-integration/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/roomkit-rfc/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/roomkit/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/hooks/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/channels/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/events/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/identity/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/docs/api/realtime/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/roomkit-ui/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://www.roomkit.live/blog/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
HEADER

# Auto-discover blog posts (every dir under blog/ with an index.html, skip blog/index.html)
for post in "$ROOT"/blog/*/index.html; do
    slug="$(basename "$(dirname "$post")")"
    cat >> "$OUT" <<EOF
    <url>
        <loc>${SITE}/blog/${slug}/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
EOF
done

cat >> "$OUT" <<'FOOTER'
    <url>
        <loc>https://www.roomkit.live/llms.txt</loc>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
</urlset>
FOOTER

echo "sitemap.xml updated with $(grep -c '<loc>' "$OUT") URLs"
