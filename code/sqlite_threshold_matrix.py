"""Validate theory-predicted first-overflow insertions across page size and payload."""
from __future__ import annotations
from pathlib import Path
import json, sqlite3, tempfile
import orderkeys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'sqlite_threshold_matrix.json'
PAGE_SIZES=[1024,2048,4096,8192]
BASE_PAYLOAD_BYTES=16
PAYLOAD_SENSITIVITY_4K=[0,16,32,48]
H=2
C=5
RECORD_OVERHEAD=4

def max_local_index_payload(U:int)->int:
    return ((U-12)*64)//255 - 23

def predicted_threshold(U:int, payload_bytes:int)->int:
    X=max_local_index_payload(U)
    # Throughout the tested range the SQLite record payload is
    # key bytes + fixed BLOB bytes + four bytes of header/serial-type overhead.
    return C*(X-H-payload_bytes-RECORD_OVERHEAD)+1

def generate_tokens(r:int):
    lo=orderkeys.generate_key_between(None,None,orderkeys.DIGITS)
    hi=orderkeys.generate_key_between(lo,None,orderkeys.DIGITS)
    a=lo; toks=[]
    for _ in range(r):
        a=orderkeys.generate_key_between(a,hi,orderkeys.DIGITS)
        toks.append(a.encode('latin1'))
    return toks

def measure(tokens, page_size:int, payload_bytes:int, path:Path):
    if path.exists(): path.unlink()
    con=sqlite3.connect(path)
    con.execute(f'PRAGMA page_size={page_size}')
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('CREATE TABLE items(k BLOB PRIMARY KEY, payload BLOB NOT NULL) WITHOUT ROWID')
    payload=b'x'*payload_bytes
    con.executemany('INSERT INTO items(k,payload) VALUES (?,?)',((sqlite3.Binary(k),payload) for k in tokens))
    con.commit()
    rows=con.execute("SELECT pagetype,count(*),max(mx_payload) FROM dbstat WHERE name='items' GROUP BY pagetype").fetchall()
    con.close()
    pages={kind:count for kind,count,_ in rows}
    max_payload=max((mx or 0) for _,_,mx in rows)
    return {'max_record_payload':max_payload,'overflow_pages':pages.get('overflow',0),'pages_by_type':pages,'db_bytes':path.stat().st_size}

def validate(page_size:int,payload_bytes:int,td:Path):
    X=max_local_index_payload(page_size)
    rstar=predicted_threshold(page_size,payload_bytes)
    toks=generate_tokens(rstar)
    tag=f'{page_size}_{payload_bytes}'
    before=measure(toks[:-1],page_size,payload_bytes,td/f'{tag}_before.sqlite')
    at=measure(toks,page_size,payload_bytes,td/f'{tag}_at.sqlite')
    expected_before_key=H + ((rstar-1 + C-1)//C)
    expected_at_key=H + ((rstar + C-1)//C)
    extra=payload_bytes+RECORD_OVERHEAD
    assert before['max_record_payload']==expected_before_key+extra, (page_size,payload_bytes,before,expected_before_key)
    assert at['max_record_payload']==expected_at_key+extra, (page_size,payload_bytes,at,expected_at_key)
    assert before['max_record_payload']==X, (page_size,payload_bytes,before['max_record_payload'],X)
    assert at['max_record_payload']==X+1, (page_size,payload_bytes,at['max_record_payload'],X)
    assert before['overflow_pages']==0, (page_size,payload_bytes,before)
    assert at['overflow_pages']>=1, (page_size,payload_bytes,at)
    return {'page_size':page_size,'fixed_payload_bytes':payload_bytes,'max_local_payload':X,
            'predicted_first_overflow_r':rstar,'before_r':rstar-1,
            'before_max_record_payload':before['max_record_payload'],'before_overflow_pages':before['overflow_pages'],
            'at_r':rstar,'at_max_record_payload':at['max_record_payload'],'at_overflow_pages':at['overflow_pages']}

def main():
    rows=[]
    seen=set()
    configs=[(U,BASE_PAYLOAD_BYTES) for U in PAGE_SIZES]
    configs += [(4096,p) for p in PAYLOAD_SENSITIVITY_4K]
    configs=[c for c in configs if not (c in seen or seen.add(c))]
    max_r=max(predicted_threshold(U,p) for U,p in configs)
    # All configurations use the same canonical right-moving allocator run.
    # Generate it once and reuse prefixes; this changes runtime only, not data.
    all_tokens=generate_tokens(max_r)
    with tempfile.TemporaryDirectory(prefix='runcap_threshold_') as td:
        td=Path(td)
        for page_size,payload_bytes in configs:
            X=max_local_index_payload(page_size)
            rstar=predicted_threshold(page_size,payload_bytes)
            tokens=all_tokens[:rstar]
            tag=f'{page_size}_{payload_bytes}'
            before=measure(tokens[:-1],page_size,payload_bytes,td/f'{tag}_before.sqlite')
            at=measure(tokens,page_size,payload_bytes,td/f'{tag}_at.sqlite')
            expected_before_key=H + ((rstar-1 + C-1)//C)
            expected_at_key=H + ((rstar + C-1)//C)
            extra=payload_bytes+RECORD_OVERHEAD
            assert before['max_record_payload']==expected_before_key+extra
            assert at['max_record_payload']==expected_at_key+extra
            assert before['max_record_payload']==X
            assert at['max_record_payload']==X+1
            assert before['overflow_pages']==0
            assert at['overflow_pages']>=1
            row={'page_size':page_size,'fixed_payload_bytes':payload_bytes,'max_local_payload':X,
                 'predicted_first_overflow_r':rstar,'before_r':rstar-1,
                 'before_max_record_payload':before['max_record_payload'],'before_overflow_pages':before['overflow_pages'],
                 'at_r':rstar,'at_max_record_payload':at['max_record_payload'],'at_overflow_pages':at['overflow_pages']}
            rows.append(row); print(row,flush=True)
    sens=[r for r in rows if r['page_size']==4096]
    sens.sort(key=lambda r:r['fixed_payload_bytes'])
    assert [r['predicted_first_overflow_r'] for r in sens]==[4981,4901,4821,4741]
    OUT.write_text(json.dumps({'sqlite_version':sqlite3.sqlite_version,'rows':rows,
                               'payload_sensitivity_4k':sens},indent=2))
    print('PASS: seven distinct predicted first-overflow thresholds observed exactly; wrote',OUT)

if __name__=='__main__': main()
