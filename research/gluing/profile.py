from pathlib import Path
import subprocess,csv,json
p=Path(__file__).resolve().parent;root=p.parents[1];out=p/'results/profile';out.mkdir(parents=True,exist_ok=True);summary={}
for v in ['baseline','previous','zero_chain','glued']:
 f=out/(v+'.csv');log=out/(v+'.log')
 with f.open('w') as o,log.open('w') as e:r=subprocess.run([str(p/'bin'/(v+'_counts')),str(p/'core.tsv'),'1','0','42'],cwd=root,stdout=o,stderr=e,timeout=240)
 if r.returncode:raise RuntimeError(log.read_text()[-3000:])
 rows=list(csv.DictReader(f.open()));assert len(rows)==24 and all(x['valid']=='1' for x in rows)
 counts={k:sum(int(x[k]) for x in rows) for k in ['push','pop','stale','cell_checks','primitive_checks','prune_calls','heuristic_calls','final_entries','glued_cells','macro_edges']}
 summary[v]={'tasks':24,'counters':counts,'cpu_time_not_used_for_performance':True};print(v,counts,flush=True)
(out/'summary.json').write_text(json.dumps(summary,indent=2))
