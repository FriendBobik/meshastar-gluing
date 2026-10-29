#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <random>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <ctime>
#include <cstring>
#include <sys/resource.h>
#include <unistd.h>
#ifdef __APPLE__
#include <mach/mach.h>
#include <mach/thread_policy.h>
#include <pthread.h>
#else
#include <sched.h>
#endif
#include "common.hpp"
#include "KC_search_params.hpp"
#include "KC_astar.hpp"
#include "gluing_stats.hpp"
#include "macro_paths.hpp"
MyHEAP *HEAP=nullptr;
GluingStats g_stats;
MacroPaths g_macro;
static double cpu_ms() {timespec ts{};if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&ts))throw std::runtime_error("thread CPU clock unavailable");return ts.tv_sec*1000.0+ts.tv_nsec/1e6;}
using Wall=std::chrono::steady_clock;
static double wall_ms(Wall::time_point start) {return std::chrono::duration<double,std::milli>(Wall::now()-start).count();}
struct Task {std::string id,map,control;int si,sj,st,fi,fj,ft;float w;};
static int thread_count() {
#ifdef __APPLE__
 thread_act_array_t threads;mach_msg_type_number_t n=0;
 if(task_threads(mach_task_self(),&threads,&n)!=KERN_SUCCESS)return -1;
 for(unsigned i=0;i<n;i++)mach_port_deallocate(mach_task_self(),threads[i]);
 vm_deallocate(mach_task_self(),(vm_address_t)threads,n*sizeof(thread_t));return (int)n;
#else
 std::ifstream f("/proc/self/status");std::string s;while(std::getline(f,s))if(s.rfind("Threads:",0)==0)return std::stoi(s.substr(8));return -1;
#endif
}
int main(int argc,char **argv) {
 if(argc<4){std::cerr<<"usage: bench tasks.tsv measured_rounds warmup_rounds [seed] [cpu_id]\n";return 1;}
 try {
 int rounds=std::stoi(argv[2]),warmup=std::stoi(argv[3]);unsigned seed=argc>4?std::stoul(argv[4]):42;
 int cpu_id=argc>5?std::stoi(argv[5]):-1;int affinity=-1;
#ifdef __APPLE__
 int qos=pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
 if(cpu_id>=0){thread_affinity_policy_data_t p={cpu_id+1};auto th=mach_thread_self();affinity=thread_policy_set(th,THREAD_AFFINITY_POLICY,(thread_policy_t)&p,THREAD_AFFINITY_POLICY_COUNT);mach_port_deallocate(mach_task_self(),th);}
 std::cerr<<"PLATFORM macos affinity_result="<<affinity<<" hard_pin=0 qos="<<qos<<" pid="<<getpid()<<" threads="<<thread_count()<<"\n";
#else
 if(cpu_id<0){cpu_set_t allowed;CPU_ZERO(&allowed);if(sched_getaffinity(0,sizeof(allowed),&allowed)==0)for(int i=0;i<CPU_SETSIZE;i++)if(CPU_ISSET(i,&allowed)){cpu_id=i;break;}}
 if(cpu_id>=0){cpu_set_t mask;CPU_ZERO(&mask);CPU_SET(cpu_id,&mask);affinity=sched_setaffinity(0,sizeof(mask),&mask);}
 if(affinity!=0)throw std::runtime_error("CPU pin failed");
 std::cerr<<"PLATFORM linux hard_pin=1 cpu="<<cpu_id<<" pid="<<getpid()<<" threads="<<thread_count()<<"\n";
#endif
 std::ifstream input(argv[1]);if(!input)throw std::runtime_error("Cannot read task manifest");std::string line;std::getline(input,line);std::vector<Task> tasks;
 while(std::getline(input,line)){Task t;std::istringstream s(line);s>>t.id>>t.map>>t.control>>t.si>>t.sj>>t.st>>t.fi>>t.fj>>t.ft>>t.w;if(!s)throw std::runtime_error("bad task row");tasks.push_back(t);}
 if(tasks.empty())throw std::runtime_error("Empty manifest");
 HEAP=new MyHEAP();
 std::string loaded_map,loaded_control;Map *map=nullptr;ControlSet *cs=nullptr;MeshInfo *mesh=nullptr;
 std::mt19937 rng(seed);
 std::cout<<"task,round,mode,found,cost,path_cost,path_hash,valid,steps,cpu_ms,wall_ms,init_cpu_ms,cleanup_cpu_ms,checked_cells,nvcsw,nivcsw,pool_capacity,push,pop,stale,cell_checks,primitive_checks,prune_calls,heuristic_calls,final_entries,glued_cells,macro_edges\n";
 for(int round=-warmup;round<rounds;round++) {
  std::vector<int> order(tasks.size());for(size_t i=0;i<order.size();i++)order[i]=(int)i;std::shuffle(order.begin(),order.end(),rng);
  for(int ix:order) {
   auto t=tasks[ix];
   if(t.control!=loaded_control) {
    delete mesh;delete cs;
    cs=new ControlSet();mesh=new MeshInfo();
    // Loaders log on stdout; redirect these messages to stderr without changing source.
    auto buf=std::cout.rdbuf();std::cout.rdbuf(std::cerr.rdbuf());
    cs->load_primitives("data/"+t.control+"_control_set.txt");mesh->load("data/"+t.control+"_mesh_info.txt");
    std::cout.rdbuf(buf);double begin=cpu_ms();g_macro=MacroPaths{};g_macro.build(*mesh);
    std::cerr<<"PRECOMPUTE control="<<t.control<<" cpu_ms="<<cpu_ms()-begin<<" enabled="<<g_macro.enabled<<"\n";
    if(!g_macro.enabled)throw std::runtime_error("Unexpected non-tree mesh");loaded_control=t.control;
   }
   if(t.map!=loaded_map){delete map;map=new Map();map->read_file_to_cells("maps/"+t.map+".map");loaded_map=t.map;}
   Vertex start(t.si,t.sj,t.st),goal(t.fi,t.fj,t.ft);
   double init_start=cpu_ms();auto params=new MeshGraphParams(&start,&goal,map,cs,mesh,t.w,0,0);double init_ms=cpu_ms()-init_start;
   g_stats=GluingStats{};rusage before{},after{};getrusage(RUSAGE_SELF,&before);double cpu_start=cpu_ms();auto wall_start=Wall::now();
   auto result=AstarSearch(params,false);
   double elapsed_wall=wall_ms(wall_start),elapsed_cpu=cpu_ms()-cpu_start;getrusage(RUSAGE_SELF,&after);
   double cost=result.path_found?result.final_node->g:-1,path_cost=result.path_found?0:-1;bool valid=true;uint64_t hash=1469598103934665603ULL;
   if(result.path_found) {
    auto n=result.final_node;std::vector<int> ids;size_t depth=0;
    if(!params->is_goal(n->vertex))valid=false;
    while(!(n->parent==NULL_Node)) {
     if(++depth>1000000)throw std::runtime_error("parent loop");
     auto par=n->parent;auto u=par->vertex,v=n->vertex;
     int a=mesh->theta_by_initial_config[u->config_id],b=mesh->theta_by_initial_config[v->config_id];
     if(a<0||b<0){valid=false;break;}
     int id=cs->get_prim_between_states(a,v->i-u->i,v->j-u->j,b);
     if(id<0){valid=false;break;}
     auto prim=cs->list_all_prims[id];path_cost+=cs->cost(id);ids.push_back(id);
     for(size_t j=0;j<prim->swept_cells_i.size();j++){int i=u->i+prim->swept_cells_i[j],col=u->j+prim->swept_cells_j[j];if(!map->in_bounds(i,col)||!map->traversable(i,col))valid=false;}
     n=par;
    }
    if(n->vertex->i!=start.i||n->vertex->j!=start.j||mesh->theta_by_initial_config[n->vertex->config_id]!=start.theta)valid=false;
    if(std::abs(path_cost-cost)>std::max(.01,1e-5*path_cost))valid=false;
    for(auto it=ids.rbegin();it!=ids.rend();it++){hash^=(uint64_t)(*it+1);hash*=1099511628211ULL;}
    HEAP->delete_SearchNode(result.final_node);
   }
   int checked=params->checked_cells;double cleanup_start=cpu_ms();delete params;double cleanup_ms=cpu_ms()-cleanup_start;
   if(!valid)throw std::runtime_error("Invalid path for "+t.id);
   if(round<0)continue;
   std::cout<<std::setprecision(12)<<t.id<<','<<round<<','<<GLUING_MODE<<','<<result.path_found<<','<<cost<<','<<path_cost<<','<<hash<<','<<valid<<','<<result.steps<<','<<elapsed_cpu<<','<<elapsed_wall<<','<<init_ms<<','<<cleanup_ms<<','<<checked<<','<<after.ru_nvcsw-before.ru_nvcsw<<','<<after.ru_nivcsw-before.ru_nivcsw<<','<<HEAP->N;
   auto &s=g_stats;std::cout<<','<<s.push<<','<<s.pop<<','<<s.stale<<','<<s.cell_checks<<','<<s.primitive_checks<<','<<s.prune_calls<<','<<s.heuristic_calls<<','<<s.final_entries<<','<<s.glued_cells<<','<<s.macro_edges<<std::endl;
  }
 }
 delete map;delete mesh;delete cs;delete HEAP;
 } catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
