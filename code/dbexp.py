"""SQLite storage/latency experiment. Timing outputs are descriptive single-machine measurements.
Use --repetitions > 1 for new inferential timing work; the manuscript reports the
archived single-run results only as descriptive evidence.
"""
from pathlib import Path
import argparse,os,random,sqlite3,time,json,tempfile,platform,sys

def bench(keys,payload=16,seed=0):
    rnd=random.Random(seed)
    fd,path=tempfile.mkstemp(prefix='fareykey_',suffix='.db'); os.close(fd); os.unlink(path)
    con=sqlite3.connect(path); con.execute('PRAGMA journal_mode=OFF')
    page_size=con.execute('PRAGMA page_size').fetchone()[0]
    auto_vacuum=con.execute('PRAGMA auto_vacuum').fetchone()[0]
    con.execute('CREATE TABLE items (k BLOB PRIMARY KEY, v BLOB) WITHOUT ROWID')
    rows=[(sqlite3.Binary(k),b'x'*payload) for k in keys]; rnd.shuffle(rows)
    t=time.perf_counter(); con.executemany('INSERT INTO items VALUES (?,?)',rows); con.commit(); ins=time.perf_counter()-t
    t=time.perf_counter(); n=sum(1 for _ in con.execute('SELECT k FROM items ORDER BY k')); scan=time.perf_counter()-t
    probes=[keys[rnd.randrange(len(keys))] for _ in range(2000)]
    t=time.perf_counter()
    for k in probes: con.execute('SELECT v FROM items WHERE k=?',(sqlite3.Binary(k),)).fetchone()
    point=time.perf_counter()-t
    ranges=[]
    for _ in range(200):
        i=rnd.randrange(max(1,len(keys)-100)); ranges.append((keys[i],keys[min(i+100,len(keys)-1)]))
    t=time.perf_counter()
    for lo,hi in ranges: con.execute('SELECT count(*) FROM items WHERE k>=? AND k<=?',(sqlite3.Binary(lo),sqlite3.Binary(hi))).fetchone()
    ran=time.perf_counter()-t
    con.close(); size=os.path.getsize(path); os.remove(path)
    return {'n':len(keys),'key_bytes':sum(map(len,keys)),'db_bytes':size,'insert_s':ins,'scan_s':scan,'point2000_s':point,'range200_s':ran,'scanned':n,
            'environment':{'python':sys.version.split()[0],'sqlite':sqlite3.sqlite_version,'os':platform.platform(),'page_size':page_size,'journal_mode':'OFF','auto_vacuum':auto_vacuum,'table_layout':'WITHOUT ROWID','payload_bytes':payload}}
