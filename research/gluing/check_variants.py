"""
Функциональная проверка всех вариантов стенда на manual.tsv (20 ручных случаев) и, по желанию, на core.tsv:
для каждой задачи признак «путь найден» и стоимость должны совпасть с baseline (допуск max(0,002, 1e-5·C)).
Корректность самого пути (начало, финиш, примитивы, коллизии, сумма стоимостей) проверяет bench.cpp и
завершается с ошибкой, если путь неверен.
Запуск из корня репозитория: python3 research/gluing/check_variants.py [manual.tsv core.tsv ...]
"""
import csv, io, subprocess, sys
from pathlib import Path

p = Path(__file__).resolve().parent; root = p.parents[1]
variants = ['previous', 'zero_chain', 'glued', 'glued_closed', 'chain_on_pop', 'chain_on_pop_closed']


def run(variant, tasks):
    r = subprocess.run([str(p / 'bin' / variant), str(p / tasks), '1', '0', '1'], cwd=root, capture_output=True, text=True, timeout=900)
    if r.returncode:
        raise SystemExit(f'FAIL: {variant} на {tasks}: {r.stderr[-500:]}')
    return {row['task']: row for row in csv.DictReader(io.StringIO(r.stdout))}


failed = False
for tasks in (sys.argv[1:] or ['manual.tsv']):
    base = run('baseline', tasks)
    for v in variants:
        res = run(v, tasks); bad = []
        for t, b in base.items():
            x = res[t]; cb, cx = float(b['cost']), float(x['cost'])
            if b['found'] != x['found'] or abs(cb - cx) > max(0.002, 1e-5 * abs(cb)) or x['valid'] != '1':
                bad.append(t)
        print(f'{tasks}: {v:20s} задач {len(res):3d}, расхождений с baseline {len(bad)}' + (f' {bad[:3]}' if bad else ''))
        failed |= bool(bad)
if failed:
    raise SystemExit('FAIL: варианты расходятся с baseline')
print('PASS: все варианты дают те же стоимости и корректные пути')
