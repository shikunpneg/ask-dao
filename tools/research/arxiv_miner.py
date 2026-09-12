# -*- coding: utf-8 -*-
"""tools/research/arxiv_miner.py — arXiv 前沿摘要挖掘：从最新论文里挖"开放/未知/新问题"（R56）

目标(用户): 跑出新问题、新知识。
来源: arXiv API(公开, 批量取最新论文摘要) —— 这是**前沿知识**流, 比维基更"新"。

方法:
  1. 抓取若干主题(cs.AI/physics/astro-ph/math/q-bio)的最新论文摘要
  2. 挖"开放问题/未知/挑战/未被解决/需要/尚不明确"等信号
  3. 每条 -> 科学问题(带主题域 + 判定路由)
  4. 并入 discovery_manifest
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

TOPICS = {
    "cs.AI": "人工智能", "physics": "物理", "astro-ph": "天文",
    "math": "数学", "q-bio": "生物", "cs.LG": "机器学习",
}

OPEN_SIG = [
    r"(remains|remain|still)\s+(open|unknown|unresolved|unclear|challenging)",
    r"(open|unsolved|unresolved)\s+(problem|question|issue)",
    r"(not yet|has not been|is not)\s+(understood|solved|known|explained)",
    r"unknown\s+(whether|how|why|what)",
    r"(future work|future direction|further research)",
    r"有待|尚不明确|未解决|仍是一个挑战",
]

# 判定路由(按主题)
ROUTE = {
    "人工智能": "实验/基准", "物理": "理论+实验", "天文": "观测",
    "数学": "数值+证明", "生物": "实验+数据", "机器学习": "实验+理论",
}


def fetch_arxiv(topic, n=40, retries=3):
    """arXiv API: 按主题取最新论文标题+摘要(带重试)。"""
    url = ("http://export.arxiv.org/api/query?" +
           urllib.parse.urlencode({"search_query": f"cat:{topic}",
                                   "sortBy": "submittedDate", "sortOrder": "descending",
                                   "max_results": n}))
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                xml = r.read().decode("utf-8", errors="ignore")
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml)
            out = []
            for e in root.findall("a:entry", ns):
                title = (e.findtext("a:title", "", ns) or "").replace("\n", " ").strip()
                summ = (e.findtext("a:summary", "", ns) or "").replace("\n", " ").strip()
                out.append({"title": title, "abstract": summ})
            return out
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def mine_paper(p, topic, dom):
    """从论文标题+摘要挖开放信号 -> 科学问题。"""
    text = p["title"] + " " + p["abstract"]
    hits = [m.group(0) for m in re.finditer(OPEN_SIG[0] + "|" + OPEN_SIG[1] + "|" +
                                            OPEN_SIG[2] + "|" + OPEN_SIG[3] + "|" + OPEN_SIG[4],
                                            text, re.I)]
    if not hits:
        return []
    qs = []
    for h in hits[:2]:
        # 提取命中词附近的句子(±80字符)
        m = re.search(re.escape(h[:20]), text, re.I)
        s = max(0, m.start() - 60)
        e = min(len(text), m.end() + 60)
        ctx = text[s:e].strip()
        qs.append({
            "source": f"arxiv:{topic}", "domain": dom, "title": p["title"][:80],
            "open_signal": h[:40], "context": ctx,
            "scientific_question": f"[{dom}] 论文「{p['title'][:40]}」提及的开放点: "
                                   f"'{ctx[:60]}' — 该问题的精确刻画与解法?",
            "judge_route": ROUTE.get(dom, "待定"), "status": "待判定",
        })
    return qs


def main():
    print("=" * 100)
    print("arXiv 前沿摘要挖掘 —— 从最新论文挖'开放/未知'信号")
    print("=" * 100)
    all_q = []
    for topic, dom in TOPICS.items():
        try:
            papers = fetch_arxiv(topic)
            print(f"\n  [{dom}] {topic}: 抓到 {len(papers)} 篇最新论文")
            nq = 0
            for p in papers:
                qs = mine_paper(p, topic, dom)
                all_q += qs
                nq += len(qs)
            print(f"    挖到 {nq} 条开放问题信号")
        except Exception as e:
            print(f"    !! 失败: {e}")
        time.sleep(2)

    print(f"\n  共挖到 {len(all_q)} 条 arXiv 前沿问题")
    print(f"\n  按领域: {dict(Counter(q['domain'] for q in all_q))}")
    print(f"\n  样本:")
    for q in all_q[:8]:
        print(f"    [{q['domain']}] {q['scientific_question'][:100]}")

    # 并入 manifest
    man = HERE / "out/demo/discovery_manifest.json"
    d = json.loads(man.read_text(encoding="utf-8"))
    start = len([p for p in d["problems"] if str(p.get("id", "")).startswith("ARX")])
    d["problems"] += [{**q, "id": f"ARX_{start+i}"} for i, q in enumerate(all_q)]
    d["count"] = len(d["problems"])
    man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "out/demo/arxiv_miner.json").write_text(
        json.dumps(all_q, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  已并入 discovery_manifest (总数 {d['count']})")
    print("  已存 out/demo/arxiv_miner.json")
    print("\n诚实: 挖到的是论文**自己标记的开放点**(作者说'open/unresolved'), 是前沿裂缝;")
    print("  每条可复核(指向具体论文); 判定路由是粗粒度, 需精化。")


if __name__ == "__main__":
    main()
