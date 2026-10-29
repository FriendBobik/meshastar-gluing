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
