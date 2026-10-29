from pathlib import Path
import subprocess,csv,json,time
p=Path(__file__).resolve().parent;root=p.parents[1];out=p/'results/pilot';out.mkdir(parents=True,exist_ok=True)
def read(f):
 with f.open() as r:return list(csv.DictReader(r))
def compare(rows,base):
 b={r['task']:r for r in base};bad=[]
 for r in rows:
  q=b[r['task']]
  if r['valid']!='1' or r['found']!=q['found'] or (r['found']=='1' and abs(float(r['path_cost'])-float(q['path_cost']))>max(.002,1e-5*float(q['path_cost']))):bad.append((r['task'],q['found'],r['found'],q['path_cost'],r['path_cost']))
 return bad
summary={}
for suite in ['manual','core']:
 base=None
 for variant in ['baseline','previous','zero_chain','glued']:
  counts='_counts' if suite=='core' else ''
  file=out/f'{suite}_{variant}.csv';log=file.with_suffix('.log');start=time.time()
  with file.open('w') as f,log.open('w') as e:r=subprocess.run([str(p/'bin'/(variant+counts)),str(p/(suite+'.tsv')),'1','0','42'],cwd=root,stdout=f,stderr=e,timeout=240)
  if r.returncode:raise RuntimeError((suite,variant,log.read_text()[-2000:]))
  rows=read(file)
  if variant=='baseline':base=rows
  bad=compare(rows,base)
  countsums={k:sum(int(x[k]) for x in rows) for k in ['push','pop','cell_checks','heuristic_calls','final_entries','glued_cells','macro_edges']}
  item={'suite':suite,'variant':variant,'rows':len(rows),'bad':bad,'cpu_ms':sum(float(x['cpu_ms']) for x in rows),'elapsed_s':time.time()-start,'counters':countsums}
  print(item,flush=True);summary[suite+'_'+variant]=item
  (out/'summary.json').write_text(json.dumps(summary,indent=2))
  if bad:raise RuntimeError('Outcome mismatch')
