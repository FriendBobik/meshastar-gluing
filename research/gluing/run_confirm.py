from pathlib import Path
import subprocess,csv,json,time,hashlib,os,platform
p=Path(__file__).resolve().parent;root=p.parents[1];out=p/'results/confirm';out.mkdir(parents=True,exist_ok=True)
variants=['baseline','glued'];orders=[['baseline','glued','glued','baseline'],['glued','baseline','baseline','glued']]
manifest={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'platform':platform.platform(),'machine':platform.machine(),'cpu_model':'Apple M1' if platform.system()=='Darwin' else platform.processor(),'single_thread':True,'hard_cpu_pin':platform.system()=='Linux','affinity_probe':'KERN_NOT_SUPPORTED (46)' if platform.system()=='Darwin' else 'sched_setaffinity checked in benchmark','qos':'USER_INITIATED' if platform.system()=='Darwin' else 'default','clock':'CLOCK_THREAD_CPUTIME_ID and steady_clock','schedule':'session1 ABBA, session2 BAAB; 5 measured rounds + 1 warmup in each process','rounds_per_task_per_variant':20,'bin_sha256':{v:hashlib.sha256((p/'bin'/v).read_bytes()).hexdigest() for v in variants},'tasks_sha256':hashlib.sha256((p/'core.tsv').read_bytes()).hexdigest(),'runs':[]}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
reference={}
for session,order in enumerate(orders,1):
 for block,v in enumerate(order):
  stem=f's{session}_b{block}_{v}';f=out/(stem+'.csv');log=out/(stem+'.log');seed=20261029+session*100 # identical task permutation stream across variants within session
  cmd=[str(p/'bin'/v),str(p/'core.tsv'),'5','1',str(seed)]
  print('START',stem,time.strftime('%H:%M:%S'),flush=True);start=time.time()
  with f.open('w') as o,log.open('w') as e:r=subprocess.run(cmd,cwd=root,stdout=o,stderr=e,timeout=600)
  if r.returncode:raise RuntimeError((stem,r.returncode,log.read_text()[-3000:]))
  rows=list(csv.DictReader(f.open()));assert len(rows)==120
  mismatch=[]
  for row in rows:
   assert row['valid']=='1'
   key=(v,row['task']);signature=(row['found'],row['cost'],row['path_hash'],row['steps'],row['checked_cells'])
   if key in reference and reference[key]!=signature:mismatch.append((row['task'],reference[key],signature))
   reference[key]=signature
  if mismatch:raise RuntimeError(('non-deterministic algorithm',mismatch))
  entry={'session':session,'block':block,'variant':v,'rows':len(rows),'wall_seconds':time.time()-start,'sum_cpu_ms':sum(float(x['cpu_ms']) for x in rows),'cpu_wall_ratio':sum(float(x['cpu_ms']) for x in rows)/sum(float(x['wall_ms']) for x in rows),'file':f.name,'command':cmd,'deterministic':True}
  manifest['runs'].append(entry);(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('DONE',entry,flush=True)
print('PASS confirm',flush=True)
