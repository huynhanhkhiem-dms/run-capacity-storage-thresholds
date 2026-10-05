"""Replay josephg/editing-traces sequential ASCII traces.

The output schema intentionally matches the archived benchmark summaries so
`compare_rerun.py` can perform a field-for-field deterministic comparison.
Timing fields are emitted for transparency but are not compared.
"""
from pathlib import Path
import argparse, gzip, json, time, statistics
from sortedcontainers import SortedList
import cfkey as ck
import orderkeys

class Scheme:
    def __init__(self, name):
        self.name = name
    @property
    def label(self):
        return {'fi62':'FI-62','fi36':'FI-36','sri':'Farey-SRI'}[self.name]
    def alloc(self, a, b):
        if self.name == 'sri':
            return ck.simplest_between(a, b)
        digits = orderkeys.DIGITS if self.name == 'fi62' else orderkeys.DIGITS[:36]
        return orderkeys.generate_key_between(a, b, digits)
    def bits(self, k):
        return ck.keylen_bits(k) if self.name == 'sri' else len(k) * 8
    def token(self, k):
        return ck.encode(k) if self.name == 'sri' else k.encode('latin1')


def replay(scheme, data, sample_every=2000):
    sl = SortedList()
    tok2id = {}
    tok2char = {}
    sizes = []
    curve = []
    nins = ndel = 0
    cur_max = 0
    alloc_s = 0.0
    wall0 = time.time()

    for txn in data['txns']:
        for pos, dl, ins in txn['patches']:
            if dl:
                for tok in list(sl[pos:pos+dl]):
                    tok2id.pop(tok, None)
                    tok2char.pop(tok, None)
                del sl[pos:pos+dl]
                ndel += dl
            if ins:
                p = pos
                for ch in ins:
                    lt = sl[p-1] if p else None
                    rt = sl[p] if p < len(sl) else None
                    a = tok2id.get(lt) if lt is not None else None
                    b = tok2id.get(rt) if rt is not None else None
                    t0 = time.perf_counter()
                    k = scheme.alloc(a, b)
                    alloc_s += time.perf_counter() - t0
                    tok = scheme.token(k)
                    if lt is not None:
                        assert lt < tok
                    if rt is not None:
                        assert tok < rt
                    sl.add(tok)
                    tok2id[tok] = k
                    tok2char[tok] = ch
                    bits = scheme.bits(k)
                    sizes.append(bits)
                    cur_max = max(cur_max, bits)
                    nins += 1
                    p += 1
                    if nins % sample_every == 0:
                        curve.append([nins, cur_max])

    reconstructed = ''.join(tok2char[t] for t in sl)
    assert reconstructed == data['endContent']

    live_bits = [scheme.bits(tok2id[t]) for t in sl]
    ss = sorted(sizes)
    n = len(ss)
    wall = time.time() - wall0
    summary = {
        'scheme': scheme.label,
        'n_txns': len(data['txns']),
        'n_ins': nins,
        'n_del': ndel,
        'n_live': len(sl),
        'final_chars': len(data['endContent']),
        'gen_mean_bits': statistics.fmean(ss) if ss else 0,
        'gen_max_bits': ss[-1] if ss else 0,
        'gen_p50_bits': ss[n//2] if ss else 0,
        'gen_p95_bits': ss[int(.95*n)] if ss else 0,
        'gen_p99_bits': ss[int(.99*n)] if ss else 0,
        'live_mean_bits': statistics.fmean(live_bits) if live_bits else 0,
        'live_max_bits': max(live_bits) if live_bits else 0,
        'live_bytes': sum((b+7)//8 for b in live_bits),
        'total_gen_bytes': sum((b+7)//8 for b in ss),
        'alloc_secs': round(alloc_s, 2),
        'wall_secs': round(wall, 1),
        'us_per_alloc': round(1e6*alloc_s/max(1,nins), 2),
        'reconstruction_match': True,
    }
    return {'summary': summary, 'curve': curve}, list(sl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trace-dir', required=True, type=Path)
    ap.add_argument('--trace', required=True)
    ap.add_argument('--scheme', choices=['fi62','fi36','sri'], required=True)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--keys-output', type=Path)
    args = ap.parse_args()
    with gzip.open(args.trace_dir / f'{args.trace}.json.gz', 'rt') as f:
        data = json.load(f)
    res, keys = replay(Scheme(args.scheme), data)
    res['summary']['trace'] = args.trace
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(res, indent=2))
    if args.keys_output:
        import pickle
        args.keys_output.write_bytes(pickle.dumps(keys))
    print(json.dumps(res['summary'], indent=2))

if __name__ == '__main__':
    main()
