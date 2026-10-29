"""
Сравнение склейки, компактного CLOSED и сжатия при извлечении на одном стенде (Linux, 29.10.2026).

Варианты: baseline, glued, glued_closed, chain_on_pop, chain_on_pop_closed (см. build.sh, variants.py).
Серии:
  core    — core.tsv, 2 сеанса × (1 прогрев + 5 замеров); порядок вариантов во втором сеансе обратный;
  holdout — holdout.tsv, 1 прогрев + 3 замера;
  counts  — core.tsv, 1 проход бинарников со счётчиками операций (время не используется).
Каждый процесс однопоточный и закреплён за своим CPU (sched_setaffinity в bench.cpp); одновременно работает
не больше --jobs процессов на разных CPU. Готовые CSV пропускаются, поэтому прогон можно продолжать частями:
  python3 research/gluing/run_compare.py --jobs 2 --budget 160
"""
import argparse, csv, hashlib, json, os, platform, subprocess, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

p = Path(__file__).resolve().parent; root = p.parents[1]; out = p / 'results/linux_compare'
VARIANTS = ['baseline', 'glued', 'glued_closed', 'chain_on_pop', 'chain_on_pop_closed']


def jobs():
    j = []
    for s, order in ((1, VARIANTS), (2, VARIANTS[::-1])):
        for v in order:
            j.append((f'core_s{s}_{v}', v, 'core.tsv', 5, 1, 20261029 + 100 * s))
    for v in VARIANTS:
        j.append((f'holdout_{v}', v, 'holdout.tsv', 3, 1, 20261129))
    for v in VARIANTS:
        j.append((f'counts_{v}', v + '_counts', 'core.tsv', 1, 0, 20261229))
    return j


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--jobs', type=int, default=1); ap.add_argument('--budget', type=float, default=1e9)
    a = ap.parse_args(); out.mkdir(parents=True, exist_ok=True)
    cpus = sorted(os.sched_getaffinity(0)); cpus = cpus[1:] or cpus  # CPU 0 оставляем системе, если есть выбор
    mf = out / 'manifest.json'
    manifest = json.loads(mf.read_text()) if mf.exists() else {
        'platform': platform.platform(), 'machine': platform.machine(), 'cpu_count': os.cpu_count(),
        'clock': 'CLOCK_THREAD_CPUTIME_ID', 'pinning': 'sched_setaffinity, one process per CPU',
        'parallel_jobs': a.jobs, 'variants': VARIANTS, 'runs': {}}
    manifest['bin_sha256'] = {v: hashlib.sha256((p / 'bin' / v).read_bytes()).hexdigest() for v in VARIANTS}
    todo = [j for j in jobs() if not (out / (j[0] + '.csv')).exists()]
    start = time.time()

    def run(job, cpu):
        stem, binary, tasks, rounds, warm, seed = job
        if time.time() - start > a.budget: return None
        cmd = [str(p / 'bin' / binary), str(p / tasks), str(rounds), str(warm), str(seed), str(cpu)]
        tmp = out / (stem + '.part')
        t0 = time.time()
        with tmp.open('w') as o, (out / (stem + '.log')).open('w') as e:
            r = subprocess.run(cmd, cwd=root, stdout=o, stderr=e)
        if r.returncode: raise SystemExit(f'{stem}: код {r.returncode}')
        tmp.replace(out / (stem + '.csv'))
        return stem, {'command': cmd[1:], 'binary': binary, 'cpu': cpu, 'wall_s': round(time.time() - t0, 1),
                      'rows': sum(1 for _ in csv.DictReader((out / (stem + '.csv')).open()))}

    with ThreadPoolExecutor(a.jobs) as ex:
        futures = [ex.submit(run, j, cpus[i % a.jobs % len(cpus)]) for i, j in enumerate(todo)]
        for f in futures:
            r = f.result()
            if r: manifest['runs'][r[0]] = r[1]; mf.write_text(json.dumps(manifest, indent=1, ensure_ascii=False)); print('DONE', r[0], r[1]['wall_s'], 's', flush=True)
    left = [j[0] for j in jobs() if not (out / (j[0] + '.csv')).exists()]
    print('осталось запусков:', len(left))


if __name__ == '__main__':
    main()
