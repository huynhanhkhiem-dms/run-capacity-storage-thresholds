"""Fast deterministic verification of the core claims used in the paper."""
from fractions import Fraction
import random
import cfkey as ck
import orderkeys
from math import ceil, floor, log2


def all_rationals(maxden=40, multiplier=12):
    s=set()
    for q in range(1,maxden+1):
        for p in range(0,multiplier*q+1):
            f=Fraction(p,q)
            s.add((f.numerator,f.denominator))
    return sorted(s,key=lambda r: Fraction(*r))


def check_order_exhaustive():
    rats=all_rationals()
    enc=[ck.encode(r) for r in rats]
    assert len(enc)==len(set(enc))
    assert enc==sorted(enc)
    for r,e in zip(rats,enc): assert ck.decode(e)==r
    return len(rats)


def check_random(n=50000, seed=20260920):
    rnd=random.Random(seed)
    for _ in range(n):
        a=Fraction(rnd.randint(0,10**6),rnd.randint(1,10**6))
        b=Fraction(rnd.randint(0,10**6),rnd.randint(1,10**6))
        if a==b: continue
        ra=(a.numerator,a.denominator); rb=(b.numerator,b.denominator)
        assert (a<b)==(ck.encode(ra)<ck.encode(rb))
    return n


def check_simplest_small(maxden=30, trials=10000, seed=7):
    rnd=random.Random(seed)
    rats=all_rationals(maxden,4)
    for _ in range(trials):
        i=rnd.randrange(len(rats)-1); j=rnd.randrange(i+1,len(rats))
        x,y=rats[i],rats[j]
        k=ck.simplest_between(x,y)
        fx,fy,fk=Fraction(*x),Fraction(*y),Fraction(*k)
        assert fx<fk<fy
        # Brute-force every denominator smaller than k.q. If any numerator fits,
        # k is not minimum-denominator.
        for q in range(1,k[1]):
            lo=(x[0]*q)//x[1]+1
            hi=(y[0]*q-1)//y[1]
            assert lo>hi
    return trials


def check_sequence(nseq=100, nops=250, seed=11):
    rnd=random.Random(seed)
    total=0
    for _ in range(nseq):
        keys=[]
        for _ in range(nops):
            if keys and rnd.random()<0.2:
                del keys[rnd.randrange(len(keys))]
                continue
            p=rnd.randrange(len(keys)+1)
            a=keys[p-1] if p else None
            b=keys[p] if p<len(keys) else None
            k=ck.simplest_between(a,b)
            if a is not None: assert ck.less(a,k)
            if b is not None: assert ck.less(k,b)
            keys.insert(p,k); total+=1
        encoded=[ck.encode(k) for k in keys]
        assert encoded==sorted(encoded)
    return total



def _ceil_sum(r, t):
    q, s = divmod(r, t)
    return t*q*(q+1)//2 + s*(q+1)


def check_midpoint_run_formula():
    """Verify exact directional suffix growth and cumulative storage."""
    for digits in (orderkeys.DIGITS, orderkeys.DIGITS[:36]):
        B=len(digits)
        t_right=floor(log2(B))
        t_left=ceil(log2(B))
        lo=orderkeys.generate_key_between(None,None,digits)
        hi=orderkeys.generate_key_between(lo,None,digits)
        head_bytes=len(lo.encode('latin1'))

        # Right-moving: fixed upper endpoint.
        a=lo
        observed_suffix_sum=0
        for r in range(1,251):
            a=orderkeys.generate_key_between(a,hi,digits)
            suffix=len(a)-len(orderkeys.get_integer_part(a))
            observed_suffix_sum += suffix
            assert suffix==ceil(r/t_right), (B,'right',r,suffix,ceil(r/t_right),a)
            assert observed_suffix_sum==_ceil_sum(r,t_right)
            expected_total=r*head_bytes+_ceil_sum(r,t_right)
            # All generated keys in this canonical run share the same integer head.
            # The equality below checks the closed-form physical-byte total.
            if r==1:
                generated=[a]
            else:
                generated.append(a)
            assert sum(len(k.encode('latin1')) for k in generated)==expected_total

        # Left-moving: fixed lower endpoint.
        b=hi
        observed_suffix_sum=0
        generated=[]
        for r in range(1,251):
            b=orderkeys.generate_key_between(lo,b,digits)
            suffix=len(b)-len(orderkeys.get_integer_part(b))
            observed_suffix_sum += suffix
            assert suffix==ceil(r/t_left), (B,'left',r,suffix,ceil(r/t_left),b)
            assert observed_suffix_sum==_ceil_sum(r,t_left)
            generated.append(b)
            expected_total=r*head_bytes+_ceil_sum(r,t_left)
            assert sum(len(k.encode('latin1')) for k in generated)==expected_total
    return 'B=62 and B=36, both directions, exact cumulative bytes, r<=250'



