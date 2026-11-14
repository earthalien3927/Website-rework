import sys, numpy as np, cv2
from PIL import Image, ImageOps
import pillow_heif; pillow_heif.register_heif_opener()
im = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert('RGB'); im.thumbnail((1100,1100), Image.LANCZOS)
a = np.asarray(im).astype(np.float32)/255
pink = np.float32([1.0, .35, .75])
lum = a @ np.float32([.3,.55,.15])
# glow: blurred highlights, tinted pink, screened on
hi = np.clip((lum-.35)/.5, 0, 1)
g = cv2.GaussianBlur(hi, (0,0), 45)[...,None] * pink
s = float(sys.argv[3])
out = 1 - (1-a)*(1 - g*s)
# gentle overall pink wash in the shadows/mids
out = out*(1-.10*s) + (out*pink)*(.10*s) + pink*.06*s*(1-lum[...,None])
Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save(sys.argv[2], quality=82, optimize=True)
