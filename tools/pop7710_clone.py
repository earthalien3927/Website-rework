import sys, numpy as np, cv2
from PIL import Image, ImageDraw
orig = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
a = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32)
H, W = a.shape[:2]
def poly(pts):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255); return np.asarray(m) > 0
def clone(base, src, mask, dx, dy=0, feather=2.0):
    sh = np.roll(np.roll(src, dy, 0), dx, 1)   # pixel at x takes src[x-dx]
    s = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), feather)[..., None]
    return base * (1 - s) + sh * s
# left post: copy the scenery from just left of it
m = poly([(336,1845),(396,1845),(430,1985),(432,2632),(302,2632),(304,1985)])
a = clone(a, orig, m, 125)
# antenna in front of the Marriott: copy the tower one window bay to the left
m = poly([(2575,1290),(2668,1290),(2668,2000),(2575,2000)])
a = clone(a, a.copy(), m, 122)
# right post: copy the boat hull from just right of it
m = poly([(2645,2062),(2695,2062),(2718,2115),(2720,2652),(2624,2652),(2626,2115)])
a = clone(a, orig, m, -100)
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(sys.argv[3])
