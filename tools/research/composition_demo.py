# -*- coding: utf-8 -*-
"""composition_demo.py — 方向级组合样例(L3 x L1 / L3 x L2) + 一个数值判定的融合探针
样例以"研究方向的典型问法"组合"别方向对象/算子", 每个标注判定路由。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

DEMOS = [
    # (组合, 候选问题, 判定路由)
    ("数论-表示计数 × 代数-范数(L2: 代数数范数)",
     "环 Z[√d] 中范数 N(a+b√d)=n 的表示数 r_d(n): 在 n≤N 的分布、纪录与界?(类数相关)",
     "数值: 计算 r_d(n) 到 N 并找纪录; 理论: 类数与解析数论(部分已知)"),
    ("动力-周期/收敛(L3) × 数论-3n+k(L1 载体: 递推族)",
     "3n+k 型映射(k=1..7) 小参数全扫: 哪些 k 出现多循环/疑似发散?",
     "数值(本轮即判): 迭代扫至 2e4"),
    ("组合-极值与禁构 × 分析-极值模板(L3×L3)",
     "在禁 subgraph 约束下, 度分布不均匀度的极值(图×分析混合量)",
     "数值+图枚举(可造); 需要图载体引擎(未建)"),
    ("逻辑-可定义性(L3) × 概率-相变(L3)",
     "受限语法随机公式的 0-1 律阈值如何随语法(L3方向参数)移动?",
     "数值相变模拟+形式证明(部分, 需语法引擎)"),
    ("数论-分布 × 概率-大偏差",
     "质数在短区间计数偏离期望的偏差尾部分布是否高斯?",
     "数值: 统计偏差直方图; 理论: 黎曼假说相关(部分已知)"),
]


def scan_3nk(max_n=12000, k_lo=1, k_hi=7):
    """3n+k: n 奇 -> 3n+k, 偶 -> n/2. 小规模: 起始<=12000, 步数<=600, 超 1e6 判逃逸。"""
    res = {}
    for k in range(k_lo, k_hi + 1):
        multi_cycles = 0
        escape = 0
        sample = None
        for start in range(2, 12001):
            x = start
            seen = {}
            steps = 0
            while steps < 600:
                if x == 1:
                    break
                if x > 1000000:
                    escape += 1
                    break
                if x in seen:
                    cyc = len(seen) - seen[x]
                    if cyc not in (1, 2):
                        multi_cycles += 1
                        if sample is None:
                            sample = (start, x, cyc)
                    break
                seen[x] = steps
                x = 3 * x + k if x % 2 else x // 2
                steps += 1
            else:
                escape += 1
        res[k] = {"multi_cycles": multi_cycles, "escape": escape, "sample": sample}
    return res


if __name__ == "__main__":
    r = scan_3nk()
    lines = ["# 方向级组合样例(composition_demo)", ""]
    for i, (combo, q, route) in enumerate(DEMOS, 1):
        lines += [f"## C{i}: {combo}", f"- 候选问题: {q}", f"- 判定路由: {route}", ""]
    lines.append("## 数值探针: 3n+k 族(k=1..7, 起始≤12000, 逃逸阈 1e6)")
    for k, v in r.items():
        lines.append(f"- k={k}: 非平凡多循环起始数={v['multi_cycles']}, 逃逸疑似={v['escape']}, 例={v['sample']}")
    lines.append("")
    lines.append("注: 3n+1(k=1) 无数值异常符合预期; k>1 出现非平凡环/疑似逃逸即为该族'记录级发现'(需与文献 3n+k 比对)。")
    path = Path(__file__).resolve().parent.parent / "docs/composition_demo.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:3]))
    for k, v in r.items():
        print(f"k={k}: cycles={v['multi_cycles']} escape={v['escape']} sample={v['sample']}")
