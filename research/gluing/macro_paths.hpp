#pragma once
#include <set>
#include <queue>
#include <stdexcept>
#include "KC_structs.hpp"
struct MacroStep {int di,dj,config,prim;};
struct MacroPaths {
 bool enabled=false;
 std::vector<std::vector<MacroStep>> zero,full;
 // Conservative gate: unique internal predecessors and finite ancestry rooted at initial.
 void build(const MeshInfo &m) {
  size_t n=m.successors.size();zero.assign(n,{});full.assign(n,{});
  std::vector<int> degree(n,0);std::vector<bool> reached(n,false),used(n,false);std::queue<int> q;
  for(size_t c=0;c<n;c++) {
   if(m.theta_by_initial_config[c]>=0){q.push((int)c);reached[c]=true;}
   if(!m.successors[c].empty())used[c]=true;
   for(auto e:m.successors[c]) {
    int d=std::get<2>(e);if(d<0||(size_t)d>=n)return;
    used[d]=true;
    if(m.theta_by_initial_config[d]<0&&++degree[d]>1)return;
   }
  }
  while(!q.empty()) {int c=q.front();q.pop();for(auto e:m.successors[c]){int d=std::get<2>(e);if(!reached[d]){reached[d]=true;q.push(d);}}}
  for(size_t c=0;c<n;c++)if(used[c]&&m.theta_by_initial_config[c]<0&&(degree[c]!=1||!reached[c]))return;
  // Equal remaining endpoints (after translation) certify zero-cost chains.
  for(size_t c=0;c<n;c++) {
   if(m.theta_by_initial_config[c]>=0)continue;
   int cfg=(int)c,di=0,dj=0;
   while(m.successors[cfg].size()==1) {
    auto e=m.successors[cfg][0];int next=std::get<2>(e),prim=std::get<3>(e);
    bool initial=m.theta_by_initial_config[next]>=0;
    if(initial!=(prim>=0))return;
    if(!initial) {
     std::set<std::tuple<int,int,int,int>> before,after;
     for(auto f:m.primitives_in_config[cfg])before.emplace(std::get<0>(f),std::get<1>(f),std::get<2>(f),std::get<4>(f));
     for(auto f:m.primitives_in_config[next])after.emplace(std::get<0>(f),std::get<1>(f)+std::get<0>(e),std::get<2>(f)+std::get<1>(e),std::get<4>(f));
     if(before!=after)return;
    }
    di+=std::get<0>(e);dj+=std::get<1>(e);
    full[c].push_back({di,dj,next,prim});
    if(!initial)zero[c].push_back({di,dj,next,prim});
    cfg=next;if(initial)break;
    if(full[c].size()>n)return;
   }
  }
  enabled=true;
 }
};
extern MacroPaths g_macro;
