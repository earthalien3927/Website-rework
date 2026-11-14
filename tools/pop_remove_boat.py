import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(np.float32)
H, W = a.shape[:2]
# mask: the white boat behind Pop (canopy + hull band), above Pop's hull, left of the bow grab rail
m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
d.polygon([(258,92),(330,92),(378,100),(378,117),(366,119),(366,145),(340,146),(258,148),(258,120)], fill=255)
mask = np.asarray(m) > 0
fill = a.copy()
for y in range(H):
    for x in range(W):
        if mask[y, x]:
            sy = 69 + ((y - 69) % 28)   # repeat 6 floors of the tower / sky above
            fill[y, x] = a[sy, x]
# tower gets a touch darker toward its base (shade)
yy = np.arange(H)[:, None].repeat(W, 1)
shade = np.clip((yy - 96) / 60.0, 0, 1) * 0.12
fill = fill * (1 - shade[..., None] * mask[..., None])
soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
res = a * (1 - soft) + fill * soft
img = Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))
# redraw Pop's stainless bow rail in front (supersampled)
S = 4; big = img.resize((W*S, H*S), Image.LANCZOS); bd = ImageDraw.Draw(big)
rail = (205, 209, 216)
def L(p, q, w): bd.line([(p[0]*S, p[1]*S), (q[0]*S, q[1]*S)], fill=rail, width=int(w*S))
L((258,141.5),(367,137.5),1.3)
L((258,131),(367,127),1.0)
for x in (272, 300, 328, 356):
    yt = 131 - (x-258)*4/109; L((x, yt), (x, 147 - (x-258)*2/109), 1.0)
img = big.resize((W, H), Image.LANCZOS)
img.save(out)
