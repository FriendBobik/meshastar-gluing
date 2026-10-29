#!/bin/bash
set -eu
cd "$(dirname "$0")"
compiler=${CXX:-/usr/bin/clang++}
if [[ ! -x "$compiler" ]]; then compiler=${CXX:-c++}; fi
python3 prepare_cli.py
sources=(generated_cli/src/KC_heap.cpp generated_cli/src/KC_searching.cpp generated_cli/src/KC_structs.cpp generated_cli/src/KC_search_params.cpp generated_cli/src/KC_algorithms.cpp generated_cli/src/KC_testing.cpp generated_cli/src/gluing_state.cpp)
for spec in mesh_astar_baseline:0 mesh_astar_glued:3; do
 name=${spec%:*}; mode=${spec#*:}
 "$compiler" -std=c++17 -O3 -DGLUING_MODE=$mode -I generated_cli/include -I . "${sources[@]}" -o bin/$name
done
