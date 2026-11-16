# Motion-graphic word card in the GRWTH theme: black, white + ice gradient, Archivo Black.
# usage: python mg.py out.mp4 duration 'WORD@t[:ice][:big]|WORD@t...'   (one line per item, items stack centred)
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS=1080,1920,30; F='/tmp/claude-0/-home-user-tafheem/8da1ac7c-cc1d-5ff9-b059-1539c9419264/scratchpad/grwth/fonts/ArchivoBlack-Regular.ttf'
out,dur,spec=sys.argv[1],float(sys.argv[2]),sys.argv[3]
items=[]
for it in spec.split('|'):
    p=it.split(':'); w,t=p[0].rsplit('@',1); items.append((w,float(t),'ice' in p,'big' in p))
def ice(txt,f):
    b=ImageDraw.Draw(Image.new('L',(1,1))).textbbox((0,0),txt,font=f); w,h=b[2],b[3]
    m=Image.new('L',(w,h)); ImageDraw.Draw(m).text((0,0),txt,font=f,fill=255)
    g=np.zeros((h,w,4),np.uint8); tt=np.linspace(0,1,h)[:,None]
    for i,(a,b2) in enumerate([(236,150),(247,205),(253,235)]): g[:,:,i]=(a+(b2-a)*tt).astype(np.uint8)
    g[:,:,3]=np.array(m); return Image.fromarray(g,'RGBA')
sprites=[]
for w,t,ic,big in items:
    f=ImageFont.truetype(F,170 if big else 110)
    im=ice(w,f) if ic else None
    if im is None:
        b=ImageDraw.Draw(Image.new('L',(1,1))).textbbox((0,0),w,font=f); im=Image.new('RGBA',(b[2],b[3])); ImageDraw.Draw(im).text((0,0),w,font=f,fill='white')
    sprites.append((im,t))
gap=40; tot=sum(s.height for s,_ in sprites)+gap*(len(sprites)-1); ys=[]; y=(H-tot)//2
for s,_ in sprites: ys.append(y); y+=s.height+gap
yy,xx=np.mgrid[0:H,0:W]; glow=np.exp(-(((xx-W/2)/700)**2+((yy-H/2)/900)**2))
bg=np.stack([glow*18,glow*30,glow*40],-1).astype(np.uint8); bgim=Image.fromarray(bg,'RGB').convert('RGBA')
pr=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','16','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
for n in range(int(dur*FPS)):
    T=n/FPS; fr=bgim.copy()
    for (s,t),y0 in zip(sprites,ys):
        k=(T-t)/0.2
        if k<=0: continue
        k=min(k,1); e=1-(1-k)**3; sc=1.35-0.35*e
        sp=s.resize((max(1,int(s.width*sc)),max(1,int(s.height*sc))),Image.LANCZOS)
        a=sp.getchannel('A').point(lambda v:int(v*e)); sp.putalpha(a)
        fr.alpha_composite(sp,((W-sp.width)//2,y0+(s.height-sp.height)//2))
    z=1+0.03*T/dur; zz=fr.resize((int(W*z),int(H*z)),Image.BILINEAR).crop(((int(W*z)-W)//2,(int(H*z)-H)//2,(int(W*z)-W)//2+W,(int(H*z)-H)//2+H))
    pr.stdin.write(zz.convert('RGB').tobytes())
pr.stdin.close(); pr.wait(); print(out)
