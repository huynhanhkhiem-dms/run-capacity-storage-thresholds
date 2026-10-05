"""Rational order keys used in the minimum-denominator experiments.

The allocator chooses the rational of minimum denominator (then minimum numerator)
strictly inside an open interval.  This is the classical "simplest fraction"
problem; see Sivignon (Discrete Applied Mathematics, 2016).  The byte encoder is
an LCF-style continued-fraction encoding inspired by Matula & Kornerup (ARITH 1983).
The contribution of the accompanying paper is not the invention of either primitive.
"""
from __future__ import annotations

from math import gcd
from typing import Optional, Tuple

Rat = Tuple[int, int]
ZERO: Rat = (0, 1)
INF: Rat = (1, 0)


def normalize(r: Rat) -> Rat:
    p, q = r
    if q == 0:
        return INF
    if q < 0:
        p, q = -p, -q
    g = gcd(abs(p), q)
    return p // g, q // g


def less(a: Rat, b: Rat) -> bool:
    if a[1] == 0:
        return False
    if b[1] == 0:
        return True
    return a[0] * b[1] < b[0] * a[1]


def reduced_mediant(a: Optional[Rat], b: Optional[Rat]) -> Rat:
    """Reduced mediant, retained only for diagnostic ablations."""
    p1, q1 = a if a is not None else ZERO
    p2, q2 = b if b is not None else INF
    return normalize((p1 + p2, q1 + q2))


def simplest_between(x: Optional[Rat], y: Optional[Rat]) -> Rat:
    """Minimum-denominator rational strictly between x and y.

    Ties are broken by numerator.  None denotes 0/1 on the left and +infinity
    on the right.  The implementation is iterative, avoiding recursion-depth
    failures on long continued-fraction paths.
    """
    p1, q1 = normalize(x) if x is not None else ZERO
    p2, q2 = normalize(y) if y is not None else INF
    if q1 == 0:
        raise ValueError("lower bound cannot be +infinity")
    if q2 != 0 and not (p1 * q2 < p2 * q1):
        raise ValueError("expected x < y")

    stack = []
    while True:
        a = p1 // q1
        # If the next integer lies strictly below the upper endpoint, it is
        # necessarily the minimum-denominator solution.
        if q2 == 0 or (a + 1) * q2 < p2:
            p, q = a + 1, 1
            break

        fx_p, fx_q = p1 - a * q1, q1
        fy_p, fy_q = p2 - a * q2, q2
        stack.append(a)

        # Reciprocal maps (x-a, y-a) to (1/(y-a), 1/(x-a)) and reverses order.
        p1, q1 = fy_q, fy_p
        if fx_p == 0:
            p2, q2 = INF
        else:
            p2, q2 = fx_q, fx_p

    for a in reversed(stack):
        p, q = a * p + q, p
    return normalize((p, q))


def to_cf(p: int, q: int):
    """Canonical continued fraction of p/q; q > 0."""
    p, q = normalize((p, q))
    terms = []
    while True:
        a = p // q
        terms.append(a)
        p, q = q, p - a * q
        if q == 0:
            break
    if len(terms) > 1 and terms[-1] == 1:
        terms.pop()
        terms[-1] += 1
    return terms


def from_cf(terms):
    p, q = 1, 0
    for a in reversed(terms):
        p, q = a * p + q, p
    return normalize((p, q))


class BitWriter:
    __slots__ = ("bits",)
    def __init__(self):
        self.bits = []
    def put(self, b: int, flip: bool):
        self.bits.append((b ^ 1) if flip else b)
    def bytes(self) -> bytes:
        out = bytearray()
        acc = n = 0
        for b in self.bits:
            acc = (acc << 1) | b
            n += 1
            if n == 8:
                out.append(acc)
                acc = n = 0
        if n:
            out.append(acc << (8 - n))
        return bytes(out)


def _put_term(w: BitWriter, m: int, flip: bool, end_possible: bool):
    if m < 1:
        raise ValueError("term code requires m >= 1")
    L = m.bit_length() - 1
    if end_possible:
        w.put(0, flip)
    for _ in range(L):
        w.put(1, flip)
    w.put(0, flip)
    for i in range(L - 1, -1, -1):
        w.put((m >> i) & 1, flip)


def encode(r: Rat) -> bytes:
    """Byte string whose ordinary lexicographic order matches rational order."""
    p, q = normalize(r)
    if p < 0 or q <= 0:
        raise ValueError("encoder expects a non-negative finite rational")
    terms = to_cf(p, q)
    w = BitWriter()
    _put_term(w, terms[0] + 1, False, True)
    prev_one = False
    for i, a in enumerate(terms[1:], start=1):
        _put_term(w, a, i % 2 == 1, not prev_one)
        prev_one = a == 1
    w.put(1, len(terms) % 2 == 1)  # END with continued-fraction parity
    return w.bytes()


def decode(buf: bytes) -> Rat:
    bits = [(byte >> i) & 1 for byte in buf for i in range(7, -1, -1)]
    pos = idx = 0
    terms = []
    prev_one = False
    while True:
        if pos >= len(bits):
            raise ValueError("truncated encoding")
        flip = idx % 2 == 1
        if not prev_one:
            b = bits[pos] ^ (1 if flip else 0)
            pos += 1
            if b == 1:
                break
        L = 0
        while True:
            if pos >= len(bits):
                raise ValueError("truncated term")
            b = bits[pos] ^ (1 if flip else 0)
            pos += 1
            if b == 0:
                break
            L += 1
        m = 1
        for _ in range(L):
            if pos >= len(bits):
                raise ValueError("truncated suffix")
            b = bits[pos] ^ (1 if flip else 0)
            pos += 1
            m = (m << 1) | b
        t = m - 1 if idx == 0 else m
        terms.append(t)
        prev_one = idx >= 1 and t == 1
        idx += 1
    return from_cf(terms)


def keylen_bits(r: Rat) -> int:
    p, q = normalize(r)
    terms = to_cf(p, q)
    n = 2 * ((terms[0] + 1).bit_length() - 1) + 2
    prev_one = False
    for a in terms[1:]:
        n += 2 * (a.bit_length() - 1) + 1 + (0 if prev_one else 1)
        prev_one = a == 1
    return n + 1


def keylen_bytes(r: Rat) -> int:
    return (keylen_bits(r) + 7) // 8
