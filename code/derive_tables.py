from pathlib import Path
import csv,json,math
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'/'real_traces'
OUT=ROOT/'results'/'derived_real_trace_summary.csv'
TRACES=[
 ('friendsforever_flat','friendsforever'),('clownschool_flat','clownschool'),
 ('sveltecomponent','sveltecomponent'),('json-crdt-blog-post','json-crdt-blog'),
 ('json-crdt-patch','json-crdt-patch'),('seph-blog1','seph-blog1'),
 ('rustcode','rustcode'),('automerge-paper','automerge-paper')]
rows=[]
for stem,label in TRACES:
    f=json.load(open(R/f'{stem}__FI-62.json'))['summary']
    s=json.load(open(R/f'{stem}__Farey-SRI.json'))['summary']
    rows.append({
      'trace':label,'insertions':f['n_ins'],'deletions':f['n_del'],'live_items':f['n_live'],
      'fi62_live_bytes':f['live_bytes'],'sri_live_bytes':s['live_bytes'],
      'fi62_to_sri_ratio':f['live_bytes']/s['live_bytes'],
      'fi62_live_mean_bytes':f['live_bytes']/f['n_live'],
      'sri_live_mean_bytes':s['live_bytes']/s['n_live'],
      'fi62_max_generated_bytes':math.ceil(f['gen_max_bits']/8),
      'sri_max_generated_bytes':math.ceil(s['gen_max_bits']/8),
      'fi62_live_max_bytes':math.ceil(f['live_max_bits']/8),
      'sri_live_max_bytes':math.ceil(s['live_max_bits']/8),
    })
with open(OUT,'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(OUT)
