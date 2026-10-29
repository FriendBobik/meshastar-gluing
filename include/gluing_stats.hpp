#pragma once
#include <cstdint>
struct GluingStats {uint64_t push=0,pop=0,stale=0,cell_checks=0,primitive_checks=0,prune_calls=0,heuristic_calls=0,final_entries=0,glued_cells=0,macro_edges=0;};
extern GluingStats g_stats;
#ifdef GLUING_COUNTERS
#define GCOUNT(x) (++g_stats.x)
#else
#define GCOUNT(x) ((void)0)
#endif
