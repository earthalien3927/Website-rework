#!/usr/bin/env python3
"""Remove the dark plate behind the "by Scotty" signature and wax seal on a
painting image, and brighten the signature.

How it works:
  1. POLY outlines the plate (and its drop shadow), in pixels of the image.
  2. Inside it, the signature ink (light, colourless strokes) and the red wax
     seal are picked out.
  3. Everything inside the outline is repainted as a smooth blend of the paint
     just outside it (reddish pixels are left out of the blend).
  4. The seal goes back as it was; the ink goes back with a soft edge,
     brightened by BOOST.

Usage:
  python3 tools/fix_signature.py IN.png OUT.png --poly "x,y x,y ..." [--boost 1.15]
  Touch-up pass for a small area with no signature in it:
  python3 tools/fix_signature.py IN.png OUT.png --poly "..." --no-ink
Needs: pip install opencv-python-headless
"""
import argparse

import cv2
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--poly", required=True, help='plate outline: "x,y x,y ..."')
ap.add_argument("--boost", type=float, default=1.15)
ap.add_argument("--blend", type=float, default=14, help="smoothness of the repaint (px)")
ap.add_argument("--no-ink", action="store_true", help="just blend the area (touch-ups; no signature inside)")
ap.add_argument("--max-bg", type=float, default=255, help="ignore outside paint brighter than this (0-255)")
args = ap.parse_args()

im = Image.open(args.src)
mode = im.mode if im.mode in ("RGB", "RGBA") else "RGB"
rgba = np.asarray(im.convert("RGBA")).copy()
pts = np.array([[int(v) for v in p.split(",")] for p in args.poly.split()], np.int32)
pad = int(args.blend * 6)
x0, y0 = np.maximum(pts.min(0) - pad, 0)
x1, y1 = np.minimum(pts.max(0) + pad, [rgba.shape[1], rgba.shape[0]])
roi = rgba[y0:y1, x0:x1, :3].astype(np.float32)
r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
lum = 0.3 * r + 0.59 * g + 0.11 * b
sat = roi.max(-1) - roi.min(-1)
k = lambda n: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n, n))

plate = np.zeros(lum.shape, np.uint8)
cv2.fillPoly(plate, [pts - [x0, y0]], 1)
inside = plate > 0

# Seal: red wax inside the plate, as one solid shape (its darker folds included).
red = ((r > 90) & (r > g * 1.5) & (r > b * 1.4) & inside).astype(np.uint8)
red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, k(9))
seal = np.zeros_like(red)
cnts, _ = cv2.findContours(red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = [c for c in cnts if cv2.contourArea(c) > 200]
cv2.drawContours(seal, cnts, -1, 1, thickness=-1)
seal = seal > 0

# Ink: light, colourless strokes inside the plate.
stroke = (lum > 110) & (sat < 60) & inside & ~cv2.dilate(seal.astype(np.uint8), k(5)).astype(bool)
if args.no_ink:
    stroke[:] = False; seal[:] = False
ink = roi[stroke & (lum > np.percentile(lum[stroke], 60))].mean(0) if stroke.any() else np.array([255., 255., 255.])
ink_l = 0.3 * ink[0] + 0.59 * ink[1] + 0.11 * ink[2]
under = cv2.GaussianBlur(cv2.erode(lum, k(11)), (0, 0), 3)        # plate brightness beside each stroke
zone = (cv2.dilate(stroke.astype(np.uint8), k(3)) > 0) & inside
alpha = np.clip((lum - under) / np.maximum(ink_l - under, 1), 0, 1) * zone
alpha = np.clip((alpha - .08) / .92, 0, 1)
ink_col = np.clip(ink * args.boost, 0, 255)

# Repaint the plate from the paint around it.
reddish = (r > g * 1.35) & (r > 60)
shadowy = lum < 33                                    # leftover drop shadow / dark lines
bright = lum > args.max_bg                             # nearby highlights that don't run under the plate
wgt = (~inside & ~reddish & ~shadowy & ~bright).astype(np.float32)
# Coarse to fine, so the middle of a large plate (far from any outside paint)
# still gets the surrounding colour instead of going dark.
smooth = None
for sg in (args.blend * 8, args.blend * 4, args.blend * 2, args.blend):
    num = cv2.GaussianBlur(roi * wgt[..., None], (0, 0), sg)
    den = cv2.GaussianBlur(wgt, (0, 0), sg)[..., None]
    est = num / np.maximum(den, 1e-6)
    sure = np.clip(den / 0.25, 0, 1)
    smooth = est if smooth is None else est * sure + smooth * (1 - sure)
soft = cv2.GaussianBlur(plate.astype(np.float32), (0, 0), 2.5)[..., None]
clean = smooth * soft + roi * (1 - soft)

seal_a = cv2.GaussianBlur(seal.astype(np.float32), (0, 0), .8)[..., None]
out = clean * (1 - alpha[..., None]) + ink_col * alpha[..., None]
out = out * (1 - seal_a) + roi * seal_a
rgba[y0:y1, x0:x1, :3] = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(rgba, "RGBA").convert(mode).save(args.dst)
print(f"plate {int(inside.sum())} px, seal {int(seal.sum())} px, ink {ink.round().tolist()} -> {ink_col.round().tolist()}")
