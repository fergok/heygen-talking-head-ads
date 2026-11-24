import importlib.util,subprocess,glob,os,shutil,json
from PIL import Image
import numpy as np
sp=importlib.util.spec_from_file_location("e","edit.py");e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
F=e.B+"ffmpeg"
def frames(src,n0,cnt):
    d="m/fx";shutil.rmtree(d,ignore_errors=True);os.makedirs(d)
    subprocess.run([F,"-y","-v","quiet","-ss",f"{n0/30-0.5:.4f}","-i",src,"-vf",f"select='gte(n\\,0)',fps=30","-t","1.2",f"{d}/%03d.png"])
    return sorted(glob.glob(d+"/*.png"))
def band(p):
    a=np.array(Image.open(p).convert("L")).astype(int)
    return a[1380:1530,60:1020]>235
def full(p):
    return np.array(Image.open(p).convert("L").resize((108,192))).astype(int)
for v in "ABCD":
    src=f"out/REDSKIT_Hook{v}.mp4";bad=0
    for s in e.broll_shots():
        for tag,t in (("in",s[0]),("out",s[1])):
            n=round(t*30);fs=frames(src,n,36)
            d=[(band(fs[i])^band(fs[i-1])).sum() for i in range(1,len(fs))]
            p=[np.abs(full(fs[i])-full(fs[i-1])).mean() for i in range(1,len(fs))]
            on=d[14]>200 and d[13]<d[14]*.5 and d[15]<d[14]*.5
            pic=p[14]>=max(p[13],p[15])
            if not (on and pic): bad+=1
            print(v,tag,round(t,3),s[2],"txt",d[13],d[14],d[15],"pic",round(p[13],1),round(p[14],1),round(p[15],1),"" if on and pic else "<<<")
    print(v,"misaligned:",bad)
