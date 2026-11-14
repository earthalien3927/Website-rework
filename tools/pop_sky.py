import sys, numpy as np, cv2
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32) / 255
H, W = a.shape[:2]
hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV); h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
blue = ((h > 185) & (h < 250)).astype(np.float32) * np.clip((s - .08) / .2, 0, 1)
cloud = np.clip((v - .72) / .2, 0, 1) * np.clip((.22 - s) / .12, 0, 1)
pinkish = ((h > 270) | (h < 25)).astype(np.float32) * np.clip((s - .12) / .15, 0, 1)
yy = np.linspace(0, 1, H)[:, None]
upper = np.clip((0.62 - yy) / 0.25, 0, 1)          # sky and towers, fading out before the hull
m = np.clip(np.maximum(blue, cloud) * (1 - pinkish), 0, 1) * upper
m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)
amt = float(sys.argv[3]) if len(sys.argv) > 3 else 0.16
out = a.copy()
out = out * (1 - m[..., None] * amt)                # a little darker
hsv2 = cv2.cvtColor(out.astype(np.float32), cv2.COLOR_RGB2HSV)
hsv2[..., 1] = np.clip(hsv2[..., 1] * (1 + m * 0.10), 0, 1)   # and a touch deeper blue
out = cv2.cvtColor(hsv2.astype(np.float32), cv2.COLOR_HSV2RGB)
Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8)).save(sys.argv[2])
