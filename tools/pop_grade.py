import sys, numpy as np, cv2
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)/255
H,W=a.shape[:2]
# S-curve contrast
a = a + 0.22*(a-0.5)*(1-np.abs(2*a-1))*2
a = np.clip(a,0,1)
hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
h,s,v = hsv[...,0],hsv[...,1],hsv[...,2]
pink = ((h>280)|(h<20)).astype(np.float32)
blue = ((h>190)&(h<240)).astype(np.float32)
s = np.clip(s*(1.18+0.22*pink+0.15*blue),0,1)
yy = np.linspace(0,1,H)[:,None]
v = v*(1-0.18*blue*np.clip(1-yy*2.2,0,1))   # deepen the upper sky
hsv = np.dstack([h,s,v]); a = cv2.cvtColor(hsv.astype(np.float32), cv2.COLOR_HSV2RGB)
# vignette
Y,X=np.mgrid[0:H,0:W]; r=np.sqrt(((X-W*0.52)/(W*0.62))**2+((Y-H*0.5)/(H*0.62))**2)
a = a*(1-0.28*np.clip(r-0.55,0,1)[...,None]*1.6)
# light sharpen
b = cv2.GaussianBlur(a,(0,0),1.2); a = np.clip(a+0.5*(a-b),0,1)
Image.fromarray((a*255).astype(np.uint8)).save(sys.argv[2])
