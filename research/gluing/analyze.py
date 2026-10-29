from pathlib import Path
import csv,json,math,statistics,random,collections,hashlib
p=Path(__file__).resolve().parent;out=p/'results';conf=out/'confirm'
manifest=json.loads((conf/'manifest.json').read_text())
meta={x['id']:x for x in csv.DictReader((p/'core.tsv').open(),delimiter='\t')}
records=[]
for run in manifest['runs']:
 for row in csv.DictReader((conf/run['file']).open()):
  r=dict(row);r.update(session=run['session'],block=run['block'],variant=run['variant']);r['cpu_ms']=float(r['cpu_ms']);r['wall_ms']=float(r['wall_ms']);r['call_cpu_ms']=float(r['init_cpu_ms'])+r['cpu_ms']+float(r['cleanup_cpu_ms']);records.append(r)
by=collections.defaultdict(list)
for r in records:by[(r['task'],r['variant'],r['session'])].append(r)
per_task=[];mismatch=[]
for task in meta:
 pooled={v:[r for r in records if r['task']==task and r['variant']==v] for v in ['baseline','glued']}
 if any(not a for a in pooled.values()):continue
 a=pooled['baseline'];b=pooled['glued']
 aq=a[0];bq=b[0]
 valid=all(r['valid']=='1' for r in a+b)
 cost_match=aq['found']==bq['found'] and (aq['found']=='0' or abs(float(aq['path_cost'])-float(bq['path_cost']))<=max(.002,1e-5*float(aq['path_cost'])))
 if not valid or not cost_match:mismatch.append(task)
 med={v:{k:statistics.median(r[k] for r in data) for k in ['cpu_ms','wall_ms','call_cpu_ms']} for v,data in pooled.items()}
 row={'id':task,'map':meta[task]['map'],'control':meta[task]['control'],'found':aq['found']=='1','baseline_cpu_ms':med['baseline']['cpu_ms'],'glued_cpu_ms':med['glued']['cpu_ms'],'speedup':med['baseline']['cpu_ms']/med['glued']['cpu_ms'],'baseline_wall_ms':med['baseline']['wall_ms'],'glued_wall_ms':med['glued']['wall_ms'],'baseline_call_cpu_ms':med['baseline']['call_cpu_ms'],'glued_call_cpu_ms':med['glued']['call_cpu_ms'],'same_path':aq['path_hash']==bq['path_hash'],'valid':valid,'cost_match':cost_match,'reps':{v:len(x) for v,x in pooled.items()},'session_speedups':{}}
 for sess in [1,2]:
  aa=by.get((task,'baseline',sess));bb=by.get((task,'glued',sess))
  if aa and bb:row['session_speedups'][str(sess)]=statistics.median(r['cpu_ms'] for r in aa)/statistics.median(r['cpu_ms'] for r in bb)
 row['relative_mad']={v:statistics.median(abs(r['cpu_ms']-med[v]['cpu_ms']) for r in data)/med[v]['cpu_ms'] for v,data in pooled.items()}
 per_task.append(row)
assert not mismatch,mismatch

def aggregate(rows,ci=True):
 if not rows:return {}
 a=sum(x['baseline_cpu_ms'] for x in rows);b=sum(x['glued_cpu_ms'] for x in rows)
 d={'tasks':len(rows),'baseline_sum_median_cpu_ms':a,'glued_sum_median_cpu_ms':b,'cpu_speedup':a/b,'cpu_time_reduction_pct':100*(1-b/a),'geomean_speedup':math.exp(statistics.mean(math.log(x['speedup']) for x in rows)),'wins':sum(x['speedup']>1 for x in rows),'baseline_sum_median_wall_ms':sum(x['baseline_wall_ms'] for x in rows),'glued_sum_median_wall_ms':sum(x['glued_wall_ms'] for x in rows),'call_speedup':sum(x['baseline_call_cpu_ms'] for x in rows)/sum(x['glued_call_cpu_ms'] for x in rows)}
 if ci:
  rng=random.Random(20261029);groups=collections.defaultdict(list)
  for r in rows:groups[r['map']].append(r)
  names=list(groups);ratios=[];gmean=[]
  for _ in range(10000):
   sample=[r for name in rng.choices(names,k=len(names)) for r in groups[name]]
   ratios.append(sum(x['baseline_cpu_ms'] for x in sample)/sum(x['glued_cpu_ms'] for x in sample))
   gmean.append(math.exp(statistics.mean(math.log(x['speedup']) for x in sample)))
  def interval(values):values.sort();return [values[249],values[9749]]
  d['map_cluster_bootstrap_speedup_95']=interval(ratios);d['map_cluster_bootstrap_geomean_95']=interval(gmean)
 return d
result={'completed_runs':len(manifest['runs']),'measured_searches':len(records),'validation':{'all_costs_match':True,'all_paths_valid':True,'same_path_tasks':sum(x['same_path'] for x in per_task)},'all_tasks':aggregate(per_task),'solved':aggregate([r for r in per_task if r['found']]),'unsolved':aggregate([r for r in per_task if not r['found']]),'nontrivial_geomean':aggregate([r for r in per_task if r['baseline_cpu_ms']>=1]),'by_map':{},'by_control':{},'sessions':{},'tasks':per_task}
for field,key in [('map','by_map'),('control','by_control')]:
 for val in sorted(set(r[field] for r in per_task)):result[key][val]=aggregate([r for r in per_task if r[field]==val],False)
for session in [1,2]:
 rows=[]
 for t in per_task:
  a=by.get((t['id'],'baseline',session));b=by.get((t['id'],'glued',session))
  if a and b:
   x=dict(t);x['baseline_cpu_ms']=statistics.median(r['cpu_ms'] for r in a);x['glued_cpu_ms']=statistics.median(r['cpu_ms'] for r in b);x['speedup']=x['baseline_cpu_ms']/x['glued_cpu_ms'];x['baseline_wall_ms']=statistics.median(r['wall_ms'] for r in a);x['glued_wall_ms']=statistics.median(r['wall_ms'] for r in b);x['baseline_call_cpu_ms']=statistics.median(r['call_cpu_ms'] for r in a);x['glued_call_cpu_ms']=statistics.median(r['call_cpu_ms'] for r in b);rows.append(x)
 if rows:result['sessions'][str(session)]=aggregate(rows,False)
(out/'confirmation_summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['tasks','by_control','by_map']},indent=2))
