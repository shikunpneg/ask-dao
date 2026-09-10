# -*- coding: utf-8 -*-
"""tools/tension_hist.py — 科学史语料的张力探测(用户: 别只做哲学)

把张力探测器从"中国哲学史"扩展到**科学史/科学哲学/科普**语料:
用科学史里的经典对峙(两套框架冲突)作为概念对, 在科学史文本里扫。
科学史的对峙才是"分歧中生新问题"的源头 —— 每次科学革命都是一次张力解决。
"""
import json
import re
from collections import Counter
from pathlib import Path

TEXT = Path(r"E:\ask-dao\_text")
FILES = ["histmath.md", "histphys.md", "milestones.md", "kuhn_structure.md",
         "popper_conjectures.md", "popper_logic.md", "strevens_knowledge.md", "whys.md"]

# 科学史经典对峙(两套框架/范式之间的张力)
PAIRS = [
    ("地心说 vs 日心说", ["地心", "托勒密"], ["日心", "哥白尼"]),
    ("本轮 vs 椭圆", ["本轮", "均轮"], ["椭圆", "开普勒"]),
    ("连续 vs 离散(光)", ["波动", "波", "连续"], ["微粒", "光子", "离散"]),
    ("燃素 vs 氧化", ["燃素"], ["氧化", "氧"]),
    ("活力 vs 能量", ["活力", "vis viva"], ["能量守恒", "热功当量"]),
    ("热质 vs 分子运动", ["热质"], ["分子运动", "统计力学"]),
    ("绝对空间 vs 相对论", ["绝对空间", "绝对时间", "以太"], ["相对论", "闵可夫斯基"]),
    ("决定论 vs 量子", ["决定论", "拉普拉斯妖"], ["不确定性", "量子力学", "波函数"]),
    ("归纳 vs 证伪", ["归纳", "确证"], ["证伪", "反例", "可检验性"]),
    ("范式累积 vs 范式革命", ["累积", "常规科学"], ["革命", "范式转换"]),
    ("还原论 vs 整体论", ["还原", "基本粒子"], ["整体", "涌现"]),
    ("突变 vs 渐变(演化)", ["突变", "大爆炸"], ["渐变", "均变", "进化"]),
]

# 科学史元模式: 该张力如何解决 -> 是否产生了新问题
M_PAT = [
    ("M6 悖论", r"矛盾|不一致|不相容|悖论"),
    ("M2 异常", r"异常|反例|不符合|无法解释|不能说明|观测到.*无法"),
    ("M1 统一", r"统一|同源|合并|综合|结合|等价"),
    ("M3 公设被挑战", r"推翻|质疑|挑战|放弃|替代|革命"),
    ("M0 无模式", None),
]

CONFRONT = re.compile(r"vs|对|争论|争论|争议|挑战|反对|批判|取代|替代|区分|两种")


def main():
    out = []
    for fname in FILES:
        f = TEXT / fname
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        paras = re.split(r"\n\s*\n", text)
        for topic, a, b in PAIRS:
            for pi, para in enumerate(paras):
                if len(para) < 60 or para.startswith("#"):
                    continue
                ha = [t for t in a if t in para]
                hb = [t for t in b if t in para]
                if ha and hb:
                    Ms = [m for m, p in M_PAT if p and re.search(p, para)]
                    if not Ms:
                        Ms = ["M0 无模式"]
                    out.append({"topic": topic, "file": fname, "para": pi,
                                "A": ha[:2], "B": hb[:2], "M": Ms,
                                "excerpt": re.sub(r"\s+", " ", para)[:220]})
    print("=" * 100)
    print("科学史语料张力探测(非哲学)")
    print("=" * 100)
    print(f"  扫描 {len(FILES)} 个文件, 命中张力候选 **{len(out)}**")
    print(f"\n  按主题:")
    for t, n in Counter(o["topic"] for o in out).items():
        print(f"    {t:<20}{n}")
    print(f"\n  按 M 模式:")
    mc = Counter(m for o in out for m in o["M"])
    print(f"    {dict(mc)}")
    print("\n  == 带 M2 异常 / M6 悖论 的候选(最像新问题前身) ==")
    interesting = [o for o in out if any("M2" in m or "M6" in m for m in o["M"])]
    for o in interesting[:10]:
        print(f"\n  [{','.join(o['M'])}] {o['topic']} @{o['file']}:{o['para']}")
        print(f"      {o['excerpt'][:160]}")
    print("\n诚实: 命中=两套框架在邻近文本被同时提及; M 模式是关键词启发;")
    print("      需人工复核是否'真张力'(不只是罗列两派)。")
    Path("out/demo/tensions_hist.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/tensions_hist.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                   encoding="utf-8")
    print("已存 out/demo/tensions_hist.json")


if __name__ == "__main__":
    main()
