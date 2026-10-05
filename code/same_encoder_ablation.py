"""Same-encoder ablation for the canonical right-moving run.

Maps Greenspan FI positions between a0 and a1 to their exact base-B rationals,
then encodes both those positions and the SRI positions with the same LCF-style
continued-fraction byte encoder from cfkey.py. This isolates allocation policy
from physical encoding.
"""
from __future__ import annotations
import argparse, json, os, sqlite3, tempfile, math
from fractions import Fraction
from pathlib import Path
import cfkey as ck
import orderkeys


def fi_suffix_fraction(key: str, digits=orderkeys.DIGITS, head='a0') -> Fraction:
    if not key.startswith(head):
        raise ValueError(f'expected key with head {head!r}: {key!r}')
    suf = key[len(head):]
    B = len(digits)
    idx = {c:i for i,c in enumerate(digits)}
    num = 0
    den = 1
    for c in suf:
        num = num * B + idx[c]
        den *= B
    return Fraction(num, den)


def fi_positions(r: int, digits=orderkeys.DIGITS):
    """Exact canonical right-run positions as rational pairs.

    Theorem 2 implies C=floor(log2 B) midpoint choices per suffix level.
    At level m and within-level step j, the suffix is (B-1)^(m-1) d_j
    with d_j = B-floor(B/2^j), hence numerator B^m-B+d_j over B^m.
    This avoids reparsing O(r^2) suffix characters in the ablation.
    """
    B=len(digits); C=math.floor(math.log2(B))
    if C < 1:
        raise ValueError('radix must be at least 2')
    out=[]; Bpow=B
    for i in range(1,r+1):
        j=(i-1)%C + 1
        if i>1 and j==1:
            Bpow *= B
        d = B - (B // (1 << j))
        out.append((Bpow - B + d, Bpow))
    return out


def validate_formula_prefix(n=250, digits=orderkeys.DIGITS):
    """Cross-check the closed-form rational map against actual allocator keys."""
    expected=fi_positions(n,digits)
    a,b='a0','a1'
    for i,(p,q) in enumerate(expected, start=1):
        k=orderkeys.generate_key_between(a,b,digits)
        x=fi_suffix_fraction(k,digits,'a0')
        if x != Fraction(p,q):
            raise AssertionError((i,k,x,(p,q)))
        a=k


def sri_positions(r:int, validate_prefix:int=250):
    """Exact canonical SRI positions i/(i+1), with allocator cross-check.

    Recomputing simplest_between from scratch for every i makes the 10,000-row
    ablation unnecessarily slow even though the canonical closed form is exact.
    We validate a deterministic prefix against the allocator, then use the
    proved closed form for the full run.  This changes runtime only.
    """
    a=(0,1); b=(1,1)
    for i in range(1,min(r,validate_prefix)+1):
        k=ck.simplest_between(a,b)
        expected=(i,i+1)
        if ck.normalize(k)!=expected:
            raise AssertionError((i,k,expected))
        a=k
    return [(i,i+1) for i in range(1,r+1)]


def lcf_bytes_fraction(x: Fraction)->bytes:
    return ck.encode((x.numerator,x.denominator))


def sqlite_size(keys, page_size=4096, payload=16):
    fd,path=tempfile.mkstemp(prefix='sameenc_',suffix='.db'); os.close(fd); os.unlink(path)
    con=sqlite3.connect(path)
    con.execute(f'PRAGMA page_size={page_size}')
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('VACUUM')
    con.execute('CREATE TABLE items (k BLOB PRIMARY KEY, v BLOB) WITHOUT ROWID')
    con.executemany('INSERT INTO items VALUES (?,?)',((sqlite3.Binary(k),b'x'*payload) for k in keys))
    con.commit()
    pages=con.execute('PRAGMA page_count').fetchone()[0]
    overflow=None
    try:
        overflow=con.execute("SELECT count(*) FROM dbstat WHERE name='items' AND pagetype='overflow'").fetchone()[0]
    except sqlite3.OperationalError:
        pass
    con.close(); size=os.path.getsize(path); os.remove(path)
    return {'db_bytes':size,'pages':pages,'overflow_pages':overflow}


def one(r:int, do_db=True):
    fi=fi_positions(r)
    sri=sri_positions(r)
    fi_keys=[ck.encode(x) for x in fi]
    sri_keys=[ck.encode(x) for x in sri]
    out={
        'r':r,
        'FI_same_encoder':{
            'key_bytes':sum(map(len,fi_keys)),
            'max_key_bytes':max(map(len,fi_keys)),
            'mean_key_bytes':sum(map(len,fi_keys))/r,
        },
        'SRI_same_encoder':{
            'key_bytes':sum(map(len,sri_keys)),
            'max_key_bytes':max(map(len,sri_keys)),
            'mean_key_bytes':sum(map(len,sri_keys))/r,
        },
    }
    out['key_byte_ratio']=out['FI_same_encoder']['key_bytes']/out['SRI_same_encoder']['key_bytes']
    if do_db:
        out['FI_same_encoder']['sqlite_4k']=sqlite_size(fi_keys)
        out['SRI_same_encoder']['sqlite_4k']=sqlite_size(sri_keys)
        out['sqlite_file_ratio']=out['FI_same_encoder']['sqlite_4k']['db_bytes']/out['SRI_same_encoder']['sqlite_4k']['db_bytes']
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sizes',nargs='*',type=int,default=[100,1000,5000,10000]); ap.add_argument('--no-db',action='store_true')
    args=ap.parse_args()
    validate_formula_prefix()
    result={str(r):one(r,not args.no_db) for r in args.sizes}
    dst=Path(__file__).resolve().parents[1]/'results'/'same_encoder_ablation.json'
    dst.write_text(json.dumps(result,indent=2))
    for r in args.sizes:
        row=result[str(r)]
        msg=(f"r={r}: key ratio={row['key_byte_ratio']:.1f}x")
        if not args.no_db:
            msg += f", SQLite ratio={row['sqlite_file_ratio']:.1f}x"
        print(msg, flush=True)
    print(f"PASS: same-encoder ablation; wrote {dst}", flush=True)

if __name__=='__main__': main()
