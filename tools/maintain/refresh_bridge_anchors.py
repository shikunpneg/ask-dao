# -*- coding: utf-8 -*-
"""重跑 9 个重点组合的 M7 经验锚点（语料补全后），不走浏览器。

同时核实：词条通道命中数 558 -> 452 的变化是不是"修掉假阳性"，
以及 9 个重点组合在两个成分词条里是否真的互相提及。
"""
import json
import sys
from pathlib import Path

ROOT = Path(r'E:\ask-dao\ask-dao-machine')
sys.path.insert(0, str(ROOT / 'tools'))

from word_understand import WORDS, understand, question  # noqa: E402
from retrieve_browser import wiki_page  # noqa: E402

WU = ROOT / 'out' / 'demo' / 'word_understand.json'
CACHE = ROOT / 'out' / 'demo' / 'retrieve_cache_browser.json'
BMS = ROOT / 'out' / 'demo' / 'browser_mass_search.json'

PAIRS = [('熵', '选择'), ('责任', '催化'), ('熵', '市场'), ('公理化', '记忆'),
         ('记忆', '压缩'), ('意识', '拓扑'), ('正义', '测度'),
         ('编码', '公理化'), ('演化', '发育')]
TERMS = ['熵选择', '责任催化', '熵市场', '公理化记忆', '记忆压缩',
         '意识拓扑', '正义测度', '编码公理化', '演化发育']
PAIR_OF = dict(zip(TERMS, PAIRS))


def entry_hits(a, b, max_hits=2):
    """与 retrieve_browser.retrieve 的「词条通道」逐行等价，但不碰 Edge。"""
    hits = []
    cross = []
    for term in (a, b):
        page = wiki_page(term)
        if not page:
            continue
        other = b if term == a else a
        chosen = [p for p in page.get('paragraphs', []) if other in p]
        is_cross = bool(chosen)
        if not chosen:
            chosen = page.get('paragraphs', [])[:1]      # 退化：取第一段
        for p in chosen[:max_hits]:
            hits.append({'title': f"维基·{page.get('title', term)}", 'fragment': p[:350]})
        cross.append((term, page.get('title'), len(chosen), is_cross))
    return hits, cross


print('=' * 90)
print('一、9 个重点组合：成分词条是否真的互相提及（当前语料）')
print('=' * 90)
for t in TERMS:
    a, b = PAIR_OF[t]
    _, cross = entry_hits(a, b)
    flags = []
    for term, title, n, is_cross in cross:
        flags.append(f"{term}({title}) {'✓提及' if is_cross else '✗未提'}")
    print(f'  {t:8}  ' + '   '.join(flags))

print()
print('=' * 90)
print('二、558 -> 452 的核实：备份里那 212 条"失去命中"的，是不是抓取回退造出的假阳性')
print('=' * 90)
bms = json.loads(BMS.read_text(encoding='utf-8'))
baks = sorted((ROOT / 'out' / 'demo').glob('browser_mass_search.backup_*.json'))
if baks:
    old = json.loads(baks[-1].read_text(encoding='utf-8'))
    od = {x['term']: x for x in old}
    lost = [x['term'] for x in bms
            if od.get(x['term'], {}).get('has_entry_hits') and not x.get('has_entry_hits')]
    print(f'  失去命中 {len(lost)} 条；看其中 5 条当时命中的"段落"长什么样：')
    for t in lost[:5]:
        o = od[t]
        print(f'\n  ▶ {t}')
        for h in (o.get('entry_hits') or [])[:2]:
            print(f'     标题={h["title"]}')
            print(f'     片段={h["fragment"][:200]!r}')
    # 统计失去命中的那些，当时片段里是否含导航栏特征
    NAV = ('跳转到内容', '主菜单', '资助维基百科', '创建账号', 'Telegram', 'IRC://')
    navy = 0
    for t in lost:
        for h in (od[t].get('entry_hits') or []):
            if sum(1 for m in NAV if m in h['fragment']) >= 2:
                navy += 1
                break
    print(f'\n  失去命中的 {len(lost)} 条中，当时片段含导航栏特征的有 {navy} 条')

print()
print('=' * 90)
print('三、重算 9 个重点组合的锚点（写回 retrieve_cache_browser.json + word_understand.json）')
print('=' * 90)
cache = json.loads(CACHE.read_text(encoding='utf-8'))
wu = json.loads(WU.read_text(encoding='utf-8'))
idx = {x['term']: i for i, x in enumerate(wu)}

changed = 0
for t in TERMS:
    a, b = PAIR_OF[t]
    hits, _ = entry_hits(a, b)
    key = f'{a}×{b}'
    old_rec = cache.get(key) or {}
    cache[key] = {'query': f'{a} {b}', 'hits': hits,
                  'search': old_rec.get('search')}     # 搜索通道保持原样（Edge 抓的）
    # 重算理解
    rec = {'term': t, 'a': a, 'b': b,
           'understandings': understand(a, b, WORDS[a], WORDS[b], hits),
           'context_hits': len(hits),
           'context_query': f'{a} {b}',
           'question': question(a, b)}
    if t in idx:
        old_u = wu[idx[t]]
        if len(old_u.get('understandings') or []) != len(rec['understandings']):
            changed += 1
        wu[idx[t]] = rec
    else:
        print(f'  [警告] word_understand.json 里没有 {t}')

CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
WU.write_text(json.dumps(wu, ensure_ascii=False, indent=1), encoding='utf-8')
n_anchor = sum(1 for x in wu if '经验锚点' in json.dumps(x, ensure_ascii=False))
print(f'  写回完成；理解条目数变化 {changed}')
print(f'  word_understand.json 中带「经验锚点」的条目：{n_anchor}')

print()
for t in TERMS:
    i = idx.get(t)
    if i is None:
        continue
    x = wu[i]
    print(f'▶ {x["term"]}   (context_hits={x["context_hits"]})')
    for m in x['understandings']:
        if m.startswith('经验锚点'):
            print(f'    {m}')
    print()
