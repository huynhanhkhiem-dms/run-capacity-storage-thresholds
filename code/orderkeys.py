"""Iterative implementation of the Greenspan/rocicorp fractional-indexing format.

This local copy is used for deterministic reruns without relying on recursive
midpoint code.  `validate_fi_reference.py` can compare it with the published
Python `fractional-indexing==0.1.3` package when that dependency is installed.
"""
from typing import Optional

DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
ZERO = DIGITS[0]
SMALLEST_INT = 'A' + ZERO * 26


def _maps(digits):
    return {c:i for i,c in enumerate(digits)}


def get_integer_length(head: str) -> int:
    if 'a' <= head <= 'z': return ord(head)-ord('a')+2
    if 'A' <= head <= 'Z': return ord('Z')-ord(head)+2
    raise ValueError('invalid key head')


def get_integer_part(key: str) -> str:
    n=get_integer_length(key[0])
    if n>len(key): raise ValueError('invalid key')
    return key[:n]


def increment_integer(x: str, digits=DIGITS):
    idx=_maps(digits); B=len(digits); zero=digits[0]
    head,digs=x[0],list(x[1:]); carry=True
    for i in reversed(range(len(digs))):
        d=idx[digs[i]]+1
        if d==B: digs[i]=zero
        else: digs[i]=digits[d]; carry=False; break
    if carry:
        if head=='Z': return 'a'+zero
        if head=='z': return None
        h=chr(ord(head)+1)
        if h>'a': digs.append(zero)
        else: digs.pop()
        return h+''.join(digs)
    return head+''.join(digs)


def decrement_integer(x: str, digits=DIGITS):
    idx=_maps(digits); B=len(digits)
    head,digs=x[0],list(x[1:]); borrow=True
    for i in reversed(range(len(digs))):
        d=idx[digs[i]]-1
        if d==-1: digs[i]=digits[-1]
        else: digs[i]=digits[d]; borrow=False; break
    if borrow:
        if head=='a': return 'Z'+digits[-1]
        if head=='A': return None
        h=chr(ord(head)-1)
        if h<'Z': digs.append(digits[-1])
        else: digs.pop()
        return h+''.join(digs)
    return head+''.join(digs)


def midpoint_iter(a: str, b: Optional[str], digits=DIGITS) -> str:
    idx=_maps(digits); B=len(digits); zero=digits[0]
    out=[]
    while True:
        if b:
            n=0; la,lb=len(a),len(b)
            while n<lb:
                x=a[n] if n<la else zero
                if x!=b[n]: break
                n+=1
            if n:
                out.append(b[:n]); a,b=a[n:],b[n:]
                if b=='': b=None
                continue
        da=idx[a[0]] if a else 0
        db=idx[b[0]] if b is not None else B
        if db-da>1:
            mid=(da+db+1)//2
            out.append(digits[mid]); return ''.join(out)
        if b is not None and len(b)>1:
            out.append(b[0]); return ''.join(out)
        out.append(digits[da]); a,b=a[1:],None


def generate_key_between(a: Optional[str], b: Optional[str], digits=DIGITS) -> str:
    zero=digits[0]
    smallest='A'+zero*26
    if a is None and b is None: return 'a'+zero
    if a is None:
        ib=get_integer_part(b); fb=b[len(ib):]
        if ib==smallest: return ib+midpoint_iter('',fb,digits)
        if ib<b: return ib
        res=decrement_integer(ib,digits)
        if res is None: raise ValueError('cannot decrement')
        return res
    if b is None:
        ia=get_integer_part(a); fa=a[len(ia):]
        i=increment_integer(ia,digits)
        return ia+midpoint_iter(fa,None,digits) if i is None else i
    ia=get_integer_part(a); fa=a[len(ia):]
    ib=get_integer_part(b); fb=b[len(ib):]
    if ia==ib: return ia+midpoint_iter(fa,fb,digits)
    i=increment_integer(ia,digits)
    if i is None: raise ValueError('cannot increment')
    if i<b: return i
    return ia+midpoint_iter(fa,None,digits)
