# -*- coding: utf-8 -*-
"""tools/research/tension_detector.py — 语料张力探测器 v0 (PLAN_TENSION_DETECTOR)
对每对'概念两极关键词组', 在同一文本中同时命中两极 -> 张力候选(裂缝位置)。
局限: 关键词启发, 命中≠真矛盾; 需语义复核; v0 筛'候选裂缝'。"""
import re
from pathlib import Path

TEXT = Path(r"E:\ask-dao\_text")

# 概念对: (概念名, 极A关键词, 极B关键词)
PAIRS = [
    ("知行关系", ["知先行后", "知难行易", "先知后行"], ["行易知难", "行先知后", "不知亦能行", "知行合一", "知以行为功"]),
    ("求理路径(朱陆)", ["即物穷理", "格物致知", "今日格一物", "铢积寸累"], ["心即理", "致良知", "先立其大者", "六经注我"]),
    ("性善/性恶", ["性善", "恻隐之心"], ["性恶", "化性起伪"]),
    ("言意之辨", ["得意忘象", "言不尽意", "得意忘言"], ["言尽意", "名逐物而迁"]),
    ("天人之分/感应", ["天人感应", "同类相动", "人副天数"], ["明于天人之分", "天行有常", "天人交相胜"]),
    ("有无之辨", ["贵无", "以无为本"], ["崇有", "无不能生有"]),
    ("理气先后", ["理先于气", "理在气先"], ["理在气中", "理只是气之理", "气外无理"]),
    ("顿渐之争", ["顿悟", "一闻言下便悟", "见性成佛"], ["渐修", "积习既久", "豁然贯通"]),
    ("名实观", ["名教", "以名定是非", "事各顺于名"], ["稽实定数", "名无固宜", "约定俗成", "循名责实"]),
    ("知行来源", ["生而知之", "良知良能"], ["学而知之", "困而学之", "不学自知"]),
]

FILES = [
    "中国哲学史第2版.md",
    "哲学100问_套装共3册_零基础哲学入门读物_一部深邃_古典_诗意_浪漫的极简西方哲学史_喜马拉雅超红的哲学课_全网已突破5000000次播放量_z_library_sk_1lib_sk_z_lib_sk_.md",
    "handbook\\07_一般科学哲学_焦点主题.md",
]


def scan(pair_file, pair_idx):
    fname, (topic, a, b) = pair_file
    raw = (TEXT / fname).read_text(encoding="utf-8", errors="ignore")
    lines = raw.splitlines()
    res = []
    for ln, line in enumerate(lines):
        if len(line) < 4 or line.startswith("#"):
            continue
        ha = any(t in line for t in a)
        hb = any(t in line for t in b)
        if ha and hb:
            res.append((ln, re.sub(r"\s+", " ", line)[:160]))
    return res


def main():
    out = {}
    total = 0
    for fname in FILES:
        for pi, pair in enumerate(PAIRS):
            hits = scan((fname, pair), pi)
            if hits:
                total += len(hits)
                key = f"{pair[0]} @ {fname[:18]}"
                out[key] = hits[:6]
    for k, v in out.items():
        print(f"== {k} : {len(v)} 命中(显示前{len(v)})")
        for ln, s in v:
            print(f"   L{ln}: {s}")
    Path("out/demo/tensions_v0.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/tensions_v0.json").write_text(
        __import__("json").dumps({k: v for k, v in out.items()}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("总命中:", total)


if __name__ == "__main__":
    main()
