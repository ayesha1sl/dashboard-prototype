#!/usr/bin/env python3
"""Re-box the Cloudbot nav icons onto their own artwork.

Figma exports each nav icon inside its layout wrapper, so the same 14px glyph
comes out boxed as 14x14, 23.5x21 or 26x21 depending on how much margin the
row happened to carry. Masked into one uniform square with `contain`, that
padding reads as three different icon weights down a single column.

Nothing is redrawn here — the path data is untouched. We only measure where
the artwork actually sits and move the viewBox onto it, exactly as was done
for the Alert Box toggle tick. Every path in this set is absolute M/L/C/H/V,
so the control points bound the glyph (a hair loose on curves, which is
harmless — it only pads by a fraction of a pixel).

Run from the repo root:  python _build/tighten-cb-icons.py
"""

import glob
import os
import re

DIR = 'assets/media/dashboard/cb'


def bbox(d):
    """Bounding box of an absolute-only path, from its points."""
    xs, ys = [], []
    x = y = 0.0
    for cmd, body in re.findall(r'([MLCHV])([^MLCHVZ]*)', d):
        n = [float(v) for v in re.findall(r'-?\d*\.?\d+(?:e-?\d+)?', body)]
        if cmd == 'H':
            xs += n
            ys.append(y)
            x = n[-1]
        elif cmd == 'V':
            ys += n
            xs.append(x)
            y = n[-1]
        else:  # M / L / C are all flat lists of x,y pairs
            xs += n[0::2]
            ys += n[1::2]
            x, y = n[-2], n[-1]
    return min(xs), min(ys), max(xs), max(ys)


for path in sorted(glob.glob(os.path.join(DIR, '*.svg'))):
    src = open(path, encoding='utf-8').read()
    boxes = [bbox(d) for d in re.findall(r'\sd="([^"]+)"', src)]
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)

    old = re.search(r'viewBox="([^"]+)"', src).group(1)
    new = '%s %s %s %s' % tuple(round(v, 3) for v in (x0, y0, x1 - x0, y1 - y0))
    if new == old:
        continue

    # width/height must follow, or a browser sizing the <img> by attribute
    # would letterbox it back into the old padded box
    out = re.sub(r'viewBox="[^"]+"', 'viewBox="%s"' % new, src, count=1)
    out = re.sub(r'\swidth="[^"]+"', ' width="%s"' % round(x1 - x0, 3), out, count=1)
    out = re.sub(r'\sheight="[^"]+"', ' height="%s"' % round(y1 - y0, 3), out, count=1)
    open(path, 'w', encoding='utf-8').write(out)
    print('%-20s %-22s -> %s' % (os.path.basename(path), old, new))
