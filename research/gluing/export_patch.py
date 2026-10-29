from pathlib import Path
import difflib
p=Path(__file__).resolve().parent;root=p.parents[1];patch=[]
for f in (p/'generated_cli/src').glob('*.cpp'):
 rel=Path('src')/f.name;old=p/'source_snapshot'/rel
 a=old.read_text().splitlines(True) if old.exists() else [];b=f.read_text().splitlines(True)
 patch+=difflib.unified_diff(a,b,fromfile='a/'+str(rel) if old.exists() else '/dev/null',tofile='b/'+str(rel))
for name in ['macro_paths.hpp','gluing_stats.hpp']:
 s=(p/name).read_text()
 if name=='macro_paths.hpp':s=s.replace('#pragma once','#pragma once\n#ifndef GLUING_MODE\n#define GLUING_MODE 3\n#endif',1)
 patch+=difflib.unified_diff([],s.splitlines(True),fromfile='/dev/null',tofile='b/include/'+name)
a=(p/'source_snapshot/Makefile').read_text();b=a.replace('obj/KC_algorithms.o','obj/KC_algorithms.o obj/gluing_state.o').replace('include/KC_algorithms.hpp','include/KC_algorithms.hpp include/macro_paths.hpp include/gluing_stats.hpp')
patch+=difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/Makefile',tofile='b/Makefile')
(p/'gluing.patch').write_text(''.join(patch));print(p/'gluing.patch')
