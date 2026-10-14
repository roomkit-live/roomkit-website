# RoomKit Website

Landing pages for [roomkit.live](https://www.roomkit.live) and
[RoomKit UI](https://www.roomkit.live/roomkit-ui/).

## Structure

```
index.html                       Framework landing page
css/site.css                     Shared landing-page styles and fonts
js/site.js                       Navigation and clipboard controls
js/home.js                       Homepage conversation switcher
roomkit-ui/                      Desktop app page, gallery and real screenshots
examples/first_conversation.py   Downloadable, runnable framework example
blog/                            Articles, using css/style.css and js/main.js
404.html                         Custom 404 page
favicon.svg                      Site favicon
og-image.svg / og-image.png       Social preview image
robots.txt / sitemap.xml         Crawler directives and sitemap
```

The landing pages use the navy, indigo and cyan RoomKit palette, a lowercase
`roomkit.` wordmark with a white point, and self-hosted fonts. The original footer
resources are retained. Legacy styles and scripts remain available for the blog.

## Local preview

```bash
python3 -m http.server 8097 --bind 127.0.0.1
```

Open `http://127.0.0.1:8097/` or `http://127.0.0.1:8097/roomkit-ui/`.
Documentation and `llms*.txt` are assembled from sibling repositories during the
build; use the live site for those links when previewing only this checkout.

The homepage's conversation switcher is illustrative and makes no provider calls.
Its complete Python example uses a scripted AI provider, requires Python 3.12+
and `pip install roomkit`, and runs without an API key. The displayed code is
explicitly an excerpt of that download.

Both pages remain readable without JavaScript. The switchers support arrow keys,
Home and End; navigation supports Escape; install/run commands have copy controls.
The app gallery offers light/dark captures and links to full-size images.

## RoomKit UI release and screenshots

The app page describes published version **0.3.1**, verified October 14, 2026.
Download links point to that release's actual macOS, Windows and Linux assets.
Update the version and all download links together when promoting a new release;
check claims against the release tag rather than unreleased work on `main`.

Screenshots match v0.3.1 and use isolated demo data. To recapture from the app repo:

```bash
cd ../roomkit-ui
.venv/bin/python scripts/capture_screenshots.py
```

Copy the referenced PNGs from `assets/screenshots/` into `roomkit-ui/screenshots/`.
Keep `roomkit-ui/screenshot.png`: an older blog post references that historical image.

## Deployment

The site is containerized and deployed to the existing Kubernetes installation:

```bash
./deploy.sh
```

`make gather` pulls the sibling repositories, checks matching `llms*.txt` copies,
assembles the static assets and documentation, and regenerates the sitemap.
`make build` builds and pushes the image; `make deploy` applies the Kubernetes
manifests and waits for rollout. See `Makefile`, `Dockerfile.website` and `k8s.yml`.

The build includes `examples/` so the downloadable Python example works in
production. The homepage no longer uses the old generated counts/latest-post cards.

CSS and JS URLs on the two landing pages carry a SHA-256 content prefix in `?v=`
because nginx caches static assets as immutable. After changing one of these files,
update its version in both pages where referenced:

```bash
sha256sum css/site.css js/site.js js/home.js roomkit-ui/page.css roomkit-ui/page.js
```

Before deployment, check the assembled site's local links, metadata, screenshots,
keyboard interactions, clipboard contents and responsive layouts. Run the Python
example in an environment with RoomKit installed. The Docker build also builds the
framework documentation with `mkdocs build --strict`.

## Related repositories

- [roomkit](https://github.com/roomkit-live/roomkit) — Python library
- [roomkit-ui](https://github.com/roomkit-live/roomkit-ui) — Desktop assistant
- [roomkit-docs](https://github.com/roomkit-live/roomkit-docs) — Documentation
- [roomkit-specs](https://github.com/roomkit-live/roomkit-specs) — Protocol specs