def _prefix_sums(caps):
    out=[]
    total=0
    for c in caps:
        total += c
        out.append(total)
    return out


def _depth_for_r(prefix, r):
    return next(m for m, S_m in enumerate(prefix, 1) if S_m >= r)


def _packed_lengths(caps, r):
    lengths=[]
    for level, c in enumerate(caps, 1):
        take=min(c, r-len(lengths))
        lengths.extend([level]*take)
        if len(lengths)==r:
            return lengths
    raise AssertionError('profile too short for r')


def _shortest_distinct_total(B, r):
    """Minimum total length of r distinct strings over a B-symbol alphabet."""
    remaining=r
    length=0
    total=0
    slots=1  # the empty string
    while remaining:
        take=min(remaining, slots)
        total += take*length
        remaining -= take
        length += 1
        slots *= B
    return total


def check_run_capacity_bound():
    """Check the finite-alphabet lower bound, tail sums, inverse depths, and growth regimes."""
    # Proposition 1: compare its constructive lower bound with the exact
    # shortest-string packing for representative finite alphabets.
    for B in (2,4,16,62,256):
        for r in range(2,5001,37):
            total=_shortest_distinct_total(B,r)
            # Largest integer m with B^m <= (B-1)r/2, computed without floats.
            m=0
            while 2*(B**(m+1)) <= (B-1)*r:
                m += 1
            if m >= 1:
                assert 2*total >= r*m, (B,r,total,m)

    rnd=random.Random(20260923)
    profiles=[[rnd.randint(1,12) for _ in range(40)] for _ in range(250)]
    for caps in profiles:
        prefix=_prefix_sums(caps)
        max_r=min(prefix[-1],500)
        for r in range(1,max_r+1):
            lengths=_packed_lengths(caps,r)
            tail=0
            S=0
            for m in range(0,len(caps)+1):
                if m>0:
                    S += caps[m-1]
                tail += max(r-S,0)
                if S>=r:
                    break
            assert sum(lengths)==tail, (caps,r,sum(lengths),tail)
            assert max(lengths)==_depth_for_r(prefix,r)

            # Theorem 1, generalized depth-cost form.  Build a deterministic
            # nondecreasing cost by cumulative nonnegative increments and
            # verify the discrete tail-sum identity for this exact profile.
            if r == 1 or r == max_r or r % max(1, max_r//20) == 0:
                max_depth=max(lengths)
                increments=[rnd.randint(0,9) for _ in range(max_depth)]
                g=[0]*(max_depth+1)
                g[1]=rnd.randint(0,20)
                for m in range(1,max_depth):
                    g[m+1]=g[m]+increments[m]
                lhs=sum(g[d] for d in lengths)
                rhs=r*g[1]
                S=0
                for m in range(1,max_depth):
                    S += caps[m-1]
                    rhs += (g[m+1]-g[m])*max(r-S,0)
                assert lhs==rhs, (caps,r,g,lhs,rhs)

            # Theorem 1 inversion: reconstruct exact packed depths from
            # successive increments of a strictly increasing cumulative cost,
            # then reconstruct cumulative capacity from those depths.
            if r == max_r:
                max_depth=max(lengths)
                strict_g={d: 3*d*d + 2*d + 7 for d in range(1,max_depth+1)}
                cumulative=[0]
                for d in lengths:
                    cumulative.append(cumulative[-1] + strict_g[d])
                inv={value:depth for depth,value in strict_g.items()}
                recovered_depths=[inv[cumulative[i]-cumulative[i-1]]
                                  for i in range(1,len(cumulative))]
                assert recovered_depths==lengths, (caps,recovered_depths,lengths)
                for m in range(1,max_depth+1):
                    recovered_S=sum(1 for d in recovered_depths if d<=m)
                    expected_S=min(prefix[m-1], max_r)
                    assert recovered_S==expected_S, (caps,m,recovered_S,expected_S)

    # Theorem 1 dominance equivalence.  Construct paired exact profiles
    # with equal total capacity by moving one unit of capacity from a deeper
    # level to a shallower level.  The modified profile must dominate the
    # original in cumulative capacity, in generalized-inverse depths, and
    # for every tested nondecreasing depth cost.  Reversing the pair must
    # fail at the separating depth/step cost.
    dominance_pairs=0
    for _ in range(250):
        base=[rnd.randint(2,12) for _ in range(24)]
        j=rnd.randint(0,20)
        k=rnd.randint(j+1,23)
        better=base.copy()
        better[j] += 1
        better[k] -= 1
        p_better=_prefix_sums(better)
        p_base=_prefix_sums(base)
        assert all(a>=b for a,b in zip(p_better,p_base))
        assert any(a>b for a,b in zip(p_better,p_base))
        total=p_base[-1]
        d_better=[_depth_for_r(p_better,i) for i in range(1,total+1)]
        d_base=[_depth_for_r(p_base,i) for i in range(1,total+1)]
        assert all(a<=b for a,b in zip(d_better,d_base))
        assert any(a<b for a,b in zip(d_better,d_base))

        # Step costs isolate every cumulative-capacity coordinate.
        for m in range(1,len(base)+1):
            for r in (1, min(total, p_base[m-1]), total):
                cost_better=sum(1 for d in d_better[:r] if d>m)
                cost_base=sum(1 for d in d_base[:r] if d>m)
                assert cost_better<=cost_base

        # General nondecreasing costs test the representation-independent
        # cumulative-cost order at several horizons.
        increments=[rnd.randint(0,9) for _ in range(len(base)+1)]
        g=[0]*(len(base)+2)
        g[1]=rnd.randint(0,20)
        for m in range(1,len(base)+1):
            g[m+1]=g[m]+increments[m]
        for r in (1, total//3, 2*total//3, total):
            cb=sum(g[d] for d in d_better[:r])
            co=sum(g[d] for d in d_base[:r])
            assert cb<=co, (better,base,r,cb,co)

        # Reverse dominance is false, and a step cost at a separating depth
        # supplies an explicit witness.
        sep=next(m for m,(a,b) in enumerate(zip(p_better,p_base),1) if a>b)
        r=p_better[sep-1]
        reverse_base=sum(1 for d in d_base[:r] if d>sep)
        reverse_better=sum(1 for d in d_better[:r] if d>sep)
        assert reverse_base>reverse_better
        dominance_pairs += 1

    # Exact polynomial profiles S_m=m^alpha for alpha=1,2,3.  Their
    # per-level capacities are c_m=m^alpha-(m-1)^alpha.
    for alpha in (1,2,3):
        caps=[m**alpha-(m-1)**alpha for m in range(1,81)]
        prefix=_prefix_sums(caps)
        assert all(S==(m+1)**alpha for m,S in enumerate(prefix))
        for r in range(1,prefix[-1]+1, max(1,prefix[-1]//997)):
            d=_depth_for_r(prefix,r)
            assert (d-1)**alpha < r <= d**alpha
            lengths=_packed_lengths(caps,r)
            assert max(lengths)==d

    # Exact exponential profile S_m=2^m-1, i.e. c_m=2^(m-1).
    caps=[2**(m-1) for m in range(1,21)]
    prefix=_prefix_sums(caps)
    for m,S in enumerate(prefix,1):
        assert S==2**m-1
    for r in range(1,prefix[-1]+1,997):
        d=_depth_for_r(prefix,r)
        assert 2**(d-1) <= r <= 2**d-1
        assert max(_packed_lengths(caps,r))==d

    for C in range(1,33):
        for r in range(1,1001):
            lengths=[(i+C-1)//C for i in range(1,r+1)]
            assert sum(lengths)==_ceil_sum(r,C)
            assert max(lengths)==(r+C-1)//C
            q,s=divmod(r,C)
            assert _ceil_sum(r,C)==C*q*(q+1)//2+s*(q+1)
    return f'finite-alphabet packing B=2,4,16,62,256 + 250 variable profiles + {dominance_pairs} dominance pairs + polynomial/exponential regimes + C<=32; r<=1000'


def check_page_transition_formula():
    """Check Theorem 4 transfer, threshold signatures, sparse bounds, and payload probes."""
    rnd=random.Random(20260924)
    checked=0

    # General exact profiles: choose a monotone payload P(k)=k+c and set a
    # local limit that admits exactly m_X suffix levels.  Brute force the
    # first insertion whose packed depth exceeds that level.
    for _ in range(1000):
        caps=[rnd.randint(1,16) for _ in range(30)]
        prefix=_prefix_sums(caps)
        H=rnd.randint(0,12)
        w=rnd.randint(1,8)
        c=rnd.randint(0,20)
        m_X=rnd.randint(0,20)
        X=H+w*m_X+c
        predicted=(prefix[m_X-1] if m_X>0 else 0)+1
        r=1
        while True:
            d=_depth_for_r(prefix,r)
            if H+w*d+c > X:
                break
            r += 1
        assert r==predicted, (caps,H,w,c,m_X,X,r,predicted)
        shallow_capacity=(prefix[m_X-1] if m_X>0 else 0)
        # Threshold-based identification: if a threshold isolates depth m_X,
        # the observed first crossing recovers S_mX exactly.
        recovered_capacity = predicted - 1
        assert recovered_capacity == shallow_capacity, (caps,m_X,recovered_capacity,shallow_capacity)
        # Inverse design criterion: no overflow through horizon R iff R <= S_mX.
        for R in (1, max(1, shallow_capacity), shallow_capacity+1):
            expected_no_overflow = R <= shallow_capacity
            actual_no_overflow = R < predicted
            assert actual_no_overflow == expected_no_overflow, (caps,m_X,R,shallow_capacity,predicted)

        # Sparse threshold-signature bounds.  Observe cumulative capacity only
        # at two depths and verify the theorem's sharp positive-integer bounds
        # for an intermediate unobserved depth.
        m1=rnd.randint(0,17)
        m2=rnd.randint(m1+2,20)
        m=rnd.randint(m1+1,m2-1)
        T1=(prefix[m1-1] if m1>0 else 0)
        T2=prefix[m2-1]
        Sm=prefix[m-1]
        lower=T1+(m-m1)
        upper=T2-(m2-m)
        assert lower <= Sm <= upper, (caps,m1,m,m2,T1,Sm,T2,lower,upper)

        # Both bounds are attainable by a positive-integer profile segment
        # with the same observed endpoint capacities.
        D=T2-T1
        width=m2-m1
        assert D >= width
        # Lower-bound construction: unit capacity through m, then put all
        # surplus at the first level after m while keeping later levels >=1.
        left=[1]*(m-m1)
        right=[1]*(m2-m)
        surplus=D-width
        if right:
            right[0]+=surplus
        else:
            left[-1]+=surplus
        assert T1+sum(left)==lower
        assert T1+sum(left)+sum(right)==T2

        # Upper-bound construction: put all surplus before/at m.
        left2=[1]*(m-m1)
        right2=[1]*(m2-m)
        if left2:
            left2[-1]+=surplus
        else:
            right2[0]+=surplus
        assert T1+sum(left2)==upper
        assert T1+sum(left2)+sum(right2)==T2

        # Capacity-dominance threshold consequence: move one unit from a
        # deeper level to a shallower one, preserving total capacity.  The
        # dominating profile cannot cross the same monotone threshold earlier.
        if len(caps) >= 3:
            j=rnd.randint(0,min(m_X, len(caps)-2)) if m_X>0 else 0
            k=rnd.randint(max(j+1,1),len(caps)-1)
            if caps[k] > 1:
                dom=caps.copy(); dom[j]+=1; dom[k]-=1
                pdom=_prefix_sums(dom)
                assert all(a>=b for a,b in zip(pdom,prefix))
                predicted_dom=(pdom[m_X-1] if m_X>0 else 0)+1
                assert predicted_dom >= predicted
        checked += 1

    # Constant-profile closed form with a limit that may fall between two
    # suffix-width increments.
    for _ in range(1000):
        C=rnd.randint(1,32)
        H=rnd.randint(0,12)
        w=rnd.randint(1,8)
        c=rnd.randint(0,20)
        X=rnd.randint(H+c,H+c+500)
        predicted=C*((X-H-c)//w)+1
        r=1
        while H+w*((r+C-1)//C)+c <= X:
            r += 1
        assert r==predicted, (C,H,w,c,X,r,predicted)

        # Corollary 5: a q*w payload perturbation advances the crossing by C*q.
        max_q=(X-H-c)//w
        if max_q >= 1:
            q=rnd.randint(1,min(5,max_q))
            predicted_shifted=C*((X-H-(c+q*w))//w)+1
            assert predicted-predicted_shifted == C*q, (C,H,w,c,X,q,predicted,predicted_shifted)
        checked += 1
    return checked

def check_mediant_gap_family():
    checked=0
    for n in range(2,1000):
        if __import__('math').gcd(n+2,3)!=1:
            continue
        x=(n-1,2*n-1); y=(n+2,2*n+1)
        s=ck.simplest_between(x,y); m=ck.reduced_mediant(x,y)
        assert s==(1,2), (n,s)
        assert m==(2*n+1,4*n), (n,m)
        assert m[1]//s[1]==2*n
        checked+=1
    return checked

if __name__=='__main__':
    n=check_order_exhaustive()
    print('exhaustive rationals:',n,'PASS')
    n2=check_random(); print('random pair comparisons:',n2,'PASS')
    n3=check_simplest_small(); print('simplest-fraction brute-force intervals:',n3,'PASS')
    n4=check_sequence(); print('random insert/delete allocations:',n4,'PASS')
    n5=check_midpoint_run_formula(); print('midpoint run exact formula:',n5,'PASS')
    n6=check_run_capacity_bound(); print('run-capacity packing bound:',n6,'PASS')
    n7=check_page_transition_formula(); print('page-transition formula:',n7,'PASS')
    n8=check_mediant_gap_family(); print('unbounded mediant-gap family instances:',n8,'PASS')
