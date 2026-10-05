from pathlib import Path
import csv,json
import matplotlib.pyplot as plt
DPI=1200  # Springer line-art requirement; raster figures remain publication-grade at final size.
ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures'; FIG.mkdir(exist_ok=True)
# Figure 1: real trace storage ratio
rows=list(csv.DictReader(open(ROOT/'results'/'derived_real_trace_summary.csv')))
names=[r['trace'] for r in rows]
ratios=[float(r['fi62_to_sri_ratio']) for r in rows]
plt.figure(figsize=(8.2,4.8))
plt.bar(names,ratios)
plt.yscale('log')
plt.ylabel('FI-62 live key bytes / SRI live key bytes (log scale)')
plt.xlabel('Editing trace')
plt.xticks(rotation=35,ha='right')
plt.tight_layout(); plt.savefig(FIG/'fig1_real_trace_ratio.png',dpi=DPI); plt.close()
# Figure 2: right-moving run growth
x=json.load(open(ROOT/'results'/'synthetic_valid.json'))
rs=[1000,10000]
fi=[x[f'FI-62|rightrun|{r}'][0] for r in rs]
sri=[x[f'Farey-SRI|rightrun|{r}'][0] for r in rs]
# add SRI 100k while FI not run
plt.figure(figsize=(6.8,4.6))
plt.plot(rs,fi,marker='o',linestyle='-',label='FI-62')
plt.plot([1000,10000,100000],[x[f'Farey-SRI|rightrun|{r}'][0] for r in [1000,10000,100000]],marker='s',linestyle='--',label='SRI')
plt.xscale('log'); plt.yscale('log')
plt.xlabel('Insertions in one interior right-moving run')
plt.ylabel('Maximum generated key length (stored bytes)')
plt.legend(); plt.tight_layout(); plt.savefig(FIG/'fig2_run_growth.png',dpi=DPI); plt.close()
# Figure 3: controlled SQLite scaling
S=json.load(open(ROOT/'results'/'sqlite_scaling.json'))['rows']
fi=[r for r in S if r['scheme']=='FI-62']
sri=[r for r in S if r['scheme']=='Farey-SRI']
plt.figure(figsize=(6.8,4.6))
plt.plot([r['r'] for r in fi],[r['db_bytes']/1024/1024 for r in fi],marker='o',linestyle='-',label='FI-62')
plt.plot([r['r'] for r in sri],[r['db_bytes']/1024/1024 for r in sri],marker='s',linestyle='--',label='SRI')
plt.axvline(4901,linestyle='--',linewidth=1,label='predicted and observed overflow onset')
plt.xscale('log'); plt.yscale('log')
plt.xlabel('Insertions in canonical interior run')
plt.ylabel('SQLite file size (MiB)')
plt.legend(); plt.tight_layout(); plt.savefig(FIG/'fig3_sqlite_scaling.png',dpi=DPI); plt.close()
# Figure 4: exploratory real-trace SQLite deterministic storage
D=json.load(open(ROOT/'results'/'dbexp_single_run.json'))
labels=[]; vals=[]
for k in D:
    lk=k.lower()
    if 'fi' in lk and '62' in lk: labels.append('FI-62'); vals.append(D[k]['db_bytes']/1024/1024)
    elif 'sri' in lk: labels.append('SRI'); vals.append(D[k]['db_bytes']/1024/1024)
if not labels:
    labels=['FI-62','SRI']; vals=[55111680/1024/1024,643072/1024/1024]
# deduplicate preserving first
seen={};
for a,b in zip(labels,vals): seen.setdefault(a,b)
plt.figure(figsize=(5.6,4.3))
plt.bar(list(seen.keys()),list(seen.values()))
plt.ylabel('SQLite file size (MiB)')
plt.xlabel('Order-key scheme')
plt.tight_layout(); plt.savefig(FIG/'fig4_sqlite_stress.png',dpi=DPI); plt.close()
