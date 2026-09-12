# -*- coding: utf-8 -*-
"""tools/core/retrieve_browser.py — 浏览器检索器(selenium + Edge) for 想象模块方案2

经验文本源 = 中文维基百科。双通道:
  A. 词条通道: 打开 a 和 b 的百科条目, 提取含另一词的段落作 M7 经验锚点。
     优先读本地 data/wiki/{term}.json(fetch_wiki.py 抓好的词条), 没有才开 Edge 抓。
  B. 搜索通道: 对组合词 a×b 本身在维基搜一次, 看这个"组合词"在现实中是否已有
     所指(有词条/被提及), 作为组合是否"已成词"的经验信号。

单 Edge 驱动复用(打开一次, 全程复用), 结果落 out/demo/retrieve_cache_browser.json。
网络/驱动失败一律降级到本地缓存, 不让想象模块被打断。

用法: python retrieve_browser.py 熵 选择
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CACHE_FILE = HERE / "out" / "demo" / "retrieve_cache_browser.json"
WIKI_DIR = HERE / "data" / "wiki"

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

_driver_singleton = None


def get_driver():
    global _driver_singleton
    if _driver_singleton is None:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.edge.service import Service
        opts = Options()
        opts.binary_location = EDGE
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        _driver_singleton = webdriver.Edge(service=Service(), options=opts)
    return _driver_singleton


def close_driver():
    global _driver_singleton
    if _driver_singleton is not None:
        try:
            _driver_singleton.quit()
        except Exception:
            pass
        _driver_singleton = None


def _wiki_page_via_driver(term):
    """开 Edge 抓中文维基词条正文。失败返回 None。"""
    from urllib.parse import quote
    d = get_driver()
    d.set_page_load_timeout(25)
    d.get("https://zh.wikipedia.org/wiki/" + quote(term))
    time.sleep(1.5)
    title = d.title.replace(" - 维基百科，自由的百科全书", "").strip()
    paras = d.find_elements("css selector", "div.mw-parser-output > p")
    texts = [p.text.strip() for p in paras if len(p.text.strip()) > 15]
    if not texts:
        body = d.find_element("tag name", "body").text
        texts = [body[:600]]
    return {"term": term, "title": title, "paragraphs": texts[:10]}


def wiki_page(term, retries=1):
    """词条通道: 优先本地缓存, 没有才开 Edge。失败返回 None(不抛)。"""
    local = WIKI_DIR / f"{term}.json"
    if local.exists():
        try:
            return json.loads(local.read_text(encoding="utf-8"))
        except Exception:
            pass
    for attempt in range(retries + 1):
        try:
            return _wiki_page_via_driver(term)
        except Exception as e:
            if attempt >= retries:
                print(f"[browser] {term} 词条抓取失败: {type(e).__name__}", file=sys.stderr)
                return None
            time.sleep(2)
            try:
                close_driver()
            except Exception:
                pass
    return None


def _search_combo(term):
    """搜索通道: 对组合词 term 在维基搜一次, 返回该组合在现实中是否已成词。"""
    from urllib.parse import quote
    d = get_driver()
    d.set_page_load_timeout(25)
    d.get("https://zh.wikipedia.org/w/index.php?search=" + quote(term) + "&go=Go")
    time.sleep(1.2)
    body = d.find_element("tag name", "body").text
    title = (d.title or "").replace(" - 维基百科，自由的百科全书", "").strip()
    snippet = body[:900]
    # 是组合词条本身(标题=组合词且非"未找到/结果")才算"已成词"
    has_entry = (title == term) and "维基百科没有这个标题" not in snippet and "找不到匹配" not in snippet
    return {"query": term, "title": title, "snippet": snippet, "has_entry": has_entry}


def retrieve(a, b, max_hits=2):
    """对 a×b 检索维基, 返回 {"query", "hits", "search"}。双通道全部落结果。"""
    hits = []
    for term in (a, b):
        page = wiki_page(term)
        if not page:
            continue
        other = b if term == a else a
        chosen = [p for p in page.get("paragraphs", []) if other in p]
        if not chosen:
            chosen = page.get("paragraphs", [])[:1]
        for p in chosen[:max_hits]:
            frag = p[:350]
            hits.append({"title": f"维基·{page.get('title', term)}", "fragment": frag})

    search = None
    try:
        search = _search_combo(a + b)
    except Exception as e:
        print(f"[browser] 组合搜索 {a+b} 失败: {type(e).__name__}", file=sys.stderr)

    return {"query": f"{a} {b}", "hits": hits, "search": search}


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def retrieve_cached(a, b):
    key = f"{a}×{b}"
    cache = load_cache()
    if key in cache:
        return cache[key]
    r = retrieve(a, b)
    cache[key] = r
    save_cache(cache)
    return r


if __name__ == "__main__":
    args = sys.argv[1:]
    a, b = (args[0], args[1]) if len(args) >= 2 else ("熵", "选择")
    try:
        r = retrieve_cached(a, b)
        print(f"query: {r['query']}, hits: {len(r['hits'])}")
        for h in r["hits"]:
            print("-", h["title"][:50])
            print("  ", h["fragment"][:150])
        s = r.get("search")
        if s:
            print(f"search: 组合词「{s['query']}」已成词? {s['has_entry']} | 标题={s['title'][:40]!r}")
    finally:
        close_driver()
