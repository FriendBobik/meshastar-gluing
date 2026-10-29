"""
Сводка серии run_compare.py: results/linux_compare/*.csv -> results/linux_compare/summary.json.

Метрика, как в основной серии: для каждой задачи медиана CPU-времени повторов, затем сумма медиан;
ускорение = сумма baseline / сумма варианта. 95% ДИ — бутстрэп по картам (кластер = карта, 10 000 выборок).
Дополнительно: ср. геометрическое ускорений (задачи с baseline > 0,05 мс), число задач, где вариант быстрее,
совпадение признака «путь найден» и стоимости с baseline, суммы операций из бинарников со счётчиками.
"""
import csv, json, math, random, statistics
from collections import defaultdict
from pathlib import Path

d = Path(__file__).resolve().parent / 'results/linux_compare'
V = ['baseline', 'glued', 'glued_closed', 'chain_on_pop', 'chain_on_pop_closed']
TASKMAP = {}
for f in ('core.tsv', 'holdout.tsv'):
    for r in csv.DictReader((d.parents[1] / f).open(), delimiter='\t'):
        TASKMAP[r['id']] = r['map']


def series(prefixes):
    t = defaultdict(lambda: defaultdict(list)); res = defaultdict(dict)
    for v in V:
        for pre in prefixes:
            for r in csv.DictReader((d / f'{pre}{v}.csv').open()):
                t[r['task']][v].append(float(r['cpu_ms'])); res[r['task']][v] = (r['found'], float(r['cost']))
    return t, res


random.seed(20261029)


def summarize(prefixes):
    t, res = series(prefixes); tasks = sorted(t)
    med = {k: {v: statistics.median(t[k][v]) for v in V} for k in tasks}
    groups = defaultdict(list)
    for k in tasks: groups[TASKMAP[k]].append(k)
    mism = {v: [k for k in tasks if res[k][v][0] != res[k]['baseline'][0] or
                abs(res[k][v][1] - res[k]['baseline'][1]) > max(0.002, 1e-5 * abs(res[k]['baseline'][1]))] for v in V[1:]}
    out = {'tasks': len(tasks), 'repeats': len(t[tasks[0]]['baseline']), 'maps': len(groups),
           'unsolved': sum(res[k]['baseline'][0] == '0' for k in tasks), 'variants': {}}
    sb = sum(med[k]['baseline'] for k in tasks); out['baseline_sum_median_cpu_ms'] = sb
    for v in V[1:]:
        sv = sum(med[k][v] for k in tasks)
        sp = [med[k]['baseline'] / med[k][v] for k in tasks if med[k]['baseline'] > 0.05]
        bs = []
        for _ in range(10000):
            ks = [k for g in random.choices(list(groups), k=len(groups)) for k in groups[g]]
            bs.append(sum(med[k]['baseline'] for k in ks) / sum(med[k][v] for k in ks))
        bs.sort()
        out['variants'][v] = {'sum_median_cpu_ms': sv, 'speedup': sb / sv, 'reduction_pct': 100 * (1 - sv / sb),
                              'ci95_speedup': [bs[250], bs[9749]], 'geomean_speedup': math.exp(sum(map(math.log, sp)) / len(sp)),
                              'wins': sum(med[k][v] < med[k]['baseline'] for k in tasks), 'cost_mismatches': mism[v]}
    return out


summary = {'core': summarize(['core_s1_', 'core_s2_']), 'holdout': summarize(['holdout_'])}
F = ['steps', 'push', 'pop', 'heuristic_calls', 'prune_calls', 'final_entries', 'cell_checks', 'stale']
cnt = {v: defaultdict(float) for v in V}
for v in V:
    for r in csv.DictReader((d / f'counts_{v}.csv').open()):
        for f in F: cnt[v][f] += float(r[f])
summary['operations_core'] = {v: {f: cnt[v][f] for f in F} for v in V}
summary['operations_ratio'] = {v: {f: cnt[v][f] / cnt['baseline'][f] for f in F if cnt['baseline'][f]} for v in V}
(d / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False))
for key, title in (('core', 'core.tsv'), ('holdout', 'holdout.tsv')):
    s = summary[key]
    print(f"\n{title}: задач {s['tasks']} ({s['maps']} карт, без пути {s['unsolved']}), замеров на вариант {s['repeats']}, baseline {s['baseline_sum_median_cpu_ms'] / 1000:.2f} с")
    for v, x in s['variants'].items():
        print(f"  {v:20s} −{x['reduction_pct']:.1f}%  ×{x['speedup']:.3f} [{x['ci95_speedup'][0]:.3f}; {x['ci95_speedup'][1]:.3f}]  ср.геом ×{x['geomean_speedup']:.3f}  быстрее {x['wins']}/{s['tasks']}  расхождений {len(x['cost_mismatches'])}")
print('\nоперации core (отношение к baseline):')
for v in V[1:]:
    print('  ' + f'{v:20s} ' + ' '.join(f"{f}={summary['operations_ratio'][v][f]:.3f}" for f in ('steps', 'push', 'heuristic_calls', 'final_entries', 'cell_checks', 'stale')))
