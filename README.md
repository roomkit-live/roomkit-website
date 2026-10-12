# RoomKit Website

Landing page for [roomkit.live](https://www.roomkit.live).

## Structure

```
index.html        Main landing page
404.html          Custom 404 page
css/style.css     Styles
js/main.js        Client-side JS
roomkit-ui/       Native app showcase, interactive gallery and real screenshots
favicon.svg       Site favicon
og-image.svg      Open Graph preview image
robots.txt        Crawler directives
sitemap.xml       Sitemap
```

## Deployment

The site is containerized and deployed to Kubernetes:

```bash
# Build and deploy
./deploy.sh
```

See `Dockerfile.website` and `k8s.yml` for infrastructure details.

## RoomKit UI showcase

Preview the static site locally:

```bash
python3 -m http.server 8097 --bind 127.0.0.1
```

Open `http://127.0.0.1:8097/roomkit-ui/`. Page-specific styles and interactions live
in `roomkit-ui/page.css` and `page.js`; the framework landing page is independent.
The gallery supports keyboard navigation, light/dark captures and full-size images.
With JavaScript disabled, all three views remain readable.

Screenshots come from real widgets with isolated demo data in the app repository:

```bash
cd ../roomkit-ui
.venv/bin/python scripts/capture_screenshots.py
```

Copy the referenced PNGs from `assets/screenshots/` into this repo's
`roomkit-ui/screenshots/`. Keep the original `roomkit-ui/screenshot.png`: an older
blog post references that historical image.

Until the app release is published, the page explicitly labels the interface as a
development preview and separates source installation from stable downloads. When
the release ships, update that wording alongside the app's version and changelog.
Validate tabs, theme switching, mobile navigation, copy feedback, image links and
responsive layouts before deploying. The deployment script also rebuilds the framework
documentation from sibling repositories; it is not just a static page upload.

## Related Repos

- [roomkit](https://github.com/roomkit-live/roomkit) — Python library
- [roomkit-docs](https://github.com/roomkit-live/roomkit-docs) — Documentation
- [roomkit-specs](https://github.com/roomkit-live/roomkit-specs) — Protocol specs
