# -*- coding: utf-8 -*-
"""tools/engines/browser_mass_search.py — 全量双通道维基搜索(词条通道 + 组合词搜索通道)

对词库 82 词两两组合出的每个组合词(如「熵选择」)做双通道检索:
  A. 词条通道: a 与 b 的维基词条里, 是否提到对方(现实中两词是否有关联)。
     —— 复用 data/wiki/*.json 缓存, 本地秒回, 不开浏览器。
  B. 搜索通道: 组合词本身在维基有没有条目/是否已成词。
     —— 需要开 Edge(约 6s/组合)。

可续跑: 结果落 out/demo/browser_mass_search.json, 已完成 term 集合即进度,
重跑自动跳过。复用 retrieve_cache_browser.json 缓存, 已抓过的组合秒过。
单 Edge 驱动复用, 每 50 组合重建一次防内存泄漏。连错 N 次自动暂停, 可重启续跑。

用法:
  python browser_mass_search.py                # 全量(从断点续跑)
  python browser_mass_search.py --limit 50     # 只跑 50 个新组合(小批验证)
  python browser_mass_search.py --quick        # 只跑词条通道(本地, 不开浏览器)
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from retrieve_browser import (  # noqa: E402
    EDGE, get_driver, close_driver, load_cache, save_cache, retrieve, wiki_page,
)

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out" / "demo" / "browser_mass_search.json"
PROG = HERE / "out" / "demo" / "browser_mass_search_progress.json"
BATCH = 50          # 每批重建一次驱动
MAX_CONSEC_FAIL = 5  # 连续失败 N 次暂停(防把 Edge 打挂)


def load_done():
    if OUT.exists():
        try:
            d = json.loads(OUT.read_text(encoding="utf-8"))
            return d if isinstance(d, list) else []
        except Exception:
            return []
    return []


def save_done(done):
    OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    PROG.write_text(json.dumps([x["term"] for x in done], ensure_ascii=False), encoding="utf-8")


def make_one(term, a, b):
    """双通道检索一个组合词, 返回整理后的结果行。任何失败降级不抛。"""
    hits = []
    # A. 词条通道: 优先本地 data/wiki 缓存(不开浏览器)
    for w in (a, b):
        page = wiki_page(w)
        if not page:
            continue
        other = b if w == a else a
        chosen = [p for p in page.get("paragraphs", []) if other in p]
        if not chosen:
            continue  # 词条里没提对方 = 无关联信号, 不记
        frag = chosen[0][:220]
        hits.append({"title": f"维基·{page.get('title', w)}", "fragment": frag})
    return {"term": term, "a": a, "b": b,
            "entry_hits": hits, "has_entry_hits": bool(hits),
            "search": None}


def add_search(done_row, term):
    """B. 搜索通道: 组合词本身在维基有无条目。写回 done_row。"""
    cache = load_cache()
    key = f"{term}×search"
    if key in cache:
        r = cache[key]
    else:
        r = _search_combo_safe(term)
        cache[key] = r
        save_cache(cache)
    done_row["search"] = r


def _search_combo_safe(term):
    from urllib.parse import quote
    d = get_driver()
    d.set_page_load_timeout(25)
    d.get("https://zh.wikipedia.org/w/index.php?search=" + quote(term) + "&go=Go")
    time.sleep(1.2)
    body = d.find_element("tag name", "body").text
    title = (d.title or "").replace(" - 维基百科，自由的百科全书", "").strip()
    snippet = body[:900]
    has_entry = (title == term) and "维基百科没有这个标题" not in snippet and "找不到匹配" not in snippet
    return {"query": term, "title": title, "snippet": snippet, "has_entry": has_entry}


def _fresh_driver():
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    opts = Options()
    opts.binary_location = EDGE
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    return webdriver.Edge(service=Service(), options=opts)


def rebuild_driver(i, driver=None):
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
    for _ in range(3):
        try:
            return _fresh_driver()
        except Exception:
            time.sleep(3)
    return None


def _worker_serial(pairs_slice, shard_idx):
    """单 worker: 处理自己那批组合, 独立 Edge 驱动, 写独立分片文件。"""
    from retrieve_browser import get_driver, close_driver, load_cache, save_cache, wiki_page
    shard_file = HERE / "out" / "demo" / f"browser_mass_search_shard_{shard_idx}.json"
    done_shard = []
    if shard_file.exists():
        try:
            done_shard = json.loads(shard_file.read_text(encoding="utf-8"))
        except Exception:
            done_shard = []
    done_terms = {x["term"] for x in done_shard}
    driver = None
    consec_fail = 0
    t0 = time.time()
    for i, (a, b) in enumerate(pairs_slice):
        term = a + b
        if term in done_terms:
            continue
        if i % BATCH == 0:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass
            driver = _fresh_driver()
            if driver is None:
                print(f"[shard{shard_idx}] 驱动失败, 暂停", file=sys.stderr, flush=True)
                return
        try:
            row = make_one(term, a, b)
            # 搜索通道
            cache = load_cache()
            key = f"{term}×search"
            if key in cache:
                r = cache[key]
            else:
                r = _search_combo_safe(term)
                cache[key] = r
                save_cache(cache)
            row["search"] = r
            done_shard.append(row)
            shard_file.write_text(json.dumps(done_shard, ensure_ascii=False, indent=1), encoding="utf-8")
            consec_fail = 0
            if (i + 1) % 10 == 0:
                print(f"[shard{shard_idx}] {i+1}/{len(pairs_slice)} {term}", flush=True)
        except Exception as e:
            consec_fail += 1
            print(f"[shard{shard_idx}] {term} 失败({type(e).__name__}): {str(e)[:60]} consec={consec_fail}",
                  file=sys.stderr, flush=True)
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
            if consec_fail >= MAX_CONSEC_FAIL:
                print(f"[shard{shard_idx}] 连续失败暂停", file=sys.stderr, flush=True)
                break
            time.sleep(2)
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
    print(f"[shard{shard_idx}] 完成, 分片 {len(done_shard)} 条", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只跑 N 个新组合(0=不限)")
    ap.add_argument("--quick", action="store_true", help="只跑词条通道, 不开浏览器")
    ap.add_argument("--parallel", type=int, default=0, help="并行 worker 数(0=串行)")
    args = ap.parse_args()

    from word_understand import WORDS  # noqa: E402
    words = sorted(WORDS)
    pairs = [(a, b) for a in words for b in words if a != b]
    print(f"词库 {len(words)} 词, 两两组合 {len(pairs)} 个", flush=True)

    done = load_done()
    done_terms = {x["term"] for x in done}
    pending = [(a, b) for a, b in pairs if a + b not in done_terms]
    print(f"已完成 {len(done_terms)}, 待跑 {len(pending)}", flush=True)
    if args.limit:
        pending = pending[:args.limit]
        print(f"本批跑 {len(pending)} 个", flush=True)
    if not pending:
        print("全部完成。", flush=True)
        return

    if args.parallel > 1:
        import multiprocessing as mp
        n = min(args.parallel, len(pending))
        chunks = [pending[i::n] for i in range(n)]
        print(f"并行 {n} worker, 各分片 {[len(c) for c in chunks]} 个", flush=True)
        procs = [mp.Process(target=_worker_serial, args=(c, i), name=f"search-{i}")
                 for i, c in enumerate(chunks)]
        for p in procs:
            p.start()
        for p in procs:
            p.join()
        # 合并分片 -> 主输出文件
        merged = list(done)
        for i in range(n):
            sf = HERE / "out" / "demo" / f"browser_mass_search_shard_{i}.json"
            if sf.exists():
                merged.extend(json.loads(sf.read_text(encoding="utf-8")))
        save_done(merged)
        print(f"并行完成, 合并 {len(merged)} 条", flush=True)
        return

    driver = None
    consec_fail = 0
    t0 = time.time()
    for i, (a, b) in enumerate(pending):
        term = a + b
        if i % BATCH == 0:
            driver = rebuild_driver(i, driver)
            if driver is None:
                print("[停] 驱动启动连续失败, 已暂停", file=sys.stderr, flush=True)
                return
        try:
            row = make_one(term, a, b)
            if not args.quick:
                add_search(row, term)
            done = load_done()
            done.append(row)
            save_done(done)
            consec_fail = 0
            if (i + 1) % 20 == 0 or (i + 1) == len(pending):
                el = time.time() - t0
                rate = (i + 1) / max(el, 1)
                eta = (len(pending) - i - 1) / max(rate, 1e-9)
                s = row.get("search") or {}
                print(f"[{i+1}/{len(pending)}] {term}: 词条命中={row['has_entry_hits']} "
                      f"组合已成词={s.get('has_entry')} "
                      f"{rate:.2f}词/s ETA {eta/60:.0f}min", flush=True)
        except Exception as e:
            consec_fail += 1
            print(f"[{i+1}/{len(pending)}] {term} 失败({type(e).__name__}): "
                  f"{str(e)[:80]} consec={consec_fail}", file=sys.stderr, flush=True)
            try:
                close_driver()
            except Exception:
                pass
            driver = None
            if consec_fail >= MAX_CONSEC_FAIL:
                print("[停] 连续失败 N 次, 已暂停(可重启续跑)", file=sys.stderr, flush=True)
                return
            time.sleep(3)

    close_driver()
    n = len(load_done())
    hits = sum(1 for x in load_done() if x["has_entry_hits"])
    ents = sum(1 for x in load_done() if x.get("search") and x["search"].get("has_entry"))
    print(f"全部完成: {n} 条, 词条命中 {hits}, 组合已成词 {ents}, 用时 {(time.time()-t0)/3600:.2f}h", flush=True)


if __name__ == "__main__":
    main()
