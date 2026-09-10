# -*- coding: utf-8 -*-
"""tools/web_experience.py — 网页经验模块：随机爬取网页 -> 日常疑问 -> 科学问题

用户: "视觉可以先不做, 可以先去网页随机爬虫获取信息。"

链路: 随机抓网页文本 -> 抽疑问句(为什么/是否/如何/什么是) -> 结构化
     -> 日常疑问 -> 科学问题(带判定路由) -> 并入 discovery_manifest。

信息源: 用 urllib 抓公开页面(维基/arXiv摘要/科普), 提取文本。
"""
import html
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# 公开信息源(只抓文本/摘要, 尊重 robots)
SOURCES = [
    ("https://en.wikipedia.org/wiki/Black_hole", "天文"),
    ("https://en.wikipedia.org/wiki/Evolution", "生物"),
    ("https://en.wikipedia.org/wiki/Quantum_mechanics", "物理"),
    ("https://en.wikipedia.org/wiki/Consciousness", "心理"),
    ("https://arxiv.org/abs/2306.13282", "数学"),   # 示例论文(若有)
    ("https://en.wikipedia.org/wiki/Artificial_intelligence", "信息"),
]

# 疑问句模式(中文 + 英文 + 陈述转疑问的信号词)
Q_PAT = [
    ("为什么", r"为什么(.{4,50}?)[？?]"),
    ("是否", r"是否(.{4,50}?)[？?]"),
    ("如何", r"如何(.{4,50}?)[？?]"),
    ("what", r"[Ww]hy(.{4,60}?)[?]"),
    ("how", r"[Hh]ow(.{4,60}?)[?]"),
    ("whether", r"[Ww]hether(.{4,60}?)[?]"),
    ("what-is", r"[Ww]hat is(.{4,60}?)[?]"),
]

# 陈述里的"因果/未知"信号 -> 转成疑问(从信息里挖问题)
CAUSE_PAT = [
    ("归因", r"([^。.]{10,60}(?:因为|由于|导致|归因于)[^。.]{5,40})"),
    ("未知", r"([^。.]{10,60}(?:unknown|not known|not understood|unexplained|mystery)[^。.]{5,40})"),
    ("因果", r"([^.]{10,60}(?:causes?|leads to|results from|due to)[^.]{5,40})"),
]

# 科学化路由(按领域)
ROUTE = {
    "天文": "观测+物理建模", "生物": "实验+系谱证据", "物理": "理论+实验",
    "心理": "实验设计", "数学": "数值+证明", "信息": "计算+统计",
}


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read().decode("utf-8", errors="ignore")
    # 粗提取文本: 去标签/去脚本
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", data, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text)


def mine(text):
    qs = []
    # 直接疑问句
    for qtype, pat in Q_PAT:
        for m in re.finditer(pat, text):
            frag = m.group(1).strip()
            if 4 <= len(frag) <= 60:
                qs.append((qtype, frag))
    # 陈述里的因果/未知 -> 转疑问
    for ctype, pat in CAUSE_PAT:
        for m in re.finditer(pat, text):
            frag = m.group(1).strip()
            if 10 <= len(frag) <= 80:
                qs.append((f"{ctype}:", f"这段陈述('{frag[:40]}…')的机制/原因是什么?"))
    # 去重
    seen, out = set(), []
    for qtype, frag in qs:
        if frag not in seen:
            seen.add(frag)
            out.append((qtype, frag))
    return out[:10]


def main():
    print("=" * 100)
    print("网页经验模块 —— 随机爬取 -> 日常疑问 -> 科学问题")
    print("=" * 100)
    all_q = []
    for url, dom in SOURCES:
        try:
            text = fetch(url)
            print(f"\n  [{dom}] {url}")
            print(f"    抓取 {len(text)} 字符")
            qs = mine(text)
            print(f"    抽到 {len(qs)} 条疑问:")
            for qtype, frag in qs[:4]:
                print(f"      [{qtype}] {frag[:60]}")
                all_q.append({"source": url, "domain": dom,
                              "daily_question": f"{qtype}{frag}?",
                              "scientific_question": f"在{dom}中, '{frag}' 的机制/结构是什么?",
                              "judge_route": ROUTE.get(dom, "待定"),
                              "status": "待判定"})
        except Exception as e:
            print(f"    !! 抓取失败: {e}")
        time.sleep(1)

    print(f"\n  共产生 {len(all_q)} 条网页->科学问题")

    # 并入 manifest
    man = HERE / "out/demo/discovery_manifest.json"
    if man.exists():
        d = json.loads(man.read_text(encoding="utf-8"))
        d["problems"] += all_q
        d["count"] = len(d["problems"])
        man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  已并入 discovery_manifest (总数 {d['count']})")

    (HERE / "out/demo/web_experience.json").write_text(
        json.dumps(all_q, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  已存 out/demo/web_experience.json")
    print("\n诚实: 这些是网页随机抓取 -> 日常疑问 -> 粗科学化; 判定路由是粗粒度;")
    print("  下一步: 把'日常疑问'用 grammar 框架精确定型(接问题生成器)。")


if __name__ == "__main__":
    main()
