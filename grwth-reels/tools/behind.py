# Put hook text behind the person: python behind.py final.mp4 band.mp4 until out.mp4 [shade]
import sys,subprocess,numpy as np,mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
F,Bp,until,out=sys.argv[1],sys.argv[2],float(sys.argv[3]),sys.argv[4]; shade=len(sys.argv)>5
W,H,BH,TOP,FPS=1080,1920,1350,285,30
seg=vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
  base_options=BaseOptions(model_asset_path=sys.argv[0].rsplit('/',2)[0]+'/models/selfie.tflite'),output_confidence_masks=True))
rd=lambda p,w,h:(subprocess.Popen(["ffmpeg","-v","error","-i",p,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE),w*h*3)
pf,nf=rd(F,W,H); pb,nb=rd(Bp,W,BH)
wr=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",F,
  "-map","0:v","-map","1:a","-c:v","libx264","-crf","18","-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",out],stdin=subprocess.PIPE)
a=np.zeros((BH,1,1),np.float32)
if shade:
    y=np.arange(520); a[:520,0,0]=150/255*(1-y/520)**1.5
i=0
while True:
    f=pf.stdout.read(nf)
    if len(f)<nf: break
    fr=np.frombuffer(f,np.uint8).reshape(H,W,3).copy(); t=i/FPS
    b=pb.stdout.read(nb) if pb else b''
    if t<until and len(b)==nb:
        B=np.frombuffer(b,np.uint8).reshape(BH,W,3)
        m=seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(B))).confidence_masks[0].numpy_view()
        m=np.clip((m.astype(np.float32).reshape(BH,W)-0.3)/0.4,0,1)[...,None]
        Bs=B.astype(np.float32)*(1-a)
        reg=fr[TOP:TOP+BH].astype(np.float32)
        fr[TOP:TOP+BH]=(reg*(1-m)+Bs*m).astype(np.uint8)
    wr.stdin.write(fr.tobytes()); i+=1
wr.stdin.close(); wr.wait(); print("frames",i)
