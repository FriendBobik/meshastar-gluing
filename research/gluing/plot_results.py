from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;s=json.loads((p/'results/confirmation_summary.json').read_text());names=list(s['by_map']);names.sort()
fig,ax=plt.subplots(figsize=(8,4.4));ys=list(range(len(names)))
for j,session in enumerate(['1','2']):
 ratios=[]
 for name in names:
  rows=[x for x in s['tasks'] if x['map']==name]
  # Per-map session ratios need the per-task session medians, not an average of ratios.
  import csv,statistics
  d=p/'results/confirm';r={v:[x for f in d.glob('s'+session+'_b*_'+v+'.csv') for x in csv.DictReader(f.open())] for v in ['baseline','glued']}
  vals={v:sum(statistics.median(float(x['cpu_ms']) for x in r[v] if x['task']==t['id']) for t in rows) for v in r}
  ratios.append(vals['baseline']/vals['glued'])
 ax.scatter(ratios,[i+(-.12 if j==0 else .12) for i in ys],s=55,label=f'Сеанс {session}',marker='o' if j==0 else 's',zorder=3)
ax.axvline(1,color='#555',linewidth=1,linestyle='--');ax.set_yticks(ys,names);ax.invert_yaxis();ax.set_xlabel('Ускорение по CPU-времени, исходная версия / склеивание');ax.grid(axis='x',alpha=.25);ax.legend(frameon=False);ax.spines[['right','top']].set_visible(False);fig.tight_layout();folder=p/'figures';folder.mkdir(exist_ok=True);fig.savefig(folder/'sessions.png',dpi=190);fig.savefig(folder/'sessions.svg')
