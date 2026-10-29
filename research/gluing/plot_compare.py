"""Графики серии run_compare.py: figures/compare_time.png (время) и figures/compare_ops.png (операции)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p = Path(__file__).resolve().parent; S = json.loads((p / 'results/linux_compare/summary.json').read_text())
BLUE, GREY, TXT, SUB, LINE = '#2350D8', '#8A909C', '#16181D', '#575C66', '#D9DCE2'
LAB = {'glued': 'склейка при генерации', 'chain_on_pop': 'сжатие при извлечении',
       'chain_on_pop_closed': 'сжатие при извлечении\n+ компактный CLOSED', 'glued_closed': 'склейка при генерации\n+ компактный CLOSED'}
order = ['glued', 'chain_on_pop', 'chain_on_pop_closed', 'glued_closed']
red = lambda sp: (1 - 1 / sp) * 100
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
for ax, key in zip(axes, ['core', 'holdout']):
    s = S[key]
    for y, v in enumerate(order):
        x = s['variants'][v]; col = BLUE if v.endswith('closed') else GREY
        lo, hi = red(x['ci95_speedup'][0]), red(x['ci95_speedup'][1]); m = x['reduction_pct']
        ax.plot([lo, hi], [y, y], color=col, lw=3); ax.scatter([m], [y], s=110, color=col, zorder=3)
        ax.text(m, y - 0.3, f"−{m:.1f}%".replace('.', ','), ha='center', va='bottom', fontsize=12, color=col)
    ax.axvline(0, color=TXT, lw=1, ls=(0, (3, 3)))
    ax.set_title(f"{'Основной набор' if key == 'core' else 'Отложенные карты'}: задач {s['tasks']}, карт {s['maps']}, замеров {s['repeats']}",
                 fontsize=12, color=TXT, loc='left')
    ax.set_xlim(-2, 40); ax.set_ylim(len(order) - 0.4, -0.8)
    ax.tick_params(colors=SUB); ax.tick_params(axis='y', length=0)
    for sp_ in ('top', 'right', 'left'): ax.spines[sp_].set_visible(False)
    ax.spines['bottom'].set_color(LINE); ax.grid(axis='x', color=LINE); ax.set_axisbelow(True)
axes[0].set_yticks(range(len(order)), [LAB[v] for v in order], fontsize=11, color=TXT)
fig.supxlabel('сокращение CPU-времени поиска против MeshA*, % (сумма медиан; отрезок — 95% ДИ, бутстрэп по картам)', fontsize=10, color=SUB)
fig.tight_layout(); fig.savefig(p / 'figures/compare_time.png', dpi=160, facecolor='white')

O = S['operations_ratio']
mets = [('push', 'вставки\nв OPEN'), ('heuristic_calls', 'расчёты\nэвристики'), ('final_entries', 'просмотр\nFinals'), ('cell_checks', 'проверки\nклеток')]
fig, ax = plt.subplots(figsize=(8, 4.6)); w = 0.36
for si, (v, col) in enumerate([('glued', GREY), ('chain_on_pop', BLUE)]):
    xs = [i + (si - 0.5) * w for i in range(len(mets))]; vals = [(O[v][m] - 1) * 100 for m, _ in mets]
    ax.bar(xs, vals, width=w * 0.92, color=col, label=LAB[v])
    for x, val in zip(xs, vals): ax.text(x, val - 0.8, f'{val:.0f}%'.replace('-', '−'), ha='center', va='top', fontsize=10, color=TXT)
ax.axhline(0, color=TXT, lw=1); ax.set_ylim(-40, 9)
ax.set_xticks(range(len(mets)), [m for _, m in mets], fontsize=10, color=TXT)
ax.set_ylabel('изменение против MeshA*, %', color=SUB); ax.tick_params(colors=SUB)
for sp_ in ('top', 'right', 'bottom'): ax.spines[sp_].set_visible(False)
ax.grid(axis='y', color=LINE); ax.set_axisbelow(True); ax.legend(frameon=False, loc='upper center', ncol=2, fontsize=10)
ax.set_title('Операции на core.tsv, сумма по 24 задачам (компактный CLOSED их не меняет)', fontsize=11, color=TXT, loc='left')
fig.tight_layout(); fig.savefig(p / 'figures/compare_ops.png', dpi=160, facecolor='white')
print(p / 'figures/compare_time.png'); print(p / 'figures/compare_ops.png')
