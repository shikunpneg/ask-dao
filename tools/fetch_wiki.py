# -*- coding: utf-8 -*-
"""tools/fetch_wiki.py — 抓取词库 82 词的维基百科词条正文, 每词一个 JSON 文件

用 Edge 无头浏览器打开中文维基词条, 抓正文段落, 存到 data/wiki/{term}.json
(含 term/title/url/paragraphs/raw)。断点续跑: 已存在的词条跳过。
失败重试, 重试仍失败记录到 data/wiki/_failed.json(不阻塞)。
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from word_understand import WORDS  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
WIKI_DIR = HERE / "data" / "wiki"
FAILED = WIKI_DIR / "_failed.json"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def make_driver():
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    opts = Options()
    opts.binary_location = EDGE
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    return webdriver.Edge(service=Service(), options=opts)


def fetch_term(driver, term):
    """打开词条页, 抓正文段落。无词条时返回 title 含 '维基百科' 搜索页标记。"""
    from urllib.parse import quote
    url = "https://zh.wikipedia.org/wiki/" + quote(term)
    driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(2)
    title = driver.title.replace(" - 维基百科，自由的百科全书", "").strip()
    # 正文段落: div.mw-parser-output > p
    paras = driver.find_elements("css selector", "div.mw-parser-output > p")
    texts = [p.text.strip() for p in paras if len(p.text.strip()) > 15]
    # 若无正文段落(可能是消歧/空), 取主 body 文本
    if not texts:
        body = driver.find_element("tag name", "body").text
        texts = [body[:800]]
    return {"term": term, "title": title, "url": url,
            "paragraphs": texts[:20], "raw": "\n\n".join(texts[:10])}


def load_failed():
    if FAILED.exists():
        try:
            return json.loads(FAILED.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_failed(f):
    FAILED.write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    words = sorted(WORDS)
    done = {p.stem for p in WIKI_DIR.glob("*.json") if p.stem != "_failed"}
    pending = [w for w in words if w not in done]
    print(f"词库 {len(words)} 词; 已完成 {len(done)}; 待抓 {len(pending)}", flush=True)
    if not pending:
        print("全部已抓取。", flush=True)
        return

    failed = load_failed()
    driver = None
    for i, term in enumerate(pending):
        # 每 25 词重建 driver(防内存泄漏/tab崩溃)
        if driver is None or i % 25 == 0:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            for _ in range(3):
                try:
                    driver = make_driver()
                    break
                except Exception as e:
                    print(f"[init] driver 失败: {e}", file=sys.stderr, flush=True)
                    time.sleep(3)
            else:
                print("[init] 连续失败, 退出", flush=True)
                break
        ok = False
        for attempt in range(3):
            try:
                r = fetch_term(driver, term)
                # 判断是否真有词条(标题若是组合词本身且有正文=有条目; 否则是搜索页)
                (WIKI_DIR / f"{term}.json").write_text(
                    json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
                ok = True
                if (i + 1) % 10 == 0:
                    print(f"[{i+1}/{len(pending)}] {term}: 段落{len(r['paragraphs'])} "
                          f"标题={r['title'][:25]!r}", flush=True)
                break
            except Exception as e:
                print(f"[{i+1}/{len(pending)}] {term} 失败({attempt+1}/3): "
                      f"{type(e).__name__} {str(e)[:70]}", file=sys.stderr, flush=True)
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None
                time.sleep(3)
                for _ in range(3):
                    try:
                        driver = make_driver()
                        break
                    except Exception:
                        time.sleep(3)
        if not ok:
            failed.append(term)
            save_failed(failed)
            print(f"[记] {term} 抓取失败, 已记入 _failed.json", flush=True)

    print(f"完成。成功 {len(WIKI_DIR.glob('*.json'))-1} 个, 失败 {len(load_failed())} 个", flush=True)


if __name__ == "__main__":
    main()
