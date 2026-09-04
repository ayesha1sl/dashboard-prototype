# Streamlabs Dashboard — redesign prototype

An interactive front-end prototype of a redesigned `streamlabs.com/dashboard`,
built from the Figma file **Onboarding and Dashboard**
(`JFbnYaQeA4lGKTwlt4xcpY`). Plain HTML/CSS/JS — no build step, no dependencies.

## Run it

```
python -m http.server 8099
```

then open <http://localhost:8099>.

Serve it rather than double-clicking `index.html`: Chrome treats every `file://`
document as an opaque origin, which blocks the CSS `mask-image` fetches the icons
rely on and the `@font-face` loads. See [Offline / `file://`](#offline-file) if you
need the page to work straight off disk.

## Layout

```
index.html                  the whole page — markup + inline prototype JS
assets/
  dashboard.css             every style for the page
  roboto.css                bundled Roboto (300/400/500/700 only)
  icons.css                 icomoon glyph font, generated from the desktop app
  fonts/                    icomoon.woff + the Roboto woff2 subsets
  media/dashboard/          art, grouped by area — see below
_build/inline-icons.js      optional: inline every icon as a data: URI
vercel.json                 cache headers for a static deploy
```

`assets/media/dashboard/` subfolders: `gs/` getting-started card, `live/` top bar,
`nav/` left rail, `perf/` channel performance, `plat/` platform connect table,
`q2/` quick-links strip, `disc/` Discord card, `social/` footer socials.

## What's interactive

- **Getting Started** runs a three-phase state machine: checklist → confetti →
  health check → *Stream Setup*. Skip/undo per step; "Download Streamlabs Desktop"
  fakes an instant download and drops a chip in the corner.
- **Growth mode** (the switch on the final Stream Setup card) flips
  `grid[data-growth]`, which reflows the grid and hides the follow-alert promo.
- The **Ultra banner** dismisses, and the support cards scroll via `[data-scroll]`.

All of it is in the single `<script>` at the bottom of `index.html`.

## Icon technique

Icons are CSS masks, not `<img>`, so they inherit colour on hover:

```html
<span class="stat__ico" style="--ico: url(media/dashboard/perf/s-views.svg)"></span>
```

```css
.stat__ico { background: var(--muted); -webkit-mask: var(--ico) no-repeat center / contain; }
```

Two gotchas when adding icons exported from Figma:

- **Mask URLs are relative to `assets/`, not to the page** — write
  `url(media/dashboard/…)` even inside `index.html`. Chrome resolves a `url()`
  that a `var()` substitutes against the stylesheet doing the substituting
  (`assets/dashboard.css`), not against the document. `<img src="…">` is the
  opposite: those stay page-relative, `assets/media/dashboard/…`.
- Figma stores many vectors upside-down and rights them with a `-scale-y-100`
  wrapper on export. Those need `transform: scaleY(-1)` on the mask span — the
  already-upright ones carry an `--upright` modifier instead.

## Offline / `file://`

```
node _build/inline-icons.js
```

rewrites every `--ico: url(…)` into a var, inlines small `<img>` SVGs, and emits
`assets/dashboard-icons.css` with the masks and the icomoon face as data: URIs.
Link that stylesheet from `<head>` afterwards and the page renders identically
from disk. It rewrites `index.html` in place, so commit first.

## Origin

Extracted from `design-system-site/` in the `slobs-client` (Streamlabs Desktop)
repo, where it was developed alongside that app's design-system pages. Nothing
here depends on that repo any more.
# dashboard-prototype
