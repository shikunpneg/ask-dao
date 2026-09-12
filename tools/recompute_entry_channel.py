# -*- coding: utf-8 -*-
"""强制重算「词条通道」（本地，不开浏览器）。

为什么需要：browser_mass_search.py 的循环跳过已完成的 term，所以语料补全后
`--quick` 会直接返回（日志里的「完成 0s」）。而它的 has_entry_hits 是在语料只有
49/82 时算出来的 —— 凡涉及 `熵`/`记忆`/`测度` 等 33 个词的组合，当时都只能去开
Edge 现抓（多数失败），被判成「无关联信号」。

本脚本按 make_one 的同一逻辑重算全部组合：
    for w in (a, b):
        page = data/wiki/{w}.json
        命中段落 = [p for p in page.paragraphs if 另一个词 in p]
        有命中才记（没提对方 = 无关联信号）
搜索通道（Edge 抓的）保持不动。

原文件先备份。
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r'E:\ask-dao\ask-dao-machine')
OUT = ROOT / 'out' / 'demo' / 'browser_mass_search.json'
WIKI = ROOT / 'data' / 'wiki'


def main():
    if not OUT.exists():
        print('找不到 browser_mass_search.json')
        return
    rows = json.loads(OUT.read_text(encoding='utf-8'))
    print(f'原记录 {len(rows)} 条')

    bak = OUT.with_name(f'browser_mass_search.backup_{time.strftime("%Y%m%d_%H%M%S")}.json')
    shutil.copy2(OUT, bak)
    print(f'已备份 -> {bak.name}')

    # 一次把 82 个词条读进内存（原逻辑每次重读文件，13k 次 IO）
    pages = {}
    for f in WIKI.glob('*.json'):
        if f.name == '_failed.json':
            continue
        try:
            pages[f.stem] = json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            continue
    print(f'词条缓存 {len(pages)} 个')

    old_hit = sum(1 for x in rows if x.get('has_entry_hits'))
    changed = 0
    newly = 0
    lost = 0
    for r in rows:
        a, b = r.get('a'), r.get('b')
        hits = []
        for w in (a, b):
            page = pages.get(w)
            if not page:
                continue
            other = b if w == a else a
            chosen = [p for p in (page.get('paragraphs') or []) if other in p]
            if not chosen:
                continue
            hits.append({'title': f"维基·{page.get('title', w)}", 'fragment': chosen[0][:220]})
        new_flag = bool(hits)
        if new_flag != bool(r.get('has_entry_hits')):
            changed += 1
            if new_flag:
                newly += 1
            else:
                lost += 1
        r['entry_hits'] = hits
        r['has_entry_hits'] = new_flag

    new_hit = sum(1 for x in rows if x.get('has_entry_hits'))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')

    n = len(rows)
    print()
    print('=' * 72)
    print(f'词条通道命中： {old_hit} ({100*old_hit/n:.1f}%)  ->  {new_hit} ({100*new_hit/n:.1f}%)')
    print(f'  状态改变 {changed} 条（新命中 {newly} / 失去 {lost}）')
    print('=' * 72)

    # 重点组合
    ONLY = {'熵选择': ('熵', '选择'), '责任催化': ('责任', '催化'), '熵市场': ('熵', '市场'),
            '公理化记忆': ('公理化', '记忆'), '记忆压缩': ('记忆', '压缩'),
            '意识拓扑': ('意识', '拓扑'), '正义测度': ('正义', '测度'),
            '编码公理': ('编码', '公理化'), '进化发育': ('演化', '发育')}
    print()
    print('9 个重点组合的词条通道：')
    d = {x['term']: x for x in rows}
    for t in sorted(ONLY):
        x = d.get(t) or {}
        hs = x.get('entry_hits') or []
        mark = '命中' if hs else '无'
        print(f'  {t:6} {mark}  {len(hs)} 条')
        for h in hs[:2]:
            print(f'        · {h["title"][:26]}  {h["fragment"][:90]}')

    print()
    print('命中数最高的 12 个组合：')
    top = sorted([x for x in rows if x.get('has_entry_hits')],
                 key=lambda x: -len(x.get('entry_hits') or []))[:12]
    for x in top:
        print(f'  {x["term"]:8} {len(x["entry_hits"])} 条  '
              + ' | '.join(h['title'][:16] for h in x['entry_hits']))


if __name__ == '__main__':
    main()
