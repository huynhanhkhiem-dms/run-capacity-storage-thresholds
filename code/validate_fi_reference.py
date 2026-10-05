"""Optional byte-for-byte comparison with fractional-indexing==0.1.3.
Run after `pip install -r ../requirements.txt`.
"""
import random
import orderkeys

try:
    import fractional_indexing as ref
except ImportError as exc:
    raise SystemExit('Install fractional-indexing==0.1.3 first') from exc

rnd=random.Random(9)
lst=[]
checks=0
for _ in range(5000):
    p=rnd.randrange(len(lst)+1)
    a=lst[p-1] if p else None
    b=lst[p] if p<len(lst) else None
    k=ref.generate_key_between(a,b)
    k2=orderkeys.generate_key_between(a,b)
    assert k==k2,(a,b,k,k2)
    lst.insert(p,k); checks+=1
print('byte-for-byte FI checks:',checks,'PASS')
