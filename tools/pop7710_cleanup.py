import sys, numpy as np, cv2
from PIL import Image, ImageDraw
a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
H, W = a.shape[:2]
def poly(pts):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255); return np.asarray(m) > 0
rng = np.random.default_rng(1)
def row_interp(img, mask, pad=3, vb=9):
    out = img.copy()
    ys, xs = np.nonzero(mask)
    for y in np.unique(ys):
        row = mask[y]; x = 0
        while x < W:
            if row[x]:
                x0 = x
                while x < W and row[x]: x += 1
                l = max(x0 - pad, 0); r = min(x + pad, W - 1)
                L = img[y, max(l-4,0):l+1].mean(0); R = img[y, r:r+5].mean(0)
                t = np.linspace(0, 1, x - x0 + 2)[1:-1, None]
                out[y, x0:x] = L * (1 - t) + R * t
            else: x += 1
    # blend vertically inside the mask to hide row streaks, add a little grain
    bl = cv2.GaussianBlur(out, (1, vb), 0) if vb > 1 else out
    out[mask] = bl[mask] + rng.normal(0, 2.2, (mask.sum(), 3))
    return out
def blend(base, fill, mask, feather=1.6):
    s = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), feather)[..., None]
    return base * (1 - s) + fill * s

# 1) posts on the dock and the little stool
posts = [
    poly([(1660,1972),(1714,1972),(1738,2030),(1744,2628),(1626,2628),(1630,2030)]),   # centre post
    poly([(2650,2068),(2690,2068),(2712,2120),(2714,2648),(2630,2648),(2632,2120)]),   # right post
    poly([(340,1855),(392,1855),(424,1990),(426,2628),(308,2628),(310,1990)]),         # left post
    poly([(1342,2522),(1608,2522),(1608,2597),(1342,2597)]),                           # stool
]
for i, m in enumerate(posts):
    a = blend(a, row_interp(a, m, vb=1 if i == 0 else 9), m, 1.0 if i == 0 else 1.2)

# 2) top part of the boat beside Pop: tower runs straight down, open sky between
top = poly([(1952,1600),(3024,1600),(3024,2065),(2880,2045),(2750,2015),(2650,2003),(2350,2008),
            (2290,1993),(1992,2035),(1988,1990),(1941,1800),(1946,1720)])
fill = a.copy(); P = 77; src0 = 1300
ys, xs = np.nonzero(top)
tower = xs >= 2212
sy = src0 + ((ys - src0) % (3*P))           # repeat 3 floors from the clean tower above
fill[ys[tower], xs[tower]] = a[sy[tower], xs[tower]]
sky = ~tower
msy = np.clip(3200 - ys[sky], 0, H-1)          # mirror the sky above
fill[ys[sky], xs[sky]] = a[msy, xs[sky]]
# a touch of haze lower down in the sky gap, slight shade toward the tower base
yy = np.arange(H)[:, None].repeat(W, 1).astype(np.float32)
haze = np.clip((yy - 1750) / 300, 0, 1)[..., None] * 0.18
xx = np.arange(W)[None, :].repeat(H, 0)
skym = (top & (xx < 2212))[..., None]
fill = np.where(skym, fill * (1 - haze) + np.array([228, 234, 242], np.float32) * haze, fill)
shade = (top & (xx >= 2212))[..., None] * np.clip((yy - 1700) / 360, 0, 1)[..., None] * 0.10
fill = fill * (1 - shade)
a = blend(a, fill, top, 1.4)
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(sys.argv[2])
