import wave,json,numpy as np,re
w=wave.open("audio/skit.wav");sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
hop=int(.02*sr);win=int(.04*sr)
rows=[]
for i in range(0,len(x)-win,hop):
    f=x[i:i+win]*np.hanning(win);e=np.sqrt((f**2).mean())
    ac=np.correlate(f,f,'full')[win-1:]
    lo,hi=int(sr/320),int(sr/75)
    k=lo+ac[lo:hi].argmax();v=ac[k]/(ac[0]+1e-9)
    rows.append((i/sr,e,sr/k if v>.45 else 0))
t=np.array([r[0] for r in rows]);e=np.array([r[1] for r in rows]);f=np.array([r[2] for r in rows])
th=max(np.percentile(e,30)*1.5,.004)
lab=np.where(e<th,'.',np.where(f==0,'?',np.where(f<165,'M','F')))
np.savez("qa/spk.npz",t=t,e=e,f=f,lab=lab)
def show(a,b):
    m=(t>=a)&(t<b);print(f"{a:6.2f} ", "".join(lab[m]))
print("th",th)
for a in [7,10.4,11.6,12.6,14,15.4,19,25.4,26,28,28.6,35,36,43.4,44,44.6,61.2,63.8,64.4,66.2,67.2,79.8,81.2,92.8,95.6]:
    show(a,a+1.2)
