"""
Текстовые правки исходников MeshA* для двух дополнений к склейке.

1. Компактный CLOSED (флаг компиляции COMPACT_CLOSED).
   Следствие леммы 1: развёртка пучка — дерево, у неначальной (internal) клетки ровно один
   предок, поэтому она порождается не более одного раза и её не нужно хранить в CLOSED.
   CLOSED хранит только initial-клетки, слой = курс θ: 16 слоёв вместо MAX_CONFIGS = 1800
   (при карте 1200×1200: 2,7 МиБ вместо 309 МиБ). Включается во время работы, только если
   MacroPaths подтвердил структуру дерева (g_macro.enabled), иначе используется обычный CLOSED.

2. Сжатие цепочки при извлечении (GLUING_MODE == 4) — альтернативная реализация той же идеи
   для сравнения: после извлечения вершины пройти цепочку до развилки (каждая клетка
   проверяется на столкновение) и породить потомков конца цепочки.

Правки применяются регулярными выражениями, поэтому работают и на исходном коде авторов
(source_snapshot), и на корневом CLI. Каждая правка проверяет, что применилась ровно один раз.
"""
import re


def _sub_once(pattern, repl, text, what):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'variants.py: не найдено место правки: {what}')
    return new


def compact_closed_header(hpp):
    if 'compact_theta' in hpp:
        return hpp
    return _sub_once(r'(\n    SearchTree\(\);\n)', r'''\1
#ifdef COMPACT_CLOSED
    // Компактный CLOSED (следствие леммы 1): если задан, хранятся только initial-клетки,
    // слой = курс θ (NUM_HEADINGS слоёв). Internal-клетки не повторяются и не хранятся.
    const vector<int> *compact_theta = nullptr;
    explicit SearchTree(const vector<int> *theta_by_initial_config);
#endif
''', hpp, 'SearchTree() в KC_searching.hpp')


def compact_closed_source(cpp):
    if 'compact_theta' in cpp:
        return cpp
    cpp = _sub_once(r'(    fast_closed\.assign\(\(total_states / 8\) \+ 1, 0\);[ \t]*\n\}\n)', r'''\1
#ifdef COMPACT_CLOSED
SearchTree::SearchTree(const vector<int> *theta_by_initial_config) {
    // Только initial-клетки: слой = θ, поэтому NUM_HEADINGS слоёв вместо MAX_CONFIGS.
    compact_theta = theta_by_initial_config;
    uint64_t total_states = (uint64_t)MAX_MAP_HEIGHT * MAX_MAP_WIDTH * NUM_HEADINGS;
    fast_closed.assign((total_states / 8) + 1, 0);
}
#endif
''', cpp, 'конец SearchTree::SearchTree()')
    # add_to_closed: internal-клетка в компактном режиме не помечается
    cpp = _sub_once(r'(    int layer_index = v->config_id;[ \t]*\n)(\s*size_t num = index_in_closed\(v->i, v->j, layer_index\);.*?fast_closed\[num / 8\] \|= \(1 << \(num % 8\)\);[ \t]*\n)',
                    r'''\1#ifdef COMPACT_CLOSED
    if (compact_theta) layer_index = (*compact_theta)[layer_index];
    if (layer_index >= 0) {
#endif
\2#ifdef COMPACT_CLOSED
    }
#endif
''', cpp, 'add_to_closed')
    # was_expanded: internal-клетка в компактном режиме никогда не раскрыта повторно
    cpp = _sub_once(r'(\n)(    size_t num = index_in_closed\(i, j, layer_index\);)', r'''\1#ifdef COMPACT_CLOSED
    if (compact_theta) {
        layer_index = (*compact_theta)[layer_index];
        if (layer_index < 0) return false;
    }
#endif
\2''', cpp, 'was_expanded')
    return cpp


def compact_closed_params(cpp):
    if 'COMPACT_CLOSED' in cpp:
        return cpp
    # MeshGraphParams — второй конструктор с new SearchTree() в файле
    idx = [m.start() for m in re.finditer(r'    this->ast = new SearchTree\(\);\n', cpp)]
    if len(idx) != 2:
        raise SystemExit('variants.py: ожидались два конструктора с new SearchTree()')
    i = idx[1]
    repl = '''#ifdef COMPACT_CLOSED
    // Компактный CLOSED только при подтверждённой структуре дерева (MacroPaths проверил лемму 1).
    this->ast = g_macro.enabled ? new SearchTree(&mesh_info->theta_by_initial_config) : new SearchTree();
#else
    this->ast = new SearchTree();
#endif
'''
    return cpp[:i] + repl + cpp[i + len('    this->ast = new SearchTree();\n'):]


def chain_on_pop(cpp):
    if 'GLUING_MODE == 4' in cpp:
        return cpp
    return _sub_once(
        r'    // --- Standard Successor Generation \(Algorithm 2\) ---\n(.*?)    for \(auto triple : mesh_info->successors\[v->config_id\]\) \{\n(.*?)        int i = v->i \+ di;\n        int j = v->j \+ dj;\n',
        r'''    int base_i = v->i, base_j = v->j, base_config = v->config_id;
#if GLUING_MODE == 4
    // Сжатие при извлечении: проходим цепочку (один неначальный потомок, f постоянно по лемме 2),
    // проверяем каждую клетку на столкновение и порождаем потомков конца цепочки.
    while (mesh_info->successors[base_config].size() == 1 && get<3>(mesh_info->successors[base_config][0]) == -1) {
        auto e = mesh_info->successors[base_config][0];
        base_i += get<0>(e); base_j += get<1>(e); base_config = get<2>(e);
        if (!check_cell(task_map, base_i, base_j, &checked_cells)) return;
        GCOUNT(glued_cells);
    }
#endif
    // --- Standard Successor Generation (Algorithm 2) ---
\1    for (auto triple : mesh_info->successors[base_config]) {
\2        int i = base_i + di;
        int j = base_j + dj;
''', cpp, 'цикл генерации потомков')
