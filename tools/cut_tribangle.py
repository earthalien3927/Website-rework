import sys, json, numpy as np, cv2
from PIL import Image, ImageDraw
im = Image.open('popweb/IMG_8451.png').convert('RGB')
G = json.load(open('tri_geom.json'))
W, H = im.size
m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
for poly in G['polys']: d.polygon([tuple(p) for p in poly], fill=255)
for (x1,y1,x2,y2,w) in G['bars']: d.line([(x1,y1),(x2,y2)], fill=255, width=w)
tm = Image.new('L', (W, H), 0); td = ImageDraw.Draw(tm)
td.polygon([tuple(p) for p in G['tri_out']], fill=255); td.polygon([tuple(p) for p in G['tri_in']], fill=0)
from PIL import ImageChops
m = ImageChops.lighter(m, tm)
if sys.argv[1] == 'check':
    v = Image.composite(Image.new('RGB',(W,H),(0,255,0)), im, m.point(lambda a: a*0.45))
    v.crop((1550,520,2850,1820)).resize((780,780)).save('tri_chk.png')
else:
    from PIL import ImageFilter
    m = m.filter(ImageFilter.GaussianBlur(1.5))
    rgba = im.copy(); rgba.putalpha(m); rgba = rgba.crop(m.getbbox())
    rgba.save(sys.argv[1]); print(rgba.size)
