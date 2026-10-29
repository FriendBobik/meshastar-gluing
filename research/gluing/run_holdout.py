from pathlib import Path
import subprocess,csv,json,time
p=Path(__file__).resolve().parent;root=p.parents[1];out=p/'results/holdout';out.mkdir(parents=True,exist_ok=True)
for v in ['glued','previous','zero_chain','baseline']:
 file=out/(v+'.csv');log=out/(v+'.log');start=time.time()
 with file.open('w') as o,log.open('w') as e:r=subprocess.run([str(p/'bin'/v),str(p/'holdout.tsv'),'3','1','20261101'],cwd=root,stdout=o,stderr=e,timeout=600)
 if r.returncode:raise RuntimeError(log.read_text()[-3000:])
 print(v,'holdout done',round(time.time()-start,1),'s',flush=True)
base=list(csv.DictReader((out/'baseline.csv').open()));new=list(csv.DictReader((out/'glued.csv').open()));reference={(r['task'],r['round']):r for r in base};bad=[]
for r in new:
 q=reference[(r['task'],r['round'])]
 if r['valid']!='1' or r['found']!=q['found'] or (r['found']=='1' and abs(float(r['path_cost'])-float(q['path_cost']))>max(.002,1e-5*float(q['path_cost']))):bad.append((r['task'],q['path_cost'],r['path_cost']))
if bad:raise RuntimeError(bad)
import statistics
by={}
for task in sorted(set(r['task'] for r in base)):
 aa=statistics.median(float(r['cpu_ms']) for r in base if r['task']==task);bb=statistics.median(float(r['cpu_ms']) for r in new if r['task']==task);by[task]={'baseline_cpu_ms':aa,'glued_cpu_ms':bb,'speedup':aa/bb}
a=sum(v['baseline_cpu_ms'] for v in by.values());b=sum(v['glued_cpu_ms'] for v in by.values())
result={'tasks':len(by),'repeats':3,'all_costs_match':True,'all_paths_valid':True,'baseline_sum_median_cpu_ms':a,'glued_sum_median_cpu_ms':b,'speedup':a/b,'reduction_pct':100*(1-b/a),'per_task':by}
(out/'summary.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='per_task'},flush=True)

for variant in ['previous','zero_chain']:
 other=list(csv.DictReader((out/(variant+'.csv')).open()))
 for r in other:
  q=reference[(r['task'],r['round'])]
  assert r['valid']=='1' and r['found']==q['found']
  assert r['found']=='0' or abs(float(r['path_cost'])-float(q['path_cost']))<=max(.002,1e-5*float(q['path_cost']))
 med={t:statistics.median(float(r['cpu_ms']) for r in other if r['task']==t) for t in by}
 if 'ablations' not in result:result['ablations']={}
 result['ablations'][variant]={'sum_median_cpu_ms':sum(med.values()),'speedup':sum(x['baseline_cpu_ms'] for x in by.values())/sum(med.values()),'all_costs_match':True,'all_paths_valid':True}
(out/'summary.json').write_text(json.dumps(result,indent=2))
print('Ablations',result.get('ablations'),flush=True)
