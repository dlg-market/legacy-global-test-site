# Legacy Global website: test build

A clickable preview of the proposed Legacy Global website redesign, built from
the design canvas. This is a test site for review, not the production site. It
is marked `noindex` and `robots.txt` blocks crawlers.

## Pages

| File | Page |
|---|---|
| `index.html` | Home |
| `services.html` | Services overview |
| `donor-advised-funds.html`, `fiscal-sponsorship.html`, `complex-giving.html`, `split-interest-giving.html`, `premium-financed-giving.html` | Service pages |
| `legacy-family.html` | The Legacy Family |
| `about.html` | About |
| `gateway.html` | The Legacy Gateway |
| `contact.html` | Contact |

## How it works

`canvas/` holds the page files exported from the design canvas (`*.dc.html`).
`tools/sync_from_canvas.py` turns each one into a plain `.html` page with its
templates embedded, and `assets/dc-lite.js` renders them in the browser. There
is no build server or framework; the pages also open straight from disk.

## Updating after design changes

1. Copy the changed `*.dc.html` files from the canvas into `canvas/`.
2. Rebuild:

   ```
   python -I tools/sync_from_canvas.py
   ```

   The 404 page assumes the site lives at `/legacy-global-test-site/`. If it
   moves (for example to a custom domain), set `SITE_BASE=/` before building.

3. Commit and push. GitHub Pages republishes within a minute or two.

## Known gaps (test build)

- Forms are not connected: Gateway request buttons, the cohort application,
  portal log-in and the contact form do not submit anywhere.
- Placeholders in square brackets (photos, team names, EINs, address, hours,
  year) still need real content.
- Service-page copy needs review and sign-off by Legacy before production.
