# -*- coding: utf-8 -*-
"""重抓 82 词条正文（MediaWiki API，纯 HTTP）。

修复 tools/fetch_wiki.py 的抓取缺陷：它走 Edge 抓 DOM，某些条目拿不到
div.mw-parser-output > p，就回退成整页 body 文本，把侧边栏导航当成了正文。
这里用官方 API 的 prop=extracts&explaintext 拿纯正文。

礼貌抓取：每请求 1s 间隔；429/5xx 指数退避；只在拿到合格正文时才覆盖。
原语料已有备份 data/wiki_backup_*。
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

NAV_MARKERS = ('跳转到内容', '主菜单', '资助维基百科', '创建账号', '个人工具', '开关目录',
               '维基百科志愿者', 'Facebook粉丝专页', 'IRC://', 'Telegram', '添加语言')


def is_garbage(paras):
    if not paras:
        return True
    head = (paras[0] or '')[:400]
    return sum(1 for m in NAV_MARKERS if m in head) >= 2


def fetch(term, tries=4):
    q = urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'formatversion': '2',
        'prop': 'extracts', 'explaintext': '1', 'redirects': '1',
        'exlimit': '1', 'titles': term,
    })
    url = f'{API}?{q}'
    wait = 2.0
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode('utf-8'))
            pages = (d.get('query') or {}).get('pages') or []
            if not pages:
                return ('NOPAGE', '', [])
            p = pages[0]
            if p.get('missing'):
                return ('MISSING', p.get('title') or term, [])
            title = p.get('title') or term
            text = p.get('extract') or ''
            paras = [x.strip() for x in text.split('\n') if len(x.strip()) > 15]
            if not paras:
                return ('EMPTY', title, [])
            return ('OK', title, paras[:20])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < tries - 1:
                print(f'    [{e.code}] 退避 {wait:.0f}s …', flush=True)
                time.sleep(wait)
                wait *= 2.5
                continue
            return ('HTTP%d' % e.code, '', [])
        except Exception as e:
            if a < tries - 1:
                time.sleep(wait)
                wait *= 2.0
                continue
            return ('ERR:' + type(e).__name__, '', [])
    return ('RETRY_EXHAUSTED', '', [])


def main():
    sys.path.insert(0, str(ROOT / 'tools'))
    from word_understand import WORDS  # noqa: E402
    terms = sorted(WORDS)

    need = []
    for t in terms:
        p = WIKI / f'{t}.json'
        cur = None
        if p.exists():
            try:
                cur = json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                cur = None
        if cur is None or cur.get('source') != 'mediawiki-api' or is_garbage(cur.get('paragraphs') or []):
            need.append(t)

    print(f'词表 {len(terms)} 词；需要重抓 {len(need)} 个（其余已是 API 正文）', flush=True)
    print()

    ok = miss = empty = bad = 0
    fixed = []
    still = []
    for i, t in enumerate(need, 1):
        p = WIKI / f'{t}.json'
        old = None
        if p.exists():
            try:
                old = json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                old = None
        was_bad = old is None or old.get('source') != 'mediawiki-api' or is_garbage(old.get('paragraphs') or [])

        st, title, paras = fetch(t)
        if st == 'OK':
            rec = {'term': t, 'title': title,
                   'url': 'https://zh.wikipedia.org/wiki/' + urllib.parse.quote(t),
                   'paragraphs': paras, 'raw': '\n\n'.join(paras[:10]),
                   'source': 'mediawiki-api'}
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
            ok += 1
            if was_bad:
                fixed.append((t, len(paras), title))
            print(f'  [{i}/{len(need)}] {t}: {len(paras)} 段  {title}', flush=True)
        else:
            if st == 'MISSING':
                miss += 1
            elif st == 'EMPTY':
                empty += 1
            else:
                bad += 1
            still.append((t, st))
            print(f'  [{i}/{len(need)}] {t}: [{st}]', flush=True)

        time.sleep(1.0)

    print()
    print(f'成功 {ok} · 页面缺失 {miss} · 无正文 {empty} · 请求失败 {bad}')
    print()
    print(f'=== 修好的（原先是外壳/未抓）{len(fixed)} 个 ===')
    for t, n, ti in fixed:
        print(f'   {t:6} {n:>2} 段  {ti}')
    if still:
        print()
        print(f'=== 仍异常 {len(still)} 个 ===')
        for t, s in still:
            print(f'   {t:6} [{s}]')

    # 现行统计
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
        if not is_garbage(ps):
            clean += 1
        tot_p += len(ps)
        tot_c += sum(len(x) for x in ps)
    print()
    print(f'语料现状：{n} 词条 · 干净 {clean} · 段落 {tot_p} · 字符 {tot_c:,}')


if __name__ == '__main__':
    main()
