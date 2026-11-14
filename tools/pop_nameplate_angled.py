import sys, numpy as np, cv2
from PIL import Image, ImageDraw
base = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)   # photo at 4x (1920x1440)
H, W = base.shape[:2]; F = 4.0; S = 3; k = 5.0
srcim = Image.open(sys.argv[2]).convert('RGB')
srcim = srcim.resize((int(srcim.width / k), int(srcim.height / k)), Image.LANCZOS)
src = np.asarray(srcim).astype(np.float32)
# nameplate slot in the close-up (IMG_8444, full-size px): top edge, pointed front end, curved lower lip
s_top = [(236,659),(2364,736)]
s_curve = [(2364,736),(2150,880),(1800,1010),(1300,1130),(800,1210),(421,1236)]
# the same slot on the angled photo (1x px of the 480 copy)
t_slot = [(130.5,116.5),(160.5,102.6),(158.5,105.0),(155.0,110.0),(149.0,117.0),(140.0,124.0),(131.5,129.4)]
sq = np.float32([(236,659),(2364,736),(236,1236)]) / k
tq = np.float32([(130.5,116.5),(160.5,102.6),(131.5,129.4)]) * F * S
M = cv2.getAffineTransform(sq, tq)
sm = Image.new('L', srcim.size, 0)
ImageDraw.Draw(sm).polygon([(x/k, y/k) for x, y in [s_top[0]] + s_curve], fill=255)
sm = np.asarray(sm).astype(np.float32) / 255
wi = cv2.warpAffine(src, M, (W*S, H*S), flags=cv2.INTER_CUBIC)
wm = cv2.warpAffine(sm, M, (W*S, H*S), flags=cv2.INTER_LINEAR)
tm = Image.new('L', (W*S, H*S), 0); ImageDraw.Draw(tm).polygon([(x*F*S, y*F*S) for x, y in t_slot], fill=255)
tm = np.asarray(tm).astype(np.float32) / 255
mask = np.minimum(wm, tm)
# bring to 4x, keep premultiplied colour so edges don't fringe
wi = cv2.resize(wi * mask[..., None], (W, H), interpolation=cv2.INTER_AREA)
mask = cv2.resize(mask, (W, H), interpolation=cv2.INTER_AREA)
wi = wi / np.maximum(mask[..., None], 1e-4)
# sit it in the shade of the recess: a bit darker and cooler, inner shadow under the top edge
g = wi.mean(2, keepdims=True); wi = g + (wi - g) * 0.85
wi = wi * 0.80
tmask = Image.new('L', (W, H), 0); ImageDraw.Draw(tmask).polygon([(x*F, y*F) for x, y in t_slot], fill=255)
tmask = np.asarray(tmask).astype(np.float32) / 255
inner = tmask - cv2.erode(tmask, np.ones((7, 7), np.uint8))
shadow = cv2.GaussianBlur(inner, (0, 0), 2.5) * 0.45
# shadow only along the top edge (the lip overhangs it)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
top_line = 116.5*F + (xx - 130.5*F) * ((102.6 - 116.5) / (160.5 - 130.5))
shadow *= np.clip(1 - (yy - top_line) / (6*F), 0, 1)
wi = wi * (1 - shadow[..., None])
# match the photo's softness so it doesn't look pasted on
wi = cv2.GaussianBlur(wi, (0, 0), 1.0)
mask = cv2.GaussianBlur(mask, (0, 0), 0.8)[..., None]
out = base * (1 - mask) + wi * mask
# keep a thin lit edge on the curved lower lip
lip = np.zeros((H, W), np.uint8)
pts = np.int32([[(x*F, y*F) for x, y in t_slot[2:]]])
cv2.polylines(lip, pts, False, 255, 3, cv2.LINE_AA)
lip = cv2.GaussianBlur(lip.astype(np.float32) / 255, (0, 0), 1.0)[..., None] * 0.55
out = out * (1 - lip) + base * lip
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(sys.argv[3])
