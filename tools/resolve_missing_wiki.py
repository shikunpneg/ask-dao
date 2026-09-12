# -*- coding: utf-8 -*-
"""补齐维基里没有同名条目的词：用搜索 API 解析到最相关条目标题，再抓正文。

例：临界 -> 临界点 / 临界现象；纠缠 -> 量子纠缠；递推 -> 递推关系；
    可判定 -> 判定问题；键合 -> 化学键；对位 -> 对位法；语用 -> 语用学。

解析结果写进 JSON 的 title 字段（桥的锚点标题会显示「维基·<真实条目标题>」），
并额外记 resolved_from，保证可追溯：抓的不是同名条目这件事是透明的。
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r'E:\ask-dao\ask-dao-machine')
WIKI = ROOT / 'data' / 'wiki'
API = 'https://zh.wikipedia.org/w/api.php'
UA = 'ask-dao-machine/0.5 (wiki corpus refresh; https://github.com/shikunpneg/ask-dao)'

TARGETS = ['不变量', '临界', '公设', '压缩', '可判定', '增长', '守恒', '对位',
           '纠缠', '表现', '语用', '适应性', '递推', '键合', '风格']


def _get(params, tries=4):
    params = dict(params)
    params.setdefault('format', 'json')
    params.setdefault('formatversion', '2')
    url = f'{API}?{urllib.parse.urlencode(params)}'
    wait = 2.0
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < tries - 1:
                time.sleep(wait)
                wait *= 2.5
                continue
            return None
        except Exception:
            if a < tries - 1:
                time.sleep(wait)
                wait *= 2.0
                continue
            return None
    return None


def search_title(term, limit=6):
    d = _get({'action': 'query', 'list': 'search', 'srsearch': term,
              'srlimit': str(limit), 'srnamespace': '0'})
    if not d:
        return []
    return [(h['title'], h.get('size', 0)) for h in (d.get('query') or {}).get('search', [])]


def extract(title):
    d = _get({'action': 'query', 'prop': 'extracts', 'explaintext': '1',
              'redirects': '1', 'exlimit': '1', 'titles': title})
    pages = (d.get('query') or {}).get('pages') if d else None
    if not pages:
        return None
    p = pages[0]
    if p.get('missing'):
        return None
    text = p.get('extract') or ''
    paras = [x.strip() for x in text.split('\n') if len(x.strip()) > 15]
    if not paras:
        return None
    return (p.get('title') or title, paras[:20])


def main():
    print(f'待补齐 {len(TARGETS)} 个\n')
    fixed = []
    still = []
    for i, term in enumerate(TARGETS, 1):
        cands = search_title(term)
        print(f'[{i}/{len(TARGETS)}] {term}')
        print('    候选: ' + ' | '.join(f'{t}({s}B)' for t, s in cands[:5]))
        got = None
        for title, _sz in cands:
            r = extract(title)
            if r:
                got = r
                break
            time.sleep(0.4)
        if got:
            title, paras = got
            rec = {'term': term, 'title': title,
                   'url': 'https://zh.wikipedia.org/wiki/' + urllib.parse.quote(title),
                   'paragraphs': paras, 'raw': '\n\n'.join(paras[:10]),
                   'source': 'mediawiki-api-search', 'resolved_from': term}
            (WIKI / f'{term}.json').write_text(
                json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
            fixed.append((term, title, len(paras)))
            print(f'    -> 采用 [{title}]  {len(paras)} 段')
        else:
            still.append((term, 'no extract'))
            print('    -> 仍无正文')
        time.sleep(1.0)

    print()
    print(f'补齐 {len(fixed)} 个 · 仍缺 {len(still)} 个')
    for t, ti, n in fixed:
        print(f'   {t:6} -> {ti:20} {n:>2} 段')
    if still:
        print('仍缺：', [t for t, _ in still])

    # 统计
    tot_p = tot_c = clean = 0
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
        head = (ps[0] if ps else '')[:400]
        if ps and sum(1 for m in ('跳转到内容', '主菜单', '资助维基百科', '创建账号',
                                  '维基百科志愿者', 'Telegram', 'IRC://')
                      if m in head) < 2:
            clean += 1
        tot_p += len(ps)
        tot_c += sum(len(x) for x in ps)
    print()
    print(f'语料现状：{n} 词条 · 干净 {clean} · 段落 {tot_p} · 字符 {tot_c:,}')


if __name__ == '__main__':
    main()
