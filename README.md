# RoomKit Website

Landing page for [roomkit.live](https://www.roomkit.live).

## Structure

```
index.html        Main landing page
404.html          Custom 404 page
css/style.css     Styles
js/main.js        Client-side JS
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

## Related Repos

- [roomkit](https://github.com/roomkit-live/roomkit) — Python library
- [roomkit-docs](https://github.com/roomkit-live/roomkit-docs) — Documentation
- [roomkit-specs](https://github.com/roomkit-live/roomkit-specs) — Protocol specs
