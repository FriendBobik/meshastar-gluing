#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
compiler=${CXX:-/usr/bin/clang++}
if [[ ! -x "$compiler" ]]; then compiler=${CXX:-c++}; fi
python3 research/gluing/prepare.py
mkdir -p research/gluing/bin
"$compiler" -std=c++17 -O2 -I research/gluing/generated/include -I research/gluing \
  research/gluing/generated/src/KC_heap.cpp \
  research/gluing/generated/src/KC_structs.cpp \
  research/gluing/generated/src/KC_searching.cpp \
  research/gluing/test_macro.cpp -o research/gluing/bin/test_macro
research/gluing/bin/test_macro
python3 research/gluing/verify_data.py
# Леммы 1 и 2 на таблицах переходов (обоснование склейки и компактного CLOSED)
python3 research/gluing/verify_tree.py
# Все варианты стенда дают те же стоимости, что baseline, на 20 ручных случаях
if [[ ! -x research/gluing/bin/glued_closed ]]; then bash research/gluing/build.sh; fi
python3 research/gluing/check_variants.py manual.tsv
# Обычный CLI (с компактным CLOSED по умолчанию): пример с обходом стены
if [[ -x ./mesh_astar ]]; then
  mkdir -p res/test
  ./mesh_astar --mode single --map maps/gluing_detour.map --prim data/base_control_set.txt --mesh data/base_mesh_info.txt \
    --start "24 12 0" --goal "24 68 0" --weight 1 --out-prefix res/test/ > /dev/null
  grep -q "Path Cost: 74.4033" res/test/result_MeshAstar.txt && grep -q "Path Cost: 74.4033" res/test/result_LBAstar.txt \
    || { echo "FAIL: CLI, стоимость пути"; exit 1; }
  echo "PASS: CLI на gluing_detour, стоимость 74.4033 совпадает с LBA*"
fi

