import sys, numpy as np, cv2
from PIL import Image, ImageDraw
base = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
H, W = base.shape[:2]; S = 2; F = 4.0
k = 2.5  # pre-shrink the big nameplate photo
srcim = Image.open(sys.argv[2]).convert('RGB'); srcim = srcim.resize((int(srcim.width/k), int(srcim.height/k)), Image.LANCZOS)
src = np.asarray(srcim).astype(np.float32)
sq = np.float32([(236,659),(2364,736),(2364,1236),(236,1236)]) / k
tri = [(x*F, y*F) for x, y in [(129,108.5),(170,101.5),(165,107),(157,114),(148,121),(139,127),(130,130.5)]]
tq = np.float32([(129,108.5),(170,101.5),(170,117),(130,130.5)]) * F * S
M = cv2.getPerspectiveTransform(sq, tq)
m = Image.new('L', srcim.size, 0)
ImageDraw.Draw(m).polygon([(x/k, y/k) for x, y in [(236,659),(2364,736),(2150,880),(1800,1010),(1300,1130),(800,1210),(421,1236)]], fill=255)
m = np.asarray(m).astype(np.float32) / 255
wi = cv2.warpPerspective(src, M, (W*S, H*S), flags=cv2.INTER_CUBIC)
wm = cv2.warpPerspective(m, M, (W*S, H*S), flags=cv2.INTER_LINEAR)
rec = Image.new('L', (W*S, H*S), 0); ImageDraw.Draw(rec).polygon([(x*S, y*S) for x, y in tri], fill=255)
wm = wm * (np.asarray(rec).astype(np.float32) / 255)
wi = cv2.resize(wi * wm[..., None], (W, H), interpolation=cv2.INTER_AREA)
wm = cv2.resize(wm, (W, H), interpolation=cv2.INTER_AREA)[..., None]
wi = wi / np.maximum(wm, 1e-4)
wi = cv2.GaussianBlur(wi, (0, 0), 1.1); wm = cv2.GaussianBlur(wm, (0, 0), 0.9)[..., None] if wm.ndim == 2 else cv2.GaussianBlur(wm[..., 0], (0, 0), 0.9)[..., None]
g = wi.mean(2, keepdims=True); wi = g + (wi - g) * 0.85; wi = wi * 0.95 + 10
out = base * (1 - wm) + wi * wm
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(sys.argv[3])
