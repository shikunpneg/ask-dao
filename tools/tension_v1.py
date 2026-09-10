# -*- coding: utf-8 -*-
"""tools/tension_v1.py — 张力探测器 v1: 段落窗 + 子类判定
子类: 对峙/批判(含 批判/反对/驳斥/不同于/相反/斥) vs 同文并存(朴素共现, 需语义复核)"""
import json
import re
from pathlib import Path

TEXT = Path(r"E:\ask-dao\_text")
PAIRS = [
    ("知行关系", ["知先行后", "知难行易", "先知后行"], ["行易知难", "行先知后", "不知亦能行", "知行合一", "知以行为功"]),
    ("求理路径", ["即物穷理", "格物致知", "今日格一物", "铢积寸累"], ["心即理", "致良知", "先立其大者", "六经注我"]),
    ("性善性恶", ["性善", "恻隐之心"], ["性恶", "化性起伪"]),
    ("言意之辨", ["得意忘象", "言不尽意", "得意忘言"], ["言尽意", "名逐物而迁"]),
    ("天人之分", ["天人感应", "同类相动", "人副天数"], ["明于天人之分", "天行有常", "天人交相胜"]),
    ("有无之辨", ["贵无", "以无为本"], ["崇有"]),
    ("理气先后", ["理先于气", "理在气先"], ["理在气中", "理只是气之理", "气外无理"]),
    ("顿渐之争", ["顿悟", "一闻言下便悟"], ["渐修", "积习既久", "豁然贯通"]),
    ("名实观", ["名教", "以名定是非", "事各顺于名"], ["稽实定数", "名无固宜", "约定俗成"]),
]
FILES = ["中国哲学史第2版.md"]
CONFRONT = re.compile(r"批判|反对|驳斥|抨击|斥责|不同于|相反|与.*相对|否定|不赞成")


def main():
    out = []
    for fname in FILES:
        text = (TEXT / fname).read_text(encoding="utf-8", errors="ignore")
        paras = re.split(r"\n\s*\n", text)
        for topic, a, b in PAIRS:
            for pi, para in enumerate(paras):
                if len(para) < 40 or para.startswith("#"):
                    continue
                ha = [t for t in a if t in para]
                hb = [t for t in b if t in para]
                if ha and hb:
                    sub = "对峙/批判" if CONFRONT.search(para) else "同文并存(需复核)"
                    flat = re.sub(r"\s+", " ", para)
                    out.append({"topic": topic, "file": fname, "para": pi,
                                "sub": sub, "A": ha[:2], "B": hb[:2],
                                "excerpt": flat[:180]})
    by = {}
    for o in out:
        by.setdefault(o["sub"], 0)
        by[o["sub"]] += 1
    Path("out/demo/tensions_v1.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/tensions_v1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
    print("分类:", by, "总数", len(out))
    for o in out[:12]:
        print(f"[{o['sub']}] {o['topic']} @p{o['para']}: {o['excerpt'][:100]}")


if __name__ == "__main__":
    main()


# ---- 科学史 M 模式启发: 张力候选 -> 大问题潜质分级 (R45) ----
def m_pattern(para):
    """用科学史 M 模式判断这个张力有没有大问题潜质。"""
    M = []
    if re.search(r"矛盾|不一致|不相容|冲突|悖论", para):
        M.append("M6 悖论")
    if re.search(r"异常|反例|不符合|例外|无法解释|不能说明", para):
        M.append("M2 异常")
    if re.search(r"统一|同源|合并|综合|会通|调和|贯通", para):
        M.append("M1 统一")
    if re.search(r"反对|批判|否定|驳斥|推翻", para):
        M.append("M3 公设被挑战")
    if not M:
        M.append("M0 无模式(普通分歧)")
    return M


def main_with_M():
    out = json.loads(Path("out/demo/tensions_v1.json").read_text(encoding="utf-8"))
    for o in out:
        o["M"] = m_pattern(o["excerpt"])
    big = [o for o in out if any(m != "M0 无模式(普通分歧)" for m in o["M"])]
    print("=" * 100)
    print("张力候选 × 科学史 M 模式 —— 大问题潜质分级")
    print("=" * 100)
    print(f"  张力总数: {len(out)}  带 M 模式(有潜质): {len(big)}")
    from collections import Counter
    mc = Counter(m for o in out for m in o["M"] if m != "M0")
    print(f"  M 模式分布: {dict(mc)}")
    print("\n  == 带 M 模式(大问题潜质)的张力候选 ==")
    for o in big[:10]:
        print(f"  [{','.join(o['M'])}] {o['topic']} @p{o['para']}")
        print(f"       {o['excerpt'][:90]}")
    print("\n诚实: M 模式是关键词启发; 命中 = 该张力带'异常/悖论/统一'信号, 需人工语义复核。")
    Path("out/demo/tensions_m.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    print("已存 out/demo/tensions_m.json")


if __name__ == "__main__":
    import sys
    if "--M" in sys.argv:
        main_with_M()
    else:
        main()
