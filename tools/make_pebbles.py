#!/usr/bin/env python3
"""Render a seamless tile of polished black onyx pebbles with a wet sheen.

Each stone is a squashed, rotated ellipsoid. The height map is lit with a soft
key light from the upper left (diffuse + a tight specular for the polish), the
gaps fall into shadow, and a faint mineral grain keeps it from looking plastic.
Positions wrap around the edges so the tile repeats without seams.

Usage: python3 tools/make_pebbles.py  ->  assets/onyx-pebbles.webp
"""
import pathlib

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "onyx-pebbles.webp"
SIZE = 720            # tile size in px
STONE = (26, 50)      # stone radius range in px (about 1-inch stones on screen)
SEED = 7

rng = np.random.default_rng(SEED)
H = np.zeros((SIZE, SIZE), np.float32)       # height map
ID = np.full((SIZE, SIZE), -1, np.int32)     # which stone owns each pixel
tone = []                                     # per-stone base tone

# Scatter stones with rejection sampling so they pack without heavy overlap.
centres = []
tries = 0
while tries < 60000:
    tries += 1
    r = rng.uniform(*STONE)
    x, y = rng.uniform(0, SIZE, 2)
    ok = True
    for (cx, cy, cr) in centres:
        dx = min(abs(x - cx), SIZE - abs(x - cx))
        dy = min(abs(y - cy), SIZE - abs(y - cy))
        if dx * dx + dy * dy < (0.74 * (r + cr)) ** 2:
            ok = False
            break
    if ok:
        centres.append((x, y, r))

yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
for i, (cx, cy, r) in enumerate(centres):
    a = r * rng.uniform(1.0, 1.35)            # long axis
    b = r * rng.uniform(0.72, 0.95)           # short axis
    th = rng.uniform(0, np.pi)
    dome = rng.uniform(0.3, 0.5)              # low = flatter, river-worn top
    lobes = [(k, rng.uniform(0, 0.09 / k ** 0.5), rng.uniform(0, 2 * np.pi)) for k in (2, 3, 5)]
    tone.append(rng.uniform(0.55, 1.25))
    for ox in (-SIZE, 0, SIZE):               # wrap for a seamless tile
        for oy in (-SIZE, 0, SIZE):
            x0, y0 = cx + ox, cy + oy
            if x0 + a < 0 or x0 - a > SIZE or y0 + a < 0 or y0 - a > SIZE:
                continue
            dx, dy = xx - x0, yy - y0
            u = (dx * np.cos(th) + dy * np.sin(th)) / a
            v = (-dx * np.sin(th) + dy * np.cos(th)) / b
            d = u * u + v * v
            ang = np.arctan2(v, u)
            d = d * (1 + sum(amp * np.sin(k * ang + ph) for k, amp, ph in lobes))  # irregular outline
            h = np.where(d < 1, np.sqrt(np.clip(1 - d, 0, 1)) ** dome * b * 0.9, 0)
            m = h > H
            H[m] = h[m]
            ID[m] = i
tone = np.array(tone, np.float32)

# Normals from the height map.
gy, gx = np.gradient(H)
n = np.dstack([-gx, -gy, np.ones_like(H)])
n /= np.linalg.norm(n, axis=2, keepdims=True)

light = np.array([-0.55, -0.65, 0.52]); light /= np.linalg.norm(light)
view = np.array([0, 0, 1.0])
half = light + view; half /= np.linalg.norm(half)
diff = np.clip(n @ light, 0, 1)
gloss = np.where(ID >= 0, np.random.default_rng(SEED + 1).uniform(0.5, 1.1, len(centres))[np.clip(ID, 0, None)], 0)
spec = np.clip(n @ half, 0, 1) ** 90 * 1.1 * gloss  # tight highlight: polished
sheen = np.clip(n @ half, 0, 1) ** 9 * 0.18          # broad wet sheen

# Ambient occlusion: blur the height map, darker in the crevices.
hb = np.asarray(Image.fromarray((H / H.max() * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), np.float32) / 255
ao = np.clip(0.35 + 1.4 * (H / H.max() - hb + 0.25), 0.15, 1.0)
ao[ID < 0] = 0.08

base = np.where(ID >= 0, tone[np.clip(ID, 0, None)], 0.0)
grain = rng.normal(0, 1, (SIZE, SIZE)).astype(np.float32)
grain = np.asarray(Image.fromarray(((grain * 18) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 - 0.5

lum = (0.035 + 0.07 * diff * base + grain * 0.02) * ao + (spec + sheen) * (ID >= 0) * (0.6 + 0.4 * ao)
lum = np.clip(lum, 0, 1)

# Onyx is black with the faintest cool-warm shift; the highlight stays neutral.
rgb = np.dstack([lum * 1.0, lum * 0.97, lum * 0.98])
img = Image.fromarray((rgb * 255).astype(np.uint8), "RGB")
OUT.parent.mkdir(exist_ok=True)
img.save(OUT, "WEBP", quality=84, method=6)
print(f"{OUT.relative_to(ROOT)}: {len(centres)} stones, {OUT.stat().st_size // 1024} KB")
