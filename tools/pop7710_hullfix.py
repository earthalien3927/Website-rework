import sys, numpy as np, cv2
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
x0, x1, y0, y1 = 1626, 1744, 2298, 2356     # hull streak left by the post: fill top-to-bottom from clean hull
top = a[y0-4:y0, x0:x1].mean(0); bot = a[y1:y1+4, x0:x1].mean(0)
t = np.linspace(0, 1, y1 - y0)[:, None, None]
patch = top[None] * (1 - t) + bot[None] * t + np.random.default_rng(2).normal(0, 1.8, (y1-y0, x1-x0, 3))
m = np.zeros(a.shape[:2], np.float32); m[y0:y1, x0:x1] = 1
s = cv2.GaussianBlur(m, (0, 0), 1.5)[..., None]
full = a.copy(); full[y0:y1, x0:x1] = patch
a = a * (1 - s) + full * s
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(sys.argv[2])
