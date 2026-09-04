#!/usr/bin/env python3
"""Key the flat backdrop out of the Alert Box deck artwork.

The alert clips we were given are screen recordings composited onto a solid
card — three of them sit on flat white, one on flat black. Dropped into the
dark promo deck they read as a bright (or dead-black) panel rather than as
alerts floating on the card, so we lift the backdrop out and re-emit them
with a real alpha channel.

Two things make this more than a colour-key:

  * The alerts contain white text and near-black fills of their own, so a
    global "white is transparent" rule would punch holes straight through
    them. We only key the backdrop *reachable from the frame edge*: flood
    fill inward from a padded border and stop at the alert's own outline.

  * Every glow is anti-aliased into the backdrop, so the boundary pixels are
    a blend. Keying them to fully-opaque leaves a halo of backdrop colour
    around each glow. Instead we un-matte: recover the coverage from the
    pixel's distance from the backdrop and solve the compositing equation
    back for the original colour.

Output is animated WebP (8-bit alpha, ~5x smaller than the source GIFs).
GIF can't be the target here — its alpha is one bit, which is exactly the
"hard halo" case above.

Run from the repo root:  python _build/key-alert-art.py
"""

import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SRC = os.path.expanduser('~/Downloads')
OUT = 'assets/media/dashboard/promo'

# backdrop 'white' or 'black'; cut = how far from the backdrop a pixel may
# stray and still count as backdrop for the flood fill. Generous on purpose:
# the fill is bounded by connectivity, not by the threshold, so a loose cut
# just means more of the glow's outer falloff gets proper partial alpha.
JOBS = [
    ('engage-alerts_2_bcPAtrYq9Vcs4GkM-ezgif.com-video-to-gif-converter.gif',
     'engage-alerts.webp', 'white', 200),
    ('alerts-hero_dwgSVrem3yjlZ6bq-ezgif.com-video-to-gif-converter.gif',
     'alerts-hero.webp', 'black', 60),
    ('ezgif.com-gif-maker.gif',
     'stream-starting.webp', 'white', 200),
]


def lut(backdrop):
    """(channel, alpha) -> un-matted channel, as a flat 65536-entry table.

    over white:  c = fg*a + 255*(1-a)  ->  fg = (c - 255 + a*255) / a
    over black:  c = fg*a              ->  fg =  c / a
    """
    t = bytearray(65536)
    for a in range(256):
        base = a << 8
        if a == 0:
            continue  # fully transparent: colour is unused, leave it 0
        f = a / 255.0
        for c in range(256):
            v = (c / 255.0 - (1.0 - f)) / f if backdrop == 'white' else (c / 255.0) / f
            t[base | c] = 0 if v < 0 else (255 if v > 1 else int(v * 255 + 0.5))
    return bytes(t)


def unmatte(band, alpha, table):
    return Image.frombytes(
        'L', band.size,
        bytes(table[(a << 8) | c] for c, a in zip(band.tobytes(), alpha.tobytes())),
    )


def key(frame, backdrop, cut):
    rgb = frame.convert('RGB')
    r, g, b = rgb.split()
    w, h = rgb.size

    if backdrop == 'white':
        # min channel: 255 only for pure white, drops as any hue creeps in
        extreme = ImageChops.darker(ImageChops.darker(r, g), b)
        seed = extreme.point(lambda v: 255 if v >= cut else 0)
        coverage = ImageChops.invert(extreme)      # 0 on white, 255 on saturated
    else:
        extreme = ImageChops.lighter(ImageChops.lighter(r, g), b)
        seed = extreme.point(lambda v: 255 if v <= cut else 0)
        coverage = extreme                          # 0 on black, 255 on bright

    # Flood inward from a one-pixel collar so every edge pixel is one seed.
    pad = Image.new('L', (w + 2, h + 2), 255)
    pad.paste(seed, (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128, thresh=0)
    reached = pad.point(lambda v: 255 if v == 128 else 0).crop((1, 1, w + 1, h + 1))

    # Grow past the hard threshold to catch the anti-aliased rim, then feather
    # so alpha eases into the opaque interior instead of stepping.
    band = reached.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))

    # alpha = 255 - band*(255 - coverage)/255  ->  band=0 opaque, band=255 keyed
    alpha = ImageChops.invert(ImageChops.multiply(band, ImageChops.invert(coverage)))

    table = key.tables.setdefault(backdrop, None) or lut(backdrop)
    key.tables[backdrop] = table

    out = Image.merge('RGBA', (
        unmatte(r, alpha, table),
        unmatte(g, alpha, table),
        unmatte(b, alpha, table),
        alpha,
    ))
    return out


key.tables = {}


for name, dest, backdrop, cut in JOBS:
    src = Image.open(os.path.join(SRC, name))
    n = getattr(src, 'n_frames', 1)
    frames = []
    for i in range(n):
        src.seek(i)
        frames.append(key(src, backdrop, cut))
    dur = src.info.get('duration') or 100

    # Once the backdrop is gone the clip is mostly empty margin — alerts-hero
    # is 41% content. The deck fits these with `contain`, so that margin would
    # be paid for twice: in bytes, and in how small the art ends up drawn.
    # Crop to the union of every frame's content so the motion still fits.
    box = None
    for f in frames:
        b = f.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                         max(box[2], b[2]), max(box[3], b[3]))
    if box:
        frames = [f.crop(box) for f in frames]

    path = os.path.join(OUT, dest)
    frames[0].save(
        path, format='WEBP', save_all=True, append_images=frames[1:],
        # q72 is ~40% smaller than q88 and the deck paints these at 423px
        # wide — a 60% downscale that hides everything the extra bitrate buys
        duration=dur, loop=0, quality=72, method=6, minimize_size=True,
    )
    print('%-22s %d frame(s) %sx%s  %.0f KB -> %.0f KB'
          % (dest, n, frames[0].width, frames[0].height,
             os.path.getsize(os.path.join(SRC, name)) / 1024,
             os.path.getsize(path) / 1024))
