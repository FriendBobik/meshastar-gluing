#include <cassert>
#include <iostream>
#include "macro_paths.hpp"
MyHEAP *HEAP=nullptr;
MacroPaths g_macro;
int main() {
 MeshInfo m;m.successors.assign(4,{});m.theta_by_initial_config.assign(4,-1);m.primitives_in_config.assign(4,{});
 m.theta_by_initial_config[0]=0;m.theta_by_initial_config[3]=1;
 m.successors[0]={{0,1,1,-1}};m.successors[1]={{0,1,2,-1}};m.successors[2]={{0,1,3,7}};
 m.primitives_in_config[1]={{1,0,2,1,7}};m.primitives_in_config[2]={{1,0,1,2,7}};
 MacroPaths a;a.build(m);assert(a.enabled);assert(a.zero[0].empty());assert(a.zero[1].size()==1);assert(a.full[1].size()==2);assert(a.full[1].back().config==3&&a.full[1].back().prim==7&&a.full[1].back().dj==2);
 // A merge invalidates the uniqueness certificate.
 m.successors[0].push_back({1,0,2,-1});MacroPaths b;b.build(m);assert(!b.enabled);m.successors[0].pop_back();
 // A changed endpoint set is not a constant-priority chain.
 m.primitives_in_config[2][0]=std::make_tuple(1,1,1,2,7);MacroPaths c;c.build(m);assert(!c.enabled);
 // Disconnected cycles are rejected rather than followed indefinitely.
 m.primitives_in_config[2][0]=std::make_tuple(1,0,1,2,7);m.successors[0].clear();m.successors[2]={{0,-1,1,-1}};MacroPaths d;d.build(m);assert(!d.enabled);
 std::cout<<"PASS: zero/full chains, initial boundaries, merge/cycle/Finals fallback\n";
}
