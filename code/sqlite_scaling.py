"""Controlled SQLite scaling experiment for the canonical monotone interior run.

Creates a fresh WITHOUT ROWID database for each (scheme, r) pair and stores
all r generated keys plus a fixed 16-byte payload.  The experiment is a
systems-level validation of the paper's cumulative-storage theorem; exact file
sizes remain SQLite-version/page-layout dependent and are treated descriptively.
"""
from __future__ import annotations
from pathlib import Path
import json, sqlite3, tempfile
import cfkey as ck
import orderkeys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'sqlite_scaling.json'
SIZES = [250, 500, 1000, 2000, 4000, 4500, 4750, 4900, 4901, 5000, 5100, 5250, 5500, 6000, 7000, 8000, 9000, 10000]

class FI62:
    name='FI-62'
    def alloc(self,a,b): return orderkeys.generate_key_between(a,b,orderkeys.DIGITS)
    def token(self,k): return k.encode('latin1')

class SRI:
    name='Farey-SRI'
    def alloc(self,a,b): return ck.simplest_between(a,b)
    def token(self,k): return ck.encode(k)


def generate_tokens(scheme, r):
    lo=scheme.alloc(None,None)
    hi=scheme.alloc(lo,None)
    a=lo
    toks=[]
    for _ in range(r):
        a=scheme.alloc(a,hi)
        toks.append(scheme.token(a))
    assert toks==sorted(toks)
    return toks


def db_measure(tokens: list[bytes], path: Path):
    if path.exists(): path.unlink()
    con=sqlite3.connect(path)
    con.execute('PRAGMA page_size=4096')
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('PRAGMA temp_store=MEMORY')
    con.execute('CREATE TABLE items(k BLOB PRIMARY KEY, payload BLOB NOT NULL) WITHOUT ROWID')
    payload=b'x'*16
    con.executemany('INSERT INTO items(k,payload) VALUES (?,?)', ((sqlite3.Binary(k),payload) for k in tokens))
    con.commit()
    page_count=con.execute('PRAGMA page_count').fetchone()[0]
    page_size=con.execute('PRAGMA page_size').fetchone()[0]
    freelist=con.execute('PRAGMA freelist_count').fetchone()[0]
    page_rows=con.execute("SELECT pagetype, count(*), max(mx_payload) FROM dbstat WHERE name='items' GROUP BY pagetype").fetchall()
    pages_by_type={kind: count for kind,count,_ in page_rows}
    max_record_payload=max((mx or 0) for _,_,mx in page_rows)
    con.close()
    return {'db_bytes': path.stat().st_size, 'page_count': page_count,
            'page_size': page_size, 'freelist_count': freelist,
            'pages_by_type': pages_by_type, 'max_record_payload': max_record_payload}


def main():
    rows=[]
    with tempfile.TemporaryDirectory(prefix='fareykey_sqlite_scaling_') as td:
        td=Path(td)
        for scheme in (FI62(), SRI()):
            for r in SIZES:
                toks=generate_tokens(scheme,r)
                m=db_measure(toks, td/f'{scheme.name}_{r}.sqlite')
                row={'scheme':scheme.name,'r':r,
                     'total_key_bytes':sum(map(len,toks)),
                     'mean_key_bytes':sum(map(len,toks))/r,
                     'max_key_bytes':max(map(len,toks)), **m}
                rows.append(row)
                print(row, flush=True)
    OUT.write_text(json.dumps({'rows':rows,'sqlite_version':sqlite3.sqlite_version},indent=2))
    print('wrote',OUT)

if __name__=='__main__': main()
