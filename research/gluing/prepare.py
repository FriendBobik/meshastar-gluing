from pathlib import Path
import shutil,subprocess,hashlib,json
p=Path(__file__).resolve().parent;root=p.parents[1];dst=p/'generated'
# Freeze the actual pre-research source. Existing CLOSED experiment stays separate.
ref='12574ff03d8d61ac153b4e4224eac2229a9577e1'
input_root=p/'source_snapshot' if (p/'source_snapshot').exists() else root
for folder,pattern in [('include','*.hpp'),('src','*.cpp')]:
 for file in (input_root/folder).glob(pattern):
  rel=file.relative_to(input_root);out=dst/rel;out.parent.mkdir(parents=True,exist_ok=True)
  snapshot=p/'source_snapshot'/rel
  out.write_bytes(snapshot.read_bytes() if snapshot.exists() else subprocess.check_output(['git','show',ref+':'+str(rel)],cwd=root))
# Every timing variant shares this exact source and compiler flags except gluing mode.
s=dst/'src/KC_searching.cpp';t=s.read_text();t='#include "gluing_stats.hpp"\n'+t
t=t.replace('    open.push(item);','    GCOUNT(push);\n    open.push(item);')
t=t.replace('        ptrSearchNode best_node = open.top();\n        open.pop();','        ptrSearchNode best_node = open.top();\n        open.pop();\n        GCOUNT(pop);')
t=t.replace('            // Duplicate found -> Discard and recycle','            GCOUNT(stale);\n            // Duplicate found -> Discard and recycle')
s.write_text(t)
p0=dst/'src/KC_search_params.cpp';t=p0.read_text();t='#include "gluing_stats.hpp"\n#include "macro_paths.hpp"\n'+t
t=t.replace('''    if (stats_cnt != nullptr) {''','''    GCOUNT(cell_checks);
    if (stats_cnt != nullptr) {''')
t=t.replace('''    for (size_t k = start_idx;''','''    GCOUNT(primitive_checks);
    for (size_t k = start_idx;''')
t=t.replace('''    // 1. Basic check: If u itself''','''    GCOUNT(prune_calls);
    // 1. Basic check: If u itself''')
t=t.replace('''float MeshGraphParams::heuristic(ptrSearchNode node) {
    return''','''float MeshGraphParams::heuristic(ptrSearchNode node) {
    GCOUNT(heuristic_calls);
    return''')
# Count-only build captures repeated endpoint scans, without timers in hot code.
t=t.replace('''for (auto p : params->mesh_info->primitives_in_config[config_id]) {''','''for (auto p : params->mesh_info->primitives_in_config[config_id]) { GCOUNT(final_entries);''')
t=t.replace('''for (auto p : mesh_info->primitives_in_config[v->config_id]) {''','''for (auto p : mesh_info->primitives_in_config[v->config_id]) { GCOUNT(final_entries);''')
t=t.replace('''for (auto p : params->mesh_info->primitives_in_config[node->vertex->config_id]) {''','''for (auto p : params->mesh_info->primitives_in_config[node->vertex->config_id]) { GCOUNT(final_entries);''')
needle='''    // --- Optimization: Direct Jump to Unique Successor ---'''
old='''#if GLUING_MODE == 1
    // Earlier prototype: traverse after pop, rechecking pruning at each cell.
    if (g_macro.enabled && !current->mem_after_closed) {
        int ci=v->i,cj=v->j,cfg=v->config_id;
        while (mesh_info->successors[cfg].size()==1) {
            auto edge=mesh_info->successors[cfg][0];
            if (get<3>(edge)>=0) break;
            ci+=get<0>(edge);cj+=get<1>(edge);cfg=get<2>(edge);
            if (!check_cell(task_map,ci,cj,&checked_cells) || mesh_should_prune(task_map,ci,cj,cfg,this)) return;
            GCOUNT(glued_cells);
        }
        v->i=ci;v->j=cj;v->config_id=cfg;
    }
#endif
'''
t=t.replace(needle,old+needle)
# The whole source contains the same fragment only in the active standard mesh generation.
needle='''        if (check_cell(task_map, i, j, &checked_cells) &&
            !mesh_should_prune(task_map, i, j, next_config, this)) {
            
            ptrVertex u'''
rep='''        if (check_cell(task_map, i, j, &checked_cells) &&
            !mesh_should_prune(task_map, i, j, next_config, this)) {
#if GLUING_MODE >= 2
            if (g_macro.enabled && mesh_info->theta_by_initial_config[next_config]<0) {
                const auto &path = (GLUING_MODE==3 && w==1.0f) ?
                    g_macro.full[next_config] : g_macro.zero[next_config];
                bool collision=false;
                const int origin_i=i,origin_j=j;
                for (const auto &step : path) {
                    if (!check_cell(task_map,origin_i+step.di,origin_j+step.dj,&checked_cells)) {
                        collision=true; break;
                    }
                    GCOUNT(glued_cells);
                }
                if (collision) continue;
                if (!path.empty()) {
                    const auto &end=path.back();
                    i=origin_i+end.di;j=origin_j+end.dj;next_config=end.config;
                    if (end.prim>=0) cost+=(float)control_set->cost(end.prim);
                    GCOUNT(macro_edges);
                }
            }
#endif
            ptrVertex u'''
assert needle in t;t=t.replace(needle,rep);p0.write_text(t)
# Дополнения: компактный CLOSED (флаг COMPACT_CLOSED) и сжатие при извлечении (GLUING_MODE 4), см. variants.py.
import sys as _sys;_sys.path.insert(0,str(p))
import variants as _V
_h=dst/'include/KC_searching.hpp';_h.write_text(_V.compact_closed_header(_h.read_text()))
_c=dst/'src/KC_searching.cpp';_c.write_text(_V.compact_closed_source(_c.read_text()))
_q=dst/'src/KC_search_params.cpp';_q.write_text(_V.chain_on_pop(_V.compact_closed_params(_q.read_text())))
manifest={str(f.relative_to(dst)):hashlib.sha256(f.read_bytes()).hexdigest() for f in dst.rglob('*') if f.is_file()}
(p/'source_hashes.json').write_text(json.dumps(manifest,indent=2))
print(dst)
