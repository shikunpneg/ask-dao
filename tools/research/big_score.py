# -*- coding: utf-8 -*-
"""tools/research/big_score.py — 当务评价器 v0 (基于科学史 H1-H10 启发式)
给问题记录/命题打分(粗规则), 阈值>=5 进入大问题队列。
诚实: 权重来自15条史例归纳未回测; 自动token规则粗, 可人工覆盖。"""
import json
from pathlib import Path

H = [
    ("H1 跨界可公度", 2.0, ["统一", "同一律", "同时解释", "跨", "commensur", "consilience", "同一种力", "同一个方程"]),
    ("H2 悖论消解", 2.0, ["悖论", "矛盾", "不可调", "互相冲突", "又不", "却同时"]),
    ("H3 公设/定义层", 2.0, ["公设", "公理", "自明", "定义", "不可证明", "前提", "地基", "不完备", "不证自明"]),
    ("H4 可检验新预言", 1.5, ["预言", "预测", "新现象", "尚未观测", "待发现", "应存在"]),
    ("H5 新测量域", 1.5, ["测量", "仪器", "精度", "观测", "探测", "精度外"]),
    ("H6 异常累积", 1.0, ["异常", "偏差", "反例", "误差", "不拟合", "积累"]),
    ("H7 工具/方法缺口", 1.0, ["无法测", "不能证", "缺少方法", "新工具", "无仪器", "方法缺口"]),
    ("H8 反向设计论证", 1.0, ["反推", "倒推", "逆向", "为什么是这样", "机理是什么", "如何解释"]),
    ("H9 长期悬置", 1.0, ["未解", "多年", "300年", "百年", "悬置", "至今未证", "世纪"]),
    ("H10 判决实验可行", 1.0, ["实验", "判决", "可证伪", "检验", "能否区分"]),
]


def score_text(text: str) -> dict:
    res = {}
    tot = 0.0
    for name, w, keys in H:
        hit = any(k in text for k in keys)
        res[name] = w if hit else 0.0
        tot += res[name]
    return {"per": res, "total": round(tot, 1)}


def score_problem(p: dict) -> dict:
    txt = " ".join(filter(None, [p.get("statement", ""), p.get("seed", ""),
                                 " ".join(p.get("motifs", []))]))
    return score_text(txt)


def main():
    # 用史例人工条目验证打分器能识别大问题
    landmarks = {
        "第五公设可证吗?": "平行公设两千年来被视为自明却无法证明; 若反设它成立会怎样? 会不会产生自洽的新几何?",
        "光速有限吗?": "麦克斯韦方程暗示真空光速不随光源运动, 这与牛顿力学矛盾; 需要测量并检验其与理论预言是否一致。",
        "元素有统一秩序吗?": "60多个元素无统一分类; 能否列成周期表并预言未知元素, 由测量验证?",
        "费马大定理": "对所有n>2, x^n+y^n=z^n 无正整数解; 三百多年无人证出, 触及数与曲线对称的深层统一。",
        "物种起源": "化石、地理分布、育种经验多源证据都指向同一未知机制; 能否统一命名并提出可检验机制?",
    }
    print("== 史例验证 ==")
    for name, txt in landmarks.items():
        r = score_text(txt)
        print(f"{name}: {r['total']} {r['per']}")
    print("== 我们生成的问题(采样) ==")
    for fn, ids in [("math", ["B1", "G1"]), ("direction", ["D1", "D4"])]:
        d = json.loads(Path(f"out/demo/problems_{fn}.json").read_text(encoding="utf-8"))
        for p in d["problems"]:
            if p["id"] in ids:
                r = score_problem(p)
                print(f"{p['id']} {p['statement'][:30]}: {r['total']}")


if __name__ == "__main__":
    main()
