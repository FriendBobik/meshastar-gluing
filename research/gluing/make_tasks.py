from pathlib import Path
import random,csv,json,hashlib
p=Path(__file__).resolve().parent;root=p.parents[1];rng=random.Random(20261029)
columns=['id','map','control','si','sj','st','fi','fj','ft','weight']
core_maps=['Moscow_0_512','Milan_1_256','Berlin_2_256','AR0304SR','Labyrinth','WheelofWar']
extra_maps=['AR0307SR','AR0700SR','ht_0_hightown','w_woundedcoast']
def sample(m,bands,cs,prefix):
 src=list(csv.reader((root/'maps'/f'{m}.map.scen').read_text().splitlines()[1:],delimiter='\t'))
 out=[]
 for k,(lo,hi) in enumerate(bands):
  eligible=[r for r in src if lo<=float(r[8])<hi]
  if not eligible:raise ValueError((m,lo,hi))
  r=rng.choice(eligible);sx,sy,fx,fy=map(int,r[4:8]);st=rng.randrange(16);ft=rng.randrange(16)
  out.append([f'{prefix}_{m}_{cs}_{k}',m,cs,sy,sx,st,fy,fx,ft,1])
 return out
core=[];holdout=[]
for m in core_maps:core+=sample(m,[(40,80),(80,160),(160,320)],'base','core')
for m in core_maps[:3]:core+=sample(m,[(40,100),(100,200)],'add','core')
for m in extra_maps:
 for cs in ['base','add']:holdout+=sample(m,[(40,80),(80,160),(160,320)],cs,'holdout')
def write(name,rows):
 f=p/(name+'.tsv')
 with f.open('w') as o:w=csv.writer(o,delimiter='\t',lineterminator='\n');w.writerow(columns);w.writerows(rows)
write('core',core);write('holdout',holdout)
# Separate hand-checkable maps: empty field, wall detour and disconnected target.
for name,wall in [('gluing_empty',False),('gluing_detour',True),('gluing_blocked',True)]:
 field=[['.']*80 for _ in range(64)]
 if wall:
  for i in range(64):
   if name=='gluing_detour' and 48<=i<=55:continue
   field[i][40]='@'
 with (root/'maps'/f'{name}.map').open('w') as o:o.write('type octile\nheight 64\nwidth 80\nmap\n'+'\n'.join(''.join(r) for r in field)+'\n')
manual=[]
for name in ['gluing_empty','gluing_detour','gluing_blocked']:
 for cs in ['base','add']:
  for k,(st,ft) in enumerate([(0,0),(4,12),(2,6)]):manual.append([f'{name}_{cs}_{k}',name,cs,24,12,st,24,68,ft,1])
for cs in ['base','add']:manual.append([f'start_goal_{cs}','gluing_empty',cs,24,24,0,24,24,0,1])
write('manual',manual)
# Counterfactually disable the baseline's unique-endpoint jump for ablation only.
meta={'seed':20261029,'core_count':len(core),'holdout_count':len(holdout),'manual_count':len(manual),'selection':'uniform random per prespecified grid-distance band; no timing-based selection','files':{}}
for f in [p/'core.tsv',p/'holdout.tsv',p/'manual.tsv']+list((root/'maps').glob('*.map'))+list((root/'data').glob('*.txt')):
 meta['files'][str(f.relative_to(root))]=hashlib.sha256(f.read_bytes()).hexdigest()
(p/'data_manifest.json').write_text(json.dumps(meta,indent=2))
print('core',len(core),'holdout',len(holdout),'manual',len(manual))
