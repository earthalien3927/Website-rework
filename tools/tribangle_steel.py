import sys, numpy as np, cv2
from PIL import Image
im = Image.open(sys.argv[1]); a = np.asarray(im).astype(np.float32); rgb, al = a[..., :3] / 255, a[..., 3]
g = (rgb @ np.float32([.3, .55, .15]))[..., None]
rgb = g * np.float32([.97, .99, 1.03])                     # neutral, very slightly cool steel
rgb = np.clip((rgb - .5) * 1.25 + .52, 0, 1)                # polished contrast
bl = cv2.GaussianBlur(rgb, (0, 0), 1.2); rgb = np.clip(rgb + .6 * (rgb - bl), 0, 1)
out = np.dstack([rgb * 255, al]).astype(np.uint8)
o = Image.fromarray(out, 'RGBA'); w = int(sys.argv[3]); o = o.resize((w, int(w * o.height / o.width)), Image.LANCZOS); o.save(sys.argv[2]); print(o.size)
