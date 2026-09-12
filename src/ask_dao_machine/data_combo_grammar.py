# -*- coding: utf-8 -*-
"""grammar.py — 问句语法: 稳定句式(框架) × 类型化槽位; 槽位由域实体/母题填充。
  思想: 一个领域的问题集 ≈ 少量问题句式 × 实体池的组合;
        槽位带类型约束, 填错=伪问题(三惑式)。
  演示: extract_frame(把已有问题映射回句式) / cross_demo(跨域填槽 -> 前问题态候选)。
"""
import re
from typing import Dict, List, Optional

FRAMES: Dict[str, dict] = {
    "F_threshold_sum": {
        "cn": "所有 ≥{下界} 的{域}都可写成 {对象1} + {对象2}",
        "slots": {"下界": "整数参数", "域": "域构造", "对象1": "对象类", "对象2": "对象类"},
        "judge_family": "阈值扫描(真/假+反例)"},
    "F_exist_equal": {
        "cn": "存在 {域} 使 {映射1}(x) = {映射2}(x)",
        "slots": {"域": "域构造", "映射1": "映射", "映射2": "映射"},
        "judge_family": "存在例证扫描"},
    "F_parity_char": {
        "cn": "{映射}(x) 何时为奇/偶 ⇔ {刻画}",
        "slots": {"映射": "映射", "刻画": "性质"},
        "judge_family": "表对照(全量)"},
    "F_interval_exist": {
        "cn": "对任意{域}, 在{区间构造}内存在{对象类}",
        "slots": {"域": "域构造", "区间构造": "区间", "对象类": "对象类"},
        "judge_family": "区间扫描"},
    "F_recur_converge": {
        "cn": "按规则{递推}迭代, 是否{结局}?",
        "slots": {"递推": "递推映射", "结局": "轨迹类型"},
        "judge_family": "带记忆迭代"},
    "F_char_if": {
        "cn": "{性质1} 成立 当且仅当 {性质2}?",
        "slots": {"性质1": "性质", "性质2": "性质"},
        "judge_family": "全量对照"},
}

FRAME_BY_TEMPLATE = {
    "T1": "F_threshold_sum", "T1 + 约束(相异)": "F_threshold_sum", "T1 混合类": "F_threshold_sum",
    "T1(对象类=质数)": "F_threshold_sum", "T2": "F_threshold_sum", "T3": "F_threshold_sum",
    "T5": "F_exist_equal", "T7": "F_parity_char", "T8": "F_parity_char", "T9": "F_parity_char",
    "T11": "F_interval_exist", "T14": "F_recur_converge", "T16": "F_char_if",
    "T17": "F_exist_equal", "T18": "F_exist_equal", "T19": "F_exist_equal",
}


def extract_frame(record: dict) -> Optional[str]:
    tpl = record.get("template", "")
    for key, frame in FRAME_BY_TEMPLATE.items():
        if key in tpl:
            return frame
    return None


def render(frame_id: str, fills: Dict[str, str]) -> str:
    s = FRAMES[frame_id]["cn"]
    for k, v in fills.items():
        s = s.replace("{" + k + "}", str(v))
    s = re.sub(r"\{[^}]+\}", "?", s)
    return s


# 跨域填槽示范: (frame, 槽位字典, 说明) —— 全部标'前问题态'(需该域判定器)
CROSS_DEMO: List[tuple] = [
    ("F_threshold_sum",
     {"下界": "?", "域": "守恒量取值的偶数部分(物理)", "对象1": "由对称A导出的守恒量", "对象2": "由对称B导出的守恒量"},
     "把数论'两数和'句式填入物理守恒槽; 判定=结构论证+实验 -> 前问题态"),
    ("F_interval_exist",
     {"域": "进化代际", "区间构造": "两次阈值事件之间", "对象类": "可遗传的性状变异(生物)"},
     "F_interval_exist 填生物槽; 判定=进化模型+观察 -> 前问题态"),
    ("F_recur_converge",
     {"递推": "信念修正规则(AGM)", "结局": "收敛到稳定信念"},
     "把 Collatz 句式填认知槽; 判定=认知实验/形式模型 -> 前问题态"),
    ("F_exist_equal",
     {"域": "串", "映射1": "香农熵", "映射2": "柯氏复杂度"},
     "信息论槽: 是否存在使两者相等的串? 判定=信息论 -> 前问题态"),
]


def cross_demo_sentences() -> List[tuple]:
    return [(frame, render(frame, fills), note) for frame, fills, note in CROSS_DEMO]
