"""Regenerate the small synthetic result set cited in the revised manuscript."""
import json,random
from pathlib import Path
import cfkey as ck
import orderkeys

class FI:
    def __init__(self,digits): self.digits=digits
    def alloc(self,a,b): return orderkeys.generate_key_between(a,b,self.digits)
    def bytes(self,k): return len(k.encode('latin1'))
class SRI:
    def alloc(self,a,b): return ck.simplest_between(a,b)
    def bytes(self,k): return len(ck.encode(k))
class MED:
    def alloc(self,a,b): return ck.reduced_mediant(a,b)
    def bytes(self,k): return len(ck.encode(k))

def run(sc,r,mode,seed=11):
    rnd=random.Random(seed); lo=sc.alloc(None,None); hi=sc.alloc(lo,None); a,b=lo,hi
    mx=tot=0
    for i in range(r):
        if mode=='append': k=sc.alloc(b,None); b=k
        elif mode=='rightrun': k=sc.alloc(a,b); a=k
        elif mode=='alternating':
            k=sc.alloc(a,b)
            if i%2:a=k
            else:b=k
        elif mode=='random':
            k=sc.alloc(a,b)
            if rnd.random()<.5:a=k
            else:b=k
        elif mode=='runs64':
            k=sc.alloc(a,b)
            if i%64==63:a,b=lo,k
            else:a=k
        s=sc.bytes(k); mx=max(mx,s); tot+=s
    return [mx,tot/r]

def main():
    fi62=FI(orderkeys.DIGITS); fi36=FI(orderkeys.DIGITS[:36]); sri=SRI(); med=MED()
    jobs=[
      ('FI-62',fi62,'rightrun',1000),('FI-62',fi62,'rightrun',10000),
      ('Farey-SRI',sri,'rightrun',1000),('Farey-SRI',sri,'rightrun',10000),('Farey-SRI',sri,'rightrun',100000),
      ('FI-62',fi62,'append',10000),('Farey-SRI',sri,'append',10000),
      ('FI-62',fi62,'alternating',1000),
      ('Farey-SRI',sri,'alternating',1000),
      ('FI-62',fi62,'random',1000),('Farey-SRI',sri,'random',1000),
      ('Farey-SRI',sri,'runs64',10000),('Farey-SRI',sri,'runs64',100000),
      ('Reduced-Mediant',med,'runs64',1000),('Reduced-Mediant',med,'runs64',10000),
      ('FI-36',fi36,'rightrun',10000),
    ]
    out={}
    for name,sc,mode,r in jobs:
        out[f'{name}|{mode}|{r}']=run(sc,r,mode)
        print(name,mode,r,out[f'{name}|{mode}|{r}'],flush=True)
    dest=Path(__file__).resolve().parents[1]/'results'/'synthetic_valid.json'
    dest.write_text(json.dumps(out,indent=2)); print(dest)
if __name__=='__main__': main()
