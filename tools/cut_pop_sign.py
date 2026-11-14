import sys, numpy as np, cv2
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
def stadium(cl, rl, cr, rr, n=120):
    (xl, yl), (xr, yr) = cl, cr
    pts = []
    for t in np.linspace(np.pi/2, 3*np.pi/2, n):       # left half, top -> bottom
        pts.append((xl + rl*np.cos(t), yl - rl*np.sin(t)))
    for t in np.linspace(-np.pi/2, np.pi/2, n):        # right half, bottom -> top
        pts.append((xr + rr*np.cos(t), yr - rr*np.sin(t)))
    return pts
cl, rl, cr, rr = (738, 1349), 410, (3362, 1390), 406
pts = stadium(cl, rl, cr, rr)
S = 4
m = Image.new('L', (W*S//4, H*S//4), 0)
m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
m = m.filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(1.2))
if sys.argv[2] == 'check':
    v = im.copy(); d = ImageDraw.Draw(v); d.line(pts + [pts[0]], fill=(0,255,0), width=4)
    v.crop((200,820,1150,1900)).resize((475,540)).save('o_chk_l.png'); v.crop((2950,820,3900,1900)).resize((475,540)).save('o_chk_r.png')
    v.resize((1008,756)).save('o_chk.png')
else:
    rgba = im.copy(); rgba.putalpha(m)
    bb = m.getbbox(); rgba = rgba.crop(bb)
    rgba = rgba.resize((1600, int(1600*rgba.height/rgba.width)), Image.LANCZOS)
    rgba.save(sys.argv[2]); print(rgba.size)
