from pathlib import Path
import json,hashlib,zipfile,stat
p=Path(__file__).resolve().parent;root=p.parents[1];destination=root/'dist/gluing_research_20261029.zip';destination.parent.mkdir(exist_ok=True);prefix='MeshAStar_gluing';files={}
# Pure baseline sources also appear at project root; generated experiment sources remain inspectable.
for folder in ['include','src']:
 for f in (p/'source_snapshot'/folder).rglob('*'):
  if f.is_file():files[str(f.relative_to(p/'source_snapshot'))]=f
files['Makefile']=p/'source_snapshot/Makefile'
files['LICENSE.txt']=root/'LICENSE.txt'
maps={r.split('\t')[1] for file in ['core.tsv','holdout.tsv','manual.tsv'] for r in (p/file).read_text().splitlines()[1:]}
for name in maps:
 for ext in ['.map','.map.scen']:
  f=root/'maps'/(name+ext)
  if f.exists():files[str(f.relative_to(root))]=f
for pattern in ['*.map','*.map.scen']:
 for f in (root/'maps').glob(pattern):files[str(f.relative_to(root))]=f
for f in (root/'data').glob('*.txt'):files[str(f.relative_to(root))]=f
for f in p.rglob('*'):
 if not f.is_file() or '__pycache__' in f.parts or f.suffix in ['.pyc','.aux','.log'] and 'results' not in f.parts:continue
 if f.name in ['.DS_Store','package_files_sha256.json']:continue
 files[str(f.relative_to(root))]=f
manifest={name:hashlib.sha256(f.read_bytes()).hexdigest() for name,f in files.items()}
(p/'package_files_sha256.json').write_text(json.dumps(manifest,indent=2))
files['research/gluing/package_files_sha256.json']=p/'package_files_sha256.json'
readme='''Склеивание цепочек MeshA*: исследование 29 октября 2026 года\n\nОтчёт: research/gluing/report/main.pdf\nTeX: research/gluing/report/main.tex\nПодробные команды и ограничения: research/gluing/REPRODUCE.txt\nИтоговые результаты: research/gluing/results/confirmation_summary.json\nВходные задачи: research/gluing/core.tsv, holdout.tsv, manual.tsv\nПатч обычного CLI: research/gluing/gluing.patch\n\nВ архиве есть исходники и готовые Apple M1/macOS-бинарники. Для Linux пересоберите:\n  CXX=c++ bash research/gluing/build.sh\nНа macOS:\n  bash research/gluing/build.sh\n\nОсновная серия (около 15 минут на этой машине):\n  caffeinate -i python3 research/gluing/run_confirm.py\n  python3 research/gluing/analyze.py\nВ Linux уберите caffeinate -i, программа проверяет sched_setaffinity сама.\nПовторный запуск перезаписывает results/confirm, поэтому сохраните исходный архив.\n\nОбычный CLI:\n  bash research/gluing/build_cli.sh\n  research/gluing/bin/mesh_astar_glued --help\n\nДля исследования не нужен Git или доступ к сети. Файлы source_snapshot фиксируют базовый код.\nМатрица использует 24 задачи и 20 измерений каждого варианта, ещё 24 задачи на других картах проверены в трёх повторах.\nНа M1 жёсткая привязка к физическому ядру не была доступна. Все поиски однопоточные, основной показатель CPU-время потока.\n'''
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,f in sorted(files.items()):z.write(f,prefix+'/'+name)
 z.writestr(prefix+'/START_HERE.txt',readme)
sha=hashlib.sha256(destination.read_bytes()).hexdigest();destination.with_suffix('.zip.sha256').write_text(sha+'  '+destination.name+'\n')
print(destination,'bytes',destination.stat().st_size,'files',len(files)+1,'sha256',sha)
