import sys, numpy as np, cv2
from PIL import Image, ImageOps
import pillow_heif; pillow_heif.register_heif_opener()
im = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert('RGB'); im.thumbnail((1100,1100), Image.LANCZOS)
a = np.asarray(im).astype(np.float32)/255
s = float(sys.argv[3])
lum = a @ np.float32([.3,.55,.15])
# 1) pull highlights down (windows, lit wall) with a soft shoulder
k = .55
lum2 = np.where(lum < k, lum, k + (1-k)*np.tanh((lum-k)/(1-k)*1.0)*0.72)
a = a * (lum2/np.maximum(lum,1e-4))[...,None]
# 2) warm pink tint by multiplying (adds colour, not light), strongest in mids/highs
warm = np.float32([1.0, .80, .80])   # warm rose
w = np.clip((lum2-.08)/.5, 0, 1)[...,None] * s
a = a * (1 - w*(1-warm))
# 3) slight overall warmth and a touch of contrast
a = a * np.float32([1.03, .99, .95])
a = np.clip((a-.5)*1.05+.5, 0, 1)
Image.fromarray((a*255).astype(np.uint8)).save(sys.argv[2], quality=84, optimize=True)
