from pathlib import Path
import shutil
p=Path(__file__).resolve().parent;dst=p/'generated_cli'
for folder in ['include','src']:shutil.copytree(p/'generated'/folder,dst/folder,dirs_exist_ok=True)
f=dst/'src/KC_structs.cpp';s=f.read_text();s='#include "macro_paths.hpp"\n'+s
s=s.replace('    cout << "Mesh Configurations loaded successfully', '#if GLUING_MODE > 0\n    g_macro=MacroPaths{};\n    g_macro.build(*this);\n#endif\n    cout << "Mesh Configurations loaded successfully')
f.write_text(s)
(dst/'src/gluing_state.cpp').write_text('#include "gluing_stats.hpp"\n#include "macro_paths.hpp"\nGluingStats g_stats;\nMacroPaths g_macro;\n')
print(dst)
