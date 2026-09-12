# -*- coding: utf-8 -*-
"""judge_blueprints.py — 跨域候选的"判定器蓝图":
  给还没有判定器的候选问题先写明 怎么判: 证据类型/实验/可证伪标准/判官/现状。
  目的: 让"前问题态"候选具备可执行的下一步, 而不是悬在生成层。"""
from typing import List

BLUEPRINTS = [
    {
        "id": "X_PHYS_SUM",
        "claim": "守恒量取值的(适当离散化)偶数部分都可写成 对称A守恒量+对称B守恒量",
        "domain": "物理",
        "motifs": ["对称↔守恒", "两项和"],
        "evidence_needed": ["诺特配对的谱值集合", "两守恒量的和封闭性论证"],
        "experiment": "理论: 结构论证(谱空间加法); 实验: 高精度测量校验谱和",
        "falsifiable_criteria": "存在一个可测守恒量组合不落于该和集(谱间隙)",
        "judge": "物理共同体 + 实验数据(效验族)",
        "status": "前问题态(无判定器)"},
    {
        "id": "X_BIO_INTERVAL",
        "claim": "任意两次阈值事件(选择压转变)之间都会出现可遗传的性状变异",
        "domain": "生物",
        "motifs": ["连续区间", "可遗传变异", "选择"],
        "evidence_needed": ["进化实验谱系记录", "突变率的替代测量"],
        "experiment": "实验进化: 长程驯化谱系, 统计阈值事件间的固定突变",
        "falsifiable_criteria": "存在跨阈区间无固定突变的谱系(需排除抽样)",
        "judge": "进化生物学家 + 谱系数据(功能/系谱族)",
        "status": "前问题态(无判定器)"},
    {
        "id": "X_COG_FIXED",
        "claim": "AGM 信念修正规则迭代(对固定证据流)收敛到稳定信念",
        "domain": "心理认知",
        "motifs": ["递推映射", "信念修正"],
        "evidence_needed": ["AGM 后验语义的可判定性", "人类被试信念轨迹"],
        "experiment": "形式: AGM/DP 修正的动态收敛定理; 行为: 证据流条件下被试信念更新轨迹",
        "falsifiable_criteria": "存在证据流使信念振荡不收敛(环)或对初始信念敏感",
        "judge": "认知科学共同体 + 行为数据(机制族)",
        "status": "前问题态(无判定器)"},
    {
        "id": "X_INFO_EQUAL",
        "claim": "存在串 x 使 香农熵(x) = 柯氏复杂度(x)",
        "domain": "信息-计算",
        "motifs": ["香农熵", "算法复杂度", "存在-相等"],
        "evidence_needed": ["两类复杂度的等价条件分析(典型性串 típicas)"],
        "experiment": "理论: 构造典型串(如 de Bruijn/随机串上界比较); 计算: 小串枚举比对",
        "falsifiable_criteria": "对一切串两者严格不等(需给出界)",
        "judge": "信息论/复杂性理论共同体(形式族)",
        "status": "前问题态(无判定器)"},
]


def list_blueprints() -> List[dict]:
    return BLUEPRINTS
