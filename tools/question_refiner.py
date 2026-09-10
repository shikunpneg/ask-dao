# -*- coding: utf-8 -*-
"""tools/question_refiner.py — 日常疑问 -> 可判科学问题（R55）

R54 网页疑问是粗的(前缀粘连/因果转问粗糙)。本模块把"日常疑问"**精确定型**:
  疑问类型分类(机制/数量/存在性/定义/边界) -> 映射判定路由 -> 写成可验证的科学问题。

这是链路里"日常 -> 科学"的关键加工步 —— 目标是让 AI4S harness 能直接解。
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def clean(daily):
    """清洗前缀粘连: 把 'whatDidn't' / 'howbig' 拆成干净问句。"""
    t = daily.strip()
    # 去多余 '?'
    t = t.rstrip("?")
    # 英文疑问词开头(可能粘连小写后续): what/how/whether/what-is/does/is/can
    m = re.match(r"^(what|how|whether|what-is|does|is|can|why)(?=[A-Za-z])", t, re.I)
    if m and len(m.group(0)) < len(t):
        # 分离: 疑问词 + 剩余(保持可读)
        t = t
    # 去掉 qtype 前缀污染(如 'what' 'how' 作为来源标签混入)
    t = re.sub(r"^(what|how|whether|what-is|why)", "", t, flags=re.I).strip()
    return t


def classify(q):
    """按疑问类型分类日常疑问, 返回 (类型, 对象, 判定路由)。"""
    t = clean(q["daily_question"])
    dom = q["domain"]
    # 英文疑问类型(用干净的 t)
    if re.search(r"\bhow big\b|\bhow many\b|\bhow large\b|\bhow much\b", t, re.I):
        return "数量/边界", dom, {"天文": "观测统计", "生物": "生态普查", "物理": "数值模拟",
                                  "心理": "量表", "数学": "枚举", "信息": "统计"}.get(dom, "统计")
    if re.search(r"\bwhy\b|\bwhat causes\b|机制|原因", t, re.I):
        return "机制/因果", dom, {"天文": "物理建模", "生物": "实验+系谱", "物理": "理论",
                                 "心理": "实验设计", "数学": "证明", "信息": "计算"}.get(dom, "机制建模")
    if re.search(r"\bwhat is\b|\bwhat are\b|什么是", t, re.I):
        return "定义/本质", dom, {"天文": "观测定义", "生物": "分类学", "物理": "理论",
                                 "心理": "概念分析", "数学": "形式化", "信息": "计算"}.get(dom, "概念分析")
    if re.search(r"\bcan\b|\bpossible\b|能否|是否存在", t, re.I):
        return "存在性/可行性", dom, {"天文": "观测验证", "生物": "实验", "物理": "理论",
                                      "心理": "实验", "数学": "构造", "信息": "算法"}.get(dom, "验证")
    if re.search(r"\bdoes\b|\bis\b|\bis it\b", t, re.I):
        return "真伪判断", dom, {"天文": "观测", "生物": "实验", "物理": "实验+理论",
                                "心理": "实验", "数学": "判定", "信息": "检验"}.get(dom, "判定")
    # 中文疑问
    if re.search(r"多少|几个|多长|多大", t):
        return "数量/边界", dom, "统计"
    if re.search(r"为什么|为何|由于|导致|原因", t):
        return "机制/因果", dom, "机制建模"
    if re.search(r"什么是|何为", t):
        return "定义/本质", dom, "概念分析"
    return "混合/待定", dom, "待定"


def refine(q):
    kind, dom, route = classify(q)
    daily = q["daily_question"]
    daily_clean = clean(daily)
    # 写科学问题: 把日常疑问转成可验证形式
    if kind == "数量/边界":
        sci = f"在{dom}中, '{daily_clean[:40]}' 的精确数值/边界是多少? 随什么参数变化?"
    elif kind == "机制/因果":
        sci = f"在{dom}中, 驱动'{daily_clean[:40]}' 的机制是什么? 能否用可检验模型刻画?"
    elif kind == "定义/本质":
        sci = f"'{daily_clean[:40]}' 的{dom}学精确定义是什么? 该定义能否操作化(可判定)?"
    elif kind == "存在性/可行性":
        sci = f"'{daily_clean[:40]}' 在{dom}中是否可实现/存在? 构造或反例?"
    elif kind == "真伪判断":
        sci = f"'{daily_clean[:40]}' 在{dom}中是否为真? 判定依据?"
    else:
        sci = f"'{daily_clean[:40]}' 在{dom}中的结构是什么?"
    return {**q, "kind": kind, "judge_route": route,
            "scientific_question": sci.strip()}


def main():
    web = json.loads((HERE / "out/demo/web_experience.json").read_text(encoding="utf-8"))
    refined = [refine(q) for q in web]
    print("=" * 100)
    print("日常疑问 -> 可判科学问题（定型器）")
    print("=" * 100)
    print(f"  输入 {len(refined)} 条日常疑问")
    print(f"\n  类型分布: {dict(Counter(r['kind'] for r in refined))}")
    print(f"\n  样本:")
    for r in refined[:10]:
        print(f"\n  日常: {r['daily_question'][:60]}")
        print(f"  类型: {r['kind']}  路由: {r['judge_route']}")
        print(f"  科学: {r['scientific_question'][:90]}")

    # 写回 web_experience + 并入 manifest
    (HERE / "out/demo/web_experience.json").write_text(
        json.dumps(refined, ensure_ascii=False, indent=1), encoding="utf-8")
    man = HERE / "out/demo/discovery_manifest.json"
    d = json.loads(man.read_text(encoding="utf-8"))
    # 用精确定型后的版本替换旧网页条目
    d["problems"] = [p for p in d["problems"] if p.get("source", "").startswith("http")] + [
        {**r, "id": f"WEB_{i}", "domain": r["domain"],
         "statement": r["scientific_question"],
         "conjecture": r["daily_question"], "evidence": {},
         "judge_route": r["judge_route"], "status": "待判定", "layer": "L0/L1"}
        for i, r in enumerate(refined)]
    d["count"] = len(d["problems"])
    man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  已并入 discovery_manifest (总数 {d['count']})")
    print("\n诚实: 定型后的科学问题仍**未验证**(待判定); 但已有判定路由 -> 可交 AI4S harness。")


if __name__ == "__main__":
    main()
