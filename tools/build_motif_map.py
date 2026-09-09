# -*- coding: utf-8 -*-
"""build_motif_map.py — 按 MOTIF_DEFINITION 分层重建母题地图(初版, 载体/路由逐步补齐)
层级: L0 结构本体 | L1 对象族 | L2 算子/度量 | L3 方向母题(研究纲领) | L4 域(登记用)
输出: out/demo/motif_map.json + 统计打印
"""
import json
from pathlib import Path

L3_DIRECTIONS = {  # 域: [方向母题...]
    "数论": ["分布与均匀性", "表示计数(可加组合)", "素因子结构", "同余与模类", "丢番图方程与解集", "间隙与纪录", "无穷性与密度"],
    "代数": ["结构分类", "表示与模", "扩张与Galois对偶", "格与序结构", "根与不变量"],
    "分析": ["极值与正则性", "收敛与振荡", "逼近与级数", "积分与测度", "不动点与算子谱"],
    "几何/拓扑": ["形状不变量", "度量与距离极值", "覆盖与剖分", "连通与纤维化", "曲率与测地"],
    "概率/统计": ["相变与临界", "大偏差与集中", "极限定理与遍历", "估计与检验功效", "随机结构"],
    "组合": ["极值与禁构", "计数与生成函数", "染色与可满足", "设计与覆盖", "偏序与格论", "算法组合与复杂"],
    "逻辑/计算": ["可判定与不可判定", "可定义性与谱系", "模型与范畴性", "复杂度与下界", "证明与反证结构"],
    "动力系统": ["收敛与周期", "混沌与敏感", "遍历性质", "分岔与临界", "不变测度"],
    "语言-形式": ["生成文法层级", "歧义与熵率", "自动机与正则结构", "可表示性与同构"],
    "信息-计算": ["熵与信道容量", "复杂度度量", "编码与纠错", "接地与语义", "算法信息论"],
}

L2_OPS = ["因子和σ", "除数τ", "欧拉φ", "素因子计数", "数位和", "范数(代数数)", "谱半径", "香农熵",
          "柯氏复杂度", "偏差度量", "距离函数", "共轭与对偶", "迹与行列式", "模长与范数", "测度", "梯度", "拉普拉斯"]

L1_OBJECTS = ["质数", "奇合数", "平方数", "三角数", "斐波那契数", "回文数", "半素数", "完全数族",
              "格点游走", "平面图", "正则图", "线性递归序列", "模群/矩阵群", "有限域", "配分数", "黎曼ζ值",
              "连分数", "多项式族", "格(Lattice)", "自由群", "偏序集", "二叉树", "de Bruijn 序列", "无平方因子数"]

L0_STRUCT = ["群", "环", "域", "序", "度量", "拓扑", "测度", "图", "格", "范畴", "流形", "概率空间"]


def main():
    out = {"L3_directions": L3_DIRECTIONS, "L2_ops": L2_OPS,
           "L1_objects": L1_OBJECTS, "L0_structures": L0_STRUCT,
           "L4_domains": list(L3_DIRECTIONS.keys())}
    path = Path(__file__).resolve().parent.parent / "out/demo/motif_map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_l3 = sum(len(v) for v in L3_DIRECTIONS.values())
    total = n_l3 + len(L2_OPS) + len(L1_OBJECTS) + len(L0_STRUCT) + len(L3_DIRECTIONS)
    print({"L3_directions_total": n_l3, "L2": len(L2_OPS), "L1": len(L1_OBJECTS),
           "L0": len(L0_STRUCT), "L4": len(L3_DIRECTIONS), "TOTAL_base_units": total})


if __name__ == "__main__":
    main()
