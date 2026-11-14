import sys, numpy as np, cv2
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); im.thumbnail((1600,1600), Image.LANCZOS)
a = np.asarray(im).astype(np.float32)/255; H, W = a.shape[:2]
lum = a @ np.float32([.3,.55,.15])
yy, xx = np.mgrid[0:H,0:W].astype(np.float32); yn, xn = yy/H, xx/W
# window glass: bright area in the top band
top = np.clip((0.272 - yn)/0.012, 0, 1)
win = cv2.GaussianBlur((np.clip((lum-.22)/.12,0,1)*top).astype(np.float32), (0,0), 1.5)
win = np.clip(win*1.3, 0, 1)[...,None]
# night outside: dark, blue-violet, keep faint detail; bright spots become marina lights
dusk = np.float32([.16,.17,.38])*(.35+.65*(1-yn[...,None]/.31)) 
night = a*np.float32([.07,.08,.15]) + dusk*.45
# only small, isolated bright points become lights (top-hat), and only a few of them
L = lum.astype(np.float32)
th = L - cv2.morphologyEx(L, cv2.MORPH_OPEN, np.ones((11,11),np.uint8))
k = cv2.dilate(th, np.ones((25,25),np.uint8))
spots = ((th>=k)&(th>.18)).astype(np.float32)*top
rng = np.random.default_rng(5); spots *= (rng.random(spots.shape)<.25)*(.45+.55*rng.random(spots.shape))
spots = cv2.dilate(spots, np.ones((3,3),np.uint8))
print('lights', int((spots>0).sum()/9))
lights = cv2.GaussianBlur(spots.astype(np.float32),(0,0),2.5)[...,None]*np.float32([1.0,.8,.5])*1.3
lights += cv2.GaussianBlur(spots.astype(np.float32),(0,0),12)[...,None]*np.float32([1.0,.45,.8])*3.0
night = night + lights
# interior: darker and moodier
inside = a*0.42
inside = inside*np.float32([1.0,.92,1.05])
out = inside*(1-win) + night*win
# light sources: red dash glow, pink under-glow, warm pool on carpet near the wheel
def glow(cx, cy, rx, ry, col, k):
    g = np.exp(-(((xn-cx)/rx)**2 + ((yn-cy)/ry)**2))[...,None]
    return g*np.float32(col)*k
red = np.clip((a[...,0]-a[...,1]*1.3-.15)/.3,0,1)*(yn>.27)*(yn<.4)*(xn>.48)*(xn<.86)
redbloom = cv2.GaussianBlur(red.astype(np.float32),(0,0),25)[...,None]*np.float32([1,.12,.18])*1.4
add = redbloom + glow(.66,.62,.22,.22,[1,.55,.3],.32) + glow(.25,.72,.32,.07,[1,.2,.7],.45) + glow(.66,.36,.18,.06,[1,.2,.25],.25)
# carpet and leather pick up the light
out = out + add*(.55+.45*a)
# keep the chrome wheel and controls catching light
spec = np.clip((lum-.72)/.2,0,1)*(yn>.31)
out = out + cv2.GaussianBlur(spec.astype(np.float32),(0,0),1.2)[...,None]*a*0.55
# vignette + slight contrast
r = np.sqrt(((xn-.55)/.75)**2+((yn-.55)/.7)**2)
out = out*(1-.45*np.clip(r-.45,0,1)[...,None]*1.6)
out = np.clip((out-.4)*1.1+.4,0,1)
Image.fromarray((out*255).astype(np.uint8)).save(sys.argv[2], quality=86)
