#!/bin/bash
set -eu
cd "$(dirname "$0")"
compiler=${CXX:-/usr/bin/clang++}
if [[ ! -x "$compiler" ]]; then compiler=${CXX:-c++}; fi
python3 prepare.py
mkdir -p bin results
sources=(generated/src/KC_heap.cpp generated/src/KC_searching.cpp generated/src/KC_structs.cpp generated/src/KC_search_params.cpp bench.cpp)
for spec in baseline:0 previous:1 zero_chain:2 glued:3; do
 name=${spec%:*}
 mode=${spec#*:}
 "$compiler" -std=c++17 -O3 -DGLUING_MODE=$mode -I generated/include -I . $sources -o bin/$name
 "$compiler" -std=c++17 -O3 -DGLUING_MODE=$mode -DGLUING_COUNTERS -I generated/include -I . $sources -o bin/${name}_counts
done
