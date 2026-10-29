#!/bin/bash
set -eu
cd "$(dirname "$0")"
compiler=${CXX:-/usr/bin/clang++}
if [[ ! -x "$compiler" ]]; then compiler=${CXX:-c++}; fi
python3 prepare.py
mkdir -p bin results
sources=(generated/src/KC_heap.cpp generated/src/KC_searching.cpp generated/src/KC_structs.cpp generated/src/KC_search_params.cpp bench.cpp)
# имя:режим[:флаги]. glued_closed и chain_on_pop* — дополнения 29.10 (компактный CLOSED и сжатие при извлечении).
for spec in baseline:0 previous:1 zero_chain:2 glued:3 glued_closed:3:-DCOMPACT_CLOSED chain_on_pop:4 chain_on_pop_closed:4:-DCOMPACT_CLOSED; do
 IFS=: read -r name mode extra <<< "$spec"
 "$compiler" -std=c++17 -O3 -DGLUING_MODE=$mode $extra -I generated/include -I . "${sources[@]}" -o bin/$name
 "$compiler" -std=c++17 -O3 -DGLUING_MODE=$mode $extra -DGLUING_COUNTERS -I generated/include -I . "${sources[@]}" -o bin/${name}_counts
done
