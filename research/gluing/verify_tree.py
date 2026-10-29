"""
Проверка лемм 1 и 2 на таблицах переходов MeshA* (data/*_mesh_info.txt). Только стандартная библиотека.

Лемма 1: у каждой неначальной (internal) конфигурации ровно один входящий переход, и регулярный
переход никогда не ведёт в начальную конфигурацию. Отсюда развёртка пучка — дерево.
Лемма 2: на звене цепочки (единственный потомок, он internal) множество концов примитивов
(Finals) не меняется после сдвига на шаг, поэтому g, h и f постоянны вдоль цепочки.
Печатает долю звеньев и длины цепочек — от них зависит выигрыш склейки.
"""
from collections import Counter, defaultdict
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]


def load(path):
    succ, fin, init = defaultdict(list), defaultdict(list), set()
    lines = iter(path.read_text().splitlines())
    for line in lines:
        if line.startswith('in goal type:'):
            init.add(int(line.split()[3]))
        elif line.startswith('start type is:'):
            c = int(line.split()[3])
            for l in lines:
                if l.startswith('---'): break
                succ[c].append(tuple(map(int, l.split())))
        elif line.startswith('final_thetas_of_type:'):
            c = int(line.split()[1])
            for l in lines:
                if l.startswith('---'): break
                fin[c].append(tuple(map(int, l.split())))
    return succ, fin, init


def check(name):
    succ, fin, init = load(root / 'data' / f'{name}_mesh_info.txt')
    confs = set(succ) | set(fin)
    internal = confs - init
    indeg = Counter()
    into_initial = 0
    for c in confs:
        for di, dj, nc, pid in succ[c]:
            if pid == -1:
                indeg[nc] += 1
                into_initial += nc in init
    bad1 = [c for c in internal if indeg[c] != 1]
    link = lambda c: len(succ[c]) == 1 and succ[c][0][3] == -1
    links = [c for c in internal if link(c)]
    bad2 = 0
    for u in links:
        di, dj, w, _ = succ[u][0]
        a = {(ft, x, y, p) for ft, x, y, k, p in fin[u]}
        b = {(ft, x + di, y + dj, p) for ft, x, y, k, p in fin[w]}
        bad2 += a != b
    heads = [c for c in links if not any(link(p) and succ[p][0][2] == c for p in links)]
    lengths = []
    for c in heads:
        n = 0
        while c in internal and link(c):
            n += 1; c = succ[c][0][2]
        lengths.append(n)
    ok = not bad1 and into_initial == 0 and bad2 == 0
    print(f'{name}: internal {len(internal)}, лемма 1: нарушений {len(bad1)}, регулярных переходов в initial {into_initial}; '
          f'лемма 2: звеньев {len(links)} ({100 * len(links) / len(internal):.1f}%), нарушений {bad2}; '
          f'длина цепочки: средняя {sum(lengths) / len(lengths):.2f}, максимум {max(lengths)}')
    return ok


if __name__ == '__main__':
    results = [check(n) for n in (sys.argv[1:] or ['base', 'add'])]
    if not all(results):
        raise SystemExit('FAIL: структура дерева не подтверждена')
    print('PASS: леммы 1 и 2 выполняются на всех таблицах переходов')
