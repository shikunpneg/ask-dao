# -*- coding: utf-8 -*-
"""修正搜索 API 挑偏的 4 个词条（人工指定正确条目标题）。

搜索 API 按相关性排序，对「临界/适应性/不变量/风格」挑出了语义不对的条目
（核临界事故 / 免疫系统 / 绝热不变量 / 代码风格）。这里人工指定正确条目，
仍走 API 抓正文，并记 resolved_from 保证可追溯。
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r'E:\ask-dao\ask-dao-machine')
WIKI = ROOT / 'data' / 'wiki'
API = 'https://zh.wikipedia.org/w/api.php'
UA = 'ask-dao-machine/0.5 (wiki corpus; contact via repo)'

# 词 -> 优先尝试的条目标题（按顺序）
FIX = {
    '临界':   ['临界点 (热力学)', '临界点', '临界现象', '相变'],
    '适应性': ['适应 (生物学)', '适应', '适应度', '演化'],
    '不变量': ['不變量 (數學)', '不变量 (数学)', '不變量', '守恒定律'],
    '风格':   ['艺术风格', '風格 (藝術)', '音乐风格', '建筑风格'],
}


def get(params, tries=3):
    p = dict(params, format='json', formatversion='2')
    url = f'{API}?{urllib.parse.urlencode(p)}'
    wait = 2.0
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < tries - 1:
                time.sleep(wait); wait *= 2.5; continue
            return None
        except Exception:
            if a < tries - 1:
                time.sleep(wait); wait *= 2.0; continue
            return None
    return None


def extract(title):
    d = get({'action': 'query', 'prop': 'extracts', 'explaintext': '1',
             'redirects': '1', 'exlimit': '1', 'titles': title})
    pages = (d.get('query') or {}).get('pages') if d else None
    if not pages:
        return None
    p = pages[0]
    if p.get('missing'):
        return None
    text = p.get('extract') or ''
    paras = [x.strip() for x in text.split('\n') if len(x.strip()) > 15]
    return (p.get('title') or title, paras[:20]) if paras else None


for term, titles in FIX.items():
    old = None
    fp = WIKI / f'{term}.json'
    if fp.exists():
        try:
            old = json.loads(fp.read_text(encoding='utf-8'))
        except Exception:
            old = None
    print(f'\n{term}   (原为: {old.get("title") if old else "?"})')
    done = False
    for t in titles:
        r = extract(t)
        if r:
            title, paras = r
            rec = {'term': term, 'title': title,
                   'url': 'https://zh.wikipedia.org/wiki/' + urllib.parse.quote(title),
                   'paragraphs': paras, 'raw': '\n\n'.join(paras[:10]),
                   'source': 'mediawiki-api-manual', 'resolved_from': term}
            fp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
            print(f'   -> [{title}]  {len(paras)} 段  OK')
            done = True
            break
        print(f'   x  {t}: 无正文/不存在')
        time.sleep(0.5)
    if not done:
        print('   !! 全部候选都失败，保留原样')
    time.sleep(1.0)

# 统计
tot_p = tot_c = 0
n = 0
for f in WIKI.glob('*.json'):
    if f.name == '_failed.json':
        continue
    n += 1
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        continue
    ps = d.get('paragraphs') or []
    tot_p += len(ps)
    tot_c += sum(len(x) for x in ps)
print(f'\n语料：{n} 词条 · 段落 {tot_p} · 字符 {tot_c:,}')
print('\n四词现状：')
for term in FIX:
    d = json.loads((WIKI / f'{term}.json').read_text(encoding='utf-8'))
    ps = d.get('paragraphs') or []
    print(f'   {term:6} -> {d.get("title"):16} {len(ps):>2} 段  {ps[0][:70] if ps else ""}')
