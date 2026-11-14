import sys, numpy as np, cv2
from PIL import Image, ImageDraw
base = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
src = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32)
H, W = base.shape[:2]
sq = np.float32([(236,659),(2364,736),(2000,955),(421,1236)])
tq = np.float32([(1120,1812),(1850,1822),(1700,1900),(1160,1955)])
M = cv2.getPerspectiveTransform(sq, tq)
m = Image.new('L', (src.shape[1], src.shape[0]), 0)
ImageDraw.Draw(m).polygon([(236,659),(2364,736),(2150,880),(1800,1010),(1300,1130),(800,1210),(421,1236)], fill=255)
m = np.asarray(m).astype(np.float32) / 255
wi = cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_AREA)
wm = cv2.warpPerspective(m, M, (W, H), flags=cv2.INTER_LINEAR)
wm = cv2.GaussianBlur(wm, (0, 0), 0.8)[..., None]
# daylight match: lift the dark glass a little, calm the LED purple
g = wi.mean(2, keepdims=True)
wi = g + (wi - g) * 0.8
wi = wi * 0.92 + 18
out = base * (1 - wm) + wi * wm
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(sys.argv[3])
